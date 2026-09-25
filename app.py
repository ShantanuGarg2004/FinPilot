import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter.errors import RateLimitExceeded
from flasgger import Swagger

from extensions import limiter
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from routes.chat_routes import chat_bp
from routes.goal_routes import goal_bp
from database.models import create_tables
from config import Config, recommended_worker_count
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
    CORS(app, resources={r"/api/*": {"origins": "*"}})

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

    def _presented_api_key() -> str:
        header = request.headers.get("X-API-Key", "") or ""
        if header:
            return header
        # Browser login prompt for Swagger. Username is ignored; password is the API key.
        auth = request.authorization
        if auth and auth.password:
            return auth.password
        return ""

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

    # ── Auth then rate-limit ───────────────────────────────────────────────
    @app.before_request
    def require_api_key():
        if request.method == "OPTIONS":
            return
        if request.path == "/" or request.path.rstrip("/") == "/api/health":
            return
        if is_public_docs(request.path):
            if _presented_api_key() != Config.API_SECRET_KEY:
                return _unauthorized(challenge_docs=True)
            return
        if not is_application_api(request.path):
            return

        if _presented_api_key() != Config.API_SECRET_KEY:
            return _unauthorized()

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
    Swagger(app, config=swagger_config, template=swagger_template)

    @app.route("/")
    def home():
        return "AI Financial Advisor Backend Running 🚀"

    @app.route("/api/health")
    def health():
        """Liveness probe — exempt from API-key auth and rate limits."""
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
