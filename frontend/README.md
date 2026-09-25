# FinPilot frontend

React 19 and Vite client for FinPilot. Sign-in uses an HttpOnly session cookie. The browser does not send `X-API-Key`.

The platform overview, API, and database notes live in the repository [README](../README.md).

## Run it

PostgreSQL and the Flask API must already be up. From the repo root that is `docker compose up -d`, then `python app.py` on port 5000.

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to `http://127.0.0.1:5000`, so the page and the API share one origin and the session cookie is sent.

`frontend/.env` only needs:

```env
VITE_API_URL=/api
```

Leave that unset and the client still defaults to `/api`. Do not put `API_SECRET_KEY` or `VITE_API_KEY` in this folder. That key is for Swagger and local scripts. A browser that sent it would see every profile.

## What the screens do

| Screen | Behavior |
|---|---|
| Sign in / create account | `POST /api/auth/login` and `POST /api/auth/signup`. The API sets `finpilot_session`. |
| Signed out | `GET /api/auth/me` fails and the login page stays up. |
| Profiles, report, chat, goals | Calls go through `src/config/api.js` with `credentials: "include"`. |
| Sign out | `POST /api/auth/logout` and the active profile id is cleared from `sessionStorage`. |
| Session ended | A 401 `session_expired` returns the person to sign-in. The message is “Your session ended. Sign in again.” |

An account with no profiles yet sees “You are signed in and have no profiles yet.” Profiles copied from the old SQLite file belong to the bootstrap account, not to a brand-new signup.

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Dev server on port 5173 with the `/api` proxy |
| `npm run build` | Production bundle |
| `npm run preview` | Serves the production bundle |
| `npm run lint` | ESLint |

The proxy is only in the Vite dev server. A built bundle still calls `VITE_API_URL`. For a deployed site that must be the API’s public `/api` prefix, and the API `CORS_ORIGINS` list must include that site.
