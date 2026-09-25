import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from schemas import profile_schema
from database.db import get_connection

logger  = logging.getLogger(__name__)
user_bp = Blueprint("user", __name__)


# ── DB helpers (imported by other route modules) ───────────────────────────

def get_latest_user():
    """Return the most recently created user as a plain dict, or None."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1")
    user   = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id: int):
    """Return a specific user as a plain dict, or None."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user   = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def get_all_users():
    """Return all users ordered by id ascending."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id ASC")
    rows   = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Routes ─────────────────────────────────────────────────────────────────

@user_bp.route("/users", methods=["GET"])
def list_users():
    """
    List all saved user profiles.
    ---
    tags:
      - User
    responses:
      200:
        description: List of user profiles
    """
    users = get_all_users()
    return jsonify({"users": users})


@user_bp.route("/profile", methods=["POST"])
def create_profile():
    """
    Create User Profile
    ---
    tags:
      - User
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            age:
              type: integer
              example: 23
            income:
              type: number
              example: 40000
            expenses:
              type: number
              example: 25000
            savings:
              type: number
              example: 15000
            risk_appetite:
              type: string
              example: medium
            financial_goals:
              type: string
              example: Buy a car in 2 years
            debt_emi:
              type: number
              example: 5000
              description: Optional — total monthly EMI payments
    responses:
      201:
        description: Profile created successfully
      400:
        description: Validation error
      500:
        description: Database error
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    # ── Validate & deserialise ─────────────────────────────────────────────
    try:
        data = profile_schema.load(raw)
    except ValidationError as exc:
        logger.warning("create_profile: validation failed — %s", exc.messages)
        return jsonify({"error": "Validation failed", "details": exc.messages}), 400

    if data["income"] > 0 and data["expenses"] > data["income"]:
        logger.warning(
            "create_profile: expenses (%.0f) exceed income (%.0f)",
            data["expenses"], data["income"],
        )

    # ── Persist ───────────────────────────────────────────────────────────
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users
                (age, income, expenses, savings, risk_appetite, financial_goals)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["age"],
                data["income"],
                data["expenses"],
                data["savings"],
                data["risk_appetite"],
                data["financial_goals"],
            ),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
    except Exception:
        logger.exception("create_profile: DB insert failed")
        return jsonify({"error": "Database error — profile could not be saved"}), 500

    logger.info("create_profile: new profile #%d created", user_id)
    return jsonify({
        "message": "Profile saved successfully",
        "user_id": user_id,
        "profile": data,
    }), 201


@user_bp.route("/profile/<int:user_id>", methods=["DELETE"])
def delete_profile(user_id: int):
    """
    Delete a user profile and their associated report.
    ---
    tags:
      - User
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Profile deleted successfully
      404:
        description: Profile not found
      500:
        description: Deletion failed
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Profile not found"}), 404

    try:
        cursor.execute("DELETE FROM reports      WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users        WHERE id      = ?", (user_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        logger.exception("delete_profile: DB delete failed for user #%d", user_id)
        return jsonify({"error": "Deletion failed — database error"}), 500

    conn.close()
    logger.info("delete_profile: profile #%d deleted", user_id)
    return jsonify({
        "message":          f"Profile #{user_id} deleted successfully",
        "deleted_user_id":  user_id,
    })