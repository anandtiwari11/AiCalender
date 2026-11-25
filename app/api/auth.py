import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_optional_user
from app.auth.google_oauth import (
    build_authorize_url,
    exchange_code,
    fetch_userinfo,
    upsert_google_user,
)
from app.auth.session import create_session_token
from app.config import settings
from app.database import get_db
from app.models import OAuthToken, User

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ephemeral OAuth states (demo-scale; use Redis in production)
_oauth_states: set[str] = set()


def _is_google_user(user: User | None) -> bool:
    return bool(user and user.provider == "google" and user.email != "guest@cal.ai")


@router.get("/status")
def auth_status(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    authenticated = _is_google_user(user)
    has_calendar = False
    if authenticated and user:
        token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
        has_calendar = bool(token and (token.access_token or token.refresh_token))
    return {
        "authenticated": authenticated,
        "google_oauth_configured": settings.google_oauth_configured,
        "has_calendar": has_calendar,
        "user": (
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "provider": user.provider,
            }
            if authenticated and user
            else None
        ),
    }


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
    user = upsert_google_user(db, userinfo, token_payload)

    session = create_session_token(user.id)
    response = RedirectResponse(f"{settings.frontend_url}/?connected=1")
    # Same-origin Render hosting: Lax+Secure is enough and more reliable than None.
    response.set_cookie(
        key=settings.session_cookie,
        value=session,
        httponly=True,
        samesite="lax",
        max_age=settings.session_max_age,
        secure=settings.cookie_secure,
    )
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
    user.provider = "none"
    user.google_sub = None
    db.commit()
    response = JSONResponse({"ok": True})
    response.delete_cookie(
        settings.session_cookie,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    return response
