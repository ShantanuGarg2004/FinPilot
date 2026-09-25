"""Q2: chat persistence matches history, report 404/429, profile delete, goal validation."""
import json

import config
import database.db as db_mod
from app import create_app
from services.rate_limit import gateway as gw_mod


def _client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "q2.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    headers = {
        "X-API-Key": config.Config.API_SECRET_KEY,
        "Content-Type": "application/json",
    }
    return client, headers


def _profile(client, headers):
    res = client.post(
        "/api/profile",
        data=json.dumps({
            "age": 30,
            "income": 80000,
            "expenses": 40000,
            "savings": 20000,
            "risk_appetite": "medium",
            "financial_goals": "House",
        }),
        headers=headers,
    )
    assert res.status_code == 201
    return res.get_json()["user_id"]


def test_missing_report_is_404(tmp_path, monkeypatch):
    client, headers = _client(tmp_path, monkeypatch)
    res = client.get("/api/report/99999", headers=headers)
    assert res.status_code == 404
    assert res.get_json()["code"] == "not_found"


def test_report_read_returns_429(tmp_path, monkeypatch):
    client, headers = _client(tmp_path, monkeypatch)
    gw = gw_mod.get_gateway()
    gw.policies.read_report = type(gw.policies.read_report)("read_report", 1, 60, False)
    user_id = _profile(client, headers)
    assert client.get(f"/api/report/{user_id}", headers=headers).status_code == 404
    res = client.get(f"/api/report/{user_id}", headers=headers)
    assert res.status_code == 429
    assert res.get_json()["code"] == "rate_limit_exceeded"


def test_failed_chat_is_504_and_not_stored(tmp_path, monkeypatch):
    client, headers = _client(tmp_path, monkeypatch)
    user_id = _profile(client, headers)
    import routes.chat_routes as chat_routes

    monkeypatch.setattr(
        chat_routes,
        "chat_with_advisor",
        lambda *a, **k: (False, {"error": "AI provider timed out", "code": "upstream_timeout"}),
    )
    res = client.post(
        "/api/chat",
        data=json.dumps({"user_id": user_id, "query": "hello"}),
        headers=headers,
    )
    assert res.status_code == 504
    assert res.get_json()["code"] == "upstream_timeout"
    history = client.get(f"/api/chat/history/{user_id}", headers=headers)
    assert history.status_code == 200
    assert history.get_json()["history"] == []


def test_delete_profile_removes_user(tmp_path, monkeypatch):
    client, headers = _client(tmp_path, monkeypatch)
    user_id = _profile(client, headers)
    deleted = client.delete(f"/api/profile/{user_id}", headers=headers)
    assert deleted.status_code == 200
    listed = client.get("/api/users", headers=headers)
    ids = [u["id"] for u in listed.get_json()["users"]]
    assert user_id not in ids


def test_goal_plan_rejects_short_horizon(tmp_path, monkeypatch):
    client, headers = _client(tmp_path, monkeypatch)
    user_id = _profile(client, headers)
    res = client.post(
        "/api/goal-plan",
        data=json.dumps({
            "user_id": user_id,
            "goal_name": "Car",
            "target_amount": 100000,
            "time_years": 0.1,
        }),
        headers=headers,
    )
    assert res.status_code == 400
