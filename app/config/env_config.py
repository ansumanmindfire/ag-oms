"""Environment settings manager using python-dotenv and os.getenv."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application configuration settings loaded via os.getenv."""

    # Project Metadata
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Agentic Order Management System API")
    PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "0.1.0")
    PROJECT_DESCRIPTION: str = os.getenv(
        "PROJECT_DESCRIPTION",
        "Agentic Order Management System using FastAPI, LangChain, Qdrant Hybrid Search, SQLite.",
    )

    # Environment & Logging
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "DEVELOPMENT")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

    # Storage Paths & Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/db.sqlite")
    CHECKPOINT_DB_PATH: str = os.getenv("CHECKPOINT_DB_PATH", "data/db.sqlite")

    # API Keys & LLM Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    CEREBRAS_API_KEY: str = os.getenv("CEREBRAS_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen/qwen3.6-27b")
    ORCHESTRATION_MODE: str = os.getenv("ORCHESTRATION_MODE", "langgraph")  # "langgraph" or "supervisor"

    # Qdrant Vector DB Configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "order_management_specs")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_SESSION_TTL: int = int(os.getenv("REDIS_SESSION_TTL", "86400"))
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "43200"))

    # Email Service Settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "noreply@ag-oms.com")

    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == 'true'
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "ag-oms-production")


# Global settings instance
settings = Settings()
