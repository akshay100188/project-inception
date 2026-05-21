from openai import AsyncOpenAI
from supabase import create_client, Client
from config import settings

_openai = AsyncOpenAI(api_key=settings.openai_api_key)
_supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)


async def embed(text: str) -> list[float]:
    resp = await _openai.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return resp.data[0].embedding


async def search(query: str, category: str, top_k: int = 4) -> list[dict]:
    vector = await embed(query)
    result = _supabase.rpc(
        "match_corpus",
        {"query_embedding": vector, "match_category": category, "match_count": top_k},
    ).execute()
    return result.data or []


def format_context(docs: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"### {d['title']}\n{d['content']}" for d in docs
    )
