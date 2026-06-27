"""
Project Inception — FastAPI application entry point.

Registers middleware, routers, and validates configuration on startup.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from api import stream, projects, admin, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.demo_mode:
        assert settings.supabase_url.startswith("https://"), (
            "DEMO_MODE=true uses the Supabase pgvector RAG corpus — SUPABASE_URL must be set."
        )
        assert settings.anthropic_api_key, (
            "DEMO_MODE=true requires ANTHROPIC_API_KEY to be set. "
            "Set DEMO_MODE=false to run without API keys."
        )
        assert settings.openai_api_key, (
            "DEMO_MODE=true requires OPENAI_API_KEY to be set. "
            "Set DEMO_MODE=false to run without API keys."
        )
    yield


app = FastAPI(title="Project Inception", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream.router, prefix="/api/stream", tags=["stream"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(upload.router, prefix="/api", tags=["upload"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
