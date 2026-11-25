import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_optional_user
from app.auth.google_oauth import (
    build_authorize_url,
    exchange_code,
    fetch_userinfo,
    link_google_to_user,
    upsert_google_user,
)
from app.auth.phone import request_otp, verify_otp
from app.auth.session import create_session_token, decode_session_token
from app.calendar.factory import user_has_google_calendar
from app.config import settings
from app.database import get_db
from app.models import OAuthToken, User

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ephemeral OAuth states (demo-scale; use Redis in production)
_oauth_states: set[str] = set()


def _set_session_cookie(response, user_id: int) -> None:
    session = create_session_token(user_id)
    response.set_cookie(
        key=settings.session_cookie,
        value=session,
        httponly=True,
        samesite="lax",
        max_age=settings.session_max_age,
        secure=settings.cookie_secure,
    )


def _is_signed_in(user: User | None) -> bool:
    return bool(user and user.email != "guest@cal.ai")


class PhoneStartIn(BaseModel):
    phone: str = Field(min_length=8, max_length=32)


class PhoneVerifyIn(BaseModel):
    phone: str = Field(min_length=8, max_length=32)
    code: str = Field(min_length=4, max_length=8)


@router.get("/status")
def auth_status(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    authenticated = _is_signed_in(user)
    has_calendar = bool(user and user_has_google_calendar(db, user))
    return {
        "authenticated": authenticated,
        "google_oauth_configured": settings.google_oauth_configured,
        "has_calendar": has_calendar,
        "calendar_source": "google" if has_calendar else ("local" if authenticated else None),
        "phone_auth_available": True,
        "otp_dev_echo": settings.otp_dev_echo or not settings.twilio_configured,
        "user": (
            {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "name": user.name,
                "picture": user.picture,
                "provider": user.provider,
            }
            if authenticated and user
            else None
        ),
    }


@router.post("/phone/start")
async def phone_start(body: PhoneStartIn, db: Session = Depends(get_db)):
    try:
        return await request_otp(db, body.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not send code: {e}") from e


@router.post("/phone/verify")
def phone_verify(body: PhoneVerifyIn, db: Session = Depends(get_db)):
    try:
        user = verify_otp(db, body.phone, body.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    response = JSONResponse(
        {
            "ok": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "name": user.name,
                "provider": user.provider,
            },
            "calendar_source": "google" if user_has_google_calendar(db, user) else "local",
        }
    )
    _set_session_cookie(response, user.id)
    return response


@router.get("/google/start")
def google_start():
    if not settings.google_oauth_configured:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    state = secrets.token_urlsafe(24)
    _oauth_states.add(state)
    url = build_authorize_url(state)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        return RedirectResponse(f"{settings.frontend_url}/?auth_error={error}")
    if not code or not state or state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid OAuth callback")
    _oauth_states.discard(state)

    token_payload = await exchange_code(code)
    userinfo = await fetch_userinfo(token_payload["access_token"])

    # If already signed in (e.g. phone user connecting Google), attach to that account.
    existing: User | None = None
    cookie = request.cookies.get(settings.session_cookie)
    if cookie:
        uid = decode_session_token(cookie)
        if uid:
            existing = db.get(User, uid)

    if existing and existing.phone and not user_has_google_calendar(db, existing):
        try:
            user = link_google_to_user(db, existing, userinfo, token_payload)
        except ValueError:
            return RedirectResponse(f"{settings.frontend_url}/?auth_error=google_already_linked")
    else:
        user = upsert_google_user(db, userinfo, token_payload)

    response = RedirectResponse(f"{settings.frontend_url}/?connected=1")
    _set_session_cookie(response, user.id)
    return response


@router.post("/logout")
def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(
        settings.session_cookie,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    return response


@router.post("/disconnect-google")
def disconnect_google(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
    if token:
        db.delete(token)
    user.google_sub = None
    user.provider = "phone" if user.phone else "phone"
    db.commit()
    # Stay signed in — calendar falls back to local DB
    return {"ok": True, "calendar_source": "local"}
