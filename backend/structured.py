"""
Turns a plain "send text, get text back" model call into a validated,
schema-checked result - with one retry if the AI's first answer isn't
valid JSON.

This is deliberately separate from any specific provider (Gemini, etc.)
and takes the actual model call in as a plain function. That means it can
be tested with a fake, instant, offline function that pretends to be a
broken AI - see backend/verify_step4.py - instead of needing a real API
call every time we want to prove the retry logic works.
"""

from typing import Callable, TypeVar

from pydantic import BaseModel, ValidationError

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def generate_structured(
    prompt: str,
    schema: type[SchemaT],
    call_model: Callable[[str], str],
) -> SchemaT:
    """
    call_model(prompt) must return the AI's raw text response for that
    prompt. This function tries to validate that text against `schema`;
    if it fails, it retries once with a correction prompt appended. If
    the retry also fails, it raises a clear ValueError instead of letting
    a confusing parse error escape.
    """
    raw = call_model(prompt)
    parsed = _try_parse(raw, schema)
    if parsed is not None:
        return parsed

    correction_prompt = (
        f"{prompt}\n\n"
        "Your previous response was not valid JSON matching the required "
        "schema. Return ONLY valid JSON that matches the schema exactly - "
        "no markdown code fences, no explanation, no extra text."
    )
    raw_retry = call_model(correction_prompt)
    parsed = _try_parse(raw_retry, schema)
    if parsed is not None:
        return parsed

    raise ValueError(
        f"The AI did not return valid JSON matching {schema.__name__} "
        "even after one retry with a correction prompt."
    )


def _try_parse(raw_text: str, schema: type[SchemaT]) -> SchemaT | None:
    try:
        return schema.model_validate_json(raw_text)
    except (ValidationError, ValueError, TypeError):
        return None
