# User experience

**Status:** Design only. Q5 has not started.  
**Date:** 2026-09-25  
**Companion:** `docs/AUTH_ARCHITECTURE.md`

This document is the login and session flow a person sees. Financial profiles stay what they are today: a profile is not an account.

---

## 1. Two objects

| Object | What the person calls it | What it is |
|---|---|---|
| Account | The email they sign in with | One person. Holds the password. |
| Profile | “Profile” in the sidebar | One financial snapshot (age, income, goals). An account can have several. |

Signing in does not create a profile. Creating a profile does not create an account.

The active profile id can stay in `sessionStorage` for the browser tab. The account session is the cookie. Closing the tab can forget which profile was open. It does not sign the person out until the cookie expires or they sign out.

---

## 2. Signed out

The app opens on a sign-in screen. Dashboard, Advisory, Chat, Goals, and Profile are not reachable. The sidebar is not shown.

The screen has:

- Email
- Password
- Primary action: **Sign in**
- Secondary action: **Create an account**

There is no API-key field and no message about `VITE_API_KEY`.

Empty fields and a bad email shape are caught before the request. A wrong email or wrong password returns one line: **Email or password is incorrect.** The copy does not say which field failed.

---

## 3. Create an account

Fields: email, password, confirm password.

Rules the person can see:

- Email must look like an email.
- Password must be at least 12 characters.
- Confirm must match.

If the email is already registered, the screen says **An account with this email already exists** and links back to sign in. It does not sign them in.

On success the server sets the session cookie and the app opens **Profile** with an empty list and the existing profile form. The title stays “Onboarding Profile”. A short line above the form says they are signed in and have no profiles yet.

---

## 4. Sign in

Success sets the cookie and loads `GET /api/users` for this account only.

| What comes back | Where they land |
|---|---|
| No profiles | Profile, with the empty state and the form |
| One or more profiles | The last profile id stored in this tab, if it is still in the list. Otherwise the profile list, not a guessed id. |
| The stored id is not in the list | Profile list. The stale id is dropped. Dashboard is not shown for a missing profile. |

Dashboard, Advisory, Chat, and Goals stay disabled until a profile is selected, which is the same rule as today (`requiresUser` in the sidebar).

---

## 5. Signed in

The shell gains two items that are always available:

- The signed-in email, shown in the sidebar, not as a profile name
- **Sign out**

Profile create, select, and delete behave as they do now, scoped to this account. Delete still clears the report, chat, and goal caches for that profile id.

Switching profiles does not sign the person out. Signing out clears the cookie, clears those caches, clears the stored profile id, and returns to the sign-in screen.

---

## 6. Session expired

A request that fails because the cookie is missing, expired, or has a stale `session_version` is HTTP 401 with `code: session_expired`.

The app then:

1. Drops the stored profile id and the report, chat, and goal caches.
2. Replaces the current page with the sign-in screen.
3. Shows one line: **Your session ended. Sign in again.**

That screen is not the Dashboard empty state. It must not say “No report yet”, “No profile”, or “check your API key”.

A 404 `not_found` on a report still means this profile has no report. A 401 never means that.

Wrong API key on a local script stays `code: unauthorized`. The browser does not use that code for a person.

---

## 7. Bootstrap account

People who already have profiles in this database sign in as the bootstrap account, with the email and password chosen at migration. They then see the profiles, reports, and chats they already had.

Someone who creates a new account on the same server sees an empty profile list. They do not see the bootstrap profiles.

---

## 8. Copy that must change

Today a 401 is shown as “Unauthorized — check your API key configuration.” After Q5 the browser treats 401 as session expiry (section 6). Local scripts and Swagger are outside this UI.

Network errors stay as they are: the API could not be reached. A failed login is not a network error.
