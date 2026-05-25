"""
Rule-based clarification agent — no Claude API calls.
Returns domain-specific clarifying questions, enriched with feature-gap
questions derived from the 81 real-world project examples.
"""
import asyncio
from agents.rules.lookup import (
    normalize_domain, find_similar_examples_by_text, extract_reference_projects,
)

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


def _gap_questions(requirements: dict, refs: list[dict]) -> list[str]:
    """
    Generate up to 2 feature-gap questions by comparing what similar real projects
    included against what the user's requirements already mention.
    """
    mentioned = " ".join([
        requirements.get("project_name", ""),
        requirements.get("problem_statement", ""),
        " ".join(f.get("feature", "") for f in requirements.get("core_features", [])
                 if isinstance(f, dict)),
    ]).lower()

    # Collect features from similar projects that aren't mentioned in requirements
    _FEATURE_QUESTIONS = {
        "payment":        "How will payments be handled — Stripe, PayPal, or another provider?",
        "auth":           "What authentication methods are required — email/password, OAuth (Google, GitHub), or SSO?",
        "notification":   "Should the app send real-time notifications — email, push, in-app, or SMS?",
        "search":         "Do users need full-text or semantic search across the main content?",
        "analytics":      "Is a built-in analytics or reporting dashboard required at launch?",
        "admin":          "Does the team need an admin back-office to manage users and content?",
        "mobile":         "Is a native mobile app required, or is a mobile-responsive web app sufficient for launch?",
        "multi-tenant":   "Will this be multi-tenant (one instance, many customers) or single-tenant per customer?",
        "billing":        "Is subscription billing or usage-based pricing required at launch?",
        "api":            "Do third parties or customers need a public API or webhooks to integrate with?",
        "upload":         "Will users upload files, images, or videos — and if so, what are the size/format requirements?",
        "real-time":      "Does any feature require real-time updates — live feeds, collaborative editing, or chat?",
        "moderation":     "Is content moderation or trust-and-safety tooling needed at launch?",
        "export":         "Do users need to export data — CSV, PDF, or via API?",
        "role":           "What user roles are needed beyond basic auth — e.g. admin, editor, viewer, guest?",
    }

    gap_questions = []
    for ref in refs:
        for feature in ref.get("tech_stack", {}).get("key_libraries", []):
            pass  # key_libraries aren't features — skip
        for lesson in ref.get("design_lessons", []):
            lesson_lower = lesson.lower()
            for keyword, question in _FEATURE_QUESTIONS.items():
                if keyword in lesson_lower and keyword not in mentioned and question not in gap_questions:
                    gap_questions.append(question)
                    if len(gap_questions) >= 2:
                        return gap_questions

        # Also check feature names from the reference project's raw profile
        for feat_kw, question in _FEATURE_QUESTIONS.items():
            ref_content = (ref.get("domain", "") + " " +
                           " ".join(str(v) for v in ref.get("tech_stack", {}).values())).lower()
            if feat_kw in ref_content and feat_kw not in mentioned and question not in gap_questions:
                gap_questions.append(question)
                if len(gap_questions) >= 2:
                    return gap_questions

    return gap_questions


async def run_clarification_agent(state: dict) -> dict:
    queue: asyncio.Queue = state["stream_queue"]
    await queue.put({"event": "agent_start", "agent": "clarification", "data": "Generating clarifying questions…"})

    requirements = state.get("requirements", {})
    raw_input = state.get("raw_input", "")
    domain = requirements.get("domain", "saas")
    norm = normalize_domain(domain)

    # Start with domain-specific base questions
    base_questions = _QUESTIONS.get(norm, _DEFAULT_QUESTIONS)

    # Find similar projects and surface feature gaps as additional questions
    query = f"{raw_input} {requirements.get('raw_summary', '')}".strip() or domain
    similar = find_similar_examples_by_text(query, top_k=4)
    refs = extract_reference_projects(similar)
    gap_questions = _gap_questions(requirements, refs)

    # Merge: gap questions first (most specific), then domain base questions, deduplicated
    seen: set[str] = set()
    questions: list[str] = []
    for q in gap_questions + base_questions:
        if q not in seen:
            seen.add(q)
            questions.append(q)
        if len(questions) >= 4:
            break

    await queue.put({"event": "agent_done", "agent": "clarification", "data": "Questions ready."})
    return {"clarification_questions": questions, "stage": "checkpoint_1"}
