"""
Rule-based tech stack agent — no Claude API calls.
Returns a curated modern stack for the detected domain and architecture pattern.
"""
import asyncio
from agents.rules.lookup import normalize_domain, get_stack


async def run_techstack_agent(state: dict) -> dict:
    queue: asyncio.Queue = state["stream_queue"]
    await queue.put({"event": "agent_start", "agent": "techstack", "data": "Selecting technology stack..."})

    requirements = state.get("requirements", {})
    architecture = state.get("architecture", {})
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

    await queue.put({"event": "agent_done", "agent": "techstack", "data": "Tech stack selected."})
    return {"tech_stack": stack, "stage": "estimation"}
