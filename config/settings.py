# config/settings.py
"""
Enterprise HR AI — Central Configuration
All open-source, no external API keys required.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "Enterprise HR AI System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Local LLM (Ollama — 100% free, no API key) ───────
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"          # or "mistral", "phi3", "gemma2"
    OLLAMA_TIMEOUT: int = 60
    USE_OLLAMA: bool = True               # False = rule-based fallback

    # ── Embeddings (sentence-transformers — local) ────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # ── Sentiment (local HuggingFace model) ──────────────
    SENTIMENT_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"

    # ── Database (SQLite — no server needed) ─────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./hr_ai.db"
    DB_ECHO: bool = False

    # ── RAG ───────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    RAG_TOP_K: int = 3
    RAG_MIN_SCORE: float = 0.3

    # ── Agent Settings ────────────────────────────────────
    AGENT_TIMEOUT_SECONDS: int = 30
    MAX_MEMORY_ENTRIES: int = 50

    # ── Thresholds ────────────────────────────────────────
    ATTRITION_HIGH_RISK: float = 0.65
    BURNOUT_CRITICAL: float = 0.75
    BURNOUT_MODERATE: float = 0.50
    OVERTIME_LIMIT_WEEKLY: int = 60
    LATE_ARRIVALS_LIMIT_MONTHLY: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
