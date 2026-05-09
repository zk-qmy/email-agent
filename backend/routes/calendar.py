from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from backend.services.calendar_service import calendar_service

router = APIRouter()


class CreateEventRequest(BaseModel):
    organizer_id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    attendee_ids: Optional[List[int]] = None
    location: Optional[str] = None


class UpdateEventRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attendee_ids: Optional[List[int]] = None
    location: Optional[str] = None


class CheckAvailabilityRequest(BaseModel):
    user_id: int
    start_time: datetime
    duration_minutes: int


@router.post("/events")
async def create_event(request: CreateEventRequest):
    result = calendar_service.create_event(
        organizer_id=request.organizer_id,
        title=request.title,
        description=request.description,
        start_time=request.start_time,
        end_time=request.end_time,
        attendee_ids=request.attendee_ids,
        location=request.location,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"event": result["event"]}


@router.get("/events")
async def get_events(
    user_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    start_dt = None
    end_dt = None

    if start_date:
        start_dt = datetime.fromisoformat(start_date)
    if end_date:
        end_dt = datetime.fromisoformat(end_date)

    events = calendar_service.get_user_events(user_id, start_dt, end_dt)
    return {"events": events}


@router.get("/events/{event_id}")
async def get_event(event_id: int):
    event = calendar_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"event": event}


@router.put("/events/{event_id}")
async def update_event(event_id: int, request: UpdateEventRequest):
    result = calendar_service.update_event(
        event_id=event_id,
        title=request.title,
        description=request.description,
        start_time=request.start_time,
        end_time=request.end_time,
        attendee_ids=request.attendee_ids,
        location=request.location,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"event": result["event"]}


@router.delete("/events/{event_id}")
async def delete_event(event_id: int):
    result = calendar_service.delete_event(event_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"success": True}


@router.post("/availability")
async def check_availability(request: CheckAvailabilityRequest):
    result = calendar_service.check_availability(
        user_id=request.user_id,
        start_time=request.start_time,
        duration_minutes=request.duration_minutes,
    )
    return result