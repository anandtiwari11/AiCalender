from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai_routes import router as ai_router
from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.freebusy import router as freebusy_router
from app.api.intelligence import router as intelligence_router
from app.api.tasks import router as tasks_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import User

app = FastAPI(title="Cal.ai API", description="AI-native calendar with Google Calendar integration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(freebusy_router)
app.include_router(ai_router)
app.include_router(intelligence_router)
app.include_router(tasks_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        guest = db.query(User).filter(User.email == "guest@cal.ai").first()
        if not guest:
            db.add(User(email="guest@cal.ai", name="Guest", provider="mock"))
            db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "google_oauth_configured": settings.google_oauth_configured,
        "frontend_url": settings.frontend_url,
    }
