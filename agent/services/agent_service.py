import uuid
import asyncio
import os
from datetime import datetime, timezone
from typing import Optional, cast
from collections import defaultdict

from src.agent.graph import build_graph
from src.integrations.mail.client import mail_client
from src.agent.state import AgentState
from agent.services.draft_models import Draft, DraftContent
from langgraph.types import Command
from langchain_core.messages import HumanMessage


AGENT_BACKEND_URL = os.getenv("EMAIL_BACKEND_URL", "http://localhost:5001")


drafts: dict[str, Draft] = {}
threads: dict[str, dict] = {}
background_tasks: dict[str, asyncio.Task] = {}

ws_connections: dict[int, list] = defaultdict(list)


POLL_INTERVAL = 86400
FOLLOWUP_DELAY = 86400
MAX_FOLLOWUP = 2


def _resolve_recipient_name(name: str) -> tuple[str, str]:
    """Resolve recipient name to username and email.

    Args:
        name: Recipient name (username, partial name, or email)

    Returns:
        Tuple of (username, email). Returns (name, name) if not found.
    """
    import httpx
    import json

    print(f"=== _resolve_recipient_name: looking up '{name}' ===")

    if "@" in name:
        return (name.split("@")[0], name)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{AGENT_BACKEND_URL}/api/auth/search-users", params={"q": name})
            if response.status_code != 200:
                return (name, name)
            users = response.json().get("users", [])
            if not users:
                return (name, name)
            if len(users) == 1:
                return (users[0]["username"], users[0]["email"])
            return (name, name)
    except Exception as e:
        print(f"=== _resolve_recipient_name error: {e} ===")
        return (name, name)


def _add_message(thread: dict, role: str, content: str, action: str | None = None):
    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if action:
        msg["action"] = action
    thread["messages"].append(msg)


def _extract_subject_and_clean_body(draft_body: str) -> tuple[str, str]:
    if not draft_body:
        return "", ""
    lines = draft_body.strip().split("\n")
    subject = ""
    cleaned_lines = []
    for line in lines:
        if line.startswith("Subject:"):
            subject = line[len("Subject:"):].strip()
        else:
            cleaned_lines.append(line)
    return subject, "\n".join(cleaned_lines).strip()


async def _notify_client(user_id: int, event: dict):
    if user_id in ws_connections:
        for websocket in ws_connections[user_id]:
            try:
                await websocket.send_json(event)
            except Exception as e:
                print(f"[notify] Failed to send to client: {e}")

    try:
        from httpx import AsyncClient

        async with AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{AGENT_BACKEND_URL}/api/agent/notify/{user_id}",
                json=event,
            )
    except Exception as e:
        print(f"[notify] Forward to backend failed: {e}")


