# Q5 Implementation & Testing Report

**Date:** 2026-09-25  
**Scope:** `docs/PLATFORM_QUALITY_WAVES.md` — Q5 (per-person auth)  
**New dependencies installed:** none. Password hashes use Werkzeug. The session cookie uses itsdangerous. Both already come with Flask.

---

## 1. Summary

A person signs in with email and password. Financial profiles belong to that account. The browser no longer sends the deployment API key.

| Gate | Result |
|---|---|
| Pytest, excluding the optional Postgres ping | **92 passed**, 1 deselected |
| Browser click-through of sign-in | **not run** (no browser tool in this session) |

---

## 2. What shipped

| Task | Change |
|---|---|
| Q5.1 | `accounts` is separate from `users`. Profiles have `account_id`. |
| Q5.2 | `POST /api/auth/login` and `/api/auth/signup` set an HttpOnly cookie, `finpilot_session`. The React app calls same-origin `/api` through the Vite proxy and does not send `X-API-Key`. |
| Q5.3 | A signed-in person only sees and changes their own profiles, reports, chats, downloads, and goals. Another account’s id is 404 `not_found`. `GET /api/users` is that account’s list. |
| Q5.4 | A browser actor’s `rate_limit_subject()` is `acct:<account_id>`. A request with `X-API-Key` still uses the key hash and can still read every profile. |
| Q5.5 | Sign-in, create account, and sign out. A dead cookie is 401 `session_expired` with “Your session ended. Sign in again.” |
| Q5.6 | Startup attaches profiles that have no account to the bootstrap account from `BOOTSTRAP_ACCOUNT_EMAIL` and `BOOTSTRAP_ACCOUNT_PASSWORD`. Reports and chats stay on `users.id`. Rollback is in `docs/AUTH_ARCHITECTURE.md`. |

Local bootstrap login for the existing database is `bootstrap@finpilot.local`. The password is `BOOTSTRAP_ACCOUNT_PASSWORD` in the root `.env`.

---

## 3. How to reproduce

```bash
python -m pytest tests/ -q --tb=line --deselect tests/test_wave1_integration.py::test_sql_backend_ping_when_configured
```

Restart `python app.py` and `npm run dev`. Open `http://localhost:5173`. The API key is no longer in `frontend/.env`.
