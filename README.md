# Project Inception

**Turn a rough idea into a complete, reviewer-approved software specification — no AI credits required.**

Describe your product idea in plain English. Five agents extract requirements, design system architecture, select a technology stack, and estimate timeline and cost. Two human-in-the-loop checkpoints let you review and edit before anything is saved. The final output is a structured plan you can download as a 19-section HTML report plus a 5-screen interactive wireframe.

> **Default mode uses zero Anthropic credits.** Every agent — requirements, clarification, architecture, tech stack, estimation, report, and prototype — runs without a single API call, grounded in 81 real-world open-source projects. An optional `DEMO_MODE=true` flag switches every agent to Claude Sonnet if you want the full AI experience.

---

## How It Works

```
Your Idea (text or uploaded doc)
        │
        ▼
┌─────────────────────┐
│  Requirement Agent  │  Extracts structured requirements
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Clarification Agent │  Generates targeted questions about gaps
└──────────┬──────────┘
           │
           ▼
   ┌───────────────┐
   │ Checkpoint 1  │  ← You review & approve (or edit) requirements
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
                         │
                         ▼
                 ┌───────────────┐
                 │ Checkpoint 2  │  ← You review & save (or discard)
                 └───────┬───────┘
                         │
                         ▼
              Plan saved to Supabase
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Download Report        Download Wireframe
      (19-section HTML)      (5-screen prototype)
```

### Two modes, one codebase

| | Default (`DEMO_MODE=false`) | Demo (`DEMO_MODE=true`) |
|---|---|---|
| Requirement extraction | Rule-based — keyword + heuristic parsing | Claude Sonnet |
| Clarification questions | Rule-based — 4 domain-specific fixed questions | Claude Sonnet |
| Architecture design | Rule-based — matched against 81 real projects | Claude Sonnet |
| Tech stack selection | Rule-based — curated domain tables | Claude Sonnet |
| Timeline & cost estimation | Rule-based — scale + feature count heuristics | Claude Sonnet |
| HTML planning report | Template — 19-section instant generation | Claude Sonnet (4 parallel calls) |
| Interactive wireframe | Template — 5-screen domain-aware prototype | Claude Sonnet (3 parallel calls) |
| Anthropic API key needed | **No** | Yes |
| OpenAI API key needed | **No** | Yes |

> **`DEMO_MODE` is a server-side environment variable.** It is read once at startup from the environment. No HTTP request from any user — authenticated or not — can change it. Setting it to `false` (the default) permanently disables all Claude API calls for that deployment.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript + Tailwind CSS → **Vercel** |
| Backend | FastAPI + LangGraph → **Railway** (Docker) |
| AI (optional) | Claude Sonnet — all agents when `DEMO_MODE=true` only |
| Database | Supabase (PostgreSQL + pgvector + Auth) |
| Streaming | Server-Sent Events (SSE) with asyncio-based human-in-the-loop pauses |
| Rule engine | 81 real-world open-source project profiles in `backend/data/project_examples/` |

---

## Prerequisites

