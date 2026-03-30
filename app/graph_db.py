"""
Neo4j graph database layer for CareGraph.

Graph model:
  (:Senior)-[:TAKES]->(:Medication)
  (:Senior)-[:REPORTED]->(:Symptom)
  (:Senior)-[:NEEDS]->(:Service)
  (:Senior)-[:HAS_CONTACT]->(:FamilyMember)
  (:Senior)-[:CHECKED_IN]->(:CheckIn)-[:DETECTED]->(:Concern)
  (:Medication)-[:INTERACTS_WITH]->(:Medication)
  (:Medication)-[:SIDE_EFFECT]->(:Symptom)
  (:Symptom)-[:SUGGESTS]->(:Condition)
  (:Service)-[:PROVIDED_BY]->(:Provider)
  (:CheckIn)-[:TRIGGERED]->(:Alert)-[:NOTIFIED]->(:FamilyMember)
"""

from __future__ import annotations

import logging
from typing import Any

from neo4j import GraphDatabase

from app.config import settings

logger = logging.getLogger(__name__)

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        logger.info("Neo4j driver initialized")
    return _driver


def _session(driver):
    """Open a session against the configured database (required for Neo4j Aura)."""
    db = (settings.neo4j_database or "").strip()
    if db:
        return driver.session(database=db)
    return driver.session()


def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def run_query(query: str, params: dict | None = None) -> list[dict]:
    """Run a Cypher query and return results as list of dicts."""
    driver = get_driver()
    with _session(driver) as session:
        result = session.run(query, params or {})
        return [dict(record) for record in result]


def run_write(query: str, params: dict | None = None) -> None:
    """Run a write Cypher query."""
    driver = get_driver()
    with _session(driver) as session:
        session.run(query, params or {})


# ── Schema Setup ──

def setup_schema():
    """Create constraints and indexes for the graph."""
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Senior) REQUIRE s.phone IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Medication) REQUIRE m.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (sy:Symptom) REQUIRE sy.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Condition) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Provider) REQUIRE p.name IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (ci:CheckIn) ON (ci.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (a:Alert) ON (a.timestamp)",
    ]
    for q in constraints:
        try:
            run_write(q)
        except Exception as e:
            logger.debug("Schema setup: %s", e)
    logger.info("Neo4j schema ready")


# ── Senior CRUD ──

def create_senior(name: str, phone: str, medications: list[str],
                  checkin_schedule: str = "09:00", notes: str = "",
                  emergency_contacts: list[dict] = None) -> dict:
    """Create a Senior node with medications and emergency contacts."""
    run_write("""
        MERGE (s:Senior {phone: $phone})
        SET s.name = $name, s.checkin_schedule = $schedule, s.notes = $notes,
            s.created_at = datetime()
    """, {"phone": phone, "name": name, "schedule": checkin_schedule, "notes": notes})

    # Create medication nodes and relationships
    for med in medications:
        run_write("""
            MERGE (m:Medication {name: $med})
            WITH m
            MATCH (s:Senior {phone: $phone})
            MERGE (s)-[:TAKES]->(m)
        """, {"med": med, "phone": phone})

    # Create emergency contacts
    for contact in (emergency_contacts or []):
        c_name = contact.get("name", "")
        c_phone = contact.get("phone", "")
        c_relation = contact.get("relation", "")
        if c_name or c_phone:
            run_write("""
                MERGE (f:FamilyMember {phone: $c_phone})
                SET f.name = $c_name, f.relation = $c_relation
                WITH f
                MATCH (s:Senior {phone: $phone})
                MERGE (s)-[:HAS_CONTACT]->(f)
            """, {"c_phone": c_phone, "c_name": c_name, "c_relation": c_relation, "phone": phone})

    return get_senior(phone)


def get_senior(phone: str) -> dict | None:
    """Get a senior with their medications and contacts."""
    results = run_query("""
        MATCH (s:Senior {phone: $phone})
        OPTIONAL MATCH (s)-[:TAKES]->(m:Medication)
        OPTIONAL MATCH (s)-[:HAS_CONTACT]->(f:FamilyMember)
        RETURN s.name AS name, s.phone AS phone, s.checkin_schedule AS checkin_schedule,
               s.notes AS notes,
               collect(DISTINCT m.name) AS medications,
               collect(DISTINCT {name: f.name, phone: f.phone, relation: f.relation}) AS emergency_contacts
    """, {"phone": phone})
    if not results:
        return None
    r = results[0]
    # Clean up null contacts
    contacts = [c for c in r["emergency_contacts"] if c.get("name") or c.get("phone")]
    return {
        "name": r["name"], "phone": r["phone"],
        "medications": r["medications"],
        "checkin_schedule": r["checkin_schedule"] or "09:00",
        "notes": r["notes"] or "",
        "emergency_contacts": contacts,
    }


