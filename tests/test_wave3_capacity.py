"""Wave 3: busy timeout, worker formula, upstream timeout mapping."""
import database.db as db_mod
from config import Config, recommended_worker_count
from services import ai_service


def test_sqlite_connection_sets_busy_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "busy.db"))
    monkeypatch.setattr(Config, "SQLITE_BUSY_TIMEOUT_MS", 4321)
    conn = db_mod.get_connection()
    timeout_ms = conn.execute("PRAGMA busy_timeout").fetchone()[0]
    conn.close()
    assert timeout_ms == 4321


def test_recommended_workers_adds_headroom():
    assert recommended_worker_count(4, 2) == 6
    assert recommended_worker_count(0, 0) == 2


def test_worker_timeout_must_exceed_groq_timeout(monkeypatch):
    monkeypatch.setattr(Config, "GROQ_API_KEY", "k")
    monkeypatch.setattr(Config, "API_SECRET_KEY", "s")
    monkeypatch.setattr(Config, "GROQ_TIMEOUT_SECONDS", 90)
    monkeypatch.setattr(Config, "WORKER_TIMEOUT_SECONDS", 90)
    try:
        Config.validate()
    except EnvironmentError as exc:
        assert "WORKER_TIMEOUT_SECONDS" in str(exc)
    else:
        raise AssertionError("validate should reject equal timeouts")


def test_ask_gpt_maps_timeout(monkeypatch):
    from groq import APITimeoutError

    def _raise(**kwargs):
        raise APITimeoutError(request=None)

    monkeypatch.setattr(ai_service.client.chat.completions, "create", _raise)
    ok, out = ai_service.ask_gpt("hi")
    assert ok is False
    assert out["code"] == "upstream_timeout"
    assert ai_service.http_status_for_ai_code(out["code"]) == 504


def test_health_reports_capacity_settings(tmp_path, monkeypatch):
    import config
    from app import create_app
    from services.rate_limit import gateway as gw_mod

    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "wave3.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    res = app.test_client().get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["worker_timeout_seconds"] > body["groq_timeout_seconds"]
    assert body["recommended_workers"] >= 2
    assert body["sqlite_busy_timeout_ms"] > 0
