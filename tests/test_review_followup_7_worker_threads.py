"""Follow-up 7: claim threads share one worker process. The default is 1."""
import json

import config
import database.db as db_mod
from app import create_app
from conftest import sign_in
from database.repository import enqueue_report_job
from services.jobs import worker
from services.rate_limit import gateway as gw_mod


def _client(tmp_path, monkeypatch, name):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / name))
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    monkeypatch.setattr(config.Config, "FLASK_ENV", "development")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _profile(goals):
    return {
        "age": 30,
        "income": 100000,
        "expenses": 40000,
        "savings": 20000,
        "risk_appetite": "medium",
        "financial_goals": goals,
    }


def test_claim_thread_count_defaults_to_one_and_never_drops_below(monkeypatch):
    monkeypatch.setattr(worker.Config, "WORKER_CLAIM_THREADS", 1)
    assert worker.claim_thread_count() == 1
    monkeypatch.setattr(worker.Config, "WORKER_CLAIM_THREADS", 0)
    assert worker.claim_thread_count() == 1
    monkeypatch.setattr(worker.Config, "WORKER_CLAIM_THREADS", 3)
    assert worker.claim_thread_count() == 3


def test_one_claim_thread_sleeps_when_the_queue_is_empty(monkeypatch):
    monkeypatch.setattr(worker.Config, "WORKER_CLAIM_THREADS", 1)
    seen = {}

    def _idle():
        seen["called"] = True
        return None

    def _sleep(seconds):
        seen["slept"] = seconds
        raise SystemExit(0)

    monkeypatch.setattr(worker, "process_once", _idle)
    monkeypatch.setattr(worker.time, "sleep", _sleep)
    import database.models as models

    monkeypatch.setattr(models, "create_tables", lambda: None)
    try:
        worker.main()
    except SystemExit as exc:
        assert exc.code == 0
    assert seen["called"] is True
    assert seen["slept"] == worker._IDLE_SECONDS


def test_two_jobs_share_one_engine(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, "claims.db")
    sign_in(client, "worker@example.com")
    account_id = client.get("/api/auth/me").get_json()["account_id"]
    ids = []
    for goals in ("house", "car"):
        created = client.post(
            "/api/profile",
            data=json.dumps(_profile(goals)),
            headers={"Content-Type": "application/json"},
        )
        assert created.status_code == 201
        ids.append(created.get_json()["user_id"])
    enqueue_report_job(ids[0], account_id)
    enqueue_report_job(ids[1], account_id)

    import routes.report_routes as report_routes

    monkeypatch.setattr(report_routes, "generate_financial_report", lambda p, h: (True, "advisory"))
    monkeypatch.setattr(report_routes, "generate_pdf_report", lambda *a, **k: (False, "no pdf"))

    engine = db_mod.get_engine()
    pool_size = engine.pool._pool.maxsize
    first = worker.process_once()
    second = worker.process_once()
    assert first["status"] == "succeeded"
    assert second["status"] == "succeeded"
    assert first["id"] != second["id"]
    assert db_mod.get_engine() is engine
    assert pool_size == 10
    assert engine.pool._pool.maxsize == 10
