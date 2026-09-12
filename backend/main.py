"""
Career Studio backend.

This is the ONLY place in the whole project that is allowed to talk to an
AI provider's API. It reads secrets from backend/.env (a file that never
gets uploaded to GitHub - see .gitignore) and never sends any of them to
the browser.

Which provider actually runs is decided in one place: the LLM_PROVIDER
setting in backend/.env. See backend/providers/__init__.py.

What the AI is actually asked lives in backend/prompts/*.txt, not here -
see backend/prompts/README.md.

Retries, timeouts, and error messages: see backend/errors.py and each
provider's own retry/timeout settings (currently just
backend/providers/gemini_provider.py). Token usage and estimated cost are
logged to backend/usage_log.jsonl - see backend/usage_log.py.

To run this file: from the project's main folder, run
    C:\\dev\\venvs\\career-studio\\Scripts\\python.exe -m uvicorn backend.main:app --reload
Then open http://127.0.0.1:8000/api/test-llm in your browser.
"""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from .auth import require_app_password
from .errors import STATUS_BY_KIND, FriendlyError
from .profile_format import format_candidate_background
from .prompts import load_prompt
from .providers import get_provider
from .providers.gemini_provider import GeminiProvider
from .schemas import CoverLetterParagraphs, ResumeBullets, ResumeSkills, ResumeSummary

# Load backend/.env by its exact location on disk, so this works no matter
# which folder you happen to run the server from.
load_dotenv(Path(__file__).resolve().parent / ".env")

# The project's folder, one level up from backend/ - where Resume.html,
# CoverLetter.html, and index.html live. Only these three exact files are
# ever served (see the routes near the bottom) - never the whole folder,
# which would expose backend/.env and your real API key to the browser.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# dependencies=[...] applies to every route below, including the HTML
# pages - see backend/auth.py for why this is a no-op locally.
app = FastAPI(title="Career Studio Backend", dependencies=[Depends(require_app_password)])


class TestResponse(BaseModel):
    provider: str
    prompt: str
    response: str


def _raise_friendly(error: Exception, fallback_detail: str) -> None:
    """Turns any exception into an HTTPException with a sensible status
    code - a specific one if it's a FriendlyError (see backend/errors.py),
    or a generic 502 with the raw message otherwise."""
    if isinstance(error, FriendlyError):
        raise HTTPException(status_code=STATUS_BY_KIND.get(error.kind, 500), detail=error.message) from error
    raise HTTPException(status_code=502, detail=f"{fallback_detail}: {error}") from error


@app.get("/")
def read_root():
    return {"status": "Career Studio backend is running."}


@app.get("/api/test-llm", response_model=TestResponse)
def test_llm():
    """A one-off connectivity check: sends a fixed prompt to whichever
    provider LLM_PROVIDER points at in backend/.env, and returns whatever
    it says back. Nothing here is saved anywhere."""
    provider_name = os.getenv("LLM_PROVIDER", "gemini")
    prompt = load_prompt("test_connectivity")

    try:
        provider = get_provider()
        text = provider.generate(prompt)
    except Exception as error:
        _raise_friendly(error, f"{provider_name} call failed")

    return TestResponse(provider=provider_name, prompt=prompt, response=text)


@app.get("/api/test-structured", response_model=ResumeBullets)
def test_structured():
    """Proves Step 4 AND Step 5 end-to-end: this uses the real
    resume_bullets.txt template that Step 7 will use for real, filled in
    here with made-up SAMPLE data instead of a real profile and job
    description (those don't exist yet - no button calls this for real
    until Step 7). The AI's reply is returned already validated against
    the ResumeBullets schema. Nothing here is saved anywhere."""
    prompt = load_prompt(
        "resume_bullets",
        job_title="Warehouse Supervisor",
        job_company="Example Logistics Co.",
        job_description=(
            "Seeking a warehouse supervisor to lead a team of 20+ associates, "
            "improve safety compliance, and streamline shipping operations."
        ),
        entry_title="Warehouse Supervisor",
        entry_organization="Previous Employer Inc.",
        entry_date="2021 - Present",
        existing_bullets="(none yet)",
        candidate_background=(
            "Managed daily operations for a mid-size distribution center; "
            "trained new staff; reduced shipping errors."
        ),
    )
    try:
        provider = get_provider()
        result = provider.generate(prompt, schema=ResumeBullets)
    except Exception as error:
        _raise_friendly(error, "Structured generation failed")

    return result


