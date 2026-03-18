from typing import Literal, Optional
from langgraph.types import interrupt
from pydantic import BaseModel
from src.core.states import AgentState, EmailData
from src.integrations.llm.client import get_llm
from src.integrations.mail.client import mail_client
from datetime import datetime


def draft_email(state: AgentState) -> dict:
    meeting = state.meeting
    recipient = meeting.participants[0] if meeting.participants else "recipient@example.com"
    subject = f"Meeting Request for {meeting.date}" if meeting.date else "Meeting Request"
    draft = (
        f"Hi,\n\n"
        f"I would like to schedule a meeting on {meeting.date} at {meeting.time}.\n\n"
        f"Best regards"
    )
    print(f"[draft_email] draft created for {recipient}")
    return {
        "email": EmailData(draft=draft, approval_status="pending"),
        "response": f"Subject: {subject}\n\n{draft}",
    }


def process_approval(state: AgentState) -> dict:
    email_draft = state.email.draft or "No draft available"
    
    user_input = interrupt({
        "type": "approval",
        "message": "Please review and approve this email draft, or request edits.",
        "email_draft": email_draft,
        "missing_fields": [],
        "data": {
            "recipient": state.meeting.participants[0] if state.meeting.participants else None,
            "subject": f"Meeting Request for {state.meeting.date}" if state.meeting.date else "Meeting Request",
        }
    })
    
    content = user_input.get("content", "").lower() if isinstance(user_input, dict) else str(user_input).lower()
    
    if any(w in content for w in ["approved", "ok", "looks good", "yes", "send"]):
        status = "approved"
    elif "edit" in content:
        status = "edit"
    else:
        status = "pending"
    
    print(f"[process_approval] '{content}' → {status}")
    return {"email": EmailData(approval_status=status)}


def send_email(state: AgentState) -> dict:
    try:
        if not state.user_id:
            print("[send_email] error: no user_id in state")
            return {"email": EmailData(status="failed"), "response": "Failed: no user_id"}

        recipient = state.meeting.participants[0] if state.meeting.participants else None
        if not recipient:
            print("[send_email] error: no recipient found")
            return {"email": EmailData(status="failed"), "response": "Failed: no recipient"}

        subject = f"Meeting Request for {state.meeting.date}" if state.meeting.date else "Meeting Request"
        draft = state.email.draft or ""
        
        result = mail_client.send_email(
            sender_id=state.user_id,
            recipient_email=recipient,
            subject=subject,
            body=draft,
        )
        print(f"[send_email] sent: {result}")
        return {"email": EmailData(status="sent"), "response": "Email sent successfully."}
    except Exception as e:
        print(f"[send_email] error: {e}")
        return {"email": EmailData(status="failed"), "response": f"Failed: {str(e)}"}


def wait_for_reply(state: AgentState) -> dict:
    print("[wait_for_reply] no reply received (placeholder)")
    return {"email": EmailData(last_reply=None)}


def send_followup(state: AgentState) -> dict:
    followup_text = (
        "Hi again,\n\n"
        "Just following up regarding the meeting invitation.\n"
        "Please let me know if the proposed time works.\n\n"
        "Best,"
    )
    new_count = state.email.followup_count + 1
    print(f"[send_followup] follow-up #{new_count}")
    return {"email": EmailData(followup_count=new_count, draft=followup_text)}


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
    print(f"[extract_reply_intent] intent: {result.reply_intent}")
    return {"email": EmailData(reply_intent=result.reply_intent)}


def send_notification(state: AgentState) -> dict:
    print("[send_notification] notification sent (placeholder)")
    return {"response": "Notification sent successfully."}
