"""Google OAuth 2.0 — authorization code flow; secrets stay server-side."""

from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import OAuthToken, User

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def build_authorize_url(state: str) -> str:
    if not settings.google_oauth_configured:
        raise RuntimeError("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not configured")
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(settings.google_scopes),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",  # ensure refresh_token on reconnect
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


def _apply_google_tokens(db: Session, user: User, token_payload: dict) -> None:
    expires_in = int(token_payload.get("expires_in") or 3600)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    token_row = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
    if not token_row:
        token_row = OAuthToken(user_id=user.id)
        db.add(token_row)

    token_row.access_token = token_payload["access_token"]
    # Google only returns refresh_token on first consent / prompt=consent
    if token_payload.get("refresh_token"):
        token_row.refresh_token = token_payload["refresh_token"]
    token_row.token_uri = GOOGLE_TOKEN_URL
    token_row.scopes = token_payload.get("scope") or " ".join(settings.google_scopes)
    token_row.expires_at = expires_at
    token_row.updated_at = datetime.utcnow()


def link_google_to_user(db: Session, user: User, userinfo: dict, token_payload: dict) -> User:
    """Attach Google identity + calendar tokens to an existing (e.g. phone) account."""
    sub = userinfo.get("sub")
    clash = db.query(User).filter(User.google_sub == sub, User.id != user.id).first()
    if clash:
        raise ValueError("This Google account is already linked to another Cal.ai user")
    user.google_sub = sub
    if userinfo.get("email"):
        user.email = userinfo["email"]
    user.name = userinfo.get("name") or user.name or user.email
    user.picture = userinfo.get("picture") or user.picture or ""
    user.provider = "google"
    db.flush()
    _apply_google_tokens(db, user, token_payload)
    db.commit()
    db.refresh(user)
    return user


def upsert_google_user(db: Session, userinfo: dict, token_payload: dict) -> User:
    sub = userinfo.get("sub")
    email = userinfo.get("email") or f"{sub}@google.local"
    user = db.query(User).filter(User.google_sub == sub).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, google_sub=sub)
        db.add(user)

    user.google_sub = sub
    user.email = email
    user.name = userinfo.get("name") or user.name or email
    user.picture = userinfo.get("picture") or ""
    user.provider = "google"
    db.flush()
    _apply_google_tokens(db, user, token_payload)
    db.commit()
    db.refresh(user)
    return user
