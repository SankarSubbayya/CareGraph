"""Check-in endpoints — data stored in Neo4j graph."""

from fastapi import APIRouter, HTTPException

from app.graph_db import get_checkins, get_all_checkins, get_latest_checkins, get_senior
from app.services.rocketride import (
    analyze_checkin_transcript,
    local_analyzer_to_normalized,
    merged_concerns_for_storage,
    service_requests_for_storage,
)
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

    analysis = await analyze_checkin_transcript(
        transcript, senior["name"], senior.get("medications", [])
    )
    if not analysis:
        analysis = local_analyzer_to_normalized(transcript)

    concerns_store = merged_concerns_for_storage(analysis)
    svc_store = service_requests_for_storage(analysis)
    now = datetime.now(timezone.utc).isoformat()

    checkin_key = store_checkin(
        senior_phone=phone, call_id=f"sim_{now}", timestamp=now,
        transcript=transcript, mood=analysis["mood"],
        wellness_score=analysis["wellness_score"],
        medication_taken=analysis["medication_taken"],
        concerns=concerns_store,
        service_requests=svc_store,
        summary=analysis["summary"],
    )

    checkin_data = {
        "senior_phone": phone, "mood": analysis["mood"],
        "wellness_score": analysis["wellness_score"],
        "medication_taken": analysis["medication_taken"],
        "concerns": concerns_store,
        "service_requests": svc_store,
    }
    alerts = evaluate_checkin(checkin_data, senior["name"])

    return {
        "status": "processed",
        "checkin_key": checkin_key,
        "analysis": analysis,
        "alerts": len(alerts),
    }
