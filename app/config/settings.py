import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

class Settings:
    DB_URL = os.getenv("DATABASE_URL")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
    REDIS_URL = os.getenv("REDIS_URL")
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    EMBEDDING_CACHE_TTL_SECONDS = int(os.getenv("EMBEDDING_CACHE_TTL_SECONDS", "86400"))
    RETRIEVAL_CACHE_TTL_SECONDS = int(os.getenv("RETRIEVAL_CACHE_TTL_SECONDS", "1800"))
    ANSWER_CACHE_TTL_SECONDS = int(os.getenv("ANSWER_CACHE_TTL_SECONDS", "900"))
    RAG_RETRIEVAL_TOP_N = int(os.getenv("RAG_RETRIEVAL_TOP_N", "20"))
    RAG_FINAL_TOP_K = int(os.getenv("RAG_FINAL_TOP_K", "5"))
    RAG_DOCUMENT_VERSION = os.getenv("RAG_DOCUMENT_VERSION", "v1")
    GROQ_QUALITY_MODEL = os.getenv("GROQ_QUALITY_MODEL", "llama-3.3-70b-versatile")
    GROQ_FAST_MODEL = os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")
    SEMANTIC_RETRIEVAL_CACHE_ENABLED = os.getenv("SEMANTIC_RETRIEVAL_CACHE_ENABLED", "true").lower() == "true"
    SEMANTIC_RETRIEVAL_CACHE_THRESHOLD = float(os.getenv("SEMANTIC_RETRIEVAL_CACHE_THRESHOLD", "0.92"))
    SEMANTIC_RETRIEVAL_CACHE_MAX_CANDIDATES = int(os.getenv("SEMANTIC_RETRIEVAL_CACHE_MAX_CANDIDATES", "50"))

settings = Settings()
