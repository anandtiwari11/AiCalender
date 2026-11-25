"""AI orchestration over CalendarProvider — proposals require user confirmation."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.calendar.base import CalendarEvent, CalendarProvider
from app.config import settings
from app.schemas import AIAction, AIProposal


def get_ai_status() -> dict[str, str | bool]:
    if settings.gemini_api_key:
        return {
            "configured": True,
            "provider": "gemini",
            "model": settings.gemini_model,
            "label": "Gemini connected",
        }
    if settings.openai_api_key:
        return {
            "configured": True,
            "provider": "openai",
            "model": settings.openai_model,
            "label": "OpenAI connected",
        }
    return {
        "configured": False,
        "provider": "none",
        "model": "",
        "label": "No AI key — add GEMINI_API_KEY in .env",
    }


def calendar_context(provider: CalendarProvider) -> str:
    today = datetime.now()
    week_end = today + timedelta(days=7)
    events = provider.list_events(today.replace(hour=0, minute=0, second=0, microsecond=0), week_end)
    slots = provider.free_busy(today, today + timedelta(days=2), min_minutes=30)

    lines = [
        f"Current datetime: {today.strftime('%Y-%m-%d %H:%M')} ({today.strftime('%A')})",
        f"Calendar provider: {provider.name}",
        f"Events next 7 days ({len(events)}):",
    ]
    if not events:
        lines.append("- (no events yet)")
    for e in events:
        lines.append(
            f"- id={e.id} | {e.start_time.strftime('%Y-%m-%d %H:%M')}–{e.end_time.strftime('%H:%M')} "
            f"| {e.title} | category={e.category} | attendees={', '.join(e.attendees) or '-'}"
        )
    lines.append("Free slots (next 2 days):")
    if not slots:
        lines.append("- (none found in work hours)")
    for s in slots[:12]:
        lines.append(f"- {s.start.strftime('%Y-%m-%d %H:%M')}–{s.end.strftime('%H:%M')}")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are Cal.ai, an AI-native calendar assistant for business professionals.
You operate on the user's connected calendar (Google or mock).

Return JSON only:
{
  "reply": "helpful message",
  "summary": "short label",
  "actions": [
    {"type":"create_event|update_event|delete_event|info", "event_id": null, "payload": {}}
  ]
}

Rules:
- Never claim changes are already applied — user must confirm.
- Datetimes ISO 8601: YYYY-MM-DDTHH:MM:SS
- create_event payload: title, description, start_time, end_time, attendees (list or string),
  category, location, priority, meeting_link, notes
- update_event needs event_id + fields to change
- delete_event needs event_id
- Prefer free slots from context when scheduling
- Categories: meeting, focus, personal, task, important, break
"""


def _parse_llm_json(content: str) -> AIProposal:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    parsed = json.loads(content)
    actions: list[AIAction] = []
    for raw in parsed.get("actions") or []:
        if not isinstance(raw, dict):
            continue
        t = raw.get("type") or "info"
        if t not in {"create_event", "update_event", "delete_event", "create_task", "info"}:
            continue
        actions.append(
            AIAction(type=t, event_id=raw.get("event_id"), payload=raw.get("payload") or {})
        )
    return AIProposal(
        reply=parsed.get("reply") or "Done.",
        summary=parsed.get("summary") or "AI proposal",
        actions=actions,
    )


async def gemini_ai(provider: CalendarProvider, message: str) -> AIProposal | None:
    if not settings.gemini_api_key:
        return None
    prompt = (
        f"{SYSTEM_PROMPT}\n\nCalendar context:\n{calendar_context(provider)}\n\n"
        f"User request:\n{message}\n\nRespond with JSON only."
    )
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json",
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_llm_json(content)
    except Exception as exc:
        print(f"[Cal.ai] Gemini error: {exc}")
        return None


