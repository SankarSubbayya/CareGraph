"""
RocketRide AI integration for CareGraph.

Inference chain:
  1. Try RocketRide pipeline (webhook) — uses .pipe visual pipeline
  2. Fallback to GMI Cloud direct API — OpenAI-compatible at api.gmi-serving.com
  3. If neither configured, return empty (graph queries still work)

RocketRide pipelines (.pipe files):
  Webhook (input) → Prompt (template) → Gemini LLM → Response (output)

GMI Cloud direct:
  POST https://api.gmi-serving.com/v1/chat/completions (OpenAI-compatible)
"""

from __future__ import annotations

import json
import logging
import re

import httpx

from app.config import settings
from app.services import gmi_inference

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a healthcare AI assistant for CareGraph, a senior care platform. "
    "Provide concise, actionable insights written for family caregivers, not doctors."
)

# ---------------------------------------------------------------------------
# RocketRide webhook caller
# ---------------------------------------------------------------------------

async def _call_rocketride(text: str) -> str:
    """Send text to RocketRide pipeline webhook and return the answer string."""
    if not settings.rocketride_uri or not settings.rocketride_apikey:
        return ""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.rocketride_apikey}",
    }

    try:
        # Connectivity check (3s timeout)
        async with httpx.AsyncClient(timeout=3.0) as ping_client:
            resp = await ping_client.post(
                f"{settings.rocketride_uri}/webhook",
                headers=headers,
                json={"text": "ping"},
            )
            data = resp.json()
            body = data.get("data", {}).get("objects", {}).get("body", {})
            if body.get("status") == "Error":
                return ""
    except Exception:
        return ""

    try:
        # Main request (45s timeout for LLM processing)
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{settings.rocketride_uri}/webhook",
                headers=headers,
                json={"text": text},
            )
            resp.raise_for_status()
            data = resp.json()
            body = data.get("data", {}).get("objects", {}).get("body", {})
            answers = body.get("answers", [])

            if isinstance(answers, list) and answers:
                return answers[0]
            return str(answers) if answers else ""
    except Exception as e:
        logger.warning("RocketRide query failed: %s", e)
        return ""


# ---------------------------------------------------------------------------
# Unified query: RocketRide → GMI Cloud fallback
# ---------------------------------------------------------------------------

async def _query(prompt: str, *, system: str = SYSTEM_PROMPT) -> str:
    """Try RocketRide pipeline first, fall back to GMI Cloud direct."""
    # Try RocketRide
    result = await _call_rocketride(prompt)
    if result:
        logger.info("Response from RocketRide pipeline")
        return result

    # Fallback to GMI Cloud
    result = await gmi_inference.query(prompt, system=system)
    if result:
        logger.info("Response from GMI Cloud (%s)", settings.gmi_model)
        return result

    logger.debug("No inference backend available — returning empty")
    return ""


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------

def _extract_json_object(text: str) -> dict | None:
    """Extract first JSON object from a response string."""
    json_match = re.search(r"```(?:json)?\s*\n(.*?)(?:\n```|$)", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _extract_json_array(text: str) -> list | None:
    """Extract first JSON array from a response string."""
    json_match = re.search(r"```(?:json)?\s*\n(.*?)(?:\n```|$)", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    arr_match = re.search(r"\[.*\]", text, re.DOTALL)
    if arr_match:
        try:
            return json.loads(arr_match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass
    return None


# ---------------------------------------------------------------------------
# Pipeline-specific functions
# ---------------------------------------------------------------------------

async def analyze_checkin_transcript(transcript: str, senior_name: str, medications: list[str]) -> dict:
    """Analyze a check-in transcript — extract symptoms, mood, urgency."""
    meds_str = ", ".join(medications) if medications else "none listed"

    prompt = (
        f"Analyze this senior care check-in call transcript for {senior_name}.\n"
        f"Their medications: {meds_str}\n\n"
        f'Transcript:\n"{transcript}"\n\n'
        f"Extract the following as JSON:\n"
        f'{{\n'
        f'  "mood": "happy|neutral|sad|concerning",\n'
        f'  "wellness_score": 1-10,\n'
        f'  "medication_taken": true|false|null,\n'
        f'  "symptoms": ["list of symptoms mentioned"],\n'
        f'  "concerns": ["list of concerns"],\n'
        f'  "service_needs": ["list of services needed"],\n'
        f'  "summary": "one sentence summary",\n'
        f'  "recommendation": "what should the family do next"\n'
        f'}}'
    )

    response = await _query(prompt)
    if not response:
        return {}

    result = _extract_json_object(response)
    return result if result else {"raw_response": response}


async def explain_drug_interaction(drug1: str, drug2: str) -> str:
    """Explain a drug interaction in plain language for caregivers."""
    prompt = (
        f"Explain the potential drug interaction between {drug1} and {drug2} "
        f"for a senior patient.\n"
        f"Include: what happens, severity (low/medium/high), symptoms to watch for, "
        f"and what the caregiver should do.\n"
        f"Keep it under 100 words, written for a family member (not a doctor)."
    )

    return await _query(prompt)


async def generate_care_recommendation(
    senior_data: dict, recent_checkins: list[dict], graph_insights: dict
) -> str:
    """Generate personalized care recommendations from graph data."""
    prompt = (
        f"Senior: {senior_data.get('name', 'Unknown')}\n"
        f"Medications: {', '.join(senior_data.get('medications', []))}\n"
        f"Recent moods: {', '.join(c.get('mood', '?') for c in recent_checkins[:5])}\n"
        f"Recent wellness scores: {', '.join(str(c.get('wellness_score', 0)) for c in recent_checkins[:5])}\n"
        f"Symptoms reported: {', '.join(graph_insights.get('symptoms', []))}\n"
        f"Drug interactions: {graph_insights.get('interactions', 'none detected')}\n"
        f"Side effect matches: {graph_insights.get('side_effects', 'none detected')}\n"
        f"Similar seniors: {graph_insights.get('similar_seniors', 'none found')}\n\n"
        f"Based on this senior's care graph data, provide:\n"
        f"1. Top 3 actionable recommendations for the family\n"
        f"2. Any concerns to discuss with their doctor\n"
        f"3. Suggested schedule adjustments\n\n"
        f"Be concise and practical. Write for a family caregiver."
    )

    return await _query(prompt)


async def suggest_conditions(symptoms: list[str]) -> list[dict]:
    """Suggest possible conditions from symptom clusters."""
    if not symptoms:
        return []

    prompt = (
        f"Given these symptoms reported by a senior: {', '.join(symptoms)}\n\n"
        f"Suggest up to 3 possible conditions. For each, provide:\n"
        f"- condition name\n"
        f"- likelihood (low/medium/high)\n"
        f"- recommended action\n\n"
        f'Return as JSON array: [{{"condition": "...", "likelihood": "...", "action": "..."}}]\n'
        f"Note: These are suggestions, not diagnoses. Always recommend consulting a doctor."
    )

    response = await _query(prompt)
    if not response:
        return []

    result = _extract_json_array(response)
    return result if result else []
