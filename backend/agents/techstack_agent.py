"""
Tech Stack Selector agent — recommends technology choices grounded in pgvector RAG.

Combines project requirements and the chosen architecture pattern to query the
techstack corpus, then prompts Claude to produce layer-by-layer recommendations.
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

_SYSTEM_PROMPT = """You are a senior full-stack architect. Given project requirements, architecture decisions, and reference stacks, recommend the optimal technology stack.

Output ONLY valid JSON in this exact shape:
{
  "layers": {
    "frontend": {"name": "string", "rationale": "string", "key_libs": ["string"]},
    "backend": {"name": "string", "rationale": "string", "key_libs": ["string"]},
    "database": {"name": "string", "rationale": "string", "schema_hint": "string"},
    "auth": {"name": "string", "rationale": "string"},
    "infrastructure": {"name": "string", "rationale": "string"},
    "mobile": null
  },
  "alternatives": [
    {"layer": "string", "name": "string", "tradeoff": "string"}
  ]
}

Rules:
- Set "mobile" to null unless the project explicitly requires a native mobile app
- List 1–3 alternatives maximum
- Keep rationale concise (1 sentence each)
- Output raw JSON only, no markdown fences"""


async def run_techstack_agent(state: dict) -> dict:
    """
    Select the technology stack using RAG-retrieved examples and prior architecture decisions.

    Args:
        state: LangGraph state dict containing ``requirements``, ``architecture``,
               and ``stream_queue``.

    Returns:
        Partial state update with ``tech_stack`` (dict) and next ``stage``.
    """
    queue: asyncio.Queue = state["stream_queue"]

    await queue.put({
        "event": "agent_start",
        "agent": "techstack",
        "data": "Selecting technology stack...",
    })

    requirements = state.get("requirements", {})
    architecture = state.get("architecture", {})

    raw_input = state.get("raw_input", "")
    query = (
        f"Tech stack for {requirements.get('domain', '')} {requirements.get('scale', '')} "
        f"application, target users: {', '.join(requirements.get('target_users', []))}, "
        f"architecture pattern: {architecture.get('pattern', '')}"
    )

    # Local file search (always available) + curated techstack docs from pgvector
    similar_examples = find_similar_examples_by_text(raw_input or query, top_k=4)
    examples_context = format_examples_for_prompt(similar_examples)
    stack_docs = await search(query, category="techstack", top_k=3)
    stacks_context = format_context(stack_docs)
    full_response = ""

    async with _client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": (
                f"Similar real-world projects (use these as grounding precedents):\n{examples_context}\n\n"
                f"Tech stack reference docs:\n{stacks_context}\n\n"
                f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
                f"Architecture decision:\n{json.dumps(architecture, indent=2)}\n\n"
                "Output the tech stack JSON."
            ),
        }],
    ) as stream:
        async for text in stream.text_stream:
            full_response += text
            await queue.put({"event": "token", "agent": "techstack", "data": text})

    tech_stack = parse_json_response(full_response, "techstack")

    await queue.put({"event": "agent_done", "agent": "techstack", "data": "Tech stack selected."})

    return {"tech_stack": tech_stack, "stage": "estimation"}
