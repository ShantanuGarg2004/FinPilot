"""Route-class policies for the Wave 1 gateway."""
from __future__ import annotations

from dataclasses import dataclass
import re

from config import Config


@dataclass(frozen=True)
class LimitRule:
    route_class: str
    limit: int
    window_seconds: int
    per_user: bool = False


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    route_class: str | None
    limit: int | None = None
    remaining: int | None = None
    retry_after: int | None = None
    window_seconds: int | None = None
    fail_open: bool = False
    exempt: bool = False


def _per_min(n: int) -> tuple[int, int]:
    return n, 60


def _per_hour(n: int) -> tuple[int, int]:
    return n, 3600


class PolicyRegistry:
    """Map method + path → one or more LimitRules."""

    def __init__(self) -> None:
        dev = Config.FLASK_ENV in ("development", "dev", "local")
        read_min = 600 if dev else 120
        light_min = 600 if dev else 300

        self.read_light = LimitRule("read_light", *_per_min(light_min))
        self.read_report = LimitRule("read_report", *_per_min(read_min))
        self.read_chat = LimitRule("read_chat", *_per_min(read_min))
        self.write_profile = LimitRule("write_profile", *_per_min(30))
        self.write_goal = LimitRule("write_goal", *_per_min(20))
        self.llm_chat = LimitRule("llm_chat", *_per_min(15))
        self.llm_chat_user = LimitRule("llm_chat", *_per_hour(60), per_user=True)
        self.llm_report = LimitRule("llm_report", *_per_min(5))
        self.llm_report_user = LimitRule("llm_report", *_per_hour(10), per_user=True)

    def rules_for(self, method: str, path: str) -> list[LimitRule] | None:
        """Return rules to apply, [] for exempt, None if no policy (allow)."""
        method = (method or "GET").upper()
        path = path or "/"

        if method == "OPTIONS":
            return []
        if path.rstrip("/") in ("/api/health", "/health"):
            return []

        if method == "GET" and path.rstrip("/") == "/api/users":
            return [self.read_light]
        if method == "GET" and re.match(r"^/api/report/\d+$", path):
            return [self.read_report]
        if method == "GET" and re.match(r"^/api/download-report/\d+$", path):
            return [self.read_report]
        if method == "GET" and re.match(r"^/api/chat/history/\d+$", path):
            return [self.read_chat]

        if method == "POST" and path.rstrip("/") == "/api/profile":
            return [self.write_profile]
        if method == "DELETE" and re.match(r"^/api/profile/\d+$", path):
            return [self.write_profile]
        if method == "DELETE" and re.match(r"^/api/chat/history/\d+$", path):
            return [self.write_profile]

        if method == "POST" and path.rstrip("/") == "/api/goal-plan":
            return [self.write_goal]
        if method == "POST" and path.rstrip("/") == "/api/chat":
            return [self.llm_chat, self.llm_chat_user]
        if method == "POST" and path.rstrip("/") == "/api/generate-report":
            return [self.llm_report, self.llm_report_user]

        return None

    @staticmethod
    def is_llm(route_class: str | None) -> bool:
        return route_class in ("llm_chat", "llm_report")
