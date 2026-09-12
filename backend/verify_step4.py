"""
Manual proof that Step 4 works, in two parts:

1. A REAL call to Gemini, asking for resume bullets, checked against the
   ResumeBullets schema.
2. A FAKE, offline "model" that deliberately returns broken JSON, to prove
   the retry-then-fail-cleanly logic in backend/structured.py actually
   works - without depending on the real Gemini ever happening to send
   back broken JSON (which is rare and not something we can reliably
   trigger on demand).

Run it from the project's main folder with:
    C:\\dev\\venvs\\career-studio\\Scripts\\python.exe -m backend.verify_step4
"""

from pathlib import Path

from dotenv import load_dotenv

from backend.providers import get_provider
from backend.schemas import ResumeBullets
from backend.structured import generate_structured

load_dotenv(Path(__file__).resolve().parent / ".env")


def part_1_real_gemini_call():
    print("=== Part 1: real Gemini call, validated against ResumeBullets ===")
    provider = get_provider()
    result = provider.generate(
        "Write 3 short resume bullet points for a warehouse supervisor.",
        schema=ResumeBullets,
    )
    print("Type:", type(result).__name__)
    print("Validated result:", result)
    assert isinstance(result, ResumeBullets)
    assert len(result.bullets) > 0
    print("PASSED - got a real, validated ResumeBullets object.\n")


def part_2_recovers_after_one_bad_response():
    print("=== Part 2: fake model sends broken JSON once, then valid JSON ===")
    calls = {"count": 0}

    def flaky_call_model(prompt: str) -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            return "this is not json at all"
        return '{"bullets": ["Recovered on the second try"]}'

    result = generate_structured("irrelevant prompt", ResumeBullets, flaky_call_model)
    assert calls["count"] == 2, "expected exactly one retry"
    assert result.bullets == ["Recovered on the second try"]
    print("PASSED - recovered on retry after one broken response.\n")


def part_3_fails_cleanly_after_two_bad_responses():
    print("=== Part 3: fake model sends broken JSON twice in a row ===")

    def always_broken(prompt: str) -> str:
        return "still not json"

    try:
        generate_structured("irrelevant prompt", ResumeBullets, always_broken)
    except ValueError as error:
        print("Raised a clean ValueError, as expected:")
        print(" ", error)
        print("PASSED - failed cleanly instead of crashing or returning garbage.\n")
        return
    raise AssertionError("expected a ValueError but generate_structured did not raise")


if __name__ == "__main__":
    part_1_real_gemini_call()
    part_2_recovers_after_one_bad_response()
    part_3_fails_cleanly_after_two_bad_responses()
    print("All Step 4 checks passed.")
