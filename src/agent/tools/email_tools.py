# tools/email_tools.py
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text
from src.integrations.mail.sync_client import send_email_sync
from config.prompts.email import meeting_prompts

from langchain_core.tools import tool
from langgraph.types import interrupt


def _refine_draft(rendered, current_draft: str, feedback: str) -> str:
    """Ask LLM to refine the draft based on user feedback."""
    return extract_text(get_llm().invoke(
        f"{rendered.to_prompt()}\n\n"
        f"Current draft:\n{current_draft}\n\n"
        f"User feedback: {feedback}\n\n"
        f"Rewrite the email applying the feedback. "
        f"Keep 'Subject: <line>' as the very first line."
    ))
@tool
def draft_email(recipient: str, date: str, time: str, purpose: str) -> str:
    """Draft a professional meeting request email.

    Args:
        recipient: Full name or email address of the recipient
        date:      Meeting date e.g. 'tomorrow', 'Monday', '2025-05-01'
        time:      Meeting time e.g. '2pm', '14:00'
        purpose:   Reason for the meeting
    """
    # NodePrompt handles the internal prompt structure
    rendered = meeting_prompts.draft_email.render(
        recipient=recipient, date=date,
        time=time,           purpose=purpose,
    )
    # ── Initial draft ─────────────────────────────────────────
    current_draft = extract_text(get_llm().invoke(rendered.to_prompt()))
    
    # ── Review loop ───────────────────────────────────────────
    while True:
        decision = interrupt({
            "type":        "review_draft",
            "question": (
                f"\n📝 Draft email — review before sending:\n"
                f"{'─' * 48}\n"
                f"{current_draft}\n"
                f"{'─' * 48}\n"
                f"Type 'y' to approve, or give feedback to revise:"
            ),
            "draft": current_draft,
        })
        # ── Add debug print here temporarily ─────────────────────
        print(f"DEBUG decision received: {decision}")
        # ── decision must be a dict ───────────────────────────────
        if not isinstance(decision, dict):
            # Safety fallback if somehow a plain string came through
            decision = {"approved": False, "action_input": str(decision)}

        feedback = decision.get("action_input", "").strip()
        approved = decision.get("approved", False)

        if approved and not feedback:
            break

        current_draft = _refine_draft(rendered, current_draft, feedback)

    return current_draft        


@tool
def send_email(user_id: str, recipient: str, subject: str, body: str) -> str:
    """Send an email to a recipient.

    Args:
        user_id:   Sender identifier
        recipient: Recipient email or name
        subject:   Email subject line
        body:      Full email body text
    """
    # Human-in-the-loop for irreversible action
    decision = interrupt({
        "question":   f"Approve sending email to {recipient}?",
        "recipient":  recipient,
        "subject":    subject,
        "body":       body,
    })
    if not decision.get("approved", False):
        return f"Cancelled — email to {recipient} was not sent."

    result = send_email_sync(
            sender_id=user_id,
            recipient_email=recipient,
            subject=subject,
            body=body,
        )
    print(f"[send_email] sent: {result}")
    # real send logic here (SMTP, Gmail API, etc.)
    return f"Email sent to {recipient}. Subject: {subject}"
