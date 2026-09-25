import logging
from database.db import get_connection
from database.pdf_files import export_legacy_blobs

logger = logging.getLogger(__name__)


def create_tables():
    """
    Create all application tables if they don't exist, then ensure
    performance indexes are present.  Safe to call on every startup.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT,
            auth_provider   TEXT NOT NULL DEFAULT 'local',
            session_version INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── users ──────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            age              INTEGER NOT NULL,
            income           REAL    NOT NULL,
            expenses         REAL    NOT NULL,
            savings          REAL    NOT NULL,
            risk_appetite    TEXT    NOT NULL,
            financial_goals  TEXT    NOT NULL,
            created_at       TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── reports ────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL UNIQUE
                             REFERENCES users(id) ON DELETE CASCADE,
            health_json  TEXT    NOT NULL,
            ai_report    TEXT    NOT NULL,
            pdf_blob     BLOB,
            pdf_path     TEXT,
            generated_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _ensure_pdf_blob_nullable(cursor)
    _ensure_pdf_path(cursor)
    _ensure_account_id(cursor)

    # ── chat_history ───────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL
                           REFERENCES users(id) ON DELETE CASCADE,
            role       TEXT NOT NULL CHECK(role IN ('user', 'ai')),
            message    TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Indexes ────────────────────────────────────────────────────────────
    # reports.user_id  — every report lookup is by user_id
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reports_user_id
        ON reports(user_id)
    """)

    # chat_history.user_id + id (DESC) — history queries filter by user
    # then page by recency; the composite index covers both at once
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_history_user_id
        ON chat_history(user_id, id DESC)
    """)

    from database.repository import attach_orphan_profiles

    conn.commit()
    attach_orphan_profiles(conn)
    export_legacy_blobs(conn)
    conn.commit()
    conn.close()
    logger.info("Database tables and indexes verified / created.")


def _pdf_blob_notnull(cursor) -> bool:
    cursor.execute("PRAGMA table_info(reports)")
    for row in cursor.fetchall():
        if row["name"] == "pdf_blob":
            return bool(row["notnull"])
    return False


def _ensure_account_id(cursor) -> None:
    cursor.execute("PRAGMA table_info(users)")
    names = {row["name"] for row in cursor.fetchall()}
    if "account_id" not in names:
        logger.info("Migration: adding users.account_id")
        cursor.execute("ALTER TABLE users ADD COLUMN account_id INTEGER REFERENCES accounts(id)")


def _ensure_pdf_path(cursor) -> None:
    cursor.execute("PRAGMA table_info(reports)")
    names = {row["name"] for row in cursor.fetchall()}
    if "pdf_path" not in names:
        logger.info("Migration: adding reports.pdf_path")
        cursor.execute("ALTER TABLE reports ADD COLUMN pdf_path TEXT")


def _ensure_pdf_blob_nullable(cursor) -> None:
    """SQLite cannot ALTER a column to drop NOT NULL; rebuild reports when needed."""
    if not _pdf_blob_notnull(cursor):
        return

    logger.info("Migration: rebuilding reports so pdf_blob is nullable")
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.execute("""
        CREATE TABLE reports_nullable (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL UNIQUE
                             REFERENCES users(id) ON DELETE CASCADE,
            health_json  TEXT    NOT NULL,
            ai_report    TEXT    NOT NULL,
            pdf_blob     BLOB,
            generated_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT INTO reports_nullable (id, user_id, health_json, ai_report, pdf_blob, generated_at)
        SELECT id, user_id, health_json, ai_report,
               CASE
                   WHEN pdf_blob IS NULL OR length(pdf_blob) = 0 THEN NULL
                   ELSE pdf_blob
               END,
               generated_at
        FROM reports
    """)
    cursor.execute("DROP TABLE reports")
    cursor.execute("ALTER TABLE reports_nullable RENAME TO reports")
    cursor.execute("PRAGMA foreign_keys=ON")