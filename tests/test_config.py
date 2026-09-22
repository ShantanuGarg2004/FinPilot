"""Unit tests for config.Config after the Groq migration."""
import importlib

import pytest

import config


def test_required_keys_present_by_default():
    assert config.Config.GROQ_API_KEY
    assert config.Config.API_SECRET_KEY


def test_validate_passes_when_keys_present():
    # validate() returns None (does not raise) when required keys are set.
    assert config.Config.validate() is None


def test_validate_raises_when_groq_key_missing(monkeypatch):
    monkeypatch.setattr(config.Config, "GROQ_API_KEY", None)
    with pytest.raises(EnvironmentError) as excinfo:
        config.Config.validate()
    assert "GROQ_API_KEY" in str(excinfo.value)


def test_validate_raises_when_api_secret_missing(monkeypatch):
    monkeypatch.setattr(config.Config, "API_SECRET_KEY", None)
    with pytest.raises(EnvironmentError) as excinfo:
        config.Config.validate()
    assert "API_SECRET_KEY" in str(excinfo.value)


def test_validate_no_longer_requires_openai_key(monkeypatch):
    # OpenAI is fully removed: the attribute should not exist, and validate()
    # must not depend on it.
    assert not hasattr(config.Config, "OPENAI_API_KEY")
    assert config.Config.validate() is None


def test_per_service_models_configured():
    assert config.Config.GROQ_REPORT_MODEL == "openai/gpt-oss-120b"
    assert config.Config.GROQ_CHAT_MODEL == "openai/gpt-oss-20b"


def test_token_budgets_split_for_report_and_chat():
    assert config.Config.GROQ_REPORT_MAX_TOKENS >= 3500
    assert config.Config.GROQ_CHAT_MAX_TOKENS >= 1200
    assert config.Config.GROQ_REPORT_MAX_TOKENS > config.Config.GROQ_CHAT_MAX_TOKENS


def test_ratelimit_defaults_have_no_global_hour_on_config():
    # Wave 0: quotas are per-route strings; storage defaults to memory://
    assert config.Config.RATELIMIT_STORAGE_URI.startswith("memory")
    assert "per minute" in config.Config.RATELIMIT_READ
    assert "per minute" in config.Config.RATELIMIT_LLM_REPORT


def test_model_defaults_fall_back_when_env_absent(monkeypatch):
    """When the model env vars are unset, code defaults must apply."""
    import dotenv

    # Neutralise .env loading and remove the overrides so the code defaults win.
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("GROQ_REPORT_MODEL", raising=False)
    monkeypatch.delenv("GROQ_CHAT_MODEL", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("API_SECRET_KEY", "test-api-secret")

    reloaded = importlib.reload(config)
    try:
        assert reloaded.Config.GROQ_REPORT_MODEL == "openai/gpt-oss-120b"
        assert reloaded.Config.GROQ_CHAT_MODEL == "openai/gpt-oss-20b"
    finally:
        # Restore env + module state for any subsequent tests.
        monkeypatch.undo()
        importlib.reload(config)
