from datetime import datetime, timedelta
from typing import Optional, List
from langchain_core.tools import tool

from src.integrations.calendar.sync_client import (
    create_event_sync,
    get_events_sync,
    get_event_sync,
    update_event_sync,
    delete_event_sync,
    check_availability_sync,
)


@tool
def check_availability(
    user_id: int,
    date: str,
    time: str,
    duration_minutes: int = 60,
) -> str:
    """Check if a time slot is available for scheduling.

    Args:
        user_id: The user's ID
        date: Date in ISO format (YYYY-MM-DD) or readable format (e.g., "2025-05-15")
        time: Time in HH:MM format (e.g., "14:00")
        duration_minutes: Meeting duration in minutes (default 60)
    """
    try:
        start_dt = datetime.fromisoformat(f"{date}T{time}")
    except ValueError:
        try:
            parsed = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            start_dt = parsed
        except ValueError:
            return "Error: Please provide date in YYYY-MM-DD format and time in HH:MM format."

    result = check_availability_sync(user_id, start_dt, duration_minutes)

    if "error" in result:
        return f"Error checking availability: {result.get('error', 'Unknown error')}"

    if result.get("available"):
        return (
            f"Time slot is available!\n"
            f"  Date: {date}\n"
            f"  Time: {time}\n"
            f"  Duration: {duration_minutes} minutes"
        )

    conflicts = result.get("conflicts", [])
    conflict_details = []
    for c in conflicts:
        start = c.get("start_time", "")[11:16] if c.get("start_time") else "?"
        end = c.get("end_time", "")[11:16] if c.get("end_time") else "?"
        conflict_details.append(f"  - {c.get('title', 'Busy')} ({start} - {end})")

    return (
        f"Time slot is NOT available.\n"
        f"  Requested: {date} {time} for {duration_minutes} min\n"
        f"Conflicts:\n" + "\n".join(conflict_details)
    )


@tool
def schedule_meeting(
    user_id: int,
    title: str,
    date: str,
    time: str,
    duration_minutes: int = 60,
    description: Optional[str] = None,
    attendee_ids: Optional[List[int]] = None,
    location: Optional[str] = None,
) -> str:
    """Schedule a calendar meeting with automatic availability check.

    Args:
        user_id: The organizer's user ID
        title: Meeting title
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (e.g., "14:00")
        duration_minutes: Meeting duration in minutes (default 60)
        description: Optional meeting description
        attendee_ids: List of attendee user IDs
        location: Optional location/room
    """
    try:
        start_dt = datetime.fromisoformat(f"{date}T{time}")
    except ValueError:
        return "Error: Please provide date in YYYY-MM-DD format and time in HH:MM format."

    end_dt = start_dt + timedelta(minutes=duration_minutes)

    availability = check_availability_sync(user_id, start_dt, duration_minutes)

    if "error" in availability:
        return f"Error checking availability: {availability.get('error', 'Unknown error')}"

    if not availability.get("available"):
        conflicts = availability.get("conflicts", [])
        conflict_list = []
        for c in conflicts:
            start = c.get("start_time", "")[11:16] if c.get("start_time") else "?"
            end = c.get("end_time", "")[11:16] if c.get("end_time") else "?"
            conflict_list.append(f"- {c.get('title', 'Busy')} ({start}-{end})")

        return (
            f"Cannot schedule meeting - time slot is busy.\n"
            f"  Requested: {date} {time} ({duration_minutes} min)\n"
            f"Conflicts:\n" + "\n".join(conflict_list) + "\n\n"
            f"Please suggest a different time."
        )

    result = create_event_sync(
        organizer_id=user_id,
        title=title,
        start_time=start_dt,
        end_time=end_dt,
        description=description,
        attendee_ids=attendee_ids,
        location=location,
    )

    if "error" in result or "event" not in result:
        return f"Error creating meeting: {result.get('error', 'Failed to create event')}"

    event = result.get("event", {})
    start_time = event.get("start_time", "")
    end_time = event.get("end_time", "")

    start_display = start_time[11:16] if start_time else ""
    end_display = end_time[11:16] if end_time else ""

    return (
        f"Meeting scheduled successfully!\n"
        f"  Title: {title}\n"
        f"  Date: {date}\n"
        f"  Time: {start_display} - {end_display}\n"
        f"  Duration: {duration_minutes} min\n"
        f"  Event ID: {event.get('id')}"
    )


