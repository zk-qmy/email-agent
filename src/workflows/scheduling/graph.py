

from datetime import datetime
import os
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from src.workflows.scheduling.edges import (
    _route_approval, _route_followup, _route_intent,
    _route_missing_fields, _route_intent, _route_followup,
    _route_missing_fields
)
from src.workflows.scheduling.nodes import (
    ask_for_missing_info, book_calendar, book_calendar,
    check_missing_fields, extract_meeting_info, extract_meeting_info
)
from src.workflows.scheduling.state import ScheduleState
from src.nodes.shared.email_nodes import (
    draft_email,
    extract_reply_intent,
    extract_reply_intent,
    process_approval,
    send_email,
    send_followup,
    send_notification,
    wait_for_reply
)


def build_meeting_graph():
    """Compiled meeting subgraph. No checkpointer — parent router owns it."""
    builder = StateGraph(ScheduleState)

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
        {
            "ask_for_missing_info": "ask_for_missing_info",
            "draft": "draft"
        },
    )
    builder.add_edge("ask_for_missing_info", "extract_meeting_info")
    builder.add_edge("draft", "process_approval")
    builder.add_conditional_edges(
        "process_approval",
        _route_approval,
        {
            "send_email": "send_email",
            "draft": "draft",
            END: END
        },
    )
    builder.add_edge("send_email", "wait_reply")
    builder.add_conditional_edges(
        "wait_reply",
        _route_followup,
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

    return builder.compile(checkpointer=MemorySaver())


# if __name__ == "__main__":
#     # Print the graph to a file for visualization
#     # graph = build_meeting_graph()
#     # filename = datetime.now().strftime(
#     #     "scheduling_graph_%Y%m%d_%H%M%S.png")

#     # os.makedirs("assets/test_graph", exist_ok=True)
#     # png_data = graph.get_graph(xray=True).draw_mermaid_png()
#     # with open(f"assets/test_graph/{filename}", "wb") as f:
#     #     f.write(png_data)
#     # print(f"Saved to assets/test_graph/{filename}")
