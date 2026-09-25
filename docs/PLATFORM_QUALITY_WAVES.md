# Platform quality waves

**Status:** Plan only. Do not treat this file as an implementation order that has started.  
**Date:** 2026-09-25  
**Audience:** The next series of sprints, aimed at about 100 concurrent users.  
**Inputs:** Architecture review (overall **6.4 / 10**) and a pass over UX paths, HTTP APIs, the rate-limit gateway, and `X-API-Key`.  
**Companion:** `docs/IMPLEMENTATION_PLAN_RATE_LIMITER_AND_BOTTLENECKS.md` (Waves 0–3, already shipped). These quality waves start after that work.

Per-person authentication is a later phase. Until then, `X-API-Key` stays the deployment gate. Earlier waves must not invent a second user identity, and they must not keep assuming the API key is a person.

---

## 1. What was reviewed

| Surface | What it does today |
|---|---|
| Profile | Create, list, select, delete. `sessionStorage` holds the active profile id. |
| Dashboard | Loads the stored report, shows the health score, can generate. |
| Advisory | Same report cache as Dashboard, plus PDF download. |
| Chat | Loads history, sends a message, can clear history. |
| Goals | Rule-based simulator. No Groq call. Result lives only in page state. |
| Health | `GET /api/health` is public. |
| Docs UI | `/apidocs/` and `/apispec.json` are public. |
| Gateway | `services/rate_limit` on `before_request` when the backend is `sql` or `memory`. |
| API key | One shared secret. The SPA sends `VITE_API_KEY` on every call. |

There is no login, session, or owner check. Any client that has the key can read or change any numeric `user_id`.

---

## 2. Issue inventory

These are defects, gaps, and practices that will hurt correctness or the 100-user target. They are not a backlog of new product features.

### 2.1 Security and identity

| ID | Issue | Why it matters at 100 users |
|---|---|---|
| S1 | One `X-API-Key` for the whole deployment. The React bundle ships it (`VITE_API_KEY`, default `your-api-key`). | Every visitor shares one secret. Rotating it logs everyone out. It cannot become per-person auth later without a new credential. |
| S2 | No ownership check. Profile, report, chat, download, and goal routes trust `user_id` from the path or body. | One leaked key is full access to every profile, report, and chat. |
| S3 | `GET /api/users` returns every profile to any valid key. | A directory of all clients, not a “my profiles” list. |
| S4 | CORS is `*` on `/api/*`. | Any website can call the API if it has, or can trick a browser into sending, the key. |
| S5 | Swagger UI and the OpenAPI spec are unauthenticated. | The route map is public. Combined with S1, that is an invitation to script the API. |
| S6 | Gateway bucket keys hash the API key, and add `user_id` only on `llm_chat` and `llm_report` hour rules. | Fairness is “one SPA key,” not “one human.” Per-user hour caps do not cover reads, profile writes, deletes, or goals. |
| S7 | Auth is an inline `before_request` string compare, not an actor object. | Per-person auth would be a second special case beside the key check unless a single `Actor` is introduced first. |

**Rule for later auth:** keep `X-API-Key` as a server or BFF secret. The browser session identifies the person. Do not store the deployment key in the production frontend.

### 2.2 Rate-limit gateway

| ID | Issue | Why it matters |
|---|---|---|
| G1 | Flask-Limiter decorators remain on every route while `limiter.enabled` is false whenever the custom gateway is on. | Two policies. Readers will “fix” the decorator and believe it is live. |
| G2 | Quotas exist twice: `Config.RATELIMIT_*` strings and `PolicyRegistry` integers. The gateway uses only the registry. | Env changes to the string limits do nothing in the current backend. |
| G3 | `rules_for` returns `None` for unknown routes, and the gateway treats that as allow. | A new route ships unlimited until someone remembers to map it. |
| G4 | `GET /download-report/<id>` is classed as `read_report`. On a missing blob it rebuilds a PDF in the request. | A “read” can occupy a worker with ReportLab. Under a read burst that is a capacity bug, not a quota bug. |
| G5 | Goal simulation is `write_goal` (20/min per key). It does not call Groq, which is correct, but it is still per key, not per profile. | 100 people on one key share one 20/min budget. |
| G6 | Reads, profile writes, and deletes have no per-profile ceiling. | One script with the shared key can scan or delete every id inside the key budget. |
| G7 | Store errors fail open on reads and fail closed on LLM routes. That policy is right, and it is easy to regress because it is not called out in tests for every class. | A limiter outage could either hide abuse or take down cheap reads. |

