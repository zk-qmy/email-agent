from pydantic import BaseModel, Field
from typing import Literal
from src.integrations.llm.client import get_llm


class ReplyIntentOutput(BaseModel):
    reply_intent: Literal["confirmed", "negotiate", "declined"] = Field(
        description="The intent of the reply: confirmed (accepts meeting), negotiate (suggests alternatives), or declined (rejects meeting)"
    )


async def reply_intent_node(state: dict) -> dict:
    email_data = state.get("email", {})
    reply = email_data.get("last_reply") if isinstance(email_data, dict) else None

    if not reply:
        return {"email": {"reply_intent": "negotiate"}}

    meeting = state.get("meeting", {})
    meeting_details = ""
    if meeting:
        subject = meeting.get("subject", "meeting")
        date = meeting.get("date")
        time = meeting.get("time")
        participants = meeting.get("participants", [])
        meeting_details = f"Meeting about '{subject}'"
        if date:
            meeting_details += f" on {date}"
        if time:
            meeting_details += f" at {time}"
        if participants:
            meeting_details += f" with {', '.join(participants)}"

    try:
        prompt = f"""Analyze this email reply to determine the sender's intent regarding the meeting request.

Meeting details: {meeting_details}

Email reply:
{reply}

Determine if the sender:
- 'confirmed': explicitly accepts the meeting (e.g., "yes", "that works", "I'll be there", "confirmed", "sounds good")
- 'negotiate': suggests alternative times/dates or asks for changes (e.g., "how about", "can we", "different time", "maybe", "alternative")
- 'declined': declines the meeting (e.g., "no", "can't", "won't work", "declines", "busy", "unable")

Return only the intent as 'confirmed', 'negotiate', or 'declined'."""

        result = await get_llm().ainvoke(prompt)

        content = result.content if hasattr(result, "content") else str(result)
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"
            )

        content_lower = content.lower().strip()

        if "confirmed" in content_lower and "declined" not in content_lower:
            reply_intent = "confirmed"
        elif "declined" in content_lower:
            reply_intent = "declined"
        else:
            reply_intent = "negotiate"



    except Exception as e:
        print(f"[reply_intent_node] LLM error: {e}")
        reply_intent = "negotiate"

    return {"email": {"reply_intent": reply_intent}}
