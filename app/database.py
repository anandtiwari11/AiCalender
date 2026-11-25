from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _normalize_db_url(url: str) -> str:
    # Render/Heroku often provide postgres:// — SQLAlchemy wants postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


db_url = _normalize_db_url(settings.database_url)
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """create_all + lightweight column adds for existing deployments."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    statements: list[str] = []
    if "phone" not in cols:
        # SQLite & Postgres both accept NULL unique column
        statements.append("ALTER TABLE users ADD COLUMN phone VARCHAR(32)")
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        # Unique index for phone (ignore if already exists)
        try:
            if db_url.startswith("sqlite"):
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone ON users (phone)"
                    )
                )
            else:
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone ON users (phone)"
                    )
                )
        except Exception:
            pass
