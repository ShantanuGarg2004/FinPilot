"""Q4: one actor, per-profile ceilings, local CORS, Swagger off outside local."""
import json

import pytest

import config
import database.db as db_mod
from app import create_app
from services.actor import Actor
from services.rate_limit import gateway as gw_mod
from services.rate_limit.keys import hash_api_key
from services.rate_limit.policies import PolicyRegistry


def _app(tmp_path, monkeypatch, name="q4.db"):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / name))
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    return app


def _headers():
    return {
        "X-API-Key": config.Config.API_SECRET_KEY,
        "Content-Type": "application/json",
    }


def _profile(goals="house"):
    return {
        "age": 30,
        "income": 100000,
        "expenses": 40000,
        "savings": 20000,
        "risk_appetite": "medium",
        "financial_goals": goals,
    }


def test_rate_limit_subject_is_key_hash_until_accounts_exist():
    actor = Actor(kind="api_key", credential="secret-one")
    assert actor.rate_limit_subject() == hash_api_key("secret-one")
    later = Actor(kind="user", credential="42")
    assert later.rate_limit_subject() == "acct:42"


def test_per_profile_rules_cover_chat_generate_goal_and_delete():
    pol = PolicyRegistry()
    assert any(r.per_user for r in pol.rules_for("POST", "/api/chat"))
    assert any(r.per_user for r in pol.rules_for("POST", "/api/generate-report"))
    assert any(r.per_user for r in pol.rules_for("POST", "/api/goal-plan"))
    delete_rules = pol.rules_for("DELETE", "/api/profile/3")
    assert any(r.per_user for r in delete_rules)
    assert any(not r.per_user for r in delete_rules)


def test_cors_allows_local_vite_only(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "cors.db")
    client = app.test_client()
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    blocked = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert blocked.headers.get("Access-Control-Allow-Origin") != "https://evil.example"


def test_swagger_disabled_outside_local(tmp_path, monkeypatch):
    monkeypatch.setattr(config.Config, "FLASK_ENV", "production")
    app = _app(tmp_path, monkeypatch, "docs.db")
    client = app.test_client()
    res = client.get("/apidocs/")
    assert res.status_code == 404
    assert res.get_json()["code"] == "not_found"


def test_empty_cors_fails_closed_in_production(monkeypatch):
    monkeypatch.setattr(config.Config, "FLASK_ENV", "production")
    monkeypatch.setattr(config.Config, "CORS_ORIGINS", [])
    monkeypatch.setattr(config.Config, "GROQ_API_KEY", "k")
    monkeypatch.setattr(config.Config, "API_SECRET_KEY", "s")
    with pytest.raises(EnvironmentError) as excinfo:
        config.Config.validate()
    assert "CORS_ORIGINS" in str(excinfo.value)


def test_goal_ceiling_is_per_profile(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "goal.db")
    client = app.test_client()
    headers = _headers()
    created = client.post("/api/profile", data=json.dumps(_profile()), headers=headers)
    user_id = created.get_json()["user_id"]
    other = client.post("/api/profile", data=json.dumps(_profile("car")), headers=headers)
    other_id = other.get_json()["user_id"]

    gw = gw_mod.get_gateway()
    rule = type(gw.policies.write_goal)
    gw.policies.write_goal = rule("write_goal", 100, 60, False)
    gw.policies.write_goal_user = rule("write_goal", 1, 3600, True)

    body = {"user_id": user_id, "target_amount": 100000, "time_years": 2}
    first = client.post("/api/goal-plan", data=json.dumps(body), headers=headers)
    second = client.post("/api/goal-plan", data=json.dumps(body), headers=headers)
    third = client.post(
        "/api/goal-plan",
        data=json.dumps({**body, "user_id": other_id}),
        headers=headers,
    )
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.get_json()["route_class"] == "write_goal"
    assert third.status_code == 200


def test_delete_ceiling_is_per_profile(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "del.db")
    client = app.test_client()
    headers = _headers()
    created = client.post("/api/profile", data=json.dumps(_profile()), headers=headers)
    user_id = created.get_json()["user_id"]

    gw = gw_mod.get_gateway()
    rule = type(gw.policies.write_profile)
    gw.policies.write_profile = rule("write_profile", 100, 60, False)
    gw.policies.delete_profile_user = rule("write_profile", 1, 3600, True)

    assert client.delete(f"/api/profile/{user_id}", headers=headers).status_code == 200
    again = client.delete(f"/api/profile/{user_id}", headers=headers)
    assert again.status_code == 429
    assert again.get_json()["route_class"] == "write_profile"
