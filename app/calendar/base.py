"""Calendar service abstraction — UI/API never talk to Google directly."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CalendarEvent:
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: str = ""
    attendees: list[str] = field(default_factory=list)
    category: str = "meeting"
    location: str = ""
    priority: str = "medium"
    meeting_link: str = ""
    notes: str = ""
    source: str = "mock"  # mock | google
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "attendees": self.attendees,
            "category": self.category,
            "location": self.location,
            "priority": self.priority,
            "meeting_link": self.meeting_link,
            "notes": self.notes,
            "source": self.source,
        }


@dataclass
class FreeBusySlot:
    start: datetime
    end: datetime

    def to_dict(self) -> dict[str, Any]:
        return {"start": self.start.isoformat(), "end": self.end.isoformat()}


class CalendarProvider(ABC):
    """Interface every calendar backend must implement."""

    name: str

    @abstractmethod
    def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        ...

    @abstractmethod
    def get_event(self, event_id: str) -> CalendarEvent | None:
        ...

    @abstractmethod
    def create_event(self, data: dict[str, Any]) -> CalendarEvent:
        ...

    @abstractmethod
    def update_event(self, event_id: str, data: dict[str, Any]) -> CalendarEvent:
        ...

    @abstractmethod
    def delete_event(self, event_id: str) -> None:
        ...

    @abstractmethod
    def free_busy(
        self,
        start: datetime,
        end: datetime,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
        min_minutes: int = 30,
    ) -> list[FreeBusySlot]:
        ...
