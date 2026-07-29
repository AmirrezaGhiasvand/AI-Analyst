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

    # --- Environment ---
    debug: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
