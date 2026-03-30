"""Alert engine — evaluate check-in data and generate alerts.

When alerts fire, looks up the senior's emergency contacts from Neo4j
and includes notification targets in the alert response.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.graph_db import store_alert

logger = logging.getLogger(__name__)


def _get_family_contacts(senior_phone: str) -> list[dict]:
    """Look up emergency contacts for a senior from Neo4j."""
    try:
        from app.graph_db import get_driver
        driver = get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (s:Senior {phone: $phone})-[:HAS_CONTACT]->(f:FamilyMember)
                RETURN f.name AS name, f.phone AS phone, f.relation AS relation
            """, phone=senior_phone)
            return [dict(r) for r in result]
    except Exception:
        return []


def evaluate_checkin(checkin: dict, senior_name: str = "") -> list[dict]:
    """Evaluate a check-in and return alerts."""
    alerts = []
    now = datetime.now(timezone.utc).isoformat()
    who = senior_name or checkin.get("senior_phone", "")
    phone = checkin.get("senior_phone", "")

    emergency_words = {"fall", "fell", "fallen", "chest pain", "can't breathe", "emergency", "stroke", "bleeding"}
    for concern in checkin.get("concerns", []):
        if concern.lower() in emergency_words:
            alert = {"id": f"{phone}:{now}:emergency", "senior_phone": phone, "senior_name": senior_name,
                     "timestamp": now, "alert_type": "emergency", "severity": "critical",
                     "message": f"Emergency: {concern}. Immediate attention needed for {who}."}
            alerts.append(alert)

    if checkin.get("mood") == "concerning" or checkin.get("wellness_score", 10) < 4:
        alert = {"id": f"{phone}:{now}:low_mood", "senior_phone": phone, "senior_name": senior_name,
                 "timestamp": now, "alert_type": "low_mood", "severity": "high",
                 "message": f"{who} reported low mood (wellness: {checkin.get('wellness_score', 0)}/10)."}
        alerts.append(alert)

    if checkin.get("medication_taken") is False:
        alert = {"id": f"{phone}:{now}:missed_med", "senior_phone": phone, "senior_name": senior_name,
                 "timestamp": now, "alert_type": "missed_medication", "severity": "medium",
                 "message": f"{who} has not taken their medications today."}
        alerts.append(alert)

    if "loneliness" in checkin.get("concerns", []):
        alert = {"id": f"{phone}:{now}:loneliness", "senior_phone": phone, "senior_name": senior_name,
                 "timestamp": now, "alert_type": "loneliness", "severity": "medium",
                 "message": f"{who} expressed feelings of loneliness."}
        alerts.append(alert)

    for svc in checkin.get("service_requests", []):
        svc_type = svc.get("type", "other")
        severity = "critical" if svc_type == "medical_emergency" else "medium"
        alert = {"id": f"{phone}:{now}:service_{svc_type}", "senior_phone": phone, "senior_name": senior_name,
                 "timestamp": now, "alert_type": "service_request", "severity": severity,
                 "message": f"{who} requested help: {svc.get('label', svc_type)}. {svc.get('details', '')}"}
        alerts.append(alert)

    # Look up family contacts to notify
    contacts = _get_family_contacts(phone) if alerts else []

    # Store in Neo4j and add notification info
    for a in alerts:
        # Add who gets notified based on severity
        if a["severity"] == "critical":
            a["notify"] = contacts  # Notify ALL contacts for emergencies
        elif a["severity"] == "high":
            a["notify"] = contacts[:1]  # Primary contact for high severity
        else:
            a["notify"] = []  # Medium/low — dashboard only

        if a["notify"]:
            names = ", ".join(f"{c['name']} ({c['relation']})" for c in a["notify"])
            a["notification_message"] = f"Notifying: {names}"
            logger.warning("NOTIFY %s for %s: %s", names, a["senior_name"], a["message"])

        try:
            store_alert(a["id"], a["senior_phone"], a["senior_name"],
                       a["timestamp"], a["alert_type"], a["severity"], a["message"])
        except Exception as e:
            logger.warning("Failed to store alert in Neo4j: %s", e)
        logger.warning("ALERT [%s] %s: %s", a["severity"].upper(), a["alert_type"], a["message"])

    return alerts
