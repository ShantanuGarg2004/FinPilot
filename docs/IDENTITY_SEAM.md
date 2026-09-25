# Identity seam

**Status:** Q4. The caller is a deployment API key. This is not per-person authentication.

## Actor

`services/actor.py` resolves one `Actor` before the rate-limit gateway runs.

| Kind | Meaning |
|---|---|
| `anonymous` | Health, the home page, and CORS preflight. No credential. |
| `api_key` | `X-API-Key` or the Swagger Basic password matches `API_SECRET_KEY`. |
| `user` | Reserved for Q5. Not issued by this wave. |

`Actor.rate_limit_subject()` is the gateway bucket identity. For `api_key` it is a hash of the deployment key. For a future `user` actor it will be the account id. Server-to-server calls keep the key hash.

## Threat until Q5

A valid key can still read and change every profile, report, chat, download, and goal. `GET /api/users` still lists every profile. Per-profile rate ceilings are abuse control on top of the shared key. They are not row-level security and they do not prove the caller owns that `user_id`.

Do not describe Q4 as authentication of a person.

## CORS and Swagger

`CORS_ORIGINS` lists the browser origins allowed to call `/api`. When unset, the list is `http://localhost:5173` and `http://127.0.0.1:5173`. An empty list is rejected when `FLASK_ENV` is not `development`, `dev`, or `local`.

Swagger (`/apidocs/`, `/apispec.json`) is registered only in those local environments, and still requires the API key. Other environments return 404 for those paths.
