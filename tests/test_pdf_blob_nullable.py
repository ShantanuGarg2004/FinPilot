"""pdf_blob is nullable, including databases created with NOT NULL."""
import database.db as db_mod
from database.models import create_tables


def _seed_legacy_reports(conn):
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age INTEGER NOT NULL,
            income REAL NOT NULL,
            expenses REAL NOT NULL,
            savings REAL NOT NULL,
            risk_appetite TEXT NOT NULL,
            financial_goals TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            health_json TEXT NOT NULL,
            ai_report TEXT NOT NULL,
            pdf_blob BLOB NOT NULL,
            generated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "INSERT INTO users (age, income, expenses, savings, risk_appetite, financial_goals) VALUES (30, 1, 1, 1, 'low', 'house')"
    )
    conn.execute(
        "INSERT INTO reports (user_id, health_json, ai_report, pdf_blob) VALUES (1, '{}', 'saved text', ?)",
        (b"",),
    )
    conn.commit()


def test_legacy_not_null_pdf_blob_becomes_nullable(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "legacy.db"))
    conn = db_mod.get_connection()
    _seed_legacy_reports(conn)
    conn.close()

    create_tables()

    conn = db_mod.get_connection()
    info = {row["name"]: row["notnull"] for row in conn.execute("PRAGMA table_info(reports)")}
    assert info["pdf_blob"] == 0

    row = conn.execute("SELECT ai_report, pdf_blob FROM reports WHERE user_id = 1").fetchone()
    assert row["ai_report"] == "saved text"
    assert row["pdf_blob"] is None

    conn.execute(
        "INSERT INTO users (age, income, expenses, savings, risk_appetite, financial_goals) VALUES (31, 1, 1, 1, 'low', 'car')"
    )
    conn.execute(
        "INSERT INTO reports (user_id, health_json, ai_report, pdf_blob) VALUES (2, '{}', 'no pdf', NULL)"
    )
    conn.commit()
    stored = conn.execute("SELECT pdf_blob FROM reports WHERE user_id = 2").fetchone()
    assert stored["pdf_blob"] is None
    conn.close()


def test_fresh_schema_accepts_null_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "fresh.db"))
    create_tables()
    conn = db_mod.get_connection()
    info = {row["name"]: row["notnull"] for row in conn.execute("PRAGMA table_info(reports)")}
    assert info["pdf_blob"] == 0
    conn.execute(
        "INSERT INTO users (age, income, expenses, savings, risk_appetite, financial_goals) VALUES (30, 1, 1, 1, 'low', 'house')"
    )
    conn.execute(
        "INSERT INTO reports (user_id, health_json, ai_report, pdf_blob) VALUES (1, '{}', 'text', NULL)"
    )
    conn.commit()
    assert conn.execute("SELECT pdf_blob FROM reports").fetchone()["pdf_blob"] is None
    conn.close()
