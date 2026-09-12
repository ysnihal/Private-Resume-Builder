"""Tests for backend/prompts.py - no AI involved, just template loading."""

import pytest

from backend.prompts import load_prompt


def test_fills_in_placeholders():
    text = load_prompt("test_connectivity")
    assert "hello" in text.lower()


def test_resume_bullets_template_substitutes_all_placeholders():
    text = load_prompt(
        "resume_bullets",
        job_title="Warehouse Supervisor",
        job_company="Acme Co",
        job_description="Lead a team.",
        entry_title="Shift Lead",
        entry_organization="Prior Co",
        entry_date="2020-2023",
        existing_bullets="(none yet)",
        candidate_background="Managed 10 staff.",
    )
    assert "Warehouse Supervisor" in text
    assert "Shift Lead" in text
    assert "Managed 10 staff." in text
    assert "$" not in text  # no placeholder should be left unfilled


def test_missing_placeholder_raises_instead_of_leaking_literal_text():
    with pytest.raises(KeyError):
        load_prompt("resume_bullets", job_title="Only one value provided")
