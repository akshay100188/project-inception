"""
One-time seed script — run with:
  cd backend && source .venv/bin/activate && python -m rag.seed
"""
import asyncio
from openai import AsyncOpenAI
from supabase import create_client
from config import settings

_openai = AsyncOpenAI(api_key=settings.openai_api_key)
_supabase = create_client(settings.supabase_url, settings.supabase_service_key)

CORPUS: list[dict] = [
    # ── Architecture ────────────────────────────────────────────────────────
    {
        "category": "architecture",
        "title": "Monolith Architecture — When to Use",
        "content": (
            "A monolith is a single deployable unit where all components share one codebase and database. "
            "Best for: MVPs and early-stage startups (faster iteration), teams under 5 engineers, "
            "CRUD-heavy applications, B2B SaaS under 10k users. "
            "The monolith-first approach (Martin Fowler) recommends starting here, then extracting services "
            "only when boundaries become clear. Key benefits: simpler debugging, lower operational overhead, "
            "shared transactions. Avoid when: globally distributed teams own separate domains, or services "
            "have wildly different scaling profiles."
        ),
    },
    {
        "category": "architecture",
        "title": "Microservices — When to Scale Beyond Monolith",
        "content": (
            "Microservices decompose a system into independently deployable services communicating via APIs or events. "
            "Best for: teams over 20 engineers, services with different scaling profiles (e.g. image processing vs auth), "
            "when different parts need different stacks, or when independent deployment velocity is critical. "
            "Costs: operational complexity (service discovery, distributed tracing, network latency), "
            "eventual consistency challenges. Netflix, Amazon, and Uber migrated from monoliths only after "
            "hitting clear pain points. Do not start here."
        ),
    },
    {
        "category": "architecture",
        "title": "Serverless / FaaS Architecture",
        "content": (
            "Serverless (AWS Lambda, Vercel Edge Functions, Supabase Edge Functions) runs code on demand with no "
            "server management. Best for: bursty/unpredictable traffic, event-driven pipelines, scheduled jobs, "
            "APIs with short execution times, hobby projects and MVPs with variable load. "
            "Limitations: cold starts (100–500ms), execution time limits, statelessness requires external state "
            "(Redis/DB), vendor lock-in. Cost-effective at low scale; expensive at high sustained traffic vs. "
            "always-on instances. Common pattern: serverless for background tasks, always-on for the core API."
        ),
    },
    {
        "category": "architecture",
        "title": "JAMstack — Static-First for Content and Marketing",
        "content": (
            "JAMstack (JavaScript, APIs, Markup) pre-renders pages at build time, delivers via CDN, and uses APIs "
            "for dynamic data. Best for: content sites, marketing sites, documentation, e-commerce with headless CMS, "
            "blogs. Tools: Next.js or Gatsby + Vercel/Netlify, headless CMS (Contentful, Sanity, Strapi). "
            "Benefits: sub-100ms TTFB via CDN caching, excellent SEO, low hosting cost. "
            "Not ideal for: highly dynamic or user-specific content, complex admin-heavy applications."
        ),
    },
    {
        "category": "architecture",
        "title": "Event-Driven Architecture",
        "content": (
            "EDA decouples services using events: producers emit; consumers react asynchronously. "
            "Best for: notification systems, order processing pipelines, audit logging, microservices communication, "
            "real-time features. Tools: Kafka (high throughput), RabbitMQ (reliable delivery), "
            "AWS SQS/SNS (managed), Supabase Realtime (simpler cases). "
            "Patterns: CQRS (separate read/write models), Event Sourcing (events as source of truth). "
            "Complexity cost: eventual consistency, debugging event chains, ordering guarantees."
        ),
    },
    {
        "category": "architecture",
        "title": "Architecture Patterns by Domain",
        "content": (
            "Fintech: monolith or microservices with strict data isolation, event sourcing for audit trails, "
            "CQRS for transaction history, idempotent payment operations, double-entry bookkeeping data model.\n"
            "EdTech: monolith-first, content delivery via CDN, video hosting via Cloudflare Stream or Mux, "
            "LMS patterns (course/enrollment/progress models).\n"
            "SaaS B2B: multi-tenant monolith (row-level isolation), Stripe subscription integration, "
            "RBAC, webhook delivery for integrations.\n"
            "Healthcare: strict patient data isolation, FHIR-compatible data models, mandatory audit logging, "
            "encryption at rest and in transit.\n"
            "Marketplace: two-sided model (buyers/sellers/listings), escrow/payment holding, "
            "search-heavy (Elasticsearch or pgvector), trust & safety pipeline.\n"
            "Mobile-first: API-first backend, push notifications (FCM/APNs), offline-first sync."
        ),
    },
    # ── Tech Stack ──────────────────────────────────────────────────────────
    {
        "category": "techstack",
        "title": "Frontend: React Ecosystem",
        "content": (
            "React is the dominant frontend choice. Ecosystem: Vite (fast dev, recommended for SPAs), "
            "Next.js (SSR/SSG/hybrid, best for SEO-critical apps), Remix (full-stack web). "
            "For SPAs: Vite + React + React Router + TanStack Query + Zustand. "
            "UI: Tailwind CSS (utility-first, fastest dev), shadcn/ui (copy-paste components), "
            "Radix UI (accessible primitives). "
            "Choose React when: large team, rich ecosystem, complex interactive UI, or hiring pool matters."
        ),
    },
    {
        "category": "techstack",
        "title": "Frontend: Alternatives — Vue, Svelte, Angular",
        "content": (
            "Vue 3: smaller learning curve, excellent DX, Nuxt.js for SSR. Good for smaller teams or simpler apps. "
            "Svelte: compiled, minimal runtime, best raw performance, smaller ecosystem. "
            "Ideal for performance-critical dashboards. "
            "Angular: enterprise-grade, opinionated, DI + RxJS, best for large teams that need conventions enforced. "
            "SolidJS: React-like syntax with fine-grained reactivity, top performance benchmarks. "
            "Recommendation: React for most cases, Vue for smaller teams, Svelte for perf-critical UIs."
        ),
    },
    {
        "category": "techstack",
        "title": "Backend: Python Ecosystem — FastAPI, Django, Flask",
        "content": (
            "FastAPI: async-native, OpenAPI auto-generated docs, Pydantic validation, best for API-first services "
            "and ML/AI-adjacent backends. Performance near Node.js. "
            "Django: batteries-included (ORM, admin, auth), best for CRUD-heavy apps and rapid prototyping. "
            "Django REST Framework for APIs. "
            "Flask: minimal, flexible, good for simple APIs and microservices. "
            "Choose FastAPI when: async needed, ML/AI integration, OpenAPI docs matter. "
            "Choose Django when: complex admin UI needed, team knows Django, fast MVP with full ORM."
        ),
    },
    {
        "category": "techstack",
        "title": "Backend: Node.js Ecosystem",
        "content": (
            "Express.js: minimal, battle-tested, huge ecosystem. Good default for Node. "
            "NestJS: opinionated, Angular-inspired DI + decorators, TypeScript-first, good for large teams. "
            "tRPC: end-to-end type safety for TypeScript monorepos (frontend + backend share types). "
            "Hono: ultra-fast, edge-compatible. Fastify: performance-focused Express alternative. "
            "Choose Node.js when: team is TypeScript-first, real-time features (WebSockets), "
            "or sharing code between frontend and backend."
        ),
    },
    {
        "category": "techstack",
        "title": "Database Selection Guide",
        "content": (
            "PostgreSQL: default choice for most apps. ACID compliant, excellent JSONB support, "
            "full-text search, row-level security, pgvector for AI features. "
            "Managed options: Supabase, Neon, Railway, RDS. "
            "MongoDB: document-oriented, flexible schema, good for content/catalogs. Avoid for financial data. "
            "Redis: in-memory caching, sessions, rate limiting, pub/sub, leaderboards. Not a primary database. "
            "DynamoDB: AWS-native, infinite scale, single-digit millisecond latency, complex query patterns. "
            "Supabase: PostgreSQL + auth + realtime + storage + edge functions — ideal for MVPs and startups."
        ),
    },
    {
        "category": "techstack",
        "title": "Infrastructure and Deployment",
        "content": (
            "Vercel: best-in-class for Next.js/React frontends, global CDN, preview deploys, generous free tier. "
            "Railway: simple backend + database deployment, supports any Dockerfile, PostgreSQL + Redis included, affordable. "
            "Render: similar to Railway, good free tier, PostgreSQL and Redis managed. "
            "Fly.io: global multi-region deployment, Docker-based, excellent for latency-sensitive apps. "
            "AWS/GCP/Azure: full control, complex, necessary at scale (>$50k/month infra) or enterprise compliance. "
            "Recommended for MVP: Vercel (frontend) + Railway or Render (backend) + Supabase (DB/auth). "
            "Cost: $0–50/month for early MVPs."
        ),
    },
    # ── Estimation ──────────────────────────────────────────────────────────
    {
        "category": "estimation",
        "title": "Feature Complexity Benchmarks",
        "content": (
            "Actual engineering time per feature (senior engineer, includes testing):\n"
            "- User auth (email/password + OAuth): 1–2 weeks\n"
            "- CRUD API (5–10 resources) with pagination/filters: 1–2 weeks\n"
            "- Real-time features (chat/notifications): 1–2 weeks\n"
            "- Payment integration (Stripe subscriptions): 1–2 weeks\n"
            "- File upload with CDN storage: 3–5 days\n"
            "- Full-text or vector search: 3–5 days\n"
            "- Admin dashboard: 1–2 weeks\n"
            "- Email system (transactional): 2–3 days\n"
            "- Mobile app (React Native, iOS + Android): 2× web estimate\n"
            "- Third-party API integration (each): 2–5 days\n"
            "Rule of thumb: double your gut estimate. Add 20% for testing, 20% for unexpected issues."
        ),
    },
    {
        "category": "estimation",
        "title": "Team Size and Velocity Models",
        "content": (
            "Solo developer: 1× velocity, high context-switching cost, best for MVPs under 3 months. "
            "2 engineers: ~1.6× velocity (coordination overhead), optimal for early startups. "
            "3–5 engineers: 2.5–3× velocity, needs clear ownership boundaries. "
            "5–10 engineers: needs dedicated PM/tech lead, ~30% coordination overhead. "
            "Velocity benchmarks: 1 senior engineer ≈ 40–50 story points/sprint; "
            "1 story point ≈ 4–6 hours focused work. "
            "Sprint overhead: ~10–15% of team time for planning, reviews, syncs. "
            "Recommended Phase 1 setup: 2 senior full-stack engineers, or 1 full-stack + 1 designer."
        ),
    },
    {
        "category": "estimation",
        "title": "MVP Scoping Principles",
        "content": (
            "The Lean MVP: ship the minimum that delivers core value to the target user. "
            "Cut for MVP: nice-to-have features, native mobile app (do mobile web first), "
            "advanced analytics (basic dashboard only), non-critical integrations, "
            "white-labeling, enterprise admin tooling. "
            "Keep for MVP: core value proposition (the one thing users come for), "
            "basic auth and user management, the primary happy path end-to-end, "
            "minimal but functional UI, single prod environment. "
            "Signal of good MVP scope: 2 engineers can build it in 6–10 weeks."
        ),
    },
    {
        "category": "estimation",
        "title": "Cost Estimation for Technical Projects",
        "content": (
            "Engineering cost benchmarks (USD, 2024):\n"
            "- Senior full-stack engineer (contractor): $100–150/hr, $15k–25k/month\n"
            "- Mid-level engineer: $70–100/hr, $10k–15k/month\n"
            "- Junior engineer: $40–60/hr\n"
            "- Agency/dev shop: $80–200/hr\n"
            "- Offshore team (Eastern Europe quality range): $50–80/hr\n"
            "Infrastructure: $0–200/month for MVP (Vercel + Railway + Supabase free tiers). "
            "At scale (10k+ users): $500–2000/month. "
            "MVP cost formula: (engineers × rate × hours) + infra + tools (~$200/month). "
            "Example: 2 seniors × $130/hr × 320hrs = $83k + $500 infra ≈ $85k for a serious 8-week MVP. "
            "Budget split: 70% engineering, 15% design, 10% infrastructure, 5% tools/services."
        ),
    },
]


async def seed():
    print(f"Seeding {len(CORPUS)} documents...")

    # Clear existing corpus
    _supabase.table("rag_corpus").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print("Cleared existing corpus.")

    for i, doc in enumerate(CORPUS):
        resp = await _openai.embeddings.create(
            model="text-embedding-3-small",
            input=f"{doc['title']}\n\n{doc['content']}",
        )
        embedding = resp.data[0].embedding

        _supabase.table("rag_corpus").insert({
            "category": doc["category"],
            "title": doc["title"],
            "content": doc["content"],
            "embedding": embedding,
        }).execute()

        print(f"  [{i + 1}/{len(CORPUS)}] {doc['title']}")

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
