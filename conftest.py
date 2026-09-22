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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("API_SECRET_KEY", "test-api-secret")
os.environ.setdefault("GROQ_REPORT_MODEL", "openai/gpt-oss-120b")
os.environ.setdefault("GROQ_CHAT_MODEL", "openai/gpt-oss-20b")
os.environ.setdefault("GROQ_REPORT_MAX_TOKENS", "4096")
os.environ.setdefault("GROQ_CHAT_MAX_TOKENS", "1500")
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("RATELIMIT_ENABLED", "true")
os.environ.setdefault("FLASK_ENV", "production")
