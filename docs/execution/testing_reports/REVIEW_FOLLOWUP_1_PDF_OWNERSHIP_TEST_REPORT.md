# Review follow-up 1 — PDF download ownership

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` issue 1
**Verdict:** A download reads the PDF only after the caller owns the profile. A stranger receives the same 404 as a missing report, whether or not the file exists.

---

## 1. What shipped

`GET /api/download-report/<id>` calls `get_user_by_id` before `load_pdf_bytes` and before the rebuild path. `get_user_by_id` already limits the row to the signed-in account or the scoped key's account. A miss returns:

```json
{"error": "No report found. Generate one first.", "code": "not_found"}
```

That body is the same one used when the owner has no report. The rebuild quota runs only after the owner check. `load_pdf_bytes` is still unscoped, because the worker has no request. The route is what knows the caller.

## 2. Tests

`python -m pytest -q` — **121 passed** (118 before this issue, plus 3).

| Case | Result |
| --- | --- |
| Owner downloads a stored PDF | 200, file bytes |
| Other account, file present | 404, missing-report body, bytes not in the response |
| Unknown id | 404, same body |
| Other account, advisory text stored, file missing | 404, advisory text not in the body |
| `data` scope on the owner's key | 200, file bytes |
| `llm` scope without `data` | 403 `forbidden` |

Existing download, rebuild, and report-pipeline tests still pass.
