import os
from pathlib import Path
from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(dotenv_path=PROJECT_DIR / ".env")
load_dotenv(dotenv_path=APP_DIR / ".env", override=True)

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
    PROVISIONING_APPROVER_SLACK_IDS = os.getenv("PROVISIONING_APPROVER_SLACK_IDS", "")
    EMPLOYEE_REGISTER_CSV_PATH = os.getenv("EMPLOYEE_REGISTER_CSV_PATH", "runtime/onboarding_employees.csv")
    PROVISIONING_AUDIT_LOG_PATH = os.getenv("PROVISIONING_AUDIT_LOG_PATH", "runtime/provisioning_audit.jsonl")
    PROVISIONING_STATE_DIR = os.getenv("PROVISIONING_STATE_DIR", "runtime/provisioning_requests")
    TASK_ADAPTER = os.getenv("TASK_ADAPTER", "linear")
    LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
    LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")
    LINEAR_INVITE_TEAM_IDS = os.getenv("LINEAR_INVITE_TEAM_IDS", "")
    LINEAR_ONBOARDING_LABEL_ID = os.getenv("LINEAR_ONBOARDING_LABEL_ID")
    LINEAR_INVITE_ROLE = os.getenv("LINEAR_INVITE_ROLE", "admin")

settings = Settings()