### 2.3 API and data practices

| ID | Issue | Why it matters |
|---|---|---|
| A1 | SQL and connection open/close live in route modules (`user_routes`, `report_routes`, `chat_routes`). | Ownership checks and a future PostgreSQL move will be copied into every handler. |
| A2 | A new SQLite connection per helper call. `busy_timeout` is set (Wave 3). There is still one writer. | Chat inserts plus report upserts plus PDF blobs contend. 100 concurrent users will feel this before they feel the limiter. |
| A3 | PDF bytes sit in `reports.pdf_blob` (nullable). | Large writes and backups. Wave 3 deferred object storage; it is now a quality item because download regen and generate both write the blob on the request thread. |
| A4 | `except Exception` around some chat and report persistence logs and continues. | The user can see a reply that was never stored, or a stored user turn with no assistant reply. |
| A5 | Chat saves the user message before Groq returns. On provider failure the row remains. | History grows with unanswered turns. The next prompt treats them as context. |
| A6 | `models/user_model.py` (`UserProfile`) is off the main request path. Profiles are dicts from SQLite. | Two shapes for one concept. |
| A7 | `pdf_service.py` is a long procedural script. The rest of the services are smaller and typed. | PDF changes are risky and hard to review. |
| A8 | No CI workflow. The suite (65 tests at Wave 3) runs only when someone runs it. | Regressions in the gateway or report pipeline can merge silently. |
| A9 | Automated tests cluster on limiter, report soft-fail, and Groq wrappers. Health scoring, goal math, and the React pages are thin or absent. | The paths users actually click are the least locked. |

### 2.4 UX paths

| Path | What works | What is wrong |
|---|---|---|
| Profile create / list / delete | Validation errors surface. Active id is restored from `sessionStorage`. Deleting the active profile returns to Profile. | List is global (S3). Delete does not clear `reportStore` for that id, so a recreated or reused id can show a stale report until a full reload. Failed delete depends on a toast only. |
| Dashboard | Shared report cache with Advisory. 404 vs 429 vs other errors are distinguished. | Generate is synchronous. The page has no download. A `pdf_ready: false` report still looks like a normal report, which is acceptable, but nothing tells Dashboard that the PDF is missing. |
| Advisory | Same cache, so a second visit does not refetch. PDF button, regenerate, soft-fail toast. | Download that regenerates a PDF is a long read (G4) with no progress. Cache marks `pdf_ready` true after download even if a later GET would disagree. |
| Chat | History load error has a retry banner. Throttle and upstream errors become a thread message plus a toast. | Mount always fetches; Strict Mode and fast profile switches can overlap two history calls (no shared in-flight promise). Send appends the user line locally, then the server also stored it; a failed Groq call leaves an unanswered user row (A5) and a fake assistant apology that is **not** the server’s history. Clear does not cancel an in-flight send. |
| Goals | Client checks amount and horizon before POST. Errors use the shared toast mapper. | Result is discarded when leaving the page. No `loadError` banner pattern. Any key can simulate any `user_id` (S2). |
| Health / ops | JSON includes limiter ping, timeouts, recommended workers. | The UI never shows degradation. Operators must call the endpoint themselves. |

### 2.5 Scale (100 concurrent users)

Already true, and still not enough:

- Rate limits exist and LLM routes are tighter than reads.
- Advisory text is stored before PDF.
- Worker formula and timeouts are documented (`docs/CAPACITY_RUNBOOK.md`).
- SQLite waits up to 5 seconds on the writer.

Still open:

- The development server (`python app.py`) is one process. 100 users require Waitress or Gunicorn as the real entry, which is documented but not how the app is started.
- Groq and PDF work run inside the request. Worker count cannot grow past in-flight model calls.
- The mixed 80-read / 20-chat check and the kill-a-worker check from the limiter plan are still unchecked.
- App data is SQLite. The limiter database is already PostgreSQL. They will not scale as one story.

---

## 3. Quality waves

Each wave is a shippable slice. Do not start a wave until its prerequisites in §4 are true.

After each wave’s test suite, add `docs/testing_reports/<WAVE>_IMPLEMENTATION_AND_TEST_REPORT.md` with the command, pass/fail counts, and anything not run.

