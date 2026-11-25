from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import Event, Task


CATEGORY_COLORS = {
    "meeting": "#3B82F6",
    "focus": "#10B981",
    "personal": "#8B5CF6",
    "task": "#F59E0B",
    "important": "#EF4444",
    "break": "#94A3B8",
}


def day_bounds(day: datetime) -> tuple[datetime, datetime]:
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def events_for_day(db: Session, day: datetime) -> list[Event]:
    start, end = day_bounds(day)
    return (
        db.query(Event)
        .filter(Event.start_time < end, Event.end_time > start)
        .order_by(Event.start_time)
        .all()
    )


def events_in_range(db: Session, start: datetime, end: datetime) -> list[Event]:
    return (
        db.query(Event)
        .filter(Event.start_time < end, Event.end_time > start)
        .order_by(Event.start_time)
        .all()
    )


def pending_tasks(db: Session) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.status != "done")
        .order_by(Task.due_date.is_(None), Task.due_date, Task.priority.desc())
        .all()
    )


def find_overlaps(events: Iterable[Event]) -> list[tuple[Event, Event]]:
    ordered = sorted(events, key=lambda e: e.start_time)
    overlaps: list[tuple[Event, Event]] = []
    for i, a in enumerate(ordered):
        for b in ordered[i + 1 :]:
            if b.start_time >= a.end_time:
                break
            if a.start_time < b.end_time and b.start_time < a.end_time:
                overlaps.append((a, b))
    return overlaps


def free_slots(
    events: list[Event],
    day: datetime,
    work_start_hour: int = 9,
    work_end_hour: int = 18,
    min_minutes: int = 30,
) -> list[tuple[datetime, datetime]]:
    start = day.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
    end = day.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)
    busy = sorted(
        [(max(e.start_time, start), min(e.end_time, end)) for e in events if e.end_time > start and e.start_time < end],
        key=lambda x: x[0],
    )
    slots: list[tuple[datetime, datetime]] = []
    cursor = start
    for b_start, b_end in busy:
        if b_start > cursor and (b_start - cursor).total_seconds() >= min_minutes * 60:
            slots.append((cursor, b_start))
        cursor = max(cursor, b_end)
    if end > cursor and (end - cursor).total_seconds() >= min_minutes * 60:
        slots.append((cursor, end))
    return slots


def minutes_between(a: datetime, b: datetime) -> int:
    return max(0, int((b - a).total_seconds() // 60))


def compute_day_stats(db: Session, day: datetime) -> dict:
    events = events_for_day(db, day)
    meetings = [e for e in events if e.category in ("meeting", "important")]
    focus = [e for e in events if e.category == "focus"]
    meeting_minutes = sum(minutes_between(e.start_time, e.end_time) for e in meetings)
    focus_minutes = sum(minutes_between(e.start_time, e.end_time) for e in focus)
    slots = free_slots(events, day)
    available_minutes = sum(minutes_between(a, b) for a, b in slots)
    longest_free = max((minutes_between(a, b) for a, b in slots), default=0)
    tasks = [t for t in pending_tasks(db) if t.due_date and t.due_date.date() <= (day + timedelta(days=1)).date()]
    upcoming = None
    now = datetime.now()
    for e in events:
        if e.end_time >= now:
            upcoming = e
            break
    overlaps = find_overlaps(events)
    return {
        "events": events,
        "meetings_count": len(meetings),
        "meeting_minutes": meeting_minutes,
        "focus_minutes": focus_minutes,
        "available_minutes": available_minutes,
        "longest_free": longest_free,
        "free_slots": slots,
        "pending_tasks": pending_tasks(db),
        "urgent_tasks": tasks,
        "upcoming": upcoming,
        "overlaps": overlaps,
    }


def build_daily_brief(stats: dict, day: datetime) -> str:
    meetings = stats["meetings_count"]
    focus = stats["focus_minutes"]
    longest = stats["longest_free"]
    urgent = stats["urgent_tasks"]
    overlaps = stats["overlaps"]

    parts = []
    if meetings >= 4:
        parts.append(f"Your day is meeting-heavy ({meetings} meetings).")
    elif meetings == 0:
        parts.append("Your calendar is open today — a great day for deep work.")
    else:
        parts.append(f"You have {meetings} meetings today.")

    if urgent:
        due = urgent[0]
        parts.append(
            f"“{due.title}” needs attention"
            + (f" (due {due.due_date.strftime('%b %d')})" if due.due_date else "")
            + "."
        )

    if longest < 60 and meetings >= 3:
        parts.append(
            f"You only have {longest} minutes of uninterrupted time. "
            "I recommend moving a low-priority sync and reserving 90 minutes for focused work."
        )
    elif focus < 60 and urgent:
        parts.append("Consider blocking focus time before your next deadline.")
    else:
        parts.append(f"You have about {stats['available_minutes']} minutes of free time today.")

    if overlaps:
        a, b = overlaps[0]
        parts.append(f"Warning: “{a.title}” overlaps with “{b.title}”.")

    return " ".join(parts)


def week_start(day: datetime) -> datetime:
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    return start - timedelta(days=start.weekday())


def insights_data(db: Session, weeks: int = 2) -> dict:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7 * weeks)
    events = events_in_range(db, start, end)

    by_day: dict[str, int] = defaultdict(int)
    by_category: dict[str, int] = defaultdict(int)
    meeting_hours = 0.0
    focus_hours = 0.0

    for e in events:
        mins = minutes_between(e.start_time, e.end_time)
        by_day[e.start_time.strftime("%a")] += mins
        by_category[e.category] += mins
        if e.category in ("meeting", "important"):
            meeting_hours += mins / 60
        if e.category == "focus":
            focus_hours += mins / 60

    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return {
        "meeting_hours": round(meeting_hours, 1),
        "focus_hours": round(focus_hours, 1),
        "event_count": len(events),
        "by_day": [{"day": d, "minutes": by_day.get(d, 0)} for d in day_order],
        "by_category": [
            {"category": k, "minutes": v, "color": CATEGORY_COLORS.get(k, "#64748B")}
            for k, v in sorted(by_category.items(), key=lambda x: -x[1])
        ],
        "avg_meeting_load": round(meeting_hours / max(weeks, 1), 1),
    }
