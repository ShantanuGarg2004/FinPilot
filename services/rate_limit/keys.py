"""Bucket key construction — never store raw API keys."""
from __future__ import annotations

import hashlib


def hash_api_key(api_key: str) -> str:
    raw = (api_key or "anonymous").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_bucket_key(subject: str, route_class: str, user_id: int | None = None) -> str:
    """subject comes from Actor.rate_limit_subject(), already a hash or account id."""
    base = f"{subject}:{route_class}"
    if user_id is not None:
        return f"{base}:u{user_id}"
    return base
