import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DATABASE_URL: str = "sqlite:///./banking_demo.db"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # LLM Settings (Empty key activates deterministic fallback)
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"

    # Auth / JWT
    JWT_SECRET: str = "dev-secret-change-me-in-production"
    JWT_EXPIRY_HOURS: int = 12

    # Operational & Security
    DEMO_ROLE: str = "manager"
    SIMULATION_INTERVAL_SECONDS: int = 4
    MAX_TOOL_CALLS_PER_REQUEST: int = 10
    MAX_WORKFLOW_STEPS: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
