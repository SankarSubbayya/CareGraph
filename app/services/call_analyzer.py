"""Analyze call transcripts to extract wellness indicators and service requests.
Copied from CareCompanion with RocketRide AI enhancement."""

from __future__ import annotations

import re

POSITIVE_WORDS = {
    "good", "great", "fine", "wonderful", "happy", "well", "better",
    "fantastic", "lovely", "okay", "excellent", "nice",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "pain", "hurt", "sick", "tired",
    "lonely", "sad", "depressed", "worried", "confused", "dizzy",
    "weak", "worse", "struggling",
}

EMERGENCY_WORDS = {
    "fall", "fell", "fallen", "chest pain", "can't breathe",
    "breathing", "emergency", "help me", "ambulance", "911",
    "stroke", "heart", "unconscious", "bleeding",
}

MEDICATION_YES = {"yes", "took", "taken", "already", "done", "sure did", "of course"}
MEDICATION_NO = {"no", "forgot", "haven't", "didn't", "not yet", "missed", "skip"}

SERVICE_PATTERNS = {
    "shower_help": {"phrases": ["shower", "bath", "bathing", "help washing"], "label": "Shower / Bathing Help"},
    "medicine_need": {"phrases": ["need medicine", "ran out of", "prescription", "refill", "pharmacy"], "label": "Medicine / Prescription"},
    "food_order": {"phrases": ["hungry", "need food", "groceries", "meal", "can't cook", "delivery"], "label": "Food / Meal Help"},
    "mail_help": {"phrases": ["mail", "mailbox", "package", "post office"], "label": "Mail / Package Help"},
    "medical_emergency": {"phrases": ["chest pain", "can't breathe", "stroke", "heart attack", "ambulance", "911", "bleeding badly"], "label": "Medical Emergency", "urgency": "critical"},
    "transportation": {"phrases": ["ride", "drive", "appointment", "doctor visit", "need a ride"], "label": "Transportation"},
    "companionship": {"phrases": ["lonely", "alone", "no one", "nobody", "visit me"], "label": "Companionship / Social"},
}


def detect_service_requests(transcript: str) -> list[dict]:
    text_lower = transcript.lower()
    requests = []
    for req_type, config in SERVICE_PATTERNS.items():
        matched = [p for p in config["phrases"] if p in text_lower]
        if matched:
            requests.append({
                "type": req_type, "label": config["label"],
                "details": f"Detected keywords: {', '.join(matched)}",
                "urgency": config.get("urgency", "normal"),
            })
    return requests


def analyze_transcript(transcript: str) -> dict:
    if not transcript:
        return {"mood": "unknown", "wellness_score": 5, "medication_taken": None,
                "concerns": [], "service_requests": [], "summary": "No transcript available"}

    text_lower = transcript.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))

    pos_count = len(words & POSITIVE_WORDS)
    neg_count = len(words & NEGATIVE_WORDS)

    if neg_count > pos_count + 1: mood = "concerning"
    elif neg_count > pos_count: mood = "sad"
    elif pos_count > neg_count + 1: mood = "happy"
    else: mood = "neutral"

    wellness_score = max(1, min(10, 6 + pos_count - (neg_count * 2)))

    med_yes = any(w in text_lower for w in MEDICATION_YES)
    med_no = any(w in text_lower for w in MEDICATION_NO)
    medication_taken = True if med_yes and not med_no else (False if med_no and not med_yes else None)

    concerns = [p for p in EMERGENCY_WORDS if p in text_lower]
    if "lonely" in text_lower or "alone" in text_lower: concerns.append("loneliness")
    if "confused" in text_lower: concerns.append("possible confusion")

    service_requests = detect_service_requests(transcript)
    if concerns: wellness_score = max(1, wellness_score - len(concerns))

    parts = [f"Mood: {mood}"]
    if medication_taken is True: parts.append("Medications taken")
    elif medication_taken is False: parts.append("Medications NOT taken")
    if concerns: parts.append(f"Concerns: {', '.join(concerns)}")
    if service_requests: parts.append(f"Service requests: {', '.join(r['label'] for r in service_requests)}")

    return {"mood": mood, "wellness_score": wellness_score, "medication_taken": medication_taken,
            "concerns": concerns, "service_requests": service_requests, "summary": ". ".join(parts)}
