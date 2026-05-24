"""
Shared lookup tables and helpers for rule-based agents.
Data is derived from the 81 real-world project examples in backend/data/project_examples/.
No API calls — pure deterministic logic.
"""
import json
import logging
from collections import Counter
from pathlib import Path

log = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "project_examples"

_examples_cache = None


def load_examples() -> list[dict]:
    global _examples_cache
    if _examples_cache is not None:
        return _examples_cache
    examples = []
    for f in sorted(_DATA_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text())
            if "metadata" in d:
                examples.append(d)
        except Exception as exc:
            log.warning("Could not load %s: %s", f.name, exc)
    _examples_cache = examples
    return _examples_cache


def normalize_domain(domain: str) -> str:
    d = domain.lower()
    if any(k in d for k in ["ecommerce", "e-commerce", "commerce", "shop", "store", "marketplace", "retail"]):
        return "ecommerce"
    if any(k in d for k in ["edtech", "education", "learning", "lms", "course", "e-learning"]):
        return "edtech"
    if any(k in d for k in ["fintech", "finance", "payment", "billing", "banking", "insurance"]):
        return "fintech"
    if any(k in d for k in ["health", "medical", "clinical", "hospital", "patient"]):
        return "healthcare"
    if any(k in d for k in ["erp", "crm", "enterprise", "resource planning"]):
        return "erp"
    if any(k in d for k in ["social", "network", "community", "messaging", "chat", "forum"]):
        return "social"
    if any(k in d for k in ["productivity", "project management", "task", "note", "issue"]):
        return "productivity"
    if any(k in d for k in ["saas", "b2b", "platform", "analytics", "dashboard"]):
        return "saas"
    return "saas"


def find_similar_examples(norm_domain: str, top_k: int = 5) -> list[dict]:
    """Return up to top_k examples whose domain normalizes to norm_domain."""
    examples = load_examples()
    matches = [
        ex for ex in examples
        if normalize_domain(ex["metadata"].get("domain", "")) == norm_domain
    ]
    return matches[:top_k] if matches else examples[:top_k]


def most_common_pattern(examples: list[dict], scale: str) -> str:
    patterns = [ex["metadata"].get("architecture_pattern", "monolith") for ex in examples]
    if not patterns:
        return "monolith" if scale != "large" else "microservices"
    counter = Counter(patterns)
    return counter.most_common(1)[0][0]


# ── Domain-specific component sets ──────────────────────────────────────────

