from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import User, UserPreferences


DEFAULTS = {
    "work_start_hour": 9,
    "work_end_hour": 18,
    "lunch_start_hour": 12,
    "lunch_end_hour": 13,
    "preferred_meeting_start": 10,
    "preferred_meeting_end": 16,
    "preferred_focus_start": 9,
    "preferred_focus_end": 12,
    "min_focus_minutes": 90,
    "buffer_minutes": 15,
    "max_consecutive_meeting_minutes": 120,
    "break_minutes": 10,
    "timezone": "Asia/Kolkata",
    "hourly_cost_estimate": None,
    "avoid_meeting_days": "",  # comma weekdays 0=Mon
}


def default_preferences() -> dict[str, Any]:
    return dict(DEFAULTS)


def get_or_create_preferences(db: Session, user: User) -> UserPreferences:
    row = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    if row:
        return row
    row = UserPreferences(user_id=user.id, **{k: v for k, v in DEFAULTS.items() if k != "hourly_cost_estimate"})
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def preferences_dict(row: UserPreferences | None) -> dict[str, Any]:
    if not row:
        return default_preferences()
    return {
        "work_start_hour": row.work_start_hour,
        "work_end_hour": row.work_end_hour,
        "lunch_start_hour": row.lunch_start_hour,
        "lunch_end_hour": row.lunch_end_hour,
        "preferred_meeting_start": row.preferred_meeting_start,
        "preferred_meeting_end": row.preferred_meeting_end,
        "preferred_focus_start": row.preferred_focus_start,
        "preferred_focus_end": row.preferred_focus_end,
        "min_focus_minutes": row.min_focus_minutes,
        "buffer_minutes": row.buffer_minutes,
        "max_consecutive_meeting_minutes": row.max_consecutive_meeting_minutes,
        "break_minutes": row.break_minutes,
        "timezone": row.timezone,
        "hourly_cost_estimate": row.hourly_cost_estimate,
        "avoid_meeting_days": row.avoid_meeting_days or "",
    }
