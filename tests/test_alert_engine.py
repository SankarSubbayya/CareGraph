"""Unit tests for alert engine.

Uses monkeypatch to avoid Neo4j calls during testing.
"""

import pytest


@pytest.fixture(autouse=True)
def mock_neo4j(monkeypatch):
    """Prevent alert engine from writing to Neo4j during tests."""
    monkeypatch.setattr("app.services.alert_engine.store_alert", lambda *a, **kw: None)


from app.services.alert_engine import evaluate_checkin


# ---------------------------------------------------------------------------
# Emergency alerts
# ---------------------------------------------------------------------------

def test_fall_triggers_critical_alert():
    checkin = {
        "senior_phone": "+14155551001",
        "mood": "concerning",
        "wellness_score": 2,
        "medication_taken": False,
        "concerns": ["fell"],
        "service_requests": [],
    }
    alerts = evaluate_checkin(checkin, "Margaret Johnson")
    critical = [a for a in alerts if a["severity"] == "critical"]
    assert len(critical) >= 1
    assert any("fell" in a["message"].lower() for a in critical)


def test_chest_pain_triggers_critical():
    checkin = {
        "senior_phone": "+14155551001",
        "mood": "concerning",
        "wellness_score": 1,
        "medication_taken": True,
        "concerns": ["chest pain"],
        "service_requests": [],
    }
    alerts = evaluate_checkin(checkin, "Margaret Johnson")
    assert any(a["severity"] == "critical" for a in alerts)


# ---------------------------------------------------------------------------
# Low mood / wellness alerts
# ---------------------------------------------------------------------------

def test_low_wellness_triggers_high_alert():
    checkin = {
        "senior_phone": "+14155551002",
        "mood": "sad",
        "wellness_score": 3,
        "medication_taken": True,
        "concerns": [],
        "service_requests": [],
    }
    alerts = evaluate_checkin(checkin, "Robert Chen")
    assert any(a["alert_type"] == "low_mood" and a["severity"] == "high" for a in alerts)


def test_concerning_mood_triggers_alert():
    checkin = {
        "senior_phone": "+14155551002",
        "mood": "concerning",
        "wellness_score": 5,
        "medication_taken": True,
        "concerns": [],
        "service_requests": [],
    }
    alerts = evaluate_checkin(checkin, "Robert Chen")
    assert any(a["alert_type"] == "low_mood" for a in alerts)


# ---------------------------------------------------------------------------
# Medication alerts
# ---------------------------------------------------------------------------

def test_missed_medication_triggers_alert():
    checkin = {
        "senior_phone": "+14155551003",
        "mood": "neutral",
        "wellness_score": 5,
        "medication_taken": False,
        "concerns": [],
        "service_requests": [],
    }
    alerts = evaluate_checkin(checkin, "Dorothy Williams")
    assert any(a["alert_type"] == "missed_medication" for a in alerts)


def test_medication_taken_no_alert():
    checkin = {
        "senior_phone": "+14155551003",
        "mood": "happy",
        "wellness_score": 8,
        "medication_taken": True,
        "concerns": [],
        "service_requests": [],
    }
    alerts = evaluate_checkin(checkin, "Dorothy Williams")
    assert not any(a["alert_type"] == "missed_medication" for a in alerts)


# ---------------------------------------------------------------------------
# Loneliness alerts
# ---------------------------------------------------------------------------

def test_loneliness_triggers_alert():
    checkin = {
        "senior_phone": "+14155551002",
        "mood": "sad",
        "wellness_score": 4,
        "medication_taken": True,
        "concerns": ["loneliness"],
        "service_requests": [],
    }
    alerts = evaluate_checkin(checkin, "Robert Chen")
    assert any(a["alert_type"] == "loneliness" for a in alerts)


# ---------------------------------------------------------------------------
# Service request alerts
# ---------------------------------------------------------------------------

def test_service_request_triggers_alert():
    checkin = {
        "senior_phone": "+14155551002",
        "mood": "neutral",
        "wellness_score": 5,
        "medication_taken": True,
        "concerns": [],
        "service_requests": [
            {"type": "food_order", "label": "Food Help", "details": "hungry", "urgency": "normal"},
        ],
    }
    alerts = evaluate_checkin(checkin, "Robert Chen")
    assert any(a["alert_type"] == "service_request" for a in alerts)


def test_medical_emergency_service_is_critical():
    checkin = {
        "senior_phone": "+14155551001",
        "mood": "concerning",
        "wellness_score": 1,
        "medication_taken": True,
        "concerns": [],
        "service_requests": [
            {"type": "medical_emergency", "label": "Medical Emergency", "details": "chest pain", "urgency": "critical"},
        ],
    }
    alerts = evaluate_checkin(checkin, "Margaret Johnson")
    svc_alerts = [a for a in alerts if a["alert_type"] == "service_request"]
    assert any(a["severity"] == "critical" for a in svc_alerts)


# ---------------------------------------------------------------------------
# No alerts
# ---------------------------------------------------------------------------

def test_healthy_checkin_no_alerts():
    checkin = {
        "senior_phone": "+14155551001",
        "mood": "happy",
        "wellness_score": 9,
        "medication_taken": True,
        "concerns": [],
        "service_requests": [],
    }
    alerts = evaluate_checkin(checkin, "Margaret Johnson")
    assert alerts == []
