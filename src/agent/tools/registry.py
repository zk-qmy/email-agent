from src.agent.tools.basic_email_tools import (
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
from src.agent.tools.email_mining_tools import (
    get_email_content_test,
    summarize_email,
    list_email_threads,
    get_thread_content,
    # PDF process
    parse_pdf,
    validate_pdf,
    # RAG
    suggest_department,
    ask_guide,
)


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
    list_email_threads,
    get_thread_content,
    parse_pdf,
    validate_pdf,
    # RAG
    suggest_department,
    ask_guide,
    
    # Reply analysis tool
    analyze_reply_intent,
    # Calendar tools
    check_availability,
    get_calendar_events,
    update_meeting,
    cancel_meeting,
]
ALL_TOOLS_BY_NAME = {tool.name: tool for tool in ALL_TOOLS}