def list_seniors() -> list[dict]:
    """List all seniors with their medications."""
    results = run_query("""
        MATCH (s:Senior)
        OPTIONAL MATCH (s)-[:TAKES]->(m:Medication)
        OPTIONAL MATCH (s)-[:HAS_CONTACT]->(f:FamilyMember)
        RETURN s.name AS name, s.phone AS phone, s.checkin_schedule AS checkin_schedule,
               s.notes AS notes,
               collect(DISTINCT m.name) AS medications,
               collect(DISTINCT {name: f.name, phone: f.phone, relation: f.relation}) AS emergency_contacts
        ORDER BY s.name
    """)
    seniors = []
    for r in results:
        contacts = [c for c in r["emergency_contacts"] if c.get("name") or c.get("phone")]
        seniors.append({
            "name": r["name"], "phone": r["phone"],
            "medications": r["medications"],
            "checkin_schedule": r["checkin_schedule"] or "09:00",
            "notes": r["notes"] or "",
            "emergency_contacts": contacts,
        })
    return seniors


def delete_senior(phone: str) -> bool:
    """Delete a senior and their relationships."""
    results = run_query("MATCH (s:Senior {phone: $phone}) RETURN s", {"phone": phone})
    if not results:
        return False
    run_write("""
        MATCH (s:Senior {phone: $phone})
        OPTIONAL MATCH (s)-[r]-()
        DELETE r, s
    """, {"phone": phone})
    return True


# ── Check-ins ──

def store_checkin(senior_phone: str, call_id: str, timestamp: str,
                  transcript: str, mood: str, wellness_score: int,
                  medication_taken: bool | None, concerns: list[str],
                  service_requests: list[dict], summary: str) -> str:
    """Store a check-in and create symptom/concern relationships."""
    checkin_key = f"{senior_phone}:{timestamp}"

    run_write("""
        MATCH (s:Senior {phone: $phone})
        CREATE (ci:CheckIn {
            key: $key, call_id: $call_id, timestamp: $timestamp,
            transcript: $transcript, mood: $mood, wellness_score: $score,
            medication_taken: $med_taken, summary: $summary
        })
        MERGE (s)-[:CHECKED_IN]->(ci)
    """, {
        "phone": senior_phone, "key": checkin_key, "call_id": call_id,
        "timestamp": timestamp, "transcript": transcript, "mood": mood,
        "score": wellness_score, "med_taken": medication_taken, "summary": summary,
    })

    # Create concern/symptom nodes
    for concern in concerns:
        run_write("""
            MERGE (sy:Symptom {name: $concern})
            WITH sy
            MATCH (ci:CheckIn {key: $key})
            MERGE (ci)-[:DETECTED]->(sy)
            WITH sy
            MATCH (s:Senior {phone: $phone})
            MERGE (s)-[:REPORTED]->(sy)
        """, {"concern": concern, "key": checkin_key, "phone": senior_phone})

    # Create service request nodes
    for svc in service_requests:
        run_write("""
            MERGE (sv:Service {type: $type})
            SET sv.label = $label
            WITH sv
            MATCH (ci:CheckIn {key: $key})
            MERGE (ci)-[:REQUESTED]->(sv)
            WITH sv
            MATCH (s:Senior {phone: $phone})
            MERGE (s)-[:NEEDS]->(sv)
        """, {"type": svc["type"], "label": svc.get("label", ""), "key": checkin_key, "phone": senior_phone})

    return checkin_key


def get_checkins(senior_phone: str) -> list[dict]:
    """Get check-ins for a senior."""
    results = run_query("""
        MATCH (s:Senior {phone: $phone})-[:CHECKED_IN]->(ci:CheckIn)
        OPTIONAL MATCH (ci)-[:DETECTED]->(sy:Symptom)
        OPTIONAL MATCH (ci)-[:REQUESTED]->(sv:Service)
        RETURN ci.key AS key, ci.call_id AS call_id, ci.timestamp AS timestamp,
               ci.transcript AS transcript, ci.mood AS mood,
               ci.wellness_score AS wellness_score, ci.medication_taken AS medication_taken,
               ci.summary AS summary,
               collect(DISTINCT sy.name) AS concerns,
               collect(DISTINCT {type: sv.type, label: sv.label}) AS service_requests
        ORDER BY ci.timestamp DESC
    """, {"phone": senior_phone})

    checkins = []
    for r in results:
        svcs = [s for s in r["service_requests"] if s.get("type")]
        checkins.append({
            "senior_phone": senior_phone,
            "call_id": r["call_id"], "timestamp": r["timestamp"],
            "transcript": r["transcript"] or "", "mood": r["mood"] or "",
            "wellness_score": r["wellness_score"] or 0,
            "medication_taken": r["medication_taken"],
            "concerns": r["concerns"], "service_requests": svcs,
            "summary": r["summary"] or "",
        })
    return checkins


