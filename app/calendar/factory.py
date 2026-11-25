from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.calendar.base import CalendarProvider
from app.calendar.google_provider import GoogleCalendarProvider
from app.models import OAuthToken, User


def get_calendar_provider(db: Session, user: User | None) -> CalendarProvider:
    """Only real Google Calendar — no mock fallback."""
    if not user or user.provider != "google":
        raise HTTPException(status_code=401, detail="Google sign-in required")
    token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
    if not token or not (token.access_token or token.refresh_token):
        raise HTTPException(status_code=401, detail="Google Calendar not connected")
    return GoogleCalendarProvider(db, user)
