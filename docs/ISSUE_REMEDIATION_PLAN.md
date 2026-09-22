# FinPilot AI — Issue Remediation Plan

> A phased plan to fix the three issues found in the codebase. **This is a plan only — no code
> is changed by this document.** Each phase is independently shippable and ordered from
> lowest-risk / highest-value to most involved.

- **Date:** 2026-08-02
- **Scope:** Backend correctness (`debt_emi`), chat memory, and prompt consolidation.
- **Non-goals:** Auth, datastore migration, WSGI runtime (tracked separately in
`[ARCHITECTURE.md](ARCHITECTURE.md)`).

---

## 1. Issue Inventory


| #   | Issue                                                                                 | Type                | Severity | Fixed in |
| --- | ------------------------------------------------------------------------------------- | ------------------- | -------- | -------- |
| I1  | `debt_emi` validated but never persisted or used → debt pillar stuck at 7.5/15        | Functional bug      | High     | Phase 2  |
| I2  | Chat history read with wrong key (`content` vs `message`) → AI has no memory          | Functional bug      | High     | Phase 3  |
| I3  | `utils/prompt_builder.py` (stronger prompts) is dead code; weaker inline prompts used | Quality / dead code | Medium   | Phase 4  |




### Root-cause detail

- **I1:** `ProfileSchema` accepts `debt_emi`, but (a) the `users` table has no `debt_emi`
column, and (b) `user_routes.create_profile`'s `INSERT` omits it. So `get_user_by_id` never
returns it, `health_service.calculate_health_score` reads `profile.get("debt_emi") → None`,
and `_score_debt(None)` awards fixed partial credit (50% of 15 = **7.5 pts**), regardless of
real debt. The **frontend already sends** `debt_emi` — only the backend drops it.
- **I2:** `chat_routes._load_history()` returns `{"role", "message"}` dicts, but
`ai_service.chat_with_advisor()` reads `msg.get("content", "")`. The key never matches, so
`conversation_context` is always empty and the chat is effectively stateless.
- **I3:** `utils/prompt_builder.py` has a stronger SEBI-advisor prompt engine
(`build_financial_prompt`, `build_chat_prompt`) that **nothing imports**. `ai_service.py`
uses its own weaker inline prompts, so output quality is governed by the weaker prompt.

---



## 2. Guiding Principles

1. **One issue per phase, one commit per phase** — small, reviewable, revertible.
2. **Tests before/with each fix** — every phase adds unit tests that fail before and pass after.
3. **No breaking API changes** — response shapes stay backward-compatible.
4. **Idempotent DB migration** — safe to run repeatedly on existing `finance.db`.
5. **Watch cross-module coupling** — notably `pdf_service` section detection (see Phase 4).

---



## Phase 1 — Preparation & Safety Net

**Goal:** a clean baseline so each fix is isolated and reversible.

