"""Who is calling. Today that is the shared deployment key, not a person."""
from __future__ import annotations

from dataclasses import dataclass

from flask import Request

from config import Config
from database.repository import get_account_by_id
from services.rate_limit.keys import hash_api_key
from services.sessions import COOKIE_NAME, read_token


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
    """Return the caller, or None when the request must be rejected.

    A presented session cookie is resolved first. A bad cookie does not fall
    through to the API key. ``g.auth_error`` is set to ``session_expired`` or
    ``unauthorized`` when the caller cannot continue.
    """
    from flask import g

    token = req.cookies.get(COOKIE_NAME, "")
    if token:
        payload = read_token(token)
        account = get_account_by_id(payload["account_id"]) if payload else None
        version = account["session_version"] if account else None
        if account and version == payload.get("session_version"):
            g.auth_error = None
            return Actor(kind="user", credential=str(account["id"]))
        g.auth_error = "session_expired"
        return None

    key = presented_credential(req)
    if key:
        if key == Config.API_SECRET_KEY:
            g.auth_error = None
            return Actor(kind="api_key", credential=key)
        g.auth_error = "unauthorized"
        return None

    g.auth_error = "session_expired"
    return None
