"""Wave 2 unit/integration: persist-before-PDF, soft-fail, sanitize, chat context."""
import json
import tempfile
from pathlib import Path

import pytest

import config
import database.db as db_mod
from app import create_app
from services.rate_limit import gateway as gw_mod
from services.pdf_service import clean_ai_text, generate_pdf_report
from services import ai_service


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "wave2.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
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
                "age": 30,
                "income": 90000,
                "expenses": 40000,
                "savings": 25000,
                "risk_appetite": "medium",
                "financial_goals": "Buy a house",
            }
        ),
        headers=headers,
    )
    assert res.status_code == 201
    return res.get_json()["user_id"]


def test_clean_ai_text_strips_tables_and_escapes_risk():
    raw = """
## Financial Summary
Hello **world** & friends <script>

| Col | Val |
| --- | --- |
| A | 1 |

Done.
"""
    cleaned = clean_ai_text(raw)
    assert "Col" not in cleaned or "|" not in cleaned
    assert "**" not in cleaned
    assert "<script>" not in cleaned
    assert "Hello world" in cleaned or "Hello" in cleaned


def test_pdf_survives_ampersand_and_angle_brackets():
    profile = {
        "age": 30,
        "income": 1,
        "expenses": 1,
        "savings": 1,
        "risk_appetite": "low",
        "financial_goals": "Save & grow <fast>",
    }
    health = {
        "score": 50,
        "insights": ["Income > expenses & OK"],
        "warnings": ["Watch <debt>"],
        "pillar_scores": {},
    }
    ai = "## Financial Summary\nUse SIPs & ETFs <carefully>\n\n| bad | table |\n| --- | --- |\n| x | y |\n"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        path = tmp.name
    try:
        ok, result = generate_pdf_report(profile, health, ai, filename=path)
        assert ok is True, result
        assert Path(path).stat().st_size > 100
    finally:
        Path(path).unlink(missing_ok=True)


def test_generate_persists_when_pdf_fails(client, monkeypatch):
    c, headers = client
    user_id = _create_user(c, headers)
    import routes.report_routes as rr

    monkeypatch.setattr(
        rr,
        "generate_financial_report",
        lambda p, h: (True, "## Financial Summary\nAdvisory text saved."),
    )
    monkeypatch.setattr(
        rr,
        "generate_pdf_report",
        lambda *a, **k: (False, "simulated PDF parse error"),
    )

    res = c.post(
        "/api/generate-report",
        data=json.dumps({"user_id": user_id}),
        headers=headers,
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["pdf_ready"] is False
    assert "Advisory text saved" in body["ai_report"]
    assert body.get("pdf_error")

    get = c.get(f"/api/report/{user_id}", headers=headers)
    assert get.status_code == 200
    stored = get.get_json()
    assert "Advisory text saved" in stored["ai_report"]
    assert stored["pdf_ready"] is False


def test_download_regenerates_pdf_without_ai(client, monkeypatch):
    c, headers = client
    user_id = _create_user(c, headers)
    import routes.report_routes as rr

    monkeypatch.setattr(
        rr,
        "generate_financial_report",
        lambda p, h: (True, "## Financial Summary\nok\n## Budget Optimization\nb\n"),
    )
    # First generate: PDF fails
    monkeypatch.setattr(
        rr,
        "generate_pdf_report",
        lambda *a, **k: (False, "fail once"),
    )
    assert c.post(
        "/api/generate-report",
        data=json.dumps({"user_id": user_id}),
        headers=headers,
    ).status_code == 200

    # Download: PDF succeeds (regen path)
    calls = {"n": 0}

    def _ok_pdf(profile, health, ai_report, filename=None):
        calls["n"] += 1
        with open(filename, "wb") as fh:
            fh.write(b"%PDF-1.4 regen")
        return True, filename

    monkeypatch.setattr(rr, "generate_pdf_report", _ok_pdf)
    # Ensure AI is NOT called again
    monkeypatch.setattr(
        rr,
        "generate_financial_report",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("AI must not run on download")),
    )

    res = c.get(f"/api/download-report/{user_id}", headers=headers)
    assert res.status_code == 200
    assert res.data.startswith(b"%PDF")
    assert calls["n"] == 1

    # Second download should use cached blob (no regen required)
    monkeypatch.setattr(
        rr,
        "generate_pdf_report",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should use cached blob")),
    )
    res2 = c.get(f"/api/download-report/{user_id}", headers=headers)
    assert res2.status_code == 200


def test_format_conversation_context_prefers_recent_and_message_key():
    history = [{"role": "user", "message": f"msg-{i}"} for i in range(30)]
    ctx = ai_service.format_conversation_context(history)
    assert "msg-29" in ctx
    assert "msg-0" not in ctx  # outside last 20


def test_ask_gpt_maps_rate_limit_error(monkeypatch):
    from groq import RateLimitError

    class _Resp:
        status_code = 429
        headers = {}
        request = None

    def _raise(**kwargs):
        raise RateLimitError("rate limited", response=_Resp(), body={"error": "rate limited"})

    monkeypatch.setattr(ai_service.client.chat.completions, "create", _raise)
    ok, out = ai_service.ask_gpt("hi")
    assert ok is False
    assert isinstance(out, dict)
    assert out["code"] == "upstream_rate_limit"


def test_ask_gpt_maps_generic_exception_to_upstream_error(monkeypatch):
    def _raise(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ai_service.client.chat.completions, "create", _raise)
    ok, out = ai_service.ask_gpt("hi")
    assert ok is False
    assert out["code"] == "upstream_error"
    assert "boom" in out["error"]
