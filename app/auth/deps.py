from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.session import decode_session_token
from app.database import get_db
from app.models import User


def _user_from_cookie(db: Session, cookie_value: str | None) -> User | None:
    if not cookie_value:
        return None
    user_id = decode_session_token(cookie_value)
    if not user_id:
        return None
    return db.get(User, user_id)


async def get_optional_user(
    db: Session = Depends(get_db),
    calai_session: str | None = Cookie(default=None, alias="calai_session"),
) -> User | None:
    return _user_from_cookie(db, calai_session)


async def get_current_user(
    user: User | None = Depends(get_optional_user),
) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# Back-compat alias — phone and Google users are both first-class.
get_google_user = get_current_user
