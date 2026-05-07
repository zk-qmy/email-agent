from src.agent.tools.email_tools import (
    draft_meeting_email,
    draft_general_email,
    send_email,
    resolve_recipient,
    analyze_reply_intent,
)
from src.agent.tools.calendar_tools import (
    schedule_meeting,
    check_availability,
    get_calendar_events,
    update_meeting,
    cancel_meeting,
)


ALL_TOOLS = [
    # Meeting tools
    draft_meeting_email,
    send_email,
    resolve_recipient,
    # General Email tools
    draft_general_email,
    # Reply analysis tool
    analyze_reply_intent,
    # Calendar tools
    schedule_meeting,
    check_availability,
    get_calendar_events,
    update_meeting,
    cancel_meeting,
]
ALL_TOOLS_BY_NAME = {tool.name: tool for tool in ALL_TOOLS}

# TOOLS: dict[str, callable] = {
#     "draft_email": draft_email_tool,
#     "send_email": send_email_tool,
#     "schedule_meeting": schedule_meeting_tool,
# }

# # Auto-injected into the reasoning prompt
# TOOL_DESCRIPTIONS = """
# - draft_email: write a professional email
# - send_email: send an email
# - schedule_meeting: schedule a calendar meeting
# """.strip()
