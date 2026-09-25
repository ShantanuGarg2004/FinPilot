"""Profile, report, and chat SQL. Routes call these functions."""
import json

from database.db import connection
from database.pdf_files import remove_pdf, resolve, write_pdf


def get_latest_user():
    with connection() as conn:
        row = conn.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    with connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_all_users():
    with connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
    return [dict(r) for r in rows]


def insert_user(data: dict) -> int:
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users
                (age, income, expenses, savings, risk_appetite, financial_goals)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["age"],
                data["income"],
                data["expenses"],
                data["savings"],
                data["risk_appetite"],
                data["financial_goals"],
            ),
        )
        conn.commit()
        return cursor.lastrowid


def delete_user(user_id: int) -> bool:
    with connection() as conn:
        found = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not found:
            return False
        report = conn.execute(
            "SELECT pdf_path FROM reports WHERE user_id = ?",
            (user_id,),
        ).fetchone()
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
