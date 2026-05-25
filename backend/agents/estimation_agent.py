"""
Estimation Analyst agent — produces timeline, team, and cost estimates grounded in RAG.

Queries historical project benchmarks from the estimation corpus and prompts Claude
to apply them to the specific requirements, architecture, and tech stack.
"""
import asyncio
import json
import logging
import anthropic
from config import settings
from rag.corpus import search, format_context
from agents.rules.lookup import find_similar_examples_by_text, format_examples_for_prompt
from agents.agent_utils import parse_json_response

logger = logging.getLogger(__name__)

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

    raw_input = state.get("raw_input", "")
    query = (
        f"Estimation for {requirements.get('scale', 'MVP')} {requirements.get('domain', '')} project "
        f"with {len(requirements.get('core_features', []))} core features"
    )

    # Local file search (always available) + curated estimation benchmark docs from pgvector
    similar_examples = find_similar_examples_by_text(raw_input or query, top_k=4)
    examples_context = format_examples_for_prompt(similar_examples)
    bench_docs = await search(query, category="estimation", top_k=3)
    benchmarks_context = format_context(bench_docs)
    full_response = ""

    try:
        async with _client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{
                "role": "user",
                "content": (
                    f"Similar real-world projects (use actual timelines/costs as calibration):\n{examples_context}\n\n"
                    f"Estimation benchmarks:\n{benchmarks_context}\n\n"
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
    except Exception as exc:
        logger.error("Estimation API call failed: %s", exc)

    logger.info("Estimation raw response (%d chars): %.1000s", len(full_response), full_response)

    estimation = parse_json_response(full_response, "estimation")

    await queue.put({"event": "agent_done", "agent": "estimation", "data": "Estimation complete."})

    return {"estimation": estimation, "stage": "checkpoint_2"}
