from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_sub: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    picture: Mapped[str] = mapped_column(String(500), default="")
    # Auth channel: phone | google (calendar source is derived from OAuth tokens)
    provider: Mapped[str] = mapped_column(String(32), default="phone")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tokens: Mapped[list["OAuthToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class PhoneOtp(Base):
    """One-time codes for phone sign-in."""

    __tablename__ = "phone_otps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OAuthToken(Base):
    """Google tokens — never sent to the frontend."""

    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, default="")
    token_uri: Mapped[str] = mapped_column(String(255), default="https://oauth2.googleapis.com/token")
    scopes: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="tokens")


class LocalEvent(Base):
    """Events for the mock calendar provider."""

    __tablename__ = "local_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attendees: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(50), default="meeting")
    location: Mapped[str] = mapped_column(String(200), default="")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    meeting_link: Mapped[str] = mapped_column(String(300), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    proposal_json: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PendingProposal(Base):
    __tablename__ = "pending_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    actions_json: Mapped[str] = mapped_column(Text, nullable=False)
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserPreferences(Base):
    """Explicit scheduling preferences — never silently inferred into permanence."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    work_start_hour: Mapped[int] = mapped_column(Integer, default=9)
    work_end_hour: Mapped[int] = mapped_column(Integer, default=18)
    lunch_start_hour: Mapped[int] = mapped_column(Integer, default=12)
    lunch_end_hour: Mapped[int] = mapped_column(Integer, default=13)
    preferred_meeting_start: Mapped[int] = mapped_column(Integer, default=10)
    preferred_meeting_end: Mapped[int] = mapped_column(Integer, default=16)
    preferred_focus_start: Mapped[int] = mapped_column(Integer, default=9)
    preferred_focus_end: Mapped[int] = mapped_column(Integer, default=12)
    min_focus_minutes: Mapped[int] = mapped_column(Integer, default=90)
    buffer_minutes: Mapped[int] = mapped_column(Integer, default=15)
    max_consecutive_meeting_minutes: Mapped[int] = mapped_column(Integer, default=120)
    break_minutes: Mapped[int] = mapped_column(Integer, default=10)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    hourly_cost_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avoid_meeting_days: Mapped[str] = mapped_column(String(32), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MeetingNote(Base):
    __tablename__ = "meeting_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_id: Mapped[str] = mapped_column(String(128), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="user")  # user | retrieved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AIActionLog(Base):
    """Audit trail for AI proposals and executions."""

    __tablename__ = "ai_action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(64), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    actions_json: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="proposed")  # proposed|approved|rejected|executed|failed
    result_json: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Back-compat alias used by older code paths during migration
Event = LocalEvent
