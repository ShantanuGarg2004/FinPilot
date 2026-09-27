# Back button shows the previous account’s profile

**Date:** 2026-09-28  
**Status:** Fixed. History entries carry the sign-in that created them, a restored page re-checks `/api/auth/me`, and `/api` responses are `Cache-Control: no-store`. The sections below are the bug as it was found.  
**Where it shows up:** The React app in `frontend/src`. Sign-out on the server is doing its job.

---

## 1. The bug

Sign in as account A and open the profile page. Sign out. Sign in as account B. Press the browser’s back button. The profile page from account A comes back: that account’s saved profiles, and the rest of that visit’s screen.

The cookie from account A is already dead. `POST /api/auth/logout` in `routes/auth_routes.py` bumps `accounts.session_version` and clears `finpilot_session`. The next real request with that cookie is `401` `session_expired`. Account B’s cookie is the one in the browser. The page on screen is still account A’s.

---

## 2. Why the back button can reach that page

The app does not use a router. `useAppPath` in `frontend/src/App.jsx` keeps the address bar in sync with `window.history`.

- Moving between Profile, Dashboard, Advisory, Chat, and Goals calls `history.pushState(null, "", next)`. The state stored with the entry is `null`. The entry does not record which account was signed in.
- Sign-out calls `go("/", { replace: true })`. That is `history.replaceState` on the **current** entry only. Every earlier entry from account A stays on the stack. A typical stack after A opened the profile, then the dashboard, then signed out, then B signed in, still contains A’s `/profile` and A’s `/dashboard` underneath B’s current URL.

The back button fires `popstate`. The only listener copies `window.location.pathname` into React state. It does not look at who is signed in. Account B is still the React `account`, so `resolveRoute({ signedIn: true, ... })` in `frontend/src/lib/routes.js` treats the old URL as a normal signed-in screen. `/profile` renders `ProfilePage`.

---

## 3. Why that screen is still account A

Three pieces of client state outlive the sign-out, and nothing on the way back checks the account again.

**The signed-in tree is not tied to the account id.** `App` swaps the landing page and the app with `key={account ? "app" : "landing"}`. The key is the same for every signed-in account. Sign-out does unmount the app, because `account` becomes `null`, and the next sign-in mounts it again. A restored history entry does not go through that path. `popstate` only changes `path` on the tree that is already mounted. `GET /api/auth/me` runs in one effect with empty dependencies, on the first mount. A later back navigation does not call it again.

**There is no `pageshow` handler.** When the browser restores a history entry from the back-forward cache, it puts back the JavaScript heap from the visit that filled that entry: `account` (including A’s email in the sidebar), the `users` array inside `useProfiles`, and `sessionStorage` `finpilot.activeUserId`. Sign-out’s `sessionStorage.removeItem` and `setAccount(null)` happened in the newer heap. The restored heap still has account A, so the profile page paints A’s saved profiles. The effect that would have called `/api/auth/me` does not run again.

**Profile, report, chat, and goal memory is keyed by profile id, and sign-out does not clear it.**

- `useProfiles` keeps `GET /api/users` in component state. That list is not labeled with an account id.
- `frontend/src/lib/reportStore.js`, `chatStore.js`, and `goalStore.js` are module maps. They survive the unmount of `FinPilotApp`. `peekReport`, `peekChat`, and `peekGoal` seed the dashboard, advisory, and chat screens. Sign-out never calls a reset. `invalidateReport` runs when a profile is deleted, not when the person signs out.
- `apiFetch` in `frontend/src/config/api.js` sends `credentials: "include"` and does not set `cache: "no-store"`. The API does not send `Cache-Control: no-store` either. A cached `GET /api/users` (or `GET /api/report/<id>`, or chat history) can be the previous account’s body, because the cache key is the URL. The cookie is not part of that key.

So the back button reopens A’s URL, and the profile page is filled from A’s restored tree, A’s in-memory list, or a cached `GET /api/users`. The server will refuse A’s cookie on a new request. The screen does not wait for that request.

---

## 4. The fix

Keep the server logout as it is. Change the client so a history entry from one sign-in cannot paint another sign-in.

1. **Stamp every history entry with the sign-in that created it.** On sign-in, store a new epoch in `sessionStorage` (for example `finpilot.sessionEpoch`) and pass `{ epoch, accountId }` as the first argument to `pushState` and `replaceState`. Sign-out bumps that epoch and clears `finpilot.activeUserId`.

2. **On `popstate`, ignore an entry from another epoch.** If `event.state` is missing or its epoch is not the current one, replace the address bar with `/` when nobody is signed in, or with the current account’s `/profile` or `/dashboard` when someone is. Do not render the path from the old entry.

3. **On `pageshow`, if `event.persisted` is true, call `/api/auth/me` again.** If the account id differs from the one on screen, or the call is `401`, clear the tree and show the landing page or the account that the cookie actually belongs to. A restored heap must not stay on screen.

4. **Key the signed-in app by `account.id`.** `key={account ? "app" : "landing"}` should be `key={account ? account.id : "landing"}`, so account B cannot reuse account A’s React state.

5. **Clear the module caches on sign-out.** Add a reset next to the existing `invalidate*` helpers and call it from `signOut` for the report, chat, and goal maps. Clear `finpilot.activeUserId` in the same place, which `signOut` already does.

6. **Stop caching authenticated reads.** Pass `cache: "no-store"` from `apiFetch` on GET requests. Send `Cache-Control: no-store` on `/api/*` responses. The profile list for account B must be the list the server just returned for account B.

After that, back from account B returns to B’s own screens, or to the landing page. It does not paint account A’s profiles.
