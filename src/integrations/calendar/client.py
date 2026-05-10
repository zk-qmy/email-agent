import logging
import os
from typing import Optional, List
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

EMAIL_BACKEND_URL = os.getenv("EMAIL_BACKEND_URL", "http://localhost:5001")


class CalendarClientError(Exception):
    pass


class CalendarConnectionError(CalendarClientError):
    pass


class CalendarTimeoutError(CalendarClientError):
    pass


class CalendarAPIError(CalendarClientError):
    pass


class CalendarClient:
    def __init__(self, base_url: str = EMAIL_BACKEND_URL):
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, endpoint: str, **kwargs):
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            logger.error(f"Connection failed to {url}: {e}")
            raise CalendarConnectionError(f"Failed to connect to {self.base_url}") from e
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout to {url}: {e}")
            raise CalendarTimeoutError(f"Request timed out for {endpoint}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"API error {e.response.status_code} for {url}: {e}")
            raise CalendarAPIError(f"API error {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error to {url}: {e}")
            raise CalendarClientError(f"Request failed: {e}") from e

    async def create_event(
        self,
        organizer_id: int,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        attendee_ids: Optional[List[int]] = None,
        location: Optional[str] = None,
    ):
        return await self._request(
            "POST",
            "/api/calendar/events",
            json={
                "organizer_id": organizer_id,
                "title": title,
                "description": description,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "attendee_ids": attendee_ids,
                "location": location,
            },
        )

    async def get_events(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        params = {"user_id": user_id}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return await self._request("GET", "/api/calendar/events", params=params)

    async def get_event(self, event_id: int):
        return await self._request("GET", f"/api/calendar/events/{event_id}")

    async def update_event(
        self,
        event_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        attendee_ids: Optional[List[int]] = None,
        location: Optional[str] = None,
    ):
        payload = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if start_time is not None:
            payload["start_time"] = start_time.isoformat()
        if end_time is not None:
            payload["end_time"] = end_time.isoformat()
        if attendee_ids is not None:
            payload["attendee_ids"] = attendee_ids
        if location is not None:
            payload["location"] = location

        return await self._request("PUT", f"/api/calendar/events/{event_id}", json=payload)

    async def delete_event(self, event_id: int):
        return await self._request("DELETE", f"/api/calendar/events/{event_id}")

    async def check_availability(
        self,
        user_id: int,
        start_time: datetime,
        duration_minutes: int,
    ):
        return await self._request(
            "POST",
            "/api/calendar/availability",
            json={
                "user_id": user_id,
                "start_time": start_time.isoformat(),
                "duration_minutes": duration_minutes,
            },
        )


calendar_client = CalendarClient()