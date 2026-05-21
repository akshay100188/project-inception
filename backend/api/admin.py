"""
Admin-only endpoints — protected by X-Admin-Token header (must match SUPABASE_SERVICE_KEY).
These endpoints are intended for one-time operational tasks (seeding, migrations).
"""
import logging
from fastapi import APIRouter, Header, HTTPException
from config import settings
from rag.seed import seed

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/seed", summary="Seed the RAG corpus (one-time setup)")
async def seed_corpus(x_admin_token: str = Header(...)):
    """
    Embed and insert all RAG corpus documents into the ``rag_corpus`` table.

    Clears existing rows first, then re-inserts all documents with fresh embeddings.
    Protected by ``X-Admin-Token`` header — must equal ``SUPABASE_SERVICE_KEY``.
    """
    if x_admin_token != settings.supabase_service_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        await seed()
        return {"status": "ok", "message": "RAG corpus seeded successfully"}
    except Exception as exc:
        logger.error("Seed failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
