# Deploy Cal.ai remotely

Recommended split:
- **Frontend** → [Vercel](https://vercel.com) (free)
- **Backend** → [Render](https://render.com) (free web service + free Postgres)

## 1. Backend (Render)

1. Push this repo to GitHub.
2. In Render → **New** → **Blueprint** (or Web Service) using this repo.
3. If not using Blueprint, set:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add env vars:

```text
SECRET_KEY=<long random string>
ENVIRONMENT=production
COOKIE_SECURE=true
FRONTEND_URL=https://YOUR-APP.vercel.app
CORS_ORIGINS=https://YOUR-APP.vercel.app
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.5-flash-lite
DATABASE_URL=<Render Postgres URL>
```

5. Optional Google OAuth:
```text
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://YOUR-API.onrender.com/api/auth/google/callback
```

Also add that redirect URI in Google Cloud Console.

Your API will be like: `https://calai-api.onrender.com`

## 2. Frontend (Vercel)

1. Import the repo in Vercel.
2. Root directory: `frontend`
3. Framework: Vite
4. Env var:

```text
VITE_API_BASE=https://YOUR-API.onrender.com
```

5. Deploy.

## 3. Local check before deploy

```bash
# backend
cd AiCalender
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
npm run dev
```

## Notes

- Free Render services sleep when idle — first request can take ~30–60s.
- Prefer Postgres in production (`DATABASE_URL`). SQLite on ephemeral hosts loses data on restart.
- After frontend URL is known, update backend `FRONTEND_URL` / `CORS_ORIGINS` and redeploy API.
