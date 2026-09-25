import logging
import sqlite3

from flask import Blueprint, g, jsonify, request
from marshmallow import ValidationError
from werkzeug.security import check_password_hash

from database.repository import get_account_by_email, insert_account
from schemas import login_schema, passwords_match, signup_schema
from services.sessions import attach_cookie, clear_cookie

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def _account_body(account: dict):
    return {"account_id": account["id"], "email": account["email"]}


@auth_bp.route("/auth/signup", methods=["POST"])
def signup():
    """
    Create an account and set the session cookie.
    ---
    tags:
      - Auth
    security: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - confirm_password
          properties:
            email:
              type: string
              example: person@example.com
            password:
              type: string
              example: correct-horse
            confirm_password:
              type: string
              example: correct-horse
    responses:
      201:
        description: Account created. finpilot_session cookie is set.
      400:
        description: Validation error
      409:
        description: Email already registered
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    try:
        data = signup_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.messages}), 400
    if not passwords_match(data):
        return jsonify({
            "error": "Validation failed",
            "details": {"confirm_password": ["confirm password must match password"]},
        }), 400
    if get_account_by_email(data["email"]):
        return jsonify({
            "error": "An account with this email already exists",
            "code": "account_exists",
        }), 409
    try:
        account = insert_account(data["email"], data["password"])
    except sqlite3.IntegrityError:
        return jsonify({
            "error": "An account with this email already exists",
            "code": "account_exists",
        }), 409
    resp = jsonify(_account_body(account))
    resp.status_code = 201
    return attach_cookie(resp, account["id"], account["session_version"])


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Sign in and set the session cookie.
    ---
    tags:
      - Auth
    security: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: bootstrap@finpilot.local
            password:
              type: string
              example: finpilot-bootstrap-local
    responses:
      200:
        description: Signed in. finpilot_session cookie is set.
      401:
        description: Email or password is incorrect
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    try:
        data = login_schema.load(raw)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.messages}), 400
    account = get_account_by_email(data["email"])
    if not account or not account.get("password_hash"):
        return jsonify({
            "error": "Email or password is incorrect.",
            "code": "invalid_credentials",
        }), 401
    if not check_password_hash(account["password_hash"], data["password"]):
        return jsonify({
            "error": "Email or password is incorrect.",
            "code": "invalid_credentials",
        }), 401
    resp = jsonify(_account_body(account))
    return attach_cookie(resp, account["id"], account["session_version"])


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """
    Clear the session cookie.
    ---
    tags:
      - Auth
    security: []
    responses:
      200:
        description: Signed out
    """
    resp = jsonify({"message": "Signed out"})
    return clear_cookie(resp)


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    """
    Return the signed-in account. Requires the finpilot_session cookie from login.
    ---
    tags:
      - Auth
    security: []
    responses:
      200:
        description: Current account
      401:
        description: Session missing or expired
    """
    actor = getattr(g, "actor", None)
    if actor is None or actor.kind != "user":
        return jsonify({
            "error": "Your session ended. Sign in again.",
            "code": "session_expired",
        }), 401
    from database.repository import get_account_by_id
    account = get_account_by_id(int(actor.credential))
    if not account:
        return jsonify({
            "error": "Your session ended. Sign in again.",
            "code": "session_expired",
        }), 401
    return jsonify(_account_body(account))
