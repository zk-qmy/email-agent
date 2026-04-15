from typing import Literal, Optional, cast
from langgraph.types import interrupt
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel
from src.core.states import AgentState, EmailData
from src.integrations.llm.client import get_llm
from src.integrations.mail.sync_client import (
    send_email_sync,
    poll_inbox_sync,
    mark_read_sync,
)
from datetime import datetime
from config.prompts.base import PromptConfig
from config.prompts.email import meeting_prompts


def format_time(time_str: str) -> str:
    """Format 24h time to 12h format for human readability."""
    if not time_str:
        return ""
    try:
        hour, minute = time_str.split(":")
        hour, minute = int(hour), int(minute)
        if hour == 0:
            return "12:00 AM"
        elif hour < 12:
            return f"{hour}:{minute:02d} AM"
        elif hour == 12:
            return "12:00 PM"
        else:
            return f"{hour - 12}:{minute:02d} PM"
    except:
        return time_str


def draft_email(state: AgentState, prompts: PromptConfig = meeting_prompts) -> dict:
    meeting = state.meeting

    # --- resolve runtime values ---
    recipient = (
        meeting.participants[0] if meeting.participants else "recipient@example.com"
    )
    purpose = (
        getattr(meeting, "context", None)
        or getattr(meeting, "purpose", None)
        # or "discuss the agenda"
    )

    # --- build messages via NodePrompt (single source of truth) ---
    prompt = prompts.get("draft_email")
    last_msg = state.messages[-1]
    user_input: str = last_msg["content"]
    messages = prompt.build_messages(
        user_content=user_input, # TODO: add actual user message or meeting context
        recipient=recipient,
        date=meeting.date or "TBD",
        time=format_time(meeting.time) if meeting.time else "TBD",
        purpose=purpose,
    )

    # --- call LLM ---
    try:
        response = get_llm().invoke(messages)
        raw_draft = response.content if hasattr(
            response, "content") else str(response)
        print(f"draft_email: LLM response:\n{raw_draft}")

        # Handdle string and list response formats
        if isinstance(raw_draft, list):
            draft = "\n".join(
                block["text"] for block in raw_draft
                if isinstance(block, dict) and block.get("type") == "text"
            )
        print(f"draft_email: extracted draft:\n{draft}")

    except Exception:
        print("[draft_email] LLM invocation failed, using fallback draft")
        draft = (
            f"Hi,\n\nI'd like to schedule a meeting on {meeting.date}.\n\nBest regards"
        )

    # --- parse subject out of draft ---
    subject = meeting.date or "Meeting Request"
    body = draft

    if draft.startswith("Subject:"):
        lines = draft.split("\n", 1)
        subject = lines[0].replace("Subject:", "").strip()
        body = lines[1].strip() if len(lines) > 1 else draft

    print(f"[draft_email] draft created for {recipient}")
    return {
        "email": EmailData(draft=body, approval_status="pending"),
        "response": f"Subject: {subject}\n\n{body}",
    }


def process_approval(state: AgentState) -> dict:
    email_draft = state.email.draft or "No draft available"

    user_input = interrupt(
        {
            "type": "approval",
            "message": "Please review and approve this email draft, or request edits.",
            "email_draft": email_draft,
            "missing_fields": [],
            "data": {
                "recipient": (
                    state.meeting.participants[0]
                    if state.meeting.participants
                    else None
                ),
                "subject": (
                    f"Meeting Request for {state.meeting.date}"
                    if state.meeting.date
                    else "Meeting Request"
                ),
            },
        }
    )

    content = (
        user_input.get("content", "").lower()
        if isinstance(user_input, dict)
        else str(user_input).lower()
    )

    if any(w in content for w in ["approved", "ok", "looks good", "yes", "send"]):
        status = "approved"
    elif "edit" in content:
        status = "edit"
    elif "cancel" in content:
        status = "cancelled"
    else:
        status = "pending"

    print(f"[process_approval] '{content}' → {status}")
    return {"email": EmailData(approval_status=status)}