async def _process_reply(thread_id: str, reply: dict, user_id: int):
    thread = threads.get(thread_id)
    if not thread:
        return

    thread["reply_email_id"] = reply["id"]
    thread["reply_body"] = reply["body"]
    thread["status"] = "reply_received"
    thread["updated_at"] = datetime.now(timezone.utc).isoformat()

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
        graph = build_graph()
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
            thread["last_check"] = datetime.now(timezone.utc).isoformat()

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
        self.graph = build_graph()

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

        for thread_id, _ in matching:
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
        prompt: str,
    ) -> dict:
        draft_id = f"draft-{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()

        try:
            result = self.graph.invoke(
                cast(
                    AgentState,
                    {  # type: ignore[arg-type]
                        "messages": [{"role": "user", "content": prompt}],
                    },
                ),
                {"configurable": {"thread_id": draft_id, "user_id": user_id}},
            )

            if "__interrupt__" not in result or not result["__interrupt__"]:
                return {
                    "error": "Workflow did not produce expected interrupt. Draft creation requires human confirmation."
                }

            interrupt_data = result["__interrupt__"][0].value
            interrupt_type = interrupt_data.get("type", "question")

            if interrupt_type in ("review_draft", "confirm_send"):
                draft_body = interrupt_data.get("email_draft") or interrupt_data.get("draft")
                subject = interrupt_data.get("subject")
                raw_recipient = interrupt_data.get("recipient") or ""
                recipient_username, recipient_email = _resolve_recipient_name(raw_recipient)

                if not subject and draft_body:
                    subject, draft_body = _extract_subject_and_clean_body(draft_body)

                draft = Draft(
                    draft_id=draft_id,
                    user_id=user_id,
                    draft=DraftContent(
                        recipient=recipient_username,
                        recipient_username=recipient_username,
                        recipient_email=recipient_email,
                        subject=subject or "",
                        body=draft_body or "",
                    ),
                    context=prompt,
                    status="awaiting_input",
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
                        "recipient": recipient_username,
                        "recipient_username": recipient_username,
                        "recipient_email": recipient_email,
                        "subject": subject or "",
                        "body": draft_body or "",
                    },
                    "status": "awaiting_input",
                    "interrupt": {
                        "type": interrupt_type,
                        "question": interrupt_data.get("question", ""),
                    },
                    "created_at": created_at,
                }
            else:
                draft = Draft(
                    draft_id=draft_id,
                    user_id=user_id,
                    draft=DraftContent(
                        recipient="",
                        subject="",
                        body="",
                    ),
                    context=prompt,
                    status="awaiting_input",
                    thread_id=None,
                    email_id=None,
                    created_at=created_at,
                    sent_at=None,
                    updated_at=None,
                )

                drafts[draft_id] = draft

                return {
                    "draft_id": draft_id,
                    "status": "awaiting_input",
                    "interrupt": {
                        "type": interrupt_type,
                        "question": interrupt_data.get("question", ""),
                    },
                    "created_at": created_at,
                }

        except KeyError as e:
            return {"error": f"Unexpected workflow response format: missing key {e}"}
        except Exception as e:
            return {"error": f"Failed to create draft: {str(e)}"}

    async def _run_create_draft(self, thread_id: str, user_id: int, prompt: str):
        try:
            result = self.graph.invoke(
                cast(
                    AgentState,
                    {"messages": [{"role": "user", "content": prompt}]},
                ),
                {"configurable": {"thread_id": thread_id, "user_id": user_id}},
            )

            draft = drafts.get(thread_id)
            if not draft:
                await _notify_client(
                    user_id,
                    {"event": "create_error", "message": "Thread not found"},
                )
                return

            if "__interrupt__" not in result or not result["__interrupt__"]:
                await _notify_client(
                    user_id,
                    {"event": "create_error", "message": "Workflow did not produce expected interrupt"},
                )
                return

            interrupt_data = result["__interrupt__"][0].value
            interrupt_type = interrupt_data.get("type", "question")

            if interrupt_type in ("review_draft", "confirm_send"):
                draft_body = interrupt_data.get("email_draft") or interrupt_data.get("draft")
                subject = interrupt_data.get("subject")
                raw_recipient = interrupt_data.get("recipient") or ""
                recipient_username, recipient_email = _resolve_recipient_name(raw_recipient)

                if not subject and draft_body:
                    subject, draft_body = _extract_subject_and_clean_body(draft_body)

                draft.draft.recipient_username = recipient_username
                draft.draft.recipient_email = recipient_email
                draft.draft.subject = subject or ""
                draft.draft.body = draft_body or ""
                draft.status = "awaiting_input"
                draft.updated_at = datetime.now(timezone.utc).isoformat()

                thread = threads.get(thread_id)
                if thread:
                    thread["recipient"] = recipient_username
                    thread["recipient_email"] = recipient_email
                    thread["meeting"]["subject"] = subject or ""
                    thread["status"] = "awaiting_input"
                    thread["updated_at"] = datetime.now(timezone.utc).isoformat()

                await _notify_client(
                    user_id,
                    {
                        "event": "create_complete",
                        "thread_id": thread_id,
                        "draft": {
                            "recipient": recipient_username,
                            "recipient_username": recipient_username,
                            "recipient_email": recipient_email,
                            "subject": subject or "",
                            "body": draft_body or "",
                        },
                        "interrupt": {
                            "type": interrupt_type,
                            "question": interrupt_data.get("question", ""),
                        },
                    },
                )
            else:
                draft.status = "awaiting_input"
                draft.updated_at = datetime.now(timezone.utc).isoformat()

                thread = threads.get(thread_id)
                if thread:
                    thread["status"] = "awaiting_input"
                    thread["updated_at"] = datetime.now(timezone.utc).isoformat()

                await _notify_client(
                    user_id,
                    {
                        "event": "create_complete",
                        "thread_id": thread_id,
                        "interrupt": {
                            "type": interrupt_type,
                            "question": interrupt_data.get("question", ""),
                        },
                    },
                )

        except Exception as e:
            draft = drafts.get(thread_id)
            if draft:
                draft.status = "error"
            await _notify_client(
                user_id,
                {"event": "create_error", "message": str(e)},
            )

    def create_empty_thread(self, user_id: int) -> dict:
        thread_id = f"thread-{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()

        thread = {
            "thread_id": thread_id,
            "email_id": None,
            "user_id": user_id,
            "recipient": "",
            "meeting": {
                "subject": "",
                "date": None,
                "time": None,
                "participants": [],
            },
            "status": "empty",
            "reply_intent": None,
            "reply_email_id": None,
            "reply_body": None,
            "followup_count": 0,
            "last_check": created_at,
            "messages": [],
            "created_at": created_at,
            "updated_at": created_at,
        }
        threads[thread_id] = thread

        return {"thread_id": thread_id}

    async def create_draft_async(self, user_id: int, prompt: str, thread_id: Optional[str] = None) -> dict:
        if thread_id is None:
            thread_id = f"thread-{uuid.uuid4().hex[:12]}"

        created_at = datetime.now(timezone.utc).isoformat()

        if thread_id not in threads:
            thread = {
                "thread_id": thread_id,
                "email_id": None,
                "user_id": user_id,
                "recipient": "",
                "meeting": {
                    "subject": "",
                    "date": None,
                    "time": None,
                    "participants": [],
                },
                "status": "processing",
                "reply_intent": None,
                "reply_email_id": None,
                "reply_body": None,
                "followup_count": 0,
                "last_check": created_at,
                "messages": [],
                "created_at": created_at,
                "updated_at": created_at,
            }
            threads[thread_id] = thread

        draft = Draft(
            draft_id=thread_id,
            user_id=user_id,
            draft=DraftContent(recipient="", subject="", body=""),
            context=prompt,
            status="processing",
            thread_id=thread_id,
            email_id=None,
            created_at=created_at,
            sent_at=None,
            updated_at=None,
        )
        drafts[thread_id] = draft

        thread = threads.get(thread_id)
        if thread:
            thread["status"] = "processing"
            thread["updated_at"] = datetime.now(timezone.utc).isoformat()

        await _notify_client(
            user_id,
            {"event": "create_processing", "thread_id": thread_id},
        )

        asyncio.create_task(self._run_create_draft(thread_id, user_id, prompt))

        return {
            "status": "processing",
            "thread_id": thread_id,
        }

    def get_draft(self, draft_id: str) -> Optional[dict]:
        draft = drafts.get(draft_id)
        if not draft:
            return None

        return {
            "draft_id": draft.draft_id,
            "draft": {
                "recipient": draft.draft.recipient_username,
                "recipient_username": draft.draft.recipient_username,
                "recipient_email": draft.draft.recipient_email,
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

    def reply_to_draft(
        self,
        draft_id: str,
        user_id: int,
        response: str,
    ) -> dict:
        draft = drafts.get(draft_id)
        if not draft:
            return {"error": "Draft not found"}

        if draft.status not in ("awaiting_input", "pending"):
            return {"error": f"Cannot reply to draft with status: {draft.status}"}

        thread_config = {"configurable": {"thread_id": draft_id, "user_id": user_id}}

        try:
            while True:
                snapshot = self.graph.get_state(thread_config)

                if not snapshot.interrupts:
                    return {"error": "No pending interrupt to resume from"}

                interrupt_data = snapshot.interrupts[0].value
                interrupt_type = interrupt_data.get("type", "question")

                if interrupt_type == "question":
                    self.graph.update_state(
                        thread_config,
                        {"messages": [HumanMessage(content=response)]},
                    )
                    result = self.graph.invoke(
                        Command(resume=response),
                        config=thread_config,
                    )
                else:
                    result = self.graph.invoke(
                        Command(resume={"response": response}),
                        config=thread_config,
                    )

                if "__interrupt__" in result and result["__interrupt__"]:
                    interrupt_data = result["__interrupt__"][0].value
                    interrupt_type = interrupt_data.get("type", "question")

                    if interrupt_type in ("review_draft", "confirm_send"):
                        draft_body = interrupt_data.get("email_draft") or interrupt_data.get("draft")
                        subject = interrupt_data.get("subject")
                        raw_recipient = interrupt_data.get("recipient") or ""
                        recipient_username, recipient_email = _resolve_recipient_name(raw_recipient)

                        if not subject and draft_body:
                            subject, draft_body = _extract_subject_and_clean_body(draft_body)

                        draft.draft.recipient_username = recipient_username
                        draft.draft.recipient_email = recipient_email
                        draft.draft.subject = subject or ""
                        draft.draft.body = draft_body or ""
                        draft.status = "awaiting_input"
                        draft.updated_at = datetime.now(timezone.utc).isoformat()

                        return {
                            "draft_id": draft_id,
                            "draft": {
                                "recipient": recipient_username,
                                "recipient_username": recipient_username,
                                "recipient_email": recipient_email,
                                "subject": subject or "",
                                "body": draft_body or "",
                            },
                            "status": "awaiting_input",
                            "interrupt": {
                                "type": interrupt_type,
                                "question": interrupt_data.get("question", ""),
                            },
                        }
                    else:
                        return {
                            "draft_id": draft_id,
                            "status": "awaiting_input",
                            "interrupt": {
                                "type": interrupt_type,
                                "question": interrupt_data.get("question", ""),
                            },
                        }

                messages = result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if hasattr(last_msg, "content"):
                        content = last_msg.content
                        if isinstance(content, list):
                            content = " ".join(
                                block.get("text", "")
                                for block in content
                                if isinstance(block, dict)
                            )
                        draft.draft.body = content
                        draft.updated_at = datetime.now(timezone.utc).isoformat()

                        email_sent = draft.draft.recipient_username and draft.draft.subject and draft.draft.body

                        if email_sent:
                            draft.status = "sent"
                            draft.sent_at = datetime.now(timezone.utc).isoformat()

                            thread = threads.get(draft_id)
                            if thread:
                                thread["recipient"] = draft.draft.recipient_username
                                thread["recipient_email"] = draft.draft.recipient_email
                                thread["meeting"]["subject"] = draft.draft.subject
                                thread["meeting"]["participants"] = [draft.draft.recipient_username]
                                thread["status"] = "waiting_reply"
                                thread["updated_at"] = datetime.now(timezone.utc).isoformat()

                            return {
                                "draft_id": draft_id,
                                "draft": {
                                    "recipient": draft.draft.recipient_username,
                                    "recipient_username": draft.draft.recipient_username,
                                    "recipient_email": draft.draft.recipient_email,
                                    "subject": draft.draft.subject,
                                    "body": draft.draft.body,
                                },
                                "status": "sent",
                                "thread_id": draft_id,
                                "message": content,
                            }
                        else:
                            draft.status = "completed"
                            return {
                                "draft_id": draft_id,
                                "draft": {
                                    "recipient": draft.draft.recipient_username,
                                    "recipient_username": draft.draft.recipient_username,
                                    "recipient_email": draft.draft.recipient_email,
                                    "subject": draft.draft.subject,
                                    "body": draft.draft.body,
                                },
                                "status": "completed",
                                "message": content,
                            }

                return {
                    "draft_id": draft_id,
                    "status": "completed",
                    "message": "Draft processing completed",
                }

        except Exception as e:
            return {"error": f"Failed to process reply: {str(e)}"}

    async def _run_reply_to_draft(self, thread_id: str, user_id: int, response: str):
        thread_config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

        try:
            while True:
                snapshot = self.graph.get_state(thread_config)

                if not snapshot.interrupts:
                    await _notify_client(
                        user_id,
                        {"event": "reply_error", "message": "No pending interrupt to resume from"},
                    )
                    return

                interrupt_data = snapshot.interrupts[0].value
                interrupt_type = interrupt_data.get("type", "question")

                if interrupt_type == "question":
                    self.graph.update_state(
                        thread_config,
                        {"messages": [HumanMessage(content=response)]},
                    )
                    result = self.graph.invoke(
                        Command(resume=response),
                        config=thread_config,
                    )
                else:
                    result = self.graph.invoke(
                        Command(resume={"response": response}),
                        config=thread_config,
                    )

                draft = drafts.get(thread_id)
                if not draft:
                    await _notify_client(
                        user_id,
                        {"event": "reply_error", "message": "Thread not found"},
                    )
                    return

                if "__interrupt__" in result and result["__interrupt__"]:
                    interrupt_data = result["__interrupt__"][0].value
                    interrupt_type = interrupt_data.get("type", "question")

                    if interrupt_type in ("review_draft", "confirm_send"):
                        draft_body = interrupt_data.get("email_draft") or interrupt_data.get("draft")
                        subject = interrupt_data.get("subject")
                        raw_recipient = interrupt_data.get("recipient") or ""
                        recipient_username, recipient_email = _resolve_recipient_name(raw_recipient)

                        if not subject and draft_body:
                            subject, draft_body = _extract_subject_and_clean_body(draft_body)

                        draft.draft.recipient_username = recipient_username
                        draft.draft.recipient_email = recipient_email
                        draft.draft.subject = subject or ""
                        draft.draft.body = draft_body or ""
                        draft.status = "awaiting_input"
                        draft.updated_at = datetime.now(timezone.utc).isoformat()

                        await _notify_client(
                            user_id,
                            {
                                "event": "reply_complete",
                                "thread_id": thread_id,
                                "draft": {
                                    "recipient": recipient_username,
                                    "recipient_username": recipient_username,
                                    "recipient_email": recipient_email,
                                    "subject": subject or "",
                                    "body": draft_body or "",
                                },
                                "interrupt": {
                                    "type": interrupt_type,
                                    "question": interrupt_data.get("question", ""),
                                },
                            },
                        )
                    else:
                        draft.status = "awaiting_input"
                        draft.updated_at = datetime.now(timezone.utc).isoformat()

                        await _notify_client(
                            user_id,
                            {
                                "event": "reply_complete",
                                "thread_id": thread_id,
                                "interrupt": {
                                    "type": interrupt_type,
                                    "question": interrupt_data.get("question", ""),
                                },
                            },
                        )
                    return

                messages = result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if hasattr(last_msg, "content"):
                        content = last_msg.content
                        if isinstance(content, list):
                            content = " ".join(
                                block.get("text", "") for block in content if isinstance(block, dict)
                            )
                        draft.draft.body = content
                        draft.updated_at = datetime.now(timezone.utc).isoformat()

                        email_sent = draft.draft.recipient_username and draft.draft.subject and draft.draft.body

                        if email_sent:
                            draft.status = "sent"
                            draft.sent_at = datetime.now(timezone.utc).isoformat()

                            new_thread_id = f"thread-{uuid.uuid4().hex[:12]}"
                            thread = {
                                "thread_id": new_thread_id,
                                "draft_id": thread_id,
                                "email_id": None,
                                "user_id": draft.user_id,
                                "recipient": draft.draft.recipient_username,
                                "recipient_email": draft.draft.recipient_email,
                                "meeting": {
                                    "subject": draft.draft.subject,
                                    "date": None,
                                    "time": None,
                                    "participants": [draft.draft.recipient_username],
                                },
                                "status": "waiting_reply",
                                "reply_intent": None,
                                "reply_email_id": None,
                                "reply_body": None,
                                "followup_count": 0,
                                "last_check": datetime.now(timezone.utc).isoformat(),
                                "messages": [],
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "updated_at": datetime.now(timezone.utc).isoformat(),
                            }

                            threads[new_thread_id] = thread
                            draft.thread_id = new_thread_id

                            await _notify_client(
                                user_id,
                                {
                                    "event": "reply_complete",
                                    "thread_id": thread_id,
                                    "new_thread_id": new_thread_id,
                                    "status": "sent",
                                    "message": content,
                                },
                            )
                        else:
                            draft.status = "completed"
                            await _notify_client(
                                user_id,
                                {
                                    "event": "reply_complete",
                                    "thread_id": thread_id,
                                    "status": "completed",
                                    "message": content,
                                },
                            )
                    return

                await _notify_client(
                    user_id,
                    {
                        "event": "reply_complete",
                        "thread_id": thread_id,
                        "status": "completed",
                    },
                )

        except Exception as e:
            draft = drafts.get(thread_id)
            if draft:
                draft.status = "error"
            await _notify_client(
                user_id,
                {"event": "reply_error", "message": str(e)},
            )

    async def reply_to_draft_async(self, thread_id: str, user_id: int, response: str) -> dict:
        draft = drafts.get(thread_id)
        if not draft:
            return {"error": "Thread not found"}

        if draft.status not in ("awaiting_input", "pending"):
            return {"error": f"Cannot reply to thread with status: {draft.status}"}

        draft.status = "processing"
        draft.updated_at = datetime.now(timezone.utc).isoformat()

        await _notify_client(
            user_id,
            {"event": "reply_processing", "thread_id": thread_id},
        )

        asyncio.create_task(self._run_reply_to_draft(thread_id, user_id, response))

        return {
            "status": "processing",
            "thread_id": thread_id,
        }

    def cancel_draft(self, thread_id: str) -> dict:
        draft = drafts.get(thread_id)
        thread = threads.get(thread_id)

        if not draft and not thread:
            return {"error": "Thread not found"}

        if draft and draft.status == "sent":
            return {"error": "Cannot remove a sent thread"}

        drafts.pop(thread_id, None)
        threads.pop(thread_id, None)

        return {
            "thread_id": thread_id,
            "status": "removed",
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
                    "recipient": d.draft.recipient_username,
                    "recipient_username": d.draft.recipient_username,
                    "recipient_email": d.draft.recipient_email,
                    "subject": d.draft.subject,
                    "status": d.status,
                },
                "thread_id": d.thread_id,
                "created_at": d.created_at,
                "sent_at": d.sent_at,
            }
            for d in user_drafts
        ]

    async def send_draft(self, draft_id: str, body: Optional[str] = None) -> dict:
        draft = drafts.get(draft_id)
        if not draft:
            return {"error": "Draft not found"}

        if draft.status not in ("pending", "awaiting_input"):
            return {"error": f"Cannot send draft with status: {draft.status}"}

        recipient = draft.draft.recipient_username or ""
        recipient_email = draft.draft.recipient_email or ""

        if not recipient_email:
            if "@" not in recipient:
                from src.agent.tools.email_tools import resolve_recipient

                result = resolve_recipient(recipient)
                import json

                try:
                    data = json.loads(result)
                    if "email" in data:
                        recipient_email = data["email"]
                    else:
                        return {"error": result}
                except json.JSONDecodeError:
                    return {"error": result}
            else:
                recipient_email = recipient

        final_body = draft.draft.body

        try:
            result = await mail_client.send_email(
                sender_id=draft.user_id,
                recipient_email=recipient_email,
                subject=draft.draft.subject,
                body=final_body,
            )

            email_id = result.get("email_id")

            draft.status = "sent"
            draft.sent_at = datetime.now(timezone.utc).isoformat()
            draft.email_id = email_id

            thread_id = draft.thread_id
            thread = threads.get(thread_id)
            if thread:
                thread["email_id"] = email_id
                thread["recipient"] = recipient
                thread["meeting"]["subject"] = draft.draft.subject
                thread["meeting"]["participants"] = [recipient]
                thread["status"] = "waiting_reply"
                thread["updated_at"] = datetime.now(timezone.utc).isoformat()
            else:
                thread_id = f"thread-{uuid.uuid4().hex[:12]}"
                thread = {
                    "thread_id": thread_id,
                    "draft_id": draft_id,
                    "email_id": email_id,
                    "user_id": draft.user_id,
                    "recipient": recipient,
                    "meeting": {
                        "subject": draft.draft.subject,
                        "date": None,
                        "time": None,
                        "participants": [recipient],
                    },
                    "status": "waiting_reply",
                    "reply_intent": None,
                    "reply_email_id": None,
                    "reply_body": None,
                    "followup_count": 0,
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "messages": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
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
                    "recipient": draft.draft.recipient_username,
                    "recipient_username": draft.draft.recipient_username,
                    "recipient_email": draft.draft.recipient_email,
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
            "email_id": thread["email_id"],
            "user_id": thread["user_id"],
            "recipient": thread["recipient"],
            "recipient_email": thread.get("recipient_email"),
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
                "recipient": t["recipient"],
                "recipient_email": t.get("recipient_email"),
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
        thread["updated_at"] = datetime.now(timezone.utc).isoformat()

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
        thread["updated_at"] = datetime.now(timezone.utc).isoformat()

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

    def get_status(self, thread_id: str, active_workflows: dict = None) -> dict:
        thread = threads.get(thread_id)
        if not thread:
            return {"error": "Thread not found", "status": "error"}

        return {
            "thread_id": thread["thread_id"],
            "status": thread["status"],
            "recipient": thread["recipient"],
            "meeting": thread.get("meeting"),
            "reply_intent": thread.get("reply_intent"),
            "messages": thread.get("messages", []),
            "followup_count": thread["followup_count"],
            "created_at": thread["created_at"],
            "updated_at": thread["updated_at"],
        }

    def get_history(self, thread_id: str, active_workflows: dict = None) -> dict:
        thread = threads.get(thread_id)
        if not thread:
            return {"error": "Thread not found", "status": "error"}

        return {
            "thread_id": thread["thread_id"],
            "status": thread["status"],
            "user_id": thread["user_id"],
            "email_id": thread.get("email_id"),
            "draft_id": thread.get("draft_id"),
            "recipient": thread["recipient"],
            "meeting": thread.get("meeting"),
            "messages": thread.get("messages", []),
            "total_messages": len(thread.get("messages", [])),
            "created_at": thread["created_at"],
            "updated_at": thread["updated_at"],
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
