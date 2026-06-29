# Project Inception

**Turn a rough idea into a complete software plan — in your browser, with nothing saved.**

Describe your product idea in plain English. Five agents extract requirements, design system architecture, select a technology stack, and estimate timeline and cost. You review the requirements once, then the finished plan appears and you download it as a 19-section HTML report plus a 5-screen interactive wireframe.

> **No account. No database. No history.** You land straight on the portal, run the pipeline, and download your deliverables. Close the tab and everything is gone — nothing about your idea is ever stored.

> **Default mode uses zero AI credits.** Every agent — requirements, clarification, architecture, tech stack, estimation, report, and prototype — runs without a single API call, grounded in 81 real-world open-source projects. An optional `DEMO_MODE=true` flag switches every agent to Claude Sonnet if you want the full AI experience.

---

## How It Works

```
Open the app  →  land directly on the portal (no login)
        │
        ▼
Your Idea (type it, or upload a PDF / TXT / DOCX)
        │
        ▼
┌─────────────────────┐
│  Requirement Agent  │  Extracts structured requirements
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Clarification Agent │  Generates targeted questions about gaps
└──────────┬──────────┘
           ▼
   ┌───────────────┐
   │  Checkpoint   │  ← You review & approve (or edit) the requirements
   └───────┬───────┘
           │
     ┌─────┴─────────────────────────────────┐
     ▼                                       ▼
┌──────────────────┐              ┌──────────────────────┐
│ Architecture     │              │  Tech Stack Selector │
│ Agent            │              │  Agent               │
└──────────┬───────┘              └──────────┬───────────┘
           └──────────────┬──────────────────┘
                          ▼
               ┌────────────────────┐
               │  Estimation Agent  │  Timeline phases + budget ranges
               └─────────┬──────────┘
                         ▼
                 Your plan appears in the browser
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Download Report        Download Wireframe
      (19-section HTML)      (5-screen prototype)
```

Everything runs in a single browser session over one Server-Sent-Events stream. The plan lives only in the page; the downloads go straight to your device. There is no sign-in, no saved project, and no per-user data.

### Two modes, one codebase

Both modes use the **same 81 real-world project examples** as grounding context. The difference is what happens with that context.

| | Default (`DEMO_MODE=false`) | Demo (`DEMO_MODE=true`) |
|---|---|---|
| Requirement extraction | Keyword + heuristic parsing; top 3 similar projects validate domain/scale | Claude Sonnet grounded by top 3 similar project examples |
| Clarification questions | Feature-gap questions from matched project lessons + domain base questions | Claude Sonnet grounded by top 3 similar project examples |
| Architecture design | Text similarity → pattern vote from matched projects + `reference_projects` in output | Claude Sonnet grounded by top 4 similar project examples + curated architecture docs |
| Tech stack selection | Curated domain stack + `reference_projects` + `real_world_libraries` from matched projects | Claude Sonnet grounded by top 4 similar project examples + curated techstack docs |
| Timeline & cost estimation | Scale + feature count heuristics + `reference_projects` from matched projects | Claude Sonnet grounded by top 4 similar project examples + curated estimation benchmarks |
| HTML planning report | Template — 19-section instant generation | Claude Sonnet (4 parallel calls) |
| Interactive wireframe | Template — 5-screen domain-aware prototype | Claude Sonnet (3 parallel calls) |
| Anthropic API key needed | **No** | Yes |
| OpenAI API key needed | **No** | Yes |
| Database needed | **No** | Yes (pgvector RAG corpus) |

> **`DEMO_MODE` is a server-side environment variable.** It is read once at startup from the environment. No HTTP request can change it. Setting it to `false` (the default) permanently disables all Claude API calls for that deployment.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript + Tailwind CSS → **Vercel** |
| Backend | FastAPI + LangGraph (Docker) → any container host (Railway, Render, Fly.io, Cloud Run) |
| AI (optional) | Claude Sonnet — all agents when `DEMO_MODE=true` only |
| Streaming | Server-Sent Events (SSE) with an in-memory human-in-the-loop pause |
| Persistence | **None.** Plans are ephemeral and never stored |
| Rule engine | 81 real-world open-source project profiles in `backend/data/project_examples/` |
| RAG (DEMO_MODE only) | Supabase Postgres + pgvector for curated reference docs |

---

## Prerequisites

The **default deployment needs no database and no API keys at all** — only a host for the backend and one for the frontend.

