"""reports.pdf_blob is removed once startup has a file path or an empty blob."""
import database.db as db_mod
from database.models import create_tables


def _blob_column(conn):
    return conn.execute(
        """
        SELECT 1 AS present
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'reports'
          AND column_name = 'pdf_blob'
        """
    ).fetchone()


def test_startup_drops_pdf_blob(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "legacy.db"))
    create_tables()
    conn = db_mod.get_connection()
    try:
        assert _blob_column(conn) is None
    finally:
        conn.close()


def test_fresh_schema_has_no_pdf_blob(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "fresh.db"))
    create_tables()
    conn = db_mod.get_connection()
    try:
        assert _blob_column(conn) is None
        conn.execute(
            "INSERT INTO users (age, income, expenses, savings, risk_appetite, financial_goals) "
            "VALUES (30, 1, 1, 1, 'low', 'house')"
        )
        conn.execute(
            "INSERT INTO reports (user_id, health_json, ai_report) VALUES (1, '{}', 'text')"
        )
        conn.commit()
        row = conn.execute(
            "SELECT ai_report FROM reports WHERE user_id = :user_id",
            {"user_id": 1},
        ).fetchone()
        assert row["ai_report"] == "text"
    finally:
        conn.close()
