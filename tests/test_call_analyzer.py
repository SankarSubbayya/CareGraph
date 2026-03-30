"""Unit tests for transcript analysis (NLP)."""

from app.services.call_analyzer import analyze_transcript, detect_service_requests


# ---------------------------------------------------------------------------
# Mood detection
# ---------------------------------------------------------------------------

def test_happy_mood():
    result = analyze_transcript("I'm feeling great today! Everything is wonderful.")
    assert result["mood"] == "happy"
    assert result["wellness_score"] >= 7


def test_sad_mood():
    result = analyze_transcript("I'm feeling bad and tired today.")
    assert result["mood"] in ("sad", "concerning")
    assert result["wellness_score"] <= 5


def test_neutral_mood():
    result = analyze_transcript("I'm doing okay, nothing special.")
    assert result["mood"] in ("neutral", "happy")


def test_concerning_mood():
    result = analyze_transcript("I'm in terrible pain and feel awful and weak and sick.")
    assert result["mood"] == "concerning"
    assert result["wellness_score"] <= 3


# ---------------------------------------------------------------------------
# Medication adherence
# ---------------------------------------------------------------------------

def test_medication_taken():
    result = analyze_transcript("Yes I took all my medications this morning.")
    assert result["medication_taken"] is True


def test_medication_not_taken():
    result = analyze_transcript("I forgot to take my medications today.")
    assert result["medication_taken"] is False


def test_medication_unknown():
    result = analyze_transcript("The weather is nice today.")
    assert result["medication_taken"] is None


# ---------------------------------------------------------------------------
# Emergency / concern detection
# ---------------------------------------------------------------------------

def test_fall_detected():
    result = analyze_transcript("I fell yesterday and my hip hurts.")
    assert "fell" in result["concerns"]


def test_chest_pain_detected():
    result = analyze_transcript("I'm having chest pain since this morning.")
    assert "chest pain" in result["concerns"]


def test_loneliness_detected():
    result = analyze_transcript("I've been so lonely. Nobody visits me.")
    assert "loneliness" in result["concerns"]


def test_no_concerns():
    result = analyze_transcript("I'm doing great today! Took my meds.")
    assert result["concerns"] == []


# ---------------------------------------------------------------------------
# Service request detection
# ---------------------------------------------------------------------------

def test_service_shower():
    requests = detect_service_requests("I need help with my shower today.")
    assert any(r["type"] == "shower_help" for r in requests)


def test_service_food():
    requests = detect_service_requests("I'm hungry and need food delivery.")
    assert any(r["type"] == "food_order" for r in requests)


def test_service_transportation():
    requests = detect_service_requests("I need a ride to my doctor appointment.")
    assert any(r["type"] == "transportation" for r in requests)


def test_service_companionship():
    requests = detect_service_requests("I'm so lonely, nobody visits me.")
    assert any(r["type"] == "companionship" for r in requests)


def test_service_medical_emergency():
    requests = detect_service_requests("I have chest pain, call 911!")
    assert any(r["type"] == "medical_emergency" for r in requests)
    assert any(r["urgency"] == "critical" for r in requests)


def test_no_service_requests():
    requests = detect_service_requests("I'm feeling fine today.")
    assert requests == []


# ---------------------------------------------------------------------------
# Empty / edge cases
# ---------------------------------------------------------------------------

def test_empty_transcript():
    result = analyze_transcript("")
    assert result["mood"] == "unknown"
    assert result["wellness_score"] == 5
    assert result["medication_taken"] is None


def test_summary_generated():
    result = analyze_transcript("I'm feeling good. Yes I took my medications.")
    assert "Mood:" in result["summary"]
    assert result["summary"] != ""
