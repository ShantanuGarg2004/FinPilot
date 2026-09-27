# Remediation 11 — frontend regression tests

**Date:** 2026-09-27
**Plan:** `docs/ARCHITECTURE_REMEDIATION_PLAN.md` issue 11
**Verdict:** `npm test` in `frontend/` exits 0. It uses Node’s built-in test runner. No Vitest and no new package. CI is still the Python suite.

---

## 1. What is covered

`frontend/src/lib/routes.js` already decided the screen. `frontend/src/lib/reportPoll.js` now decides the report poll. `useReport` calls that function for an accepted generate, a poll snapshot, a second click while one is running, and a timeout. Neither file imports React.

| Case | Result |
| --- | --- |
| Signed out, `/chat` | Landing, and `remember` is `/chat` |
| Signed in, no profile, `/goals` | Render `/profile` |
| Signed in, profile selected, `/advisory` | Render advisory |
| Job queued, then a report and no active job | Leave generating and show that report |
| Job failed, older report exists | Keep that report and record the error |
| Second enqueue while running | Ignore it. The generation number does not change |
| Timeout | Stop and keep the report |

## 2. Command

From `frontend/`:

```text
npm test
```

That runs `node --test src/lib/routes.test.js src/lib/reportPoll.test.js`.

```text
7 passed
```

Documented in `frontend/README.md`.

## 3. Optional browser check

`frontend/scripts/landing_smoke.mjs` is not part of `npm test`. Vite was already running. The script opened Sign in and the dialog was inside the viewport, then opened `/dashboard` while signed out and the landing page stayed up. It does not compare pixels.

```text
node scripts/landing_smoke.mjs
```
