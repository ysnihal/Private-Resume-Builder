"""
Turns raw provider exceptions into a short, human-readable message plus a
machine-readable `kind` - so backend/main.py can pick a sensible HTTP
status code, and so a future frontend (Step 7) can show something a
person can actually act on instead of a raw stack trace or a provider's
internal JSON error blob.
"""

import httpx
import httpx2
from google.genai import errors as genai_errors

#: kind -> HTTP status code to answer the browser with.
STATUS_BY_KIND = {
    "rate_limit": 429,
    "auth": 500,  # the app's own misconfiguration, not the browser's fault
    "not_found": 500,  # likewise - a wrong model name in backend/.env
    "server_error": 502,
    "network": 502,
    "client_error": 502,
    "unknown": 500,
}


class FriendlyError(Exception):
    """A clean, user-facing error. `kind` picks an HTTP status (see
    STATUS_BY_KIND); `message` is safe to show directly to a person."""

    def __init__(self, kind: str, message: str):
        self.kind = kind
        self.message = message
        super().__init__(message)


def _rate_limit_message(error: genai_errors.APIError) -> str:
    """Gemini's 429 response says exactly which quota was hit (per-minute
    vs per-day) and, often, how long to wait - so use that instead of
    guessing. Falls back to a generic message if those details aren't
    present (they're normal response fields, not guaranteed on every
    error)."""
    details = error.details if isinstance(error.details, dict) else {}
    violations = []
    retry_seconds = None
    for item in details.get("error", {}).get("details", []) or details.get("details", []) or []:
        if item.get("@type", "").endswith("QuotaFailure"):
            violations.extend(v.get("quotaId", "") for v in item.get("violations", []))
        if item.get("@type", "").endswith("RetryInfo"):
            retry_seconds = item.get("retryDelay", "").rstrip("s") or None

    if any("PerDay" in v for v in violations):
        period = "Gemini's free-tier DAILY quota"
    elif any("PerMinute" in v for v in violations):
        period = "Gemini's free-tier per-minute rate limit"
    else:
        period = "Gemini's free-tier limit"

    wait_hint = f"Google says to retry in about {retry_seconds} seconds." if retry_seconds else "Wait a while and try again."
    return f"You've hit {period}. This was already retried automatically - {wait_hint}"


def to_friendly_error(error: Exception) -> FriendlyError:
    if isinstance(error, genai_errors.APIError):
        if error.code == 429 or error.status == "RESOURCE_EXHAUSTED":
            return FriendlyError("rate_limit", _rate_limit_message(error))
        if error.code in (401, 403):
            return FriendlyError(
                "auth",
                "Gemini rejected the API key in backend/.env. Check that it "
                "was copied correctly and hasn't been revoked.",
            )
        if error.code == 404:
            return FriendlyError(
                "not_found",
                f"Gemini says the model name in backend/.env doesn't exist "
                f"({error.message or 'not found'}). Check GEMINI_MODEL.",
            )
        if error.code is not None and 500 <= error.code < 600:
            return FriendlyError(
                "server_error",
                "Gemini's servers are having trouble right now. This was "
                "already retried automatically and still failed - try "
                "again shortly.",
            )
        return FriendlyError("client_error", f"Gemini rejected the request: {error.message or error}")

    if isinstance(error, (httpx.TransportError, httpx2.TransportError)):
        return FriendlyError(
            "network",
            "Could not reach Gemini's servers. This was already retried "
            "automatically and still failed - check your internet connection.",
        )

    return FriendlyError("unknown", f"Something unexpected went wrong: {error}")
