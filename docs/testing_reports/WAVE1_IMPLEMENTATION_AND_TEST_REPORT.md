# Wave 1 Implementation & Testing Report

**Date:** 2026-09-23  
**Scope:** `IMPLEMENTATION_PLAN_RATE_LIMITER_AND_BOTTLENECKS.md` — Wave 1 (Durable SQL rate limiter)  
**Branch context:** local working tree (post–Wave 0 merge)  
**New dependencies:** `SQLAlchemy>=2.0,<3`, `psycopg[binary]>=3.1,<4` (approved)

---

## 1. Summary

Wave 1 replaces Flask-Limiter as the active limiter with a **custom SQL/memory gateway**. Counters live in PostgreSQL (`finpilot_ratelimit`) so multiple workers share quotas. Flask-Limiter remains installed but is **disabled** whenever `RATELIMIT_STORAGE_BACKEND` is `sql` or `memory` to avoid double-counting.

| Gate | Result |
|---|---|
| Unit + integration + system tests | **48 passed** |
| Postgres store smoke (ping / incr / cleanup) | **pass** (Docker `finpilot-postgres` healthy) |
| New libraries | SQLAlchemy + psycopg (pinned in `requirements.txt`) |

---

## 2. What was implemented

### 2.1 Store + schema (1.1–1.5)

| Task | Change |
|---|---|
| 1.1 Deps | `SQLAlchemy`, `psycopg[binary]` in `requirements.txt` |
| 1.2 Config | `RATELIMIT_STORAGE_BACKEND`, `RATELIMIT_DATABASE_URL`; validate URL when backend=`sql` |
| 1.3 Schema | `database/sql/rate_limit_schema.sql` — `rate_limit_buckets` + `rate_limit_events`; applied via Docker init |
| 1.4 SQL store | `SqlRateLimitStore` — fixed-window UPSERT + `ping` + TTL `cleanup` |
| 1.5 Memory store | `MemoryRateLimitStore` for tests / single-process fallback |

### 2.2 Policies + gateway (1.6–1.9)

| Task | Change |
|---|---|
| 1.6 Keys / policies | `keys.py` hashes API key; `PolicyRegistry` maps method+path → route class (per-key + per-user on `llm_*`) |
| 1.7 Gateway | `RateLimitGateway` in `before_request`; fail-closed on `llm_*`, fail-open on reads if store errors |
| 1.8 Bypass Flask-Limiter | `limiter.enabled = False` when custom gateway owns limits |
| 1.9 Structured 429 | JSON `{ code, route_class, retry_after, limit, window_seconds }` + `Retry-After` / `X-RateLimit-*` |

### 2.3 Ops (1.10–1.11)

| Task | Change |
|---|---|
| 1.10 Health | `GET /api/health` reports `ratelimit_backend`, `ratelimit_store_ok`; returns 503 if store ping fails |
| 1.11 Cleanup | Probabilistic cleanup on check path (`maybe_cleanup`); SQL deletes stale buckets by `updated_at` |
| Docker | `docker-compose.yml` — Postgres 16 + schema mount; app data stays SQLite |

### 2.4 Quotas shipped

| Route class | Limit (production defaults) |
|---|---|
| OPTIONS / health | Exempt |
| `read_light` | 300 / min / key |
| `read_report` / `read_chat` | 120 / min / key (600 in development) |
| `write_profile` | 30 / min / key |
| `write_goal` | 20 / min / key |
| `llm_chat` | 15 / min / key **and** 60 / hour / user |
| `llm_report` | 5 / min / key **and** 10 / hour / user |

---

## 3. Files touched

| Area | Files |
|---|---|
| Package | `services/rate_limit/{__init__,store,sql_store,memory_store,keys,policies,gateway}.py` |
| App / config | `app.py`, `config.py`, `conftest.py`, `requirements.txt` |
| Infra | `docker-compose.yml`, `database/sql/rate_limit_schema.sql`, `.env` / `.env.example` |
| Tests | `tests/test_wave1_*.py`; Wave 0 tests updated to tighten `PolicyRegistry` |
| Docs | This report; README Wave 1 env notes (prior) |

---

## 4. Test inventory

### 4.1 Unit (`tests/test_wave1_unit_rate_limit.py`)

| Focus |
|---|
| Key hashing stability / length |
| Bucket key includes `user_id` when per-user |
| Memory store allow → deny + key isolation |
| Policy: OPTIONS/health exempt; `llm_report` dual rules; `read_report` mapping |

### 4.2 Integration / system (`tests/test_wave1_integration.py`)

| Focus |
|---|
| Health reports Wave 1 backend + store ok |
| OPTIONS never 429 |
| Read burst under read quota |
| Generate-report structured 429 with `route_class=llm_report` |
| Optional SQL ping/incr when `RATELIMIT_DATABASE_URL` reachable |

### 4.3 Regression

Wave 0 integration/system tests updated to drive the gateway (tighten `llm_report` to 2/min) so they still assert structured 429 and read/LLM independence.

---

## 5. How to run

```bash
# Rate-limit Postgres (once)
docker compose up -d

# Backend deps (if needed)
pip install -r requirements.txt

# Tests (memory backend by default via conftest)
python -m pytest tests/ -v
```

`.env` for local multi-worker / SQL:

```
RATELIMIT_STORAGE_BACKEND=sql
RATELIMIT_DATABASE_URL=postgresql+psycopg://finpilot:finpilot_dev_password@127.0.0.1:5432/finpilot_ratelimit
RATELIMIT_ENABLED=true
```

---

## 6. Acceptance vs plan

| Criterion | Status |
|---|---|
| Shared counters across workers (SQL backend) | **Met** — UPSERT on Postgres; smoke verified |
| Worker kill does not reset limits | **Met** — durable buckets in DB |
| Read storm → ~0 read 429 | **Met** in automated burst tests |
| LLM storm → `code=rate_limit_exceeded` + `route_class` | **Met** |
| Frontend banner / Retry vs JSON 429 | **Inherited from Wave 0** (contract unchanged; `route_class` additive) |

---

## 7. Follow-ups (out of Wave 1)

- Wave 2: persist AI before PDF, soft-fail PDF, chat context, report cache  
- Optional cron for cleanup if probabilistic path is not enough under very low traffic  
- Staging multi-worker load check with `RATELIMIT_STORAGE_BACKEND=sql`
