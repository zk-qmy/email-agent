from src.agent.tools.basic_email_tools import (
    draft_meeting_email,
    draft_general_email,
    send_email,
    resolve_recipient,
)
from src.agent.tools.email_mining_tools import (
    get_email_content_test,
    summarize_email,
    # PDF process
    parse_pdf,
    validate_pdf,
    # RAG
    suggest_department,
    ask_guide,
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
    schedule_meeting,
    # Email mining
    get_email_content_test,
    summarize_email,
    parse_pdf,
    validate_pdf,
    # RAG
    suggest_department,
    ask_guide,
    
]
ALL_TOOLS_BY_NAME = {tool.name: tool for tool in ALL_TOOLS}
