"""
The shared shape every AI provider must follow.

Whatever provider is picked in backend/.env (LLM_PROVIDER), the rest of the
app only ever calls `.generate(prompt)` on it and gets a plain string back.
The rest of the app never needs to know or care which company's API is
actually running underneath.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> str | BaseModel:
        """Send `prompt` to the AI and return its reply.

        If `schema` is None (the default), returns plain text - same as
        before Step 4.

        If `schema` is a Pydantic model class (see backend/schemas.py),
        the AI is constrained to return JSON matching that shape, and this
        returns an already-validated instance of `schema` - never a raw
        string. Only GeminiProvider implements this so far; the other
        three raise NotImplementedError if you pass a schema to them.

        Note: this changed from Step 2's placeholder (`schema: dict`) now
        that Step 4 actually needed it - a real Pydantic class is what
        validation requires, a plain dict wasn't enough.
        """
        raise NotImplementedError
