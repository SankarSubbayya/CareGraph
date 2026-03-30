# CareGraph

Graph-powered senior care intelligence with Neo4j + RocketRide AI. Models the complete care network — seniors, medications, symptoms, conditions, services, and family — as a knowledge graph, then uses AI to detect drug interactions, side effects, and generate care recommendations.

## Architecture

```mermaid
flowchart TB
    subgraph Users["👥 Users"]
        Family["👨‍👩‍👧 Family\n(Dashboard)"]
    end

    subgraph Neo4j["🔗 Neo4j (Graph Database)"]
        Senior["(:Senior)"]
        Med["(:Medication)"]
        Sym["(:Symptom)"]
        Cond["(:Condition)"]
        CI["(:CheckIn)"]
        Alert["(:Alert)"]
        Fam["(:FamilyMember)"]
        Svc["(:Service)"]

        Senior -->|"TAKES"| Med
        Senior -->|"REPORTED"| Sym
        Senior -->|"CHECKED_IN"| CI
        Senior -->|"HAS_CONTACT"| Fam
        Senior -->|"NEEDS"| Svc
        CI -->|"DETECTED"| Sym
        CI -->|"TRIGGERED"| Alert
        Med -->|"INTERACTS_WITH"| Med
        Med -->|"SIDE_EFFECT"| Sym
        Sym -->|"SUGGESTS"| Cond
    end

    subgraph RocketRide["🚀 RocketRide AI"]
        Analyze["Transcript Analysis"]
        DrugAI["Drug Interaction\nExplanation"]
        CareAI["Care Plan\nGeneration"]
        CondAI["Condition\nSuggestion"]
    end

    subgraph API["⚙️ FastAPI Backend"]
        CRUD["Senior CRUD"]
        CheckinAPI["Check-in Processing"]
        GraphAPI["Graph Intelligence"]
        AlertAPI["Alert Engine"]
    end

    Family --> API
    API --> Neo4j
    API --> RocketRide
    CheckinAPI -->|"Store"| CI
    GraphAPI -->|"Query"| Neo4j
    GraphAPI -->|"Reason"| RocketRide
```

## How It Works

1. **Add seniors** with their medications, contacts, and check-in schedule
2. **Simulate check-ins** — enter what the senior said, the system analyzes it
3. **Neo4j builds the graph** — symptoms, medications, conditions all connected
4. **RocketRide AI reasons** — drug interactions, side effects, care recommendations
5. **Graph intelligence** — "Dorothy is dizzy → she takes Lisinopril → dizziness is a side effect of Lisinopril"

## Graph Model

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

## Quick Start

```bash
# Start Neo4j
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/careGraph2026 neo4j:5

# Install dependencies
uv sync

# Start the server
uv run python main.py

# Seed demo data
uv run python scripts/seed_data.py

# Open dashboard
open http://localhost:8000
```

## Key Demo Scenarios

| Scenario | What Neo4j Does | What RocketRide AI Does |
|----------|----------------|------------------------|
| Margaret takes Metformin + Lisinopril | Detects INTERACTS_WITH relationship | Explains the interaction risk |
| Dorothy reports dizziness | Matches symptom to Lisinopril SIDE_EFFECT | Suggests talking to doctor |
| 3 seniors report similar symptoms | Finds shared symptom paths in graph | Identifies potential cause |
| New medication added | Checks all INTERACTS_WITH edges | Flags concerns proactively |

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
- `GET /api/graph/care-network/{phone}` — Full care network (for visualization)
- `GET /api/graph/drug-interactions/{phone}` — Drug interactions + AI explanation
- `GET /api/graph/side-effects/{phone}` — Symptom ↔ medication matches
- `GET /api/graph/similar-symptoms/{phone}` — Seniors with same symptoms
- `GET /api/graph/care-recommendation/{phone}` — AI-generated care plan
- `GET /api/graph/seniors-by-symptom/{symptom}` — Find seniors by symptom
- `GET /api/graph/seniors-by-medication/{med}` — Find seniors by medication

### Alerts
- `GET /api/alerts` — Active alerts
- `PUT /api/alerts/{id}/acknowledge` — Acknowledge

## Tech Stack

| Tool | Role |
|------|------|
| **Neo4j** | Graph database — models care relationships, drug interactions, symptoms |
| **RocketRide AI** | Intelligence — transcript analysis, drug explanations, care plans |
| **FastAPI** | Python backend API |
| **Chart.js** | Dashboard visualization |

## Project Structure

```
CareGraph/
├── main.py                    # FastAPI app
├── app/
│   ├── config.py              # Settings
│   ├── graph_db.py            # Neo4j database layer (all Cypher queries)
│   ├── models/
│   │   └── senior.py          # Pydantic models
│   ├── routers/
│   │   ├── seniors.py         # Senior CRUD
│   │   ├── checkins.py        # Check-in processing
│   │   ├── alerts.py          # Alert management
│   │   └── graph.py           # Graph intelligence + RocketRide AI
│   └── services/
│       ├── rocketride.py      # RocketRide AI integration
│       ├── call_analyzer.py   # Transcript NLP
│       └── alert_engine.py    # Rule-based alerts
├── frontend/                  # Dashboard
├── scripts/
│   └── seed_data.py           # Demo data with drug interactions
└── tests/
```
