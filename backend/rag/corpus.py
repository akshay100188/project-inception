"""
RAG corpus utilities — embed text with OpenAI and perform semantic search via pgvector.

The ``rag_corpus`` table in Supabase stores pre-embedded reference documents for three
categories: ``architecture``, ``techstack``, and ``estimation``. Agents call
:func:`search` at runtime to retrieve the most relevant documents before prompting Claude.
"""
from openai import AsyncOpenAI
from supabase import create_client, Client
from config import settings

_openai = AsyncOpenAI(api_key=settings.openai_api_key)
# Only built when a Supabase URL is configured (DEMO_MODE RAG). The default
# ephemeral flow never touches it, so the backend can run without any database.
_supabase: Client | None = (
    create_client(settings.supabase_url, settings.supabase_service_key)
    if settings.supabase_url else None
)


async def embed(text: str) -> list[float]:
    """
    Return a 1536-dimensional embedding vector for *text* using OpenAI text-embedding-3-small.

    Args:
        text: The string to embed.

    Returns:
        A list of 1536 floats representing the semantic embedding.
    """
    resp = await _openai.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return resp.data[0].embedding


import logging as _logging
_log = _logging.getLogger(__name__)


async def search(query: str, category: str, top_k: int = 4) -> list[dict]:
    """
    Perform a cosine-similarity semantic search over the RAG corpus.

    Returns an empty list (and logs a warning) if the RPC call fails, so agents
    can continue without RAG context rather than crashing the whole pipeline.

    Args:
        query: Natural-language query string.
        category: One of ``"architecture"``, ``"techstack"``, or ``"estimation"``.
        top_k: Number of results to return (default 4).

    Returns:
        List of dicts with keys ``id``, ``title``, ``content``, ``similarity``.
    """
    try:
        vector = await embed(query)
        result = _supabase.rpc(
            "match_corpus",
            {"query_embedding": vector, "match_category": category, "match_count": top_k},
        ).execute()
        return result.data or []
    except Exception as exc:
        _log.warning("RAG search failed for category=%s: %s — continuing without context", category, exc)
        return []


def format_context(docs: list[dict]) -> str:
    """
    Format retrieved documents into a single prompt-ready string.

    Args:
        docs: List of dicts returned by :func:`search`.

    Returns:
        Markdown-formatted string with each document separated by a horizontal rule.
    """
    return "\n\n---\n\n".join(
        f"### {d['title']}\n{d['content']}" for d in docs
    )
