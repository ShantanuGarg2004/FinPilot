import logging
import sqlite3

from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from schemas import chat_schema
from services.ai_service import chat_with_advisor, http_status_for_ai_code
from database.repository import clear_chat_history, get_user_by_id, load_chat_history, save_chat_turn

logger  = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


# ── Routes ─────────────────────────────────────────────────────────────────

@chat_bp.route("/chat", methods=["POST"])
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

    history = load_chat_history(user_id, limit=20)

    status, response_text = chat_with_advisor(profile, user_query, history)
    if not status:
        logger.error("chat: AI error for user #%d — %s", user_id, response_text)
        if isinstance(response_text, dict):
            code = response_text.get("code") or "upstream_error"
            body = {
                "error": response_text.get("error") or "AI chat failed",
                "code": code,
            }
            return jsonify(body), http_status_for_ai_code(code)
        return jsonify({"error": str(response_text), "code": "upstream_error"}), 503

    try:
        save_chat_turn(user_id, user_query, response_text)
    except sqlite3.Error:
        logger.exception("chat: failed to persist turn for user #%d", user_id)
        return jsonify({
            "error": "The reply was generated but could not be saved",
            "code": "server_error",
        }), 500

    logger.info("chat: response delivered for user #%d (%d chars)", user_id, len(response_text))
    return jsonify({
        "query":    user_query,
        "response": response_text,
    })


@chat_bp.route("/chat/history/<int:user_id>", methods=["GET"])
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

    history = load_chat_history(user_id, limit=100)
    logger.debug("get_chat_history: %d messages returned for user #%d", len(history), user_id)
    return jsonify({"user_id": user_id, "history": history})


@chat_bp.route("/chat/history/<int:user_id>", methods=["DELETE"])
def clear_chat_history_route(user_id: int):
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
        clear_chat_history(user_id)
        logger.info("clear_chat_history: history cleared for user #%d", user_id)
    except sqlite3.Error:
        logger.exception("clear_chat_history: DB delete failed for user #%d", user_id)
        return jsonify({
            "error": "Could not clear history — database error",
            "code": "server_error",
        }), 500

    return jsonify({"message": f"Chat history for user #{user_id} cleared."})
