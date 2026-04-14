from langgraph.graph import END, START, StateGraph
from src.workflows.scheduling.state import ScheduleState
from src.nodes.shared.email_nodes import (
    draft_email,
    extract_reply_intent,
    process_approval,
    send_email,
    send_followup,
    send_notification,
    wait_for_reply,
)
from src.workflows.scheduling.nodes import (
    ask_for_missing_info,
    book_calendar,
    check_missing_fields,
    extract_meeting_info,
)
from config.settings import settings


def _route_missing_fields(state: ScheduleState) -> str:
    return "ask_for_missing_info" if state.meeting.missing_fields else "draft"


def _route_approval(state: ScheduleState) -> str:
    if state.email.approval_status == "approved":
        return "send_email"
    if state.email.approval_status == "edit":
        return "draft"
    return END


def _route_followup(state: ScheduleState) -> str:
    if state.email.last_reply:
        print("Reply received! Extracting intent...")
        return "extract_intent"
    if state.email.followup_count < settings.MAX_FOLLOWUP_COUNT:
        print(f"State followup_count: {state.email.followup_count}")
        print(f"Max follow-ups: {settings.MAX_FOLLOWUP_COUNT}")
        print("Send follow-up email...")
        return "followup"
    print("No reply after follow-ups. Sending notification...")
    return "send_notification"


def _route_intent(state: ScheduleState) -> str:
    if state.email.reply_intent == "confirmed":
        return "book_calendar"
    if state.email.reply_intent == "negotiate":
        return "draft"
    return "send_notification"
