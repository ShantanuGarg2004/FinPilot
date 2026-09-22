import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from extensions import limiter
from schemas import chat_schema
from services.ai_service import chat_with_advisor
from routes.user_routes import get_user_by_id
from database.db import get_connection
import config as app_config

logger  = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


# ── DB helpers ─────────────────────────────────────────────────────────────

def _load_history(user_id: int, limit: int = 20) -> list:
    """Return the most recent `limit` messages for user_id, oldest first."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT role, message FROM chat_history
        WHERE user_id = ?
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r["role"], "message": r["message"]} for r in reversed(rows)]


def _save_message(user_id: int, role: str, message: str) -> None:
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
        (user_id, role, message),
    )
    conn.commit()
    conn.close()


def _clear_history(user_id: int) -> None:
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ── Routes ─────────────────────────────────────────────────────────────────

@chat_bp.route("/chat", methods=["POST"])
@limiter.limit(lambda: app_config.Config.RATELIMIT_LLM_CHAT)
def chat():
    """
    Chat with AI Financial Advisor
    ---
    tags:
      - Chat
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - query
          properties:
            user_id:
              type: integer
              example: 1
            query:
              type: string
              example: Where should I invest ₹5,000/month?
    responses:
      200:
        description: AI response
      400:
        description: Validation error
      404:
        description: User profile not found
      500:
        description: AI service error
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    try:
        data = chat_schema.load(raw)
    except ValidationError as exc:
        logger.warning("chat: validation failed — %s", exc.messages)
        return jsonify({"error": "Validation failed", "details": exc.messages}), 400

    user_id    = data["user_id"]
    user_query = data["query"]

    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({"error": f"User profile #{user_id} not found"}), 404

    history = _load_history(user_id, limit=20)

    try:
        _save_message(user_id, "user", user_query)
    except Exception:
        logger.exception("chat: failed to persist user message for user #%d", user_id)

    status, response_text = chat_with_advisor(profile, user_query, history)
    if not status:
        logger.error("chat: AI error for user #%d — %s", user_id, response_text)
        return jsonify({"error": response_text}), 500

    try:
        _save_message(user_id, "ai", response_text)
    except Exception:
        logger.exception("chat: failed to persist AI response for user #%d", user_id)

    logger.info("chat: response delivered for user #%d (%d chars)", user_id, len(response_text))
    return jsonify({
        "query":    user_query,
        "response": response_text,
    })


@chat_bp.route("/chat/history/<int:user_id>", methods=["GET"])
@limiter.limit(lambda: app_config.Config.RATELIMIT_READ)
def get_chat_history(user_id: int):
    """
    Fetch stored chat history for a user.
    ---
    tags:
      - Chat
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: List of chat messages
      404:
        description: User not found
    """
    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({"error": f"User profile #{user_id} not found"}), 404

    history = _load_history(user_id, limit=100)
    logger.debug("get_chat_history: %d messages returned for user #%d", len(history), user_id)
    return jsonify({"user_id": user_id, "history": history})


@chat_bp.route("/chat/history/<int:user_id>", methods=["DELETE"])
@limiter.limit(lambda: app_config.Config.RATELIMIT_WRITE_PROFILE)
def clear_chat_history(user_id: int):
    """
    Clear all chat history for a user.
    ---
    tags:
      - Chat
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: History cleared
      404:
        description: User not found
    """
    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({"error": f"User profile #{user_id} not found"}), 404

    try:
        _clear_history(user_id)
        logger.info("clear_chat_history: history cleared for user #%d", user_id)
    except Exception:
        logger.exception("clear_chat_history: DB delete failed for user #%d", user_id)
        return jsonify({"error": "Could not clear history — database error"}), 500

    return jsonify({"message": f"Chat history for user #{user_id} cleared."})