def get_all_checkins() -> list[dict]:
    """Get all check-ins across all seniors."""
    results = run_query("""
        MATCH (s:Senior)-[:CHECKED_IN]->(ci:CheckIn)
        RETURN s.phone AS senior_phone, ci.call_id AS call_id,
               ci.timestamp AS timestamp, ci.mood AS mood,
               ci.wellness_score AS wellness_score, ci.medication_taken AS medication_taken,
               ci.summary AS summary
        ORDER BY ci.timestamp DESC
        LIMIT 100
    """)
    return [dict(r) for r in results]


def get_latest_checkins() -> list[dict]:
    """Get the latest check-in per senior."""
    results = run_query("""
        MATCH (s:Senior)-[:CHECKED_IN]->(ci:CheckIn)
        WITH s, ci ORDER BY ci.timestamp DESC
        WITH s, collect(ci)[0] AS latest
        RETURN s.phone AS senior_phone, s.name AS senior_name,
               latest.mood AS mood, latest.wellness_score AS wellness_score,
               latest.medication_taken AS medication_taken,
               latest.timestamp AS timestamp, latest.summary AS summary
    """)
    return [dict(r) for r in results]


# ── Alerts ──

def store_alert(alert_id: str, senior_phone: str, senior_name: str,
                timestamp: str, alert_type: str, severity: str,
                message: str) -> None:
    """Store an alert and link to senior."""
    run_write("""
        MATCH (s:Senior {phone: $phone})
        CREATE (a:Alert {
            id: $id, timestamp: $timestamp, alert_type: $type,
            severity: $severity, message: $message, acknowledged: false,
            senior_name: $senior_name
        })
        MERGE (s)-[:HAS_ALERT]->(a)
    """, {
        "phone": senior_phone, "id": alert_id, "timestamp": timestamp,
        "type": alert_type, "severity": severity, "message": message,
        "senior_name": senior_name,
    })


def get_alerts(acknowledged: bool = False) -> list[dict]:
    """Get alerts, optionally including acknowledged ones."""
    if acknowledged:
        query = """
            MATCH (s:Senior)-[:HAS_ALERT]->(a:Alert)
            RETURN a.id AS id, s.phone AS senior_phone, a.senior_name AS senior_name,
                   a.timestamp AS timestamp, a.alert_type AS alert_type,
                   a.severity AS severity, a.message AS message, a.acknowledged AS acknowledged
            ORDER BY a.timestamp DESC
        """
    else:
        query = """
            MATCH (s:Senior)-[:HAS_ALERT]->(a:Alert)
            WHERE a.acknowledged = false
            RETURN a.id AS id, s.phone AS senior_phone, a.senior_name AS senior_name,
                   a.timestamp AS timestamp, a.alert_type AS alert_type,
                   a.severity AS severity, a.message AS message, a.acknowledged AS acknowledged
            ORDER BY a.timestamp DESC
        """
    return [dict(r) for r in run_query(query)]


def acknowledge_alert(alert_id: str) -> dict | None:
    """Mark an alert as acknowledged."""
    results = run_query("MATCH (a:Alert {id: $id}) RETURN a", {"id": alert_id})
    if not results:
        return None
    run_write("MATCH (a:Alert {id: $id}) SET a.acknowledged = true", {"id": alert_id})
    return {"id": alert_id, "acknowledged": True}


# ── Graph Intelligence Queries ──

def find_drug_interactions(senior_phone: str) -> list[dict]:
    """Find potential drug interactions for a senior's medications."""
    return run_query("""
        MATCH (s:Senior {phone: $phone})-[:TAKES]->(m1:Medication)
        MATCH (m1)-[:INTERACTS_WITH]-(m2:Medication)
        WHERE (s)-[:TAKES]->(m2)
        RETURN m1.name AS drug1, m2.name AS drug2,
               m1.name + ' ↔ ' + m2.name AS interaction
    """, {"phone": senior_phone})


def find_similar_symptoms(senior_phone: str) -> list[dict]:
    """Find other seniors who reported similar symptoms."""
    return run_query("""
        MATCH (s1:Senior {phone: $phone})-[:REPORTED]->(sy:Symptom)<-[:REPORTED]-(s2:Senior)
        WHERE s1 <> s2
        RETURN sy.name AS symptom, s2.name AS other_senior, s2.phone AS other_phone
    """, {"phone": senior_phone})