- [ ] Create a working branch, e.g. `fix/core-issues`.
- [ ] Back up the local DB: copy `finance.db` → `finance.db.bak` (it's git-ignored; keep a copy).
- [ ] Run the existing suite to confirm green baseline: `python -m pytest tests/ -v`.
- [ ] Confirm the frontend already sends `debt_emi` (it does — `ProfileForm` in
  ```
  `FinancialAdvisor.jsx`), so no frontend change is required for I1.
  ```

**Exit criteria:** baseline tests pass; branch and DB backup exist.

---



## Phase 2 — Fix `debt_emi` Persistence & Scoring (I1)

**Goal:** persist `debt_emi` end-to-end so the debt-to-income pillar reflects real debt.

### Step 2.1 — Add the column to the schema (fresh DBs)

In `database/models.py`, add `debt_emi` to the `users` `CREATE TABLE`:

```python
CREATE TABLE IF NOT EXISTS users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    age              INTEGER NOT NULL,
    income           REAL    NOT NULL,
    expenses         REAL    NOT NULL,
    savings          REAL    NOT NULL,
    risk_appetite    TEXT    NOT NULL,
    financial_goals  TEXT    NOT NULL,
    debt_emi         REAL,                      -- nullable: optional field
    created_at       TEXT    DEFAULT CURRENT_TIMESTAMP
)
```



### Step 2.2 — Idempotent migration for existing DBs

`CREATE TABLE IF NOT EXISTS` will **not** alter an existing table, so add a guarded `ALTER`
inside `create_tables()` (runs on every startup, safe to repeat):

```python
def _column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

# after the users table is ensured:
if not _column_exists(cursor, "users", "debt_emi"):
    cursor.execute("ALTER TABLE users ADD COLUMN debt_emi REAL")
    logger.info("Migration: added users.debt_emi column")
```



### Step 2.3 — Persist it on insert

In `routes/user_routes.py` `create_profile`, include `debt_emi` in the `INSERT`:

```python
cursor.execute(
    """
    INSERT INTO users
        (age, income, expenses, savings, risk_appetite, financial_goals, debt_emi)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    (data["age"], data["income"], data["expenses"], data["savings"],
     data["risk_appetite"], data["financial_goals"], data.get("debt_emi")),
)
```

`data.get("debt_emi")` is `None` when the client omits it (schema `load_default=None`), which
`_score_debt(None)` already handles as partial credit — the intended behaviour.

### Step 2.4 — Downstream (no change needed, verify only)

- `get_user_by_id`/`get_latest_user`/`get_all_users` use `dict(row)`, so `debt_emi` appears
automatically once the column exists.
- `health_service.calculate_health_score` already reads `profile.get("debt_emi")` and computes
`dti = debt_emi / income`.



### Step 2.5 — Tests

- Unit: `_score_debt(0.10)` → full 15; `_score_debt(0.40)` → reduced; `_score_debt(None)` → 7.5.
- Unit/integration: insert a profile with `debt_emi`, fetch it, assert the value round-trips and
`pillar_scores["debt_ratio"]` changes vs. the `None` case.

**Exit criteria:** a profile with real EMI produces a debt pillar ≠ 7.5; migration runs cleanly
on the backed-up DB; tests pass. **Commit.**

---



## Phase 3 — Restore Chat Memory (I2)

**Goal:** the chat prompt actually contains prior turns.

### Interim (minimal, low-risk) fix

In `services/ai_service.py` `chat_with_advisor`, read the correct key:

```python
for msg in history[-5:]:
    role    = msg.get("role", "user")
    content = msg.get("message", "")   # was msg.get("content", "")
    conversation_context += f"{role}: {content}\n"
```

> If **Phase 4** is executed, `chat_with_advisor` will instead delegate to
> `prompt_builder.build_chat_prompt` (which already reads `msg["message"]`), superseding this
> one-liner. Do the interim fix first for immediate value; Phase 4 then removes the duplication.



### Tests

- Unit: call `chat_with_advisor(profile, "q", history=[{"role":"user","message":"hi"}])` with the
Groq client mocked; assert the outgoing prompt/messages contain `"hi"`.

**Exit criteria:** chat prompt provably includes history; test passes. **Commit.**

---



## Phase 4 — Consolidate on `prompt_builder` (I3)

**Goal:** make the stronger prompt engine the single source of truth and retire the inline
prompts. This is the most involved phase because of a **downstream coupling in** `pdf_service`.

### Step 4.1 — Route generation through `prompt_builder`

In `services/ai_service.py`:

```python
from utils.prompt_builder import build_financial_prompt, build_chat_prompt

def generate_financial_report(profile, health_data):
    prompt = build_financial_prompt(profile, health_data)
    return ask_gpt(prompt, model=Config.GROQ_REPORT_MODEL)

def chat_with_advisor(profile, user_query, history=None):
    prompt = build_chat_prompt(profile, user_query, history)
    return ask_gpt(prompt, model=Config.GROQ_CHAT_MODEL)
```

- `build_chat_prompt` already reads `msg["message"]`, so this **also fully resolves I2** and
removes the interim patch from Phase 3.
- Consider adding an optional `system_prompt` arg to `ask_gpt` since the builder prompts embed
their own persona; keeping the existing generic `SYSTEM_PROMPT` is harmless but redundant.



### Step 4.2 — CRITICAL: realign `pdf_service` section headers

`prompt_builder.build_financial_prompt` emits **different section titles** than the inline
prompt. `pdf_service.generate_pdf_report` detects headings by matching these **old** titles:

`Financial Summary · Budget Optimization · Investment Recommendations · Risk Warnings · Goal Strategy · 30-Day Action Plan`

The builder's sections are:

`Executive Summary · Budget Optimisation · Personalised Investment Strategy · Risk Assessment & Protection · 90-Day Action Plan` (each prefixed with an emoji).

If not updated, those lines render as body text (styling degrades) but the PDF still builds.
**Action:** update the heading match-list in `pdf_service.py` to the new titles and make the
match emoji-tolerant (e.g. strip leading non-alphanumerics before comparing, or match on the
title substring).

### Step 4.3 — Decide on `profiling_service.py`

It is also unused. Either (a) delete it, or (b) wire it into `create_profile` as the
validation/normalisation path. Recommended: **delete** to reduce dead code, since Marshmallow
already validates. Record the decision in `ARCHITECTURE.md`.

### Step 4.4 — Tests

- Unit: `generate_financial_report`/`chat_with_advisor` now call `build_*` — assert the outgoing
prompt contains builder-specific markers (e.g. "SEBI", "90-Day Action Plan", instrument-naming
rules), with the Groq client mocked.
- Unit: a `pdf_service` test that feeds a builder-format report and asserts the new section
titles are detected as headings (no exception; headings applied).

**Exit criteria:** report/chat use `prompt_builder`; `pdf_service` styles the new sections; dead
modules resolved; tests pass. **Commit.**

---



## Phase 5 — Full Test & Integration Pass

- [ ] `python -m pytest tests/ -v` — all green.
- [ ] Manual/integration (real Groq key, `python app.py`):
  - Create a profile **with** `debt_emi`; generate a report; confirm the debt pillar reflects it.
  - Hold a 3-message chat; confirm the advisor references earlier turns.
  - Download the PDF; confirm the five report sections render as styled headings.
- [ ] Confirm no regression in `/api/goal-plan` and `/api/users`.

---



## Phase 6 — Documentation & Rollout

- [ ] Update `ARCHITECTURE.md`: mark I1/I2 fixed; note `prompt_builder` is now wired in and the
  ```
  dead-code / correctness-bug rows in the readiness table.
  ```
- [ ] Update `README.md` if the report section names surface anywhere user-facing.
- [ ] Push each phase's commit; open a PR summarising I1–I3 and the verification results.

---



## 3. Risk & Rollback


| Risk                                            | Mitigation                                                                                         |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `ALTER TABLE` on a populated DB                 | Idempotent guard + DB backup from Phase 1; `ALTER ADD COLUMN` is non-destructive in SQLite         |
| Report format change breaks PDF headings        | Phase 4.2 explicitly realigns `pdf_service`; covered by a PDF test                                 |
| Prompt swap changes AI tone/length unexpectedly | Phased commit; easy revert of the `ai_service` change alone                                        |
| Old profiles created before migration           | `debt_emi` is `NULL` for them → `_score_debt(None)` = existing partial-credit behaviour (no crash) |




## 4. Traceability


| Issue                 | Phase(s)                            | Primary files touched                                                                                                     |
| --------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| I1 `debt_emi`         | Phase 2                             | `database/models.py`, `routes/user_routes.py` (+ tests)                                                                   |
| I2 chat memory        | Phase 3 (interim) → Phase 4 (final) | `services/ai_service.py` (+ tests)                                                                                        |
| I3 dead prompt engine | Phase 4                             | `services/ai_service.py`, `services/pdf_service.py`, `utils/prompt_builder.py`, `services/profiling_service.py` (+ tests) |


---



## 5. Suggested Sequencing (TL;DR)

1. **Phase 1** — branch + DB backup + baseline tests.
2. **Phase 2** — `debt_emi` persistence (self-contained, high value).
3. **Phase 3** — one-line chat-memory fix (immediate value).
4. **Phase 4** — adopt `prompt_builder` (subsumes Phase 3, realign `pdf_service`, remove dead code).
5. **Phase 5** — integration pass.
6. **Phase 6** — docs + PR.

> Note: this document lives under `docs/`, which is git-ignored, so it is not committed to the
> repository by default.