### Q1 — One enforcement path

**Goal:** The gateway is the only limiter, unknown API routes are denied, and quotas have one source of truth.

| # | Task | Addresses |
|---|---|---|
| Q1.1 | Remove route `@limiter.limit` decorators, or make them no-ops that cannot be configured separately. Keep Flask-Limiter only if something still imports it; do not leave a second live policy. | G1 |
| Q1.2 | Build `PolicyRegistry` numbers from config (env), and delete or stop publishing the unused Flask-Limiter strings. | G2 |
| Q1.3 | Unknown `/api/*` routes: deny (404 or 429-class “no policy”), do not allow. Exempt only health, OPTIONS, and the documented public docs routes if those stay public. | G3 |
| Q1.4 | Split download: cheap “blob exists” vs PDF rebuild. Rebuild must not sit in the generous read bucket. | G4 |
| Q1.5 | Tests: unmapped route denied; env quota change changes the registry; download rebuild does not consume `read_report` the same way as `GET /report`. | G1–G4 |

**Out of scope:** login, new databases, job queue.

**Completed:** 2026-09-25. Quotas are parsed with the `limits` package. Unknown `/api` routes return `rate_policy_missing`. PDF rebuild uses `pdf_rebuild`, not `read_report`. Report: `docs/testing_reports/Q1_IMPLEMENTATION_AND_TEST_REPORT.md` (**68 passed**).

### Q2 — UX path correctness

**Goal:** Each screen’s empty, error, throttle, and success states match the API, and client caches do not lie.

| # | Task | Addresses |
|---|---|---|
| Q2.1 | Chat: one in-flight history load per profile (same idea as `reportStore`). Retry uses that path. | Chat double fetch |
| Q2.2 | Chat: do not persist the user turn until the assistant reply succeeds, or persist a visible failed turn and reload it. The local apology must match what `GET /chat/history` returns. | A4, A5 |
| Q2.3 | Profile delete clears report and chat client caches for that id. | Stale Dashboard |
| Q2.4 | Goals: keep the last result for the active profile while navigating away and back, or show a clear empty state that does not pretend a run is in progress. | Goals UX |
| Q2.5 | Dashboard: if `pdf_ready` is false, say the PDF is not ready yet. Advisory already toasts this on generate. | Dashboard / Advisory |
| Q2.6 | Cancel or ignore chat send responses after clear or profile switch. | Chat race |
| Q2.7 | Frontend tests or a small scripted pass for: 404 report, 429 report, 504 chat, delete profile, goal validation. | A9 |

**Out of scope:** new visual design, authentication screens.

**Completed:** 2026-09-25. Chat history is saved only after a successful reply. Report: `docs/testing_reports/Q2_IMPLEMENTATION_AND_TEST_REPORT.md` (**74 passed**).

### Q3 — Data access fit for contention

**Goal:** Handlers stop owning SQL. Writes stay short. PDF bytes stop being the hot SQLite payload. Still no per-person login.

| # | Task | Addresses |
|---|---|---|
| Q3.1 | Move profile, report, and chat SQL into one module with explicit functions. Routes call those functions. | A1 |
| Q3.2 | One connection per request, closed in `teardown`, instead of open/close per helper. Keep `busy_timeout`. | A2 |
| Q3.3 | Store PDFs on disk (path in the row). `pdf_blob` stays nullable for old rows. Download reads the file or regenerates once and writes the file. | A3, G4 |
| Q3.4 | Narrow `except Exception` on persistence: log, return a structured error when the user must know the save failed. | A4 |
| Q3.5 | Delete or isolate `UserProfile` so request code has one profile shape. | A6 |
| Q3.6 | Add CI: `pytest` on every push to `main`. | A8 |
| Q3.7 | Tests for health score bands and goal feasibility (pure functions, no Groq). | A9 |

**Out of scope:** moving the app database to PostgreSQL. That stays a Q6 decision after a load test, unless Q3 measurements already show write timeouts.

**Completed:** 2026-09-25. Profile, report, and chat SQL live in `database/repository.py`. One SQLite connection is opened per request. PDFs are files under `data/pdfs` (`PDF_STORAGE_DIR`). Report: `docs/testing_reports/Q3_IMPLEMENTATION_AND_TEST_REPORT.md`.

