"""Issue 4: health fails when the application database does not answer."""
from flask import g

import app as app_mod
import config
import database.db as db_mod
from app import create_app
from services.rate_limit import gateway as gw_mod


def _app(tmp_path, monkeypatch, name):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / name))
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    monkeypatch.setattr(config.Config, "FLASK_ENV", "development")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    return app


def test_health_is_ok_when_the_database_answers(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "health.db")
    res = app.test_client().get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok"
    assert body["database_ok"] is True
    assert body["database_backend"] == "postgresql"
    assert "sqlite_busy_timeout_ms" not in body
    assert "database_url" not in body


def test_health_is_degraded_when_the_database_ping_fails(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "health-down.db")
    monkeypatch.setattr(app_mod, "ping_database", lambda: False)
    res = app.test_client().get("/api/health")
    assert res.status_code == 503
    body = res.get_json()
    assert body["status"] == "degraded"
    assert body["database_ok"] is False
    assert body["database_backend"] == "unavailable"
    assert "sqlite_busy_timeout_ms" not in body


def test_ping_does_not_store_the_request_connection(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "health-conn.db")
    with app.test_request_context("/api/health"):
        assert app_mod.ping_database() is True
        assert getattr(g, "db_conn", None) is None