| Service | What you need | Required? |
|---|---|---|
| Backend host | Any Docker/container host (Railway, Render, Fly.io, Cloud Run) | Always |
| [Vercel](https://vercel.com) | Account for the frontend | Always (free tier) |
| [Anthropic](https://console.anthropic.com) | API key | **Only if `DEMO_MODE=true`** |
| [OpenAI](https://platform.openai.com) | API key (RAG embeddings) | **Only if `DEMO_MODE=true`** |
| [Supabase](https://supabase.com) | pgvector project for the RAG corpus | **Only if `DEMO_MODE=true`** |

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/your-username/project-inception.git
cd project-inception
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

For the default (zero-credit, no-database) mode, `.env` only needs:

```env
CORS_ORIGINS=http://localhost:5173
DEMO_MODE=false
```

Start the server:

```bash
uvicorn main:app --reload
# → API running at http://localhost:8000
```

### 3. Start the frontend

```bash
cd ../frontend
npm install
cp .env.example .env.local
```

Edit `.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

```bash
npm run dev
# → App running at http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) and start typing an idea. No sign-in step.

---

## Running in Demo Mode (Claude-powered)

To switch all agents to Claude Sonnet, add the following to `backend/.env`:

```env
DEMO_MODE=true
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

Then provision the RAG corpus once:

1. In the Supabase **SQL Editor**, run [`supabase/schema.sql`](supabase/schema.sql) (enables pgvector + the `rag_corpus` table).
2. Seed the corpus: `cd backend && python -m scripts.migrate_examples_to_supabase`

> The server validates the Anthropic and OpenAI keys at startup and **exits immediately** with a clear error if either is missing when `DEMO_MODE=true`. This prevents silent mid-request failures. To revert to zero-credit mode, set `DEMO_MODE=false` and the database becomes unnecessary.

---

## Environment Variables

### Backend — `backend/.env`

| Variable | Required | Description |
|---|---|---|
| `CORS_ORIGINS` | **Yes** | Comma-separated allowed origins. Local dev: `http://localhost:5173`. |
| `DEMO_MODE` | No | `false` (default) — all agents rule-based, zero credits, no database. `true` — all agents use Claude Sonnet. |
| `ANTHROPIC_API_KEY` | Only if `DEMO_MODE=true` | Your Anthropic API key. Server exits at startup without it when `DEMO_MODE=true`. |
| `OPENAI_API_KEY` | Only if `DEMO_MODE=true` | Your OpenAI key (RAG corpus embeddings). |
| `SUPABASE_URL` | Only if `DEMO_MODE=true` | Supabase REST URL for the pgvector RAG corpus. Unused in default mode. |
| `SUPABASE_SERVICE_KEY` | Only if `DEMO_MODE=true` | Supabase service role key. Keep server-side only. |
| `GITHUB_TOKEN` | No | Raises GitHub API rate limit from 60 → 5000 req/hr during RAG seeding. |

### Frontend — `frontend/.env.local`

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | **Yes** | Backend URL. Local dev: `http://localhost:8000`. Production: your backend host URL. |
| `VITE_POSTHOG_KEY` | No | PostHog project API key — enables usage analytics. Leave blank to disable silently. |
| `VITE_POSTHOG_HOST` | No | PostHog ingest host. Defaults to `https://us.i.posthog.com`. |
| `VITE_UMAMI_SRC` / `VITE_UMAMI_WEBSITE_ID` | No | Optional Umami analytics. Dormant unless both are set. |

---

## Deploying to Production

### Step 1 — Push to GitHub

```bash
git remote add origin https://github.com/your-username/project-inception.git
git push -u origin main
```

### Step 2 — Deploy the backend (any container host)

The backend is a standard Docker image ([`backend/Dockerfile`](backend/Dockerfile)) that reads the `PORT` env var, so it runs unchanged on Railway, Render, Fly.io, Cloud Run, or your own VPS.

1. Create a service from this repo with **root directory** `backend` (the host auto-detects the Dockerfile).
2. Set environment variables:

   | Variable | Value |
   |---|---|
   | `CORS_ORIGINS` | `https://your-app.vercel.app` |
   | `DEMO_MODE` | `false` |

   > Add `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_SERVICE_KEY` **only** if you intentionally want `DEMO_MODE=true`.

3. Copy the public backend URL after deploy.

### Step 3 — Deploy the frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New → Project**.
2. Import the repository, set **Root Directory** to `frontend`.
3. Add one environment variable: `VITE_API_URL` = your backend URL.
4. Click **Deploy**.

### Step 4 — Lock CORS

Make sure `CORS_ORIGINS` on the backend includes your Vercel URL, then redeploy the backend.

---

## Project Structure

```
project-inception/
├── backend/
│   ├── agents/
│   │   ├── requirement_agent.py      # Claude + top 3 similar project examples (DEMO_MODE=true)
│   │   ├── clarification_agent.py    # Claude + top 3 similar project examples (DEMO_MODE=true)
│   │   ├── architecture_agent.py     # Claude + top 4 similar projects + curated arch docs (DEMO_MODE=true)
│   │   ├── techstack_agent.py        # Claude + top 4 similar projects + curated stack docs (DEMO_MODE=true)
│   │   ├── estimation_agent.py       # Claude + top 4 similar projects + benchmarks (DEMO_MODE=true)
│   │   ├── report_agent.py           # 19-section HTML report — Claude version (DEMO_MODE=true)
│   │   ├── prototype_agent.py        # 5-screen wireframe — Claude version (DEMO_MODE=true)
│   │   └── rules/                    # Rule-based agents + similarity search (default mode)
│   ├── report/
│   │   ├── template_report.py        # 19-section HTML report — template version (default)
│   │   └── template_prototype.py     # 5-screen wireframe — template version (default)
│   ├── graph/
│   │   ├── planning_graph.py         # LangGraph state machine — routes to rules or Claude
│   │   └── state.py                  # PlanningState TypedDict
│   ├── rag/                          # OpenAI embed + pgvector search (DEMO_MODE only)
│   ├── data/project_examples/        # 81 real-world project profiles (JSON + embeddings)
│   ├── api/
│   │   ├── stream.py                 # SSE /api/stream/run/{id} — unauthenticated, ephemeral
│   │   ├── projects.py               # In-memory checkpoint resolver + report/prototype generators
│   │   └── upload.py                 # PDF/DOCX/TXT document parser
│   ├── checkpoint_registry.py        # asyncio.Event human-in-the-loop pauses (in-memory)
│   ├── config.py                     # Pydantic settings (reads .env)
│   ├── main.py                       # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Checkpoint/           # Requirements review modal
│       │   └── PlanOutput/           # Architecture + tech stack + estimation cards
│       ├── hooks/useAgentStream.ts   # SSE consumer + analytics
│       ├── lib/analytics.ts          # PostHog / Umami wrappers — no-op when unconfigured
│       ├── pages/Portal.tsx          # The entire single-page ephemeral flow
│       └── App.tsx
├── supabase/schema.sql               # DEMO_MODE only: pgvector rag_corpus table
└── README.md
```

---

## How the 81 Project Examples Are Used

Every project profile in `backend/data/project_examples/` contains: project name, problem statement, target users, core features, integrations, tech stack, architecture pattern, key libraries, design lessons, GitHub star count, and a pre-computed 1536-dim embedding vector.

At runtime, agents call `find_similar_examples_by_text(query, top_k)` in `agents/rules/lookup.py`. This scores every example by **word-overlap similarity** between the query and the example's full content — no API call, no database, pure Python. For _"healthcare appointment booking for patients and doctors"_, it surfaces OpenEMR and OpenMRS with their actual architecture decisions; for _"freelance marketplace for digital assets"_, it surfaces Medusa and Spree.

In both modes the examples come from local JSON files — no pgvector query, no API call, no seeding required. They are available from the first request.

---

## Analytics (optional)

The app ships with optional [PostHog](https://posthog.com) and [Umami](https://umami.is) integration, both silently disabled unless their env vars are set. Tracked events (all anonymous — there are no user accounts) include `project_started`, `checkpoint_1_shown`, `checkpoint_1_approve/edit/reject`, `plan_ready`, `report_downloaded`, `prototype_downloaded`, and `flow_error`. Add `VITE_POSTHOG_KEY` (and optionally `VITE_UMAMI_SRC` + `VITE_UMAMI_WEBSITE_ID`) in your frontend env to enable.

---

## How Credits Are Protected

- **`DEMO_MODE=false` is the default.** All seven agents run without any API calls or database.
- **`DEMO_MODE` is a server-side variable** read once at startup. No HTTP request can change it.
- **Demo mode requires all keys.** Setting `DEMO_MODE=true` without `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` causes the server to exit immediately at startup with a clear error.
- **Secrets are never committed.** `.env` is in `.gitignore`; `.env.example` contains only placeholders.

---

## Contributing

1. Fork the repository and create a feature branch (`git checkout -b feat/my-feature`).
2. Backend and frontend can be developed independently.
3. Run the build before committing: `cd frontend && npm run build` (runs `tsc` + Vite).
4. Open a pull request with a clear description of what changed and why.

---

## License

MIT — see [LICENSE](LICENSE) for full text.
