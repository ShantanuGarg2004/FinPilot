"""Unit tests for services.ai_service after the Groq migration.

All Groq network calls are mocked; no real API requests are made.
"""
from types import SimpleNamespace

import pytest

import services.ai_service as ai_service


SAMPLE_PROFILE = {
    "age": 30,
    "income": 90000,
    "expenses": 50000,
    "savings": 25000,
    "risk_appetite": "medium",
    "financial_goals": "Buy a house in 7 years",
}

SAMPLE_HEALTH = {
    "score": 72,
    "insights": ["Good savings rate"],
    "warnings": ["Build emergency fund"],
}


def _make_response(content, finish_reason="stop"):
    """Mimic the shape of a Groq chat.completions response."""
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ]
    )


class _Recorder:
    """Stand-in for client.chat.completions.create that records its kwargs."""

    def __init__(self, content="  advice  ", exc=None, finish_reason="stop"):
        self.kwargs = None
        self.calls = 0
        self._content = content
        self._exc = exc
        self._finish_reason = finish_reason

    def __call__(self, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        if self._exc is not None:
            raise self._exc
        return _make_response(self._content, self._finish_reason)


@pytest.fixture
def recorder(monkeypatch):
    rec = _Recorder()
    monkeypatch.setattr(ai_service.client.chat.completions, "create", rec)
    return rec


# ── ask_gpt ──────────────────────────────────────────────────────────────────

def test_ask_gpt_success_returns_stripped_content(recorder):
    ok, out = ai_service.ask_gpt("hello")
    assert ok is True
    assert out == "advice"  # surrounding whitespace stripped
    assert recorder.calls == 1


def test_ask_gpt_defaults_to_chat_model(recorder):
    ai_service.ask_gpt("hello")
    assert recorder.kwargs["model"] == ai_service.Config.GROQ_CHAT_MODEL


def test_ask_gpt_uses_explicit_model(recorder):
    ai_service.ask_gpt("hello", model="custom-model-x")
    assert recorder.kwargs["model"] == "custom-model-x"


def test_ask_gpt_sends_system_and_user_messages(recorder):
    ai_service.ask_gpt("my question")
    kwargs = recorder.kwargs
    msgs = kwargs["messages"]
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == ai_service.SYSTEM_PROMPT
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "my question"
    assert kwargs["temperature"] == 0.7
    assert kwargs["max_tokens"] == ai_service.Config.GROQ_CHAT_MAX_TOKENS


def test_ask_gpt_accepts_explicit_max_tokens(recorder):
    ai_service.ask_gpt("hello", max_tokens=321)
    assert recorder.kwargs["max_tokens"] == 321


def test_ask_gpt_logs_when_finish_reason_length(monkeypatch, caplog):
    rec = _Recorder(content="cut off mid", finish_reason="length")
    monkeypatch.setattr(ai_service.client.chat.completions, "create", rec)
    with caplog.at_level("WARNING"):
        ok, out = ai_service.ask_gpt("hello", max_tokens=10)
    assert ok is True
    assert out == "cut off mid"
    assert any("finish_reason=length" in r.message for r in caplog.records)


def test_ask_gpt_returns_false_on_exception(monkeypatch):
    rec = _Recorder(exc=RuntimeError("boom"))
    monkeypatch.setattr(ai_service.client.chat.completions, "create", rec)
    ok, out = ai_service.ask_gpt("hello")
    assert ok is False
    assert "boom" in out


# ── generate_financial_report ────────────────────────────────────────────────

def test_generate_financial_report_uses_report_model(recorder):
    ok, _ = ai_service.generate_financial_report(SAMPLE_PROFILE, SAMPLE_HEALTH)
    assert ok is True
    assert recorder.kwargs["model"] == ai_service.Config.GROQ_REPORT_MODEL
    assert recorder.kwargs["max_tokens"] == ai_service.Config.GROQ_REPORT_MAX_TOKENS


def test_generate_financial_report_prompt_contains_profile(recorder):
    ai_service.generate_financial_report(SAMPLE_PROFILE, SAMPLE_HEALTH)
    user_msg = recorder.kwargs["messages"][1]["content"]
    assert "Buy a house in 7 years" in user_msg
    assert "72/100" in user_msg


# ── chat_with_advisor ────────────────────────────────────────────────────────

def test_chat_with_advisor_uses_chat_model(recorder):
    ok, _ = ai_service.chat_with_advisor(SAMPLE_PROFILE, "Where to invest?")
    assert ok is True
    assert recorder.kwargs["model"] == ai_service.Config.GROQ_CHAT_MODEL
    assert recorder.kwargs["max_tokens"] == ai_service.Config.GROQ_CHAT_MAX_TOKENS


def test_chat_with_advisor_includes_query_in_prompt(recorder):
    ai_service.chat_with_advisor(SAMPLE_PROFILE, "Where to invest?")
    user_msg = recorder.kwargs["messages"][1]["content"]
    assert "Where to invest?" in user_msg


def test_chat_with_advisor_uses_message_key_from_history(recorder):
    history = [{"role": "user", "message": "prior question about SIPs"}]
    ai_service.chat_with_advisor(SAMPLE_PROFILE, "follow up", history=history)
    user_msg = recorder.kwargs["messages"][1]["content"]
    assert "prior question about SIPs" in user_msg


def test_report_and_chat_use_distinct_models(recorder):
    # Confirms the per-service wiring actually differentiates the two models.
    assert ai_service.Config.GROQ_REPORT_MODEL != ai_service.Config.GROQ_CHAT_MODEL
