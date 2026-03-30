"""Voice agent endpoints — Bland AI powered check-in calls."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from app.graph_db import get_senior, list_seniors, store_checkin
from app.services.bland_voice import (
    make_checkin_call,
    get_call_details,
    analyze_call,
    stop_call,
    list_calls,
)
from app.services.call_analyzer import analyze_transcript
from app.services.alert_engine import evaluate_checkin
from app.config import settings

router = APIRouter(prefix="/api/voice", tags=["voice"])


# ---------------------------------------------------------------------------
# Initiate calls
# ---------------------------------------------------------------------------

@router.post("/call/{phone}")
async def initiate_checkin_call(phone: str, voice: str = "June"):
    """Initiate a Bland AI voice call to check in on a senior.

    The call will be made by the AI voice agent which asks about mood,
    medications, symptoms, and service needs. Results come back via webhook
    or can be polled via GET /api/voice/call/{call_id}.
    """
    senior = get_senior(phone)
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    # Build webhook URL for call results
    webhook_url = f"{settings.base_url}/api/voice/webhook"

    result = await make_checkin_call(
        phone_number=phone,
        senior_name=senior["name"],
        medications=senior.get("medications", []),
        webhook_url=webhook_url,
        voice=voice,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result.get("message", "Bland AI call failed"))

    return {
        "status": "call_initiated",
        "call_id": result.get("call_id"),
        "senior": senior["name"],
        "phone": phone,
        "message": result.get("message", "Call queued"),
    }


@router.post("/call-all")
async def call_all_seniors(voice: str = "June"):
    """Initiate check-in calls to ALL seniors. Returns list of call IDs."""
    seniors = list_seniors()
    if not seniors:
        raise HTTPException(status_code=404, detail="No seniors registered")

    webhook_url = f"{settings.base_url}/api/voice/webhook"
    results = []

    for senior in seniors:
        result = await make_checkin_call(
            phone_number=senior["phone"],
            senior_name=senior["name"],
            medications=senior.get("medications", []),
            webhook_url=webhook_url,
            voice=voice,
        )
        results.append({
            "senior": senior["name"],
            "phone": senior["phone"],
            "call_id": result.get("call_id"),
            "status": result.get("status", "error"),
        })

    return {"calls_initiated": len(results), "results": results}


# ---------------------------------------------------------------------------
# Call status and details
# ---------------------------------------------------------------------------

@router.get("/call/{call_id}")
async def get_call_status(call_id: str):
    """Get details for a specific call including transcript and analysis."""
    result = await get_call_details(call_id)
    if not result or result.get("status") == "error":
        raise HTTPException(status_code=404, detail="Call not found")
    return result


@router.post("/call/{call_id}/analyze")
async def analyze_completed_call(call_id: str):
    """Run post-call AI analysis on a completed call."""
    result = await analyze_call(call_id)
    if not result or result.get("status") == "error":
        raise HTTPException(status_code=502, detail="Analysis failed")
    return result


@router.post("/call/{call_id}/stop")
async def stop_active_call(call_id: str):
    """Stop an ongoing call."""
    result = await stop_call(call_id)
    return result


@router.get("/calls")
async def recent_calls(limit: int = 20):
    """List recent Bland AI calls."""
    return await list_calls(limit)


# ---------------------------------------------------------------------------
# Webhook — receives call results from Bland AI
# ---------------------------------------------------------------------------

@router.post("/webhook")
async def bland_webhook(request: Request):
    """Receive call completion webhook from Bland AI.

    When a call ends, Bland AI sends the transcript and analysis here.
    We process it through the same pipeline as simulated check-ins:
    transcript → analysis → Neo4j graph → alerts.
    """
    payload = await request.json()

    call_id = payload.get("call_id", "")
    transcript = payload.get("concatenated_transcript", "")
    status = payload.get("status", "")
    request_data = payload.get("request_data", {})
    senior_name = request_data.get("senior_name", "Unknown")
    phone = payload.get("to", "")

    if not transcript or status != "completed":
        return {"status": "skipped", "reason": f"call status: {status}"}

    # Find senior by phone
    senior = get_senior(phone)
    if not senior:
        return {"status": "skipped", "reason": f"senior not found for {phone}"}

    # Process transcript through analysis pipeline
    analysis = analyze_transcript(transcript)
    now = datetime.now(timezone.utc).isoformat()

    checkin_key = store_checkin(
        senior_phone=phone,
        call_id=f"bland_{call_id}",
        timestamp=now,
        transcript=transcript,
        mood=analysis["mood"],
        wellness_score=analysis["wellness_score"],
        medication_taken=analysis["medication_taken"],
        concerns=analysis["concerns"],
        service_requests=analysis["service_requests"],
        summary=analysis["summary"],
    )

    # Evaluate for alerts
    checkin_data = {
        "senior_phone": phone,
        "mood": analysis["mood"],
        "wellness_score": analysis["wellness_score"],
        "medication_taken": analysis["medication_taken"],
        "concerns": analysis["concerns"],
        "service_requests": analysis["service_requests"],
    }
    alerts = evaluate_checkin(checkin_data, senior["name"])

    return {
        "status": "processed",
        "call_id": call_id,
        "senior": senior_name,
        "checkin_key": checkin_key,
        "alerts_generated": len(alerts),
    }
