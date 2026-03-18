from langgraph.graph import END, START, StateGraph
from src.core.states import AgentState
from src.nodes.shared.email_nodes import (
    draft_email,
    extract_reply_intent,
    process_approval,
    send_email,
    send_followup,
    send_notification,
    wait_for_reply,
)
from src.nodes.specialized.meeting_nodes import (
    ask_for_missing_info,
    book_calendar,
    check_missing_fields,
    extract_meeting_info,
)
from config.settings import settings


def _route_missing_fields(state: AgentState) -> str:
    return "ask_for_missing_info" if state.meeting.missing_fields else "draft"


def _route_approval(state: AgentState) -> str:
    if state.email.approval_status == "approved":
        return "send_email"
    if state.email.approval_status == "edit":
        return "draft"
    return END


def _route_after_wait(state: AgentState) -> str:
    if state.email.last_reply:
        return "extract_intent"
    if state.email.followup_count < settings.MAX_FOLLOWUP_COUNT:
        return "followup"
    return "send_notification"


def _route_intent(state: AgentState) -> str:
    if state.email.reply_intent == "confirmed":
        return "book_calendar"
    if state.email.reply_intent == "negotiate":
        return "draft"
    return "send_notification"


def build_meeting_graph():
    """Compiled meeting subgraph. No checkpointer — parent router owns it."""
    builder = StateGraph(AgentState)

    builder.add_node("extract_meeting_info", extract_meeting_info)
    builder.add_node("check_missing_fields", check_missing_fields)
    builder.add_node("ask_for_missing_info", ask_for_missing_info)
    builder.add_node("draft", draft_email)
    builder.add_node("process_approval", process_approval)
    builder.add_node("send_email", send_email)
    builder.add_node("wait_reply", wait_for_reply)
    builder.add_node("followup", send_followup)
    builder.add_node("extract_intent", extract_reply_intent)
    builder.add_node("book_calendar", book_calendar)
    builder.add_node("send_notification", send_notification)

    builder.add_edge(START, "extract_meeting_info")
    builder.add_edge("extract_meeting_info", "check_missing_fields")
    builder.add_conditional_edges(
        "check_missing_fields",
        _route_missing_fields,
        {"ask_for_missing_info": "ask_for_missing_info", "draft": "draft"},
    )
    builder.add_edge("ask_for_missing_info", "extract_meeting_info")
    builder.add_edge("draft", "process_approval")
    builder.add_conditional_edges(
        "process_approval",
        _route_approval,
        {"send_email": "send_email", "draft": "draft", END: END},
    )
    builder.add_edge("send_email", "wait_reply")
    builder.add_conditional_edges(
        "wait_reply",
        _route_after_wait,
        {
            "extract_intent": "extract_intent",
            "followup": "followup",
            "send_notification": "send_notification",
        },
    )
    builder.add_edge("followup", "wait_reply")
    builder.add_conditional_edges(
        "extract_intent",
        _route_intent,
        {
            "book_calendar": "book_calendar",
            "draft": "draft",
            "send_notification": "send_notification",
        },
    )
    builder.add_edge("book_calendar", "send_notification")
    builder.add_edge("send_notification", END)

    return builder.compile()
