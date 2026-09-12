"""
Tests the real /api/generate/* endpoints end-to-end - request parsing,
prompt loading, schema validation, response shape - WITHOUT ever calling
a real AI or needing an API key. The provider is replaced with a fake
one that returns canned, already-valid data.

This is the test the brief specifically asked for: proof the app works
with no API key present at all.
"""

import backend.main as main_module
from backend.schemas import CoverLetterParagraph, CoverLetterParagraphs, ResumeBullets, ResumeSkills, ResumeSummary
from fastapi.testclient import TestClient


class FakeProvider:
    """Stands in for a real provider. Returns canned, already-valid data
    matching whatever schema was requested - the same shape a real
    provider would return after Step 4's validation succeeds."""

    def generate(self, prompt: str, schema=None):
        if schema is None:
            return "fake plain text response"
        if schema is ResumeBullets:
            return ResumeBullets(bullets=["Mock bullet one", "Mock bullet two"])
        if schema is ResumeSummary:
            return ResumeSummary(summary="Mock summary text.")
        if schema is ResumeSkills:
            return ResumeSkills(skills=["Mock skill A", "Mock skill B"])
        if schema is CoverLetterParagraphs:
            return CoverLetterParagraphs(paragraphs=[CoverLetterParagraph(id="p1", text="Mock paragraph.")])
        raise AssertionError(f"test doesn't know how to fake schema: {schema}")


class FailingProvider:
    """Stands in for a provider whose real call failed - used to prove
    main.py's error mapping (backend/errors.py) works end-to-end."""

    def __init__(self, error: Exception):
        self._error = error

    def generate(self, prompt: str, schema=None):
        raise self._error


def _client_with_no_api_key_and_fake_provider(monkeypatch, provider) -> TestClient:
    # Prove this doesn't secretly need a real key: remove it entirely.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(main_module, "get_provider", lambda: provider)
    return TestClient(main_module.app)


def test_resume_bullets_endpoint(monkeypatch):
    client = _client_with_no_api_key_and_fake_provider(monkeypatch, FakeProvider())
    response = client.post(
        "/api/generate/resume-bullets",
        json={
            "job_title": "Warehouse Supervisor",
            "job_company": "Acme Co",
            "job_description": "Lead a team.",
            "entry_title": "Shift Lead",
            "entry_organization": "Prior Co",
            "entry_date": "2020-2023",
            "existing_bullets": [],
            "profile": {},
        },
    )
    assert response.status_code == 200
    assert response.json() == {"bullets": ["Mock bullet one", "Mock bullet two"]}


def test_resume_field_summary_endpoint(monkeypatch):
    client = _client_with_no_api_key_and_fake_provider(monkeypatch, FakeProvider())
    response = client.post(
        "/api/generate/resume-field",
        json={"field": "summary", "job_title": "Warehouse Supervisor", "existing_value": "", "profile": {}},
    )
    assert response.status_code == 200
    assert response.json() == {"field": "summary", "value": "Mock summary text."}


def test_resume_field_skills_endpoint_joins_list_with_commas(monkeypatch):
    client = _client_with_no_api_key_and_fake_provider(monkeypatch, FakeProvider())
    response = client.post(
        "/api/generate/resume-field",
        json={"field": "skills", "job_title": "Warehouse Supervisor", "existing_value": "", "profile": {}},
    )
    assert response.status_code == 200
    assert response.json() == {"field": "skills", "value": "Mock skill A, Mock skill B"}


def test_cover_letter_paragraphs_endpoint(monkeypatch):
    client = _client_with_no_api_key_and_fake_provider(monkeypatch, FakeProvider())
    response = client.post(
        "/api/generate/cover-letter-paragraphs",
        json={"job_title": "Warehouse Supervisor", "existing_paragraphs": [], "profile": {}},
    )
    assert response.status_code == 200
    assert response.json() == {"paragraphs": [{"id": "p1", "text": "Mock paragraph."}]}


def test_friendly_rate_limit_error_becomes_http_429(monkeypatch):
    from backend.errors import FriendlyError

    error = FriendlyError("rate_limit", "You've hit the free-tier limit.")
    client = _client_with_no_api_key_and_fake_provider(monkeypatch, FailingProvider(error))
    response = client.post(
        "/api/generate/resume-bullets",
        json={"job_title": "x", "profile": {}},
    )
    assert response.status_code == 429
    assert response.json() == {"detail": "You've hit the free-tier limit."}


def test_unexpected_error_becomes_http_502_without_crashing(monkeypatch):
    client = _client_with_no_api_key_and_fake_provider(monkeypatch, FailingProvider(RuntimeError("boom")))
    response = client.post(
        "/api/generate/resume-bullets",
        json={"job_title": "x", "profile": {}},
    )
    assert response.status_code == 502
    assert "boom" in response.json()["detail"]
