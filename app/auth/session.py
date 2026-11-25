from datetime import datetime, timedelta

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt="calai-session")


def create_session_token(user_id: int) -> str:
    return _serializer().dumps({"uid": user_id, "iat": datetime.utcnow().isoformat()})


def decode_session_token(token: str) -> int | None:
    try:
        data = _serializer().loads(token, max_age=settings.session_max_age)
        return int(data["uid"])
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        return None
