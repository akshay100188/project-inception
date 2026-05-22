"""
Application configuration — loaded from environment variables / .env file.
All secrets (API keys, DB credentials) must be set before starting the server.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    supabase_url: str
    supabase_service_key: str
    openai_api_key: str
    cors_origins: str = "http://localhost:5173"
    github_token: str = ""  # optional — raises GitHub rate limit from 60 to 5000 req/hr

    model_config = {"env_file": ".env"}


settings = Settings()
