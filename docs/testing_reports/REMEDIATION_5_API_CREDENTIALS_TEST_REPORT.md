# Remediation 5 — scoped API credentials

**Date:** 2026-09-26
**Plan:** `docs/ARCHITECTURE_REMEDIATION_PLAN.md` issue 5
**Verdict:** An API key is a hash stored on one account, with `data` and/or `llm`. It cannot see another account. The docs password is not a data key.

`SESSION_SECRET` was not changed. Signing this in does not sign browsers out. Load-test scripts still log in with the bootstrap account. They do not use a credential.

---

## 1. What shipped

`api_credentials` holds `account_id`, `label`, `key_hash`, `scopes`, and `revoked_at`. The raw key is printed once by `scripts/issue_api_credential.py`. The database stores a Werkzeug password hash.

```text
python scripts/issue_api_credential.py --email you@example.com --label local-load-test --scopes data,llm
python scripts/issue_api_credential.py --revoke 1
```

Resolution order: a valid session cookie wins, and a bad cookie does not fall through. `X-API-Key` is then matched to a non-revoked row. The actor’s credential is that account id, and the rate-limit subject is `acct:<account_id>` for both the cookie and the key. A header that matches nothing is **401** `unauthorized`. `API_SECRET_KEY` is compared only on local Swagger.

`data` covers profiles, stored reports, PDF download, goals, and chat history. `llm` covers `POST /api/generate-report` and `POST /api/chat`. A missing scope is **403** `forbidden`. There is no scope that lists every account.

`.env.example` describes the docs password and the credential script separately.

## 2. Tests

`python -m pytest -q` — **116 passed** (111 before this issue).

| Case | Result |
| --- | --- |
| Key for account A lists profiles | Only A’s profile |
| Same key reads B’s report and chat | 404, and B’s text is not in the body |
| `data` without `llm` | List succeeds, generate is 403 `forbidden` |
| `llm` on its own profile | 202, job `queued` or `running` |
| Revoked key | 401 `unauthorized` |
| Cookie ownership tests from Q5 | Still pass |
| Env `API_SECRET_KEY` on `GET /api/users` | 401 `unauthorized` |

The env key used to be **403** `api_key_not_allowed` because it was still an actor. It is not an actor on data routes anymore, so the denial is 401. It still cannot read profiles. Local Swagger still opens with that password.

## 3. Left for later

- The capacity measurement is issue 6. This issue did not run it.
- Restart Flask so the process already listening loads `api_credentials` and this resolution order.