@tool
def get_calendar_events(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Get upcoming calendar events for a user.

    Args:
        user_id: The user's ID
        start_date: Start date in YYYY-MM-DD format (optional, defaults to today)
        end_date: End date in YYYY-MM-DD format (optional)
        limit: Maximum number of events to return (default 10)
    """
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            return f"Error: Invalid start_date format. Use YYYY-MM-DD"
    else:
        start_dt = datetime.now()

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            return f"Error: Invalid end_date format. Use YYYY-MM-DD"

    result = get_events_sync(user_id, start_dt, end_dt)

    if "error" in result:
        return f"Error fetching events: {result.get('error', 'Unknown error')}"

    events = result.get("events", [])

    if not events:
        return f"No events found for the specified period."

    limited_events = events[:limit]

    event_list = []
    for e in limited_events:
        start = e.get("start_time", "")[:10] if e.get("start_time") else "?"
        time_start = e.get("start_time", "")[11:16] if e.get("start_time") else "?"
        time_end = e.get("end_time", "")[11:16] if e.get("end_time") else "?"
        event_list.append(
            f"  {e.get('id')}: {e.get('title', 'No title')} ({start} {time_start}-{time_end})"
        )

    return (
        f"Upcoming events (showing {len(limited_events)} of {len(events)}):\n"
        + "\n".join(event_list)
    )


@tool
def update_meeting(
    event_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    attendee_ids: Optional[List[int]] = None,
    location: Optional[str] = None,
) -> str:
    """Update an existing calendar meeting.

    Args:
        event_id: The event ID to update
        title: New meeting title
        description: New description
        date: New date in YYYY-MM-DD format
        time: New start time in HH:MM format
        duration_minutes: New duration in minutes
        attendee_ids: New list of attendee IDs
        location: New location
    """
    get_result = get_event_sync(event_id)

    if "error" in get_result or "event" not in get_result:
        return f"Error: Event {event_id} not found."

    event = get_result.get("event", {})

    start_time = event.get("start_time")
    end_time = event.get("end_time")

    new_start = None
    new_end = None

    if date or time:
        try:
            if start_time:
                if date and time:
                    new_start = datetime.fromisoformat(f"{date}T{time}")
                elif date:
                    new_start = datetime.fromisoformat(f"{date}T{start_time[11:16]}")
                elif time:
                    new_start = datetime.fromisoformat(f"{start_time[:10]}T{time}")
        except ValueError:
            return "Error: Invalid date/time format. Use YYYY-MM-DD and HH:MM"

    if duration_minutes and new_start:
        new_end = new_start + timedelta(minutes=duration_minutes)
    elif new_start and end_time:
        old_duration = (
            datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)
        ).total_seconds() / 60
        new_end = new_start + timedelta(minutes=int(old_duration))
    elif end_time and date:
        new_end = datetime.fromisoformat(end_time)

    if new_start and new_end:
        availability = check_availability_sync(
            event.get("organizer_id"), new_start, int((new_end - new_start).total_seconds() / 60)
        )
        if not availability.get("available"):
            return f"Error: New time slot is not available. Please choose a different time."

    result = update_event_sync(
        event_id=event_id,
        title=title,
        description=description,
        start_time=new_start,
        end_time=new_end,
        attendee_ids=attendee_ids,
        location=location,
    )

    if "error" in result:
        return f"Error updating meeting: {result.get('error', 'Unknown error')}"

    return f"Meeting updated successfully! Event ID: {event_id}"


@tool
def cancel_meeting(event_id: int) -> str:
    """Cancel and delete a calendar meeting.

    Args:
        event_id: The event ID to cancel/delete
    """
    result = delete_event_sync(event_id)

    if "error" in result:
        return f"Error cancelling meeting: {result.get('error', 'Unknown error')}"

    return f"Meeting cancelled successfully. Event ID {event_id} has been deleted."