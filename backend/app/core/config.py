from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl
from typing import List
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    APP_ENV: str = "development"
    PROJECT_NAME: str = "Enterprise AI Operations Platform"
    API_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ALLOWED_ORIGINS: List[AnyHttpUrl] | List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:8080"]
    
    # JWT Auth
    JWT_SECRET_KEY: str = "supersecretjwtkey_please_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Databases
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Dataset Storage
    DATASET_STORAGE_BACKEND: str = "local"  # "local" | "s3"
    DATASET_STORAGE_ROOT: str = "data/datasets"
    DATASET_MAX_FILE_SIZE_MB: int = 500
    DATASET_ALLOWED_EXTENSIONS: List[str] = ["csv", "xlsx", "json", "parquet", "data"]
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # ── LLM Provider Settings ────────────────────────────────────────────────
    LLM_PROVIDER: str = "ollama"                   # ollama | gemini | openai | anthropic

    # Ollama (default — local, free)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: int = 120

    # Google Gemini (optional)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # OpenAI (future-ready stub)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Anthropic Claude (future-ready stub)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"

    # LLM Generation Parameters
    LLM_TEMPERATURE: float = 0.1          # Low = factual, deterministic
    LLM_MAX_TOKENS: int = 2048
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0

    # ── Chat / Conversation Settings ────────────────────────────────────────
    CHAT_MAX_HISTORY_TURNS: int = 10       # Sliding window for conversation memory
    CHAT_SESSION_TTL_HOURS: int = 24       # Auto-expire sessions after N hours
    CHAT_MAX_CONTEXT_CHARS: int = 6000     # Max chars from retrieved chunks
    CHAT_TOP_K_RETRIEVAL: int = 5          # Default top-K for RAG retrieval
    CHAT_ENABLE_SAFETY: bool = True        # Toggle safety guardrails
    CHAT_REQUIRE_CITATIONS: bool = True    # Always require citations

    # ── Agent / Task Orchestration Settings ─────────────────────────────────
    AGENT_MAX_STEPS: int = 15              # Max iterations for the ReAct loop
    AGENT_MAX_EXECUTION_TIME: int = 300    # Hard timeout in seconds for agent run
    AGENT_MAX_MEMORY_TURNS: int = 20       # How many past messages to keep in memory
    AGENT_ENABLE_SAFETY: bool = True       # Enable prompt injection checks and loop detection

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
