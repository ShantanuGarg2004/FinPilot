"""Follow-up 8: health JSON is jsonb and timestamps are timestamptz."""
import json
from pathlib import Path

import database.db as db_mod
from database.models import create_tables
from database.repository import load_report, save_report


_SQL = Path(__file__).resolve().parents[1] / "database" / "sql" / "issue8_column_types.sql"


def _udt(conn, table, column):
    row = conn.execute(
        """
        SELECT udt_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = :table_name
          AND column_name = :column_name
        """,
        {"table_name": table, "column_name": column},
    ).fetchone()
    return row["udt_name"]


def _apply(conn):
    conn.execute(_SQL.read_text(encoding="utf-8"))
    conn.commit()


def test_new_schema_uses_jsonb_and_timestamptz(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "types.db"))
    create_tables()
    conn = db_mod.get_connection()
    try:
        assert _udt(conn, "accounts", "created_at") == "timestamptz"
        assert _udt(conn, "users", "created_at") == "timestamptz"
        assert _udt(conn, "reports", "generated_at") == "timestamptz"
        assert _udt(conn, "reports", "health_json") == "jsonb"
        assert _udt(conn, "reports", "ai_report") == "text"
        assert _udt(conn, "chat_history", "created_at") == "timestamptz"
    finally:
        conn.close()


def test_script_converts_text_columns_and_round_trips_health(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "legacy.db"))
    create_tables()
    conn = db_mod.get_connection()
    try:
        conn.execute("ALTER TABLE reports ALTER COLUMN health_json TYPE text")
        conn.execute("ALTER TABLE reports ALTER COLUMN generated_at TYPE text")
        conn.execute("ALTER TABLE accounts ALTER COLUMN created_at TYPE text")
        conn.execute("ALTER TABLE users ALTER COLUMN created_at TYPE text")
        conn.execute("ALTER TABLE chat_history ALTER COLUMN created_at TYPE text")
        conn.execute(
            """
            INSERT INTO accounts (email, password_hash)
            VALUES ('person@example.com', 'hash')
            """
        )
        account_id = conn.execute(
            "SELECT id FROM accounts WHERE email = :email",
            {"email": "person@example.com"},
        ).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO users
                (age, income, expenses, savings, risk_appetite, financial_goals, account_id, created_at)
            VALUES (30, 1, 1, 1, 'low', 'house', :account_id, '2026-09-27 18:00:00+00')
            """,
            {"account_id": account_id},
        )
        user_id = conn.execute("SELECT id FROM users").fetchone()["id"]
        conn.execute(
            """
            INSERT INTO reports (user_id, health_json, ai_report, generated_at)
            VALUES (:user_id, :health_json, 'keep this prose', '2026-09-27 18:05:00+00')
            """,
            {"user_id": user_id, "health_json": json.dumps({"score": 70})},
        )
        conn.commit()
        assert _udt(conn, "reports", "health_json") == "text"
        _apply(conn)
        assert _udt(conn, "reports", "health_json") == "jsonb"
        assert _udt(conn, "reports", "generated_at") == "timestamptz"
        assert _udt(conn, "reports", "ai_report") == "text"
        assert _udt(conn, "accounts", "created_at") == "timestamptz"
        assert _udt(conn, "users", "created_at") == "timestamptz"
        assert _udt(conn, "chat_history", "created_at") == "timestamptz"
        _apply(conn)
        assert _udt(conn, "reports", "health_json") == "jsonb"
    finally:
        conn.close()

    loaded = load_report(user_id)
    assert loaded["health"]["score"] == 70
    assert loaded["ai_report"] == "keep this prose"
    save_report(user_id, {"score": 71}, "keep this prose")
    assert load_report(user_id)["health"]["score"] == 71
