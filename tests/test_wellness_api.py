"""Tests for GET /api/seniors/wellness-overview (no Neo4j required — uses monkeypatch)."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_SAMPLE_WELLNESS = [
    {
        "phone": "+14155551001",
        "name": "Test Senior",
        "checkin_schedule": "09:00",
        "last_checkin_timestamp": "2026-03-20T12:00:00+00:00",
        "days_since_checkin": 10,
        "at_risk": True,
        "days_threshold": 7,
    },
    {
        "phone": "+14155551002",
        "name": "Ok Senior",
        "checkin_schedule": "10:00",
        "last_checkin_timestamp": "2026-03-29T12:00:00+00:00",
        "days_since_checkin": 1,
        "at_risk": False,
        "days_threshold": 7,
    },
]


def test_wellness_overview_ok(monkeypatch):
    def fake_wellness(days_threshold: int = 7):
        return [{**r, "days_threshold": days_threshold} for r in _SAMPLE_WELLNESS]

    monkeypatch.setattr("app.routers.seniors.get_senior_checkin_wellness", fake_wellness)

    resp = client.get("/api/seniors/wellness-overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["days_threshold"] == 7
    assert data["at_risk_count"] == 1
    assert len(data["seniors"]) == 2
    assert any(s["phone"] == "+14155551001" and s["at_risk"] for s in data["seniors"])


def test_wellness_overview_custom_threshold(monkeypatch):
    def fake_wellness(days_threshold: int = 7):
        rows = [
            {
                "phone": "+1",
                "name": "A",
                "checkin_schedule": "09:00",
                "last_checkin_timestamp": None,
                "days_since_checkin": None,
                "at_risk": True,
                "days_threshold": days_threshold,
            }
        ]
        return rows

    monkeypatch.setattr("app.routers.seniors.get_senior_checkin_wellness", fake_wellness)

    resp = client.get("/api/seniors/wellness-overview?days_threshold=14")
    assert resp.status_code == 200
    assert resp.json()["days_threshold"] == 14


def test_wellness_overview_invalid_threshold():
    resp = client.get("/api/seniors/wellness-overview?days_threshold=0")
    assert resp.status_code == 400

    resp = client.get("/api/seniors/wellness-overview?days_threshold=100")
    assert resp.status_code == 400


def test_wellness_route_not_shadowed_by_phone_param(monkeypatch):
    """Static path /wellness-overview must not be captured as {phone}."""
    monkeypatch.setattr("app.routers.seniors.get_senior_checkin_wellness", lambda days_threshold=7: [])
    resp = client.get("/api/seniors/wellness-overview")
    assert resp.status_code == 200
    assert resp.json() == {"days_threshold": 7, "at_risk_count": 0, "seniors": []}
