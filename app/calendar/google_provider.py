"""Google Calendar API provider — tokens stay on the backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.calendar.base import CalendarEvent, CalendarProvider, FreeBusySlot
from app.config import settings
from app.models import OAuthToken, User


def _parse_google_dt(value: dict[str, str] | None) -> datetime | None:
    if not value:
        return None
    if "dateTime" in value:
        return datetime.fromisoformat(value["dateTime"].replace("Z", "+00:00")).replace(tzinfo=None)
    if "date" in value:
        return datetime.fromisoformat(value["date"] + "T00:00:00")
    return None


def _guess_category(event: dict[str, Any]) -> str:
    title = (event.get("summary") or "").lower()
    if any(k in title for k in ("focus", "deep work", "heads down")):
        return "focus"
    if event.get("transparency") == "transparent":
        return "break"
    return "meeting"


class GoogleCalendarProvider(CalendarProvider):
    name = "google"

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self._service = None

    def _get_token_row(self) -> OAuthToken:
        row = self.db.query(OAuthToken).filter(OAuthToken.user_id == self.user.id).first()
        if not row:
            raise RuntimeError("Google Calendar is not connected for this user.")
        return row

    def _credentials(self) -> Credentials:
        row = self._get_token_row()
        creds = Credentials(
            token=row.access_token,
            refresh_token=row.refresh_token or None,
            token_uri=row.token_uri or "https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=row.scopes.split() if row.scopes else list(settings.google_scopes),
        )
        if not creds.valid or (
            row.expires_at and row.expires_at <= datetime.utcnow() + timedelta(minutes=1)
        ):
            if not creds.refresh_token:
                raise RuntimeError("Google token expired and no refresh token is stored. Reconnect.")
            creds.refresh(Request())
            row.access_token = creds.token or row.access_token
            if creds.expiry:
                row.expires_at = creds.expiry.replace(tzinfo=None)
            row.updated_at = datetime.utcnow()
            self.db.commit()
        return creds

    def _svc(self):
        if self._service is None:
            self._service = build("calendar", "v3", credentials=self._credentials(), cache_discovery=False)
        return self._service

    def _to_event(self, item: dict[str, Any]) -> CalendarEvent | None:
        start = _parse_google_dt(item.get("start"))
        end = _parse_google_dt(item.get("end"))
        if not start or not end:
            return None
        attendees = [
            a.get("email") or a.get("displayName") or ""
            for a in (item.get("attendees") or [])
            if a.get("email") or a.get("displayName")
        ]
        conf = ""
        for ep in item.get("conferenceData", {}).get("entryPoints", []) or []:
            if ep.get("entryPointType") == "video" and ep.get("uri"):
                conf = ep["uri"]
                break
        if not conf:
            conf = item.get("hangoutLink") or ""
        return CalendarEvent(
            id=item["id"],
            title=item.get("summary") or "(No title)",
            description=item.get("description") or "",
            start_time=start,
            end_time=end,
            attendees=attendees,
            category=_guess_category(item),
            location=item.get("location") or "",
            priority="medium",
            meeting_link=conf,
            notes="",
            source="google",
            raw=item,
        )

    def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        time_min = start.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        time_max = end.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        result = (
            self._svc()
            .events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                maxResults=250,
            )
            .execute()
        )
        events: list[CalendarEvent] = []
        for item in result.get("items", []):
            ev = self._to_event(item)
            if ev:
                events.append(ev)
        return events

    def get_event(self, event_id: str) -> CalendarEvent | None:
        try:
            item = self._svc().events().get(calendarId="primary", eventId=event_id).execute()
        except Exception:
            return None
        return self._to_event(item)

    def _body_from_data(self, data: dict[str, Any]) -> dict[str, Any]:
        start = data.get("start_time")
        end = data.get("end_time")
        body: dict[str, Any] = {}
        if "title" in data and data["title"] is not None:
            body["summary"] = data["title"]
        if "description" in data and data["description"] is not None:
            body["description"] = data["description"]
        if "location" in data and data["location"] is not None:
            body["location"] = data["location"]
        if start is not None:
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace("Z", ""))
            body["start"] = {"dateTime": start.isoformat(), "timeZone": "UTC"}
        if end is not None:
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace("Z", ""))
            body["end"] = {"dateTime": end.isoformat(), "timeZone": "UTC"}
        attendees = data.get("attendees")
        if attendees is not None:
            if isinstance(attendees, str):
                emails = [a.strip() for a in attendees.split(",") if a.strip()]
            else:
                emails = [str(a).strip() for a in attendees if str(a).strip()]
            body["attendees"] = [{"email": e} for e in emails if "@" in e]
        return body

    def create_event(self, data: dict[str, Any]) -> CalendarEvent:
        body = self._body_from_data(data)
        if "summary" not in body:
            body["summary"] = data.get("title") or "Untitled"
        if "start" not in body or "end" not in body:
            raise ValueError("start_time and end_time are required")
        item = self._svc().events().insert(calendarId="primary", body=body).execute()
        ev = self._to_event(item)
        if not ev:
            raise RuntimeError("Failed to create Google event")
        return ev

    def update_event(self, event_id: str, data: dict[str, Any]) -> CalendarEvent:
        existing = self._svc().events().get(calendarId="primary", eventId=event_id).execute()
        body = {**existing, **self._body_from_data(data)}
        item = (
            self._svc()
            .events()
            .update(calendarId="primary", eventId=event_id, body=body)
            .execute()
        )
        ev = self._to_event(item)
        if not ev:
            raise RuntimeError("Failed to update Google event")
        return ev

    def delete_event(self, event_id: str) -> None:
        self._svc().events().delete(calendarId="primary", eventId=event_id).execute()

    def free_busy(
        self,
        start: datetime,
        end: datetime,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
        min_minutes: int = 30,
    ) -> list[FreeBusySlot]:
        body = {
            "timeMin": start.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "timeMax": end.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "items": [{"id": "primary"}],
        }
        result = self._svc().freebusy().query(body=body).execute()
        calendars = result.get("calendars", {})
        busy_raw = calendars.get("primary", {}).get("busy", [])
        busy = []
        for b in busy_raw:
            b_start = datetime.fromisoformat(b["start"].replace("Z", "+00:00")).replace(tzinfo=None)
            b_end = datetime.fromisoformat(b["end"].replace("Z", "+00:00")).replace(tzinfo=None)
            busy.append((b_start, b_end))
        busy.sort(key=lambda x: x[0])

        slots: list[FreeBusySlot] = []
        day = start.replace(hour=0, minute=0, second=0, microsecond=0)
        while day < end:
            day_start = day.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)
            day_busy = [
                (max(b0, day_start), min(b1, day_end))
                for b0, b1 in busy
                if b1 > day_start and b0 < day_end
            ]
            cursor = day_start
            for b0, b1 in day_busy:
                if b0 > cursor and (b0 - cursor).total_seconds() >= min_minutes * 60:
                    slots.append(FreeBusySlot(cursor, b0))
                cursor = max(cursor, b1)
            if day_end > cursor and (day_end - cursor).total_seconds() >= min_minutes * 60:
                slots.append(FreeBusySlot(cursor, day_end))
            day += timedelta(days=1)
        return slots
