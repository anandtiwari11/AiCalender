"""Pure deterministic scheduling helpers — no LLM."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from app.calendar.base import CalendarEvent, FreeBusySlot


def minutes_between(a: datetime, b: datetime) -> int:
    return max(0, int((b - a).total_seconds() // 60))


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def find_overlaps(events: Iterable[CalendarEvent]) -> list[tuple[CalendarEvent, CalendarEvent]]:
    ordered = sorted(events, key=lambda e: e.start_time)
    pairs: list[tuple[CalendarEvent, CalendarEvent]] = []
    for i, a in enumerate(ordered):
        for b in ordered[i + 1 :]:
            if b.start_time >= a.end_time:
                break
            if overlaps(a.start_time, a.end_time, b.start_time, b.end_time):
                pairs.append((a, b))
    return pairs


def free_slots_from_events(
    events: list[CalendarEvent],
    day: datetime,
    work_start_hour: int = 9,
    work_end_hour: int = 18,
    min_minutes: int = 30,
    protected_categories: set[str] | None = None,
) -> list[FreeBusySlot]:
    """Treat meetings (and optionally other categories) as busy; focus blocks also occupy time."""
    protected_categories = protected_categories or set()
    start = day.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
    end = day.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)
    busy = sorted(
        [
            (max(e.start_time, start), min(e.end_time, end))
            for e in events
            if e.end_time > start and e.start_time < end
        ],
        key=lambda x: x[0],
    )
    slots: list[FreeBusySlot] = []
    cursor = start
    for b0, b1 in busy:
        if b0 > cursor and minutes_between(cursor, b0) >= min_minutes:
            slots.append(FreeBusySlot(cursor, b0))
        cursor = max(cursor, b1)
    if end > cursor and minutes_between(cursor, end) >= min_minutes:
        slots.append(FreeBusySlot(cursor, end))
    return slots


def consecutive_meeting_runs(events: list[CalendarEvent], gap_minutes: int = 5) -> list[dict]:
    meetings = sorted(
        [e for e in events if e.category in ("meeting", "important")],
        key=lambda e: e.start_time,
    )
    if not meetings:
        return []
    runs: list[dict] = []
    run = [meetings[0]]
    for e in meetings[1:]:
        gap = minutes_between(run[-1].end_time, e.start_time)
        if gap <= gap_minutes:
            run.append(e)
        else:
            runs.append(_run_summary(run))
            run = [e]
    runs.append(_run_summary(run))
    return runs


def _run_summary(run: list[CalendarEvent]) -> dict:
    return {
        "count": len(run),
        "start": run[0].start_time.isoformat(),
        "end": run[-1].end_time.isoformat(),
        "minutes": minutes_between(run[0].start_time, run[-1].end_time),
        "titles": [e.title for e in run],
    }


def rank_slots(
    slots: list[FreeBusySlot],
    duration_minutes: int,
    preferred_start_hour: int = 10,
    preferred_end_hour: int = 16,
) -> list[dict]:
    ranked = []
    for s in slots:
        if minutes_between(s.start, s.end) < duration_minutes:
            continue
        candidate_end = s.start + timedelta(minutes=duration_minutes)
        score = 100
        hour = s.start.hour
        if preferred_start_hour <= hour < preferred_end_hour:
            score += 20
        if hour < 9 or hour >= 17:
            score -= 40
        # Prefer earlier in the free block slightly
        score -= min(minutes_between(s.start.replace(hour=0, minute=0), s.start) % 180, 15)
        ranked.append(
            {
                "start": s.start.isoformat(),
                "end": candidate_end.isoformat(),
                "slot_end": s.end.isoformat(),
                "score": score,
                "duration_minutes": duration_minutes,
            }
        )
    ranked.sort(key=lambda x: -x["score"])
    return ranked


def can_place(
    start: datetime,
    end: datetime,
    events: list[CalendarEvent],
    buffer_minutes: int = 0,
) -> bool:
    padded_start = start - timedelta(minutes=buffer_minutes)
    padded_end = end + timedelta(minutes=buffer_minutes)
    for e in events:
        if overlaps(padded_start, padded_end, e.start_time, e.end_time):
            # allow exact adjacency without buffer check already accounted
            if overlaps(start, end, e.start_time, e.end_time):
                return False
            # buffer collision with non-focus is still a problem
            if e.category != "break":
                return False
    return True
