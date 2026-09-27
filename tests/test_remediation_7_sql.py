"""Named SQL binds reject a mismatch instead of running a half-bound statement."""
import pytest

import database.db as db_mod
from database.db import DatabaseError
from database.models import create_tables


def test_named_parameter_mismatch_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "binds.db"))
    create_tables()
    conn = db_mod.get_connection()
    try:
        with pytest.raises(DatabaseError):
            conn.execute("SELECT 1 AS n", (1,))
        with pytest.raises(DatabaseError):
            conn.execute("SELECT :user_id AS id", {})
    finally:
        conn.close()
