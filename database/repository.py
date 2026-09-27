"""Profile, report, and chat SQL. Routes call these functions."""
import json

import secrets

from flask import g, has_request_context
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import IntegrityConflict, connection
from database.pdf_files import remove_pdf, resolve, write_pdf


# A credential that is not an account id. SQL that sees this matches nothing.
_NO_MATCH = object()
_CREDENTIAL_SCOPES = ("data", "llm")


def _account_scope():
    """Account id for this request.

    None means there is no request, so the caller passes an owner explicitly
    (the report worker). A person and a scoped API key both return their
    account id. There is no scope that sees every account.
    """
    if not has_request_context():
        return None
    actor = getattr(g, "actor", None)
    if actor is not None and actor.kind in ("user", "api_key"):
        try:
            return int(actor.credential)
        except (TypeError, ValueError):
            return _NO_MATCH
    return None


def _owned(sql: str, params: dict, column: str = "account_id"):
    scope = _account_scope()
    if scope is None:
        return sql, params
    if scope is _NO_MATCH:
        return sql + " AND 1 = 0", params
    bound = dict(params)
    bound["owner_account_id"] = scope
    return sql + f" AND {column} = :owner_account_id", bound


def get_user_by_id(user_id: int):
    sql, params = _owned(
        "SELECT * FROM users WHERE id = :user_id",
        {"user_id": user_id},
    )
    with connection() as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def get_all_users():
    sql, params = _owned("SELECT * FROM users WHERE 1 = 1", {})
    sql += " ORDER BY id ASC"
    with connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def insert_user(data: dict) -> int:
    scope = _account_scope()
    if scope is _NO_MATCH:
        from database.db import DatabaseError
        raise DatabaseError("api key cannot write profiles")
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users
                (age, income, expenses, savings, risk_appetite, financial_goals, account_id)
            VALUES (:age, :income, :expenses, :savings, :risk_appetite, :financial_goals, :account_id)
            RETURNING id
            """,
            {
                "age": data["age"],
                "income": data["income"],
                "expenses": data["expenses"],
                "savings": data["savings"],
                "risk_appetite": data["risk_appetite"],
                "financial_goals": data["financial_goals"],
                "account_id": scope,
            },
        )
        conn.commit()
        return cursor.lastrowid


def delete_user(user_id: int) -> bool:
    sql = (
        "SELECT users.id AS id, reports.pdf_path AS pdf_path "
        "FROM users LEFT JOIN reports ON reports.user_id = users.id "
        "WHERE users.id = :user_id"
    )
    sql, params = _owned(sql, {"user_id": user_id}, column="users.account_id")
    with connection() as conn:
        found = conn.execute(sql, params).fetchone()
        if not found:
            return False
        report = found
        conn.execute("DELETE FROM reports WHERE user_id = :user_id", {"user_id": user_id})
        conn.execute("DELETE FROM chat_history WHERE user_id = :user_id", {"user_id": user_id})
        conn.execute("DELETE FROM users WHERE id = :user_id", {"user_id": user_id})
        conn.commit()
    if report is not None:
        remove_pdf(report["pdf_path"])
    return True


def save_report(user_id: int, health_data: dict, ai_report: str) -> None:
    """Store advisory text. PDF location is cleared until a new file is written."""
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO reports (user_id, health_json, ai_report, pdf_path, generated_at)
            VALUES (:user_id, :health_json, :ai_report, NULL, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                health_json  = excluded.health_json,
                ai_report    = excluded.ai_report,
                pdf_path     = NULL,
                generated_at = CURRENT_TIMESTAMP
            """,
            {
                "user_id": user_id,
                "health_json": json.dumps(health_data),
                "ai_report": ai_report,
            },
        )
        conn.commit()


def store_pdf(user_id: int, pdf_bytes: bytes) -> str:
    name = write_pdf(user_id, pdf_bytes)
    with connection() as conn:
        conn.execute(
            "UPDATE reports SET pdf_path = :pdf_path WHERE user_id = :user_id",
            {"pdf_path": name, "user_id": user_id},
        )
        conn.commit()
    return name


def load_report(user_id: int) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            """
            SELECT health_json, ai_report, pdf_path
            FROM reports WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        ).fetchone()
    if not row:
        return None
    return {
        "health": json.loads(row["health_json"]),
        "ai_report": row["ai_report"],
        "pdf_ready": resolve(row["pdf_path"]) is not None,
    }


def load_pdf_bytes(user_id: int) -> bytes | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT pdf_path FROM reports WHERE user_id = :user_id",
            {"user_id": user_id},
        ).fetchone()
    if not row:
        return None
    path = resolve(row["pdf_path"])
    if path is None:
        return None
    return path.read_bytes()


def load_chat_history(user_id: int, limit: int = 20) -> list:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT role, message FROM chat_history
            WHERE user_id = :user_id
            ORDER BY id DESC LIMIT :limit
            """,
            {"user_id": user_id, "limit": limit},
        ).fetchall()
    return [{"role": r["role"], "message": r["message"]} for r in reversed(rows)]