def find_medication_side_effects(senior_phone: str) -> list[dict]:
    """Check if reported symptoms match known medication side effects."""
    return run_query("""
        MATCH (s:Senior {phone: $phone})-[:TAKES]->(m:Medication)-[:SIDE_EFFECT]->(sy:Symptom)
        WHERE (s)-[:REPORTED]->(sy)
        RETURN m.name AS medication, sy.name AS symptom,
               'Reported symptom may be a side effect of ' + m.name AS insight
    """, {"phone": senior_phone})


def get_care_network(senior_phone: str) -> dict:
    """Get the full care network graph for a senior (for visualization)."""
    nodes = []
    edges = []

    # Senior + medications
    results = run_query("""
        MATCH (s:Senior {phone: $phone})
        OPTIONAL MATCH (s)-[:TAKES]->(m:Medication)
        OPTIONAL MATCH (s)-[:HAS_CONTACT]->(f:FamilyMember)
        OPTIONAL MATCH (s)-[:REPORTED]->(sy:Symptom)
        OPTIONAL MATCH (s)-[:NEEDS]->(sv:Service)
        RETURN s, collect(DISTINCT m) AS meds, collect(DISTINCT f) AS contacts,
               collect(DISTINCT sy) AS symptoms, collect(DISTINCT sv) AS services
    """, {"phone": senior_phone})

    if not results:
        return {"nodes": [], "edges": []}

    r = results[0]
    senior_node = dict(r["s"])
    nodes.append({"id": senior_phone, "label": senior_node.get("name", ""), "type": "Senior"})

    for m in r["meds"]:
        md = dict(m)
        nodes.append({"id": f"med_{md['name']}", "label": md["name"], "type": "Medication"})
        edges.append({"from": senior_phone, "to": f"med_{md['name']}", "label": "TAKES"})

    for f in r["contacts"]:
        fd = dict(f)
        nodes.append({"id": f"fam_{fd.get('phone','')}", "label": fd.get("name", ""), "type": "FamilyMember"})
        edges.append({"from": senior_phone, "to": f"fam_{fd.get('phone','')}", "label": "HAS_CONTACT"})

    for sy in r["symptoms"]:
        sd = dict(sy)
        nodes.append({"id": f"sym_{sd['name']}", "label": sd["name"], "type": "Symptom"})
        edges.append({"from": senior_phone, "to": f"sym_{sd['name']}", "label": "REPORTED"})

    for sv in r["services"]:
        svd = dict(sv)
        nodes.append({"id": f"svc_{svd.get('type','')}", "label": svd.get("label", svd.get("type", "")), "type": "Service"})
        edges.append({"from": senior_phone, "to": f"svc_{svd.get('type','')}", "label": "NEEDS"})

    return {"nodes": nodes, "edges": edges}


def get_seniors_by_symptom(symptom: str) -> list[dict]:
    """Find all seniors who reported a specific symptom."""
    return run_query("""
        MATCH (s:Senior)-[:REPORTED]->(sy:Symptom {name: $symptom})
        RETURN s.name AS name, s.phone AS phone
    """, {"symptom": symptom})


def get_seniors_by_medication(medication: str) -> list[dict]:
    """Find all seniors taking a specific medication."""
    return run_query("""
        MATCH (s:Senior)-[:TAKES]->(m:Medication {name: $med})
        RETURN s.name AS name, s.phone AS phone
    """, {"med": medication})


# ── Drug Interaction Knowledge ──

def add_drug_interaction(drug1: str, drug2: str, description: str = "") -> None:
    """Add a known drug interaction to the graph."""
    run_write("""
        MERGE (m1:Medication {name: $drug1})
        MERGE (m2:Medication {name: $drug2})
        MERGE (m1)-[:INTERACTS_WITH {description: $desc}]->(m2)
    """, {"drug1": drug1, "drug2": drug2, "desc": description})


def add_side_effect(medication: str, symptom: str) -> None:
    """Add a known side effect to the graph."""
    run_write("""
        MERGE (m:Medication {name: $med})
        MERGE (sy:Symptom {name: $symptom})
        MERGE (m)-[:SIDE_EFFECT]->(sy)
    """, {"med": medication, "symptom": symptom})


def add_symptom_condition(symptom: str, condition: str) -> None:
    """Add symptom-condition relationship to the graph."""
    run_write("""
        MERGE (sy:Symptom {name: $symptom})
        MERGE (c:Condition {name: $condition})
        MERGE (sy)-[:SUGGESTS]->(c)
    """, {"symptom": symptom, "condition": condition})
