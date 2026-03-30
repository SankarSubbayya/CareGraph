# CareGraph — Requirements Document

## HackWithBay 2.0 | Theme: Graph-Powered Applications with Neo4j + RocketRide AI

**Track chosen:** Smart Healthcare Diagnosis Graph (#8)

---

## Hackathon Overview

### Core Challenge
Design and build an innovative application that:
- Uses **Neo4j** as the primary database to model and query connected data
- Integrates **RocketRide AI** to add intelligence, automation, or generative capabilities
- Demonstrates how graph-based systems + AI can unlock insights, improve decisions, or enhance user experience

### Timeline
| Phase | Duration |
|-------|----------|
| On-site build | 8 hours — develop a functional prototype |
| Extended development | Additional 2-3 days — refine, scale, and polish |

### Evaluation Criteria
Projects will be judged on:
1. **Effective use of Neo4j** — graph structure, queries, insights
2. **Effective use of RocketRide AI** — intelligence, automation, reasoning
3. **Innovation and originality**
4. **Technical complexity**
5. **Real-world impact**
6. **Demo and presentation quality**

### Winning Strategy (from problem statement)
- Use Neo4j for **deep relationship modeling**, not just storing data
- Use RocketRide AI for **decision-making or intelligence**, not just a chatbot
- Combine both into a **single meaningful workflow**
- Superficial usage (e.g., simple chatbot + unused graph) will lead to disqualification

---

## Problem Statement

Senior care involves complex, interconnected data — medications, symptoms, conditions, caregivers, and services — that traditional databases fail to model effectively. Drug interactions go undetected, side effects are missed, and care coordination across family members and providers is fragmented.

CareGraph uses Neo4j to model the complete care network as a knowledge graph and RocketRide AI to reason over it — detecting risks, explaining interactions, and generating personalized care plans.

---

## Mandatory Requirements

| # | Requirement | How CareGraph Fulfills It |
|---|-------------|---------------------------|
| 1 | Use Neo4j for graph data modeling and querying | Core database — seniors, medications, symptoms, conditions, check-ins, alerts, family members, and services are all graph nodes with typed relationships |
| 2 | Use RocketRide AI for at least one core intelligent feature | Four RocketRide pipelines (.pipe files): transcript analysis, drug interaction explanation, care plan generation, and condition suggestion — each uses Webhook → Prompt → Gemini LLM → Response flow |
| 3 | Deep integration of both technologies into core workflow | Every check-in flows through Neo4j (store & query relationships) AND RocketRide AI pipelines (analyze & reason) — neither is superficial |

---

## Functional Requirements

### FR-1: Senior Management
- Add a senior with name, phone, age, medications, emergency contacts, and conditions
- List all seniors
- Delete a senior and their associated graph data
- Each senior creates graph nodes for themselves, their medications, and their contacts

### FR-2: Check-in Processing
- Simulate a check-in by providing what the senior said (transcript)
- RocketRide AI analyzes the transcript to extract symptoms, mood, and urgency
- Extracted symptoms are stored as graph nodes linked to the check-in and senior
- View check-in history per senior
- View latest check-in across all seniors

### FR-3: Drug Interaction Detection
- When a senior takes multiple medications, Neo4j stores `(:Medication)-[:INTERACTS_WITH]->(:Medication)` edges
- Query all drug interactions for a given senior via graph traversal
- RocketRide AI explains the clinical risk of each interaction in plain language

### FR-4: Side Effect Matching
- Neo4j models `(:Medication)-[:SIDE_EFFECT]->(:Symptom)` relationships
- When a senior reports a symptom, the system matches it against known side effects of their medications
- Graph path: Senior → TAKES → Medication → SIDE_EFFECT → Symptom ← REPORTED ← Senior

### FR-5: Condition Suggestion
- Neo4j models `(:Symptom)-[:SUGGESTS]->(:Condition)` relationships
- When symptoms cluster, the graph suggests possible conditions
- RocketRide AI provides reasoning and next-step recommendations

### FR-6: Care Plan Generation
- Query the senior's full care network from Neo4j (medications, symptoms, conditions, contacts, services)
- Pass the structured graph data to RocketRide AI
- Generate a personalized care recommendation plan

### FR-7: Graph Intelligence Queries
- Full care network visualization for a senior
- Find seniors who share the same symptoms (community detection)
- Find all seniors on a given medication
- Find all seniors reporting a given symptom

### FR-8: Alert Engine
- Check-ins can trigger alerts based on urgency, detected symptoms, or drug interactions
- Alerts are stored as graph nodes linked to the check-in: `(:CheckIn)-[:TRIGGERED]->(:Alert)`
- View active alerts
- Acknowledge alerts

### FR-9: Dashboard
- Web-based dashboard showing seniors, check-ins, alerts, and graph visualizations
- Interactive care network graph per senior
- Chart-based analytics

---

## Non-Functional Requirements

| # | Requirement | Details |
|---|-------------|---------|
| NFR-1 | Performance | API responses under 2 seconds for graph queries |
| NFR-2 | Usability | Dashboard usable by non-technical family members |
| NFR-3 | Portability | Runs locally with Docker (Neo4j) + Python |
| NFR-4 | Demo-ready | Seed script provides realistic demo data out of the box |
| NFR-5 | Extensibility | Graph model can be extended with new node/relationship types without schema migration |

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Graph Database | **Neo4j 5** | Stores and queries the care network graph |
| AI Orchestration | **RocketRide AI** | Pipeline orchestration via `.pipe` files — Webhook → Prompt → LLM → Response |
| LLM | **Gemini 2.5 Flash** | Language model behind RocketRide pipelines |
| Backend | **FastAPI** (Python) | REST API serving frontend and processing logic |
| Frontend | **HTML/JS + Chart.js** | Dashboard and graph visualization |
| Package Manager | **uv** | Python dependency management |
| Containerization | **Docker** | Neo4j instance |

---

## RocketRide AI Pipelines

### Architecture

Each pipeline is a `.pipe` file (JSON) that defines a visual flow in the RocketRide VS Code extension:

```
Webhook (Source) → Prompt (Template) → Gemini 2.5 Flash (LLM) → Response (Output)
```

### Pipeline Inventory

| Pipeline | File | Input | Output |
|----------|------|-------|--------|
| Check-in Analysis | `checkin_analysis.pipe` | Senior name + medications + transcript | JSON: mood, wellness_score, symptoms, concerns, service_needs, recommendation |
| Drug Interaction | `drug_interaction.pipe` | Drug pair names | Plain text: severity, symptoms to watch, caregiver actions |
| Care Recommendation | `care_recommendation.pipe` | Full graph context (meds, symptoms, checkins, interactions) | Plain text: top 3 recommendations, doctor concerns, schedule adjustments |
| Condition Suggestion | `condition_suggestion.pipe` | List of symptoms | JSON array: condition, likelihood, recommended action |

### Integration Flow

```
1. Backend receives API request (e.g., /api/graph/drug-interactions/{phone})
2. Neo4j query fetches graph relationships (e.g., INTERACTS_WITH edges)
3. Graph data formatted as text input
4. POST to RocketRide webhook: {ROCKETRIDE_URI}/webhook with {"text": "..."}
5. RocketRide pipeline processes: Prompt template → Gemini LLM
6. Response extracted from: resp["data"]["objects"]["body"]["answers"][0]
7. JSON/text parsed and returned to frontend
```

### Fallback Behavior

If RocketRide is unavailable (no API key, server down), the system:
- Still performs all Neo4j graph queries (drug interactions, side effects, etc.)
- Returns empty AI explanations — graph intelligence works without AI
- Logs warning for debugging

---

## Graph Data Model

```
(:Senior)-[:TAKES]->(:Medication)
(:Senior)-[:REPORTED]->(:Symptom)
(:Senior)-[:CHECKED_IN]->(:CheckIn)-[:DETECTED]->(:Symptom)
(:Senior)-[:HAS_CONTACT]->(:FamilyMember)
(:Senior)-[:NEEDS]->(:Service)
(:Medication)-[:INTERACTS_WITH]->(:Medication)
(:Medication)-[:SIDE_EFFECT]->(:Symptom)
(:Symptom)-[:SUGGESTS]->(:Condition)
(:CheckIn)-[:TRIGGERED]->(:Alert)
```

---

## Key Demo Scenarios

| Scenario | Neo4j Role | RocketRide AI Role |
|----------|-----------|-------------------|
| Margaret takes Metformin + Lisinopril | Detects `INTERACTS_WITH` relationship | Explains the interaction risk |
| Dorothy reports dizziness | Matches symptom to Lisinopril via `SIDE_EFFECT` edge | Suggests talking to doctor |
| 3 seniors report similar symptoms | Finds shared symptom paths in graph | Identifies potential cause |
| New medication added | Checks all `INTERACTS_WITH` edges | Flags concerns proactively |

---

## API Endpoints

### Seniors
- `POST /api/seniors` — Add senior (creates graph nodes)
- `GET /api/seniors` — List all seniors
- `DELETE /api/seniors/{phone}` — Remove senior

### Check-ins
- `POST /api/checkins/simulate/{phone}` — Simulate a check-in
- `GET /api/checkins/{phone}` — Check-in history
- `GET /api/checkins/latest/all` — Latest per senior

### Graph Intelligence
- `GET /api/graph/care-network/{phone}` — Full care network
- `GET /api/graph/drug-interactions/{phone}` — Drug interactions + AI explanation
- `GET /api/graph/side-effects/{phone}` — Symptom-medication matches
- `GET /api/graph/similar-symptoms/{phone}` — Seniors with same symptoms
- `GET /api/graph/care-recommendation/{phone}` — AI-generated care plan
- `GET /api/graph/seniors-by-symptom/{symptom}` — Find seniors by symptom
- `GET /api/graph/seniors-by-medication/{med}` — Find seniors by medication

### Alerts
- `GET /api/alerts` — Active alerts
- `PUT /api/alerts/{id}/acknowledge` — Acknowledge alert

---

## Deliverables (per hackathon rules)

- [ ] Working prototype (live or local demo)
- [ ] Source code repository
- [ ] Project description including:
  - [ ] Problem statement
  - [ ] How Neo4j is used
  - [ ] How RocketRide AI is integrated
- [ ] Pitch deck or demo video (optional)

---

## How CareGraph Maps to Evaluation Criteria

| Criteria | CareGraph Implementation |
|----------|--------------------------|
| **Effective use of Neo4j** | 9 node types, 9 relationship types; Cypher queries for drug interactions, side-effect matching, symptom community detection, care network traversal |
| **Effective use of RocketRide AI** | 4 AI features deeply integrated: transcript analysis, drug interaction explanation, condition suggestion, care plan generation — all fed by graph context |
| **Innovation and originality** | Graph-powered senior care is underserved; combining medication knowledge graph with AI reasoning for elderly safety is novel |
| **Technical complexity** | Full-stack app: Neo4j graph modeling, RocketRide AI integration, FastAPI backend, real-time dashboard, alert engine |
| **Real-world impact** | Directly addresses medication safety for seniors — drug interactions cause 125,000+ deaths/year in the US alone |
| **Demo quality** | Seed data provides realistic scenarios; dashboard visualizes the graph; each demo scenario shows Neo4j + AI working together |
