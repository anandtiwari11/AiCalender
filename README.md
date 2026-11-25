# Cal.ai

**Your time, intelligently managed.**

AI-native calendar that can manage a real **Google Calendar**, with a **mock provider** fallback for demos without OAuth credentials.

## Architecture

```
React (Vite)  →  FastAPI  →  CalendarProvider
                                ├─ GoogleCalendarProvider  → Google Calendar API
                                └─ MockCalendarProvider    → SQLite local events

React (Vite)  →  FastAPI  →  Gemini/OpenAI
                              ↓ structured actions
                         user Confirm/Dismiss
                              ↓
                         CalendarProvider mutation
```

- OAuth tokens & client secrets stay **only on the backend**
- Access tokens are refreshed server-side before Google API calls
- UI never imports Google SDKs

## Stack

| Layer | Tech |
|------|------|
| Frontend | React + Vite + TypeScript + Tailwind |
| Backend | Python FastAPI |
| DB | SQLite default (`DATABASE_URL` can point to Postgres) |
| Calendar | Google Calendar API + mock provider |
| Auth | Google OAuth 2.0 |
| AI | Gemini (preferred) or OpenAI |

## Setup

### 1. Backend

```bash
cd AiCalender
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set GEMINI_API_KEY=...
# optionally set GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Deploy remotely

See [DEPLOY.md](./DEPLOY.md) — Vercel (frontend) + Render (API + Postgres).

### 3. Google OAuth (optional but required for real calendar)

1. Create OAuth client in Google Cloud Console (Web application)
2. Authorized redirect URI: `http://127.0.0.1:8000/api/auth/google/callback`
3. Enable **Google Calendar API**
4. Put into `.env`:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:5173
```

5. Restart backend → click **Connect Google Calendar** in the sidebar

Without Google credentials the app uses the **mock calendar provider** automatically.

## API smoke tests

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/events
curl "http://127.0.0.1:8000/api/freebusy?min_minutes=30"
curl -X POST http://127.0.0.1:8000/api/ai/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Schedule 30 minutes of focus tomorrow at 10 AM"}'
```

Confirm proposals via `/api/ai/proposals/{id}/confirm` — nothing mutates until then.

## Key files

```
app/
  calendar/base.py           # CalendarProvider abstraction
  calendar/mock.py           # Demo provider
  calendar/google_provider.py
  auth/google_oauth.py       # OAuth code flow + token storage
  api/events.py freebusy.py ai_routes.py auth.py
frontend/src/                # React UI
```