def send_email(state: AgentState, config: RunnableConfig) -> dict:
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            print("[send_email] error: no user_id in config")
            return {
                "email": EmailData(status="failed"),
                "response": "Failed: no user_id",
            }

        recipient = (
            state.meeting.participants[0] if state.meeting.participants else None
        )
        if not recipient:
            print("[send_email] error: no recipient found")
            return {
                "email": EmailData(status="failed"),
                "response": "Failed: no recipient",
            }

        subject = (
            f"Meeting Request for {state.meeting.date}"
            if state.meeting.date
            else "Meeting Request"
        )
        draft = state.email.draft or ""

        result = send_email_sync(
            sender_id=user_id,
            recipient_email=recipient,
            subject=subject,
            body=draft,
        )
        print(f"[send_email] sent: {result}")
        return {
            "email": EmailData(status="sent"),
            "response": "Email sent successfully.",
        }
    except Exception as e:
        print(f"[send_email] error: {e}")
        return {"email": EmailData(status="failed"), "response": f"Failed: {str(e)}"}


def wait_for_reply(state: AgentState, config: RunnableConfig) -> dict:
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            print("[wait_for_reply] error: no user_id in config")
            return {"email": EmailData(last_reply=None)}

        last_check = getattr(state, "last_check", None)

        result = poll_inbox_sync(user_id, last_check)
        new_emails = result.get("new_emails", [])

        if new_emails:
            latest = new_emails[0]
            mark_read_sync(latest["id"])
            reply_body = latest["body"]
            print(
                f"[wait_for_reply] received reply from {latest['sender_email']}")
            return {
                "email": EmailData(last_reply=reply_body),
                "last_check": datetime.utcnow().isoformat(),
            }

        print("[wait_for_reply] no new replies")
        return {"email": EmailData(last_reply=None)}
    except Exception as e:
        print(f"[wait_for_reply] error: {e}")
        return {"email": EmailData(last_reply=None)}


def send_followup(state: AgentState, config: RunnableConfig) -> dict:
    try:
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            print("[send_followup] error: no user_id in config")
            return {"email": EmailData(followup_count=state.email.followup_count + 1)}

        recipient = (
            state.meeting.participants[0] if state.meeting.participants else None
        )
        if not recipient:
            return {"email": EmailData(followup_count=state.email.followup_count + 1)}

        new_count = state.email.followup_count + 1
        subject = (
            f"Re: Meeting Request for {state.meeting.date}"
            if state.meeting.date
            else "Re: Meeting Request"
        )
        followup_text = (
            f"Hi,\n\n"
            f"Just following up regarding the meeting invitation I sent earlier.\n"
            f"Please let me know if the proposed time works for you.\n\n"
            f"Best regards"
        )
        result = send_email_sync(
            sender_id=user_id,
            recipient_email=recipient,
            subject=subject,
            body=followup_text,
        )
        print(f"[send_followup] follow-up #{new_count} sent")
        return {"email": EmailData(followup_count=new_count)}
    except Exception as e:
        print(f"[send_followup] error: {e}")
        return {"email": EmailData(followup_count=state.email.followup_count + 1)}


class ReplyIntentOutput(BaseModel):
    reply_intent: Literal["confirmed", "negotiate", "declined"]


def extract_reply_intent(state: AgentState) -> dict:
    reply = state.email.last_reply
    if not reply:
        return {}

    result = (
        get_llm()
        .with_structured_output(ReplyIntentOutput)
        .invoke(
            [
                {
                    "role": "system",
                    "content": (
                        "Classify the email reply intent as one of:\n"
                        "- confirmed\n- negotiate\n- declined\n"
                        "Return structured output only."
                    ),
                },
                {"role": "user", "content": reply},
            ]
        )
    )

    # type: ignore[union-attr]
    reply_intent = cast(ReplyIntentOutput, result).reply_intent
    print(f"[extract_reply_intent] intent: {reply_intent}")
    return {"email": EmailData(reply_intent=reply_intent)}


def send_notification(state: AgentState) -> dict:
    print("[send_notification] notification sent (meeting confirmed/declined)")
    return {"response": "Notification sent successfully."}
