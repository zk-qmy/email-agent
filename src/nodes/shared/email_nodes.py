from typing import Literal
from langgraph.types import interrupt
from pydantic import BaseModel
from src.core.states import AgentState, EmailData
from src.integrations.llm.client import get_llm


def draft_email(state: AgentState) -> dict:
    meeting = state.meeting
    draft = (
        f"Subject: Meeting Request\n\n"
        f"Hi,\n\n"
        f"I would like to schedule a meeting on {meeting.date} at {meeting.time}.\n\n"
        f"Best regards"
    )
    print("[draft_email] draft created")
    return {
        "email": EmailData(draft=draft),
        "response": draft}


def process_approval(state: AgentState) -> dict:
    user_input = interrupt(
        {
            "email_draft": state.email.draft,
            "message": "Approve or request edit?",
        }
    )
    content = user_input["content"].lower()
    # TODO: USe LLM or keyword matching to determine approval status more robustly
    if any(w in content for w in ["approved", "ok", "looks good"]):
        status = "approved"
    elif "edit" in content:
        status = "edit"
    else:
        status = "pending"
    print(f"[process_approval] '{content}' → {status}")
    return {"email": EmailData(approval_status=status)}


def send_email(state: AgentState) -> dict:
    print(f"[send_email] sending:\n{state.email.draft}")
    return {
        "email": EmailData(status="sent"),
        "response": "Email sent successfully."
    }


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
    return {
        "email": EmailData(
            followup_count=new_count,
            draft=followup_text
        )
    }


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
                        "- confirmed\n"
                        "- negotiate\n"
                        "- declined\n"
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
