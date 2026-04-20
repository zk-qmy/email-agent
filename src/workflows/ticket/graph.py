from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime
import os
from langgraph.graph import StateGraph, START, END
from src.workflows.ticket.state import TicketState
from langgraph.graph import StateGraph
from src.workflows.ticket.nodes import (
    ai_self_correct, alert_requirement_gap,
    ask_student_for_info, draft_aa_email,
    draft_info_response, escalate_to_admin,
    extract_aa_info, extract_advisor_intent,
    extract_registrar_intent, extract_registrar_intent,
    forward_to_registrar, notify_aa_success,
    notify_aa_success, notify_aa_denied, nudge_advisor,
    nudge_registrar, nudge_registrar, process_student_approval,
    search_files_history, send_escalation_packet, send_to_advisor,
    validate_eligibility, wait_for_advisor_reply, wait_for_registrar_reply,
    wait_for_registrar_reply
)
from src.workflows.ticket.edges import (
    _route_registrar_intent, _route_workflow, _route_eligibility,
    _route_student_approval,
    _route_advisor_reply, _route_advisor_intent, _route_search_result,
    _route_registrar_reply, _route_self_correct
)


def build_ticket_graph():
    builder = StateGraph(TicketState)

    # ── Shared ──────────────────────────────────
    # builder.add_node("classify",                classify_workflow)

    # ── AA Workflow ──────────────────────────────
    builder.add_node("extract_aa_info",         extract_aa_info)
    builder.add_node("validate_eligibility",    validate_eligibility)
    builder.add_node("alert_requirement_gap",   alert_requirement_gap)
    builder.add_node("draft_aa_email",          draft_aa_email)
    builder.add_node("process_student_approval", process_student_approval)
    builder.add_node("send_to_advisor",         send_to_advisor)
    builder.add_node("wait_for_advisor_reply",  wait_for_advisor_reply)
    builder.add_node("nudge_advisor",           nudge_advisor)
    builder.add_node("send_escalation_packet",  send_escalation_packet)
    builder.add_node("extract_advisor_intent",  extract_advisor_intent)
    builder.add_node("search_files_history",    search_files_history)
    builder.add_node("draft_info_response",     draft_info_response)
    builder.add_node("ask_student_for_info",    ask_student_for_info)
    builder.add_node("notify_aa_denied",        notify_aa_denied)

    # ── Registrar Loop ───────────────────────────
    builder.add_node("forward_to_registrar",    forward_to_registrar)
    builder.add_node("wait_for_registrar_reply", wait_for_registrar_reply)
    builder.add_node("nudge_registrar",         nudge_registrar)
    builder.add_node("escalate_to_admin",       escalate_to_admin)
    builder.add_node("extract_registrar_intent", extract_registrar_intent)
    builder.add_node("notify_aa_success",       notify_aa_success)
    builder.add_node("ai_self_correct",         ai_self_correct)

    # builder.set_entry_point("classify")
    print("All nodes registered.")

    # ── Entry ────────────────────────────────────
    builder.add_edge(START, "extract_aa_info")
    '''
    builder.add_conditional_edges(
        "classify",
        _route_workflow,
        {"extract_aa_info": "extract_aa_info", END: END},
    )'''

    # ── AA info → validate ────────────────────────
    builder.add_edge("extract_aa_info", "validate_eligibility")

    builder.add_conditional_edges(
        "validate_eligibility",
        _route_eligibility,
        {"draft_aa_email": "draft_aa_email",
            "alert_requirement_gap": "alert_requirement_gap"},
    )

    builder.add_edge("alert_requirement_gap", END)

    # ── Draft → student approval ─────────────────
    builder.add_edge("draft_aa_email", "process_student_approval")

    builder.add_conditional_edges(
        "process_student_approval",
        _route_student_approval,
        {"send_to_advisor": "send_to_advisor",
         "draft_aa_email": "draft_aa_email",
         END: END,
         },
    )

    # ── Send to advisor → wait ────────────────────
    builder.add_edge("send_to_advisor", "wait_for_advisor_reply")

    builder.add_conditional_edges(
        "wait_for_advisor_reply",
        _route_advisor_reply,
        {
            "extract_advisor_intent": "extract_advisor_intent",
            "nudge_advisor": "nudge_advisor",
            "send_escalation_packet": "send_escalation_packet",
        },
    )

    builder.add_edge("nudge_advisor", "wait_for_advisor_reply")
    builder.add_edge("send_escalation_packet", END)

    builder.add_conditional_edges(
        "extract_advisor_intent",
        _route_advisor_intent,
        {
            "forward_to_registrar": "forward_to_registrar",
            "search_files_history": "search_files_history",
            "notify_aa_denied": "notify_aa_denied",
        },
    )

    builder.add_edge("notify_aa_denied", END)

    builder.add_conditional_edges(
        "search_files_history",
        _route_search_result,
        {
            "draft_info_response": "draft_info_response",
            "ask_student_for_info": "ask_student_for_info",
        },
    )

    # Both paths lead back to student approval for the updated draft
    builder.add_edge("draft_info_response",  "process_student_approval")
    builder.add_edge("ask_student_for_info", "process_student_approval")

    # ── Registrar loop ────────────────────────────
    builder.add_edge("forward_to_registrar", "wait_for_registrar_reply")

    builder.add_conditional_edges(
        "wait_for_registrar_reply",
        _route_registrar_reply,
        {
            "extract_registrar_intent": "extract_registrar_intent",
            "nudge_registrar": "nudge_registrar",
            "escalate_to_admin": "escalate_to_admin",
        },
    )

    builder.add_edge("nudge_registrar", "wait_for_registrar_reply")
    builder.add_edge("escalate_to_admin", END)

    builder.add_conditional_edges(
        "extract_registrar_intent",
        _route_registrar_intent,
        {
            "notify_aa_success": "notify_aa_success",
            "ai_self_correct": "ai_self_correct",
            "escalate_to_admin": "escalate_to_admin",
        },
    )

    builder.add_edge("notify_aa_success", END)

    builder.add_conditional_edges(
        "ai_self_correct",
        _route_self_correct,
        {
            "wait_for_registrar_reply": "wait_for_registrar_reply",
            "escalate_to_admin": "escalate_to_admin",
        },
    )

    print("All edges defined.")
    print("Graph compiled successfully.")
    return builder.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    # Print the graph to a file for visualization
    graph = build_ticket_graph()
    filename = datetime.now().strftime(
        "ticket_graph_%Y%m%d_%H%M%S.png")

    os.makedirs("assets/test_graph", exist_ok=True)
    png_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open(f"assets/test_graph/{filename}", "wb") as f:
        f.write(png_data)
    print(f"Saved to assets/test_graph/{filename}")
