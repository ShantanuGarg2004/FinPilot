import sqlite3
import logging

from config import Config

logger  = logging.getLogger(__name__)
DB_NAME = "finance.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection with:
      - WAL journal mode   → allows concurrent reads while a write is in progress
      - Foreign-key enforcement
      - Row factory        → rows accessible by column name
    """
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")   # Write-Ahead Logging
    conn.execute("PRAGMA foreign_keys=ON")    # enforce FK constraints
    conn.execute("PRAGMA synchronous=NORMAL") # safe + faster than FULL with WAL
    # Wait briefly for the single writer instead of failing immediately under load.
    conn.execute(f"PRAGMA busy_timeout={int(Config.SQLITE_BUSY_TIMEOUT_MS)}")

    return conn