| Service | What you need | Free tier? |
|---|---|---|
| [Supabase](https://supabase.com) | Project URL + anon key + service role key | Yes |
| [Railway](https://railway.app) | Account for backend deploy | $5/mo hobby plan |
| [Vercel](https://vercel.com) | Account for frontend deploy | Yes |
| [Anthropic](https://console.anthropic.com) | API key — **only needed when `DEMO_MODE=true`** | Pay-per-use |
| [OpenAI](https://platform.openai.com) | API key — **only needed when `DEMO_MODE=true`** | Pay-per-use |

> The default deployment requires **no AI API keys at all.** You only need Supabase (database + auth), Railway (backend host), and Vercel (frontend host).

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

Edit `.env` — the minimum required fields:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
CORS_ORIGINS=http://localhost:5173
DEMO_MODE=false
```

No API keys needed. Start the server:

```bash
uvicorn main:app --reload
# → API running at http://localhost:8000
```

### 4. Configure and start the frontend

```bash
cd ../frontend
npm install
cp .env.example .env.local
```

Edit `.env.local`:

```env
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_API_URL=http://localhost:8000
```

```bash
npm run dev
# → App running at http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173), sign in with a magic link, and click **+ New Project**.

---

## Running in Demo Mode (Claude-powered)

To switch all agents to Claude Sonnet, add the following to `backend/.env`:

```env
DEMO_MODE=true
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

> The server validates both keys at startup and **exits immediately** with a clear error message if either is missing when `DEMO_MODE=true`. This prevents silent mid-request failures.

To revert to zero-credit mode, set `DEMO_MODE=false` and remove or leave blank both API keys.

---

## Environment Variables

### Backend — `backend/.env`

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | **Yes** | Your Supabase project REST URL (`https://xxxx.supabase.co`). |
| `SUPABASE_SERVICE_KEY` | **Yes** | Your Supabase **service role** key. Keep this server-side only. |
| `CORS_ORIGINS` | **Yes** | Comma-separated allowed origins. Local dev: `http://localhost:5173`. |
| `DEMO_MODE` | No | `false` (default) — all agents rule-based, zero credits. `true` — all agents use Claude Sonnet. |
| `ANTHROPIC_API_KEY` | Only if `DEMO_MODE=true` | Your Anthropic API key. Server exits at startup without it when `DEMO_MODE=true`. |
| `OPENAI_API_KEY` | Only if `DEMO_MODE=true` | Your OpenAI key (RAG corpus embeddings). Server exits at startup without it when `DEMO_MODE=true`. |
| `GITHUB_TOKEN` | No | Raises GitHub API rate limit from 60 → 5000 req/hr during RAG seeding. |

### Frontend — `frontend/.env.local`

| Variable | Required | Description |
|---|---|---|
| `VITE_SUPABASE_URL` | **Yes** | Same Supabase project URL as above. |
| `VITE_SUPABASE_ANON_KEY` | **Yes** | Your Supabase **anon** key. Safe to expose in browser. |
| `VITE_API_URL` | **Yes** | Backend URL. Local dev: `http://localhost:8000`. Production: your Railway URL. |
| `VITE_POSTHOG_KEY` | No | PostHog project API key — enables usage analytics. Leave blank to disable silently. |
| `VITE_POSTHOG_HOST` | No | PostHog ingest host. Defaults to `https://us.i.posthog.com`. |

---

## Deploying to Production

### Step 1 — Push to GitHub

```bash
git remote add origin https://github.com/your-username/project-inception.git
git push -u origin main
```

### Step 2 — Deploy backend to Railway

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. Select this repository, set **Root Directory** to `backend`
3. Railway detects the `Dockerfile` automatically
4. In the Railway dashboard → service → **Variables**, add:

   | Variable | Value |
   |---|---|
   | `SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `SUPABASE_SERVICE_KEY` | `eyJ...` (service role key) |
   | `CORS_ORIGINS` | `https://your-app.vercel.app` |
   | `DEMO_MODE` | `false` |

   > Do **not** add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` unless you intentionally want `DEMO_MODE=true`.

5. Copy the Railway **Public Domain** URL after deploy

### Step 3 — Deploy frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New → Project**
2. Import your GitHub repository, set **Root Directory** to `frontend`
3. Add environment variables:

   | Variable | Value |
   |---|---|
   | `VITE_SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `VITE_SUPABASE_ANON_KEY` | `eyJ...` (anon key) |
   | `VITE_API_URL` | Your Railway backend URL |
   | `VITE_POSTHOG_KEY` | Your PostHog key (optional) |

4. Click **Deploy**

### Step 4 — Configure Supabase Auth for production

In Supabase dashboard → **Authentication → URL Configuration**:

- **Site URL**: `https://your-app.vercel.app`
- **Redirect URLs**: `https://your-app.vercel.app/**`

### Step 5 — Update CORS

Update `CORS_ORIGINS` in Railway to include your Vercel URL. Railway redeploys automatically.

---

## Project Structure

```
project-inception/
├── backend/
│   ├── agents/
│   │   ├── requirement_agent.py      # Requirement extraction — Claude version (DEMO_MODE=true)
│   │   ├── clarification_agent.py    # Clarifying questions — Claude version (DEMO_MODE=true)
│   │   ├── architecture_agent.py     # Architecture design — Claude version (DEMO_MODE=true)
│   │   ├── techstack_agent.py        # Tech stack selection — Claude version (DEMO_MODE=true)
│   │   ├── estimation_agent.py       # Timeline/budget estimation — Claude version (DEMO_MODE=true)
│   │   ├── report_agent.py           # 19-section HTML report — Claude version (DEMO_MODE=true)
│   │   ├── prototype_agent.py        # 5-screen wireframe — Claude version (DEMO_MODE=true)
│   │   └── rules/
│   │       ├── lookup.py             # Shared domain maps, stack tables, estimation logic (81 projects)
│   │       ├── requirement_rules.py  # Rule-based requirement extraction (default)
│   │       ├── clarification_rules.py# Rule-based clarification questions (default)
│   │       ├── architecture_rules.py # Rule-based architecture agent (default)
│   │       ├── techstack_rules.py    # Rule-based tech stack agent (default)
│   │       └── estimation_rules.py   # Rule-based estimation agent (default)
│   ├── report/
│   │   ├── template_report.py        # 19-section HTML report — template version (default)
│   │   └── template_prototype.py     # 5-screen wireframe — template version (default)
│   ├── graph/
│   │   ├── planning_graph.py         # LangGraph state machine — routes to rules or Claude
│   │   └── state.py                  # PlanningState TypedDict
│   ├── rag/
│   │   ├── corpus.py                 # OpenAI embed + pgvector search (DEMO_MODE=true)
│   │   └── seed.py                   # One-time corpus seeder
│   ├── data/
│   │   └── project_examples/         # 81 real-world project profiles (JSON)
│   ├── api/
│   │   ├── stream.py                 # SSE /api/stream/{project_id} endpoint
│   │   ├── projects.py               # Project CRUD + checkpoint resolver + report/prototype endpoints
│   │   ├── upload.py                 # PDF/DOCX/TXT document parser
│   │   └── admin.py                  # Internal admin endpoints
│   ├── checkpoint_registry.py        # asyncio.Event human-in-the-loop pauses
│   ├── config.py                     # Pydantic settings (reads .env)
│   ├── main.py                       # FastAPI app entry point + startup guard
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Checkpoint/           # Requirements review modal
│       │   ├── PlanOutput/           # Architecture + tech stack + estimation cards
│       │   └── Nav/
│       ├── hooks/
│       │   └── useAgentStream.ts     # SSE consumer + analytics tracking
│       ├── lib/
│       │   ├── supabase.ts
│       │   └── analytics.ts          # PostHog wrapper — no-ops when key absent
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Dashboard.tsx
│       │   ├── NewProject.tsx
│       │   └── ProjectDetail.tsx
│       └── App.tsx
├── supabase/
│   └── schema.sql                    # incept_projects + rag_corpus tables + pgvector
├── DEMO.md                           # Loom recording script (for DEMO_MODE=true)
└── README.md
```

---

## How the Rule Engine Works

In default mode, every agent is powered by `backend/agents/rules/lookup.py` and a set of 81 real-world open-source project profiles stored in `backend/data/project_examples/`.

| Agent | What it does without Claude |
|---|---|
| **Requirement** | Keyword regex over the free-form idea text → domain, scale, feature list, target users |
| **Clarification** | Returns 4 pre-written domain-specific questions (ecommerce, edtech, fintech, healthcare, erp, social, productivity, saas) |
| **Architecture** | Finds the 3 closest project examples by domain + scale → derives pattern and component list |
| **Tech stack** | Looks up a curated, opinionated stack per domain (e.g. fintech → Next.js + FastAPI + PostgreSQL + Plaid) |
| **Estimation** | Applies scale-and-feature-count heuristics calibrated against the 81 example projects |
| **Report** | Fills a 19-section HTML template with the structured plan data |
| **Prototype** | Renders a 5-screen domain-aware HTML wireframe using hardcoded realistic sample data |

---

## Analytics (PostHog)

The app ships with built-in [PostHog](https://posthog.com) integration. Completely optional — silently disabled unless `VITE_POSTHOG_KEY` is set.

### What's tracked

| Event | Trigger |
|---|---|
| `$pageview` | Every page navigation (auto) |
| `user_identified` | On login — links events to a user |
| `project_started` | User submits an idea (`input_length`, `has_upload`) |
| `flow_stage_complete` | Each agent finishes (`stage`: requirement / clarification / architecture / techstack / estimation) |
| `checkpoint_1_shown` | Requirements review modal opens |
| `checkpoint_1_approve/edit/reject` | User acts on requirements (`was_edited`) |
| `plan_ready` | Plan reaches checkpoint 2 (`domain`, `scale`, `feature_count`, `mvp_weeks`, `architecture_pattern`) |
| `plan_saved` / `plan_rejected` | User saves or discards the plan |
| `report_downloaded` | User downloads the HTML report |
| `prototype_downloaded` | User downloads the wireframe |
| `flow_error` | An agent errors mid-pipeline (`stage`) |

### Setup

1. Create a free account at [posthog.com](https://posthog.com)
2. Go to **Project Settings → Project API Key** and copy the key
3. Add to `frontend/.env.local`:

```env
VITE_POSTHOG_KEY=phc_...
VITE_POSTHOG_HOST=https://us.i.posthog.com
```

4. For production (Vercel), add the same variables in the Vercel dashboard

### Useful PostHog views

- **Funnels** → `project_started` → `checkpoint_1_shown` → `plan_ready` → `plan_saved` → `report_downloaded` — see drop-off at each stage
- **Insights → Trends** → plot `project_started` over time to see daily active usage
- **Insights → Breakdown** → break `plan_ready` by `domain` to see which project types are most popular
- **Session Replay** → watch exactly how users navigate and where they get stuck

---

## How Credits Are Protected

- **`DEMO_MODE=false` is the default.** All seven agents (requirement, clarification, architecture, tech stack, estimation, report, prototype) run without any API calls.
- **`DEMO_MODE` is a server-side variable.** No HTTP request from any user can change it — it is read once at server startup from the environment.
- **Both API keys are required to enable demo mode.** Setting `DEMO_MODE=true` without `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` causes the server to exit immediately at startup with a clear error.
- **API keys are never committed.** `.env` is in `.gitignore`. The `.env.example` file contains only empty placeholders.

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
