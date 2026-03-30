"""Custom CrewAI tools that wrap CareGraph services.

Each tool gives a CrewAI agent access to one of our backends:
- Bland AI (voice calls)
- Neo4j (graph queries)
- RocketRide / GMI Cloud (LLM inference)
- Local NLP (transcript analysis)
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from crewai.tools import BaseTool

from app.graph_db import (
    get_senior,
    list_seniors,
    get_checkins,
    find_drug_interactions,
    find_medication_side_effects,
    find_similar_symptoms,
    get_care_network,
    store_checkin,
)
from app.services.call_analyzer import analyze_transcript
from app.services.alert_engine import evaluate_checkin
from app.services import bland_voice, gmi_inference


def _run_async(coro):
    """Run an async coroutine from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Voice Tools (Bland AI)
# ---------------------------------------------------------------------------

class MakeCheckInCallTool(BaseTool):
    name: str = "make_checkin_call"
    description: str = (
        "Initiate an automated voice call to a senior for a wellness check-in. "
        "Input: JSON with 'phone' (E.164 format). "
        "Returns call_id and status."
    )

    def _run(self, phone: str = "", **kwargs) -> str:
        senior = get_senior(phone)
        if not senior:
            return json.dumps({"error": f"Senior not found for phone: {phone}"})

        result = _run_async(bland_voice.make_checkin_call(
            phone_number=phone,
            senior_name=senior["name"],
            medications=senior.get("medications", []),
        ))
        return json.dumps(result, default=str)


# ---------------------------------------------------------------------------
# Analysis Tools (Local NLP)
# ---------------------------------------------------------------------------

class AnalyzeTranscriptTool(BaseTool):
    name: str = "analyze_transcript"
    description: str = (
        "Analyze a check-in call transcript to extract mood, symptoms, "
        "medication adherence, wellness score, and service needs. "
        "Input: the raw transcript text. "
        "Returns structured analysis JSON."
    )

    def _run(self, transcript: str = "", **kwargs) -> str:
        analysis = analyze_transcript(transcript)
        return json.dumps(analysis, default=str)


# ---------------------------------------------------------------------------
# Graph Tools (Neo4j)
# ---------------------------------------------------------------------------

class GetSeniorInfoTool(BaseTool):
    name: str = "get_senior_info"
    description: str = (
        "Look up a senior's profile from the Neo4j graph including name, "
        "medications, emergency contacts, and conditions. "
        "Input: phone number. Returns senior profile JSON."
    )

    def _run(self, phone: str = "", **kwargs) -> str:
        senior = get_senior(phone)
        if not senior:
            return json.dumps({"error": f"Senior not found: {phone}"})
        return json.dumps(senior, default=str)


class FindDrugInteractionsTool(BaseTool):
    name: str = "find_drug_interactions"
    description: str = (
        "Query Neo4j graph to find all known drug interactions for a senior's medications. "
        "Input: phone number. Returns list of interacting drug pairs."
    )

    def _run(self, phone: str = "", **kwargs) -> str:
        interactions = find_drug_interactions(phone)
        return json.dumps(interactions, default=str)


class FindSideEffectsTool(BaseTool):
    name: str = "find_side_effects"
    description: str = (
        "Query Neo4j graph to find medication side effects that match "
        "the senior's reported symptoms. "
        "Input: phone number. Returns side effect matches."
    )

    def _run(self, phone: str = "", **kwargs) -> str:
        side_effects = find_medication_side_effects(phone)
        return json.dumps(side_effects, default=str)


class FindSimilarSymptomsTool(BaseTool):
    name: str = "find_similar_symptoms"
    description: str = (
        "Query Neo4j graph to find other seniors who share the same symptoms. "
        "Input: phone number. Returns list of seniors with matching symptoms."
    )

    def _run(self, phone: str = "", **kwargs) -> str:
        similar = find_similar_symptoms(phone)
        return json.dumps(similar, default=str)


class GetCareNetworkTool(BaseTool):
    name: str = "get_care_network"
    description: str = (
        "Get the full care network graph for a senior including medications, "
        "symptoms, conditions, contacts, and all relationships. "
        "Input: phone number. Returns nodes and edges."
    )

    def _run(self, phone: str = "", **kwargs) -> str:
        network = get_care_network(phone)
        return json.dumps(network, default=str)


