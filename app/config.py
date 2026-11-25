import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


class Settings:
    app_name: str = "Cal.ai"
    secret_key: str = _env("SECRET_KEY", "dev-secret-change-me")
    database_url: str = _env("DATABASE_URL", f"sqlite:///{BASE_DIR / 'calai.db'}")
    frontend_url: str = _env("FRONTEND_URL", "http://localhost:5173")
    backend_url: str = _env("BACKEND_URL", "http://127.0.0.1:8000")
    # Comma-separated extra origins for production (Vercel preview URLs, etc.)
    cors_origins: str = _env("CORS_ORIGINS", "")
    cookie_secure: bool = _env("COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
    environment: str = _env("ENVIRONMENT", "development")

    def allowed_origins(self) -> list[str]:
        origins = [
            self.frontend_url,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        for part in self.cors_origins.split(","):
            origin = part.strip()
            if origin and origin not in origins:
                origins.append(origin)
        return origins

    google_client_id: str = _env("GOOGLE_CLIENT_ID")
    google_client_secret: str = _env("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = _env(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:8000/api/auth/google/callback",
    )
    google_scopes: tuple[str, ...] = (
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
    )

    gemini_api_key: str = _env("GEMINI_API_KEY")
    gemini_model: str = _env("GEMINI_MODEL", "gemini-3.5-flash-lite")
    openai_api_key: str = _env("OPENAI_API_KEY")
    openai_model: str = _env("OPENAI_MODEL", "gpt-4o-mini")

    session_cookie: str = "calai_session"
    session_max_age: int = 60 * 60 * 24 * 14  # 14 days

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


settings = Settings()
