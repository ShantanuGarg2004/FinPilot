# Wave 2 Implementation & Testing Report

**Date:** 2026-09-23  
**Scope:** `IMPLEMENTATION_PLAN_RATE_LIMITER_AND_BOTTLENECKS.md` — Wave 2 (Hot-path correctness)  
**Branch context:** `Finpilot/Rate_Limiter` (or local follow-on)  
**New dependencies installed:** none

---

## 1. Summary

Wave 2 makes generate/chat resilient without depending on further limiter work. Advisory text is persisted **before** PDF; PDF failures soft-fail with `pdf_ready: false`; download regenerates PDF from stored text (no Groq re-call); ReportLab input is sanitized; chat context is widened; Groq failures map to structured upstream codes; Dashboard/Advisory share one report GET via an in-flight/result cache.

| Gate | Result |
|---|---|
| Full pytest suite | **56 passed** |
| New libraries | **none** |

---

## 2. What was implemented

### 2.1 Report pipeline (2.1–2.4)

| Task | Change |
|---|---|
| 2.1 Persist before PDF | `generate_report` saves health + `ai_report` immediately after AI; empty `pdf_blob` placeholder until PDF succeeds |
| 2.2 Soft-fail PDF | PDF errors no longer 500 the request; response includes `pdf_ready` + optional `pdf_error` |
| 2.3 Sanitize markdown | `clean_ai_text` strips pipe tables, fences, tags; `_safe_xml` escapes Paragraph content |
| 2.4 Download regen | Missing blob → rebuild PDF from DB text + profile; cache blob; **no** AI call |

### 2.2 Chat quality (2.5–2.7)

| Task | Change |
|---|---|
| 2.5 History key | Already fixed in Wave 0 (`message` \|\| `content`) — retained |
| 2.6 Widen context | Last **20** messages within **8000** char budget (`format_conversation_context`) |
| 2.7 Upstream errors | `RateLimitError` → `upstream_rate_limit`; other Groq/API failures → `upstream_error` (HTTP 503) |

### 2.3 Frontend (2.8–2.9)

| Task | Change |
|---|---|
| 2.8 Shared store | `frontend/src/lib/reportStore.js` — cache by `userId` |
| 2.9 In-flight dedupe | Concurrent mounts share one `GET /report` promise |
| UX | Toast when `pdf_ready: false`; download updates cache after regen |

---

## 3. Files touched

| Area | Files |
|---|---|
| Routes | `routes/report_routes.py`, `routes/chat_routes.py` |
| Services | `services/pdf_service.py`, `services/ai_service.py` |
| Frontend | `frontend/src/lib/reportStore.js`, `hooks/useReport.js`, `lib/apiErrors.js` |
| Tests | `tests/test_wave2_report_pipeline.py`, `tests/test_ai_service.py` |
| Docs | This report; implementation plan acceptance |

---

## 4. Test inventory

| Test | Focus |
|---|---|
| `test_clean_ai_text_*` | Tables / bold / tags stripped |
| `test_pdf_survives_ampersand_*` | ReportLab builds with `&` / `<>` |
| `test_generate_persists_when_pdf_fails` | 200 + GET still has AI text |
| `test_download_regenerates_pdf_without_ai` | Regen once, then cached blob |
| `test_format_conversation_context_*` | Recent window |
| `test_ask_gpt_maps_*` | Upstream codes |
| `test_chat_with_advisor_includes_more_than_five_*` | Context > 5 turns |

---

## 5. Acceptance vs plan

| Criterion | Status |
|---|---|
| PDF parse error still leaves report loadable via GET | **Met** |
| Multi-turn chat uses prior user/AI text | **Met** (wider window) |
| Dashboard then Advisory → one report GET (or cached) | **Met** (`reportStore`) |

---

## 6. Notes / follow-ups

- Soft-fail uses empty `BLOB` (schema stays `NOT NULL`) rather than a migration.
- Wave 3 still owns worker sizing, async PDF jobs, and app-DB Postgres.
