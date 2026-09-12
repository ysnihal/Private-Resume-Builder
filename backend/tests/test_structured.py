"""
Tests for backend/structured.py's retry-then-fail-cleanly logic - using a
FAKE model function, not a real AI call. This is what proves the retry
behavior works without needing an API key or spending real money.
"""

import pytest
from pydantic import BaseModel

from backend.structured import generate_structured


class Bullets(BaseModel):
    bullets: list[str]


def test_succeeds_on_first_try():
    def call_model(prompt: str) -> str:
        return '{"bullets": ["First try worked"]}'

    result = generate_structured("prompt", Bullets, call_model)
    assert result.bullets == ["First try worked"]


def test_recovers_after_one_bad_response():
    calls = {"count": 0}

    def flaky_call_model(prompt: str) -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            return "this is not json at all"
        return '{"bullets": ["Recovered on retry"]}'

    result = generate_structured("prompt", Bullets, flaky_call_model)
    assert calls["count"] == 2, "expected exactly one retry"
    assert result.bullets == ["Recovered on retry"]


def test_fails_cleanly_after_two_bad_responses():
    def always_broken(prompt: str) -> str:
        return "still not json"

    with pytest.raises(ValueError, match="did not return valid JSON"):
        generate_structured("prompt", Bullets, always_broken)