_COMPONENTS = {
    "ecommerce": [
        {"name": "Web Storefront", "role": "Customer-facing product catalog and checkout", "tech_hint": "Next.js"},
        {"name": "Backend API", "role": "Business logic, orders, inventory, auth", "tech_hint": "Node.js / FastAPI"},
        {"name": "Database", "role": "Products, customers, orders", "tech_hint": "PostgreSQL"},
        {"name": "Payment Service", "role": "Checkout and subscription billing", "tech_hint": "Stripe"},
        {"name": "Admin Dashboard", "role": "Merchant back-office", "tech_hint": "React Admin"},
    ],
    "edtech": [
        {"name": "Learning Portal", "role": "Course catalog, lesson player, student dashboard", "tech_hint": "Next.js"},
        {"name": "Backend API", "role": "Auth, course management, progress tracking", "tech_hint": "Node.js / FastAPI"},
        {"name": "Database", "role": "Users, courses, lessons, enrollments", "tech_hint": "PostgreSQL"},
        {"name": "Media Storage", "role": "Video content and course assets", "tech_hint": "Cloudflare R2 / S3"},
        {"name": "Admin Panel", "role": "Instructor and content management", "tech_hint": "React Admin"},
    ],
    "fintech": [
        {"name": "Web App", "role": "User-facing financial dashboard", "tech_hint": "Next.js"},
        {"name": "Backend API", "role": "Transactions, accounts, compliance logic", "tech_hint": "Node.js / FastAPI"},
        {"name": "Database", "role": "Accounts, transactions, audit log", "tech_hint": "PostgreSQL"},
        {"name": "Payment Gateway", "role": "External payment rail integration", "tech_hint": "Stripe / Plaid"},
        {"name": "Auth Service", "role": "MFA, session management, OAuth", "tech_hint": "Auth0 / Supabase Auth"},
    ],
    "healthcare": [
        {"name": "Patient Portal", "role": "Appointments, records, messaging", "tech_hint": "Next.js"},
        {"name": "Backend API", "role": "Clinical data, auth, integrations", "tech_hint": "Node.js / FastAPI"},
        {"name": "Database", "role": "Patients, appointments, records", "tech_hint": "PostgreSQL"},
        {"name": "Auth & Access Control", "role": "Role-based access, HIPAA compliance", "tech_hint": "Auth0"},
        {"name": "Notification Service", "role": "Appointment reminders and alerts", "tech_hint": "Twilio / SendGrid"},
    ],
    "erp": [
        {"name": "Admin Web App", "role": "ERP modules: HR, inventory, finance", "tech_hint": "React"},
        {"name": "Backend API", "role": "Business rules, workflows, reports", "tech_hint": "Node.js / FastAPI"},
        {"name": "Database", "role": "Master data and transactional records", "tech_hint": "PostgreSQL"},
        {"name": "Background Jobs", "role": "Scheduled reports and async workflows", "tech_hint": "Celery / BullMQ"},
        {"name": "Auth & Roles", "role": "Multi-tenant access control", "tech_hint": "Supabase Auth / Auth0"},
    ],
    "social": [
        {"name": "Web / Mobile App", "role": "Feed, profiles, messaging UI", "tech_hint": "Next.js / React Native"},
        {"name": "Backend API", "role": "Posts, follows, notifications, feeds", "tech_hint": "Node.js / FastAPI"},
        {"name": "Database", "role": "Users, posts, relationships", "tech_hint": "PostgreSQL"},
        {"name": "Real-time Layer", "role": "Live feed updates and chat", "tech_hint": "Supabase Realtime / Socket.io"},
        {"name": "Media Storage", "role": "Images and video uploads", "tech_hint": "Cloudflare R2 / S3"},
    ],
    "productivity": [
        {"name": "Web App", "role": "Task boards, docs, calendar", "tech_hint": "Next.js / React"},
        {"name": "Backend API", "role": "Workspaces, permissions, sync", "tech_hint": "Node.js / FastAPI"},
        {"name": "Database", "role": "Tasks, projects, users, activity", "tech_hint": "PostgreSQL"},
        {"name": "Real-time Sync", "role": "Collaborative editing and live updates", "tech_hint": "Supabase Realtime / Liveblocks"},
        {"name": "Auth Service", "role": "SSO and team management", "tech_hint": "Supabase Auth / Auth0"},
    ],
    "saas": [
        {"name": "Web App", "role": "Core product UI and onboarding", "tech_hint": "Next.js / React"},
        {"name": "Backend API", "role": "Core logic, multi-tenancy, integrations", "tech_hint": "Node.js / FastAPI"},
        {"name": "Database", "role": "Tenants, users, product data", "tech_hint": "PostgreSQL"},
        {"name": "Auth & Billing", "role": "Login, teams, subscription management", "tech_hint": "Auth0 + Stripe"},
        {"name": "Background Workers", "role": "Async jobs, webhooks, emails", "tech_hint": "BullMQ / Celery"},
    ],
}


def get_components(norm_domain: str, pattern: str) -> list[dict]:
    base = _COMPONENTS.get(norm_domain, _COMPONENTS["saas"])
    if pattern == "microservices":
        return [{"name": "API Gateway", "role": "Routes requests to downstream services", "tech_hint": "Kong / Nginx"}] + base
    return base


# ── Modern stack recommendations per domain ──────────────────────────────────

