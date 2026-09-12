"""
The one place that decides which AI provider is actually running.

Everything else in the app calls get_provider().generate(prompt) and never
imports a specific provider directly - so switching providers is a single
line in backend/.env (LLM_PROVIDER), never a code change.
"""

import os

from .anthropic_provider import AnthropicProvider
from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .openai_provider import OpenAIProvider

_PROVIDERS = {
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "groq": GroqProvider,
}


def get_provider() -> LLMProvider:
    name = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    provider_class = _PROVIDERS.get(name)
    if provider_class is None:
        raise RuntimeError(
            f"Unknown LLM_PROVIDER '{name}' in backend/.env. "
            f"Choose one of: {', '.join(_PROVIDERS)}"
        )
    return provider_class()
