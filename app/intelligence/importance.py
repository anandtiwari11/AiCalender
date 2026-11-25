"""Meeting importance scoring — heuristic, explainable, never auto-decline."""

from __future__ import annotations

from app.calendar.base import CalendarEvent


CRITICAL_KEYWORDS = (
    "board",
    "investor",
    "client",
    "customer",
    "interview",
    "launch",
    "deadline",
    "demo",
    "offer",
    "legal",
)
HIGH_KEYWORDS = (
    "review",
    "planning",
    "1:1",
    "one on one",
    "1-1",
    "strategy",
    "design",
    "architecture",
)
LOW_KEYWORDS = (
    "standup",
    "stand-up",
    "sync",
    "check-in",
    "checkin",
    "social",
    "optional",
    "fyi",
)


def score_meeting(event: CalendarEvent) -> dict:
    title = (event.title or "").lower()
    desc = (event.description or "").lower()
    blob = f"{title} {desc}"
    reasons: list[str] = []
    score = 50
    uncertain = False

    if event.category == "important":
        score += 30
        reasons.append("Marked as an important event category.")
    if event.category == "focus":
        return {
            "event_id": event.id,
            "title": event.title,
            "level": "high",
            "score": 70,
            "suggestion": "protect",
            "reasons": ["This is a focus block — treat it as protected work time."],
            "uncertain": False,
        }

    attendee_count = len(event.attendees or [])
    if attendee_count >= 5:
        score += 15
        reasons.append(f"Has {attendee_count} attendees (broader coordination).")
    elif attendee_count == 0 and not event.description:
        score -= 5
        uncertain = True
        reasons.append("Limited context (few attendees/description) — confidence is lower.")

    if any(k in blob for k in CRITICAL_KEYWORDS):
        score += 35
        reasons.append("Title/description matches critical business keywords.")
    elif any(k in blob for k in HIGH_KEYWORDS):
        score += 18
        reasons.append("Looks like a high-value working session or review.")
    if any(k in blob for k in LOW_KEYWORDS):
        score -= 20
        reasons.append("Looks like a routine/internal sync that may be movable.")

    if event.priority == "high":
        score += 15
        reasons.append("Event priority is high.")
    elif event.priority == "low":
        score -= 15
        reasons.append("Event priority is low.")

    duration = int((event.end_time - event.start_time).total_seconds() // 60)
    if duration >= 90:
        score += 5
        reasons.append("Longer meeting (≥90m) often signals higher stakes.")

    if score >= 80:
        level = "critical"
        suggestion = "attend"
    elif score >= 65:
        level = "high"
        suggestion = "attend"
    elif score >= 45:
        level = "medium"
        suggestion = "request_agenda"
    else:
        level = "low"
        suggestion = "consider_delegate_or_shorten"

    suggestion_text = {
        "attend": "Attend and prepare.",
        "request_agenda": "Request an agenda if one is missing.",
        "consider_delegate_or_shorten": "Consider shortening, making async, or delegating — do not auto-decline.",
        "protect": "Protect this focus block.",
    }[suggestion]

    if not reasons:
        reasons.append("Scored from available calendar fields only.")
        uncertain = True

    return {
        "event_id": event.id,
        "title": event.title,
        "start_time": event.start_time.isoformat(),
        "end_time": event.end_time.isoformat(),
        "level": level,
        "score": max(0, min(100, score)),
        "suggestion": suggestion,
        "suggestion_text": suggestion_text,
        "reasons": reasons,
        "uncertain": uncertain,
    }
