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

CHECKIN_TASK = """You are a friendly, warm care assistant making a daily check-in call on behalf of CareGraph.
You are calling {senior_name}. Be patient, speak slowly and clearly like you're talking to a loved one.

Start the call by saying this is their daily wellness check-in from CareGraph.

Follow this conversation flow:

1. GREETING & WELLNESS
   - Ask how they're feeling today — physically and emotionally
   - Listen carefully for any mention of pain, dizziness, fatigue, or mood changes

2. MEDICATION CHECK
   - Ask: "Have you taken all your medications today?"
   - Their medications are: {medications}
   - If they say no or forgot, gently remind them how important it is and ask if they need help remembering
   - If they mention side effects (dizziness, nausea, headaches), note it carefully

3. SYMPTOMS & CONCERNS
   - Ask if they have any new symptoms or health concerns
   - If they mention chest pain, difficulty breathing, falls, or stroke symptoms — mark it as URGENT and tell them help is on the way
   - If they seem confused or distressed, be extra gentle and reassuring

4. MEDICAL ASSISTANCE
   - Ask: "Do you need help scheduling a doctor's appointment?"
   - If yes, ask what kind of doctor they need
   - You have access to a network of doctors. Here are some you can recommend:
     {doctors}
   - If they need a dermatologist, recommend one from the list
   - If they need a primary care doctor, recommend one near their area
   - Provide the doctor's name and phone number
   - Let them know CareGraph can help coordinate with their family to schedule the visit
   - If they mention wanting a second opinion or specialist, note that as a service request

5. OTHER NEEDS
   - Ask if they need any help today — meals, transportation, companionship, or anything else
   - Listen for signs of loneliness (living alone, nobody visits, feeling isolated)

Important rules:
- Be warm, conversational, and empathetic — never robotic or rushed
- Call them by their first name
- If they seem to want to chat, let them talk — don't cut them off
- IMPORTANT: If you provide any health-related suggestions, always remind them that this is general guidance only and their doctor should make all final medical decisions. Say something like "Of course, your doctor would know best about your specific situation."
- Keep the call under 4 minutes unless they need more time
- End by saying: "Your family cares about you, and so do we at CareGraph. Don't hesitate to call if you need anything."

After the call, provide a summary of: mood, medication adherence, symptoms, doctor/medical needs, and any concerns."""


def _get_doctors_for_call() -> str:
    """Fetch top doctors from Neo4j to include in call task."""
    try:
        from app.graph_db import get_driver
        driver = get_driver()
        lines = []
        with driver.session() as session:
            # Top-rated primary care doctors with senior health interest
            result = session.run("""
                MATCH (d:Doctor)
                WHERE d.rating IS NOT NULL AND d.rating >= 4.8
                  AND d.phone IS NOT NULL AND d.accepting_patients = true
                RETURN d.name AS name, d.specialty AS specialty, d.phone AS phone,
                       d.city AS city, d.rating AS rating, d.senior_care AS senior_care
                ORDER BY d.senior_care DESC, d.rating DESC
                LIMIT 5
            """)
            for r in result:
                senior_tag = " [Senior Care Specialist]" if r["senior_care"] else ""
                lines.append(f"- {r['name']} ({r['specialty']}) in {r['city'] or 'Bay Area'}, "
                             f"Rating: {r['rating']}/5, Phone: {r['phone']}{senior_tag}")

            # Top dermatologists
            result = session.run("""
                MATCH (d:Doctor)
                WHERE d.specialty CONTAINS 'Dermatology'
                  AND d.rating IS NOT NULL AND d.rating >= 4.9
                  AND d.accepting_patients = true
                RETURN d.name AS name, d.phone AS phone, d.rating AS rating
                ORDER BY d.rating DESC
                LIMIT 3
            """)
            for r in result:
                lines.append(f"- {r['name']} (Dermatologist), Rating: {r['rating']}/5, Phone: {r['phone']}")

        return "\n     ".join(lines) if lines else "No doctors available in the system yet."
    except Exception as e:
        logger.warning("Failed to fetch doctors from Neo4j: %s", e)
        return "Doctor directory currently unavailable."


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

    # Fetch recommended doctors from Neo4j graph
    doctors_str = _get_doctors_for_call()

    task = CHECKIN_TASK.format(senior_name=senior_name, medications=meds_str, doctors=doctors_str)

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
        payload["first_sentence"] = f"Good morning {senior_name}! This is your daily check-in call from CareGraph. How are you feeling today?"

    if webhook_url and webhook_url.startswith("https://"):
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
