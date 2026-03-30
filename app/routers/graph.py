"""Graph intelligence endpoints — Neo4j powered queries + RocketRide AI."""

from fastapi import APIRouter, HTTPException

from app.graph_db import (
    get_care_network,
    find_drug_interactions,
    find_similar_symptoms,
    find_medication_side_effects,
    get_senior,
    get_checkins,
    get_seniors_by_symptom,
    get_seniors_by_medication,
)
from app.services.rocketride import (
    generate_care_recommendation,
    explain_drug_interaction,
    suggest_conditions,
)

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/care-network/{phone}")
async def care_network(phone: str):
    """Get the full care network graph for visualization."""
    network = get_care_network(phone)
    if not network["nodes"]:
        raise HTTPException(status_code=404, detail="Senior not found")
    return network


@router.get("/drug-interactions/{phone}")
async def drug_interactions(phone: str):
    """Find drug interactions for a senior's medications."""
    interactions = find_drug_interactions(phone)
    # Get AI explanation for each
    for interaction in interactions:
        explanation = await explain_drug_interaction(
            interaction["drug1"], interaction["drug2"]
        )
        interaction["ai_explanation"] = explanation
    return {"phone": phone, "interactions": interactions}


@router.get("/similar-symptoms/{phone}")
async def similar_symptoms(phone: str):
    """Find other seniors with similar symptoms."""
    return {"phone": phone, "similar": find_similar_symptoms(phone)}


@router.get("/side-effects/{phone}")
async def side_effects(phone: str):
    """Check if symptoms match medication side effects."""
    return {"phone": phone, "side_effects": find_medication_side_effects(phone)}


@router.get("/care-recommendation/{phone}")
async def care_recommendation(phone: str):
    """AI-generated care recommendation from graph data."""
    senior = get_senior(phone)
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    checkins = get_checkins(phone)
    interactions = find_drug_interactions(phone)
    side_effects = find_medication_side_effects(phone)
    similar = find_similar_symptoms(phone)

    # Collect symptoms from checkins
    symptoms = set()
    for ci in checkins:
        symptoms.update(ci.get("concerns", []))

    graph_insights = {
        "symptoms": list(symptoms),
        "interactions": ", ".join(f"{i['drug1']}↔{i['drug2']}" for i in interactions) or "none",
        "side_effects": ", ".join(f"{s['medication']}→{s['symptom']}" for s in side_effects) or "none",
        "similar_seniors": ", ".join(f"{s['other_senior']} ({s['symptom']})" for s in similar) or "none",
    }

    recommendation = await generate_care_recommendation(senior, checkins[:5], graph_insights)
    return {
        "phone": phone,
        "senior": senior["name"],
        "recommendation": recommendation,
        "graph_insights": graph_insights,
    }


@router.get("/condition-suggestions/{phone}")
async def condition_suggestions(phone: str):
    """AI-suggested conditions based on reported symptoms."""
    checkins = get_checkins(phone)
    symptoms = set()
    for ci in checkins:
        symptoms.update(ci.get("concerns", []))

    if not symptoms:
        return {"phone": phone, "suggestions": [], "note": "No symptoms reported"}

    suggestions = await suggest_conditions(list(symptoms))
    return {"phone": phone, "symptoms": list(symptoms), "suggestions": suggestions}


@router.get("/seniors-by-symptom/{symptom}")
async def by_symptom(symptom: str):
    """Find all seniors who reported a specific symptom."""
    return get_seniors_by_symptom(symptom)


@router.get("/seniors-by-medication/{medication}")
async def by_medication(medication: str):
    """Find all seniors taking a specific medication."""
    return get_seniors_by_medication(medication)
