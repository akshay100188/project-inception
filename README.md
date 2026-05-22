# Project Inception

**Turn a rough idea into a complete, reviewer-approved software specification — powered by Claude and LangGraph.**

Describe your product idea in plain English. Five AI agents extract requirements, design system architecture, select a technology stack, and estimate timeline and cost. Two human-in-the-loop checkpoints let you review and edit before anything is saved. The final output is a structured plan you can download as a 19-section HTML report or a 5-screen UI wireframe.

---

## How It Works

```
Your Idea (text or uploaded doc)
        │
        ▼
┌─────────────────────┐
│  Requirement Agent  │  Extracts structured requirements from raw input + RAG corpus
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Clarification Agent │  Generates targeted questions about gaps and ambiguities
└──────────┬──────────┘
           │
           ▼
   ┌───────────────┐
   │ Checkpoint 1  │  ← You review & approve (or edit) requirements
   └───────┬───────┘
           │
     ┌─────┴──────────────────────────────────┐
     ▼                                        ▼
┌──────────────────┐               ┌──────────────────────┐
│ Architecture     │               │  Tech Stack Selector │
│ Agent            │               │  Agent               │
└──────────┬───────┘               └──────────┬───────────┘
           │                                  │
           └──────────────┬───────────────────┘
                          ▼
               ┌────────────────────┐
               │  Estimation Agent  │  Timeline phases + budget ranges
               └─────────┬──────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Checkpoint 2  │  ← You save or discard the final plan
                 └───────┬───────┘
                         │
                         ▼
              Plan saved to Supabase
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
      Download Report         Download Prototype
   (19-section HTML)        (5-screen wireframe)
```

Each Phase 2 agent queries a **pgvector RAG corpus** of real-world open-source projects before calling Claude, so recommendations are grounded in concrete examples rather than generic advice.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript + Tailwind CSS → **Vercel** |
| Backend | FastAPI + LangGraph → **Railway** (Docker) |
| AI | Claude Sonnet (agents) · Claude Sonnet (report & prototype generation) |
| Embeddings | OpenAI `text-embedding-3-small` (RAG corpus only) |
| Database | Supabase (PostgreSQL + pgvector + Auth) |
| Streaming | Server-Sent Events (SSE) with asyncio-based human-in-the-loop pauses |

---

## Prerequisites

Before you start you need accounts and API keys from four services:

