"""Follow-up 4: the debug server stays local, and startup keeps a current kind check."""
import pytest

import app as app_mod
import database.db as db_mod
from database.models import create_tables


def _kind_check(conn):
    return conn.execute(
        """
        SELECT oid, pg_get_constraintdef(oid) AS definition
        FROM pg_constraint
        WHERE conrelid = 'jobs'::regclass AND conname = 'jobs_kind_check'
        """
    ).fetchone()


def test_production_entrypoint_does_not_listen(monkeypatch):
    monkeypatch.setattr(app_mod.Config, "FLASK_ENV", "production")

    def _unexpected():
        raise AssertionError("create_app must not run")

    monkeypatch.setattr(app_mod, "create_app", _unexpected)
    with pytest.raises(SystemExit) as excinfo:
        app_mod.serve()
    assert excinfo.value.code == 1


def test_local_entrypoint_runs_the_debugger(monkeypatch):
    monkeypatch.setattr(app_mod.Config, "FLASK_ENV", "development")
    ran = {}

    class _App:
        def run(self, debug=False):
            ran["debug"] = debug

    monkeypatch.setattr(app_mod, "create_app", lambda: _App())
    app_mod.serve()
    assert ran["debug"] is True


def test_second_startup_does_not_replace_the_kind_check(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "kind.db"))
    create_tables()
    conn = db_mod.get_connection()
    conn.execute("ALTER TABLE jobs DROP CONSTRAINT jobs_kind_check")
    conn.execute(
        "ALTER TABLE jobs ADD CONSTRAINT jobs_kind_check CHECK (kind IN ('report'))"
    )
    conn.commit()
    conn.close()

    create_tables()
    conn = db_mod.get_connection()
    replaced = _kind_check(conn)
    conn.close()
    assert "chat" in replaced["definition"]
    assert "report" in replaced["definition"]

    create_tables()
    conn = db_mod.get_connection()
    again = _kind_check(conn)
    conn.close()
    assert again["oid"] == replaced["oid"]
    assert again["definition"] == replaced["definition"]
