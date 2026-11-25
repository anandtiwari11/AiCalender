from sqlalchemy.orm import Session

from app.calendar.base import CalendarProvider
from app.calendar.google_provider import GoogleCalendarProvider
from app.calendar.mock import MockCalendarProvider
from app.models import OAuthToken, User


def get_calendar_provider(db: Session, user: User | None) -> CalendarProvider:
    """Pick Google when connected; otherwise mock so demos still work."""
    if user and user.provider == "google":
        token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
        if token and (token.access_token or token.refresh_token):
            return GoogleCalendarProvider(db, user)
    return MockCalendarProvider(db, user_id=user.id if user else None)
