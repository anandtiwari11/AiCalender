from datetime import datetime, timedelta

from app.calendar.base import CalendarEvent
from app.intelligence.conflicts import detect_conflicts, resolve_conflict_alternatives
from app.intelligence.focus import focus_protection_plan
from app.intelligence.importance import score_meeting
from app.intelligence.buffers import buffer_recommendations
from app.intelligence.scheduling_core import find_overlaps, free_slots_from_events, minutes_between


def _ev(title, start, end, category="meeting", priority="medium", attendees=None):
    return CalendarEvent(
        id=title,
        title=title,
        start_time=start,
        end_time=end,
        category=category,
        priority=priority,
        attendees=attendees or [],
    )


def test_overlap_detection():
    day = datetime(2026, 11, 26, 0, 0, 0)
    a = _ev("A", day.replace(hour=10), day.replace(hour=11))
    b = _ev("B", day.replace(hour=10, minute=30), day.replace(hour=11, minute=30))
    assert len(find_overlaps([a, b])) == 1


def test_free_slots_respect_busy():
    day = datetime(2026, 11, 26, 0, 0, 0)
    events = [_ev("Standup", day.replace(hour=9), day.replace(hour=10))]
    slots = free_slots_from_events(events, day, work_start_hour=9, work_end_hour=12, min_minutes=30)
    assert slots
    assert slots[0].start == day.replace(hour=10)


def test_importance_critical_keyword():
    day = datetime(2026, 11, 26, 0, 0, 0)
    e = _ev("Client demo", day.replace(hour=14), day.replace(hour=15), attendees=["a@x.com"] * 3)
    scored = score_meeting(e)
    assert scored["level"] in ("critical", "high")
    assert scored["reasons"]


def test_conflict_prefers_higher_importance():
    day = datetime(2026, 11, 26, 0, 0, 0)
    keep = _ev("Board review", day.replace(hour=15), day.replace(hour=16), priority="high")
    move = _ev("Optional sync", day.replace(hour=15, minute=30), day.replace(hour=16), priority="low")
    conflicts = detect_conflicts([keep, move])
    assert conflicts
    assert conflicts[0]["keep"]["title"] == "Board review"
    assert conflicts[0]["move"]["title"] == "Optional sync"


def test_focus_plan_creates_block_when_needed():
    day = datetime(2026, 11, 26, 0, 0, 0)
    events = [
        _ev("M1", day.replace(hour=9), day.replace(hour=10)),
        _ev("M2", day.replace(hour=10), day.replace(hour=11)),
        _ev("M3", day.replace(hour=11), day.replace(hour=12)),
    ]
    prefs = {"min_focus_minutes": 90, "preferred_focus_start": 13, "preferred_focus_end": 17, "work_start_hour": 9, "work_end_hour": 18, "max_consecutive_meeting_minutes": 120}
    plan = focus_protection_plan(events, prefs, day)
    assert plan["longest_free_minutes"] >= 90
    assert any(r["kind"] == "create_focus_block" for r in plan["recommendations"])


def test_buffer_prep_for_important_meeting():
    day = datetime(2026, 11, 26, 0, 0, 0)
    events = [_ev("Client launch review", day.replace(hour=14), day.replace(hour=15))]
    prefs = {"buffer_minutes": 15, "break_minutes": 10}
    plan = buffer_recommendations(events, prefs, day)
    assert any(r["kind"] == "prep_buffer" for r in plan["recommendations"])


def test_resolve_alternatives_non_empty():
    day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    move = _ev("Move me", day.replace(hour=10), day.replace(hour=11))
    others = [_ev("Busy", day.replace(hour=9), day.replace(hour=10))]
    alts = resolve_conflict_alternatives(others + [move], move, {"work_start_hour": 9, "work_end_hour": 18, "preferred_meeting_start": 10, "preferred_meeting_end": 16})
    assert isinstance(alts, list)
