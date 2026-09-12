import os
from collections.abc import Iterator

from google import genai
from google.genai import types
from pydantic import BaseModel

from ..errors import to_friendly_error
from ..structured import generate_structured
from ..usage_log import log_usage
from .base import LLMProvider

# How long to wait for Gemini before giving up on a single attempt.
REQUEST_TIMEOUT_MS = 30_000  # 30 seconds

# The google-genai SDK's own retry mechanism (built on the `tenacity`
# library): exponential backoff with jitter, retrying on rate limits
# (429), request timeouts (408), and server errors (5xx) - and also on
# network-level failures (connection errors, read timeouts) that never
# got an HTTP response at all. If this is left unset, the SDK does NOT
# retry anything by default.
RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=3,  # the original attempt plus 2 retries
    initial_delay=1.0,  # seconds
    max_delay=10.0,
    exp_base=2.0,
    jitter=0.5,
)


class GeminiProvider(LLMProvider):
    """Google Gemini, via the google-genai SDK. This is the provider the
    project is built on first - it has a usable free tier."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    def _client(self) -> genai.Client:
        return genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS, retry_options=RETRY_OPTIONS),
        )

    def _log(self, result) -> None:
        usage = getattr(result, "usage_metadata", None)
        if usage is None:
            return
        log_usage(
            provider="gemini",
            model=self.model,
            prompt_tokens=usage.prompt_token_count or 0,
            output_tokens=usage.candidates_token_count or 0,
            total_tokens=usage.total_token_count or 0,
        )

    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> str | BaseModel:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is empty in backend/.env.")
        client = self._client()

        if schema is None:
            try:
                result = client.models.generate_content(model=self.model, contents=prompt)
            except Exception as error:
                raise to_friendly_error(error) from error
            self._log(result)
            return result.text

        # Gemini's native JSON mode: response_schema constrains the model
        # to return JSON matching this exact Pydantic shape.
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        )

        def call_model(p: str) -> str:
            try:
                result = client.models.generate_content(model=self.model, contents=p, config=config)
            except Exception as error:
                raise to_friendly_error(error) from error
            self._log(result)
            return result.text

        return generate_structured(prompt, schema, call_model)

    def generate_stream(self, prompt: str) -> Iterator[str]:
        """Yields the reply as it arrives, piece by piece, instead of
        waiting for the whole thing. Not used by any endpoint yet outside
        of the Step 6 demo - Step 7 will wire this into the actual UI."""
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is empty in backend/.env.")
        client = self._client()
        try:
            stream = client.models.generate_content_stream(model=self.model, contents=prompt)
            last_result = None
            for chunk in stream:
                last_result = chunk
                if chunk.text:
                    yield chunk.text
            if last_result is not None:
                self._log(last_result)
        except Exception as error:
            raise to_friendly_error(error) from error
