from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str
    description: str = ""
    start_time: datetime
    end_time: datetime
    attendees: str = ""
    category: str = "meeting"
    location: str = ""
    priority: str = "medium"
    meeting_link: str = ""
    notes: str = ""


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attendees: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    priority: Optional[str] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


class EventOut(EventCreate):
    id: int

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    due_date: Optional[datetime] = None
    priority: str = "medium"
    status: str = "pending"
    estimated_minutes: int = 30


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    estimated_minutes: Optional[int] = None


class TaskOut(TaskCreate):
    id: int

    model_config = {"from_attributes": True}


class AIChatRequest(BaseModel):
    message: str


class AIAction(BaseModel):
    type: str  # create_event | update_event | delete_event | create_task | info
    event_id: Optional[str | int] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AIProposal(BaseModel):
    reply: str
    summary: str
    actions: list[AIAction] = Field(default_factory=list)
