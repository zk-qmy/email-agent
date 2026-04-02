import uuid
import asyncio
from datetime import datetime
from typing import Optional, cast, Any
from collections import defaultdict

from src.workflows.router import build_router
from src.integrations.mail.client import mail_client
from src.core.states import AgentState
from agent.services.draft_models import Draft, DraftContent


drafts: dict[str, Draft] = {}
threads: dict[str, dict] = {}
background_tasks: dict[str, asyncio.Task] = {}

ws_connections: dict[int, list] = defaultdict(list)


POLL_INTERVAL = 86400
FOLLOWUP_DELAY = 86400
MAX_FOLLOWUP = 2


def _add_message(thread: dict, role: str, content: str, action: str | None = None):
    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if action:
        msg["action"] = action
    thread["messages"].append(msg)


async def _notify_client(user_id: int, event: dict):
    if user_id in ws_connections:
        for websocket in ws_connections[user_id]:
            try:
                await websocket.send_json(event)
            except Exception as e:
                print(f"[notify] Failed to send to client: {e}")


async def _process_reply(thread_id: str, reply: dict, user_id: int):
    thread = threads.get(thread_id)
    if not thread:
        return

    thread["reply_email_id"] = reply["id"]
    thread["reply_body"] = reply["body"]
    thread["status"] = "reply_received"
    thread["updated_at"] = datetime.utcnow().isoformat()

    try:
        await mail_client.mark_read(reply["id"])
    except Exception as e:
        print(f"[process_reply] Failed to mark read: {e}")

    asyncio.create_task(
        _notify_client(
            user_id,
            {
                "event": "reply_received",
                "thread_id": thread_id,
                "reply_body": reply["body"],
                "sender": reply.get("sender_email"),
                "intent": "processing",
            },
        )
    )

    try:
        graph = build_router()
        result = await graph.ainvoke(
            cast(
                AgentState,
                {  # type: ignore[arg-type]
                    "messages": [{"role": "user", "content": reply["body"]}],
                    "workflow": "schedule",
                    "meeting": thread.get("meeting", {}),
                    "email": {"last_reply": reply["body"]},
                },
            ),
            {"configurable": {"thread_id": thread_id, "user_id": user_id}},
        )
        result_dict = dict(result) if isinstance(result, dict) else result.model_dump()
        email_data = result_dict.get("email", {})
        if isinstance(email_data, dict):
            intent = email_data.get("reply_intent", "confirmed")
        else:
            intent = getattr(email_data, "reply_intent", None) or "confirmed"
    except Exception:
        intent = "confirmed"

    thread["reply_intent"] = intent

    await _notify_client(
        user_id,
        {
            "event": "reply_received",
            "thread_id": thread_id,
            "reply_body": reply["body"],
            "sender": reply.get("sender_email"),
            "intent": intent,
        },
    )


async def _poll_thread(thread_id: str):
    thread = threads.get(thread_id)
    if not thread:
        return

    try:
        result = await mail_client.poll_inbox(
            user_id=thread["user_id"], last_check=thread.get("last_check")
        )

        new_emails = result.get("new_emails", [])
        replies = [
            e for e in new_emails if e.get("sender_email") == thread["recipient"]
        ]

        if replies:
            await _process_reply(thread_id, replies[0], thread["user_id"])

            if thread_id in background_tasks:
                background_tasks[thread_id].cancel()
                del background_tasks[thread_id]
        else:
            thread["last_check"] = datetime.utcnow().isoformat()

    except Exception as e:
        print(f"[poll] Error polling thread {thread_id}: {e}")


async def _auto_followup(thread_id: str):
    thread = threads.get(thread_id)
    if not thread:
        return

    await asyncio.sleep(FOLLOWUP_DELAY)

    while thread["status"] == "waiting_reply":
        await _poll_thread(thread_id)

        if thread["status"] != "waiting_reply":
            break

        thread["followup_count"] += 1

        if thread["followup_count"] > MAX_FOLLOWUP:
            await _notify_client(
                thread["user_id"],
                {
                    "event": "status_update",
                    "thread_id": thread_id,
                    "status": "max_followup_reached",
                    "message": "No response after maximum followups",
                },
            )
            break

        followup_body = (
            f"Hi,\n\n"
            f"Just following up regarding my previous email about "
            f"{thread.get('meeting', {}).get('subject', 'the meeting')}.\n\n"
            f"Please let me know if you need any additional information.\n\n"
            f"Best regards"
        )

        try:
            await mail_client.send_email(
                sender_id=thread["user_id"],
                recipient_email=thread["recipient"],
                subject=f"Re: {thread.get('meeting', {}).get('subject', 'Meeting')}",
                body=followup_body,
            )
        except Exception as e:
            print(f"[followup] Failed to send: {e}")

        await _notify_client(
            thread["user_id"],
            {
                "event": "followup_sent",
                "thread_id": thread_id,
                "followup_count": thread["followup_count"],
            },
        )

        await asyncio.sleep(POLL_INTERVAL)

    if thread_id in background_tasks:
        del background_tasks[thread_id]


