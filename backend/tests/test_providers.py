"""
Tests for the provider factory (backend/providers/__init__.py) - checks
that LLM_PROVIDER picks the right class. Does not call any real AI:
constructing a provider just reads its API key from the environment, it
doesn't make a network request.
"""

from backend.providers import get_provider
from backend.providers.anthropic_provider import AnthropicProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.groq_provider import GroqProvider
from backend.providers.openai_provider import OpenAIProvider


def test_defaults_to_gemini_when_unset(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert isinstance(get_provider(), GeminiProvider)


def test_selects_provider_by_name(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    assert isinstance(get_provider(), AnthropicProvider)

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    assert isinstance(get_provider(), OpenAIProvider)

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    assert isinstance(get_provider(), GroqProvider)


def test_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "GEMINI")
    assert isinstance(get_provider(), GeminiProvider)


def test_unknown_provider_raises_clear_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "not-a-real-provider")
    try:
        get_provider()
        raise AssertionError("expected a RuntimeError")
    except RuntimeError as error:
        assert "not-a-real-provider" in str(error)
