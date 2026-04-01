"""
config/settings.py
─────────────────
Central configuration using Pydantic Settings.
All env vars are validated and typed here.
"""
print(f"[LOADING] {__file__}")

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ── API Keys ──────────────────────────────────────────────────────────────
    youtube_api_key: str = Field(..., env="YOUTUBE_API_KEY")
    openrouter_api_key: str = Field("", env="OPENROUTER_API_KEY")  # Required unless using Ollama

    # ── Model Config ──────────────────────────────────────────────────────────
    # Set OLLAMA_BASE_URL to use local Ollama instead of OpenRouter
    # Example: OLLAMA_BASE_URL=http://localhost:11434
    ollama_base_url: str = Field("", env="OLLAMA_BASE_URL")
    ollama_model: str = Field("llama3.2", env="OLLAMA_MODEL")
    
    # OpenRouter model ID (used if OLLAMA_BASE_URL is not set)
    llm_model: str = Field("anthropic/claude-3.5-sonnet", env="LLM_MODEL")

    # ── Storage ───────────────────────────────────────────────────────────────
    chroma_persist_dir: str = Field("./data/vectorstore", env="CHROMA_PERSIST_DIR")
    cache_dir: str = Field("./data/processed", env="CACHE_DIR")
    raw_data_dir: str = Field("./data/raw", env="RAW_DATA_DIR")

    # ── Ingestion Limits ──────────────────────────────────────────────────────
    max_comments_per_video: int = Field(100, env="MAX_COMMENTS_PER_VIDEO")
    max_videos_per_channel: int = Field(10, env="MAX_VIDEOS_PER_CHANNEL")

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = Field("development", env="APP_ENV")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
