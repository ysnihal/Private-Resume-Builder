"""
Logs how many tokens each AI call used and what that would cost on a paid
tier, so you can see usage over time without digging through a provider's
own dashboard. Appends one JSON line per call to backend/usage_log.jsonl
(gitignored - this is local runtime data, not something to publish).

Gemini's free tier costs $0 while you're under its request limits -
"estimated cost" here is only what the SAME usage would cost on the paid
tier, for awareness of what you'd be spending if you outgrow free.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "usage_log.jsonl"

# Price per 1 million tokens, in USD. Source: Google's official pricing
# page (ai.google.dev/gemini-api/docs/pricing), checked 2026-09-11 for the
# rate that applies through Dec 31, 2026 (it rises after that - update
# this if the log's estimates start looking off).
PRICING_PER_MILLION_TOKENS = {
    "gemini-3.6-flash": {"input": 0.75, "output": 3.75},
}


def log_usage(provider: str, model: str, prompt_tokens: int, output_tokens: int, total_tokens: int) -> None:
    prices = PRICING_PER_MILLION_TOKENS.get(model)
    estimated_cost = (
        (prompt_tokens / 1_000_000 * prices["input"]) + (output_tokens / 1_000_000 * prices["output"])
        if prices
        else None  # unknown model - don't guess a price
    )

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(estimated_cost, 6) if estimated_cost is not None else None,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