_STACKS = {
    "ecommerce": {
        "frontend": {"name": "Next.js", "rationale": "SSR for SEO-critical product pages", "key_libs": ["Tailwind CSS", "Zustand", "React Query"]},
        "backend": {"name": "Node.js + Express", "rationale": "Fast JSON APIs, large npm ecosystem for commerce", "key_libs": ["Prisma", "Stripe SDK", "Zod"]},
        "database": {"name": "PostgreSQL", "rationale": "ACID transactions essential for orders and inventory", "schema_hint": "products, orders, order_items, customers, inventory"},
        "auth": {"name": "Supabase Auth", "rationale": "Managed auth with social login and magic links"},
        "infrastructure": {"name": "Vercel + Supabase", "rationale": "Zero-config deploys; managed Postgres with RLS"},
        "mobile": None,
    },
    "edtech": {
        "frontend": {"name": "Next.js", "rationale": "SSR for course SEO; rich client-side video player", "key_libs": ["Tailwind CSS", "React Player", "React Query"]},
        "backend": {"name": "FastAPI (Python)", "rationale": "Async support for media processing; Python AI ecosystem", "key_libs": ["SQLAlchemy", "Pydantic", "Celery"]},
        "database": {"name": "PostgreSQL", "rationale": "Relational model fits courses, enrollments, and progress", "schema_hint": "users, courses, lessons, enrollments, progress, quizzes"},
        "auth": {"name": "Supabase Auth", "rationale": "Handles student/instructor roles out of the box"},
        "infrastructure": {"name": "Vercel + Supabase + Cloudflare R2", "rationale": "CDN-backed media storage; serverless frontend deploys"},
        "mobile": None,
    },
    "fintech": {
        "frontend": {"name": "Next.js", "rationale": "SSR for fast dashboards; strong TypeScript support", "key_libs": ["Tailwind CSS", "Recharts", "React Hook Form"]},
        "backend": {"name": "Node.js + Express", "rationale": "High-throughput transaction processing; broad payment SDK support", "key_libs": ["Prisma", "Stripe", "Zod", "Bull"]},
        "database": {"name": "PostgreSQL", "rationale": "Strong consistency for financial records; audit log support", "schema_hint": "accounts, transactions, ledger, users, kyc_records"},
        "auth": {"name": "Auth0", "rationale": "Enterprise-grade MFA and compliance features"},
        "infrastructure": {"name": "AWS / Railway + PostgreSQL", "rationale": "SOC2-ready infrastructure; isolated VPC for PII"},
        "mobile": None,
    },
    "healthcare": {
        "frontend": {"name": "Next.js", "rationale": "Accessible UI components; server-side data protection", "key_libs": ["Tailwind CSS", "React Hook Form", "date-fns"]},
        "backend": {"name": "FastAPI (Python)", "rationale": "Python ecosystem for HL7/FHIR integrations; async IO", "key_libs": ["SQLAlchemy", "Pydantic", "python-jose"]},
        "database": {"name": "PostgreSQL", "rationale": "HIPAA-compatible with row-level security and audit logging", "schema_hint": "patients, appointments, records, providers, audit_log"},
        "auth": {"name": "Auth0", "rationale": "HIPAA-eligible, MFA, fine-grained role management"},
        "infrastructure": {"name": "AWS (HIPAA BAA) + RDS PostgreSQL", "rationale": "HIPAA Business Associate Agreement available; encrypted at rest"},
        "mobile": None,
    },
    "erp": {
        "frontend": {"name": "React + Vite", "rationale": "Data-dense admin UI with tables, forms, dashboards", "key_libs": ["Ant Design", "React Query", "Recharts"]},
        "backend": {"name": "Node.js + Express", "rationale": "Flexible API layer for complex business workflows", "key_libs": ["Prisma", "BullMQ", "Zod"]},
        "database": {"name": "PostgreSQL", "rationale": "Complex relational data with multi-tenant row-level security", "schema_hint": "tenants, users, roles, inventory, hr_records, finance_entries"},
        "auth": {"name": "Supabase Auth", "rationale": "Built-in multi-tenant RLS policies"},
        "infrastructure": {"name": "Railway + Supabase", "rationale": "Managed Postgres with RLS; simple container deploys"},
        "mobile": None,
    },
    "social": {
        "frontend": {"name": "Next.js", "rationale": "SEO-friendly public profiles; real-time feed updates", "key_libs": ["Tailwind CSS", "Zustand", "SWR"]},
        "backend": {"name": "Node.js + Express", "rationale": "High concurrency for feed fanout and WebSocket connections", "key_libs": ["Prisma", "Socket.io", "Bull"]},
        "database": {"name": "PostgreSQL + Redis", "rationale": "Relational core for users/posts; Redis for feed caching", "schema_hint": "users, posts, follows, likes, comments, notifications"},
        "auth": {"name": "Supabase Auth", "rationale": "Social OAuth (Google, GitHub) with minimal configuration"},
        "infrastructure": {"name": "Vercel + Supabase + Cloudflare R2", "rationale": "Edge CDN for media; managed real-time subscriptions"},
        "mobile": None,
    },
    "productivity": {
        "frontend": {"name": "Next.js", "rationale": "Rich interactive UI with offline-first considerations", "key_libs": ["Tailwind CSS", "Zustand", "Liveblocks"]},
        "backend": {"name": "Node.js + Express", "rationale": "WebSocket support for real-time collaboration", "key_libs": ["Prisma", "Socket.io", "Zod"]},
        "database": {"name": "PostgreSQL", "rationale": "Flexible schema for tasks, projects, and workspaces", "schema_hint": "workspaces, projects, tasks, users, comments, activity_log"},
        "auth": {"name": "Supabase Auth", "rationale": "Team invites, SSO, and magic links built-in"},
        "infrastructure": {"name": "Vercel + Supabase", "rationale": "Supabase Realtime handles collaborative sync"},
        "mobile": None,
    },
    "saas": {
        "frontend": {"name": "Next.js", "rationale": "Fast onboarding pages, dashboard, and marketing site", "key_libs": ["Tailwind CSS", "React Query", "Recharts"]},
        "backend": {"name": "Node.js + Express", "rationale": "Scalable REST API with multi-tenant isolation", "key_libs": ["Prisma", "Stripe", "BullMQ", "Zod"]},
        "database": {"name": "PostgreSQL", "rationale": "Multi-tenant RLS; strong consistency for billing data", "schema_hint": "tenants, users, subscriptions, usage_events, api_keys"},
        "auth": {"name": "Supabase Auth / Auth0", "rationale": "SSO, team management, and JWT-based API auth"},
        "infrastructure": {"name": "Vercel + Supabase / Railway", "rationale": "Managed Postgres, zero-ops deploys, global CDN"},
        "mobile": None,
    },
}


