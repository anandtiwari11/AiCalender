from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.ai_routes import router as ai_router
from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.freebusy import router as freebusy_router
from app.api.intelligence import router as intelligence_router
from app.api.tasks import router as tasks_router
from app.config import BASE_DIR, settings
from app.database import ensure_schema
from app.legal_pages import ABOUT_HTML, PRIVACY_HTML, TERMS_HTML

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

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"


@app.on_event("startup")
def on_startup():
    ensure_schema()


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "google_oauth_configured": settings.google_oauth_configured,
        "frontend_url": settings.frontend_url,
    }


@app.get("/about", response_class=HTMLResponse)
def about_page():
    """Public marketing page (no login) for Google OAuth home-page checks."""
    return ABOUT_HTML


@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    return PRIVACY_HTML


@app.get("/terms", response_class=HTMLResponse)
def terms_of_service():
    return TERMS_HTML


if FRONTEND_ASSETS.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS), name="frontend-assets")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    """Serve the Vite SPA when frontend/dist is present (Codespace / single-host deploy)."""
    if full_path.startswith("api/"):
        return {"detail": "Not Found"}
    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file() and candidate.resolve().is_relative_to(FRONTEND_DIST.resolve()):
            return FileResponse(candidate)
        return FileResponse(index)
    return {"detail": "Frontend not built. Run npm run build in frontend/."}
