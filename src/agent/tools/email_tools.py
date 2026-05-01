# tools/email_tools.py
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text
from src.integrations.mail.sync_client import send_email_sync
from config.prompts.email import email_prompts

from typing import List
from langchain_core.tools import tool
from langgraph.types import interrupt


# PRIVATE FUNCs
def _refine_draft(rendered, previous_draft: str, feedback: str) -> str:
    """Ask LLM to refine the draft based on user feedback."""
    print("=== Feed back to LLM to refine draft ... === ")
    # print(f"Previous draft: {previous_draft} \n Feedback: {feedback}")
    return extract_text(
        get_llm().invoke(
            f"{rendered.to_prompt()}\n\n"
            f"Previous draft:\n{previous_draft}\n\n"
            f"User feedback: {feedback}\n\n"
            f"Rewrite the email applying the feedback. "
            f"Keep 'Subject: <line>' as the very first line."
        )
    )


def _parse_decision(raw) -> dict:
    """Normalise interrupt() return value to a plain dict."""
    if isinstance(raw, dict):
        return raw
    return {"approved": False, "action_input": str(raw)}


def _review_draft(draft: str) -> dict:
    """Single interrupt for draft review — shared by all draft tools."""
    decision = _parse_decision(
        interrupt(
            {
                "type": "review_draft",
                "question": (
                    f"\n📝 Draft email — review before sending:\n"
                    f"{'─' * 48}\n{draft}\n{'─' * 48}\n"
                    f"Type 'y' to approve, or give feedback to revise:"
                ),
                "draft": draft,
            }
        )
    )

    return {
        "draft": draft,
        "approved": decision.get("approved", False),
        "user_feedback": decision.get("action_input", ""),
    }


# EMAIL TOOLS


@tool
def draft_meeting_email(
    recipients: List[str],
    date: str,
    time: str,
    purpose: str,
    previous_draft: str = "",
    user_feedback: str = "",
) -> str:
    """Draft a professional meeting request email and present it to the user for review.

    Args:
        recipients:     List of recipient names
        date:           Meeting date e.g. '2025-05-02', 'Monday'
        time:           Meeting time e.g. '2pm', '14:00'
        purpose:        Reason for the meeting
        previous_draft: Prior draft to show instead of generating a new one
        user_feedback:  Feedback from user to guide the next revision
    """
    rendered = email_prompts.draft_meeting_email.render(
        recipients=recipients, date=date, time=time, purpose=purpose
    )

    if user_feedback and previous_draft:
        draft = _refine_draft(rendered, previous_draft, user_feedback)
    elif previous_draft:
        draft = previous_draft.strip()
    else:
        draft = extract_text(get_llm().invoke(rendered.to_prompt()))

    return _review_draft(draft)


@tool
def send_email(
    user_id: str,
    recipients: List[str],
    subject: str,
    body: str,
    draft_approved: bool = False,
) -> str:
    """Send an email to a recipient.
    Args:
        user_id:   Sender identifier
        recipient: Recipients' emails
        subject:   Email subject line
        body:      Full email body text
        draft_approved: Flag to skip confirmation if draft was already approved
    """
    print("Tools: using `send_email` ...")
    # Human-in-the-loop for irreversible action
    if not draft_approved:
        decision = _parse_decision(
            interrupt(
                {
                    "type": "confirm_send",
                    "question": f"Approve sending email to {recipients}?",
                    "recipient": recipients,
                    "subject": subject,
                    "body": body,
                }
            )
        )
        if not decision.get("approved", False):
            return f"=== Cancelled — email to {recipients} was not sent. ==="

    result = send_email_sync(
        sender_id=user_id,
        recipient_email=recipients,
        subject=subject,
        body=body,
    )
    print(f"=== [send_email] sent: {result}")
    # real send logic here (SMTP, Gmail API, etc.)
    return f"Email sent to {recipients}. Subject: {subject}"


# GENERAL EMAIL TOOLS


@tool
def draft_general_email(
    recipients: List[str],
    key_points: List[str],
    purpose: str,
    tone: str = "professional",
    previous_draft: str = "",
    user_feedback: str = "",
) -> str:
    """Draft a email and present it to the user for review.

    Args:
        recipients:     List of recipient names
        key_points:     List of main ideas
        purpose:        Reason for the meeting
        tone:           Tone of the email e.g 'friendly', 'professional'
        previous_draft: Prior draft to show instead of generating a new one
        user_feedback:  Feedback from user to guide the next revision
    """
    rendered = email_prompts.draft_general_email.render(
        recipients=recipients,
        key_points=key_points,
        purpose=purpose,
        tone=tone
    )

    if user_feedback and previous_draft:
        draft = _refine_draft(rendered, previous_draft, user_feedback)
    elif previous_draft:
        draft = previous_draft.strip()
    else:
        draft = extract_text(get_llm().invoke(rendered.to_prompt()))

    return _review_draft(draft)
