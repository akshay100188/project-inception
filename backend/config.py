"""
Application configuration — loaded from environment variables / .env file.

DEMO_MODE=false (default): rule-based agents — no API keys required beyond Supabase.
DEMO_MODE=true:            Claude-powered agents — ANTHROPIC_API_KEY and OPENAI_API_KEY required.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    cors_origins: str = "http://localhost:5173"
    demo_mode: bool = False  # True → Claude API agents; False → rule-based (no credits used)

    # Required only when demo_mode=True
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    github_token: str = ""  # optional — raises GitHub rate limit from 60 to 5000 req/hr

    model_config = {"env_file": ".env"}


settings = Settings()
