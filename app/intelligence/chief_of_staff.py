from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.calendar.base import CalendarEvent
from app.intelligence.buffers import buffer_recommendations
from app.intelligence.conflicts import detect_conflicts, resolve_conflict_alternatives
from app.intelligence.focus import focus_protection_plan
from app.intelligence.importance import score_meeting
from app.intelligence.scheduling_core import free_slots_from_events, minutes_between


def _greeting(now: datetime) -> str:
    h = now.hour
    if h < 12:
        return "Good morning"
    if h < 17:
        return "Good afternoon"
    return "Good evening"


def build_chief_of_staff_brief(
    events: list[CalendarEvent],
    tasks: list[dict[str, Any]],
    prefs: dict,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now()
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = day + timedelta(days=1)
    day_events = sorted(
        [e for e in events if e.start_time < tomorrow and e.end_time > day],
        key=lambda e: e.start_time,
    )
    meetings = [e for e in day_events if e.category in ("meeting", "important")]
    focus = [e for e in day_events if e.category == "focus"]

    slots = free_slots_from_events(
        day_events,
        day,
        work_start_hour=prefs.get("work_start_hour", 9),
        work_end_hour=prefs.get("work_end_hour", 18),
        min_minutes=30,
    )
    available = sum(minutes_between(s.start, s.end) for s in slots)
    longest = max((minutes_between(s.start, s.end) for s in slots), default=0)

    scored = [score_meeting(e) for e in meetings]
    scored.sort(key=lambda x: -x["score"])
    important = [s for s in scored if s["level"] in ("critical", "high")]

    conflicts = detect_conflicts(day_events)
    focus_plan = focus_protection_plan(day_events, prefs, day)
    buffers = buffer_recommendations(day_events, prefs, day)

    # Deadlines / high priority tasks due soon
    upcoming_deadlines = []
    high_tasks = []
    for t in tasks:
        if t.get("status") == "done":
            continue
        high_tasks.append(t)
        due = t.get("due_date")
        if due:
            if isinstance(due, str):
                due_dt = datetime.fromisoformat(due.replace("Z", ""))
            else:
                due_dt = due
            if due_dt.date() <= (day + timedelta(days=2)).date():
                upcoming_deadlines.append(
                    {
                        "id": t.get("id"),
                        "title": t.get("title"),
                        "due_date": due_dt.isoformat(),
                        "priority": t.get("priority"),
                        "estimated_minutes": t.get("estimated_minutes", 30),
                    }
                )

    problems = []
    if conflicts:
        problems.append(f"{len(conflicts)} overlapping meeting pair(s).")
    if longest < prefs.get("min_focus_minutes", 90) and upcoming_deadlines:
        problems.append(
            f"Only {longest}m uninterrupted time while deadline(s) need attention."
        )
    if len(meetings) >= 5:
        problems.append(f"Meeting-heavy day ({len(meetings)} meetings).")

    narrative_parts = [
        f"{_greeting(now)}! You have {len(meetings)} meeting(s) today."
    ]
    if important:
        narrative_parts.append(
            f"Most important: “{important[0]['title']}” ({important[0]['level']})."
        )
    if upcoming_deadlines:
        d0 = upcoming_deadlines[0]
        narrative_parts.append(
            f"Upcoming deadline: “{d0['title']}”"
            + (f" (~{d0['estimated_minutes']}m estimate)." if d0.get("estimated_minutes") else ".")
        )
    narrative_parts.append(
        f"You currently have about {available}m free time; longest uninterrupted block is {longest}m."
    )
    if conflicts:
        c0 = conflicts[0]
        narrative_parts.append(
            f"Conflict: {c0['problem']} {c0['explanation']}"
        )
    if longest < prefs.get("min_focus_minutes", 90):
        narrative_parts.append(
            f"I recommend protecting {prefs.get('min_focus_minutes', 90)} minutes for focused work"
            + (
                f" related to “{upcoming_deadlines[0]['title']}”."
                if upcoming_deadlines
                else "."
            )
        )

    # Build actionable recommendation cards (deduped by kind priority)
    recommendations: list[dict] = []
    for c in conflicts:
        alts = resolve_conflict_alternatives(day_events, _event_from_dict(c["move"]), prefs)
        actions = []
        if alts:
            actions = [
                {
                    "type": "update_event",
                    "event_id": c["move"]["id"],
                    "payload": {"start_time": alts[0]["start"], "end_time": alts[0]["end"]},
                }
            ]
        recommendations.append(
            {
                "id": f"conflict-{c['move']['id']}",
                "kind": "resolve_conflict",
                "problem": c["problem"],
                "explanation": c["explanation"],
                "proposed_action": (
                    f"Move “{c['move']['title']}” to {alts[0]['start'][0:16].replace('T', ' ')}"
                    if alts
                    else "Review overlapping meetings and pick an alternate slot."
                ),
                "expected_benefit": "Removes double-booking and protects the higher-priority meeting.",
                "actions": actions,
                "alternatives": alts,
            }
        )

    for rec in focus_plan["recommendations"]:
        if rec.get("actions") or rec["kind"] in ("create_focus_block", "protect_focus", "meeting_overload"):
            if rec["kind"] == "focus-ok":
                continue
            recommendations.append(rec)

    for rec in buffers["recommendations"][:3]:
        recommendations.append(rec)

    # Low importance move suggestion when meeting-heavy + low focus
    if len(meetings) >= 4 and longest < prefs.get("min_focus_minutes", 90):
        low = [s for s in scored if s["level"] == "low"]
        if low and focus_plan["default_actions"]:
            recommendations.insert(
                0,
                {
                    "id": f"lighten-{low[0]['event_id']}",
                    "kind": "optimize_day",
                    "problem": "Meeting load crowds out deep work.",
                    "explanation": (
                        f"“{low[0]['title']}” scored low importance. "
                        f"Longest free block is only {longest}m."
                    ),
                    "proposed_action": (
                        f"Keep low-priority syncs flexible and reserve "
                        f"{prefs.get('min_focus_minutes', 90)}m focus time."
                    ),
                    "expected_benefit": "More realistic progress on deadlines without ignoring critical meetings.",
                    "actions": focus_plan["default_actions"],
                },
            )

    return {
        "generated_at": now.isoformat(),
        "greeting": _greeting(now),
        "narrative": " ".join(narrative_parts),
        "schedule": [e.to_dict() for e in day_events],
        "important_meetings": important[:5],
        "all_meeting_scores": scored,
        "upcoming_deadlines": upcoming_deadlines,
        "high_priority_tasks": high_tasks[:8],
        "conflicts": conflicts,
        "available_minutes": available,
        "longest_free_minutes": longest,
        "focus_minutes": sum(minutes_between(e.start_time, e.end_time) for e in focus),
        "problems": problems,
        "recommendations": recommendations,
        "focus_plan": focus_plan,
        "buffer_plan": buffers,
        "prefs_used": {
            "min_focus_minutes": prefs.get("min_focus_minutes"),
            "work_start_hour": prefs.get("work_start_hour"),
            "work_end_hour": prefs.get("work_end_hour"),
        },
    }


def _event_from_dict(d: dict) -> CalendarEvent:
    return CalendarEvent(
        id=str(d["id"]),
        title=d.get("title") or "",
        start_time=datetime.fromisoformat(d["start_time"].replace("Z", "")),
        end_time=datetime.fromisoformat(d["end_time"].replace("Z", "")),
        description=d.get("description") or "",
        attendees=d.get("attendees") or [],
        category=d.get("category") or "meeting",
        location=d.get("location") or "",
        priority=d.get("priority") or "medium",
        meeting_link=d.get("meeting_link") or "",
        notes=d.get("notes") or "",
        source=d.get("source") or "mock",
    )
