"""
Requirement Analyst agent — extracts structured requirements from a raw project idea.

Uses Claude Sonnet with prompt caching to produce a validated JSON requirements object.
"""
import asyncio
import anthropic
from config import settings
from rag.corpus import search as _corpus_search, format_context as _format_context
from agents.agent_utils import parse_json_response

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

# Cached system prompt — stays in cache after first call (~70% cost reduction)
_SYSTEM_PROMPT = """You are a senior software requirements analyst. Your job is to extract clear, structured requirements from a rough project idea described by a user.

Output ONLY valid JSON in this exact shape:
{
  "project_name": "string",
  "problem_statement": "string (1-2 sentences)",
  "target_users": ["string"],
  "core_features": [
    {"feature": "string", "priority": "must-have|nice-to-have"}
  ],
  "integrations": ["string"],
  "scale": "MVP|small|medium|large",
  "domain": "string (e.g. fintech, edtech, saas, healthcare)"
}

Rules:
- Be concise and specific, no padding
- Infer reasonable defaults from context
- Do not ask questions — extract what you can, leave blanks as null
- Output raw JSON only, no markdown fences"""


async def run_requirement_agent(state: dict) -> dict:
    """
    Extract structured project requirements from the user's raw idea text.

    Streams tokens back through the queue and returns a requirements dict
    that conforms to the JSON schema defined in _SYSTEM_PROMPT.

    Args:
        state: LangGraph state dict containing ``raw_input`` and ``stream_queue``.

    Returns:
        Partial state update with ``requirements`` (dict) and next ``stage``.
    """
    queue: asyncio.Queue = state["stream_queue"]

    await queue.put({"event": "agent_start", "agent": "requirement", "data": "Analyzing your project idea..."})

    # Fetch similar real-world projects from Supabase as few-shot grounding.
    try:
        similar_projects = await _corpus_search(state["raw_input"], category="project_example", top_k=2)
    except Exception:
        similar_projects = []

    blocks = _format_context(similar_projects)

    few_shot_block = ""
    if similar_projects:
        few_shot_block = (
            "\n\nReference projects from similar real-world apps (use to calibrate your output):\n"
            + blocks
            + "\n\n---\n"
        )

    full_response = ""

    async with _client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # prompt caching
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"{few_shot_block}Extract requirements from this project idea:\n\n{state['raw_input']}",
            }
        ],
    ) as stream:
        async for text in stream.text_stream:
            full_response += text
            await queue.put({"event": "token", "agent": "requirement", "data": text})

    requirements = parse_json_response(full_response, "requirement")

    await queue.put({"event": "agent_done", "agent": "requirement", "data": "Requirements extracted."})

    return {"requirements": requirements, "stage": "clarification"}
