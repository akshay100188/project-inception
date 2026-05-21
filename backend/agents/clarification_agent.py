import asyncio
import json
import anthropic
from config import settings

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
    queue: asyncio.Queue = state["stream_queue"]

    await queue.put({"event": "agent_start", "agent": "clarification", "data": "Identifying gaps in requirements..."})

    requirements = state.get("requirements", {})
    full_response = ""

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
                "content": f"Generate clarification questions for this project:\n\n{json.dumps(requirements, indent=2)}",
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
