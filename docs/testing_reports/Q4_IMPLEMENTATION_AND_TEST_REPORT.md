# Q4 Implementation & Testing Report

**Date:** 2026-09-25  
**Scope:** `docs/PLATFORM_QUALITY_WAVES.md` — Q4 (identity seam, still the shared API key)  
**New dependencies installed:** none

---

## 1. Summary

The API now has one caller object. That caller is still the deployment key, not a person. Browser calls are limited to the local Vite origins.

| Gate | Result |
|---|---|
| Pytest, excluding the optional Postgres ping | **87 passed**, 1 deselected |
| Browser click-through | **not run** |

---

## 2. What shipped

| Task | Change |
|---|---|
| Q4.1 | `services/actor.py` resolves `anonymous` or `api_key`. `require_api_key` stores that actor or returns 401. `user` is reserved for Q5 and is not issued. |
| Q4.2 | The gateway bucket id is `Actor.rate_limit_subject()`. Today that is the key hash. A future `user` actor returns the account id. |
| Q4.3 | Chat, generate, goal, and profile delete each have a per-profile ceiling in addition to the shared-key ceiling. |
| Q4.4 | `CORS_ORIGINS` defaults to `http://localhost:5173` and `http://127.0.0.1:5173`. An empty list is rejected when `FLASK_ENV` is not local. |
| Q4.5 | Swagger is registered only when `FLASK_ENV` is `development`, `dev`, or `local`, and still requires the API key. Other environments return 404. |
| Q4.6 | `docs/IDENTITY_SEAM.md` states that a valid key can still read and change every profile. Per-profile limits are not row-level security. |

---

## 3. How to reproduce

```bash
python -m pytest tests/ -q --tb=line --deselect tests/test_wave1_integration.py::test_sql_backend_ping_when_configured
```
