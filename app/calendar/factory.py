from sqlalchemy.orm import Session

from app.calendar.base import CalendarProvider
from app.calendar.google_provider import GoogleCalendarProvider
from app.calendar.mock import MockCalendarProvider
from app.models import OAuthToken, User


def user_has_google_calendar(db: Session, user: User | None) -> bool:
    if not user:
        return False
    token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
    return bool(token and (token.access_token or token.refresh_token))


def get_calendar_provider(db: Session, user: User | None) -> CalendarProvider:
    """Google Calendar when connected; otherwise local DB events for this user."""
    if not user:
        return MockCalendarProvider(db, user_id=None)
    if user_has_google_calendar(db, user):
        return GoogleCalendarProvider(db, user)
    return MockCalendarProvider(db, user_id=user.id)
