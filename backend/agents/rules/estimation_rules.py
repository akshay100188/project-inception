"""
Rule-based estimation agent — no Claude API calls.
Derives timeline, team size, and cost range from scale and feature count.
"""
import asyncio
from agents.rules.lookup import (
    normalize_domain, estimate,
    find_similar_examples_by_text, extract_reference_projects,
)


async def run_estimation_agent(state: dict) -> dict:
    queue: asyncio.Queue = state["stream_queue"]
    await queue.put({"event": "agent_start", "agent": "estimation", "data": "Estimating timeline and costs..."})

    requirements = state.get("requirements", {})
    raw_input = state.get("raw_input", "")
    domain = requirements.get("domain", "saas")
    scale = requirements.get("scale", "medium")
    features = requirements.get("core_features", [])

    norm = normalize_domain(domain)
    must_have_count = len([f for f in features if isinstance(f, dict) and f.get("priority") == "must-have"])
    feature_count = must_have_count or len(features)

    estimation = estimate(scale, feature_count, norm)

    # Enrich with reference projects for grounding
    query = f"{raw_input} {requirements.get('raw_summary', '')}".strip() or domain
    similar = find_similar_examples_by_text(query, top_k=5)
    refs = extract_reference_projects(similar)
    estimation["reference_projects"] = refs

    await queue.put({"event": "agent_done", "agent": "estimation", "data": "Estimation complete."})
    return {"estimation": estimation, "stage": "checkpoint_2"}