def get_stack(norm_domain: str) -> dict:
    return _STACKS.get(norm_domain, _STACKS["saas"])


# ── Estimation tables ────────────────────────────────────────────────────────

def estimate(scale: str, feature_count: int, norm_domain: str) -> dict:
    s = scale.lower() if scale else "medium"

    if s in ("small", "mvp") or feature_count <= 4:
        mvp_weeks, full_weeks, team_size = 6, 14, 2
        mvp_low, mvp_high = 15_000, 30_000
        confidence = "high"
    elif s == "large" or feature_count >= 10:
        mvp_weeks, full_weeks, team_size = 20, 40, 4
        mvp_low, mvp_high = 60_000, 120_000
        confidence = "medium"
    else:
        mvp_weeks, full_weeks, team_size = 12, 24, 3
        mvp_low, mvp_high = 30_000, 60_000
        confidence = "high"

    domain_roles = {
        "fintech":    ["Backend Engineer", "Frontend Engineer", "Security Engineer", "QA Engineer"],
        "healthcare": ["Backend Engineer", "Frontend Engineer", "Compliance Engineer", "QA Engineer"],
        "ecommerce":  ["Full-Stack Engineer", "Frontend Engineer", "DevOps Engineer"],
        "edtech":     ["Full-Stack Engineer", "Frontend Engineer", "Content Engineer"],
    }
    roles = domain_roles.get(norm_domain, ["Full-Stack Engineer", "Frontend Engineer", "Backend Engineer", "DevOps Engineer"])[:team_size]

    phases = [
        {"name": "Discovery & Setup",     "weeks": max(1, mvp_weeks // 6), "deliverables": ["Repo setup", "CI/CD pipeline", "DB schema v1"]},
        {"name": "Core Feature Build",    "weeks": max(2, mvp_weeks // 3), "deliverables": ["Primary user flows", "API endpoints", "Auth integration"]},
        {"name": "Integration & Testing", "weeks": max(2, mvp_weeks // 4), "deliverables": ["Third-party integrations", "E2E tests", "Performance baseline"]},
        {"name": "MVP Launch",            "weeks": max(1, mvp_weeks // 6), "deliverables": ["Production deploy", "Monitoring setup", "Soft launch"]},
    ]

    risks = [
        "Third-party API reliability and rate limits may affect timeline",
        "Scope creep from stakeholder feedback during build phase",
        "Integration complexity may exceed initial estimates",
        "Team ramp-up time on unfamiliar parts of the stack",
    ]
    if norm_domain == "fintech":
        risks.insert(0, "Regulatory compliance and KYC requirements add non-trivial scope")
    elif norm_domain == "healthcare":
        risks.insert(0, "HIPAA compliance audit and BAA negotiations can delay launch")

    return {
        "mvp_weeks": mvp_weeks,
        "full_product_weeks": full_weeks,
        "recommended_team": {"size": team_size, "roles": roles},
        "phases": phases,
        "cost_range": {
            "mvp_low": mvp_low,
            "mvp_high": mvp_high,
            "currency": "USD",
            "basis": f"{team_size} engineers at $100–150/hr",
        },
        "confidence": confidence,
        "risks": risks[:4],
    }
