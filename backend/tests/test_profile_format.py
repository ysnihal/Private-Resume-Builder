"""Tests for backend/profile_format.py - pure formatting, no AI involved."""

from backend.profile_format import format_candidate_background


def test_empty_profile_does_not_crash():
    text = format_candidate_background(None)
    assert "no profile information" in text.lower()

    text = format_candidate_background({})
    assert "no profile information" in text.lower()


def test_formats_current_job_as_present():
    profile = {
        "workExperience": [
            {
                "jobTitle": "Shift Lead",
                "employer": "Prior Co",
                "startDate": "2020",
                "endDate": "",
                "current": True,
                "notes": "Managed 10 staff.",
            }
        ]
    }
    text = format_candidate_background(profile)
    assert "Shift Lead" in text
    assert "Prior Co" in text
    assert "Present" in text
    assert "Managed 10 staff." in text


def test_includes_education_achievements_and_hobbies():
    profile = {
        "education": [{"degree": "BA", "fieldOfStudy": "Business", "school": "State U", "startDate": "2016", "endDate": "2020"}],
        "achievements": "Employee of the year",
        "hobbies": "Hiking",
    }
    text = format_candidate_background(profile)
    assert "BA" in text and "Business" in text and "State U" in text
    assert "Employee of the year" in text
    assert "Hiking" in text
