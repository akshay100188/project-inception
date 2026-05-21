"""
Project Inception — FastAPI application entry point.

Registers middleware, routers, and validates configuration on startup.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from api import stream, projects, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify config is sane
    assert settings.anthropic_api_key, "ANTHROPIC_API_KEY not set"
    assert settings.openai_api_key, "OPENAI_API_KEY not set"
    assert settings.supabase_url.startswith("https://"), "SUPABASE_URL must be a REST URL"
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


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
