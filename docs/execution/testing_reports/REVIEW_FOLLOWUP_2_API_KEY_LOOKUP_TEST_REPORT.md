# Review follow-up 2 — API key lookup

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` issue 2
**Verdict:** A new API key is found by one indexed SHA-256 digest. A rejected key is counted for that client address before the 401, and further rejects from that address are 429.

---

## 1. What shipped

`api_credentials.key_sha256` stores the hex digest. `issue_api_credential` writes it. A unique index covers live rows. Lookup reads that one row and compares the digest. It does not load every credential and it does not run a password-hash check for a key that has a digest.

Rows issued earlier have no digest. Those are still matched with the password hash until they are reissued with `scripts/issue_api_credential.py`. Startup logs how many live rows are in that state.

A presented key that matches nothing increments a `credential_failure` bucket keyed by client address, using the same 20-per-minute ceiling as login. The 401 is returned only while that bucket allows it. A missing cookie is still `session_expired` and does not use this bucket. Login and signup quotas are unchanged.

## 2. Tests

`python -m pytest -q` — **126 passed** (121 before this issue, plus 5).

| Case | Result |
| --- | --- |
| New key, with legacy rows present | 200, password-hash check not called |
| Wrong key | First 20 are 401, the next is 429 `rate_limit_exceeded` |
| Requests with no cookie, same client | Stay 401 `session_expired` |
| Revoked key | 401 `unauthorized` |
| `llm` scope on `GET /api/users` | 403 `forbidden` |
| Legacy row with only a password hash | Still lists that account's profile |
