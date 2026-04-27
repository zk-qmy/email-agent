# src/tools/human_tools.py
from typing import List, Optional
from langchain_core.tools import tool
from langgraph.types import interrupt
from typing import Optional, Literal


@tool
def ask_human(question: str,
              context: Optional[str] = None,
              question_type: Literal["approval", "clarification", "preference"] = "clarification") -> dict:
    """
    Ask the human a question and wait for their response.


    WHEN TO CALL THIS:
    - Before sending any email (question_type="approval") — show the draft
    - When required info is missing and cannot be inferred (question_type="clarification")
    - When you want to confirm user preferences for automatic actions like
      followup emails or calendar booking (question_type="preference")


    DO NOT call this for things you can determine yourself:
    - Do not ask "should I draft the email?" — just draft it
    - Do not ask "what tone?" — use professional tone by default
    - Do not ask for permission to check the inbox — just check it


    context: show the user relevant content, e.g. the email draft
    Returns: { response: str, approved: bool }
    """
    reply = interrupt({
        "type":          question_type,
        "message":       question,
        "context":       context,
    })
    content = reply.get("content", "") if isinstance(
        reply, dict) else str(reply)
    approved = any(w in content.lower()
                   for w in ["yes", "ok", "approved", "looks good", "send", "confirm", "go ahead"])
    return {"response": content, "approved": approved}
