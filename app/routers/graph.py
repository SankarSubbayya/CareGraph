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


@router.get("/doctors")
async def list_doctors(specialty: str = "", city: str = "", limit: int = 20):
    """Query doctors from the Neo4j knowledge graph."""
    from app.graph_db import get_driver
    driver = get_driver()
    with driver.session() as session:
        query = "MATCH (d:Doctor) WHERE d.accepting_patients = true"
        params = {"limit": limit}
        if specialty:
            query += " AND toLower(d.specialty) CONTAINS toLower($specialty)"
            params["specialty"] = specialty
        if city:
            query += " AND toLower(d.city) CONTAINS toLower($city)"
            params["city"] = city
        query += " RETURN d ORDER BY d.rating DESC LIMIT $limit"
        result = session.run(query, **params)
        doctors = []
        for r in result:
            d = dict(r["d"])
            doctors.append(d)
    return {"doctors": doctors, "total": len(doctors)}


@router.get("/doctors/for-senior/{phone}")
async def doctors_for_senior(phone: str):
    """Find recommended doctors for a senior based on their conditions."""
    from app.graph_db import get_driver
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Senior {phone: $phone})-[:REPORTED]->(:Symptom)-[:SUGGESTS]->(c:Condition)<-[:CAN_TREAT]-(d:Doctor)
            WHERE d.accepting_patients = true
            RETURN DISTINCT d.name AS name, d.specialty AS specialty, d.phone AS phone,
                   d.city AS city, d.rating AS rating, d.senior_care AS senior_care,
                   collect(DISTINCT c.name) AS conditions
            ORDER BY d.senior_care DESC, d.rating DESC
            LIMIT 10
        """, phone=phone)
        doctors = [dict(r) for r in result]

    return {"phone": phone, "recommended_doctors": doctors}


@router.get("/doctors-network/{phone}")
async def doctors_network(phone: str):
    """Get the full doctors graph for a senior — for interactive visualization.

    Shows: Senior → Symptoms → Conditions → Doctors → Clinics
    """
    from app.graph_db import get_driver
    driver = get_driver()
    nodes = []
    edges = []
    seen_nodes = set()

    def add_node(nid, label, ntype):
        if nid not in seen_nodes:
            seen_nodes.add(nid)
            nodes.append({"id": nid, "label": label, "type": ntype})

    with driver.session() as session:
        # Senior → Symptoms → Conditions → Doctors → Clinics
        result = session.run("""
            MATCH (s:Senior {phone: $phone})
            OPTIONAL MATCH (s)-[:REPORTED]->(sy:Symptom)
            OPTIONAL MATCH (sy)-[:SUGGESTS]->(c:Condition)
            OPTIONAL MATCH (c)<-[:CAN_TREAT]-(d:Doctor)
            WHERE d.accepting_patients = true AND d.rating IS NOT NULL AND d.rating >= 4.7
            OPTIONAL MATCH (d)-[:PRACTICES_AT]->(cl:Clinic)
            RETURN s, sy, c, d, cl
            LIMIT 100
        """, phone=phone)

        for r in result:
            if r["s"]:
                s = dict(r["s"])
                add_node(phone, s.get("name", ""), "Senior")

            if r["sy"]:
                sy = dict(r["sy"])
                sid = f"sym_{sy['name']}"
                add_node(sid, sy["name"], "Symptom")
                edges.append({"from": phone, "to": sid, "label": "REPORTED"})

            if r["c"]:
                c = dict(r["c"])
                cid = f"cond_{c['name']}"
                add_node(cid, c["name"], "Condition")
                if r["sy"]:
                    edges.append({"from": f"sym_{dict(r['sy'])['name']}", "to": cid, "label": "SUGGESTS"})

            if r["d"]:
                d = dict(r["d"])
                did = f"doc_{d['name']}"
                rating = f" ({d.get('rating', '?')}/5)" if d.get("rating") else ""
                add_node(did, d["name"] + rating, "Doctor")
                if r["c"]:
                    edges.append({"from": did, "to": f"cond_{dict(r['c'])['name']}", "label": "CAN_TREAT"})

            if r["cl"]:
                cl = dict(r["cl"])
                clid = f"clinic_{cl['name']}"
                city = f" ({cl.get('city', '')})" if cl.get("city") else ""
                add_node(clid, cl["name"] + city, "Clinic")
                if r["d"]:
                    edges.append({"from": f"doc_{dict(r['d'])['name']}", "to": clid, "label": "PRACTICES_AT"})

    # Deduplicate edges
    edge_set = set()
    unique_edges = []
    for e in edges:
        key = f"{e['from']}|{e['to']}|{e['label']}"
        if key not in edge_set:
            edge_set.add(key)
            unique_edges.append(e)

    return {"nodes": nodes, "edges": unique_edges}
