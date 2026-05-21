"""
Estimation Analyst agent — produces timeline, team, and cost estimates grounded in RAG.

Queries historical project benchmarks from the estimation corpus and prompts Claude
to apply them to the specific requirements, architecture, and tech stack.
"""
import asyncio
import json
import re
import anthropic
from config import settings
from rag.corpus import search, format_context

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = """You are a senior engineering manager with experience scoping and estimating software projects.

Given project requirements, architecture, and tech stack, produce a realistic timeline and cost estimate.

Output ONLY valid JSON in this exact shape:
{
  "mvp_weeks": 8,
  "full_product_weeks": 20,
  "recommended_team": {
    "size": 2,
    "roles": ["string"]
  },
  "phases": [
    {"name": "string", "weeks": 2, "deliverables": ["string"]}
  ],
  "cost_range": {
    "mvp_low": 20000,
    "mvp_high": 40000,
    "currency": "USD",
    "basis": "string — e.g. '2 senior engineers at $100–150/hr'"
  },
  "confidence": "low|medium|high",
  "risks": ["string"]
}

Rules:
- phases should cover the MVP timeline (3–5 phases)
- risks: 2–4 items maximum
- Be realistic — double naive estimates; add buffer for integration and testing
- Output raw JSON only, no markdown fences"""


async def run_estimation_agent(state: dict) -> dict:
    """
    Estimate MVP timeline, team composition, and cost range for the project.

    Args:
        state: LangGraph state dict containing ``requirements``, ``architecture``,
               ``tech_stack``, and ``stream_queue``.

    Returns:
        Partial state update with ``estimation`` (dict) and next ``stage``.
    """
    queue: asyncio.Queue = state["stream_queue"]

    await queue.put({
        "event": "agent_start",
        "agent": "estimation",
        "data": "Estimating timeline and costs...",
    })

    requirements = state.get("requirements", {})
    architecture = state.get("architecture", {})
    tech_stack = state.get("tech_stack", {})

    query = (
        f"Estimation for {requirements.get('scale', 'MVP')} {requirements.get('domain', '')} project "
        f"with {len(requirements.get('core_features', []))} core features"
    )

    docs = await search(query, category="estimation", top_k=3)
    context = format_context(docs)
    full_response = ""

    async with _client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": (
                f"Reference benchmarks:\n{context}\n\n"
                f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
                f"Architecture:\n{json.dumps(architecture, indent=2)}\n\n"
                f"Tech stack:\n{json.dumps(tech_stack, indent=2)}\n\n"
                "Output the estimation JSON."
            ),
        }],
    ) as stream:
        async for text in stream.text_stream:
            full_response += text
            await queue.put({"event": "token", "agent": "estimation", "data": text})

    try:
        estimation = json.loads(full_response)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", full_response, re.DOTALL)
        estimation = json.loads(match.group()) if match else {"raw": full_response}

    await queue.put({"event": "agent_done", "agent": "estimation", "data": "Estimation complete."})

    return {"estimation": estimation, "stage": "checkpoint_2"}
