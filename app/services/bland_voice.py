"""
Bland AI voice agent integration for CareGraph.

Uses Bland AI (https://www.bland.ai) to make automated check-in phone calls
to seniors and receive transcripts via webhook for graph analysis.

API docs: https://docs.bland.ai
Base URL: https://api.bland.ai/v1
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BLAND_BASE_URL = "https://api.bland.ai/v1"

CHECKIN_TASK = """You are a friendly, warm care assistant calling to check in on {senior_name}.
You work for CareGraph, a senior care service. Be patient, speak slowly and clearly.

Your goals for this call:
1. Ask how they're feeling today (mood and physical wellness)
2. Ask if they've taken their medications ({medications})
3. Ask if they have any pain, dizziness, or other symptoms
4. Ask if they need any services (meals, transportation, companionship, medical appointment)
5. Listen for any concerns or emergencies

Important rules:
- Be warm, conversational, and empathetic — not robotic
- If they mention chest pain, difficulty breathing, falls, or stroke symptoms, mark it as urgent
- If they seem confused or distressed, be extra gentle
- Keep the call under 3 minutes
- End by saying their family cares about them and to call back anytime

After the call, provide a summary of their mood, symptoms, medication adherence, and any concerns."""


async def _bland_request(method: str, path: str, **kwargs) -> dict:
    """Make an authenticated request to Bland AI API."""
    if not settings.bland_api_key:
        logger.debug("BLAND_API_KEY not set — skipping")
        return {}

    headers = {
        "authorization": settings.bland_api_key,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method,
                f"{BLAND_BASE_URL}{path}",
                headers=headers,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        logger.warning("Bland AI %s %s error %s: %s", method, path, e.response.status_code, e.response.text[:200])
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.warning("Bland AI request failed: %s", e)
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Outbound calls — automated senior check-ins
# ---------------------------------------------------------------------------

async def make_checkin_call(
    phone_number: str,
    senior_name: str,
    medications: list[str],
    *,
    webhook_url: str | None = None,
    voice: str = "June",
    first_sentence: str | None = None,
) -> dict:
    """Initiate an automated check-in call to a senior via Bland AI.

    Args:
        phone_number: Senior's phone in E.164 format (e.g., +15551234567)
        senior_name: Senior's name for personalized conversation
        medications: List of current medications to ask about
        webhook_url: URL to receive call results when call ends
        voice: Bland AI voice (June, Josh, Nat, Paige, Derek, Florian)
        first_sentence: Custom opening line

    Returns:
        {"status": "success", "call_id": "...", "message": "..."} or error
    """
    meds_str = ", ".join(medications) if medications else "none currently listed"

    task = CHECKIN_TASK.format(senior_name=senior_name, medications=meds_str)

    payload: dict[str, Any] = {
        "phone_number": phone_number,
        "task": task,
        "voice": voice,
        "model": "base",
        "language": "en",
        "max_duration": 5,
        "record": True,
        "wait_for_greeting": True,
        "temperature": 0.7,
        "interruption_threshold": 300,
        "request_data": {
            "senior_name": senior_name,
            "medications": medications,
        },
        "summary_prompt": (
            "Summarize this senior care check-in call. Extract: "
            "1) Overall mood (happy/neutral/sad/concerning) "
            "2) Wellness score (1-10) "
            "3) Whether they took medications (yes/no/unclear) "
            "4) Any symptoms mentioned "
            "5) Any services needed "
            "6) Any urgent concerns"
        ),
    }

    if first_sentence:
        payload["first_sentence"] = first_sentence
    else:
        payload["first_sentence"] = f"Hi {senior_name}, this is your care assistant from CareGraph. How are you doing today?"

    if webhook_url:
        payload["webhook"] = webhook_url

    return await _bland_request("POST", "/calls", json=payload)


# ---------------------------------------------------------------------------
# Call management
# ---------------------------------------------------------------------------

async def get_call_details(call_id: str) -> dict:
    """Get full details for a completed call including transcript and analysis."""
    return await _bland_request("GET", f"/calls/{call_id}")


async def analyze_call(call_id: str) -> dict:
    """Run post-call analysis on a completed call."""
    return await _bland_request("POST", f"/calls/{call_id}/analyze", json={
        "goal": "Evaluate the senior care check-in call for health and safety concerns",
        "questions": [
            ["What is the senior's overall mood?", "happy, neutral, sad, or concerning"],
            ["Did the senior take their medications?", "yes, no, or unclear"],
            ["What symptoms did the senior report?", "list of symptoms or none"],
            ["Does the senior need any services?", "list of services or none"],
            ["Are there any urgent health concerns?", "yes with details, or no"],
            ["What is an appropriate wellness score from 1-10?", "number"],
        ],
    })


async def stop_call(call_id: str) -> dict:
    """Stop an ongoing call."""
    return await _bland_request("POST", f"/calls/{call_id}/stop")


async def list_calls(limit: int = 20) -> dict:
    """List recent calls."""
    return await _bland_request("GET", f"/calls?limit={limit}")
