"""Phone OTP sign-in. SMS via Twilio when configured; otherwise OTP is returned for demo."""

from __future__ import annotations

import hashlib
import hmac
import logging
import random
import re
from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import PhoneOtp, User

logger = logging.getLogger(__name__)

OTP_TTL_MINUTES = 10
MAX_ATTEMPTS = 5


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"[^\d+]", "", (raw or "").strip())
    if not digits:
        raise ValueError("Phone number is required")
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if digits.startswith("+"):
        body = re.sub(r"\D", "", digits)
        if len(body) < 10 or len(body) > 15:
            raise ValueError("Enter a valid phone number with country code")
        return "+" + body
    body = re.sub(r"\D", "", digits)
    if len(body) == 10:
        # Default to India for 10-digit local numbers
        return "+91" + body
    if len(body) >= 11:
        return "+" + body
    raise ValueError("Enter a valid phone number (with country code, e.g. +9198…)")


def _hash_code(phone: str, code: str) -> str:
    material = f"{phone}:{code}:{settings.secret_key}".encode()
    return hashlib.sha256(material).hexdigest()


def _generate_code() -> str:
    return f"{random.SystemRandom().randint(0, 999999):06d}"


async def _send_sms(phone: str, code: str) -> bool:
    """Return True if SMS was sent via Twilio."""
    if not settings.twilio_configured:
        return False
    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    )
    body = f"Your Cal.ai code is {code}. It expires in {OTP_TTL_MINUTES} minutes."
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            url,
            data={"To": phone, "From": settings.twilio_from_number, "Body": body},
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        )
        if resp.status_code >= 400:
            logger.warning("Twilio SMS failed: %s %s", resp.status_code, resp.text[:200])
            resp.raise_for_status()
    return True


async def request_otp(db: Session, phone_raw: str) -> dict:
    phone = normalize_phone(phone_raw)
    code = _generate_code()
    now = datetime.utcnow()
    # Invalidate prior unused codes
    db.query(PhoneOtp).filter(
        PhoneOtp.phone == phone,
        PhoneOtp.consumed.is_(False),
    ).update({"consumed": True})
    row = PhoneOtp(
        phone=phone,
        code_hash=_hash_code(phone, code),
        expires_at=now + timedelta(minutes=OTP_TTL_MINUTES),
    )
    db.add(row)
    db.commit()

    sms_sent = False
    try:
        sms_sent = await _send_sms(phone, code)
    except Exception:
        logger.exception("Failed to send OTP SMS")
        if settings.environment == "production" and not settings.otp_dev_echo:
            raise

    payload: dict = {
        "ok": True,
        "phone": phone,
        "sms_sent": sms_sent,
        "expires_in_seconds": OTP_TTL_MINUTES * 60,
    }
    # Echo OTP when Twilio isn't used / explicitly allowed (prototype & local).
    if settings.otp_dev_echo or not sms_sent:
        payload["dev_otp"] = code
    return payload


def verify_otp(db: Session, phone_raw: str, code: str) -> User:
    phone = normalize_phone(phone_raw)
    code = (code or "").strip()
    if not re.fullmatch(r"\d{6}", code):
        raise ValueError("Enter the 6-digit code")

    now = datetime.utcnow()
    row = (
        db.query(PhoneOtp)
        .filter(PhoneOtp.phone == phone, PhoneOtp.consumed.is_(False))
        .order_by(PhoneOtp.created_at.desc())
        .first()
    )
    if not row or row.expires_at < now:
        raise ValueError("Code expired. Request a new one.")
    if row.attempts >= MAX_ATTEMPTS:
        row.consumed = True
        db.commit()
        raise ValueError("Too many attempts. Request a new code.")

    expected = row.code_hash
    actual = _hash_code(phone, code)
    row.attempts += 1
    if not hmac.compare_digest(expected, actual):
        db.commit()
        raise ValueError("Invalid code")

    row.consumed = True
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        # Synthetic unique email so existing unique constraint stays happy
        email = f"phone_{phone.lstrip('+')}@users.cal.ai"
        user = User(
            phone=phone,
            email=email,
            name=f"User {phone[-4:]}",
            provider="phone",
        )
        db.add(user)
    else:
        if user.provider not in ("google", "phone"):
            user.provider = "phone"
    db.commit()
    db.refresh(user)
    return user
