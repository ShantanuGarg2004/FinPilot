# Remediation 10 — paths for the signed-in app

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REMEDIATION_PLAN.md` issue 10
**Verdict:** The signed-in screens follow the URL. Back and forward use that path. The profile id stays in `sessionStorage`. No new package.

---

## 1. What changed

`frontend/src/lib/routes.js` decides the screen from the path, whether the person is signed in, and whether a profile id is stored. `frontend/src/App.jsx` writes the path with `history.pushState` and reads it again on `popstate`. Guard redirects use `replaceState`, so a blocked URL does not stick in the back stack.

| Path | Result |
| --- | --- |
| `/` signed out | Landing |
| `/` signed in | `/dashboard` when a profile id is stored, otherwise `/profile` |
| `/profile` | Profile, signed in |
| `/dashboard`, `/advisory`, `/chat`, `/goals` | That screen when a profile is selected. Otherwise `/profile` |
| Anything else | `/` when signed out, `/profile` when signed in |

A signed-out visit to a known app path keeps that path and shows the landing page, so sign-in returns there. Sign-out goes to `/` and removes `finpilot.activeUserId`.

`page-enter` in `AppShell` is keyed on the path.

## 2. Checks

The guard function was asserted in Node for the path table, including `/chat` with and without a profile id.

The same flows were then opened in a headless browser against the Vite dev server at `http://localhost:5173`. API calls were answered with a stub so the check was the screen, not Flask.

| Check | Result |
| --- | --- |
| Signed out, `/dashboard` | Landing stays on `/dashboard` |
| Sign in there with a stored profile | Dashboard |
| Sign in there with no profile | Profile, URL `/profile` |
| Refresh `/chat` with a profile | Chat, URL stays `/chat` |
| Refresh `/chat` with no profile | Profile, URL `/profile` |
| Open Dashboard, then Back | Returns to `/chat` |
| Sign out | `/`, and the stored profile id is gone |

`frontend/package.json` has no router package.
