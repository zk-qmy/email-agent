from langchain_core.tools import tool
from typing import List, Optional


@tool
def book_calendar(date: str, time: str, participants: List[str],
                  title: Optional[str] = None) -> dict:
    """
    Book a calendar event after the meeting is confirmed.
    Call ONLY after classify_reply returns intent="confirmed",
    OR when auto_calendar preference was set to True by the user earlier.
    Returns: { confirmation_id: str, booked: bool }
    """
    # Your calendar integration here
    print("PLACEHOLDER: booked calendar")
    return {"booked": True, "confirmation_id": f"CAL-{date}-{time}".replace(" ", "-")}


@tool
def set_sleep(hours: float, reason: str) -> dict:
    """
    Put the agent to sleep for N of hours.
    IMPROTANT: this tool only returns the wake_at time.
    and setting graph_Status="sleeping" and sleep_until=wake_at on state.
    DO NOT call this tool outside the agent loop.
    Returns: { sleeping: True, wake_at: str (ISO datetime) }
    """
    from datetime import datetime, timedelta
    wake_at = (datetime.now() + timedelta(hours=hours)).isoformat()
    # The graph node that executes this tool will also set graph_status="sleeping"
    # and sleep_until=wake_at on the state before returning to END.
    return {"sleeping": True, "wake_at": wake_at, "reason": reason}


@tool
def send_notification(message: str, user_id: int) -> dict:
    """
    Notify the user of the final outcome.
    ALWAYS call this as the very last action.
    Returns: { notified: bool }
    """
    print(f"[NOTIFY user={user_id}]: {message}")
    # Push notification / websocket / email to user
    return {"notified": True}
