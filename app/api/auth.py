import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_optional_user, get_user_or_guest
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


@router.get("/status")
def auth_status(
    user: User | None = Depends(get_optional_user),
):
    return {
        "authenticated": bool(user and user.email != "guest@cal.ai"),
        "google_oauth_configured": settings.google_oauth_configured,
        "user": (
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "provider": user.provider,
            }
            if user
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
    response.set_cookie(
        key=settings.session_cookie,
        value=session,
        httponly=True,
        # Cross-site frontend/API hosting needs None+Secure; local uses Lax.
        samesite="none" if settings.cookie_secure else "lax",
        max_age=settings.session_max_age,
        secure=settings.cookie_secure,
    )
    return response


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # Keep Google tokens unless disconnect is requested; logout only clears session.
    response = JSONResponse({"ok": True})
    response.delete_cookie(settings.session_cookie)
    return response


@router.post("/disconnect-google")
def disconnect_google(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_or_guest),
):
    token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
    if token:
        db.delete(token)
    user.provider = "mock"
    user.google_sub = None
    db.commit()
    return {"ok": True, "provider": "mock"}
