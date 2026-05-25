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
│   │   ├── requirement_agent.py      # Claude + top 3 similar project examples as grounding (DEMO_MODE=true)
│   │   ├── clarification_agent.py    # Claude + top 3 similar project examples for gap analysis (DEMO_MODE=true)
│   │   ├── architecture_agent.py     # Claude + top 4 similar projects + curated arch docs (DEMO_MODE=true)
│   │   ├── techstack_agent.py        # Claude + top 4 similar projects + curated stack docs (DEMO_MODE=true)
│   │   ├── estimation_agent.py       # Claude + top 4 similar projects + estimation benchmarks (DEMO_MODE=true)
│   │   ├── report_agent.py           # 19-section HTML report — Claude version (DEMO_MODE=true)
│   │   ├── prototype_agent.py        # 5-screen wireframe — Claude version (DEMO_MODE=true)
│   │   └── rules/
│   │       ├── lookup.py             # Text similarity search over 81 projects + domain/stack/estimation tables
│   │       ├── requirement_rules.py  # Rule-based requirement extraction (default)
│   │       ├── clarification_rules.py# Feature-gap + domain clarification questions (default)
│   │       ├── architecture_rules.py # Text similarity → pattern vote + reference_projects (default)
│   │       ├── techstack_rules.py    # Curated stack + real_world_libraries from matches (default)
│   │       └── estimation_rules.py   # Scale heuristics + reference_projects from matches (default)
│   ├── report/
│   │   ├── template_report.py        # 19-section HTML report — template version (default)
│   │   └── template_prototype.py     # 5-screen wireframe — template version (default)
│   ├── graph/
│   │   ├── planning_graph.py         # LangGraph state machine — routes to rules or Claude
│   │   └── state.py                  # PlanningState TypedDict
│   ├── rag/
│   │   ├── corpus.py                 # OpenAI embed + pgvector search for curated reference docs
│   │   └── seed.py                   # Seeds 14 curated architecture/techstack/estimation docs into pgvector
│   ├── scripts/
│   │   ├── migrate_examples_to_supabase.py  # One-time: push 81 project embeddings → rag_corpus table
│   │   └── seed_from_github.py              # Scrapes new project profiles from GitHub
│   ├── data/
│   │   └── project_examples/         # 81 real-world project profiles (JSON + pre-computed embeddings)
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

## How the 81 Project Examples Are Used

Every project profile in `backend/data/project_examples/` contains: project name, problem statement, target users, core features, integrations, tech stack, architecture pattern, key libraries, design lessons, GitHub star count, and a pre-computed 1536-dim embedding vector.

At runtime, agents call `find_similar_examples_by_text(query, top_k)` in `lookup.py`. This scores every example by **word-overlap similarity** between the query and the example's full content field — no API call, no database, pure Python. For a query like _"healthcare appointment booking for patients and doctors"_, it surfaces OpenEMR and OpenMRS with their actual architecture decisions and design lessons. For _"freelance marketplace for digital assets"_, it surfaces Medusa and Spree.

The matched examples flow into agents in two ways:

**In DEMO_MODE=false (rule-based):**

| Agent | What the 81 projects provide |
|---|---|
| **Requirement** | Keyword regex → domain, scale, feature list, target users |
| **Clarification** | Top 4 similar projects → feature-gap questions (what those projects had that isn't in your requirements) merged with domain base questions |
| **Architecture** | Top 5 similar projects → pattern vote (most common architecture across matches) + `reference_projects` in the output |
| **Tech stack** | Curated domain stack + `reference_projects` + `real_world_libraries` aggregated from matched projects |
| **Estimation** | Scale + feature count heuristics + `reference_projects` from matched projects in the output |
| **Report** | 19-section HTML template populated with the structured plan |
| **Prototype** | 5-screen domain-aware wireframe with realistic hardcoded data |

**In DEMO_MODE=true (Claude-powered):**

| Agent | What the 81 projects provide |
|---|---|
| **Requirement** | Top 3 similar project profiles prepended as few-shot grounding before Claude extracts requirements |
| **Clarification** | Top 3 similar project profiles shown to Claude so it identifies feature gaps vs real precedents |
| **Architecture** | Top 4 similar project profiles + curated architecture reference docs passed to Claude |
| **Tech stack** | Top 4 similar project profiles + curated techstack reference docs passed to Claude |
| **Estimation** | Top 4 similar project profiles + curated estimation benchmark docs passed to Claude |

In both modes the examples come from local JSON files — no pgvector query, no API call, no seeding required. They are available from the first request.

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
