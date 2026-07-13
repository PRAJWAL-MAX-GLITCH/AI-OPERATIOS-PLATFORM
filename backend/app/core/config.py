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
    ALLOWED_ORIGINS: List[AnyHttpUrl] | List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # JWT Auth
    JWT_SECRET_KEY: str = "supersecretjwtkey_please_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Databases
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_platform"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Dataset Storage
    DATASET_STORAGE_BACKEND: str = "local"  # "local" | "s3"
    DATASET_STORAGE_ROOT: str = "data/datasets"
    DATASET_MAX_FILE_SIZE_MB: int = 500
    DATASET_ALLOWED_EXTENSIONS: List[str] = ["csv", "xlsx", "json", "parquet", "data"]
    
    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
