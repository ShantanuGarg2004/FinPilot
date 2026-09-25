"""Q3: one SQLite connection per request, PDFs on disk, score and goal bands."""
import json
import config
import database.db as db_mod
from app import create_app
from config import Config
from database.models import create_tables
from database.pdf_files import file_name_for
from services.goal_service import _feasibility_label, calculate_goal_plan
from services.health_service import calculate_health_score
from services.rate_limit import gateway as gw_mod


def _profile(**overrides):
    data = {
        "age": 35,
        "income": 100000,
        "expenses": 40000,
        "savings": 30000,
        "risk_appetite": "medium",
        "financial_goals": "house",
    }
    data.update(overrides)
    return data


def test_health_score_bands():
    excellent = calculate_health_score(_profile(savings=30000))
    good = calculate_health_score(_profile(savings=20000))
    fair = calculate_health_score(_profile(savings=10000))
    none = calculate_health_score(_profile(savings=0, expenses=40000))

    assert excellent["pillar_scores"]["savings_rate"] == 25
    assert good["pillar_scores"]["savings_rate"] == 20
    assert fair["pillar_scores"]["savings_rate"] == 14
    assert none["pillar_scores"]["savings_rate"] == 0
    assert 0 <= excellent["score"] <= 100

    six_months = calculate_health_score(_profile(savings=60000, expenses=10000))
    three_months = calculate_health_score(_profile(savings=30000, expenses=10000))
    assert six_months["pillar_scores"]["emergency_fund"] == 20
    assert three_months["pillar_scores"]["emergency_fund"] == 13

    healthy_debt = calculate_health_score(_profile(debt_emi=20000))
    heavy_debt = calculate_health_score(_profile(debt_emi=60000))
    assert healthy_debt["pillar_scores"]["debt_ratio"] == 15
    assert heavy_debt["pillar_scores"]["debt_ratio"] == 0


def test_goal_feasibility_bands():
    assert _feasibility_label(75) == "High Feasibility"
    assert _feasibility_label(74) == "Moderate Feasibility"
    assert _feasibility_label(50) == "Moderate Feasibility"
    assert _feasibility_label(49) == "Low Feasibility"

    ok, easy = calculate_goal_plan(
        {"savings": 50000, "risk_appetite": "high"},
        {"goal_name": "Buffer", "target_amount": 100000, "time_years": 10},
    )
    assert ok is True
    assert easy["feasible"] is True
    assert easy["feasibility_label"] == "High Feasibility"

    ok, hard = calculate_goal_plan(
        {"savings": 100, "risk_appetite": "low"},
        {"goal_name": "Villa", "target_amount": 50_000_000, "time_years": 1},
    )
    assert ok is True
    assert hard["feasible"] is False
    assert hard["feasibility_label"] == "Low Feasibility"


def test_legacy_blob_is_copied_to_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "legacy.db"))
    monkeypatch.setattr(Config, "PDF_STORAGE_DIR", str(tmp_path / "pdfs"))
    create_tables()

    conn = db_mod.get_connection()
    conn.execute(
        "INSERT INTO users (age, income, expenses, savings, risk_appetite, financial_goals) "
        "VALUES (30, 1, 1, 1, 'low', 'house')"
    )
    conn.execute(
        "INSERT INTO reports (user_id, health_json, ai_report, pdf_blob) VALUES (1, '{}', 'text', ?)",
        (b"%PDF-legacy",),
    )
    conn.commit()
    conn.close()

    create_tables()

    conn = db_mod.get_connection()
    row = conn.execute("SELECT pdf_path, pdf_blob FROM reports WHERE user_id = 1").fetchone()
    conn.close()
    assert row["pdf_blob"] is None
    assert row["pdf_path"] == file_name_for(1)
    stored = tmp_path / "pdfs" / file_name_for(1)
    assert stored.read_bytes() == b"%PDF-legacy"


def test_one_connection_per_request(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "conn.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    headers = {
        "X-API-Key": config.Config.API_SECRET_KEY,
        "Content-Type": "application/json",
    }
    created = client.post(
        "/api/profile",
        data=json.dumps(_profile()),
        headers=headers,
    )
    user_id = created.get_json()["user_id"]

    opened = {"n": 0}
    real_open = db_mod.open_connection

    def _counting():
        opened["n"] += 1
        return real_open()

    monkeypatch.setattr(db_mod, "open_connection", _counting)
    res = client.get(f"/api/chat/history/{user_id}", headers=headers)
    assert res.status_code == 200
    assert opened["n"] == 1


def test_profile_save_failure_is_structured(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "err.db"))
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True

    import routes.user_routes as ur
    from database.db import DatabaseError

    def _boom(_data):
        raise DatabaseError("database is locked")

    monkeypatch.setattr(ur, "insert_user", _boom)
    client = app.test_client()
    res = client.post(
        "/api/profile",
        data=json.dumps(_profile()),
        headers={
            "X-API-Key": config.Config.API_SECRET_KEY,
            "Content-Type": "application/json",
        },
    )
    assert res.status_code == 500
    assert res.get_json()["code"] == "server_error"


def test_download_reads_pdf_file(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_NAME", str(tmp_path / "pdf.db"))
    monkeypatch.setattr(Config, "PDF_STORAGE_DIR", str(tmp_path / "pdfs"))
    monkeypatch.setattr(config.Config, "PDF_STORAGE_DIR", str(tmp_path / "pdfs"))
    monkeypatch.setattr(config.Config, "RATELIMIT_STORAGE_BACKEND", "memory")
    gw_mod._gateway = None
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    headers = {
        "X-API-Key": config.Config.API_SECRET_KEY,
        "Content-Type": "application/json",
    }
    created = client.post("/api/profile", data=json.dumps(_profile()), headers=headers)
    user_id = created.get_json()["user_id"]

    import routes.report_routes as rr

    monkeypatch.setattr(rr, "generate_financial_report", lambda p, h: (True, "advisory"))

    def _ok_pdf(profile, health, ai_report, filename=None):
        with open(filename, "wb") as fh:
            fh.write(b"%PDF-1.4 on-disk")
        return True, filename

    monkeypatch.setattr(rr, "generate_pdf_report", _ok_pdf)
    generated = client.post(
        "/api/generate-report",
        data=json.dumps({"user_id": user_id}),
        headers=headers,
    )
    assert generated.status_code == 200
    assert generated.get_json()["pdf_ready"] is True

    conn = db_mod.get_connection()
    row = conn.execute(
        "SELECT pdf_path, pdf_blob FROM reports WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    assert row["pdf_blob"] is None
    assert row["pdf_path"] == file_name_for(user_id)

    downloaded = client.get(f"/api/download-report/{user_id}", headers=headers)
    assert downloaded.status_code == 200
    assert downloaded.data == b"%PDF-1.4 on-disk"
