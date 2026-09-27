# Remediation 3 — session cookie has its own secret

**Date:** 2026-09-26
**Plan:** `docs/ARCHITECTURE_REMEDIATION_PLAN.md` issue 3
**Verdict:** `finpilot_session` is signed with `SESSION_SECRET`. Deploying this logs every current browser out once. Cookies already in browsers were signed with `API_SECRET_KEY`, and there is no second signer that still accepts them. Sign in again after the Flask process restarts.

`API_SECRET_KEY` was not rotated. Its value is unchanged. It remains the local docs password and the `X-API-Key` scripts send. It is not an argument to the session serializer.

---

## 1. What shipped

`Config.validate()` refuses to start when `SESSION_SECRET` is missing, shorter than 32 characters, or equal to `API_SECRET_KEY`.

`services/sessions.py` builds `URLSafeTimedSerializer` with `Config.SESSION_SECRET` and the existing salt `finpilot-session`. Cookie lifetime stays 12 hours. `HttpOnly`, `SameSite=Lax`, and `Secure` outside local `FLASK_ENV` are unchanged.

Logout increments `accounts.session_version`. A copied cookie from before logout no longer matches the account, so clearing the browser cookie is not the only thing that ends the session. A bad or missing cookie still just clears the cookie.

`.env.example` documents the new setting. The local `.env` has a generated value and is not part of the commit set.

## 2. Tests

`python -m pytest -q` — **108 passed** (103 before this issue).

| Case | Result |
| --- | --- |
| `issue_token` then a different `SESSION_SECRET` | `read_token` returns `None` |
| Signup | `Set-Cookie` contains `finpilot_session` |
| Logout | `session_version` moves from 1 to 2, and the old cookie gets 401 `session_expired` |
| `SESSION_SECRET` equal to `API_SECRET_KEY` | `validate()` raises |
| `SESSION_SECRET` missing | `validate()` raises |
| `SESSION_SECRET` shorter than 32 characters | `validate()` raises |

Grep of `services/sessions.py`: the serializer is `URLSafeTimedSerializer(Config.SESSION_SECRET, salt="finpilot-session")`. `API_SECRET_KEY` does not appear in that file.

## 3. Left for later

- `GET /api/health` still does not run `SELECT 1` on the application database. That is issue 4.
- No credentials table and no scopes. That is issue 5.
- Restart Flask so this process loads `SESSION_SECRET`. Everyone who was signed in will need to sign in again.
