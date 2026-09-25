"""Profile, report, and chat SQL. Routes call these functions."""
import json

from flask import g, has_request_context
from werkzeug.security import generate_password_hash

from database.db import connection
from database.pdf_files import remove_pdf, resolve, write_pdf


def _account_scope():
    """Browser actors see only their profiles. The deployment key sees every row."""
    if not has_request_context():
        return None
    actor = getattr(g, "actor", None)
    if actor is not None and actor.kind == "user":
        return int(actor.credential)
    return None


def get_latest_user():
    with connection() as conn:
        row = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    account_id = _account_scope()
    sql = "SELECT * FROM users WHERE id = ?"
    args = [user_id]
    if account_id is not None:
        sql += " AND account_id = ?"
        args.append(account_id)
    with connection() as conn:
        row = conn.execute(sql, args).fetchone()
    return dict(row) if row else None


def get_all_users():
    account_id = _account_scope()
    sql = "SELECT * FROM users"
    args = []
    if account_id is not None:
        sql += " WHERE account_id = ?"
        args.append(account_id)
    sql += " ORDER BY id ASC"
    with connection() as conn:
        rows = conn.execute(sql, args).fetchall()
    return [dict(r) for r in rows]


def insert_user(data: dict) -> int:
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users
                (age, income, expenses, savings, risk_appetite, financial_goals, account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["age"],
                data["income"],
                data["expenses"],
                data["savings"],
                data["risk_appetite"],
                data["financial_goals"],
                _account_scope(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def delete_user(user_id: int) -> bool:
    account_id = _account_scope()
    sql = "SELECT users.id AS id, reports.pdf_path AS pdf_path FROM users LEFT JOIN reports ON reports.user_id = users.id WHERE users.id = ?"
    args = [user_id]
    if account_id is not None:
        sql += " AND users.account_id = ?"
        args.append(account_id)
    with connection() as conn:
        found = conn.execute(sql, args).fetchone()
        if not found:
            return False
        report = found
        conn.execute("DELETE FROM reports WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    if report is not None:
        remove_pdf(report["pdf_path"])
    return True


def save_report(user_id: int, health_data: dict, ai_report: str) -> None:
    """Store advisory text. PDF location is cleared until a new file is written."""
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO reports (user_id, health_json, ai_report, pdf_blob, pdf_path, generated_at)
            VALUES (?, ?, ?, NULL, NULL, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                health_json  = excluded.health_json,
                ai_report    = excluded.ai_report,
                pdf_blob     = NULL,
                pdf_path     = NULL,
                generated_at = CURRENT_TIMESTAMP
            """,
            (user_id, json.dumps(health_data), ai_report),
        )
        conn.commit()


def store_pdf(user_id: int, pdf_bytes: bytes) -> str:
    name = write_pdf(user_id, pdf_bytes)
    with connection() as conn:
        conn.execute(
            "UPDATE reports SET pdf_path = ?, pdf_blob = NULL WHERE user_id = ?",
            (name, user_id),
        )
        conn.commit()
    return name


def load_report(user_id: int) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            """
            SELECT health_json, ai_report, pdf_path,
                   CASE
                       WHEN pdf_blob IS NOT NULL AND length(pdf_blob) > 0 THEN 1
                       ELSE 0
                   END AS has_blob
            FROM reports WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    if not row:
        return None
    pdf_ready = resolve(row["pdf_path"]) is not None or bool(row["has_blob"])
    return {
        "health": json.loads(row["health_json"]),
        "ai_report": row["ai_report"],
        "pdf_ready": pdf_ready,
    }


def load_pdf_bytes(user_id: int) -> bytes | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT pdf_path, pdf_blob FROM reports WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    path = resolve(row["pdf_path"])
    if path is not None:
        return path.read_bytes()
    if row["pdf_blob"] is None:
        return None
    blob = bytes(row["pdf_blob"])
    return blob or None


def load_chat_history(user_id: int, limit: int = 20) -> list:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT role, message FROM chat_history
            WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [{"role": r["role"], "message": r["message"]} for r in reversed(rows)]


def save_chat_turn(user_id: int, user_message: str, ai_message: str) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
            (user_id, "user", user_message),
        )
        conn.execute(
            "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
            (user_id, "ai", ai_message),
        )
        conn.commit()


def clear_chat_history(user_id: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        conn.commit()


def get_account_by_id(account_id: int):
    with connection() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return dict(row) if row else None


def get_account_by_email(email: str):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    return dict(row) if row else None


def insert_account(email: str, password: str) -> dict:
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO accounts (email, password_hash, auth_provider)
            VALUES (?, ?, 'local')
            """,
            (email.strip().lower(), generate_password_hash(password)),
        )
        conn.commit()
        account_id = cursor.lastrowid
    return get_account_by_id(account_id)


def attach_orphan_profiles(conn) -> None:
    """Point every unowned profile at the bootstrap account. Reports and chats stay put."""
    from config import Config

    cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
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
    existing = conn.execute("SELECT id FROM accounts WHERE email = ?", (email,)).fetchone()
    if existing:
        account_id = existing["id"]
    else:
        cursor = conn.execute(
            """
            INSERT INTO accounts (email, password_hash, auth_provider)
            VALUES (?, ?, 'local')
            """,
            (email, generate_password_hash(password)),
        )
        account_id = cursor.lastrowid
    conn.execute(
        "UPDATE users SET account_id = ? WHERE account_id IS NULL",
        (account_id,),
    )