def save_chat_turn(user_id: int, user_message: str, ai_message: str) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, message) VALUES (:user_id, :role, :message)",
            {"user_id": user_id, "role": "user", "message": user_message},
        )
        conn.execute(
            "INSERT INTO chat_history (user_id, role, message) VALUES (:user_id, :role, :message)",
            {"user_id": user_id, "role": "ai", "message": ai_message},
        )
        conn.commit()


def clear_chat_history(user_id: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM chat_history WHERE user_id = :user_id", {"user_id": user_id})
        conn.commit()


def bump_session_version(account_id: int) -> None:
    """Invalidate every cookie for this account. Logout calls this."""
    with connection() as conn:
        conn.execute(
            "UPDATE accounts SET session_version = session_version + 1 WHERE id = :account_id",
            {"account_id": int(account_id)},
        )
        conn.commit()


def get_account_by_id(account_id: int):
    with connection() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = :account_id", {"account_id": account_id}).fetchone()
    return dict(row) if row else None


def get_account_by_email(email: str):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE email = :email",
            {"email": email.strip().lower()},
        ).fetchone()
    return dict(row) if row else None


def _credential_scopes(raw: str) -> tuple[str, ...]:
    found = []
    for part in (raw or "").split(","):
        scope = part.strip()
        if scope in _CREDENTIAL_SCOPES and scope not in found:
            found.append(scope)
    return tuple(found)


def issue_api_credential(account_id: int, label: str, scopes: list[str]) -> tuple[str, int]:
    """Store a hash and return the raw key once, plus the row id."""
    name = (label or "").strip()
    if not name:
        raise ValueError("label is required")
    clean = []
    for scope in scopes:
        item = (scope or "").strip()
        if not item or item in clean:
            continue
        if item not in _CREDENTIAL_SCOPES:
            raise ValueError("scopes must be data, llm, or both")
        clean.append(item)
    if not clean:
        raise ValueError("scopes must be data, llm, or both")
    raw_key = secrets.token_urlsafe(32)
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO api_credentials (account_id, label, key_hash, scopes)
            VALUES (:account_id, :label, :key_hash, :scopes)
            RETURNING id
            """,
            {
                "account_id": int(account_id),
                "label": name,
                "key_hash": generate_password_hash(raw_key),
                "scopes": ",".join(clean),
            },
        )
        conn.commit()
        return raw_key, int(cursor.lastrowid)


def revoke_api_credential(credential_id: int) -> None:
    with connection() as conn:
        conn.execute(
            """
            UPDATE api_credentials
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE id = :credential_id AND revoked_at IS NULL
            """,
            {"credential_id": int(credential_id)},
        )
        conn.commit()


def find_active_api_credential(raw_key: str):
    """Match a presented key to a live row. The raw key is not stored."""
    if not raw_key:
        return None
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM api_credentials WHERE revoked_at IS NULL"
        ).fetchall()
    for row in rows:
        try:
            matches = check_password_hash(row["key_hash"], raw_key)
        except (TypeError, ValueError):
            matches = False
        if matches:
            return {
                "id": row["id"],
                "account_id": row["account_id"],
                "label": row["label"],
                "scopes": _credential_scopes(row["scopes"]),
            }
    return None


def insert_account(email: str, password: str) -> dict:
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO accounts (email, password_hash, auth_provider)
            VALUES (:email, :password_hash, 'local')
            RETURNING id
            """,
            {
                "email": email.strip().lower(),
                "password_hash": generate_password_hash(password),
            },
        )
        conn.commit()
        account_id = cursor.lastrowid
    return get_account_by_id(account_id)


def enqueue_report_job(user_id: int, account_id) -> dict:
    """Insert one queued report job, or return the active job if one exists."""
    with connection() as conn:
        existing = _active_report_job(conn, user_id)
        if existing:
            return existing
        try:
            cursor = conn.execute(
                """
                INSERT INTO jobs (kind, account_id, user_id, status)
                VALUES ('report', :account_id, :user_id, 'queued')
                RETURNING id
                """,
                {"account_id": account_id, "user_id": user_id},
            )
            conn.commit()
            return {"job_id": cursor.lastrowid, "status": "queued"}
        except IntegrityConflict:
            conn.rollback()
            existing = _active_report_job(conn, user_id)
            if not existing:
                raise
            return existing


def _active_report_job(conn, user_id: int):
    row = conn.execute(
        """
        SELECT id, status FROM jobs
        WHERE user_id = :user_id AND kind = 'report' AND status IN ('queued', 'running')
        ORDER BY id
        LIMIT 1
        """,
        {"user_id": user_id},
    ).fetchone()
    if not row:
        return None
    return {"job_id": row["id"], "status": row["status"]}


def latest_report_job(user_id: int):
    """Newest report job, omitting a succeeded row so the stored report speaks for it."""
    with connection() as conn:
        row = conn.execute(
            """
            SELECT id, status, error_code
            FROM jobs
            WHERE user_id = :user_id AND kind = 'report'
            ORDER BY id DESC
            LIMIT 1
            """,
            {"user_id": user_id},
        ).fetchone()
    if not row or row["status"] == "succeeded":
        return None
    payload = {"job_id": row["id"], "status": row["status"]}
    if row["status"] == "failed":
        payload["error_code"] = row["error_code"]
    return payload


