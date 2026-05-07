from src.agent.tools.email_tools import (
    draft_meeting_email,
    draft_general_email,
    send_email,
    resolve_recipient,
)
from src.agent.tools.schedule_tools import schedule_meeting


ALL_TOOLS = [
    # Meeting tools
    draft_meeting_email,
    send_email,
    resolve_recipient,
    # General Email tools
    draft_general_email,
    # Book calendar
    schedule_meeting
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
