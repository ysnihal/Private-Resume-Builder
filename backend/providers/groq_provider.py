import os

from groq import Groq
from pydantic import BaseModel

from .base import LLMProvider


class GroqProvider(LLMProvider):
    """Groq - hosts fast, cheap open-weight models. Uses an OpenAI-style
    chat API under the hood, via the official groq SDK."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> str:
        if schema is not None:
            raise NotImplementedError(
                "Structured JSON output isn't implemented for Groq yet - only Gemini supports it so far."
            )
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is empty in backend/.env.")
        client = Groq(api_key=self.api_key)
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        return completion.choices[0].message.content