### Q4 — Identity seam (still the shared API key)

**Goal:** Code speaks about an actor. Today the actor is “valid deployment key, no person.” Per-person auth can plug in without rewriting the gateway.

| # | Task | Addresses |
|---|---|---|
| Q4.1 | Introduce one `Actor` (or equivalent) resolved in a single place: `anonymous`, `api_key`, later `user`. `require_api_key` becomes “resolve actor or 401.” | S7 |
| Q4.2 | Gateway bucket id comes from `Actor.rate_limit_subject()`. Today that is the key hash. Document that it will become the account id. | S6, S7 |
| Q4.3 | Add per-profile ceilings for chat, generate, goal, and delete, keyed by `user_id` **in addition to** the deployment key. This is abuse control, not authentication. | G5, G6 |
| Q4.4 | Restrict CORS to the known frontend origins via env. | S4 |
| Q4.5 | Protect Swagger in any non-local environment, or disable it. | S5 |
| Q4.6 | Document the threat: until Q5, a valid key is still every profile (S2, S3). Do not claim row-level security in this wave. | S2, S3 |

**Out of scope:** passwords, OAuth, sessions, signup UI.

### Q5 — Per-person auth

**Goal:** A person signs in. Financial profiles belong to that account. `X-API-Key` is no longer the browser credential.

| # | Task | Addresses |
|---|---|---|
| Q5.1 | Account store separate from `users` (financial profiles). Profiles gain `account_id`. | S2, S3 |
| Q5.2 | Browser uses a session cookie or bearer token. Production frontend does not contain `VITE_API_KEY`. Local dev may keep the key for scripts and Swagger. | S1 |
| Q5.3 | Every profile, report, chat, download, and goal call checks `account_id`. `GET /users` returns only that account’s profiles. | S2, S3 |
| Q5.4 | `Actor.rate_limit_subject()` returns the account id for browser traffic. The deployment key remains the subject for server-to-server calls. | S6 |
| Q5.5 | Login, logout, and expired-session UX. 401 copy must not look like “no report.” | UX |
| Q5.6 | Migration for existing rows: assign them to a bootstrap account or require re-create. Write the rollback. | Data |

**Depends on Q4.** Do not add a second `before_request` that only checks a user header beside the raw key compare.

### Q6 — Prove 100 concurrent users

**Goal:** Measure, then change the runtime or the app database only if the measurement fails.

| # | Task | Addresses |
|---|---|---|
| Q6.1 | Run the API under Waitress (Windows) or Gunicorn (Linux) using `docs/CAPACITY_RUNBOOK.md`. Stop using the Flask dev server for this test. | Scale |
| Q6.2 | Load script: about 80 cheap reads and 20 chat or generate calls with Groq stubbed. Record p95, 429 mix, 503/504, and SQLite `database is locked`. | Scale, A2 |
| Q6.3 | Chaos: kill one worker mid-generate. Others serve health. Limiter counters remain if the backend is Postgres. | Scale |
| Q6.4 | If reads miss the p95 target or locks appear, move app data to PostgreSQL (separate database from `finpilot_ratelimit`) and pool connections. | A2 |
| Q6.5 | If workers saturate on Groq while the limiter still allows calls, add a report job queue and poll `GET /report`. Chat can stay synchronous until the same evidence appears. | Scale |
| Q6.6 | Publish the numbers in `docs/testing_reports/`. Residual risk stays written down if you keep SQLite. | Ops |

---

## 4. Prerequisites

A wave starts only when every row for that wave is true. Later waves assume the earlier wave’s exit criteria, not merely that the tasks were started.

### Q1 prerequisites

| Prerequisite | Why |
|---|---|
| Limiter Waves 0–3 are on `main` (gateway, persist-before-PDF, busy timeout, worker timeout). | Q1 edits the live gateway. |
| `RATELIMIT_STORAGE_BACKEND` is `memory` or `sql`, and tests use `memory`. | Confirms which limiter is active before removing decorators. |
| No in-flight feature branch that adds `@limiter.limit` routes. | Those decorators would be deleted or ignored. |
| Agreement that unknown `/api` routes will fail closed. | This can break an undocumented client. |

### Q2 prerequisites

