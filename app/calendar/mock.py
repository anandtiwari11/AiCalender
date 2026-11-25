"""In-memory/SQLite mock calendar — demoable without Google OAuth."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.calendar.base import CalendarEvent, CalendarProvider, FreeBusySlot
from app.models import LocalEvent


def _attendees_list(raw: str | list[str] | None) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(a).strip() for a in raw if str(a).strip()]
    return [a.strip() for a in str(raw).split(",") if a.strip()]


def _as_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", ""))


class MockCalendarProvider(CalendarProvider):
    name = "mock"

    def __init__(self, db: Session, user_id: int | None = None):
        self.db = db
        self.user_id = user_id

    def _query(self):
        q = self.db.query(LocalEvent)
        if self.user_id is not None:
            q = q.filter(LocalEvent.user_id == self.user_id)
        return q

    def _to_event(self, row: LocalEvent) -> CalendarEvent:
        return CalendarEvent(
            id=str(row.id),
            title=row.title,
            description=row.description or "",
            start_time=row.start_time,
            end_time=row.end_time,
            attendees=_attendees_list(row.attendees),
            category=row.category or "meeting",
            location=row.location or "",
            priority=row.priority or "medium",
            meeting_link=row.meeting_link or "",
            notes=row.notes or "",
            source="mock",
        )

    def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        rows = (
            self._query()
            .filter(LocalEvent.start_time < end, LocalEvent.end_time > start)
            .order_by(LocalEvent.start_time)
            .all()
        )
        return [self._to_event(r) for r in rows]

    def get_event(self, event_id: str) -> CalendarEvent | None:
        row = self._query().filter(LocalEvent.id == int(event_id)).first()
        return self._to_event(row) if row else None

    def create_event(self, data: dict[str, Any]) -> CalendarEvent:
        attendees = data.get("attendees", [])
        if isinstance(attendees, list):
            attendees_str = ", ".join(attendees)
        else:
            attendees_str = str(attendees or "")
        row = LocalEvent(
            user_id=self.user_id,
            title=data.get("title") or "Untitled",
            description=data.get("description") or "",
            start_time=_as_dt(data["start_time"]),
            end_time=_as_dt(data["end_time"]),
            attendees=attendees_str,
            category=data.get("category") or "meeting",
            location=data.get("location") or "",
            priority=data.get("priority") or "medium",
            meeting_link=data.get("meeting_link") or "",
            notes=data.get("notes") or "",
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_event(row)

    def update_event(self, event_id: str, data: dict[str, Any]) -> CalendarEvent:
        row = self._query().filter(LocalEvent.id == int(event_id)).first()
        if not row:
            raise ValueError(f"Event {event_id} not found")
        for field in (
            "title",
            "description",
            "category",
            "location",
            "priority",
            "meeting_link",
            "notes",
        ):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        if "attendees" in data and data["attendees"] is not None:
            attendees = data["attendees"]
            row.attendees = (
                ", ".join(attendees) if isinstance(attendees, list) else str(attendees)
            )
        if "start_time" in data and data["start_time"] is not None:
            row.start_time = _as_dt(data["start_time"])
        if "end_time" in data and data["end_time"] is not None:
            row.end_time = _as_dt(data["end_time"])
        self.db.commit()
        self.db.refresh(row)
        return self._to_event(row)

    def delete_event(self, event_id: str) -> None:
        row = self._query().filter(LocalEvent.id == int(event_id)).first()
        if row:
            self.db.delete(row)
            self.db.commit()

    def free_busy(
        self,
        start: datetime,
        end: datetime,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
        min_minutes: int = 30,
    ) -> list[FreeBusySlot]:
        events = self.list_events(start, end)
        slots: list[FreeBusySlot] = []
        day = start.replace(hour=0, minute=0, second=0, microsecond=0)
        while day < end:
            day_start = day.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)
            busy = sorted(
                [
                    (max(e.start_time, day_start), min(e.end_time, day_end))
                    for e in events
                    if e.end_time > day_start and e.start_time < day_end
                ],
                key=lambda x: x[0],
            )
            cursor = day_start
            for b_start, b_end in busy:
                if b_start > cursor and (b_start - cursor).total_seconds() >= min_minutes * 60:
                    slots.append(FreeBusySlot(cursor, b_start))
                cursor = max(cursor, b_end)
            if day_end > cursor and (day_end - cursor).total_seconds() >= min_minutes * 60:
                slots.append(FreeBusySlot(cursor, day_end))
            day += timedelta(days=1)
        return slots


def ensure_demo_event_id() -> str:
    return str(uuid4())
