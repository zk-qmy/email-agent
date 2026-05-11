from datetime import datetime
from typing import Optional, List
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import CalendarEvent, User


class CalendarService:
    def __init__(self):
        pass

    def _get_session(self) -> Session:
        return SessionLocal()

    def create_event(
        self,
        organizer_id: int,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        attendee_ids: Optional[List[int]] = None,
        location: Optional[str] = None,
    ) -> dict:
        session = self._get_session()
        try:
            if start_time >= end_time:
                return {"success": False, "error": "End time must be after start time"}

            event = CalendarEvent(
                organizer_id=organizer_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                attendee_ids=attendee_ids or [],
                location=location,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return {"success": True, "event": event.to_dict()}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def get_event(self, event_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            event = session.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
            if event:
                return event.to_dict()
            return None
        finally:
            session.close()

    def get_user_events(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[dict]:
        session = self._get_session()
        try:
            query = session.query(CalendarEvent).filter(
                or_(
                    CalendarEvent.organizer_id == user_id,
                    CalendarEvent.attendee_ids.contains([user_id])
                )
            )

            if start_date:
                query = query.filter(CalendarEvent.end_time >= start_date)
            if end_date:
                query = query.filter(CalendarEvent.start_time <= end_date)

            events = query.order_by(CalendarEvent.start_time.asc()).all()
            return [e.to_dict() for e in events]
        finally:
            session.close()

    def update_event(
        self,
        event_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        attendee_ids: Optional[List[int]] = None,
        location: Optional[str] = None,
    ) -> dict:
        session = self._get_session()
        try:
            event = session.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
            if not event:
                return {"success": False, "error": "Event not found"}

            if title is not None:
                event.title = title
            if description is not None:
                event.description = description
            if start_time is not None:
                event.start_time = start_time
            if end_time is not None:
                event.end_time = end_time
            if attendee_ids is not None:
                event.attendee_ids = attendee_ids
            if location is not None:
                event.location = location

            event.updated_at = datetime.utcnow()

            if start_time and end_time and start_time >= end_time:
                return {"success": False, "error": "End time must be after start time"}

            session.commit()
            session.refresh(event)
            return {"success": True, "event": event.to_dict()}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def delete_event(self, event_id: int) -> dict:
        session = self._get_session()
        try:
            event = session.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
            if not event:
                return {"success": False, "error": "Event not found"}

            session.delete(event)
            session.commit()
            return {"success": True}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def check_availability(
        self,
        user_id: int,
        start_time: datetime,
        duration_minutes: int,
    ) -> dict:
        session = self._get_session()
        try:
            from datetime import timedelta

            end_time = start_time + timedelta(minutes=duration_minutes)

            conflicts = session.query(CalendarEvent).filter(
                or_(
                    and_(
                        CalendarEvent.organizer_id == user_id,
                        CalendarEvent.start_time < end_time,
                        CalendarEvent.end_time > start_time,
                    ),
                    and_(
                        CalendarEvent.attendee_ids.contains([user_id]),
                        CalendarEvent.start_time < end_time,
                        CalendarEvent.end_time > start_time,
                    )
                )
            ).order_by(CalendarEvent.start_time.asc()).all()

            if conflicts:
                return {
                    "available": False,
                    "conflicts": [c.to_dict() for c in conflicts],
                }

            return {
                "available": True,
                "conflicts": [],
            }
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return user.to_dict()
            return None
        finally:
            session.close()


calendar_service = CalendarService()