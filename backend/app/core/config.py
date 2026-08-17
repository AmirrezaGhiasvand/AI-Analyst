from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Analytics Studio"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./storage/app.db"
    storage_dir: str = "./storage/datasets"
    max_upload_size_mb: int = 500

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "mistral:7b"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_model: str = ""

    debug: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()