| Service | What you need | Free tier? |
|---|---|---|
| [Anthropic](https://console.anthropic.com) | API key — all Claude agent calls | Pay-per-use |
| [OpenAI](https://platform.openai.com) | API key — RAG embedding only | Pay-per-use |
| [Supabase](https://supabase.com) | Project URL + anon key + service role key | Yes (free tier works) |
| [Railway](https://railway.app) | Account for backend deploy | $5/mo hobby plan |
| [Vercel](https://vercel.com) | Account for frontend deploy | Yes (free tier works) |

**Runtime costs:** A single full plan generation (all 5 agents) costs approximately $0.05–0.15 in Claude API credits. Report and prototype generation add $0.10–0.25 each.

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/your-username/project-inception.git
cd project-inception
```

### 2. Set up Supabase

1. Go to [supabase.com](https://supabase.com) and create a new project
2. In the **SQL Editor**, paste and run the contents of [`supabase/schema.sql`](supabase/schema.sql)
3. In **Authentication → Providers**, make sure **Email** is enabled (magic link)
4. Note your **Project URL**, **Anon key**, and **Service role key** from Project Settings → API

### 3. Configure and start the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in all values (see [Environment Variables](#environment-variables) below):

```bash
uvicorn main:app --reload
# → API running at http://localhost:8000
```

### 4. Seed the RAG corpus (one-time setup)

The RAG corpus gives agents real-world reference examples. This step calls the OpenAI embeddings API and writes ~100 documents to Supabase.

```bash
# With the backend venv still active:
python -m rag.seed
# → Seeding architecture patterns...
# → Seeding tech stack patterns...
# → Seeding estimation patterns...
# → Done. 96 documents embedded.
```

> **Skipping RAG:** If you don't want to seed the corpus, agents will still run — they'll just produce more generic recommendations without real-world grounding.

### 5. Configure and start the frontend

```bash
cd ../frontend
npm install
cp .env.example .env.local
```

Edit `.env.local` with your Supabase URL, anon key, and backend URL, then:

```bash
npm run dev
# → App running at http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173), sign in with a magic link, and click **+ New Project**.

---

## Environment Variables

### Backend — `backend/.env`

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | Your Anthropic API key (`sk-ant-...`). Get it at [console.anthropic.com](https://console.anthropic.com/settings/keys). All agent calls use this key. |
| `OPENAI_API_KEY` | **Yes** | Your OpenAI API key (`sk-proj-...`). Used only for RAG corpus embeddings (`text-embedding-3-small`). |
| `SUPABASE_URL` | **Yes** | Your Supabase project REST URL (`https://xxxx.supabase.co`). Found in Project Settings → API. |
| `SUPABASE_SERVICE_KEY` | **Yes** | Your Supabase **service role** key (not the anon key). Keep this secret — it bypasses Row Level Security. |
| `CORS_ORIGINS` | **Yes** | Comma-separated list of allowed origins. For local dev: `http://localhost:5173`. For production add your Vercel URL. |
| `GITHUB_TOKEN` | No | GitHub personal access token. Raises the GitHub API rate limit from 60 to 5000 requests/hour (used during RAG seeding only). |

### Frontend — `frontend/.env.local`

| Variable | Required | Description |
|---|---|---|
| `VITE_SUPABASE_URL` | **Yes** | Same Supabase project URL as above. |
| `VITE_SUPABASE_ANON_KEY` | **Yes** | Your Supabase **anon** (public) key. Safe to expose in browser code — Row Level Security enforces access. |
| `VITE_API_URL` | **Yes** | URL of your backend. For local dev: `http://localhost:8000`. For production: your Railway URL. |

---

## Deploying to Production

### Step 1 — Push to GitHub

```bash
git remote add origin https://github.com/your-username/project-inception.git
git push -u origin main
```

### Step 2 — Deploy backend to Railway

1. Go to [railway.app](https://railway.app) and click **New Project → Deploy from GitHub repo**
2. Select this repository and set the **Root Directory** to `backend`
3. Railway will detect the `Dockerfile` automatically
4. In the Railway dashboard, go to your service → **Variables** and add:

   | Variable | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | `sk-ant-...` |
   | `OPENAI_API_KEY` | `sk-proj-...` |
   | `SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `SUPABASE_SERVICE_KEY` | `eyJ...` (service role key) |
   | `CORS_ORIGINS` | `https://your-app.vercel.app` |

5. After deploy, copy the Railway **Public Domain** URL (e.g. `https://inception-backend.railway.app`)
6. Run the RAG seed once via Railway's terminal: **Service → Shell**:
   ```bash
   python -m rag.seed
   ```

### Step 3 — Deploy frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and click **Add New → Project**
2. Import your GitHub repository
3. Set **Root Directory** to `frontend`
4. Under **Environment Variables**, add:

   | Variable | Value |
   |---|---|
   | `VITE_SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `VITE_SUPABASE_ANON_KEY` | `eyJ...` (anon key) |
   | `VITE_API_URL` | Your Railway backend URL |

5. Click **Deploy** — Vercel auto-detects Vite

### Step 4 — Configure Supabase Auth for production

In Supabase dashboard → **Authentication → URL Configuration**:

- **Site URL**: `https://your-app.vercel.app`
- **Redirect URLs**: `https://your-app.vercel.app/**`

This is required for magic link emails to redirect users back to your app.

### Step 5 — Update CORS

Go back to Railway → your backend service → Variables and update `CORS_ORIGINS` to include your Vercel URL:

```
CORS_ORIGINS=https://your-app.vercel.app
```

Railway redeploys automatically.

---

## Project Structure

```
project-inception/
├── backend/
│   ├── agents/
│   │   ├── requirement_agent.py      # Extracts structured requirements from raw input
│   │   ├── clarification_agent.py    # Generates clarifying questions
│   │   ├── architecture_agent.py     # Designs system architecture
│   │   ├── techstack_agent.py        # Selects technology stack
│   │   ├── estimation_agent.py       # Estimates timeline and budget
│   │   ├── report_agent.py           # Generates 19-section HTML planning report
│   │   └── prototype_agent.py        # Generates 5-screen HTML UI wireframe
│   ├── graph/
│   │   ├── planning_graph.py         # LangGraph state machine wiring all agents
│   │   └── state.py                  # PlanningState TypedDict
│   ├── rag/
│   │   ├── corpus.py                 # OpenAI embed + pgvector semantic search
│   │   └── seed.py                   # One-time corpus seeder (~96 documents)
│   ├── api/
│   │   ├── stream.py                 # SSE /api/stream/{project_id} endpoint
│   │   ├── projects.py               # Project CRUD + /checkpoint resolver
│   │   ├── upload.py                 # PDF/DOCX/TXT document parser
│   │   └── admin.py                  # Internal admin endpoints
│   ├── checkpoint_registry.py        # asyncio.Event-based human-in-the-loop pauses
│   ├── config.py                     # Pydantic settings (reads from .env)
│   ├── main.py                       # FastAPI app + CORS + lifespan
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Checkpoint/           # Requirements review modal (Checkpoint 1)
│       │   ├── PlanOutput/           # Architecture + tech stack + estimation cards
│       │   └── Nav/                  # Top navigation bar
│       ├── hooks/
│       │   └── useAgentStream.ts     # SSE consumer — processes events into React state
│       ├── pages/
│       │   ├── Login.tsx             # Magic link sign-in
│       │   ├── Dashboard.tsx         # Project list
│       │   ├── NewProject.tsx        # Idea input → streaming → checkpoint flow
│       │   └── ProjectDetail.tsx     # Saved plan view + report/prototype download
│       ├── lib/supabase.ts           # Supabase client + auth helper
│       └── App.tsx                   # Routes
├── supabase/
│   └── schema.sql                    # incept_projects + rag_corpus tables + pgvector
└── README.md
```

---

## Using Your Own API Keys

This project is designed so that anyone can self-host it with their own credentials. **No shared keys, no usage caps, no SaaS signup required.** Here is exactly what each key does:

**`ANTHROPIC_API_KEY`** — the only key that matters for the core feature. Every agent call (requirement extraction, architecture design, tech stack selection, estimation, report generation, prototype generation) goes through your key. Plan for roughly $0.05–0.50 per project depending on complexity and which outputs you generate.

**`OPENAI_API_KEY`** — used exclusively for the RAG corpus feature: embedding reference documents at seed time and embedding queries at runtime to find relevant examples. If you skip seeding the corpus, you can stub this variable with any non-empty string and the agents will still run (RAG lookups fail silently and return empty context).

**`SUPABASE_SERVICE_KEY`** — stays on the server only (never sent to the browser). Used by the backend to write plan data and update project status. Row Level Security on Supabase ensures users can only access their own projects.

**`VITE_SUPABASE_ANON_KEY`** — the browser-facing key. Safe to ship in frontend code because Supabase RLS enforces row-level access.

---

## Contributing

1. Fork the repository and create a feature branch (`git checkout -b feat/my-feature`)
2. Make your changes — backend and frontend can be developed independently
3. Run the TypeScript check before committing: `cd frontend && npx tsc --noEmit`
4. Open a pull request with a clear description of what changed and why

Bug reports and feature requests are welcome via GitHub Issues.

---

## License

MIT — see [LICENSE](LICENSE) for full text.
