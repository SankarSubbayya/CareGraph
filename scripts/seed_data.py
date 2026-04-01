"""Seed demo data into Neo4j for CareGraph hackathon demo."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph_db import (
    setup_schema, create_senior, store_checkin, store_alert,
    add_drug_interaction, add_side_effect, add_symptom_condition,
    dedupe_alerts,
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
    # Additional demo seniors (varied comorbidities, meds, living situations)
    {"name": "James O'Connor", "phone": "+14155551004",
     "medications": ["Warfarin 5mg", "Metoprolol 25mg"],
     "schedule": "08:00", "notes": "Atrial fibrillation. INR checked monthly at clinic.",
     "contacts": [{"name": "Moira O'Connor", "phone": "+14155552004", "relation": "daughter"}]},
    {"name": "Linda Park", "phone": "+14155551005",
     "medications": ["Albuterol HFA 90mcg", "Fluticasone 250mcg", "Tiotropium 18mcg"],
     "schedule": "09:30", "notes": "COPD — uses rescue inhaler; pulmonary rehab Tuesdays.",
     "contacts": [{"name": "Kevin Park", "phone": "+14155552005", "relation": "son"}]},
    {"name": "Harold Mills", "phone": "+14155551006",
     "medications": ["Digoxin 0.125mg", "Furosemide 40mg", "Spironolactone 25mg"],
     "schedule": "07:45", "notes": "CHF with reduced EF. Daily weights on fridge chart.",
     "contacts": [{"name": "Nurse Liaison Mills", "phone": "+14155552006", "relation": "son"}]},
    {"name": "Anne Patel", "phone": "+14155551007",
     "medications": ["Insulin glargine 24 units", "Metformin 500mg", "Empagliflozin 10mg"],
     "schedule": "08:15", "notes": "Type 2 diabetes; CGM training completed last month.",
     "contacts": [{"name": "Sanjay Patel", "phone": "+14155552007", "relation": "husband"}]},
    {"name": "George Foster", "phone": "+14155551008",
     "medications": ["Levodopa/Carbidopa 25/100mg", "Rasagiline 1mg"],
     "schedule": "10:15", "notes": "Parkinson's — freezing episodes; lives with spouse.",
     "contacts": [{"name": "Helen Foster", "phone": "+14155552008", "relation": "wife"}]},
    {"name": "Ruth Okonkwo", "phone": "+14155551009",
     "medications": ["Sertraline 50mg", "Trazodone 50mg", "Buspirone 10mg"],
     "schedule": "11:00", "notes": "GAD and insomnia; therapist every other week.",
     "contacts": [{"name": "Chioma Okonkwo", "phone": "+14155552009", "relation": "niece"}]},
    {"name": "Walter Kim", "phone": "+14155551010",
     "medications": ["Ibuprofen 400mg PRN", "Omeprazole 20mg", "Lisinopril 10mg"],
     "schedule": "09:45", "notes": "Osteoarthritis; uses cane. PPI for GI protection with NSAID.",
     "contacts": [{"name": "Min-Ji Kim", "phone": "+14155552010", "relation": "daughter"}]},
    {"name": "Patricia Nguyen", "phone": "+14155551011",
     "medications": ["Aspirin 81mg", "Clopidogrel 75mg", "Atorvastatin 40mg"],
     "schedule": "08:45", "notes": "Post-stroke on dual antiplatelet; speech therapy ongoing.",
     "contacts": [{"name": "Linh Nguyen", "phone": "+14155552011", "relation": "daughter"}]},
    {"name": "Eleanor Price", "phone": "+14155551012",
     "medications": ["Gabapentin 300mg", "Acetaminophen 500mg PRN"],
     "schedule": "10:30", "notes": "Diabetic neuropathy; prefers morning calls.",
     "contacts": [{"name": "Marcus Price", "phone": "+14155552012", "relation": "son"}]},
    {"name": "Samuel Rivera", "phone": "+14155551013",
     "medications": ["Prednisone 10mg", "Montelukast 10mg", "Albuterol HFA 90mcg"],
     "schedule": "07:30", "notes": "Persistent asthma; allergy to sulfa drugs noted in chart.",
     "contacts": [{"name": "Elena Rivera", "phone": "+14155552013", "relation": "wife"}]},
]

TRANSCRIPTS = [
    "I'm feeling great today! Yes, I took all my medications this morning.",
    "I'm okay, nothing special. Yes I took my pills.",
    "Feeling a bit tired and dizzy today. Yes I took my medications though.",
    "I'm not feeling great. I forgot to take my medications. I've been lonely.",
    "I'm doing fine. Yes, took all my meds. My daughter called yesterday.",
    "Feeling good! Already took my pills. Going to do some gardening today.",
    # Richer scenarios for analyzer (mood, services, concerns)
    "Wonderful mood! Took my pills. I need a ride to my doctor visit tomorrow.",
    "I'm confused about which bottle is morning versus night but I took something.",
    "Short of breath walking to the mailbox. Yes I used my inhaler and took my meds.",
    "Chest pain came back for a minute. I took my aspirin. Yes I took everything else too.",
    "Lonely week. I ran out of groceries and can't cook much. Yes I took my medications.",
    "Pretty good. My hip hurts but I'm okay. Yes took all meds.",
    "I need help with mail and packages piling up. Feeling fine, took my pills.",
    "Terrible sleep. I'm worried and tired. I didn't take my night medicine yet.",
    "Happy day! Church friends visited. Already took my morning medications.",
    "I fell getting out of bed but I'm not hurt. Yes I took my pills this morning.",
    "Can't breathe well after climbing stairs. I took my rescue inhaler. Meds otherwise yes.",
    "Sad and alone today. Forgot my morning pills — I'll take them after this call.",
    "Excellent! Refill picked up from pharmacy. Took everything on schedule.",
]

# (drug_a, drug_b, clinical_note)
DRUG_INTERACTIONS = [
    ("Metformin 500mg", "Lisinopril 10mg",
     "May increase risk of lactic acidosis. Monitor kidney function."),
    ("Amlodipine 5mg", "Atorvastatin 20mg",
     "Amlodipine may increase atorvastatin levels. Monitor for muscle pain."),
    ("Aspirin 81mg", "Lisinopril 10mg",
     "Aspirin may reduce effectiveness of Lisinopril. Monitor blood pressure."),
    ("Warfarin 5mg", "Aspirin 81mg",
     "Combined antithrombotic effect increases bleeding risk. Monitor INR closely."),
    ("Ibuprofen 400mg PRN", "Lisinopril 10mg",
     "NSAIDs may reduce antihypertensive effect and worsen renal function."),
    ("Aspirin 81mg", "Clopidogrel 75mg",
     "Dual antiplatelet therapy increases bleeding risk; duration per cardiology."),
    ("Metformin 500mg", "Insulin glargine 24 units",
     "Increased hypoglycemia risk when both are used; coordinate glucose checks."),
    ("Digoxin 0.125mg", "Furosemide 40mg",
     "Diuretic-induced electrolyte shifts may precipitate digoxin toxicity."),
    ("Sertraline 50mg", "Trazodone 50mg",
     "Additive serotonergic effects; watch for serotonin syndrome symptoms."),
    ("Prednisone 10mg", "Ibuprofen 400mg PRN",
     "NSAID plus corticosteroid increases GI ulceration risk."),
]

# (medication, symptom_keyword matching graph / analyzer)
SIDE_EFFECTS = [
    ("Lisinopril 10mg", "dizzy"),
    ("Lisinopril 10mg", "cough"),
    ("Metformin 500mg", "nausea"),
    ("Amlodipine 5mg", "dizzy"),
    ("Atorvastatin 20mg", "muscle pain"),
    ("Omeprazole 20mg", "headache"),
    ("Warfarin 5mg", "bruising"),
    ("Fluticasone 250mcg", "hoarse"),
    ("Furosemide 40mg", "dizzy"),
    ("Insulin glargine 24 units", "weak"),
    ("Levodopa/Carbidopa 25/100mg", "nausea"),
    ("Sertraline 50mg", "nausea"),
    ("Gabapentin 300mg", "drowsy"),
    ("Prednisone 10mg", "insomnia"),
    ("Metoprolol 25mg", "tired"),
    ("Empagliflozin 10mg", "thirsty"),
]

SYMPTOM_CONDITIONS = [
    ("dizzy", "Hypertension"),
    ("dizzy", "Dehydration"),
    ("fell", "Fall Risk"),
    ("chest pain", "Cardiac Event"),
    ("confused", "Cognitive Decline"),
    ("lonely", "Depression Risk"),
    ("breathing", "COPD"),
    ("weak", "Hypoglycemia"),
    ("bruising", "Anticoagulation Risk"),
    ("insomnia", "Depression Risk"),
    ("tremor", "Parkinson's Disease"),
    ("swelling", "Heart Failure"),
    ("pain", "Chronic Pain"),
    ("nausea", "GI Distress"),
    ("thirsty", "Dehydration"),
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
    for a, b, note in DRUG_INTERACTIONS:
        add_drug_interaction(a, b, note)
    print(f"  Added {len(DRUG_INTERACTIONS)} drug interactions")

    for med, symptom in SIDE_EFFECTS:
        add_side_effect(med, symptom)
    print(f"  Added {len(SIDE_EFFECTS)} side effects")

    for symptom, condition in SYMPTOM_CONDITIONS:
        add_symptom_condition(symptom, condition)
    print(f"  Added {len(SYMPTOM_CONDITIONS)} symptom-condition mappings")

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

    # Linda — respiratory concern (COPD cohort; matches emergency keyword in alert engine)
    resp_checkin = {"senior_phone": "+14155551005", "mood": "concerning", "wellness_score": 3,
                    "medication_taken": True, "concerns": ["can't breathe"],
                    "service_requests": []}
    store_checkin(
        "+14155551005", "copd_breath", ts,
        "I can't breathe well when I walk fast. Yes I took my medications and used my inhaler.",
        "concerning", 3, True, ["can't breathe"], [],
        "Dyspnea on exertion; meds taken",
    )
    evaluate_checkin(resp_checkin, "Linda Park")
    print("  Created breathing alert for Linda (COPD)")

    # Ruth — loneliness pathway
    lonely_checkin = {"senior_phone": "+14155551009", "mood": "sad", "wellness_score": 4,
                      "medication_taken": True, "concerns": ["loneliness"],
                      "service_requests": []}
    store_checkin(
        "+14155551009", "lonely_1", ts,
        "I feel lonely and alone this week. I took my pills though.",
        "sad", 4, True, ["loneliness"], [],
        "Social isolation concern",
    )
    evaluate_checkin(lonely_checkin, "Ruth Okonkwo")
    print("  Created loneliness alert for Ruth")

    d = dedupe_alerts()
    if d["alerts_removed"]:
        print(
            f"\n  Deduped alerts: removed {d['alerts_removed']} duplicate node(s) "
            f"({d['duplicate_groups']} duplicate group(s) by senior + message)."
        )

    print("\n🎉 Done! Visit http://localhost:8000")
    print("\n📊 Key demo queries:")
    print("  - Margaret's drug interactions: Metformin ↔ Lisinopril, Aspirin ↔ Lisinopril")
    print("  - Dorothy's dizziness matches Lisinopril side effect (graph intelligence!)")
    print("  - Walter: Ibuprofen + Lisinopril interaction; Patricia: dual antiplatelet")
    print("  - 13 seeded seniors with varied conditions, meds, and check-in transcripts")


if __name__ == "__main__":
    seed()
