"""Phase 1 intelligence APIs — grounded in calendar/task data; mutations via proposals."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_user_or_guest
from app.calendar.factory import get_calendar_provider
from app.database import get_db
from app.intelligence.buffers import buffer_recommendations
from app.intelligence.chief_of_staff import build_chief_of_staff_brief
from app.intelligence.conflicts import (
    conflict_resolution_actions,
    detect_conflicts,
    resolve_conflict_alternatives,
)
from app.intelligence.focus import focus_protection_plan
from app.intelligence.importance import score_meeting
from app.intelligence.preferences import get_or_create_preferences, preferences_dict
from app.models import AIActionLog, PendingProposal, Task, User

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


def _day_window(day: datetime | None = None) -> tuple[datetime, datetime]:
    d = (day or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    return d, d + timedelta(days=7)


def _tasks_for_user(db: Session, user: User) -> list[dict]:
    rows = (
        db.query(Task)
        .filter((Task.user_id == user.id) | (Task.user_id.is_(None)))
        .order_by(Task.due_date.is_(None), Task.due_date)
        .all()
    )
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "priority": t.priority,
            "status": t.status,
            "estimated_minutes": t.estimated_minutes,
        }
        for t in rows
    ]


def _store_proposal(db: Session, user: User, summary: str, actions: list[dict], kind: str) -> int | None:
    if not actions:
        return None
    pending = PendingProposal(
        user_id=user.id,
        summary=summary,
        actions_json=json.dumps(actions),
    )
    db.add(pending)
    db.add(
        AIActionLog(
            user_id=user.id,
            kind=kind,
            summary=summary,
            actions_json=json.dumps(actions),
            status="proposed",
        )
    )
    db.commit()
    db.refresh(pending)
    return pending.id


@router.get("/chief-of-staff")
def chief_of_staff(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    prefs = preferences_dict(get_or_create_preferences(db, user))
    provider = get_calendar_provider(db, user)
    start, end = _day_window()
    events = provider.list_events(start, end)
    tasks = _tasks_for_user(db, user)
    brief = build_chief_of_staff_brief(events, tasks, prefs)
    brief["provider"] = provider.name
    return brief


@router.get("/importance")
def importance(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    provider = get_calendar_provider(db, user)
    start, end = _day_window()
    events = [
        e
        for e in provider.list_events(start, start + timedelta(days=1))
        if e.category in ("meeting", "important")
    ]
    return {
        "provider": provider.name,
        "meetings": [score_meeting(e) for e in events],
    }


@router.get("/conflicts")
def conflicts(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    prefs = preferences_dict(get_or_create_preferences(db, user))
    provider = get_calendar_provider(db, user)
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    events = provider.list_events(start, start + timedelta(days=3))
    detected = detect_conflicts(events)
    enriched = []
    for c in detected:
        from app.intelligence.chief_of_staff import _event_from_dict

        move = _event_from_dict(c["move"])
        alts = resolve_conflict_alternatives(events, move, prefs)
        enriched.append({**c, "alternatives": alts})
    return {"provider": provider.name, "conflicts": enriched}


class ResolveConflictIn(BaseModel):
    move_event_id: str
    alternative_start: str
    alternative_end: str


@router.post("/conflicts/propose")
def propose_conflict_resolution(
    body: ResolveConflictIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    actions = [
        {
            "type": "update_event",
            "event_id": body.move_event_id,
            "payload": {
                "start_time": body.alternative_start,
                "end_time": body.alternative_end,
            },
        }
    ]
    proposal_id = _store_proposal(
        db, user, f"Resolve conflict by moving event {body.move_event_id}", actions, "resolve_conflict"
    )
    return {"proposal_id": proposal_id, "actions": actions}


@router.get("/focus")
def focus(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    prefs = preferences_dict(get_or_create_preferences(db, user))
    provider = get_calendar_provider(db, user)
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    events = provider.list_events(start, start + timedelta(days=1))
    plan = focus_protection_plan(events, prefs, start)
    plan["provider"] = provider.name
    return plan


@router.post("/focus/protect")
def protect_focus(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    prefs = preferences_dict(get_or_create_preferences(db, user))
    provider = get_calendar_provider(db, user)
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    events = provider.list_events(start, start + timedelta(days=1))
    plan = focus_protection_plan(events, prefs, start)
    actions = []
    for rec in plan["recommendations"]:
        actions.extend(rec.get("actions") or [])
    # Also try to move interrupters using conflict alternatives
    from app.intelligence.chief_of_staff import _event_from_dict

    for intr in plan.get("interruptions") or []:
        move = _event_from_dict(intr["intruder"])
        alts = resolve_conflict_alternatives(events, move, prefs)
        if alts:
            actions.append(
                {
                    "type": "update_event",
                    "event_id": move.id,
                    "payload": {"start_time": alts[0]["start"], "end_time": alts[0]["end"]},
                }
            )
    proposal_id = _store_proposal(
        db, user, "Protect my focus time", actions, "create_focus_block"
    )
    return {"proposal_id": proposal_id, "actions": actions, "plan": plan}


@router.get("/buffers")
def buffers(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    prefs = preferences_dict(get_or_create_preferences(db, user))
    provider = get_calendar_provider(db, user)
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    events = provider.list_events(start, start + timedelta(days=1))
    plan = buffer_recommendations(events, prefs, start)
    plan["provider"] = provider.name
    return plan


class ProposeRecommendationIn(BaseModel):
    summary: str
    actions: list[dict] = Field(default_factory=list)
    kind: str = "recommendation"


@router.post("/propose")
def propose_recommendation(
    body: ProposeRecommendationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    proposal_id = _store_proposal(db, user, body.summary, body.actions, body.kind)
    return {"proposal_id": proposal_id, "actions": body.actions}


class PrefsUpdate(BaseModel):
    work_start_hour: int | None = None
    work_end_hour: int | None = None
    lunch_start_hour: int | None = None
    lunch_end_hour: int | None = None
    preferred_meeting_start: int | None = None
    preferred_meeting_end: int | None = None
    preferred_focus_start: int | None = None
    preferred_focus_end: int | None = None
    min_focus_minutes: int | None = None
    buffer_minutes: int | None = None
    max_consecutive_meeting_minutes: int | None = None
    break_minutes: int | None = None
    timezone: str | None = None
    hourly_cost_estimate: int | None = None
    avoid_meeting_days: str | None = None


@router.get("/preferences")
def get_prefs(db: Session = Depends(get_db), user: User = Depends(get_user_or_guest)):
    return preferences_dict(get_or_create_preferences(db, user))


@router.put("/preferences")
def update_prefs(
    body: PrefsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    row = get_or_create_preferences(db, user)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    return preferences_dict(row)
