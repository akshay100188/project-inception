# Project Inception

Converts a rough project idea into a structured, reviewer-approved planning document — powered by Claude and LangGraph.

## Stack
- **Frontend**: React + Vite + Tailwind → **Vercel**
- **Backend**: FastAPI + LangGraph → **Railway**
- **AI**: Claude Sonnet (agents) + Claude Haiku (clarification) + OpenAI text-embedding-3-small (RAG)
- **Database**: Supabase (PostgreSQL + pgvector + Auth)

## Agent Pipeline
```
Requirement Analyst → Clarification Agent
        ↓
   [Checkpoint 1] ← human reviews requirements
        ↓
Architecture Architect → Tech Stack Selector → Estimation Analyst
        ↓
   [Checkpoint 2] ← human approves plan → saved to Supabase
```

---

## Local Development

### 1. Supabase
1. Create a project at [supabase.com](https://supabase.com)
2. Run `supabase/schema.sql` in the SQL Editor
3. Copy your **Project URL**, **Anon key**, and **Service role key**

### 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in all keys
uvicorn main:app --reload

# Seed the RAG corpus (one-time)
python -m rag.seed
```

### 3. Frontend
```bash
cd frontend
npm install
cp .env.example .env.local   # fill in Supabase + API URL
npm run dev
```

Open http://localhost:5173

---

## Deploy

### Backend → Railway

1. Push the repo to GitHub
2. Create a new Railway project → **Deploy from GitHub repo** → select `backend/` as root
3. Railway auto-detects the `Dockerfile`
4. Add environment variables in Railway dashboard:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `OPENAI_API_KEY` | `sk-proj-...` |
| `SUPABASE_URL` | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | `eyJ...` |
| `CORS_ORIGINS` | `https://your-app.vercel.app` |

5. After deploy, copy the Railway public URL (e.g. `https://inception-backend.railway.app`)
6. Run the seed script once: Railway dashboard → **Shell** → `python -m rag.seed`

### Frontend → Vercel

1. Import the GitHub repo in [vercel.com](https://vercel.com)
2. Set **Root Directory** to `frontend`
3. Add environment variables:

| Variable | Value |
|---|---|
| `VITE_SUPABASE_URL` | `https://xxx.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | `eyJ...` (anon key) |
| `VITE_API_URL` | `https://your-backend.railway.app` |

4. Deploy — Vercel auto-detects Vite

### Supabase Auth (production)
In Supabase dashboard → **Authentication → URL Configuration**:
- **Site URL**: `https://your-app.vercel.app`
- **Redirect URLs**: `https://your-app.vercel.app/**`

---

## Project Structure
```
inception/
├── backend/
│   ├── agents/              # Claude-powered agents (5 total)
│   │   ├── requirement_agent.py
│   │   ├── clarification_agent.py
│   │   ├── architecture_agent.py
│   │   ├── techstack_agent.py
│   │   └── estimation_agent.py
│   ├── graph/               # LangGraph state machine
│   │   ├── planning_graph.py
│   │   └── state.py
│   ├── rag/                 # pgvector RAG
│   │   ├── corpus.py        # embed + semantic search
│   │   └── seed.py          # 16-doc corpus seeder
│   ├── api/                 # FastAPI routes
│   │   ├── stream.py        # SSE streaming endpoint
│   │   └── projects.py      # CRUD + checkpoint resolver
│   ├── checkpoint_registry.py  # asyncio pause/resume
│   ├── config.py
│   ├── main.py
│   ├── Dockerfile
│   └── railway.toml
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── AgentPanel/      # Live streaming panel
│       │   ├── Checkpoint/      # Requirements review modal
│       │   ├── Nav/             # Top navigation
│       │   └── PlanOutput/      # Plan cards + export
│       ├── hooks/
│       │   └── useAgentStream.ts  # SSE consumer + state
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Dashboard.tsx
│       │   ├── NewProject.tsx
│       │   └── ProjectDetail.tsx
│       ├── lib/supabase.ts
│       └── App.tsx
└── supabase/
    └── schema.sql           # incept_projects + rag_corpus + pgvector
```

## Phase Roadmap
- **Phase 1** ✅ Requirement + Clarification agents, SSE streaming, Supabase auth
- **Phase 2** ✅ Architecture, Tech Stack, Estimation agents + pgvector RAG corpus
- **Phase 3** ✅ True blocking checkpoints, polished UI, PDF/Markdown export, Nav
- **Phase 4** ✅ Docker + Railway + Vercel deploy, demo script
