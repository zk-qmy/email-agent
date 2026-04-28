from langchain_core.tools import tool


@tool
def schedule_meeting(
    title: str, recipient: str, date: str, time: str, duration: int
) -> str:
    """Schedule a calendar meeting.

    Args:
        title:     Meeting title
        recipient: Attendee name or email
        date:      Meeting date
        time:      Meeting time
        duration:  Duration in minutes
    """
    return (
        f"Meeting scheduled.\n"
        f"  Title:    {title}\n"
        f"  With:     {recipient}\n"
        f"  Date:     {date}\n"
        f"  Time:     {time}\n"
        f"  Duration: {duration} min"
    )
