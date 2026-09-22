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
from config import Config

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

    # Attach rate limiter (OPTIONS exempt via extensions.request_filter)
    limiter.init_app(app)

    # Init DB
    create_tables()

    # ── API key auth middleware ────────────────────────────────────────────
    @app.before_request
    def require_api_key():
        if request.method == "OPTIONS":
            return
        open_paths = ("/apidocs/", "/apispec.json", "/flasgger_static")
        if request.path == "/" or request.path.rstrip("/") == "/api/health":
            return
        if any(request.path.startswith(p) for p in open_paths):
            return
        if not request.path.startswith("/api"):
            return

        client_key = request.headers.get("X-API-Key", "")
        if client_key != Config.API_SECRET_KEY:
            logger.warning("Rejected request — bad API key from %s", request.remote_addr)
            return jsonify({
                "error": "Unauthorised — invalid or missing X-API-Key header",
                "code": "unauthorized",
            }), 401

    # ── Wave 0.9: structured 429 JSON for the SPA ─────────────────────────
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(exc: RateLimitExceeded):
        retry_after = None
        try:
            # Flask-Limiter may attach Retry-After via the HTTPException headers.
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
    Swagger(app, config=swagger_config)

    @app.route("/")
    def home():
        return "AI Financial Advisor Backend Running 🚀"

    @app.route("/api/health")
    def health():
        """Liveness probe — exempt from API-key auth and rate limits."""
        return jsonify({
            "status": "ok",
            "ratelimit_enabled": Config.RATELIMIT_ENABLED,
            "ratelimit_storage": Config.RATELIMIT_STORAGE_URI.split("://", 1)[0],
        })

    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(report_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(goal_bp, url_prefix="/api")

    logger.info(
        "App ready — rate limiting enabled=%s storage=%s",
        Config.RATELIMIT_ENABLED,
        Config.RATELIMIT_STORAGE_URI,
    )
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