def get_user_for_owner(user_id: int, account_id):
    """Profile row only when it belongs to this job's account. NULL matches NULL."""
    with connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM users
            WHERE id = :user_id AND account_id IS NOT DISTINCT FROM :account_id
            """,
            {"user_id": user_id, "account_id": account_id},
        ).fetchone()
    return dict(row) if row else None


def fail_stale_report_jobs(timeout_seconds: int) -> None:
    with connection() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'failed',
                error_code = 'worker_lost',
                error_detail = 'worker_timeout',
                finished_at = CURRENT_TIMESTAMP
            WHERE kind IN ('report', 'chat')
              AND status = 'running'
              AND started_at IS NOT NULL
              AND started_at < CURRENT_TIMESTAMP - make_interval(secs => :timeout_seconds)
            """,
            {"timeout_seconds": int(timeout_seconds)},
        )
        conn.commit()


def enqueue_chat_job(user_id: int, account_id, query: str) -> dict:
    """Queue one chat turn. The worker calls Groq. Many chats may be queued."""
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO jobs (kind, account_id, user_id, status, payload)
            VALUES ('chat', :account_id, :user_id, 'queued', :payload)
            RETURNING id
            """,
            {"account_id": account_id, "user_id": user_id, "payload": query},
        )
        conn.commit()
        return {"job_id": cursor.lastrowid, "status": "queued"}


def latest_chat_job(user_id: int):
    """Newest chat job, omitting a succeeded row because the history has the reply."""
    with connection() as conn:
        row = conn.execute(
            """
            SELECT id, status, error_code
            FROM jobs
            WHERE user_id = :user_id AND kind = 'chat'
            ORDER BY id DESC
            LIMIT 1
            """,
            {"user_id": user_id},
        ).fetchone()
    if not row or row["status"] == "succeeded":
        return None
    payload = {"job_id": row["id"], "status": row["status"]}
    if row["status"] == "failed":
        payload["error_code"] = row["error_code"]
    return payload


def claim_next_report_job():
    with connection() as conn:
        row = conn.execute(
            """
            WITH next AS (
                SELECT id FROM jobs
                WHERE kind IN ('report', 'chat') AND status = 'queued'
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE jobs
            SET status = 'running',
                attempts = attempts + 1,
                started_at = CURRENT_TIMESTAMP
            FROM next
            WHERE jobs.id = next.id
            RETURNING jobs.id AS id, jobs.kind AS kind, jobs.account_id AS account_id,
                      jobs.user_id AS user_id, jobs.attempts AS attempts,
                      jobs.payload AS payload
            """
        ).fetchone()
        conn.commit()
    return dict(row) if row else None


def finish_report_job(job_id: int, status: str, error_code=None, error_detail=None) -> None:
    with connection() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = :status,
                error_code = :error_code,
                error_detail = :error_detail,
                finished_at = CURRENT_TIMESTAMP
            WHERE id = :job_id
            """,
            {
                "status": status,
                "error_code": error_code,
                "error_detail": error_detail,
                "job_id": job_id,
            },
        )
        conn.commit()


def get_report_job(job_id: int):
    with connection() as conn:
        row = conn.execute(
            """
            SELECT id, status, error_code, error_detail, user_id, account_id, attempts
            FROM jobs WHERE id = :job_id
            """,
            {"job_id": job_id},
        ).fetchone()
    return dict(row) if row else None


def attach_orphan_profiles(conn) -> None:
    """Point every unowned profile at the bootstrap account. Reports and chats stay put."""
    from config import Config

    cols = {
        row["name"]
        for row in conn.execute(
            """
            SELECT column_name AS name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = :table_name
            """,
            {"table_name": "users"},
        )
    }
    if "account_id" not in cols:
        return
    orphans = conn.execute("SELECT COUNT(*) AS n FROM users WHERE account_id IS NULL").fetchone()["n"]
    if not orphans:
        return
    email = (Config.BOOTSTRAP_ACCOUNT_EMAIL or "").strip().lower()
    password = Config.BOOTSTRAP_ACCOUNT_PASSWORD or ""
    if not email or not password:
        raise EnvironmentError(
            "Existing profiles have no account. Set BOOTSTRAP_ACCOUNT_EMAIL and "
            "BOOTSTRAP_ACCOUNT_PASSWORD before starting."
        )
    existing = conn.execute(
        "SELECT id FROM accounts WHERE email = :email",
        {"email": email},
    ).fetchone()
    if existing:
        account_id = existing["id"]
    else:
        cursor = conn.execute(
            """
            INSERT INTO accounts (email, password_hash, auth_provider)
            VALUES (:email, :password_hash, 'local')
            RETURNING id
            """,
            {"email": email, "password_hash": generate_password_hash(password)},
        )
        account_id = cursor.lastrowid
    conn.execute(
        "UPDATE users SET account_id = :account_id WHERE account_id IS NULL",
        {"account_id": account_id},
    )
