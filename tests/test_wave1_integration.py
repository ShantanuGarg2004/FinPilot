"""Integration / system tests for Wave 1 gateway (memory backend)."""
import json

import pytest

import config
import database.db as db_mod
from app import create_app
from services.rate_limit import gateway as gw_mod
from services.rate_limit.policies import PolicyRegistry


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "wave1.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    monkeypatch.setattr(config.Config, "FLASK_ENV", "production")
    gw_mod._gateway = None

    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), {
        "X-API-Key": config.Config.API_SECRET_KEY,
        "Content-Type": "application/json",
    }


def test_health_reports_wave1_backend(client):
    c, _ = client
    res = c.get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["ratelimit_backend"] == "memory"
    assert body["ratelimit_store_ok"] is True


def test_options_never_429(client):
    c, headers = client
    for _ in range(30):
        assert c.options("/api/report/1", headers=headers).status_code != 429


def test_read_burst_under_read_quota(client):
    c, headers = client
    for _ in range(40):
        res = c.get("/api/report/1", headers=headers)
        assert res.status_code in (200, 404)
        assert res.status_code != 429


def test_generate_report_rate_limited_with_route_class(client, monkeypatch):
    c, headers = client
    import routes.report_routes as rr

    # Tighten llm_report minute cap for a fast denial.
    gw = gw_mod.get_gateway()
    assert gw is not None
    gw.policies.llm_report = type(gw.policies.llm_report)("llm_report", 2, 60, False)
    gw.policies.llm_report_user = type(gw.policies.llm_report_user)("llm_report", 100, 3600, True)

    monkeypatch.setattr(
        rr,
        "get_user_by_id",
        lambda uid: {
            "id": uid,
            "age": 30,
            "income": 1,
            "expenses": 1,
            "savings": 1,
            "risk_appetite": "low",
            "financial_goals": "abcdefghij",
        },
    )
    monkeypatch.setattr(
        rr,
        "calculate_health_score",
        lambda p: {"score": 1, "insights": [], "warnings": [], "pillar_scores": {}},
    )
    monkeypatch.setattr(rr, "generate_financial_report", lambda p, h: (True, "ok"))

    def _fake_pdf(profile, health, ai_report, filename=None):
        with open(filename, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        return True, filename

    monkeypatch.setattr(rr, "generate_pdf_report", _fake_pdf)
    monkeypatch.setattr(rr, "_save_report_to_db", lambda *a, **k: None)

    codes = []
    bodies = []
    for _ in range(5):
        res = c.post("/api/generate-report", data=json.dumps({"user_id": 1}), headers=headers)
        codes.append(res.status_code)
        if res.status_code == 429:
            bodies.append(res.get_json())
    assert 429 in codes
    assert any(c == 200 for c in codes)
    assert bodies[0]["code"] == "rate_limit_exceeded"
    assert bodies[0]["route_class"] == "llm_report"
    assert "Retry-After" in res.headers or bodies[0].get("retry_after") is not None


def test_sql_backend_ping_when_configured(tmp_path, monkeypatch):
    """Optional: if RATELIMIT_DATABASE_URL works, sql store must ping."""
    url = config.Config.RATELIMIT_DATABASE_URL
    if not url:
        pytest.skip("no RATELIMIT_DATABASE_URL in environment")

    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "wave1_sql.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "sql")
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    gw_mod._gateway = None

    try:
        from services.rate_limit.sql_store import SqlRateLimitStore

        store = SqlRateLimitStore(url)
        if not store.ping():
            pytest.skip("postgres not reachable")
        r1 = store.incr_and_check("wave1-test-key", 60, 100)
        assert r1.allowed
    finally:
        gw_mod._gateway = None