| Prerequisite | Why |
|---|---|
| Q1 merged. Download classification must be stable before the UI copy about PDF readiness. | Otherwise the client teaches the wrong limit behavior. |
| Structured error codes already used by the SPA (`rate_limit_exceeded`, `not_found`, `upstream_timeout`, `upstream_error`, `pdf_unavailable`). | Q2 only aligns screens with that contract. |
| `reportStore` remains the single report cache. | Delete and PDF flags must update that store, not a second cache. |

### Q3 prerequisites

| Prerequisite | Why |
|---|---|
| Q1 and Q2 merged. | Moving SQL and PDF files while chat persistence and caches are still wrong doubles the migration. |
| Disk path for PDFs chosen (local directory in dev, same idea in prod). Not S3 unless backup pain is already real. | Q3.3 needs a directory and a backup note. |
| Backup of `finance.db` before the PDF file migration. | Existing blobs must be copied out once. |
| CI runner can execute `pytest` without Postgres (memory backend). | Q3.6 must be green on a clean machine. |
| Postgres for the **limiter** is unchanged. | App data and limiter data stay separate. |

### Q4 prerequisites

| Prerequisite | Why |
|---|---|
| Q1 merged. Gateway subject is a single function. | Q4.2 replaces the key hash call site, not a scattered header read. |
| Q3 merged if PDF paths and repositories landed. | Actor checks should sit in one data module, not in six route copies. Q4 can start after Q1 if Q3 slips, but then Q4.3 ceilings must be updated again when repositories land. Prefer Q3 first. |
| Written decision: Q4 does **not** authenticate people. | Prevents a half-built login inside the seam wave. |
| CORS origin list for local Vite and the real frontend host. | Q4.4 fails closed if the list is empty in production. |

### Q5 prerequisites

| Prerequisite | Why |
|---|---|
| Q4 merged. `Actor` and `rate_limit_subject()` exist. | Login fills the actor. It does not add a parallel middleware. |
| Q2 cache rules merged. | Session expiry and profile lists must invalidate the same stores. |
| Account schema reviewed (password hash or external IdP, not a new shared secret in the bundle). | S1 returns if the SPA still embeds a god key. |
| Migration plan for current `users` rows and their reports and chats. | Otherwise existing demos lose data or stay world-readable. |
| Threat note from Q4.6 still accurate, then replaced by ownership tests. | Q5 is done only when S2 and S3 tests fail closed. |
| Secret handling: production `API_SECRET_KEY` only on the server. Frontend env documented as dev-only. | Q5.2. |

### Q6 prerequisites

| Prerequisite | Why |
|---|---|
| Q1–Q3 merged. | Load numbers are meaningless if reads rebuild PDFs in SQLite and two limiters disagree. |
| Q4 merged. | The test must hammer the same subject the gateway will use in production. Per-person subjects can wait, but the hook must exist so the script is not rewritten. |
| Q5 merged **or** an explicit waiver that the load test uses one API key and does not prove fair multi-tenant limits. | 100 humans on one key is a different test from 100 accounts. |
| Waitress or Gunicorn installed on the load-test host. Not a new application dependency until you choose the host OS. | `python app.py` invalidates the result. |
| Groq stub or recorded responses for the chat/generate portion. | A real provider will dominate latency and spend. |
| Limiter Postgres running if the chaos step must show durable counters. | Memory backend resets per process and fails the chaos check. |
| p95 read target remains under 200 ms for cheap GETs, from the earlier plan, unless you publish a new target before the run. | Otherwise Q6.4 and Q6.5 have no pass/fail line. |

---

## 5. Suggested order

```text
Q1 enforcement → Q2 UX correctness → Q3 data access and CI
        → Q4 actor seam → Q5 per-person auth → Q6 load proof
```

Q6.4 (app PostgreSQL) and Q6.5 (job queue) run only when Q6.2 or Q6.3 fails. They are not default scope.

---

## 6. Exit for the whole series

| Check | Done when |
|---|---|
| One limiter | Route decorators cannot enforce a different quota from `PolicyRegistry`. |
| Closed API map | A new unmapped `/api` route is denied by tests. |
| Honest UX | Chat history after a failed send matches the thread on screen. Profile delete cannot show another profile’s cached report. |
| Identity | Production browser traffic has an account. The deployment API key is not in the frontend bundle. |
| Ownership | A token for account A cannot read account B’s report, chat, or goal. |
| Scale | A written load report on a multi-worker server, with SQLite kept or replaced based on that report. |
