"""pdf_blob is nullable on the PostgreSQL schema."""
import database.db as db_mod
from database.models import create_tables


def _blob_nullable(conn) -> bool:
    row = conn.execute(
        """
        SELECT is_nullable
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'reports'
          AND column_name = 'pdf_blob'
        """
    ).fetchone()
    return row is not None and row["is_nullable"] == "YES"


def test_legacy_not_null_pdf_blob_becomes_nullable(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "legacy.db"))
    create_tables()
    conn = db_mod.get_connection()
    assert _blob_nullable(conn) is True
    conn.execute(
        "INSERT INTO users (age, income, expenses, savings, risk_appetite, financial_goals) "
        "VALUES (30, 1, 1, 1, 'low', 'house')"
    )
    conn.execute(
        "INSERT INTO reports (user_id, health_json, ai_report, pdf_blob) VALUES (1, '{}', 'saved text', NULL)"
    )
    conn.commit()
    row = conn.execute("SELECT ai_report, pdf_blob FROM reports WHERE user_id = 1").fetchone()
    assert row["ai_report"] == "saved text"
    assert row["pdf_blob"] is None
    conn.close()


def test_fresh_schema_accepts_null_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "fresh.db"))
    create_tables()
    conn = db_mod.get_connection()
    assert _blob_nullable(conn) is True
    conn.execute(
        "INSERT INTO users (age, income, expenses, savings, risk_appetite, financial_goals) "
        "VALUES (30, 1, 1, 1, 'low', 'house')"
    )
    conn.execute(
        "INSERT INTO reports (user_id, health_json, ai_report, pdf_blob) VALUES (1, '{}', 'text', NULL)"
    )
    conn.commit()
    assert conn.execute("SELECT pdf_blob FROM reports").fetchone()["pdf_blob"] is None
    conn.close()
