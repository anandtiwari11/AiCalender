from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_google_user
from app.calendar.factory import get_calendar_provider
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api/freebusy", tags=["freebusy"])


@router.get("")
def freebusy(
    start: str | None = None,
    end: str | None = None,
    min_minutes: int = Query(30, ge=5, le=480),
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_dt = datetime.fromisoformat(start) if start else now
    end_dt = datetime.fromisoformat(end) if end else now + timedelta(days=2)
    provider = get_calendar_provider(db, user)
    slots = provider.free_busy(start_dt, end_dt, min_minutes=min_minutes)
    return {
        "provider": provider.name,
        "slots": [s.to_dict() for s in slots],
    }
