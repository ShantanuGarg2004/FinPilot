"""Rate-limit storage interface and result types."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class IncrResult:
    allowed: bool
    hit_count: int
    limit: int
    remaining: int
    reset_at: datetime
    window_seconds: int

    @property
    def retry_after(self) -> int | None:
        if self.allowed:
            return None
        now = datetime.now(timezone.utc)
        reset = self.reset_at if self.reset_at.tzinfo else self.reset_at.replace(tzinfo=timezone.utc)
        return max(1, int((reset - now).total_seconds()))


class RateLimitStore(ABC):
    @abstractmethod
    def incr_and_check(self, key: str, window_seconds: int, limit: int) -> IncrResult:
        """Atomically increment the fixed window counter and say allow/deny."""

    @abstractmethod
    def ping(self) -> bool:
        """True if the store is reachable."""

    @abstractmethod
    def cleanup(self, older_than_seconds: int = 172800) -> int:
        """Delete stale windows; return rows removed."""
