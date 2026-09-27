"""Report worker. Claim one queued job, run Groq, save text, then the PDF.

Run as its own process:

    python -m services.jobs.worker

When GROQ_STUB is on, GROQ_STUB_HOLD_SECONDS keeps the claimed job in
``running`` before the stub returns. The web process does not wait. Tests
leave the hold at 0.
"""
import logging
import os
import time

from config import Config
from database.db import DatabaseError
from database.repository import (
    claim_next_report_job,
    fail_stale_report_jobs,
    finish_report_job,
    get_report_job,
    get_user_for_owner,
)

logger = logging.getLogger(__name__)

_IDLE_SECONDS = 0.5


def process_once():
    """Finish at most one report job. Returns the job row, or None when idle."""
    fail_stale_report_jobs(Config.WORKER_TIMEOUT_SECONDS)
    job = claim_next_report_job()
    if job is None:
        return None
    try:
        if job.get("kind") == "chat":
            _run_chat(job)
        else:
            _run_report(job)
    except Exception:
        logger.exception("report job %s failed before it could record a result", job["id"])
        finish_report_job(job["id"], "failed", "server_error", "worker")
    return get_report_job(job["id"])


def _hold_for_stub(job_id: int) -> None:
    """Pause a stubbed job while its row stays ``running``. Live Groq does not pause here."""
    if not Config.GROQ_STUB:
        return
    raw = os.getenv("GROQ_STUB_HOLD_SECONDS", "")
    try:
        seconds = float(raw) if str(raw).strip() else 0.0
    except ValueError:
        seconds = 0.0
    if seconds <= 0:
        return
    seconds = min(seconds, 30.0)
    logger.info("report job %s stub hold %.1fs", job_id, seconds)
    time.sleep(seconds)


def _run_report(job: dict) -> None:
    import routes.report_routes as report_routes

    profile = get_user_for_owner(job["user_id"], job["account_id"])
    if not profile:
        finish_report_job(job["id"], "failed", "not_found", "owner_mismatch")
        logger.info("report job %s rejected: profile owner does not match", job["id"])
        return

    health = report_routes.calculate_health_score(profile)
    _hold_for_stub(job["id"])
    ok, ai_report = report_routes.generate_financial_report(profile, health)
    if not ok:
        code = "upstream_error"
        if isinstance(ai_report, dict) and ai_report.get("code"):
            code = str(ai_report["code"])[:80]
        finish_report_job(job["id"], "failed", code, "generate_financial_report")
        logger.info("report job %s failed in generation code=%s", job["id"], code)
        return

    try:
        report_routes._save_report_to_db(profile["id"], health, ai_report, pdf_bytes=None)
    except DatabaseError:
        logger.exception("report job %s could not save advisory text", job["id"])
        finish_report_job(job["id"], "failed", "server_error", "save_report")
        return

    pdf_ok, pdf_result = report_routes._build_pdf_bytes(profile, health, ai_report)
    if pdf_ok:
        try:
            report_routes._update_pdf_blob(profile["id"], pdf_result)
        except (DatabaseError, OSError):
            logger.exception("report job %s saved text; PDF file was not stored", job["id"])
    else:
        logger.error("report job %s saved text; PDF build failed", job["id"])

    finish_report_job(job["id"], "succeeded")
    logger.info("report job %s succeeded for profile %s", job["id"], profile["id"])


def _run_chat(job: dict) -> None:
    import routes.chat_routes as chat_routes

    profile = get_user_for_owner(job["user_id"], job["account_id"])
    if not profile:
        finish_report_job(job["id"], "failed", "not_found", "owner_mismatch")
        logger.info("chat job %s rejected: profile owner does not match", job["id"])
        return

    query = (job.get("payload") or "").strip()
    if not query:
        finish_report_job(job["id"], "failed", "invalid", "empty_query")
        return

    _hold_for_stub(job["id"])
    history = chat_routes.load_chat_history(profile["id"], limit=20)
    ok, response_text = chat_routes.chat_with_advisor(profile, query, history)
    if not ok:
        code = "upstream_error"
        if isinstance(response_text, dict) and response_text.get("code"):
            code = str(response_text["code"])[:80]
        finish_report_job(job["id"], "failed", code, "chat_with_advisor")
        logger.info("chat job %s failed code=%s", job["id"], code)
        return

    try:
        chat_routes.save_chat_turn(profile["id"], query, response_text)
    except DatabaseError:
        logger.exception("chat job %s could not save the turn", job["id"])
        finish_report_job(job["id"], "failed", "server_error", "save_chat")
        return

    finish_report_job(job["id"], "succeeded")
    logger.info("chat job %s succeeded for profile %s", job["id"], profile["id"])


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    )
    from database.models import create_tables

    create_tables()
    logger.info("Report worker watching the jobs table")
    while True:
        job = process_once()
        if job is None:
            time.sleep(_IDLE_SECONDS)


if __name__ == "__main__":
    main()
