"""
Pytest bootstrap for the FinPilot backend test suite.

This runs before any test module is imported, so it is the right place to:
  1. Put the project root on sys.path (enables `import config`, `import services.*`).
  2. Establish a deterministic, offline test environment. Values are set with
     ``setdefault`` BEFORE `config` is imported, so `config.load_dotenv(override=False)`
     will not clobber them and the Groq client can be constructed without a real key
     (every network call is mocked in the tests).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("API_SECRET_KEY", "test-api-secret")
os.environ.setdefault("GROQ_REPORT_MODEL", "openai/gpt-oss-120b")
os.environ.setdefault("GROQ_CHAT_MODEL", "openai/gpt-oss-20b")
os.environ.setdefault("GROQ_REPORT_MAX_TOKENS", "4096")
os.environ.setdefault("GROQ_CHAT_MAX_TOKENS", "1500")
os.environ.setdefault("GROQ_TIMEOUT_SECONDS", "90")
os.environ.setdefault("WORKER_TIMEOUT_SECONDS", "120")
os.environ.setdefault("SQLITE_BUSY_TIMEOUT_MS", "5000")
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("RATELIMIT_ENABLED", "true")
# Tests use in-memory Wave 1 store by default (no Postgres required).
os.environ.setdefault("RATELIMIT_STORAGE_BACKEND", "memory")
os.environ.setdefault(
    "APP_DATABASE_URL",
    "postgresql+psycopg://finpilot:finpilot_dev_password@127.0.0.1:5432/finpilot_test",
)
os.environ.setdefault("FLASK_ENV", "production")
os.environ.setdefault("BOOTSTRAP_ACCOUNT_EMAIL", "bootstrap@finpilot.local")
os.environ.setdefault("BOOTSTRAP_ACCOUNT_PASSWORD", "bootstrap-test-password")
os.environ.setdefault(
    "PDF_STORAGE_DIR",
    os.path.join(tempfile.gettempdir(), "finpilot-pytest-pdfs"),
)
