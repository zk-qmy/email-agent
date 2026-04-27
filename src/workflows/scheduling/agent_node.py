# src/workflows/scheduling/agent_node.py
from datetime import datetime
from .state import ScheduleState
from src.tools.calendar_tools import (
    book_calendar, set_sleep, send_notification
    )
from src.tools.human_tools import ask_human
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage, SystemMessage
from src.tools.scheduling_tools import (
    extract_meeting_info, get_recipient_email)
from src.tools.email_tools import (
    draft_email, send_email, check_inbox,
    classify_reply, send_followup
    )


ALL_TOOLS = [
    extract_meeting_info, get_recipient_email,
    draft_email, send_email, check_inbox, classify_reply, send_followup,
    ask_human, book_calendar, set_sleep, send_notification,
]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


SYSTEM_PROMPT = """
You are an autonomous scheduling assistant. Your job is to help users schedule meetings
by reasoning about what needs to happen next and taking action.


You have tools available. Use them. Do not ask permission for actions you can do yourself.


WHEN TO USE ask_human:
  - Before sending any email: show the draft and ask for approval.
  - When critical info is missing and cannot be inferred.
  - When you want to confirm whether to handle followup/calendar automatically.
  Do NOT ask for anything else. Do not ask permission to draft, to check inbox,
  to classify a reply, or to look up an email address.


HANDLING USER PREFERENCES:
  When the user says "yes, send followup automatically" or "yes, book calendar too",
  remember this for the rest of the session. Do not ask again.
  If auto_followup is True in state, send followup without asking.
  If auto_calendar is True in state, book calendar without asking.


WAITING FOR REPLIES:
  After sending an email, call set_sleep(hours=24, reason="waiting for reply").
  This saves your state and puts you to sleep. You will be woken when a reply arrives
  or after 24 hours, whichever is first.


Current user ID: {user_id}
Current session: {session_id}
Current time: {now}


State summary: auto_followup={auto_followup}, auto_calendar={auto_calendar},
followup_count={followup_count}
"""


def get_llm_with_tools():
    from src.integrations.llm.client import get_llm
    return get_llm().bind_tools(ALL_TOOLS)


async def agent_node(state: ScheduleState) -> dict:
    """
    The entire reasoning loop in one node.
    The LLM sees all messages (including previous tool results),
    reasons about the situation, and decides what tool to call next.
    """
    system = SystemMessage(content=SYSTEM_PROMPT.format(
        user_id=state.user_id,
        session_id=state.session_id,
        now=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        auto_followup=state.auto_followup,
        auto_calendar=state.auto_calendar,
        followup_count=state.followup_count,
    ))

    llm = get_llm_with_tools()
    messages = [system] + list(state.messages)

    # ── LLM reasons and decides what to do ──
    response = await llm.ainvoke(messages)

    updates = {"messages": [response]}

    # ── No tool call: agent is done reasoning ──
    if not response.tool_calls:
        return {**updates, "graph_status": "completed"}

    # ── Execute each tool call ──
    tool_results = []
    for tc in response.tool_calls:
        tool = TOOL_MAP.get(tc["name"])
        if not tool:
            tool_results.append(ToolMessage(
                content=f"Error: unknown tool {tc['name']}",
                tool_call_id=tc["id"],
            ))
            continue

        # ask_human calls interrupt() inside — this pauses the whole graph
        result = await tool.ainvoke(tc["args"])
        tool_results.append(ToolMessage(
            content=str(result),
            tool_call_id=tc["id"],
            name=tc["name"],
        ))

        # ── Side effects: update state based on tool results ──
        if tc["name"] == "set_sleep" and isinstance(result, dict):
            updates["graph_status"] = "sleeping"
            updates["sleep_until"] = result.get("wake_at")

        if tc["name"] == "send_email" and isinstance(result, dict):
            if result.get("status") == "sent":
                updates["last_sent_at"] = result.get("sent_at")

        if tc["name"] == "send_followup":
            updates["followup_count"] = state.followup_count + 1

        # ── Parse user preferences from ask_human responses ──
        if tc["name"] == "ask_human" and isinstance(result, dict):
            response_text = result.get("response", "").lower()
            if any(w in response_text for w in ["follow", "followup", "follow up"]):
                updates["auto_followup"] = True
            if any(w in response_text for w in ["calendar", "book", "schedule"]):
                updates["auto_calendar"] = True

    updates["messages"] = updates.get("messages", [response]) + tool_results
    return updates