@app.get("/api/test-stream")
def test_stream():
    """Proves streaming works: the reply arrives in pieces as Gemini
    generates it, instead of all at once. Only Gemini supports this so
    far. Nothing here is saved anywhere."""
    provider = get_provider()
    if not isinstance(provider, GeminiProvider):
        raise HTTPException(status_code=501, detail="Streaming isn't implemented for this provider yet.")

    prompt = load_prompt("test_connectivity")

    def stream():
        try:
            for piece in provider.generate_stream(prompt):
                yield piece
        except FriendlyError as error:
            yield f"\n\n[STREAM ERROR: {error.message}]"

    return StreamingResponse(stream(), media_type="text/plain")


# ---------------------------------------------------------------------------
# Real generation endpoints (Step 7) - these are what the actual "Generate
# with AI" buttons in Resume.html and CoverLetter.html call.
# ---------------------------------------------------------------------------


class ResumeBulletsRequest(BaseModel):
    job_title: str = ""
    job_company: str = ""
    job_description: str = ""
    entry_title: str = ""
    entry_organization: str = ""
    entry_date: str = ""
    existing_bullets: list[str] = []
    profile: dict = {}


@app.post("/api/generate/resume-bullets", response_model=ResumeBullets)
def generate_resume_bullets(request: ResumeBulletsRequest):
    prompt = load_prompt(
        "resume_bullets",
        job_title=request.job_title or "(not specified)",
        job_company=request.job_company or "(not specified)",
        job_description=request.job_description or "(none provided)",
        entry_title=request.entry_title or "(untitled)",
        entry_organization=request.entry_organization or "(not specified)",
        entry_date=request.entry_date or "(not specified)",
        existing_bullets="\n".join(request.existing_bullets) or "(none yet)",
        candidate_background=format_candidate_background(request.profile),
    )
    try:
        result = get_provider().generate(prompt, schema=ResumeBullets)
    except Exception as error:
        _raise_friendly(error, "Resume bullet generation failed")
    return result


class ResumeFieldRequest(BaseModel):
    field: Literal["summary", "skills"]
    job_title: str = ""
    job_company: str = ""
    job_description: str = ""
    existing_value: str = ""
    profile: dict = {}


@app.post("/api/generate/resume-field")
def generate_resume_field(request: ResumeFieldRequest):
    common_args = dict(
        job_title=request.job_title or "(not specified)",
        job_company=request.job_company or "(not specified)",
        job_description=request.job_description or "(none provided)",
        existing_value=request.existing_value or "(none yet)",
        candidate_background=format_candidate_background(request.profile),
    )
    try:
        if request.field == "summary":
            prompt = load_prompt("resume_summary", **common_args)
            result = get_provider().generate(prompt, schema=ResumeSummary)
            return {"field": "summary", "value": result.summary}

        prompt = load_prompt("resume_skills", **common_args)
        result = get_provider().generate(prompt, schema=ResumeSkills)
        return {"field": "skills", "value": ", ".join(result.skills)}
    except Exception as error:
        _raise_friendly(error, "Resume field generation failed")


class CoverLetterParagraphIn(BaseModel):
    id: str
    text: str


class CoverLetterRequest(BaseModel):
    job_title: str = ""
    job_company: str = ""
    hiring_manager: str = ""
    job_description: str = ""
    existing_paragraphs: list[CoverLetterParagraphIn] = []
    profile: dict = {}


@app.post("/api/generate/cover-letter-paragraphs", response_model=CoverLetterParagraphs)
def generate_cover_letter_paragraphs(request: CoverLetterRequest):
    existing_text = (
        "\n".join(f"{p.id}: {p.text}" for p in request.existing_paragraphs) or "(none yet)"
    )
    prompt = load_prompt(
        "cover_letter_paragraphs",
        job_title=request.job_title or "(not specified)",
        job_company=request.job_company or "(not specified)",
        hiring_manager=request.hiring_manager or "Hiring Manager",
        job_description=request.job_description or "(none provided)",
        existing_paragraphs=existing_text,
        candidate_background=format_candidate_background(request.profile),
    )
    try:
        result = get_provider().generate(prompt, schema=CoverLetterParagraphs)
    except Exception as error:
        _raise_friendly(error, "Cover letter generation failed")
    return result


# ---------------------------------------------------------------------------
# Serving the app's own HTML files (Step 7) - so they're loaded from
# http://127.0.0.1:8000/... instead of opened as a local file://. Same
# origin as the API means the browser never needs CORS at all. Only these
# three exact files are served - never a folder mount - so nothing else in
# the project (backend/.env included) is ever reachable over HTTP.
# ---------------------------------------------------------------------------


@app.get("/index.html")
def serve_index():
    return FileResponse(PROJECT_ROOT / "index.html")


@app.get("/Resume.html")
def serve_resume():
    return FileResponse(PROJECT_ROOT / "Resume.html")


@app.get("/CoverLetter.html")
def serve_cover_letter():
    return FileResponse(PROJECT_ROOT / "CoverLetter.html")
