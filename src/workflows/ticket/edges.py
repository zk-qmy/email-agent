from langgraph.graph import END
from src.workflows.ticket.state import TicketState


# ── Route after classify ─────────────────────
def _route_workflow(state: TicketState):
    if state.workflow == "ticket":
        return "extract_aa_info"
    # schedule / chat branches not implemented here — return END
    return END
# ── Route after eligibility check ────────────


def _route_eligibility(state: TicketState):
    if state.ticket_request.is_eligible:
        return "draft_aa_email"
    return "alert_requirement_gap"

# ── Route after student approval ─────────────


def _route_student_approval(state: TicketState):
    if state.aa_email.approval_status == "approved":
        return "send_to_advisor"
    elif state.aa_email.approval_status == "cancelled":
        print("Student cancelled the request.")
        return END
    # edit or pending → redraft
    return "draft_aa_email"


# ── Route after waiting for advisor ──────────
# TODO: add to config
MAX_ADVISOR_NUDGES = 3


def _route_advisor_reply(state: TicketState):
    if state.aa_email.last_reply:
        return "extract_advisor_intent"
    # Timeout path
    if state.aa_email.nudge_count < MAX_ADVISOR_NUDGES:
        return "nudge_advisor"
    return "send_escalation_packet"

# ── Route advisor intent ──────────────────────


def _route_advisor_intent(state: TicketState):
    intent = state.aa_email.reply_intent
    if intent == "approved":
        return "forward_to_registrar"
    elif intent == "needs_info":
        return "search_files_history"
    elif intent == "rejected":
        return "notify_aa_denied"
    # Fallback
    return "notify_aa_denied"

# ── Search files → draft or ask student ──────


def _route_search_result(state: TicketState):
    if state.aa_email.search_result == "found":
        return "draft_info_response"
    return "ask_student_for_info"


# TODO: add to config
MAX_REGISTRAR_NUDGES = 3


def _route_registrar_reply(state: TicketState):
    if state.registrar_email.last_reply:
        return "extract_registrar_intent"
    if state.registrar_email.nudge_count < MAX_REGISTRAR_NUDGES:
        return "nudge_registrar"
    return "escalate_to_admin"

# ── Route registrar intent ────────────────────


def _route_registrar_intent(state: TicketState):
    intent = state.registrar_email.reply_intent
    if intent == "approved":
        return "notify_aa_success"
    elif intent == "issue_detected":
        return "ai_self_correct"
    return "escalate_to_admin"

# ── Self-correct branch ───────────────────────


def _route_self_correct(state: TicketState):
    if state.registrar_email.self_correct_result == "fixed":
        # Re-enter the registrar wait loop with the corrected submission
        return "wait_for_registrar_reply"
    return "escalate_to_admin"

