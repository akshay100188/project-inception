"""
Rule-based tech stack agent — no Claude API calls.
Returns a curated modern stack for the detected domain and architecture pattern.
"""
import asyncio
from agents.rules.lookup import (
    normalize_domain, get_stack,
    find_similar_examples_by_text, extract_reference_projects,
)


async def run_techstack_agent(state: dict) -> dict:
    queue: asyncio.Queue = state["stream_queue"]
    await queue.put({"event": "agent_start", "agent": "techstack", "data": "Selecting technology stack..."})

    requirements = state.get("requirements", {})
    architecture = state.get("architecture", {})
    raw_input = state.get("raw_input", "")
    domain = requirements.get("domain", "saas")
    pattern = architecture.get("pattern", "monolith")

    norm = normalize_domain(domain)
    stack = get_stack(norm)

    # Microservices hint: swap infra to container-based
    if pattern == "microservices":
        stack = dict(stack)
        stack["infrastructure"] = {
            "name": "AWS ECS / Kubernetes",
            "rationale": "Container orchestration required for independent service deployments",
        }

    # Enrich with real-world reference projects via text similarity
    query = f"{raw_input} {requirements.get('raw_summary', '')}".strip() or domain
    similar = find_similar_examples_by_text(query, top_k=5)
    refs = extract_reference_projects(similar)

    # Surface any key_libraries actually used in similar real projects
    seen_libs: set[str] = set()
    real_libs: list[str] = []
    for ref in refs:
        for lib in ref.get("tech_stack", {}).get("key_libraries", []):
            if isinstance(lib, str) and lib not in seen_libs:
                seen_libs.add(lib)
                real_libs.append(lib)

    stack = dict(stack)
    stack["reference_projects"] = refs
    if real_libs:
        stack["real_world_libraries"] = real_libs[:10]

    await queue.put({"event": "agent_done", "agent": "techstack", "data": "Tech stack selected."})
    return {"tech_stack": stack, "stage": "estimation"}
