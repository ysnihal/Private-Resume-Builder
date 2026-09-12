import os

import anthropic
from pydantic import BaseModel

from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Claude, via the official anthropic SDK."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")

    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> str:
        if schema is not None:
            raise NotImplementedError(
                "Structured JSON output isn't implemented for Anthropic yet - only Gemini supports it so far."
            )
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is empty in backend/.env.")
        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        # response.content is a list of content blocks (text, thinking, ...);
        # find the first text block rather than assuming content[0] is text.
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""
