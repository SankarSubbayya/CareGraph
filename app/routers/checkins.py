"""Check-in endpoints — data stored in Neo4j graph."""

from fastapi import APIRouter, HTTPException

from app.graph_db import get_checkins, get_all_checkins, get_latest_checkins, get_senior
from app.services.call_analyzer import analyze_transcript
from app.services.alert_engine import evaluate_checkin
from app.graph_db import store_checkin
from datetime import datetime, timezone

router = APIRouter(prefix="/api/checkins", tags=["checkins"])


@router.get("")
async def all_checkins():
    return get_all_checkins()


@router.get("/latest/all")
async def latest_checkins():
    return get_latest_checkins()


@router.get("/{phone}")
async def senior_checkins(phone: str):
    return get_checkins(phone)


@router.post("/simulate/{phone}")
async def simulate_checkin(phone: str, transcript: str = "I'm feeling good today. Yes I took my medications."):
    """Simulate a check-in by providing a transcript directly."""
    senior = get_senior(phone)
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    analysis = analyze_transcript(transcript)
    now = datetime.now(timezone.utc).isoformat()

    checkin_key = store_checkin(
        senior_phone=phone, call_id=f"sim_{now}", timestamp=now,
        transcript=transcript, mood=analysis["mood"],
        wellness_score=analysis["wellness_score"],
        medication_taken=analysis["medication_taken"],
        concerns=analysis["concerns"],
        service_requests=analysis["service_requests"],
        summary=analysis["summary"],
    )

    checkin_data = {
        "senior_phone": phone, "mood": analysis["mood"],
        "wellness_score": analysis["wellness_score"],
        "medication_taken": analysis["medication_taken"],
        "concerns": analysis["concerns"],
        "service_requests": analysis["service_requests"],
    }
    alerts = evaluate_checkin(checkin_data, senior["name"])

    return {
        "status": "processed",
        "checkin_key": checkin_key,
        "analysis": analysis,
        "alerts": len(alerts),
        "alert_details": alerts,
    }
