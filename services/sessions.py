"""Signed session cookie. itsdangerous already ships with Flask."""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config

COOKIE_NAME = "finpilot_session"
MAX_AGE_SECONDS = 12 * 60 * 60


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(Config.API_SECRET_KEY, salt="finpilot-session")


def issue_token(account_id: int, session_version: int) -> str:
    return _serializer().dumps(
        {"account_id": int(account_id), "session_version": int(session_version)}
    )


def read_token(token: str) -> dict | None:
    try:
        data = _serializer().loads(token, max_age=MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict) or "account_id" not in data:
        return None
    return data


def attach_cookie(response, account_id: int, session_version: int):
    secure = Config.FLASK_ENV not in ("development", "dev", "local")
    response.set_cookie(
        COOKIE_NAME,
        issue_token(account_id, session_version),
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        secure=secure,
        samesite="Lax",
        path="/",
    )
    return response


def clear_cookie(response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return response
