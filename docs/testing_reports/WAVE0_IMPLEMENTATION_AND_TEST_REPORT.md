# Wave 0 Implementation & Testing Report

**Date:** 2026-09-22  
**Scope:** `IMPLEMENTATION_PLAN_RATE_LIMITER_AND_BOTTLENECKS.md` — Wave 0 (Unblock)  
**Branch context:** `dev`  
**New dependencies installed:** none (used existing Flask-Limiter / Groq / React)

---

## 1. Summary

Wave 0 is implemented and verified. The auto-load “regenerate loop” root causes (global `60/hour` on reads + OPTIONS counted + auth middleware bug) are fixed using **Flask-Limiter configuration**, not a custom limiter. AI token budgets are split for report vs chat, truncation is logged via `finish_reason`, the SPA persists the active profile in `sessionStorage`, and 429 responses return structured JSON.

| Gate | Result |
|---|---|
| Unit + integration + system tests | **36 passed** |
| Frontend ESLint | **pass** |
| New libraries | **none requested / none added** |

---

## 2. What was implemented

### 2.1 Rate limiter policy (0.1–0.4)

| Task | Change |
|---|---|
| 0.1 OPTIONS exempt | `extensions.py` → `@limiter.request_filter` skips `OPTIONS` (+ `/api/health`) |
| 0.2 Remove global hour budget | `default_limits=[]` (no more `60 per hour` on every route) |
| 0.3 Per-route classes | Read / write / LLM / goal limits via `@limiter.limit(lambda: app_config.Config.…)` |
| 0.4 Dev-friendly defaults | `Config.RATELIMIT_*`, `RATELIMIT_ENABLED`, higher read ceiling when `FLASK_ENV=development` |
| Bonus bugfix | Auth `before_request` used `startswith("/")`, which exempted **all** API paths from API-key checks — fixed |

### 2.2 AI completeness (0.5–0.7)

| Task | Change |
|---|---|
| 0.5 Split `max_tokens` | `GROQ_REPORT_MAX_TOKENS` default **4096**, `GROQ_CHAT_MAX_TOKENS` default **1500** |
| 0.6 `finish_reason` | Warning log when `finish_reason == "length"` |
| Chat history key | Also accept DB field `message` (one-line; unblocks context) |

### 2.3 Frontend / API contract (0.8–0.9)

| Task | Change |
|---|---|
| 0.8 Persist profile | `sessionStorage` key `finpilot.activeUserId`; initial page dashboard when restored |
| 0.9 Structured 429 | `RateLimitExceeded` handler → `{ code: "rate_limit_exceeded", retry_after, limit, error }` |
| Health | `GET /api/health` public + limiter-exempt |

---

## 3. Files touched

| Area | Files |
|---|---|
| Config / limiter | `config.py`, `extensions.py`, `app.py` |
| Routes | `routes/user_routes.py`, `report_routes.py`, `chat_routes.py`, `goal_routes.py` |
| AI | `services/ai_service.py` |
| Frontend | `frontend/src/App.jsx` |
| Tests | `conftest.py`, `tests/test_ai_service.py`, `tests/test_config.py`, **new** `tests/test_wave0_*.py` |

---

## 4. Test inventory

### 4.1 Unit

| File | Focus |
|---|---|
| `tests/test_config.py` | Token budgets, ratelimit config strings |
| `tests/test_ai_service.py` | Per-call `max_tokens`, `finish_reason=length` logging, history `message` key |
| `tests/test_wave0_unit_limiter.py` | OPTIONS/health exempt filters; empty global defaults |

### 4.2 Integration

| File | Focus |
|---|---|
| `tests/test_wave0_integration.py` | Health public; OPTIONS never 429; 404 vs throttle; structured 401; profile CRUD; generate → structured 429 |

### 4.3 System

| File | Focus |
|---|---|
| `tests/test_wave0_system.py` | Read burst without 429; OPTIONS+GET interleaved; LLM quota independent of reads; `RATELIMIT_ENABLED=false` allows burst |

---

## 5. Test run results

**Command:** `python -m pytest tests/ -v`  
**Environment:** Windows, Python 3.14.2, pytest 9.0.3  

```
36 passed in ~3.7s
```

**Frontend:** `npm run lint` — clean.

### Notable failures found during development (fixed before final run)

1. **Auth bypass** — `startswith("/")` treated every path as open → fixed in `app.py`.  
2. **Stale Config after `importlib.reload`** — limit lambdas now read `app_config.Config` via module reference.  
3. **React lint** — session restore rewritten to avoid `setState` inside effects.

---

## 6. Acceptance criteria (Wave 0)

| Criterion | Status |
|---|---|
| Dashboard ↔ Advisory style read traffic should not hit `GET /report` 429 under normal ceilings | **Met** (system read-burst test; global hour limit removed) |
| `OPTIONS /api/report/<id>` never 429 | **Met** |
| `POST /generate-report` still capped | **Met** (structured 429 when exceeded) |
| Report token budget ≥ 3500 | **Met** (4096 default) |
| Truncation logged on `finish_reason=length` | **Met** |
| FE persists active profile across refresh | **Met** (`sessionStorage`) |
| 429 JSON usable by SPA | **Met** (`code=rate_limit_exceeded`) |

---

## 7. How to re-run

```bash
# Backend (from repo root)
python -m pytest tests/ -v

# Frontend lint
cd frontend && npm run lint
```

Optional env knobs (no new packages):

```env
RATELIMIT_ENABLED=true
RATELIMIT_STORAGE_URI=memory://
RATELIMIT_READ=120 per minute
RATELIMIT_LLM_REPORT=5 per minute
GROQ_REPORT_MAX_TOKENS=4096
GROQ_CHAT_MAX_TOKENS=1500
FLASK_ENV=development
```

---

## 8. Residual risk / next wave

| Item | Notes |
|---|---|
| `memory://` limiter | Not shared across workers — **Wave 1** SQL store |
| Per-user LLM caps | Still IP-keyed — Wave 1 `KeyBuilder` |
| Persist-before-PDF | Not in Wave 0 — **Wave 2** |
| Live Groq completeness | Unit-tested budgets only; sample live reports manually after restart |

---

## 9. Conclusion

Wave 0 is **complete**: policy hotfix + token split + FE session restore + structured 429, covered by **36 automated tests** and a clean frontend lint. No new libraries were added. Proceed to Wave 1 when PostgreSQL/MySQL for the limiter is approved.
