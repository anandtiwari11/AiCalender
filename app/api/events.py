from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_google_user
from app.calendar.factory import get_calendar_provider
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api/events", tags=["events"])


class EventIn(BaseModel):
    title: str
    description: str = ""
    start_time: datetime
    end_time: datetime
    attendees: list[str] | str = Field(default_factory=list)
    category: str = "meeting"
    location: str = ""
    priority: str = "medium"
    meeting_link: str = ""
    notes: str = ""


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    attendees: list[str] | str | None = None
    category: str | None = None
    location: str | None = None
    priority: str | None = None
    meeting_link: str | None = None
    notes: str | None = None


@router.get("")
def list_events(
    start: str | None = None,
    end: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_dt = datetime.fromisoformat(start) if start else now - timedelta(days=1)
    end_dt = datetime.fromisoformat(end) if end else now + timedelta(days=14)
    provider = get_calendar_provider(db, user)
    events = provider.list_events(start_dt, end_dt)
    return {
        "provider": provider.name,
        "events": [e.to_dict() for e in events],
    }


@router.get("/{event_id}")
def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    provider = get_calendar_provider(db, user)
    event = provider.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.to_dict()


@router.post("")
def create_event(
    body: EventIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    provider = get_calendar_provider(db, user)
    event = provider.create_event(body.model_dump())
    return event.to_dict()


@router.patch("/{event_id}")
def update_event(
    event_id: str,
    body: EventUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    provider = get_calendar_provider(db, user)
    try:
        event = provider.update_event(event_id, body.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return event.to_dict()


@router.delete("/{event_id}")
def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    provider = get_calendar_provider(db, user)
    provider.delete_event(event_id)
    return {"ok": True}
