import logging
from database.db import DatabaseError

from flask import Blueprint, g, jsonify, request
from marshmallow import ValidationError

from schemas import chat_schema
from services.ai_service import chat_with_advisor
from database.repository import (
    clear_chat_history,
    enqueue_chat_job,
    get_user_by_id,
    latest_chat_job,
    load_chat_history,
    save_chat_turn,
)

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
      202:
        description: Chat job queued. A worker writes the reply.
      400:
        description: Validation error
      404:
        description: User profile not found
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    try:
        data = chat_schema.load(raw)
    except ValidationError as exc:
        logger.warning("chat: validation failed — %s", exc.messages)
        return jsonify({"error": "Validation failed", "details": exc.messages}), 400

    user_id = data["user_id"]
    user_query = data["query"]

    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({"error": f"User profile #{user_id} not found"}), 404

    actor = getattr(g, "actor", None)
    if actor is not None and actor.kind in ("user", "api_key"):
        account_id = int(actor.credential)
    else:
        account_id = profile.get("account_id")

    job = enqueue_chat_job(user_id, account_id, user_query)
    logger.info("chat: job %s queued for user #%s", job["job_id"], user_id)
    return jsonify({"query": user_query, **job}), 202


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
    body = {"user_id": user_id, "history": history}
    job = latest_chat_job(user_id)
    if job:
        body["job"] = job
    logger.debug("get_chat_history: %d messages returned for user #%d", len(history), user_id)
    return jsonify(body)


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
    except DatabaseError:
        logger.exception("clear_chat_history: DB delete failed for user #%d", user_id)
        return jsonify({
            "error": "Could not clear history — database error",
            "code": "server_error",
        }), 500

    return jsonify({"message": f"Chat history for user #{user_id} cleared."})
