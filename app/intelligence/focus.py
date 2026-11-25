from __future__ import annotations

from datetime import datetime, timedelta

from app.calendar.base import CalendarEvent
from app.intelligence.scheduling_core import (
    consecutive_meeting_runs,
    free_slots_from_events,
    minutes_between,
    rank_slots,
)


def focus_protection_plan(events: list[CalendarEvent], prefs: dict, day: datetime | None = None) -> dict:
    day = (day or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    day_events = [e for e in events if e.start_time.date() == day.date()]
    min_focus = int(prefs.get("min_focus_minutes", 90))
    focus_start = int(prefs.get("preferred_focus_start", 9))
    focus_end = int(prefs.get("preferred_focus_end", 12))
    work_start = int(prefs.get("work_start_hour", 9))
    work_end = int(prefs.get("work_end_hour", 18))

    existing_focus = [e for e in day_events if e.category == "focus"]
    slots = free_slots_from_events(
        day_events, day, work_start_hour=work_start, work_end_hour=work_end, min_minutes=min_focus
    )
    preferred = [
        s
        for s in slots
        if s.start.hour < focus_end and (s.end.hour > focus_start or s.start.hour >= focus_start)
    ]
    ranked = rank_slots(
        preferred or slots,
        min_focus,
        preferred_start_hour=focus_start,
        preferred_end_hour=focus_end,
    )

    interruptions = []
    for f in existing_focus:
        for e in day_events:
            if e.id == f.id:
                continue
            if e.category == "focus":
                continue
            if f.start_time < e.end_time and e.start_time < f.end_time:
                interruptions.append(
                    {
                        "focus": f.to_dict(),
                        "intruder": e.to_dict(),
                        "problem": f"“{e.title}” interrupts focus block “{f.title}”.",
                    }
                )

    runs = consecutive_meeting_runs(day_events)
    overloaded = [r for r in runs if r["minutes"] >= int(prefs.get("max_consecutive_meeting_minutes", 120))]

    recommendations = []
    actions: list[dict] = []

    if existing_focus and not interruptions:
        recommendations.append(
            {
                "id": "focus-ok",
                "kind": "focus_protect",
                "problem": "Focus blocks present",
                "explanation": f"You already have {len(existing_focus)} focus block(s) today.",
                "proposed_action": "Keep them protected; avoid booking over them.",
                "expected_benefit": "Preserves deep work.",
                "actions": [],
            }
        )
    elif ranked:
        best = ranked[0]
        recommendations.append(
            {
                "id": "create-focus",
                "kind": "create_focus_block",
                "problem": f"Only short free gaps — need ≥{min_focus}m deep work.",
                "explanation": (
                    f"Longest suitable slot starts at {best['start'][11:16]}. "
                    f"Preferred focus window is {focus_start}:00–{focus_end}:00."
                ),
                "proposed_action": f"Create a {min_focus}-minute focus block.",
                "expected_benefit": f"Guarantees {min_focus} minutes of uninterrupted work.",
                "actions": [
                    {
                        "type": "create_event",
                        "event_id": None,
                        "payload": {
                            "title": "Deep Work — Protected Focus",
                            "description": "Created by Focus Time Protector. Do not schedule over this.",
                            "start_time": best["start"],
                            "end_time": best["end"],
                            "category": "focus",
                            "priority": "high",
                        },
                    }
                ],
            }
        )
        actions.extend(recommendations[-1]["actions"])

    for intr in interruptions:
        recommendations.append(
            {
                "id": f"intrusion-{intr['intruder']['id']}",
                "kind": "protect_focus",
                "problem": intr["problem"],
                "explanation": "A meeting overlaps a protected focus block.",
                "proposed_action": f"Move “{intr['intruder']['title']}” to a free slot.",
                "expected_benefit": "Restores uninterrupted deep work.",
                "actions": [],  # filled by conflict resolver in API when alternatives exist
                "intruder_id": intr["intruder"]["id"],
            }
        )

    for run in overloaded:
        recommendations.append(
            {
                "id": f"run-{run['start']}",
                "kind": "meeting_overload",
                "problem": f"{run['count']} back-to-back meetings ({run['minutes']}m).",
                "explanation": "Exceeds your max consecutive meeting preference.",
                "proposed_action": "Insert a break or move the lowest-priority meeting.",
                "expected_benefit": "Reduces context switching fatigue.",
                "actions": [],
            }
        )

    longest_free = max((minutes_between(s.start, s.end) for s in slots), default=0)
    return {
        "day": day.strftime("%Y-%m-%d"),
        "existing_focus": [e.to_dict() for e in existing_focus],
        "free_slots": [{"start": s.start.isoformat(), "end": s.end.isoformat()} for s in slots],
        "longest_free_minutes": longest_free,
        "interruptions": interruptions,
        "consecutive_runs": runs,
        "recommendations": recommendations,
        "default_actions": actions,
    }
