"""Unit tests for RocketRide helpers (mocked HTTP, no real RocketRide/Neo4j)."""

import pytest

from app.services import rocketride as rr


def test_normalize_maps_service_needs_to_service_request_strings():
    raw = {
        "mood": "neutral",
        "wellness_score": 6,
        "medication_taken": None,
        "symptoms": ["dizzy"],
        "concerns": ["pain"],
        "service_needs": ["Meals on Wheels", "Transportation"],
        "summary": "ok",
        "recommendation": "call doctor",
    }
    out = rr._normalize_checkin_llm(raw, "Pat")
    assert out["service_requests"] == ["Meals on Wheels", "Transportation"]
    assert out["symptoms"] == ["dizzy"]
    assert out["concerns"] == ["pain"]
    assert out["recommendation"] == "call doctor"


def test_parse_json_from_markdown_fence():
    text = """```json
{"mood": "happy", "wellness_score": 8, "symptoms": [], "concerns": [], "service_needs": [], "summary": "x", "recommendation": ""}
```"""
    assert rr._extract_json_object(text)["mood"] == "happy"


def test_extract_nested_answers_format():
    payload = {
        "data": {
            "objects": {
                "body": {"answers": ["hello from pipeline"], "status": "Ok"}
            }
        }
    }
    assert rr.extract_text_from_rocketride_payload(payload) == "hello from pipeline"


@pytest.mark.asyncio
async def test_analyze_checkin_falls_back_when_webhook_invalid(monkeypatch):
    async def empty_infer(*_a, **_k):
        return ""

    monkeypatch.setattr(rr, "infer_with_fallback", empty_infer)
    out = await rr.analyze_checkin_transcript("hello", "Sam", [])
    assert out == {}


@pytest.mark.asyncio
async def test_explain_drug_returns_webhook_text(monkeypatch):
    async def fake_infer(prompt, *, system=rr.SYSTEM_PROMPT, webhook_url=None):
        return "  Combined risk: moderate.  "

    monkeypatch.setattr(rr, "infer_with_fallback", fake_infer)
    out = await rr.explain_drug_interaction("Aspirin", "Warfarin")
    assert out == "Combined risk: moderate."


@pytest.mark.asyncio
async def test_explain_drug_falls_back_empty(monkeypatch):
    async def empty_infer(*_a, **_k):
        return ""

    monkeypatch.setattr(rr, "infer_with_fallback", empty_infer)
    out = await rr.explain_drug_interaction("X", "Y")
    assert out == ""


def test_service_requests_for_storage_from_strings():
    norm = {
        "mood": "neutral",
        "wellness_score": 5,
        "medication_taken": None,
        "symptoms": [],
        "concerns": [],
        "service_requests": ["Food help", "Food help"],
        "summary": "s",
        "recommendation": "",
    }
    stored = rr.service_requests_for_storage(norm)
    assert len(stored) == 1
    assert stored[0]["type"] == "food_help"
    assert stored[0]["label"] == "Food help"


def test_merged_concerns_for_storage():
    norm = {
        "symptoms": ["dizzy", "dizzy"],
        "concerns": ["pain"],
        "mood": "neutral",
        "wellness_score": 5,
        "medication_taken": None,
        "service_requests": [],
        "summary": "",
        "recommendation": "",
    }
    m = rr.merged_concerns_for_storage(norm)
    assert "dizzy" in m and "pain" in m
