"""One-time copy of an existing finance.db into PostgreSQL."""
import logging
import re
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_TABLES = ("accounts", "users", "reports", "chat_history")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ident(name: str) -> str:
    if not _IDENT.fullmatch(name):
        raise ValueError(f"refusing SQL identifier {name!r}")
    return name


def import_sqlite_if_empty(conn, sqlite_path: str = "finance.db") -> int:
    """
    Copy rows when PostgreSQL has no profiles yet and a SQLite file is present.
    Existing PostgreSQL rows are left alone. A normal start does not call this.
    """
    present = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    if present:
        return 0
    path = Path(sqlite_path)
    if not path.is_file():
        return 0

    source = sqlite3.connect(path)
    source.row_factory = sqlite3.Row
    try:
        copied = 0
        for table in _TABLES:
            if not _sqlite_table(source, table):
                continue
            columns = [row[1] for row in source.execute(f"PRAGMA table_info({_ident(table)})")]
            target_columns = {
                row["name"]
                for row in conn.execute(
                    """
                    SELECT column_name AS name
                    FROM information_schema.columns
                    WHERE table_schema = current_schema() AND table_name = :table_name
                    """,
                    {"table_name": table},
                )
            }
            use = [_ident(name) for name in columns if name in target_columns and _IDENT.fullmatch(name)]
            if not use or "id" not in use:
                continue
            rows = source.execute(
                f"SELECT {', '.join(use)} FROM {_ident(table)}"
            ).fetchall()
            if not rows:
                continue
            binds = ", ".join(f":{name}" for name in use)
            sql = f"INSERT INTO {_ident(table)} ({', '.join(use)}) VALUES ({binds})"
            for row in rows:
                conn.execute(sql, {name: row[name] for name in use})
            copied += len(rows)
            conn.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{_ident(table)}', 'id'),
                    (SELECT MAX(id) FROM {_ident(table)})
                )
                """
            )
        if copied:
            logger.info("Copied %d row(s) from %s into PostgreSQL", copied, path)
        return copied
    finally:
        source.close()


def _sqlite_table(source, name: str) -> bool:
    row = source.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = :name",
        {"name": name},
    ).fetchone()
    return row is not None
