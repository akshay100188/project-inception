"""
Clarification Agent — generates targeted follow-up questions from structured requirements.

Uses Claude Haiku (fast, low-cost) to identify the most impactful gaps before
architecture planning begins.
"""
import asyncio
import json
import anthropic
from config import settings
from agents.rules.lookup import find_similar_examples_by_text, format_examples_for_prompt

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = """You are a senior product manager conducting a brief discovery session.

Given structured project requirements, generate exactly 3 targeted follow-up questions that will meaningfully improve planning accuracy. Focus on ambiguities around:
- Business model / monetization (if unclear)
- Technical constraints or existing systems
- Timeline or budget hard limits
- User scale expectations

Output ONLY valid JSON:
{
  "questions": [
    {"id": "q1", "question": "string", "context": "string (why this matters)"},
    {"id": "q2", "question": "string", "context": "string"},
    {"id": "q3", "question": "string", "context": "string"}
  ]
}

Rules:
- Ask only what you cannot infer
- Each question must be answerable in 1-2 sentences
- Output raw JSON only, no markdown fences"""


async def run_clarification_agent(state: dict) -> dict:
    """
    Generate three targeted clarification questions for the extracted requirements.

    Args:
        state: LangGraph state dict containing ``requirements`` and ``stream_queue``.

    Returns:
        Partial state update with ``clarification_questions`` (list[str]) and next ``stage``.
    """
    queue: asyncio.Queue = state["stream_queue"]

    await queue.put({"event": "agent_start", "agent": "clarification", "data": "Identifying gaps in requirements..."})

    requirements = state.get("requirements", {})
    raw_input = state.get("raw_input", "")
    full_response = ""

    # Ground questions in real projects — surface feature gaps the user hasn't mentioned.
    similar = find_similar_examples_by_text(raw_input or json.dumps(requirements), top_k=3)
    examples_block = format_examples_for_prompt(similar)
    examples_section = (
        f"\nSimilar real-world projects for reference (note which features they included "
        f"that may be absent from the requirements below):\n{examples_block}\n\n---\n"
        if examples_block else ""
    )

    async with _client.messages.stream(
        model="claude-haiku-4-5-20251001",   # fast + cheap for short Q generation
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"{examples_section}"
                    f"Generate clarification questions for this project:\n\n"
                    f"{json.dumps(requirements, indent=2)}"
                ),
            }
        ],
    ) as stream:
        async for text in stream.text_stream:
            full_response += text
            await queue.put({"event": "token", "agent": "clarification", "data": text})

    try:
        result = json.loads(full_response)
        questions = [q["question"] for q in result.get("questions", [])]
        raw_questions = result.get("questions", [])
    except (json.JSONDecodeError, KeyError):
        questions = []
        raw_questions = []

    await queue.put({"event": "agent_done", "agent": "clarification", "data": "Clarification questions ready."})

    return {
        "clarification_questions": questions,
        "_clarification_questions_full": raw_questions,
        "stage": "checkpoint_1",
    }
