from __future__ import annotations

from datetime import datetime, timedelta

from app.calendar.base import CalendarEvent
from app.intelligence.importance import score_meeting
from app.intelligence.scheduling_core import find_overlaps, free_slots_from_events, rank_slots


def detect_conflicts(events: list[CalendarEvent]) -> list[dict]:
    pairs = find_overlaps(events)
    out = []
    for a, b in pairs:
        a_score = score_meeting(a)
        b_score = score_meeting(b)
        # Prefer keeping the higher-importance meeting
        if a_score["score"] >= b_score["score"]:
            keep, move = a, b
            keep_score, move_score = a_score, b_score
        else:
            keep, move = b, a
            keep_score, move_score = b_score, a_score
        out.append(
            {
                "keep": keep.to_dict(),
                "move": move.to_dict(),
                "keep_importance": keep_score,
                "move_importance": move_score,
                "problem": f"“{a.title}” overlaps “{b.title}”.",
                "explanation": (
                    f"Recommended keep “{keep.title}” ({keep_score['level']}) and "
                    f"reschedule “{move.title}” ({move_score['level']})."
                ),
            }
        )
    return out


def resolve_conflict_alternatives(
    events: list[CalendarEvent],
    move_event: CalendarEvent,
    prefs: dict,
    days_ahead: int = 5,
) -> list[dict]:
    duration = int((move_event.end_time - move_event.start_time).total_seconds() // 60)
    day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    alternatives: list[dict] = []
    for offset in range(0, days_ahead + 1):
        d = day + timedelta(days=offset)
        day_events = [
            e
            for e in events
            if e.id != move_event.id and e.start_time.date() == d.date()
        ]
        # also include move_event's original day peers without itself
        slots = free_slots_from_events(
            day_events,
            d,
            work_start_hour=prefs.get("work_start_hour", 9),
            work_end_hour=prefs.get("work_end_hour", 18),
            min_minutes=duration,
        )
        ranked = rank_slots(
            slots,
            duration,
            preferred_start_hour=prefs.get("preferred_meeting_start", 10),
            preferred_end_hour=prefs.get("preferred_meeting_end", 16),
        )
        for r in ranked[:3]:
            alternatives.append({**r, "day": d.strftime("%Y-%m-%d")})
    alternatives.sort(key=lambda x: -x["score"])
    return alternatives[:5]


def conflict_resolution_actions(
    conflict: dict,
    alternative: dict,
) -> list[dict]:
    move = conflict["move"]
    return [
        {
            "type": "update_event",
            "event_id": move["id"],
            "payload": {
                "start_time": alternative["start"],
                "end_time": alternative["end"],
            },
        }
    ]
