"""
Rule-based architecture agent — no Claude API calls.
Derives architecture from domain + scale by matching against the 81 project examples.
"""
import asyncio
from agents.rules.lookup import (
    normalize_domain, find_similar_examples_by_text,
    most_common_pattern, get_components, extract_reference_projects,
)

_PATTERN_DESC = {
    "monolith":      "A single deployable unit handles all concerns — ideal for fast iteration and small-to-medium teams.",
    "microservices": "Independently deployable services per domain — justified by scale, team size, or isolated reliability requirements.",
    "serverless":    "Function-based compute with no server management — suited for event-driven workloads with variable traffic.",
    "jamstack":      "Pre-rendered frontend with headless APIs — optimizes for performance and CDN-edge delivery.",
    "event-driven":  "Services communicate through an event bus — decouples producers from consumers for high-throughput async flows.",
}

_DATA_FLOW = {
    "monolith":      "User request → Load balancer → Application server (auth → business logic → DB query) → JSON response → Client render.",
    "microservices": "Client → API Gateway (auth + routing) → Domain service → Service DB → Event bus (async side-effects) → Response.",
    "serverless":    "Client → CDN / edge → Serverless function (stateless handler) → Managed DB / storage → Response.",
    "jamstack":      "Browser → CDN (pre-rendered HTML) → Client-side JS → Headless API → DB → JSON response.",
    "event-driven":  "Producer emits event → Message broker → Consumer service processes → State change persisted → Optional reply event.",
}

_KEY_DECISIONS = {
    "monolith": [
        "Single deployable unit reduces operational overhead for early-stage teams",
        "Shared database simplifies transactions and consistency guarantees",
        "Vertical scaling covers MVP load; horizontal sharding deferred until needed",
    ],
    "microservices": [
        "Service boundaries drawn along business domain lines to minimise coupling",
        "Each service owns its own database to enforce encapsulation",
        "API gateway centralises auth, rate-limiting, and request routing",
        "Async event bus decouples services for resilience and independent deployability",
    ],
    "serverless": [
        "Pay-per-invocation model reduces idle cost for variable workloads",
        "Stateless functions simplify horizontal scaling and deployments",
        "Cold-start latency accepted in exchange for zero server management",
    ],
    "jamstack": [
        "Pre-rendering at build time maximises CDN cache hit rate",
        "Headless API separation allows frontend and backend to evolve independently",
        "CDN edge delivery achieves global low-latency without infrastructure overhead",
    ],
    "event-driven": [
        "Event sourcing provides full audit log of state changes",
        "Async processing decouples peak load from downstream consumers",
        "Dead-letter queues ensure no events are silently dropped",
    ],
}

_FUTURE_EVOLUTION = {
    "monolith":      "Extract high-traffic or independently scalable modules into separate services once team and load justify the overhead.",
    "microservices": "Introduce a service mesh (Istio / Linkerd) for observability and traffic management as the number of services grows.",
    "serverless":    "Migrate latency-sensitive hot paths to containerised long-running services when cold-start becomes unacceptable.",
    "jamstack":      "Add ISR (Incremental Static Regeneration) or edge middleware to support personalised or frequently-updated content.",
    "event-driven":  "Add event replay and consumer group versioning to support zero-downtime schema evolution.",
}


async def run_architecture_agent(state: dict) -> dict:
    queue: asyncio.Queue = state["stream_queue"]
    await queue.put({"event": "agent_start", "agent": "architecture", "data": "Designing system architecture..."})

    requirements = state.get("requirements", {})
    raw_input = state.get("raw_input", "")
    domain = requirements.get("domain", "saas")
    scale = requirements.get("scale", "medium")
    features = requirements.get("core_features", [])

    norm = normalize_domain(domain)

    # Semantic text-similarity search over 81 project examples
    query = f"{raw_input} {requirements.get('raw_summary', '')}".strip() or domain
    similar = find_similar_examples_by_text(query, top_k=5)
    pattern = most_common_pattern(similar, scale)

    # Upgrade to microservices for genuinely large fintech/ecommerce projects
    must_have = [f for f in features if isinstance(f, dict) and f.get("priority") == "must-have"]
    if scale == "large" and norm in ("fintech", "ecommerce") and len(must_have) >= 8:
        pattern = "microservices"

    refs = extract_reference_projects(similar)

    architecture = {
        "pattern": pattern,
        "description": _PATTERN_DESC.get(pattern, _PATTERN_DESC["monolith"]),
        "components": get_components(norm, pattern),
        "data_flow": _DATA_FLOW.get(pattern, _DATA_FLOW["monolith"]),
        "key_decisions": _KEY_DECISIONS.get(pattern, _KEY_DECISIONS["monolith"]),
        "future_evolution": _FUTURE_EVOLUTION.get(pattern, _FUTURE_EVOLUTION["monolith"]),
        "reference_projects": refs,
    }

    await queue.put({"event": "agent_done", "agent": "architecture", "data": "Architecture designed."})
    return {"architecture": architecture, "stage": "techstack"}
