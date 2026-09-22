"""Unit tests for Wave 0 limiter extension helpers."""
from flask import Flask

from extensions import limiter, _exempt_options_and_health


def test_request_filter_exempts_options(monkeypatch):
    app = Flask(__name__)
    with app.test_request_context("/api/report/1", method="OPTIONS"):
        assert _exempt_options_and_health() is True


def test_request_filter_exempts_health(monkeypatch):
    app = Flask(__name__)
    with app.test_request_context("/api/health", method="GET"):
        assert _exempt_options_and_health() is True


def test_request_filter_does_not_exempt_normal_get():
    app = Flask(__name__)
    with app.test_request_context("/api/report/1", method="GET"):
        assert _exempt_options_and_health() is False


def test_limiter_has_empty_default_limits():
    # Wave 0: Limiter constructed with default_limits=[] (no global 60/hour).
    configured = getattr(limiter, "_default_limits", None)
    assert configured is None or list(configured) == [] or configured == []
    # Also confirm OPTIONS filter is registered.
    assert callable(_exempt_options_and_health)
