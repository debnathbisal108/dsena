# AI Sales Employee v2

An autonomous AI sales representative for small businesses. No sequences. No templates. No manual configuration after setup.

## What makes this different

Every other sales tool makes you configure Day 1, Day 3, Day 7 follow-up sequences. This platform replaces all of that with an AI agent that:

- Reads your website and builds its own knowledge base
- Scores every lead across 6 dimensions on arrival
- Decides when and whether to follow up (not you)
- Writes every email fresh based on conversation context
- Handles objections using your actual business knowledge
- Books meetings autonomously when intent is high
- Stops outreach automatically when appropriate

## Quick Start (Local)

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in GROQ_API_KEY at minimum
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Visit http://localhost:3000 → Register → Complete 5-step onboarding → Go live.

## Deployment (Render + Neon)

### 1. Neon PostgreSQL
- Create free project at neon.tech
- Connection string: `postgresql+asyncpg://user:pass@host/db?ssl=require`

### 2. Groq API
- Get free key at console.groq.com
- Model: `llama-3.3-70b-versatile`

### 3. Google Cloud (for OAuth + Calendar)
- New project → Enable Google Calendar API
- OAuth consent screen → External
- Credentials → OAuth 2.0 Client ID → Web application
- Authorized redirect URIs:
  - `https://your-backend.onrender.com/api/auth/google/callback`
  - `https://your-backend.onrender.com/api/calendar/callback`

### 4. Resend (email)
- Sign up at resend.com → verify domain → create API key

### 5. Render
- Push to GitHub
- New → Blueprint → select render.yaml
- Fill in all `sync: false` env vars

### Backend env vars
```
DATABASE_URL=postgresql+asyncpg://...?ssl=require
JWT_SECRET=<32 char random string>
GROQ_API_KEY=gsk_xxx
RESEND_API_KEY=re_xxx
RESEND_FROM_EMAIL=ai@yourdomain.com
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
FRONTEND_URL=https://your-frontend.onrender.com
BACKEND_URL=https://your-backend.onrender.com
ALLOWED_ORIGINS=https://your-frontend.onrender.com
ENVIRONMENT=production
DEBUG=false
```

### Frontend env vars
```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
```

## Architecture

```
Lead submits form
      │
      ▼ (immediate — <100ms)
FastAPI saves lead + returns 201
      │
      └── BackgroundTask: qualify_new_lead()
                │
                ├── RAG: retrieve relevant knowledge chunks
                ├── Groq: score lead (6 dimensions)
                ├── Groq: write personalized first response
                ├── Resend: send email to lead
                └── Schedule: set next_action_at

APScheduler (every 15 min)
      │
      └── run_agent_loop()
            │
            For each lead where next_action_at <= NOW():
              ├── Anti-spam check
              ├── RAG: retrieve context
              ├── Groq: evaluate — what should happen next?
              │     Returns: send_followup | propose_meeting |
              │              stop_outreach | escalate_human | wait_longer
              ├── Execute decision
              │     send_followup → write fresh email → send → log
              │     propose_meeting → write booking invite → send → log
              │     stop_outreach → update status → log
              │     escalate_human → flag → notify owner → log
              │     wait_longer → update next_action_at → log
              └── Update lead scores
```

## Key Files

| File | Purpose |
|---|---|
| `backend/app/services/ai/agent.py` | The autonomous agent loop |
| `backend/app/services/ai/prompts.py` | All AI prompts (edit here only) |
| `backend/app/services/ai/rag.py` | Knowledge retrieval |
| `backend/app/services/knowledge/crawler.py` | Website crawler |
| `backend/app/services/anti_spam.py` | Spam prevention |
| `frontend/src/app/onboarding/page.tsx` | 5-step setup wizard |
| `frontend/src/app/(dashboard)/leads/[id]/page.tsx` | Lead detail with AI panel |
| `frontend/src/app/(dashboard)/knowledge/page.tsx` | Knowledge base manager |

## Localhost → Production Replacements

| File | Change |
|---|---|
| `frontend/src/lib/api.ts` | `NEXT_PUBLIC_API_URL` env var (already env-driven) |
| `frontend/src/app/form/[orgSlug]/page.tsx` | `NEXT_PUBLIC_API_URL` env var |
| `frontend/src/app/book/[orgSlug]/page.tsx` | `NEXT_PUBLIC_API_URL` env var |
| `backend/.env` | All URLs point to Render services |
