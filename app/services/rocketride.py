"""
RocketRide AI integration for CareGraph.

Uses RocketRide AI for:
1. Transcript analysis — extract symptoms, mood, service needs
2. Drug interaction reasoning — explain why interactions are dangerous
3. Care recommendations — suggest next steps based on graph patterns
4. Symptom-to-condition inference — suggest possible conditions
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def query_rocketride(prompt: str, context: str = "") -> str:
    """Send a prompt to RocketRide AI and get a response."""
    if not settings.rocketride_apikey:
        logger.debug("RocketRide API key not set — using fallback")
        return ""

    payload = {
        "messages": [
            {"role": "system", "content": "You are a healthcare AI assistant for CareGraph, a senior care platform. Provide concise, actionable insights."},
        ],
    }

    if context:
        payload["messages"].append({"role": "system", "content": f"Context:\n{context}"})

    payload["messages"].append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {settings.rocketride_apikey}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.rocketride_uri}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        logger.warning("RocketRide query failed: %s", e)
        return ""


async def analyze_checkin_transcript(transcript: str, senior_name: str, medications: list[str]) -> dict:
    """Use RocketRide AI to analyze a check-in transcript."""
    meds_str = ", ".join(medications) if medications else "none listed"

    prompt = f"""Analyze this senior care check-in call transcript for {senior_name}.
Their medications: {meds_str}

Transcript:
"{transcript}"

Extract the following as JSON:
{{
  "mood": "happy|neutral|sad|concerning",
  "wellness_score": 1-10,
  "medication_taken": true|false|null,
  "symptoms": ["list of symptoms mentioned"],
  "concerns": ["list of concerns"],
  "service_needs": ["list of services needed"],
  "summary": "one sentence summary",
  "recommendation": "what should the family do next"
}}"""

    response = await query_rocketride(prompt)

    if not response:
        return {}

    # Try to parse JSON from response
    import json
    try:
        # Find JSON in response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {"raw_response": response}


async def explain_drug_interaction(drug1: str, drug2: str) -> str:
    """Use RocketRide AI to explain a drug interaction."""
    prompt = f"""Explain the potential drug interaction between {drug1} and {drug2} for a senior patient.
Include: what happens, severity (low/medium/high), and what the caregiver should do.
Keep it under 100 words, written for a family member (not a doctor)."""

    return await query_rocketride(prompt)


async def generate_care_recommendation(senior_data: dict, recent_checkins: list[dict],
                                        graph_insights: dict) -> str:
    """Use RocketRide AI to generate personalized care recommendations from graph data."""
    context = f"""Senior: {senior_data.get('name', 'Unknown')}
Medications: {', '.join(senior_data.get('medications', []))}
Recent moods: {', '.join(c.get('mood', '?') for c in recent_checkins[:5])}
Recent wellness scores: {', '.join(str(c.get('wellness_score', 0)) for c in recent_checkins[:5])}
Symptoms reported: {', '.join(graph_insights.get('symptoms', []))}
Drug interactions: {graph_insights.get('interactions', 'none detected')}
Side effect matches: {graph_insights.get('side_effects', 'none detected')}
Similar seniors: {graph_insights.get('similar_seniors', 'none found')}"""

    prompt = """Based on this senior's care graph data, provide:
1. Top 3 actionable recommendations for the family
2. Any concerns to discuss with their doctor
3. Suggested schedule adjustments

Be concise and practical. Write for a family caregiver, not a medical professional."""

    return await query_rocketride(prompt, context)


async def suggest_conditions(symptoms: list[str]) -> list[dict]:
    """Use RocketRide AI to suggest possible conditions from symptoms."""
    if not symptoms:
        return []

    prompt = f"""Given these symptoms reported by a senior: {', '.join(symptoms)}

Suggest up to 3 possible conditions. For each, provide:
- condition name
- likelihood (low/medium/high)
- recommended action

Return as JSON array: [{{"condition": "...", "likelihood": "...", "action": "..."}}]
Note: These are suggestions, not diagnoses. Always recommend consulting a doctor."""

    response = await query_rocketride(prompt)
    if not response:
        return []

    import json
    try:
        start = response.find("[")
        end = response.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return []
