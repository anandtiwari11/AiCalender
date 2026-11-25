from __future__ import annotations

from datetime import datetime, timedelta

from app.calendar.base import CalendarEvent
from app.intelligence.importance import score_meeting
from app.intelligence.scheduling_core import can_place, minutes_between


def buffer_recommendations(events: list[CalendarEvent], prefs: dict, day: datetime | None = None) -> dict:
    day = (day or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    day_events = sorted(
        [e for e in events if e.start_time.date() == day.date()],
        key=lambda e: e.start_time,
    )
    buffer_m = int(prefs.get("buffer_minutes", 15))
    break_m = int(prefs.get("break_minutes", 10))
    recommendations = []

    for i, e in enumerate(day_events):
        if e.category not in ("meeting", "important"):
            continue
        importance = score_meeting(e)
        # Prep buffer before important/critical meetings
        if importance["level"] in ("critical", "high"):
            prep_start = e.start_time - timedelta(minutes=buffer_m)
            prep_end = e.start_time
            if prep_start.date() == day.date() and can_place(prep_start, prep_end, day_events, buffer_minutes=0):
                # ensure no overlap with previous event end
                prev = day_events[i - 1] if i > 0 else None
                if not prev or prev.end_time <= prep_start:
                    recommendations.append(
                        {
                            "id": f"prep-{e.id}",
                            "kind": "prep_buffer",
                            "problem": f"No prep buffer before “{e.title}” ({importance['level']}).",
                            "explanation": (
                                f"High-importance meetings benefit from {buffer_m}m preparation time."
                            ),
                            "proposed_action": f"Add a {buffer_m}m prep block before the meeting.",
                            "expected_benefit": "Better meeting readiness without rushing.",
                            "actions": [
                                {
                                    "type": "create_event",
                                    "event_id": None,
                                    "payload": {
                                        "title": f"Prep — {e.title}",
                                        "description": "Smart buffer before an important meeting.",
                                        "start_time": prep_start.isoformat(),
                                        "end_time": prep_end.isoformat(),
                                        "category": "break",
                                        "priority": "medium",
                                    },
                                }
                            ],
                        }
                    )

        # Break between back-to-back meetings
        if i + 1 < len(day_events):
            nxt = day_events[i + 1]
            if nxt.category not in ("meeting", "important"):
                continue
            gap = minutes_between(e.end_time, nxt.start_time)
            if gap < break_m:
                # try place break after e if there's room by shifting conceptually — only if gap==0 and we can insert by moving? 
                # For buffers we only create if free space exists of break_m after e before nxt — if gap is 0, suggest moving nxt
                if gap == 0:
                    recommendations.append(
                        {
                            "id": f"b2b-{e.id}-{nxt.id}",
                            "kind": "back_to_back",
                            "problem": f"Back-to-back: “{e.title}” → “{nxt.title}”.",
                            "explanation": f"Gap is {gap}m; preferred break is {break_m}m.",
                            "proposed_action": (
                                f"Move “{nxt.title}” later by {break_m} minutes to create a break."
                            ),
                            "expected_benefit": "Reduces context-switch stress between meetings.",
                            "actions": [
                                {
                                    "type": "update_event",
                                    "event_id": nxt.id,
                                    "payload": {
                                        "start_time": (nxt.start_time + timedelta(minutes=break_m)).isoformat(),
                                        "end_time": (nxt.end_time + timedelta(minutes=break_m)).isoformat(),
                                    },
                                }
                            ],
                        }
                    )
                elif gap > 0:
                    # create short break occupying the gap if gap >= break preference partially
                    br_end = e.end_time + timedelta(minutes=min(break_m, gap))
                    if can_place(e.end_time, br_end, day_events):
                        recommendations.append(
                            {
                                "id": f"break-{e.id}",
                                "kind": "break_buffer",
                                "problem": f"Only {gap}m between meetings (prefer {break_m}m).",
                                "explanation": "A short recovery buffer improves meeting quality.",
                                "proposed_action": "Mark a short break block between meetings.",
                                "expected_benefit": "Protected transition time.",
                                "actions": [
                                    {
                                        "type": "create_event",
                                        "event_id": None,
                                        "payload": {
                                            "title": "Break",
                                            "description": "Smart buffer between meetings.",
                                            "start_time": e.end_time.isoformat(),
                                            "end_time": br_end.isoformat(),
                                            "category": "break",
                                            "priority": "low",
                                        },
                                    }
                                ],
                            }
                        )

        # Travel heuristic if location looks physical and next differs
        if e.location and i + 1 < len(day_events):
            nxt = day_events[i + 1]
            if nxt.location and nxt.location.strip().lower() != e.location.strip().lower():
                if "zoom" not in e.location.lower() and "meet" not in e.location.lower():
                    gap = minutes_between(e.end_time, nxt.start_time)
                    if gap < 30:
                        recommendations.append(
                            {
                                "id": f"travel-{e.id}",
                                "kind": "travel_buffer",
                                "problem": f"Possible travel between “{e.location}” and “{nxt.location}”.",
                                "explanation": f"Only {gap}m between different physical locations.",
                                "proposed_action": "Add travel buffer or move the later meeting.",
                                "expected_benefit": "Avoids late arrivals.",
                                "actions": [],
                            }
                        )

    return {
        "day": day.strftime("%Y-%m-%d"),
        "buffer_minutes": buffer_m,
        "break_minutes": break_m,
        "recommendations": recommendations,
    }
