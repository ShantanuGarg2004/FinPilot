"""Flask before-request rate-limit gateway."""
from __future__ import annotations

import logging
import random
import threading
from typing import Any

from flask import Request, jsonify

from config import Config
from .keys import build_bucket_key
from .memory_store import MemoryRateLimitStore
from .policies import LimitDecision, LimitRule, PolicyRegistry
from .sql_store import SqlRateLimitStore
from .store import RateLimitStore

logger = logging.getLogger(__name__)


def _extract_user_id(req: Request) -> int | None:
    # Path params like /report/12
    for part in (req.view_args or {}).values():
        if isinstance(part, int):
            return part
    # JSON body (cached by Flask)
    data = req.get_json(silent=True)
    if isinstance(data, dict) and "user_id" in data:
        try:
            return int(data["user_id"])
        except (TypeError, ValueError):
            return None
    return None


class RateLimitGateway:
    def __init__(self, store: RateLimitStore, policies: PolicyRegistry | None = None) -> None:
        self.store = store
        self.policies = policies or PolicyRegistry()
        self._checks = 0
        self._lock = threading.Lock()

    def check(self, req: Request) -> LimitDecision | None:
        """
        Return a deny decision, or None when the request may proceed.
        Exempt / unmapped routes return None.
        """
        if not Config.RATELIMIT_ENABLED:
            return None

        rules = self.policies.rules_for(req.method, req.path)
        if rules is None:
            return None
        if rules == []:
            return LimitDecision(allowed=True, route_class=None, exempt=True)

        api_key = req.headers.get("X-API-Key", "") or ""
        user_id = _extract_user_id(req)

        maybe_cleanup()

        last_ok: LimitDecision | None = None
        for rule in rules:
            decision = self._apply_rule(api_key, user_id, rule)
            if decision is None:
                # store failure handled per fail-open/closed
                continue
            if not decision.allowed:
                return decision
            last_ok = decision
        return last_ok

    def _apply_rule(self, api_key: str, user_id: int | None, rule: LimitRule) -> LimitDecision | None:
        if rule.per_user and user_id is None:
            # Cannot enforce per-user without id — skip this rule rather than block reads.
            return LimitDecision(
                allowed=True,
                route_class=rule.route_class,
                limit=rule.limit,
                remaining=rule.limit,
                window_seconds=rule.window_seconds,
            )

        key = build_bucket_key(api_key, rule.route_class, user_id if rule.per_user else None)
        try:
            result = self.store.incr_and_check(key, rule.window_seconds, rule.limit)
        except Exception:
            logger.exception("rate limit store error for %s", rule.route_class)
            if PolicyRegistry.is_llm(rule.route_class):
                # Fail closed for expensive LLM routes
                return LimitDecision(
                    allowed=False,
                    route_class=rule.route_class,
                    limit=rule.limit,
                    remaining=0,
                    retry_after=30,
                    window_seconds=rule.window_seconds,
                    fail_open=False,
                )
            # Fail open for reads
            return LimitDecision(
                allowed=True,
                route_class=rule.route_class,
                limit=rule.limit,
                remaining=rule.limit,
                window_seconds=rule.window_seconds,
                fail_open=True,
            )

        return LimitDecision(
            allowed=result.allowed,
            route_class=rule.route_class,
            limit=result.limit,
            remaining=result.remaining,
            retry_after=result.retry_after,
            window_seconds=result.window_seconds,
        )

    def denial_response(self, decision: LimitDecision):
        body = {
            "error": "Rate limit exceeded",
            "code": "rate_limit_exceeded",
            "route_class": decision.route_class,
            "retry_after": decision.retry_after,
            "limit": decision.limit,
            "window_seconds": decision.window_seconds,
        }
        resp = jsonify(body)
        resp.status_code = 429
        if decision.retry_after is not None:
            resp.headers["Retry-After"] = str(decision.retry_after)
        if decision.limit is not None:
            resp.headers["X-RateLimit-Limit"] = str(decision.limit)
        if decision.remaining is not None:
            resp.headers["X-RateLimit-Remaining"] = str(max(0, decision.remaining))
        return resp

    def ping(self) -> bool:
        return self.store.ping()


_gateway: RateLimitGateway | None = None
_cleanup_counter = 0
_cleanup_lock = threading.Lock()


def build_store() -> RateLimitStore:
    backend = (Config.RATELIMIT_STORAGE_BACKEND or "memory").lower()
    if backend == "sql":
        return SqlRateLimitStore(Config.RATELIMIT_DATABASE_URL or "")
    # memory (and unknown) → in-process store
    return MemoryRateLimitStore()


def build_gateway() -> RateLimitGateway:
    global _gateway
    store = build_store()
    _gateway = RateLimitGateway(store)
    return _gateway


def get_gateway() -> RateLimitGateway | None:
    return _gateway


def maybe_cleanup() -> None:
    """Occasionally purge stale buckets (no external cron required for Wave 1)."""
    global _cleanup_counter
    with _cleanup_lock:
        _cleanup_counter += 1
        if _cleanup_counter % 200 != 0 and random.random() > 0.02:
            return
        gw = _gateway
    if not gw:
        return
    try:
        removed = gw.store.cleanup()
        if removed:
            logger.info("rate_limit cleanup removed %d stale buckets", removed)
    except Exception:
        logger.exception("rate_limit cleanup failed")


def uses_custom_gateway() -> bool:
    """True when Wave 1 gateway owns limiting (sql or memory backend)."""
    backend = (Config.RATELIMIT_STORAGE_BACKEND or "memory").lower()
    return backend in ("sql", "memory")
