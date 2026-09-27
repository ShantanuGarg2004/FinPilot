# Remediation 2 — API key is not a data credential

**Date:** 2026-09-26
**Plan:** `docs/planning/ARCHITECTURE_REMEDIATION_PLAN.md` issue 2
**Verdict:** A request that presents only `X-API-Key` cannot read or change profiles, reports, chat, or goals.

The key’s value was not rotated. The session cookie is still signed with `API_SECRET_KEY`. That split is issue 3.

---

## 1. What shipped

Data routes answer **403** `api_key_not_allowed` when the actor is the deployment key. The routes are users, profile, report, generate-report, download-report, chat, and goal-plan.

Login, signup, logout, health, and local Swagger are unchanged. Swagger’s description now says the key is the docs password and does not open profiles. Try-it-out on a data route stays forbidden until the browser has `finpilot_session`.

`repository._account_scope()` no longer treats an API key as “every row.” Outside a request it is still `None`, which is the report worker’s path. The worker keeps passing the account id on the job.

Cookie ownership is the same as Q5. `get_latest_user()` is still unused and was not deleted.

`scripts/load_test_q6.py` and `scripts/load_test_wave3.py` log in with `BOOTSTRAP_ACCOUNT_EMAIL` and `BOOTSTRAP_ACCOUNT_PASSWORD` and send the session cookie. They do not send `X-API-Key` on data calls.

## 2. Tests

`python -m pytest -q` — **103 passed**.

| Case | Result |
| --- | --- |
| `GET /api/users` with only the deployment key | 403 `api_key_not_allowed` |
| `POST /api/generate-report` with only the deployment key | 403 `api_key_not_allowed` |
| A signed-in person still cannot see another account’s profile | Pass, existing Q5 test |
| `GET /api/health` with no credential | 200 |
| Signup and `GET /api/auth/me` | 200 |
| Local `/apispec.json` with the docs password | 200, and the description says the key does not open profiles |
| A wrong key, with no session cookie | 401 `unauthorized` |
| `data_headers()` sends `Cookie` and does not send `X-API-Key` | Pass |

## 3. Left for later

- No credentials table and no scopes. That is issue 5.
- `SESSION_SECRET` is not introduced. Rotating `API_SECRET_KEY` would still end every browser session.
- Restart the Flask process that is already listening before this 403 is what that process returns.
