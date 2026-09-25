"""Q1: one gateway, config quotas, fail-closed unknown routes, PDF rebuild bucket."""
import json

import app as app_mod
import config
import database.db as db_mod
from app import create_app
from services.rate_limit import gateway as gw_mod
from services.rate_limit import policies as pol_mod
from services.rate_limit.policies import PolicyRegistry


def test_registry_reads_quota_from_config(monkeypatch):
    monkeypatch.setattr(pol_mod.Config, "RATELIMIT_LLM_REPORT", "2 per minute")
    monkeypatch.setattr(pol_mod.Config, "RATELIMIT_LLM_REPORT_USER", "9 per hour")
    pol = PolicyRegistry()
    assert pol.llm_report.limit == 2
    assert pol.llm_report.window_seconds == 60
    assert pol.llm_report_user.limit == 9
    assert pol.llm_report_user.window_seconds == 3600


def test_swagger_requires_api_key(tmp_path, monkeypatch):
    import base64

    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "q1docs.db"))
    monkeypatch.setattr(app_mod.Config, "FLASK_ENV", "development")
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    key = config.Config.API_SECRET_KEY
    basic = base64.b64encode(f"finpilot:{key}".encode()).decode()

    for path in ("/apidocs", "/apidocs/", "/apispec.json"):
        locked = client.get(path)
        assert locked.status_code == 401, path
        assert locked.get_json()["code"] == "unauthorized"
        assert "Basic" in (locked.headers.get("WWW-Authenticate") or "")

        opened = client.get(path, headers={"Authorization": f"Basic {basic}"})
        assert opened.status_code != 401, path
        assert opened.status_code != 429, path


def test_download_is_not_read_report():
    pol = PolicyRegistry()
    rules = pol.rules_for("GET", "/api/download-report/3")
    assert rules[0].route_class == "read_download"
    assert pol.rules_for("GET", "/api/report/3")[0].route_class == "read_report"


def test_unmapped_api_route_is_denied(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "q1.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True

    @app.route("/api/not-a-real-route")
    def _extra():
        return {"ok": True}

    client = app.test_client()
    res = client.get(
        "/api/not-a-real-route",
        headers={"X-API-Key": config.Config.API_SECRET_KEY},
    )
    assert res.status_code == 429
    body = res.get_json()
    assert body["code"] == "rate_policy_missing"


def test_download_rebuild_does_not_use_read_report_bucket(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "q1b.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    gw = gw_mod.get_gateway()
    gw.policies.read_report = type(gw.policies.read_report)("read_report", 1, 60, False)
    gw.policies.pdf_rebuild = type(gw.policies.pdf_rebuild)("pdf_rebuild", 1, 60, False)

    client = app.test_client()
    headers = {
        "X-API-Key": config.Config.API_SECRET_KEY,
        "Content-Type": "application/json",
    }
    created = client.post(
        "/api/profile",
        data=json.dumps({
            "age": 30,
            "income": 1,
            "expenses": 1,
            "savings": 1,
            "risk_appetite": "low",
            "financial_goals": "house",
        }),
        headers=headers,
    )
    user_id = created.get_json()["user_id"]

    import routes.report_routes as rr

    monkeypatch.setattr(
        rr,
        "generate_financial_report",
        lambda p, h: (True, "## Financial Summary\nok"),
    )
    monkeypatch.setattr(rr, "generate_pdf_report", lambda *a, **k: (False, "no pdf"))
    assert client.post(
        "/api/generate-report",
        data=json.dumps({"user_id": user_id}),
        headers=headers,
    ).status_code == 200

    # Exhaust the report-read bucket. Download must still be allowed once.
    assert client.get(f"/api/report/{user_id}", headers=headers).status_code == 200
    assert client.get(f"/api/report/{user_id}", headers=headers).status_code == 429

    def _ok_pdf(profile, health, ai_report, filename=None):
        with open(filename, "wb") as fh:
            fh.write(b"%PDF-1.4 q1")
        return True, filename

    monkeypatch.setattr(rr, "generate_pdf_report", _ok_pdf)
    monkeypatch.setattr(rr, "_load_pdf_blob_from_db", lambda uid: None)
    first = client.get(f"/api/download-report/{user_id}", headers=headers)
    assert first.status_code == 200, first.data
    second = client.get(f"/api/download-report/{user_id}", headers=headers)
    assert second.status_code == 429
    assert second.get_json()["route_class"] == "pdf_rebuild"
    assert client.get(f"/api/report/{user_id}", headers=headers).status_code == 429
