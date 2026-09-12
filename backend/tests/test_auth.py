"""
Tests backend/auth.py's password gate: a no-op locally (no APP_PASSWORD
set), enforced once one is configured (e.g. on Render).
"""

from fastapi.testclient import TestClient

import backend.main as main_module


def test_no_password_required_when_unset(monkeypatch):
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    client = TestClient(main_module.app)
    response = client.get("/")
    assert response.status_code == 200


def test_rejects_missing_credentials_when_password_set(monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "correct-horse-battery-staple")
    client = TestClient(main_module.app)
    response = client.get("/")
    assert response.status_code == 401


def test_rejects_wrong_password(monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "correct-horse-battery-staple")
    client = TestClient(main_module.app)
    response = client.get("/", auth=("anyone", "wrong-password"))
    assert response.status_code == 401


def test_accepts_correct_password(monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "correct-horse-battery-staple")
    client = TestClient(main_module.app)
    response = client.get("/", auth=("anyone", "correct-horse-battery-staple"))
    assert response.status_code == 200