class StoreCheckInTool(BaseTool):
    name: str = "store_checkin"
    description: str = (
        "Store a check-in record in the Neo4j graph. "
        "Input: JSON with senior_phone, call_id, timestamp, transcript, "
        "mood, wellness_score, medication_taken, concerns, service_requests, summary. "
        "Returns checkin key."
    )

    def _run(self, **kwargs) -> str:
        from datetime import datetime, timezone
        checkin_key = store_checkin(
            senior_phone=kwargs.get("senior_phone", ""),
            call_id=kwargs.get("call_id", f"crew_{datetime.now(timezone.utc).isoformat()}"),
            timestamp=kwargs.get("timestamp", datetime.now(timezone.utc).isoformat()),
            transcript=kwargs.get("transcript", ""),
            mood=kwargs.get("mood", "neutral"),
            wellness_score=kwargs.get("wellness_score", 5),
            medication_taken=kwargs.get("medication_taken"),
            concerns=kwargs.get("concerns", []),
            service_requests=kwargs.get("service_requests", []),
            summary=kwargs.get("summary", ""),
        )
        return json.dumps({"checkin_key": checkin_key})


# ---------------------------------------------------------------------------
# AI Reasoning Tools (GMI Cloud)
# ---------------------------------------------------------------------------

class ExplainDrugInteractionTool(BaseTool):
    name: str = "explain_drug_interaction"
    description: str = (
        "Use AI (GMI Cloud) to explain a drug interaction in plain language. "
        "Input: two drug names separated by ' and '. "
        "Returns explanation for family caregivers."
    )

    def _run(self, drugs: str = "", **kwargs) -> str:
        parts = drugs.split(" and ", 1)
        drug1 = parts[0].strip() if parts else ""
        drug2 = parts[1].strip() if len(parts) > 1 else ""

        prompt = (
            f"Explain the drug interaction between {drug1} and {drug2} "
            f"for a senior patient. Include severity, symptoms to watch, "
            f"and what caregivers should do. Keep under 100 words."
        )
        result = _run_async(gmi_inference.query(prompt, system="You are a senior care AI assistant."))
        return result or "No AI explanation available."


class GenerateCareRecommendationTool(BaseTool):
    name: str = "generate_care_recommendation"
    description: str = (
        "Use AI (GMI Cloud) to generate a personalized care plan. "
        "Input: JSON string with senior data, symptoms, interactions, and checkin history. "
        "Returns care recommendations for family."
    )

    def _run(self, context: str = "", **kwargs) -> str:
        prompt = (
            f"Based on this senior's care data, provide:\n"
            f"1. Top 3 actionable recommendations for the family\n"
            f"2. Any concerns to discuss with their doctor\n"
            f"3. Suggested schedule adjustments\n\n"
            f"Data:\n{context}\n\n"
            f"Be concise. Write for a family caregiver."
        )
        result = _run_async(gmi_inference.query(prompt, system="You are a senior care AI assistant."))
        return result or "No AI recommendation available."


# ---------------------------------------------------------------------------
# Alert Tools
# ---------------------------------------------------------------------------

class EvaluateAlertsTool(BaseTool):
    name: str = "evaluate_alerts"
    description: str = (
        "Evaluate a check-in for alerts based on urgency, symptoms, and medication adherence. "
        "Input: JSON with senior_phone, mood, wellness_score, medication_taken, concerns, service_requests, and senior_name. "
        "Returns list of triggered alerts."
    )

    def _run(self, **kwargs) -> str:
        checkin_data = {
            "senior_phone": kwargs.get("senior_phone", ""),
            "mood": kwargs.get("mood", "neutral"),
            "wellness_score": kwargs.get("wellness_score", 5),
            "medication_taken": kwargs.get("medication_taken"),
            "concerns": kwargs.get("concerns", []),
            "service_requests": kwargs.get("service_requests", []),
        }
        senior_name = kwargs.get("senior_name", "Unknown")
        alerts = evaluate_checkin(checkin_data, senior_name)
        return json.dumps(alerts, default=str)