class AgentService:
    def __init__(self):
        self.graph = build_router()

    def add_websocket(self, user_id: int, websocket):
        ws_connections[user_id].append(websocket)

    def remove_websocket(self, user_id: int, websocket):
        if user_id in ws_connections:
            ws_connections[user_id] = [
                ws for ws in ws_connections[user_id] if ws != websocket
            ]

    async def handle_backend_push(self, user_id: int, event: dict):
        evt = event.get("event")
        if evt != "new_email":
            return

        email_data = event.get("email", {})
        sender_email = email_data.get("sender_email")
        email_id = email_data.get("id")

        if not sender_email or not email_id:
            return

        matching = [
            (tid, t)
            for tid, t in threads.items()
            if t["user_id"] == user_id
            and t["status"] == "waiting_reply"
            and t["recipient"] == sender_email
        ]

        for thread_id, thread in matching:
            try:
                email = await mail_client.get_email(email_id)
                if email and "email" in email:
                    reply_data = email["email"]
                    await _process_reply(thread_id, reply_data, user_id)

                    if thread_id in background_tasks:
                        background_tasks[thread_id].cancel()
                        del background_tasks[thread_id]
            except Exception as e:
                print(
                    f"[handle_backend_push] Error processing reply for thread {thread_id}: {e}"
                )

    def create_draft(
        self,
        user_id: int,
        recipient: str,
        subject: str,
        context: str,
    ) -> dict:
        draft_id = f"draft-{uuid.uuid4().hex[:12]}"
        created_at = datetime.utcnow().isoformat()

        try:
            result = self.graph.invoke(
                cast(
                    AgentState,
                    {  # type: ignore[arg-type]
                        "messages": [{"role": "user", "content": context}],
                        "meeting": {
                            "participants": [recipient],
                            "date": subject,
                            "context": context,
                        },
                        "email": {},
                    },
                ),
                {"configurable": {"thread_id": draft_id, "user_id": user_id}},
            )

            if "__interrupt__" not in result or not result["__interrupt__"]:
                return {
                    "error": "Workflow did not produce expected interrupt. Draft creation requires human confirmation."
                }

            interrupt_data = result["__interrupt__"][0].value
            draft_body = interrupt_data.get("email_draft")

            if not draft_body:
                return {"error": "Workflow did not produce an email draft."}
        except KeyError as e:
            return {"error": f"Unexpected workflow response format: missing key {e}"}
        except Exception as e:
            return {"error": f"Failed to create draft: {str(e)}"}

        created_at = datetime.utcnow().isoformat()

        draft = Draft(
            draft_id=draft_id,
            user_id=user_id,
            draft=DraftContent(
                recipient=recipient,
                subject=subject,
                body=draft_body,
            ),
            context=context,
            status="pending",
            thread_id=None,
            email_id=None,
            created_at=created_at,
            sent_at=None,
            updated_at=None,
        )

        drafts[draft_id] = draft

        return {
            "draft_id": draft_id,
            "draft": {
                "recipient": recipient,
                "subject": subject,
                "body": draft_body,
            },
            "status": "pending",
            "created_at": created_at,
        }

    def get_draft(self, draft_id: str) -> Optional[dict]:
        draft = drafts.get(draft_id)
        if not draft:
            return None

        return {
            "draft_id": draft.draft_id,
            "draft": {
                "recipient": draft.draft.recipient,
                "subject": draft.draft.subject,
                "body": draft.draft.body,
            },
            "status": draft.status,
            "user_id": draft.user_id,
            "context": draft.context,
            "thread_id": draft.thread_id,
            "created_at": draft.created_at,
            "sent_at": draft.sent_at,
            "email_id": draft.email_id,
        }

    def cancel_draft(self, draft_id: str) -> dict:
        draft = drafts.get(draft_id)
        if not draft:
            return {"error": "Draft not found"}

        if draft.status == "sent":
            return {"error": "Cannot cancel a sent draft"}

        draft.status = "cancelled"

        return {
            "draft_id": draft_id,
            "draft": {
                "recipient": draft.draft.recipient,
                "subject": draft.draft.subject,
                "body": draft.draft.body,
            },
            "status": "cancelled",
        }

    def get_user_drafts(self, user_id: int, status: Optional[str] = None) -> list:
        user_drafts = [draft for draft in drafts.values() if draft.user_id == user_id]

        if status:
            user_drafts = [d for d in user_drafts if d.status == status]

        user_drafts.sort(key=lambda x: x.created_at, reverse=True)

        return [
            {
                "draft_id": d.draft_id,
                "draft": {
                    "recipient": d.draft.recipient,
                    "subject": d.draft.subject,
                    "status": d.status,
                },
                "thread_id": d.thread_id,
                "created_at": d.created_at,
                "sent_at": d.sent_at,
            }
            for d in user_drafts
        ]

    async def send_draft(self, draft_id: str) -> dict:
        draft = drafts.get(draft_id)
        if not draft:
            return {"error": "Draft not found"}

        if draft.status != "pending":
            return {"error": f"Cannot send draft with status: {draft.status}"}

        final_body = draft.draft.body

        try:
            result = await mail_client.send_email(
                sender_id=draft.user_id,
                recipient_email=draft.draft.recipient,
                subject=draft.draft.subject,
                body=final_body,
            )

            email_id = result.get("email_id")

            draft.status = "sent"
            draft.sent_at = datetime.utcnow().isoformat()
            draft.email_id = email_id

            thread_id = f"thread-{uuid.uuid4().hex[:12]}"
            thread = {
                "thread_id": thread_id,
                "draft_id": draft_id,
                "email_id": email_id,
                "user_id": draft.user_id,
                "recipient": draft.draft.recipient,
                "meeting": {
                    "subject": draft.draft.subject,
                    "date": None,
                    "time": None,
                    "participants": [draft.draft.recipient],
                },
                "status": "waiting_reply",
                "reply_intent": None,
                "reply_email_id": None,
                "reply_body": None,
                "followup_count": 0,
                "last_check": datetime.utcnow().isoformat(),
                "messages": [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            threads[thread_id] = thread
            draft.thread_id = thread_id

            from agent.services.ws_client import backend_ws_client

            await backend_ws_client.connect(draft.user_id)

            task = asyncio.create_task(_auto_followup(thread_id))
            background_tasks[thread_id] = task

            await _notify_client(
                draft.user_id,
                {
                    "event": "draft_sent",
                    "draft_id": draft_id,
                    "thread_id": thread_id,
                    "email_id": email_id,
                },
            )

            await _notify_client(
                draft.user_id,
                {
                    "event": "waiting_reply",
                    "thread_id": thread_id,
                    "message": "Email sent. Waiting for reply...",
                },
            )

            return {
                "draft_id": draft_id,
                "draft": {
                    "recipient": draft.draft.recipient,
                    "subject": draft.draft.subject,
                    "body": final_body,
                },
                "thread_id": thread_id,
                "email_id": email_id,
                "status": "sent",
                "message": "Email sent successfully",
            }

        except Exception as e:
            return {"error": f"Failed to send email: {str(e)}"}

    def get_thread(self, thread_id: str) -> Optional[dict]:
        thread = threads.get(thread_id)
        if not thread:
            return None

        return {
            "thread_id": thread["thread_id"],
            "draft_id": thread["draft_id"],
            "email_id": thread["email_id"],
            "user_id": thread["user_id"],
            "recipient": thread["recipient"],
            "meeting": thread["meeting"],
            "status": thread["status"],
            "reply_intent": thread["reply_intent"],
            "reply_body": thread.get("reply_body"),
            "followup_count": thread["followup_count"],
            "messages": thread.get("messages", []),
            "created_at": thread["created_at"],
            "updated_at": thread["updated_at"],
        }

    def get_user_threads(self, user_id: int, status: Optional[str] = None) -> list:
        user_threads = [
            thread for thread in threads.values() if thread["user_id"] == user_id
        ]

        if status:
            user_threads = [t for t in user_threads if t["status"] == status]

        user_threads.sort(key=lambda x: x["created_at"], reverse=True)

        return [
            {
                "thread_id": t["thread_id"],
                "draft_id": t["draft_id"],
                "recipient": t["recipient"],
                "status": t["status"],
                "reply_intent": t["reply_intent"],
                "followup_count": t["followup_count"],
                "created_at": t["created_at"],
            }
            for t in user_threads
        ]

    async def confirm_meeting(self, thread_id: str) -> dict:
        thread = threads.get(thread_id)
        if not thread:
            return {"error": "Thread not found"}

        if thread["status"] == "completed":
            return {"error": "Thread already completed"}

        thread["status"] = "completed"
        thread["updated_at"] = datetime.utcnow().isoformat()

        _add_message(thread, "assistant", "Meeting confirmed")

        await _notify_client(
            thread["user_id"],
            {
                "event": "meeting_confirmed",
                "thread_id": thread_id,
                "meeting": thread["meeting"],
                "message": "Meeting confirmed successfully",
            },
        )

        if thread_id in background_tasks:
            background_tasks[thread_id].cancel()
            del background_tasks[thread_id]

        return {
            "thread_id": thread_id,
            "status": "completed",
            "meeting": thread["meeting"],
            "message": "Meeting confirmed successfully",
        }

    async def decline_meeting(self, thread_id: str) -> dict:
        thread = threads.get(thread_id)
        if not thread:
            return {"error": "Thread not found"}

        if thread["status"] == "declined":
            return {"error": "Thread already declined"}

        thread["status"] = "declined"
        thread["updated_at"] = datetime.utcnow().isoformat()

        _add_message(thread, "assistant", "Meeting declined")

        await _notify_client(
            thread["user_id"],
            {
                "event": "meeting_declined",
                "thread_id": thread_id,
                "message": "Meeting declined",
            },
        )

        if thread_id in background_tasks:
            background_tasks[thread_id].cancel()
            del background_tasks[thread_id]

        return {
            "thread_id": thread_id,
            "status": "declined",
            "message": "Meeting declined",
        }

    def get_status(self, thread_id: str, active_workflows: dict) -> dict:
        if thread_id not in active_workflows:
            return {"error": "Thread not found", "status": "error"}

        workflow = active_workflows[thread_id]

        return {
            "thread_id": thread_id,
            "status": workflow["status"],
            "current_step": workflow.get("current_step", "unknown"),
            "email_context": workflow.get("email_context"),
            "interrupt": workflow.get("interrupt", {}),
            "messages": workflow.get("messages", []),
        }

    def get_history(self, thread_id: str, active_workflows: dict) -> dict:
        if thread_id not in active_workflows:
            return {"error": "Thread not found", "status": "error"}

        workflow = active_workflows[thread_id]

        return {
            "thread_id": thread_id,
            "status": workflow["status"],
            "user_id": workflow["user_id"],
            "email_id": workflow["email_id"],
            "email_context": workflow.get("email_context"),
            "messages": workflow["messages"],
            "total_messages": len(workflow["messages"]),
            "created_at": workflow.get("created_at"),
        }

    def _handle_error(
        self, thread_id: str, error: Exception, active_workflows: dict, operation: str
    ) -> dict:
        workflow = active_workflows.get(thread_id)
        if not workflow:
            return {"error": f"{operation} failed: Thread not found", "status": "error"}

        error_str = str(error)

        if "interrupt" in error_str.lower() or "interrupted" in error_str.lower():
            workflow["status"] = "interrupted"

            workflow["interrupt"] = {
                "type": "info",
                "question": "Please provide input.",
                "data": {},
            }

            try:
                error_value = getattr(error, "value", None)
                if isinstance(error_value, dict):
                    workflow["interrupt"] = {
                        "type": error_value.get("type", "info"),
                        "question": error_value.get("message", "Please provide input."),
                        "data": error_value,
                    }
            except Exception:
                pass

            return {
                "status": "interrupted",
                "thread_id": thread_id,
                "action_needed": workflow["interrupt"].get("type", "info"),
                "question": workflow["interrupt"].get("question"),
                "messages": workflow["messages"],
            }

        workflow["status"] = "error"
        _add_message(workflow, "assistant", f"Error: {error_str}", action="error")

        return {
            "status": "error",
            "thread_id": thread_id,
            "error": error_str,
            "messages": workflow["messages"],
        }


agent_service = AgentService()