async def openai_ai(provider: CalendarProvider, message: str) -> AIProposal | None:
    if not settings.openai_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": (
                                f"Calendar context:\n{calendar_context(provider)}\n\n"
                                f"User request:\n{message}"
                            ),
                        },
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _parse_llm_json(content)
    except Exception as exc:
        print(f"[Cal.ai] OpenAI error: {exc}")
        return None


def _unavailable(reason: str) -> AIProposal:
    return AIProposal(reply=f"AI unavailable. {reason}", summary="AI unavailable", actions=[])


async def run_assistant(
    provider: CalendarProvider, message: str
) -> tuple[AIProposal, str]:
    status = get_ai_status()
    if not status["configured"]:
        return _unavailable("Add GEMINI_API_KEY to .env"), "none"
    if status["provider"] == "gemini":
        proposal = await gemini_ai(provider, message)
        if proposal:
            return proposal, "gemini"
        return _unavailable("Gemini request failed."), "gemini-error"
    proposal = await openai_ai(provider, message)
    if proposal:
        return proposal, "openai"
    return _unavailable("OpenAI request failed."), "openai-error"


def apply_actions(provider: CalendarProvider, actions: list[dict[str, Any]]) -> list[str]:
    """Validate + apply structured AI actions against the calendar provider."""
    results: list[str] = []
    for raw in actions:
        action_type = raw.get("type")
        payload = raw.get("payload") or {}
        event_id = raw.get("event_id")

        if action_type == "create_event":
            if "start_time" not in payload or "end_time" not in payload:
                results.append("Skipped create_event: missing times")
                continue
            event = provider.create_event(payload)
            results.append(f"Created “{event.title}” ({event.id})")
        elif action_type == "update_event" and event_id:
            event = provider.update_event(str(event_id), payload)
            results.append(f"Updated “{event.title}”")
        elif action_type == "delete_event" and event_id:
            provider.delete_event(str(event_id))
            results.append(f"Deleted event {event_id}")
        elif action_type == "info":
            continue
        else:
            results.append(f"Skipped unsupported action: {action_type}")
    return results


def daily_brief(provider: CalendarProvider) -> dict[str, Any]:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    events = provider.list_events(today, tomorrow)
    meetings = [e for e in events if e.category in ("meeting", "important")]
    focus = [e for e in events if e.category == "focus"]
    slots = provider.free_busy(today, tomorrow, min_minutes=30)
    available = sum(int((s.end - s.start).total_seconds() // 60) for s in slots)
    longest = max((int((s.end - s.start).total_seconds() // 60) for s in slots), default=0)
    overlaps = []
    ordered = sorted(events, key=lambda e: e.start_time)
    for i, a in enumerate(ordered):
        for b in ordered[i + 1 :]:
            if b.start_time >= a.end_time:
                break
            if a.start_time < b.end_time and b.start_time < a.end_time:
                overlaps.append((a.title, b.title))

    parts = []
    if len(meetings) >= 4:
        parts.append(f"Your day is meeting-heavy ({len(meetings)} meetings).")
    elif not meetings:
        parts.append("Your calendar is open today — a great day for deep work.")
    else:
        parts.append(f"You have {len(meetings)} meetings today.")
    parts.append(f"About {available} minutes free; longest block {longest}m.")
    if overlaps:
        parts.append(f"Conflict: “{overlaps[0][0]}” overlaps “{overlaps[0][1]}”.")

    upcoming = None
    now = datetime.now()
    for e in events:
        if e.end_time >= now:
            upcoming = e.to_dict()
            break

    return {
        "brief": " ".join(parts),
        "meetings_count": len(meetings),
        "focus_minutes": sum(int((e.end_time - e.start_time).total_seconds() // 60) for e in focus),
        "available_minutes": available,
        "longest_free": longest,
        "overlaps": [{"a": a, "b": b} for a, b in overlaps],
        "upcoming": upcoming,
        "events": [e.to_dict() for e in events],
        "provider": provider.name,
    }
