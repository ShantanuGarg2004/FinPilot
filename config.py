import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── LLM provider: Groq (OpenAI-compatible) ──────────────────────────────
    GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
    # Per-service model selection (overridable via .env). Defaults are chosen
    # for each service's role: a high-capability model for the in-depth
    # advisory report, and a low-latency model for interactive chat.
    GROQ_REPORT_MODEL = os.getenv("GROQ_REPORT_MODEL", "openai/gpt-oss-120b")
    GROQ_CHAT_MODEL   = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")

    # Secret key clients must send as X-API-Key header to reach the API.
    # Set this in your .env file. If absent, the server refuses to start.
    API_SECRET_KEY   = os.getenv("API_SECRET_KEY")
    # Rate limiting storage (use "memory://" for dev, Redis URI for prod)
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    @classmethod
    def validate(cls):
        missing = [k for k in ("GROQ_API_KEY", "API_SECRET_KEY") if not getattr(cls, k)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Add them to your .env file."
            )