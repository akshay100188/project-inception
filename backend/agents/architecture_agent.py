"""
Architecture Agent — recommends a system architecture pattern grounded in pgvector RAG.

Queries the RAG corpus for relevant architecture patterns before prompting Claude,
ensuring recommendations are reference-backed rather than purely hallucinated.
"""
import asyncio
import json
import logging
import anthropic
from config import settings
from rag.corpus import search, format_context
from agents.agent_utils import parse_json_response

logger = logging.getLogger(__name__)

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = """You are a senior solutions architect. Given project requirements and reference architecture patterns, recommend the optimal system architecture.

Output ONLY valid JSON in this exact shape:
{
  "pattern": "monolith|microservices|serverless|jamstack|event-driven",
  "description": "1-2 sentence rationale for the chosen pattern",
  "components": [
    {"name": "string", "role": "string", "tech_hint": "string"}
  ],
  "data_flow": "string — describe how data moves through the system end-to-end",
  "key_decisions": ["string"],
  "future_evolution": "string — how to scale this when the time comes"
}

Rules:
- Choose the simplest pattern that meets the requirements
- List 3–6 components maximum
- key_decisions: 2–4 bullet decisions that shaped the architecture
- Output raw JSON only, no markdown fences"""


async def run_architecture_agent(state: dict) -> dict:
    """
    Design the system architecture using RAG-retrieved patterns and project requirements.

    Performs a semantic search on the architecture corpus, then prompts Claude with
    the top-k reference documents to produce a grounded architecture recommendation.

    Args:
        state: LangGraph state dict containing ``requirements`` and ``stream_queue``.

    Returns:
        Partial state update with ``architecture`` (dict) and next ``stage``.
    """
    queue: asyncio.Queue = state["stream_queue"]

    await queue.put({
        "event": "agent_start",
        "agent": "architecture",
        "data": "Designing system architecture...",
    })

    requirements = state.get("requirements", {})
    query = (
        f"{requirements.get('domain', '')} {requirements.get('scale', '')} application "
        f"with {', '.join(f['feature'] for f in requirements.get('core_features', []))}"
    )

    docs = await search(query, category="architecture", top_k=4)
    context = format_context(docs)
    full_response = ""

    async with _client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{"type": "text", "text": _SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": (
                f"Reference patterns:\n{context}\n\n"
                f"Project requirements:\n{json.dumps(requirements, indent=2)}\n\n"
                "Output the architecture JSON."
            ),
        }],
    ) as stream:
        async for text in stream.text_stream:
            full_response += text
            await queue.put({"event": "token", "agent": "architecture", "data": text})

    architecture = parse_json_response(full_response, "architecture")

    await queue.put({"event": "agent_done", "agent": "architecture", "data": "Architecture designed."})

    return {"architecture": architecture, "stage": "techstack"}
