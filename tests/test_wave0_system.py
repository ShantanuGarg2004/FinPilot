"""System-level Wave 0 checks: end-to-end read vs LLM policy behaviour.

These tests exercise the full Flask stack (auth + limiter + routes) with a
temporary database. External Groq/PDF work is stubbed only where the test
focuses on limiter behaviour.
"""
import json

import pytest

import config
import database.db as db_mod
from app import create_app
from extensions import limiter


@pytest.fixture()
def system_client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "wave0_system.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_URI", "memory://")
    monkeypatch.setattr(config.Config, "RATELIMIT_READ", "50 per minute")
    monkeypatch.setattr(config.Config, "RATELIMIT_LLM_REPORT", "2 per minute")
    limiter.enabled = True

    try:
        limiter.reset()
    except Exception:
        pass

    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), {
        "X-API-Key": config.Config.API_SECRET_KEY,
        "Content-Type": "application/json",
    }


def _create_user(client, headers):
    res = client.post(
        "/api/profile",
        data=json.dumps(
            {
                "age": 32,
                "income": 100000,
                "expenses": 55000,
                "savings": 30000,
                "risk_appetite": "high",
                "financial_goals": "Early retirement",
            }
        ),
        headers=headers,
    )
    assert res.status_code == 201
    return res.get_json()["user_id"]


def test_system_read_burst_stays_under_read_quota(system_client):
    """Many GET /report calls must not 429 under Wave 0 read ceiling."""
    client, headers = system_client
    user_id = _create_user(client, headers)

    statuses = []
    for _ in range(30):
        res = client.get(f"/api/report/{user_id}", headers=headers)
        statuses.append(res.status_code)
        # 404 is fine (no report yet); 429 is the regression we fixed.
        assert res.status_code != 429
    assert all(s in (200, 404) for s in statuses)


def test_system_options_and_get_interleaved(system_client):
    client, headers = system_client
    user_id = _create_user(client, headers)
    for _ in range(20):
        opt = client.options(f"/api/report/{user_id}", headers=headers)
        get = client.get(f"/api/report/{user_id}", headers=headers)
        assert opt.status_code != 429
        assert get.status_code != 429


def test_system_llm_quota_independent_of_reads(system_client, monkeypatch):
    """Reads should not burn LLM quota; LLM endpoint still enforces its own cap."""
    client, headers = system_client
    user_id = _create_user(client, headers)

    import routes.report_routes as rr

    monkeypatch.setattr(
        rr,
        "calculate_health_score",
        lambda p: {"score": 60, "insights": [], "warnings": [], "pillar_scores": {}},
    )
    monkeypatch.setattr(rr, "generate_financial_report", lambda p, h: (True, "report text"))

    def _fake_pdf(profile, health, ai_report, filename=None):
        with open(filename, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        return True, filename

    monkeypatch.setattr(rr, "generate_pdf_report", _fake_pdf)
    monkeypatch.setattr(rr, "_save_report_to_db", lambda *a, **k: None)

    for _ in range(25):
        assert client.get(f"/api/report/{user_id}", headers=headers).status_code != 429

    codes = []
    for _ in range(4):
        res = client.post(
            "/api/generate-report",
            data=json.dumps({"user_id": user_id}),
            headers=headers,
        )
        codes.append(res.status_code)
    assert 429 in codes
    # At least one generate should have succeeded before throttle.
    assert any(c == 200 for c in codes)


def test_system_disabled_ratelimit_allows_burst(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "wave0_off.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", False)
    monkeypatch.setattr(config.Config, "RATELIMIT_LLM_REPORT", "1 per minute")

    limiter.enabled = False
    try:
        try:
            limiter.reset()
        except Exception:
            pass

        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        headers = {
            "X-API-Key": config.Config.API_SECRET_KEY,
            "Content-Type": "application/json",
        }

        import routes.report_routes as rr

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
                "financial_goals": "x" * 10,
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

        codes = [
            client.post("/api/generate-report", data=json.dumps({"user_id": 1}), headers=headers).status_code
            for _ in range(5)
        ]
        assert 429 not in codes
        assert all(c == 200 for c in codes)
    finally:
        limiter.enabled = True
