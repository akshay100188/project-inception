"""
Rule-based clarification agent — no Claude API calls.
Returns domain-specific clarifying questions without an API call.
"""
import asyncio
from agents.rules.lookup import normalize_domain

_QUESTIONS: dict[str, list[str]] = {
    "ecommerce": [
        "Will the platform support multiple vendors/sellers, or a single merchant storefront?",
        "Which payment methods are required at launch — card, PayPal, crypto, or buy-now-pay-later?",
        "Do you need real-time inventory tracking and low-stock alerts?",
        "Should there be a native mobile app, or is a mobile-responsive web app sufficient?",
    ],
    "edtech": [
        "Will courses include video content, or primarily text-based lessons and quizzes?",
        "Should students be able to earn certificates or credentials on completion?",
        "Is live instructor-to-student interaction (live classes, Q&A) a requirement?",
        "Will the platform be B2C (individual learners) or B2B (corporate training teams)?",
    ],
    "fintech": [
        "What financial rail integrations are required — Stripe, Plaid, ACH, or others?",
        "Are there regulatory compliance requirements such as KYC, AML, or PCI-DSS?",
        "Will users need multi-currency support or operate in a single currency?",
        "Is this B2C (personal finance) or B2B (business accounts/billing)?",
    ],
    "healthcare": [
        "Does this need to comply with HIPAA or other regional health data regulations?",
        "Will the platform integrate with existing EHR/EMR systems (e.g. Epic, Cerner)?",
        "Should appointment booking support telemedicine/video consultations?",
        "Who manages access — patients self-serve, or providers manage patient records?",
    ],
    "erp": [
        "Which core ERP modules are needed at launch — HR, inventory, finance, or all three?",
        "Is multi-company or multi-branch support required from day one?",
        "Should the system integrate with existing accounting software (QuickBooks, Xero)?",
        "Will external vendors or customers need a self-service portal?",
    ],
    "social": [
        "Will content be public (Twitter-style) or private within networks/groups?",
        "Is real-time messaging a core feature or a phase-2 addition?",
        "Do you need content moderation tools built in for launch?",
        "Will there be a creator monetisation layer (subscriptions, tips, ads)?",
    ],
    "productivity": [
        "Is real-time collaborative editing (Google Docs-style) a day-one requirement?",
        "Should the tool integrate with existing platforms like Slack, GitHub, or Google Calendar?",
        "Will teams need granular permission levels (viewer / editor / admin)?",
        "Is a mobile app required at launch, or desktop/web first?",
    ],
    "saas": [
        "Will this be multi-tenant (shared infrastructure) or single-tenant per customer?",
        "What pricing model do you have in mind — per seat, usage-based, or flat subscription?",
        "Do enterprise customers need SSO (SAML/OIDC) or custom RBAC at launch?",
        "Is a self-serve onboarding flow required, or will sales/CS onboard customers manually?",
    ],
}

_DEFAULT_QUESTIONS = [
    "Who is the primary user — consumer, business, or internal team?",
    "What does success look like at the end of the MVP launch?",
    "Are there existing tools or systems this needs to integrate with on day one?",
    "What is the expected number of users at launch vs. six months later?",
]


async def run_clarification_agent(state: dict) -> dict:
    queue: asyncio.Queue = state["stream_queue"]
    await queue.put({"event": "agent_start", "agent": "clarification", "data": "Generating clarifying questions…"})

    requirements = state.get("requirements", {})
    domain = requirements.get("domain", "saas")
    norm = normalize_domain(domain)

    questions = _QUESTIONS.get(norm, _DEFAULT_QUESTIONS)

    await queue.put({"event": "agent_done", "agent": "clarification", "data": "Questions ready."})
    return {"clarification_questions": questions, "stage": "checkpoint_1"}
