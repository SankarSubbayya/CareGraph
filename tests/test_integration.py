"""Integration tests — hit real Neo4j Aura database.

These tests verify the full pipeline: graph_db queries, analysis, and API endpoints.
Requires seeded data (run scripts/seed_data.py first).
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from app.graph_db import (
    get_senior,
    list_seniors,
    find_drug_interactions,
    find_medication_side_effects,
    find_similar_symptoms,
    get_care_network,
    get_checkins,
    get_alerts,
    get_senior_checkin_wellness,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Neo4j graph queries
# ---------------------------------------------------------------------------

class TestGraphDB:
    """Tests that query Neo4j Aura directly."""

    def test_list_seniors(self):
        seniors = list_seniors()
        assert len(seniors) >= 3
        names = [s["name"] for s in seniors]
        assert "Margaret Johnson" in names
        assert "Robert Chen" in names
        assert "Dorothy Williams" in names

    def test_get_senior_by_phone(self):
        senior = get_senior("+14155551001")
        assert senior is not None
        assert senior["name"] == "Margaret Johnson"
        assert "Metformin 500mg" in senior["medications"]
        assert "Lisinopril 10mg" in senior["medications"]

    def test_get_senior_not_found(self):
        senior = get_senior("+10000000000")
        assert senior is None

    def test_drug_interactions_margaret(self):
        interactions = find_drug_interactions("+14155551001")
        assert len(interactions) >= 2
        drug_pairs = [(i["drug1"], i["drug2"]) for i in interactions]
        assert any("Metformin" in d1 and "Lisinopril" in d2
                    for d1, d2 in drug_pairs)

    def test_side_effects_dorothy(self):
        side_effects = find_medication_side_effects("+14155551003")
        assert len(side_effects) >= 1
        assert any(se["symptom"] == "dizzy" and "Lisinopril" in se["medication"]
                    for se in side_effects)

    def test_care_network(self):
        network = get_care_network("+14155551003")
        assert "nodes" in network
        assert "edges" in network
        assert len(network["nodes"]) >= 3
        assert len(network["edges"]) >= 2

    def test_checkin_history(self):
        checkins = get_checkins("+14155551001")
        assert len(checkins) >= 1

    def test_alerts_exist(self):
        alerts = get_alerts()
        assert len(alerts) >= 1

    def test_senior_checkin_wellness_shape(self):
        rows = get_senior_checkin_wellness(days_threshold=7)
        assert len(rows) >= 3
        for r in rows:
            assert "phone" in r and "name" in r
            assert "at_risk" in r and isinstance(r["at_risk"], bool)
            assert r.get("days_threshold") == 7


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestAPI:
    """Tests that hit FastAPI endpoints."""

    def test_root_serves_dashboard(self):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_list_seniors_endpoint(self):
        resp = client.get("/api/seniors")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3

    def test_get_senior_endpoint(self):
        resp = client.get("/api/seniors/+14155551001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Margaret Johnson"

    def test_get_senior_not_found(self):
        resp = client.get("/api/seniors/+10000000000")
        assert resp.status_code == 404

    def test_checkins_endpoint(self):
        resp = client.get("/api/checkins/+14155551001")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    def test_latest_checkins_endpoint(self):
        resp = client.get("/api/checkins/latest/all")
        assert resp.status_code == 200

    def test_alerts_endpoint(self):
        resp = client.get("/api/alerts")
        assert resp.status_code == 200

    def test_wellness_overview_endpoint(self):
        resp = client.get("/api/seniors/wellness-overview?days_threshold=7")
        assert resp.status_code == 200
        data = resp.json()
        assert "at_risk_count" in data and "seniors" in data
        assert isinstance(data["seniors"], list)
        assert len(data["seniors"]) >= 3
        assert data["days_threshold"] == 7

    def test_drug_interactions_endpoint(self):
        resp = client.get("/api/graph/drug-interactions/+14155551001")
        assert resp.status_code == 200
        data = resp.json()
        assert "interactions" in data

    def test_side_effects_endpoint(self):
        resp = client.get("/api/graph/side-effects/+14155551003")
        assert resp.status_code == 200

    def test_care_network_endpoint(self):
        resp = client.get("/api/graph/care-network/+14155551003")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data

    def test_simulate_checkin(self):
        resp = client.post(
            "/api/checkins/simulate/+14155551001",
            params={"transcript": "I'm feeling good today. Yes took my meds."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processed"
        assert "analysis" in data

    def test_simulate_checkin_not_found(self):
        resp = client.post(
            "/api/checkins/simulate/+10000000000",
            params={"transcript": "hello"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# End-to-end pipeline test
# ---------------------------------------------------------------------------

class TestPipeline:
    """Full pipeline: transcript → analyze → graph match."""

    def test_dizzy_matches_lisinopril_side_effect(self):
        """Dorothy reports dizziness → should match Lisinopril side effect in graph."""
        # Simulate check-in with dizziness
        resp = client.post(
            "/api/checkins/simulate/+14155551003",
            params={"transcript": "I've been feeling dizzy all morning."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "dizzy" in data["analysis"]["concerns"] or data["analysis"]["mood"] in ("sad", "concerning")

        # Check graph for side effect match
        side_effects = find_medication_side_effects("+14155551003")
        lisinopril_match = [se for se in side_effects
                            if se["symptom"] == "dizzy" and "Lisinopril" in se["medication"]]
        assert len(lisinopril_match) >= 1

    def test_fall_triggers_emergency_pipeline(self):
        """Margaret reports a fall → emergency alert should be generated."""
        resp = client.post(
            "/api/checkins/simulate/+14155551001",
            params={"transcript": "I fell in the bathroom. My hip hurts badly. I forgot my medications."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["alerts"] >= 1
        assert data["analysis"]["medication_taken"] is False
        assert "fell" in data["analysis"]["concerns"]
