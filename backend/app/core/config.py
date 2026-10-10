from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App Info
    PROJECT_NAME: str = "ResAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database & Cache
    DATABASE_URL: str = "sqlite+aiosqlite:///./resai.db"
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # AI / LLM Config
    LLM_PROVIDER: str = "groq"  # "groq", "gemini", "openai"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "openai/gpt-oss-120b"

    # Search Provider
    SEARCH_PROVIDER: str = "ddg"  # "tavily", "ddg"
    TAVILY_API_KEY: Optional[str] = None
    OPENALEX_EMAIL: str = "researcher@resai.local"

    # Security & Cors
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    SECRET_KEY: str = "resai_super_secret_jwt_key_change_in_production_32bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # Limits & Governance Defaults
    MAX_RESEARCH_ITERATIONS: int = 3
    MAX_TOOL_CALLS: int = 15
    MAX_SOURCES: int = 10
    MAX_UPLOAD_SIZE_MB: int = 10
    RESEARCH_TIMEOUT_SECONDS: int = 300
    CACHE_TTL_SECONDS: int = 3600
    LOG_LEVEL: str = "INFO"


settings = Settings()
