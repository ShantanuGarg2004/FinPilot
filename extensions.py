"""Shared Flask-Limiter instance (Wave 0: no global hour budget on reads)."""
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config

limiter = Limiter(
    key_func=get_remote_address,
    # Wave 0: empty defaults — limits are applied per-route (read vs LLM).
    default_limits=[],
    storage_uri=Config.RATELIMIT_STORAGE_URI,
    enabled=Config.RATELIMIT_ENABLED,
)


@limiter.request_filter
def _exempt_options_and_health():
    """CORS preflight and health checks must never consume quota or return 429."""
    if request.method == "OPTIONS":
        return True
    path = (request.path or "").rstrip("/")
    return path in ("/api/health", "/health")
