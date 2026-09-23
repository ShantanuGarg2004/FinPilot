import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Config:
    # ── LLM provider: Groq (OpenAI-compatible) ──────────────────────────────
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    # Per-service model selection (overridable via .env).
    GROQ_REPORT_MODEL = os.getenv("GROQ_REPORT_MODEL", "openai/gpt-oss-120b")
    GROQ_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "openai/gpt-oss-20b")

    # Wave 0: split token budgets (report needs full 6-section output).
    GROQ_REPORT_MAX_TOKENS = _env_int("GROQ_REPORT_MAX_TOKENS", 4096)
    GROQ_CHAT_MAX_TOKENS = _env_int("GROQ_CHAT_MAX_TOKENS", 1500)

    # Secret key clients must send as X-API-Key header to reach the API.
    API_SECRET_KEY = os.getenv("API_SECRET_KEY")

    # Rate limiting (Wave 0 Flask-Limiter + Wave 1 SQL store prep)
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_ENABLED = _env_bool("RATELIMIT_ENABLED", True)
    RATELIMIT_STORAGE_BACKEND = (os.getenv("RATELIMIT_STORAGE_BACKEND") or "memory").lower()
    RATELIMIT_DATABASE_URL = os.getenv("RATELIMIT_DATABASE_URL")
    FLASK_ENV = (os.getenv("FLASK_ENV") or os.getenv("FINPILOT_ENV") or "production").lower()

    # Legacy Flask-Limiter string ceilings (kept for decorator compatibility;
    # Wave 1 gateway uses PolicyRegistry integer quotas instead).
    _dev = FLASK_ENV in ("development", "dev", "local")
    RATELIMIT_READ = os.getenv(
        "RATELIMIT_READ",
        "600 per minute" if _dev else "120 per minute",
    )
    RATELIMIT_WRITE_PROFILE = os.getenv("RATELIMIT_WRITE_PROFILE", "30 per minute")
    RATELIMIT_LLM_CHAT = os.getenv("RATELIMIT_LLM_CHAT", "15 per minute")
    RATELIMIT_LLM_REPORT = os.getenv("RATELIMIT_LLM_REPORT", "5 per minute")
    RATELIMIT_GOAL = os.getenv("RATELIMIT_GOAL", "20 per minute")

    @classmethod
    def validate(cls):
        missing = [k for k in ("GROQ_API_KEY", "API_SECRET_KEY") if not getattr(cls, k)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Add them to your .env file."
            )
        if cls.RATELIMIT_ENABLED and cls.RATELIMIT_STORAGE_BACKEND == "sql":
            if not cls.RATELIMIT_DATABASE_URL:
                raise EnvironmentError(
                    "RATELIMIT_STORAGE_BACKEND=sql requires RATELIMIT_DATABASE_URL "
                    "(PostgreSQL SQLAlchemy URL)."
                )
