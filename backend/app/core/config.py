"""
Application configuration.

All settings are loaded from environment variables (see .env.example).
Using pydantic-settings keeps config validated and typed instead of
scattering os.environ.get() calls throughout the codebase.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    app_name: str = "AI Analytics Studio"
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    # SQLite for local-first development. Swapping to Postgres later is a
    # one-line change here since models are written DB-agnostically.
    database_url: str = "sqlite:///./storage/app.db"

    # --- File storage ---
    storage_dir: str = "./storage/datasets"
    max_upload_size_mb: int = 500

    # --- LLM providers ---
    # "ollama" is the default (free, local). "openrouter" is used as a
    # fallback for tasks local models struggle with, per our free-first
    # cost strategy. Both are accessed via the OpenAI-compatible client —
    # neither needs a separate SDK.
    llm_provider: str = "ollama"

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "mistral:7b"

    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    # No default here on purpose — OpenRouter's free (:free) model lineup
    # changes frequently (models get delisted/added regularly). Check
    # https://openrouter.ai/models?fmt=table&max_price=0 for what's
    # currently free and set this in your .env.
    openrouter_model: str = ""

    # --- Environment ---
    debug: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()