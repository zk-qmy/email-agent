import asyncio
import nest_asyncio
from typing import Optional, List
from datetime import datetime

try:
    nest_asyncio.apply()
except ValueError:
    pass

from src.integrations.calendar.client import CalendarClient


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def create_event_sync(
    organizer_id: int,
    title: str,
    start_time: datetime,
    end_time: datetime,
    description: Optional[str] = None,
    attendee_ids: Optional[List[int]] = None,
    location: Optional[str] = None,
):
    client = CalendarClient()
    return _run_async(
        client.create_event(
            organizer_id=organizer_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            attendee_ids=attendee_ids,
            location=location,
        )
    )


def get_events_sync(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    client = CalendarClient()
    return _run_async(client.get_events(user_id, start_date, end_date))


def get_event_sync(event_id: int):
    client = CalendarClient()
    return _run_async(client.get_event(event_id))


def update_event_sync(
    event_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    attendee_ids: Optional[List[int]] = None,
    location: Optional[str] = None,
):
    client = CalendarClient()
    return _run_async(
        client.update_event(
            event_id=event_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            attendee_ids=attendee_ids,
            location=location,
        )
    )


def delete_event_sync(event_id: int):
    client = CalendarClient()
    return _run_async(client.delete_event(event_id))


def check_availability_sync(
    user_id: int,
    start_time: datetime,
    duration_minutes: int,
):
    client = CalendarClient()
    return _run_async(
        client.check_availability(user_id, start_time, duration_minutes)
    )