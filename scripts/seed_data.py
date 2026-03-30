"""Seed demo data into Neo4j for CareGraph hackathon demo."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph_db import (
    setup_schema, create_senior, store_checkin, store_alert,
    add_drug_interaction, add_side_effect, add_symptom_condition,
)
from app.services.call_analyzer import analyze_transcript
from app.services.alert_engine import evaluate_checkin
from datetime import datetime, timedelta, timezone
import random

SENIORS = [
    {"name": "Margaret Johnson", "phone": "+14155551001",
     "medications": ["Metformin 500mg", "Lisinopril 10mg", "Aspirin 81mg"],
     "schedule": "09:00", "notes": "Lives alone. Daughter Sarah visits weekends.",
     "contacts": [{"name": "Sarah Johnson", "phone": "+14155552001", "relation": "daughter"}]},
    {"name": "Robert Chen", "phone": "+14155551002",
     "medications": ["Amlodipine 5mg", "Atorvastatin 20mg"],
     "schedule": "10:00", "notes": "Recently widowed. Enjoys gardening.",
     "contacts": [{"name": "David Chen", "phone": "+14155552002", "relation": "son"}]},
    {"name": "Dorothy Williams", "phone": "+14155551003",
     "medications": ["Levothyroxine 50mcg", "Omeprazole 20mg", "Lisinopril 10mg"],
     "schedule": "08:30", "notes": "Mild mobility issues. Uses walker.",
     "contacts": [{"name": "James Williams", "phone": "+14155552003", "relation": "son"}]},
]

TRANSCRIPTS = [
    "I'm feeling great today! Yes, I took all my medications this morning.",
    "I'm okay, nothing special. Yes I took my pills.",
    "Feeling a bit tired and dizzy today. Yes I took my medications though.",
    "I'm not feeling great. I forgot to take my medications. I've been lonely.",
    "I'm doing fine. Yes, took all my meds. My daughter called yesterday.",
    "Feeling good! Already took my pills. Going to do some gardening today.",
]


def seed():
    print("Setting up Neo4j schema...")
    setup_schema()

    # Create seniors
    for s in SENIORS:
        create_senior(s["name"], s["phone"], s["medications"], s["schedule"], s["notes"], s["contacts"])
        print(f"  Created {s['name']}")

    # Add drug interaction knowledge
    print("\nAdding medical knowledge to graph...")
    add_drug_interaction("Metformin 500mg", "Lisinopril 10mg",
                         "May increase risk of lactic acidosis. Monitor kidney function.")
    add_drug_interaction("Amlodipine 5mg", "Atorvastatin 20mg",
                         "Amlodipine may increase atorvastatin levels. Monitor for muscle pain.")
    add_drug_interaction("Aspirin 81mg", "Lisinopril 10mg",
                         "Aspirin may reduce effectiveness of Lisinopril. Monitor blood pressure.")
    print("  Added 3 drug interactions")

    # Add side effects
    add_side_effect("Lisinopril 10mg", "dizzy")
    add_side_effect("Lisinopril 10mg", "cough")
    add_side_effect("Metformin 500mg", "nausea")
    add_side_effect("Amlodipine 5mg", "dizzy")
    add_side_effect("Atorvastatin 20mg", "muscle pain")
    add_side_effect("Omeprazole 20mg", "headache")
    print("  Added 6 side effects")

    # Add symptom-condition mappings
    add_symptom_condition("dizzy", "Hypertension")
    add_symptom_condition("dizzy", "Dehydration")
    add_symptom_condition("fell", "Fall Risk")
    add_symptom_condition("chest pain", "Cardiac Event")
    add_symptom_condition("confused", "Cognitive Decline")
    add_symptom_condition("lonely", "Depression Risk")
    print("  Added 6 symptom-condition mappings")

    # Seed check-in history
    print("\nSeeding check-in history...")
    now = datetime.now(timezone.utc)
    for s in SENIORS:
        for days_ago in range(7, 0, -1):
            ts = (now - timedelta(days=days_ago, hours=random.randint(0, 3))).isoformat()
            transcript = random.choice(TRANSCRIPTS)
            analysis = analyze_transcript(transcript)
            store_checkin(
                senior_phone=s["phone"], call_id=f"seed_{s['phone']}_{days_ago}",
                timestamp=ts, transcript=transcript, mood=analysis["mood"],
                wellness_score=analysis["wellness_score"],
                medication_taken=analysis["medication_taken"],
                concerns=analysis["concerns"],
                service_requests=analysis["service_requests"],
                summary=analysis["summary"],
            )
        print(f"  Seeded 7 days for {s['name']}")

    # Create demo alerts
    print("\nCreating demo alerts...")
    ts = now.isoformat()

    # Margaret fell
    fell_checkin = {"senior_phone": "+14155551001", "mood": "concerning", "wellness_score": 2,
                    "medication_taken": False, "concerns": ["fell", "pain"],
                    "service_requests": [], "summary": "Fell. Missed meds."}
    store_checkin("+14155551001", "alert_fell", ts, "I fell yesterday. My hip hurts. I forgot my medications.",
                  "concerning", 2, False, ["fell", "pain"], [], "Fell. Missed meds.")
    evaluate_checkin(fell_checkin, "Margaret Johnson")
    print("  Created emergency alerts for Margaret")

    # Robert needs food + shower
    svc_checkin = {"senior_phone": "+14155551002", "mood": "sad", "wellness_score": 4,
                   "medication_taken": True, "concerns": [],
                   "service_requests": [{"type": "shower_help", "label": "Shower Help", "details": "shower", "urgency": "normal"},
                                        {"type": "food_order", "label": "Food Help", "details": "hungry", "urgency": "normal"}]}
    store_checkin("+14155551002", "svc_1", ts, "I need help showering. I'm hungry.", "sad", 4, True, [],
                  svc_checkin["service_requests"], "Needs shower + food")
    evaluate_checkin(svc_checkin, "Robert Chen")
    print("  Created service requests for Robert")

    # Dorothy dizzy (matches Lisinopril side effect!)
    dizzy_checkin = {"senior_phone": "+14155551003", "mood": "sad", "wellness_score": 4,
                     "medication_taken": True, "concerns": ["dizzy"],
                     "service_requests": []}
    store_checkin("+14155551003", "dizzy_1", ts, "I've been feeling dizzy all day.", "sad", 4, True,
                  ["dizzy"], [], "Dizzy — possible Lisinopril side effect")
    evaluate_checkin(dizzy_checkin, "Dorothy Williams")
    print("  Created dizziness alert for Dorothy (matches Lisinopril side effect!)")

    print("\n🎉 Done! Visit http://localhost:8000")
    print("\n📊 Key demo queries:")
    print("  - Margaret's drug interactions: Metformin ↔ Lisinopril, Aspirin ↔ Lisinopril")
    print("  - Dorothy's dizziness matches Lisinopril side effect (graph intelligence!)")
    print("  - Margaret & Dorothy both take Lisinopril (similar medications)")


if __name__ == "__main__":
    seed()
