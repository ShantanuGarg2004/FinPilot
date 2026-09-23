"""In-memory fixed-window store (tests / single-process fallback)."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from .store import IncrResult, RateLimitStore


class MemoryRateLimitStore(RateLimitStore):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # (key, window_start_epoch) -> hit_count
        self._buckets: dict[tuple[str, int], int] = {}

    def incr_and_check(self, key: str, window_seconds: int, limit: int) -> IncrResult:
        now = time.time()
        window_start = int(now // window_seconds) * window_seconds
        bucket = (key, window_start)
        with self._lock:
            hits = self._buckets.get(bucket, 0) + 1
            self._buckets[bucket] = hits
        reset_at = datetime.fromtimestamp(window_start + window_seconds, tz=timezone.utc)
        allowed = hits <= limit
        remaining = max(0, limit - hits)
        return IncrResult(
            allowed=allowed,
            hit_count=hits,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            window_seconds=window_seconds,
        )

    def ping(self) -> bool:
        return True

    def cleanup(self, older_than_seconds: int = 172800) -> int:
        cutoff = time.time() - older_than_seconds
        with self._lock:
            stale = [k for k in self._buckets if k[1] < cutoff]
            for k in stale:
                del self._buckets[k]
            return len(stale)
