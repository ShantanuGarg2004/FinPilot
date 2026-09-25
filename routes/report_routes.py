import io
import json
import logging
import os
import tempfile

from flask import Blueprint, jsonify, send_file, request
from marshmallow import ValidationError

from schemas import generate_report_schema
from services.health_service import calculate_health_score
from services.ai_service import generate_financial_report, http_status_for_ai_code
from services.pdf_service import generate_pdf_report
from routes.user_routes import get_user_by_id
from database.db import get_connection
from services.rate_limit.gateway import get_gateway

logger = logging.getLogger(__name__)
report_bp = Blueprint("report", __name__)


# ── DB helpers ─────────────────────────────────────────────────────────────

def _save_report_to_db(
    user_id: int,
    health_data: dict,
    ai_report: str,
    pdf_bytes: bytes | None = None,
) -> None:
    """Persist health + AI text. pdf_bytes=None stores NULL until a PDF exists."""
    blob = pdf_bytes if pdf_bytes else None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reports (user_id, health_json, ai_report, pdf_blob, generated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            health_json  = excluded.health_json,
            ai_report    = excluded.ai_report,
            pdf_blob     = excluded.pdf_blob,
            generated_at = CURRENT_TIMESTAMP
        """,
        (user_id, json.dumps(health_data), ai_report, blob),
    )
    conn.commit()
    conn.close()


def _update_pdf_blob(user_id: int, pdf_bytes: bytes) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reports SET pdf_blob = ? WHERE user_id = ?",
        (pdf_bytes, user_id),
    )
    conn.commit()
    conn.close()


def _load_report_from_db(user_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT health_json, ai_report, pdf_blob FROM reports WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    blob = row["pdf_blob"]
    pdf_ready = bool(blob) and len(bytes(blob)) > 0
    return {
        "health": json.loads(row["health_json"]),
        "ai_report": row["ai_report"],
        "pdf_ready": pdf_ready,
    }


def _load_pdf_blob_from_db(user_id: int) -> bytes | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_blob FROM reports WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or row["pdf_blob"] is None:
        return None
    blob = bytes(row["pdf_blob"])
    return blob if blob else None


def _ai_failure_response(result):
    """Map ask_gpt / generate_financial_report failure payload to HTTP response."""
    if isinstance(result, dict):
        code = result.get("code") or "upstream_error"
        body = {
            "error": result.get("error") or "AI generation failed",
            "code": code,
        }
        return jsonify(body), http_status_for_ai_code(code)
    return jsonify({"error": str(result), "code": "upstream_error"}), 500


def _build_pdf_bytes(profile, health_data, ai_report) -> tuple[bool, bytes | str]:
    """Generate PDF to a temp file and return bytes. On failure: (False, error)."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        status, result = generate_pdf_report(
            profile, health_data, ai_report, filename=tmp_path
        )
        if not status:
            return False, result

        with open(tmp_path, "rb") as f:
            return True, f.read()
    except Exception as exc:
        logger.exception("PDF build failed")
        return False, str(exc)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                logger.warning("could not delete temp PDF %s", tmp_path)


# ── Routes ─────────────────────────────────────────────────────────────────

@report_bp.route("/report/<int:user_id>", methods=["GET"])
def get_stored_report(user_id: int):
    """
    Fetch a previously generated report.
    ---
    tags:
      - Report
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Stored report
      404:
        description: No report found
    """
    data = _load_report_from_db(user_id)
    if not data:
        return jsonify({"error": "No report found for this user", "code": "not_found"}), 404
    return jsonify(data)


@report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """
    Generate (or regenerate) a financial report.
    ---
    tags:
      - Report
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: integer
              example: 1
    responses:
      200:
        description: Report generated (pdf_ready may be false)
      400:
        description: Validation error or user not found
      500:
        description: Generation or storage error
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    try:
        data = generate_report_schema.load(raw)
    except ValidationError as exc:
        logger.warning("generate_report: validation failed — %s", exc.messages)
        return jsonify({"error": "Validation failed", "details": exc.messages}), 400

    user_id = data["user_id"]
    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({"error": f"User profile #{user_id} not found"}), 400

    # 1. Health score
    health_data = calculate_health_score(profile)
    logger.info(
        "generate_report: health score for user #%d = %d",
        user_id,
        health_data.get("score", 0),
    )

    # 2. AI report text
    status, ai_report = generate_financial_report(profile, health_data)
    if not status:
        logger.error("generate_report: AI generation failed for user #%d", user_id)
        return _ai_failure_response(ai_report)

    # 3. Persist AI + health BEFORE PDF so a PDF failure never discards advisory text
    try:
        _save_report_to_db(user_id, health_data, ai_report, pdf_bytes=None)
        logger.info("generate_report: advisory persisted (pre-PDF) for user #%d", user_id)
    except Exception:
        logger.exception("generate_report: DB save failed for user #%d", user_id)
        return jsonify({
            "error": "Report generated but could not be saved to DB",
            "code": "server_error",
        }), 500

    # 4. Best-effort PDF
    pdf_ready = False
    pdf_error = None
    ok, pdf_result = _build_pdf_bytes(profile, health_data, ai_report)
    if ok:
        try:
            _update_pdf_blob(user_id, pdf_result)
            pdf_ready = True
            logger.info("generate_report: PDF saved for user #%d", user_id)
        except Exception:
            logger.exception("generate_report: PDF blob update failed for user #%d", user_id)
            pdf_error = "PDF generated but could not be saved"
    else:
        pdf_error = str(pdf_result)
        logger.error(
            "generate_report: PDF soft-failed for user #%d — %s",
            user_id,
            pdf_error,
        )

    body = {
        "user_id": user_id,
        "health": health_data,
        "ai_report": ai_report,
        "pdf_ready": pdf_ready,
    }
    if pdf_error and not pdf_ready:
        body["pdf_error"] = pdf_error
    return jsonify(body)


@report_bp.route("/download-report/<int:user_id>", methods=["GET"])
def download_report(user_id: int):
    """
    Download the stored PDF. If the blob is missing, regenerate from saved text
    (no AI re-call).
    ---
    tags:
      - Report
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: PDF download
      404:
        description: No report found
    """
    pdf_bytes = _load_pdf_blob_from_db(user_id)
    if pdf_bytes:
        return send_file(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=f"financial_report_profile_{user_id}.pdf",
            mimetype="application/pdf",
        )

    # Rebuild is a separate, tighter bucket than GET /report (Q1.4).
    gw = get_gateway()
    if gw is not None:
        decision = gw.consume(request, gw.policies.pdf_rebuild)
        if decision is not None and not decision.allowed:
            return gw.denial_response(decision)

    stored = _load_report_from_db(user_id)
    if not stored:
        return jsonify({
            "error": "No report found. Generate one first.",
            "code": "not_found",
        }), 404

    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({
            "error": f"User profile #{user_id} not found",
            "code": "not_found",
        }), 404

    ok, pdf_result = _build_pdf_bytes(profile, stored["health"], stored["ai_report"])
    if not ok:
        logger.error("download_report: PDF regen failed for user #%d — %s", user_id, pdf_result)
        return jsonify({
            "error": "PDF is not available and could not be regenerated",
            "code": "pdf_unavailable",
            "details": str(pdf_result),
        }), 503

    try:
        _update_pdf_blob(user_id, pdf_result)
    except Exception:
        logger.exception("download_report: could not cache regenerated PDF for user #%d", user_id)

    return send_file(
        io.BytesIO(pdf_result),
        as_attachment=True,
        download_name=f"financial_report_profile_{user_id}.pdf",
        mimetype="application/pdf",
    )
