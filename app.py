import logging
from flask import Flask, g, request, jsonify
from flask_cors import CORS
from flask_limiter.errors import RateLimitExceeded
from flasgger import Swagger

from extensions import limiter
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from routes.chat_routes import chat_bp
from routes.goal_routes import goal_bp
from routes.auth_routes import auth_bp
from database.models import create_tables
from database.db import close_request_connection
from config import Config, recommended_worker_count
from services.actor import Actor, resolve_actor
from services.rate_limit import build_gateway
from services.rate_limit.gateway import get_gateway, is_application_api, is_public_docs, uses_custom_gateway

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    Config.validate()

    app = Flask(__name__)
    CORS(
        app,
        resources={r"/api/*": {"origins": Config.CORS_ORIGINS}},
        supports_credentials=True,
    )

    # Wave 1: custom gateway owns limits when backend is sql|memory.
    # Keep Flask-Limiter imported for route decorators but disable it to avoid double-counting.
    if uses_custom_gateway():
        limiter.enabled = False
        gateway = build_gateway()
        logger.info(
            "Wave 1 rate-limit gateway active (backend=%s, store_ping=%s)",
            Config.RATELIMIT_STORAGE_BACKEND,
            gateway.ping(),
        )
    else:
        limiter.enabled = Config.RATELIMIT_ENABLED
        logger.info("Flask-Limiter active (legacy backend=%s)", Config.RATELIMIT_STORAGE_BACKEND)

    limiter.init_app(app)

    # Init app DB (SQLite profiles/reports/chat)
    create_tables()
    app.teardown_appcontext(close_request_connection)

    def _local_env() -> bool:
        return Config.FLASK_ENV in ("development", "dev", "local")

    def _unauthorized(challenge_docs: bool = False):
        logger.warning("Rejected request — bad API key from %s", request.remote_addr)
        resp = jsonify({
            "error": "Unauthorised — invalid or missing X-API-Key header",
            "code": "unauthorized",
        })
        resp.status_code = 401
        if challenge_docs:
            resp.headers["WWW-Authenticate"] = 'Basic realm="FinPilot API docs"'
        return resp

    def _bind_actor():
        actor = resolve_actor(request)
        if actor is None:
            return None
        g.actor = actor
        return actor

    # ── Auth then rate-limit ───────────────────────────────────────────────
    @app.before_request
    def require_api_key():
        if request.method == "OPTIONS":
            g.actor = Actor(kind="anonymous")
            return
        if request.path == "/" or request.path.rstrip("/") == "/api/health":
            g.actor = Actor(kind="anonymous")
            return
        if request.method == "POST" and request.path.rstrip("/") in (
            "/api/auth/login",
            "/api/auth/signup",
            "/api/auth/logout",
        ):
            g.actor = Actor(kind="anonymous")
            return
        if is_public_docs(request.path):
            if not _local_env():
                return jsonify({"error": "Not found", "code": "not_found"}), 404
            if _bind_actor() is None:
                return _unauthorized(challenge_docs=True)
            return
        if not is_application_api(request.path):
            return

        if _bind_actor() is None:
            if getattr(g, "auth_error", None) == "unauthorized":
                return _unauthorized()
            return jsonify({
                "error": "Your session ended. Sign in again.",
                "code": "session_expired",
            }), 401

    @app.before_request
    def enforce_rate_limit():
        if request.method == "OPTIONS":
            return
        if is_public_docs(request.path) or not is_application_api(request.path):
            return
        if request.path.rstrip("/") == "/api/health":
            return
        gw = get_gateway()
        if not gw:
            return
        decision = gw.check(request)
        if decision is not None and not decision.allowed and not decision.exempt:
            return gw.denial_response(decision)

    # ── Legacy Flask-Limiter 429 shape (if ever re-enabled) ────────────────
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(exc: RateLimitExceeded):
        retry_after = None
        try:
            for item in exc.get_headers() or []:
                if str(item[0]).lower() == "retry-after":
                    retry_after = int(item[1])
                    break
        except Exception:
            retry_after = None

        body = {
            "error": "Rate limit exceeded",
            "code": "rate_limit_exceeded",
            "retry_after": retry_after,
            "limit": str(exc.description) if exc.description else None,
        }
        resp = jsonify(body)
        resp.status_code = 429
        if retry_after is not None:
            resp.headers["Retry-After"] = str(retry_after)
        return resp

    # ── Swagger ───────────────────────────────────────────────────────────
    swagger_config = {
        "headers": [],
        "specs": [{"endpoint": "apispec", "route": "/apispec.json",
                   "rule_filter": lambda rule: True,
                   "model_filter": lambda tag: True}],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }
    swagger_template = {
        "securityDefinitions": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header",
                "description": "Same value as API_SECRET_KEY",
            }
        },
        "security": [{"ApiKeyAuth": []}],
    }
    if Config.FLASK_ENV in ("development", "dev", "local"):
        Swagger(app, config=swagger_config, template=swagger_template)
    else:
        logger.info("Swagger disabled because FLASK_ENV=%s", Config.FLASK_ENV)

    @app.route("/")
    def home():
        return "AI Financial Advisor Backend Running 🚀"

    @app.route("/api/health")
    def health():
        """
        Liveness probe. No API key and no session.
        ---
        tags:
          - Health
        security: []
        responses:
          200:
            description: Process is up
          503:
            description: Rate-limit store is down
        """
        gw = get_gateway()
        store_ok = gw.ping() if gw else None
        status = "ok" if store_ok is not False else "degraded"
        return jsonify({
            "status": status,
            "ratelimit_enabled": Config.RATELIMIT_ENABLED,
            "ratelimit_backend": Config.RATELIMIT_STORAGE_BACKEND,
            "ratelimit_store_ok": store_ok,
            "ratelimit_storage": Config.RATELIMIT_STORAGE_URI.split("://", 1)[0],
            "groq_timeout_seconds": Config.GROQ_TIMEOUT_SECONDS,
            "worker_timeout_seconds": Config.WORKER_TIMEOUT_SECONDS,
            "recommended_workers": recommended_worker_count(),
            "sqlite_busy_timeout_ms": Config.SQLITE_BUSY_TIMEOUT_MS,
        }), (200 if status == "ok" else 503)

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(report_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(goal_bp, url_prefix="/api")

    logger.info(
        "App ready — ratelimit enabled=%s backend=%s flask_limiter=%s",
        Config.RATELIMIT_ENABLED,
        Config.RATELIMIT_STORAGE_BACKEND,
        limiter.enabled,
    )
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
