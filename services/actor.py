"""Who is calling. Today that is the shared deployment key, not a person."""
from __future__ import annotations

from dataclasses import dataclass

from flask import Request

from config import Config
from services.rate_limit.keys import hash_api_key


@dataclass(frozen=True)
class Actor:
    """anonymous, api_key, or later user. Request code should not grow a second identity."""

    kind: str
    credential: str = ""

    def rate_limit_subject(self) -> str:
        """Bucket identity for the rate-limit gateway.

        Today this is a hash of the deployment API key. When per-person auth
        exists, a browser actor (kind ``user``) returns the account id here.
        Server-to-server calls keep the key hash.
        """
        if self.kind == "user" and self.credential:
            return f"acct:{self.credential}"
        return hash_api_key(self.credential)


def presented_credential(req: Request) -> str:
    header = req.headers.get("X-API-Key", "") or ""
    if header:
        return header
    auth = req.authorization
    if auth and auth.password:
        return auth.password
    return ""


def resolve_actor(req: Request) -> Actor | None:
    """Return the caller, or None when the request must be rejected with 401."""
    key = presented_credential(req)
    if key and key == Config.API_SECRET_KEY:
        return Actor(kind="api_key", credential=key)
    return None
