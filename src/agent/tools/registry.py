from src.agent.tools.email_tools import draft_email_tool, send_email_tool
from src.agent.tools.meeting_tools import schedule_meeting_tool

TOOLS: dict[str, callable] = {
    "draft_email": draft_email_tool,
    "send_email": send_email_tool,
    "schedule_meeting": schedule_meeting_tool,
}

# Auto-injected into the reasoning prompt
TOOL_DESCRIPTIONS = """
- draft_email: write a professional email
- send_email: send an email
- schedule_meeting: schedule a calendar meeting
""".strip()
