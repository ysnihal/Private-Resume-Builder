import os

from openai import OpenAI
from pydantic import BaseModel

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI, via the official openai SDK's Responses API."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-6-astra")

    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> str:
        if schema is not None:
            raise NotImplementedError(
                "Structured JSON output isn't implemented for OpenAI yet - only Gemini supports it so far."
            )
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is empty in backend/.env.")
        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(model=self.model, input=prompt)
        return response.output_text
