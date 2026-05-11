# tools/email_tools.py
import json
import os
from datetime import datetime
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text
from src.integrations.mail.sync_client import send_email_sync
from config.tool_prompts.email import email_prompts

from typing import List, Optional
from langchain_core.tools import tool
from langgraph.types import interrupt


# PRIVATE FUNCs
async def _refine_draft(rendered, previous_draft: str, feedback: str) -> str:
    """Ask LLM to refine the draft based on user feedback."""
    print("=== Feed back to LLM to refine draft ... === ")
    return extract_text(
        await get_llm().ainvoke(
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
        if "response" in raw:
            response = raw.get("response", "").strip().lower()
            if response == "y":
                return {"approved": True, "action_input": ""}
            else:
                return {"approved": False, "action_input": raw.get("response", "")}
        return raw
    return {"approved": False, "action_input": str(raw)}


async def _normalize_datetime(date: str, time: str) -> tuple[str, str]:
    """Normalize date and time to YYYY-MM-DD and HH:MM format using LLM."""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        prompt = f"""Today's date: {today}

Convert the following date and time to standard formats:
Date: {date}
Time: {time}

Return ONLY a JSON object with normalized "date" and "time" fields:
- date: YYYY-MM-DD format (e.g., "{today}")
- time: HH:MM format in 24-hour (e.g., "14:00", not "2pm")

If the input is already normalized, return as-is.
For relative dates like "tomorrow", "next Monday", calculate the actual date using today's date as reference.
For times like "2pm", "3:30pm", convert to 24-hour format."""

        result = await get_llm().ainvoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"
            )
        import re
        match = re.search(r'\{[^}]+"date"\s*:\s*"([^"]+)"[^}]+"time"\s*:\s*"([^"]+)"', content, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
    except Exception as e:
        print(f"[_normalize_datetime] Error: {e}")
    return date, time


def _review_draft(
    draft: str,
    recipient: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    meeting_date: str = None,
    meeting_time: str = None,
    purpose: str = None,
) -> dict:
    """Single interrupt for draft review — shared by all draft tools."""
    cc_line = f"\nCC: {', '.join(cc)}" if cc else ""
    bcc_line = f"\nBCC: {', '.join(bcc)}" if bcc else ""
    recipients_block = f"To: {recipient}{cc_line}{bcc_line}\n"
    decision = _parse_decision(
        interrupt(
            {
                "type": "review_draft",
                "question": (
                    f"\n📝 Draft email — review before sending:\n"
                    f"{'─' * 48}\n{recipients_block}\n{draft}\n{'─' * 48}\n"
                    f"Type 'y' to approve, or give feedback to revise:"
                ),
                "draft": draft,
                "recipient": recipient,
"cc": cc,
                "bcc": bcc,
                "meeting_date": meeting_date,
                "meeting_time": meeting_time,
                "purpose": purpose,
            }
        )
    )

    return {
        "draft": draft,
        "approved": decision.get("approved", False),
        "user_feedback": decision.get("action_input", ""),
"draft": draft,
        "approved": decision.get("approved", False),
        "user_feedback": decision.get("action_input", ""),
        "cc": cc,
        "bcc": bcc,
        "meeting_date": meeting_date,
        "meeting_time": meeting_time,
        "purpose": purpose,
    }


BACKEND_URL = os.getenv("EMAIL_BACKEND_URL", "http://127.0.0.1:5001")


@tool
def resolve_recipient(name: str) -> str:
    """Look up recipient email by name with fuzzy search.

    Args:
        name: Recipient's name (username, partial name, or email)

    Returns:
        Email address if found, or error message asking user to clarify.
    """
    import httpx

    print(f"=== resolve_recipient: looking up '{name}' ===")

    if "@" in name:
        return f'{{"email": "{name}"}}'

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{BACKEND_URL}/api/auth/search-users", params={"q": name})
            if response.status_code != 200:
                return "Failed to search users. Please provide email directly."
            users = response.json().get("users", [])
            if not users:
                return f"User '{name}' not found. Please provide email directly."
            if len(users) == 1:
                return f'{{"email": "{users[0]["email"]}", "username": "{users[0]["username"]}"}}'
            options = [f"{u['username']} ({u['email']})" for u in users]
            return f"Multiple matches found: {', '.join(options)}. Please specify which one."
    except Exception as e:
        return f"Failed to resolve recipient: {str(e)}. Please provide email directly."


# EMAIL TOOLS


@tool
async def draft_meeting_email(
    recipient: str,
    date: str,
    time: str,
    purpose: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    previous_draft: str = "",
    user_feedback: str = "",
) -> str:
    """Draft a professional meeting request email and present it to the user for review.

    Args:
        recipient:     Recipient's name
        date:           Meeting date e.g. '2025-05-02', 'Monday'
        time:           Meeting time e.g. '2pm', '14:00'
        purpose:        Reason for the meeting
        cc:             List of CC email addresses (optional)
        bcc:            List of BCC email addresses (optional)
        previous_draft: Prior draft to show instead of generating a new one
        user_feedback:  Feedback from user to guide the next revision
    """
    normalized_date, normalized_time = await _normalize_datetime(date, time)

    rendered = email_prompts.draft_meeting_email.render(
        recipient=recipient, date=normalized_date, time=normalized_time, purpose=purpose
    )

    if user_feedback and previous_draft:
        draft = await _refine_draft(rendered, previous_draft, user_feedback)
    elif previous_draft:
        draft = previous_draft.strip()
    else:
        draft = extract_text(await get_llm().ainvoke(rendered.to_prompt()))

    return _review_draft(draft, recipient, cc=cc, bcc=bcc, meeting_date=normalized_date, meeting_time=normalized_time, purpose=purpose)


@tool
def send_email(
    user_id: int,
    recipient: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    draft_approved: bool = False,
) -> str:
    """Send an email to a recipient.
    Args:
        user_id:   Sender's user ID (integer)
        recipient: Recipient's email address
        subject:   Email subject line
        body:      Full email body text
        cc:        List of CC email addresses (optional)
        bcc:       List of BCC email addresses (optional)
        draft_approved: Flag to skip confirmation if draft was already approved
    """
    print("Tools: using `send_email` ...")

    result = send_email_sync(
        sender_id=user_id,
        recipient_email=recipient,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
    )
    print(f"=== [send_email] sent: {result}")
    parts = [f"Email sent to {recipient}"]
    if cc:
        parts.append(f"CC: {', '.join(cc)}")
    if bcc:
        parts.append(f"BCC: {', '.join(bcc)}")
    parts.append(f"Subject: {subject}")
    return ". ".join(parts)


# GENERAL EMAIL TOOLS


@tool
async def draft_general_email(
    recipient: str,
    key_points: List[str],
    purpose: str,
    tone: str = "professional",
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    previous_draft: str = "",
    user_feedback: str = "",
) -> str:
    """Draft a email and present it to the user for review.

    Args:
        recipient:     Recipient's name
        key_points:     List of main ideas
        purpose:        Reason for the meeting
        tone:           Tone of the email e.g 'friendly', 'professional'
        cc:             List of CC email addresses (optional)
        bcc:            List of BCC email addresses (optional)
        previous_draft: Prior draft to show instead of generating a new one
        user_feedback:  Feedback from user to guide the next revision
    """
    rendered = email_prompts.draft_general_email.render(
        recipient=recipient,
        key_points=key_points,
        purpose=purpose,
        tone=tone
    )

    if user_feedback and previous_draft:
        draft = await _refine_draft(rendered, previous_draft, user_feedback)
    elif previous_draft:
        draft = previous_draft.strip()
    else:
        draft = extract_text(await get_llm().ainvoke(rendered.to_prompt()))

    return _review_draft(draft, recipient, cc=cc, bcc=bcc)


@tool
def analyze_reply_intent(reply_body: str, meeting_details: str) -> str:
    """Analyze a reply email to determine the sender's intent regarding the meeting.

    Args:
        reply_body: The full text content of the reply email
        meeting_details: Summary of the meeting that was proposed (date, time, purpose, recipient)

    Returns:
        JSON string with reply_intent ('confirmed', 'negotiate', or 'declined') and reason
    """
    print("=== analyze_reply_intent: analyzing reply ===")

    prompt = f"""You are analyzing a reply to a meeting request email.

Meeting details:
{meeting_details}

Reply email content:
{reply_body}

Determine the sender's intent by analyzing the reply content:
- 'confirmed': The sender explicitly accepts the meeting (e.g., "yes", "that works", "I'll be there", "confirmed")
- 'negotiate': The sender suggests alternative times/dates or asks for changes (e.g., "how about", "can we", "different time", "maybe")
- 'declined': The sender declines the meeting (e.g., "no", "can't", "won't work", "declines", "busy")
- If unclear, default to 'negotiate'

Output ONLY valid JSON with this exact format:
{{"reply_intent": "confirmed|negotiate|declined", "reason": "brief explanation"}}"""

    try:
        result = extract_text(get_llm().invoke(prompt))
        parsed = json.loads(result)
        if parsed.get("reply_intent") in ("confirmed", "negotiate", "declined"):
            return json.dumps(parsed)
        return json.dumps({"reply_intent": "negotiate", "reason": "Could not determine intent, defaulting to negotiate"})
    except Exception as e:
        print(f"[analyze_reply_intent] Error: {e}")
        return json.dumps({"reply_intent": "negotiate", "reason": f"Error: {str(e)}"})
