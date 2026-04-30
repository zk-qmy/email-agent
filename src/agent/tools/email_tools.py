# tools/email_tools.py
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text
from src.integrations.mail.sync_client import send_email_sync
from config.prompts.email import meeting_prompts

from typing import List
from langchain_core.tools import tool
from langgraph.types import interrupt


def _refine_draft(rendered, previous_draft: str, feedback: str) -> str:
    """Ask LLM to refine the draft based on user feedback."""
    print(f"Previous draft: {previous_draft} \n Feedback: {feedback}")
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


@tool
def draft_email(
    recipients: List[str],
    date: str,
    time: str,
    purpose: str,
    previous_draft: str = "",
) -> str:
    """Draft a professional meeting request email, with human review + revision loop.

    Args:
        recipient: Full name or email address of the recipient(s)
        date:      Meeting date e.g. 'tomorrow', 'Monday', '2025-05-01'
        time:      Meeting time e.g. '2pm', '14:00'
        purpose:   Reason for the meeting
        previous_draft: Prior draft to refine instead of generating from scratch
    """
    print("Tools: using `draft_email`...")
    rendered = meeting_prompts.draft_email.render(
        recipients=recipients,
        date=date,
        time=time,
        purpose=purpose,
    )

    draft = previous_draft.strip() or extract_text(
        get_llm().invoke(rendered.to_prompt())
    )

    # Keep looping until user approves
    while True:
        decision = _parse_decision(
            interrupt(
                {
                    "type": "review_draft",
                    "question": (
                        f"\n📝 Draft email — review before sending:\n"
                        f"{'─' * 48}\n"
                        f"{draft}\n"
                        f"{'─' * 48}\n"
                        f"Type 'y' to approve, or give feedback to revise:"
                    ),
                    "draft": draft,
                }
            )
        )

        if decision.get("approved", False):
            return draft  # user approved, pass draft to agent

        feedback = decision.get("action_input", "").strip()
        if not feedback:
            return draft  # user said 'n' with no feedback, return as-is

        # Revise and loop back → interrupt() fires again with updated draft
        draft = _refine_draft(rendered, draft, feedback)


@tool
def send_email(user_id: str, recipients: List[str], subject: str, body: str) -> str:
    """Send an email to a recipient.

    Args:
        user_id:   Sender identifier
        recipient: Recipients' emails
        subject:   Email subject line
        body:      Full email body text
    """
    print("Tools: using `send_email` ...")
    # Human-in-the-loop for irreversible action
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
        return f"Cancelled — email to {recipients} was not sent."

    result = send_email_sync(
        sender_id=user_id,
        recipient_email=recipients,
        subject=subject,
        body=body,
    )
    print(f"[send_email] sent: {result}")
    # real send logic here (SMTP, Gmail API, etc.)
    return f"Email sent to {recipients}. Subject: {subject}"


ALL_TOOLS = [draft_email, send_email]  #, schedule_meeting]
ALL_TOOLS_BY_NAME = {tool.name: tool for tool in ALL_TOOLS}