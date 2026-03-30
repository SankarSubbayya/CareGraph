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
2. **Bland AI calls seniors** — automated voice agent asks about mood, medications, symptoms
3. **Transcript flows to backend** — Bland AI webhook sends transcript when call ends
4. **Neo4j builds the graph** — symptoms, medications, conditions all connected
5. **RocketRide AI / GMI Cloud reasons** — drug interactions, side effects, care recommendations
6. **Graph intelligence** — "Dorothy is dizzy → she takes Lisinopril → dizziness is a side effect of Lisinopril"

## Voice Agent (Bland AI)

CareGraph uses **Bland AI** to make automated phone calls to seniors for daily check-ins.

### Call Flow

```
CareGraph triggers call → Bland AI dials senior → AI voice agent converses
→ Call ends → Webhook sends transcript → NLP analysis → Neo4j graph update → Alerts
```

### What the Voice Agent Does

- Asks how the senior is feeling (mood, wellness)
- Asks about medication adherence
- Listens for symptoms (pain, dizziness, chest pain, etc.)
- Asks about service needs (meals, transport, companionship)
- Detects emergencies (falls, breathing difficulty, chest pain)
- Speaks warmly and patiently — not robotic

### Setup

1. Sign up at [bland.ai](https://www.bland.ai) and get an API key
2. Set `BLAND_API_KEY` in your environment (e.g. Codespaces secret or `export` before `uv run`)
3. Call `POST /api/voice/call/{phone}` to initiate a check-in call

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

### Neo4j credentials

The backend reads **`NEO4J_URI`**, **`NEO4J_USERNAME`**, **`NEO4J_PASSWORD`**, and optionally **`NEO4J_DATABASE`** from the environment only. It does not load a `.env` file or call the GitHub API at runtime.

- **CI:** add the same names as [repository Actions secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions); the [Neo4j smoke workflow](.github/workflows/neo4j-smoke.yml) uses them automatically.
- **GitHub Codespaces:** add [Codespaces secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-development-environment-secrets-for-your-repository) with the same names.
- **Local machine:** `export` the variables in your shell (or your IDE run configuration) before starting the app. Repository secrets are not available on a plain git clone.

Details: [.github/SETUP_SECRETS.md](.github/SETUP_SECRETS.md).

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

### CrewAI Multi-Agent Pipeline
- `POST /api/crew/checkin/{phone}` — Full pipeline: call → analyze → graph → recommend → alert
- `POST /api/crew/analyze/{phone}` — Analysis pipeline with transcript (no call)
- `POST /api/crew/insights/{phone}` — Graph insights + recommendations only

### Voice Agent (Bland AI)
- `POST /api/voice/call/{phone}` — Initiate check-in call to a senior
- `POST /api/voice/call-all` — Call all registered seniors
- `GET /api/voice/call/{call_id}` — Get call details + transcript
- `POST /api/voice/call/{call_id}/analyze` — Run post-call AI analysis
- `POST /api/voice/call/{call_id}/stop` — Stop an ongoing call
- `GET /api/voice/calls` — List recent calls
- `POST /api/voice/webhook` — Webhook endpoint (receives Bland AI call results)

### Alerts
- `GET /api/alerts` — Active alerts
- `PUT /api/alerts/{id}/acknowledge` — Acknowledge

## CrewAI Multi-Agent Architecture

CareGraph uses **CrewAI** to orchestrate 5 specialized AI agents that collaborate on senior care check-ins.

### Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Check-in Agent** | Senior Care Caller | Bland AI voice calls, senior lookup |
| **Analysis Agent** | Health Transcript Analyst | NLP analyzer, graph store |
| **Graph Agent** | Care Network Analyst | Neo4j drug interactions, side effects, similar symptoms, care network |
| **Recommendation Agent** | Care Plan Advisor | GMI Cloud LLM for explanations and care plans |
| **Alert Agent** | Safety Monitor | Alert evaluation engine |

### Crew Pipelines

**Full Check-in** (`POST /api/crew/checkin/{phone}`):
```
Check-in Agent → Analysis Agent → Graph Agent → Recommendation Agent → Alert Agent
  (Bland AI)      (NLP extract)    (Neo4j)       (GMI Cloud LLM)       (Alerts)
```

**Analysis Only** (`POST /api/crew/analyze/{phone}`):
```
Analysis Agent → Graph Agent → Recommendation Agent → Alert Agent
  (transcript)    (Neo4j)       (GMI Cloud LLM)       (Alerts)
```

**Graph Insights** (`POST /api/crew/insights/{phone}`):
```
Graph Agent → Recommendation Agent
  (Neo4j)       (GMI Cloud LLM)
```

---

## RocketRide AI Pipeline Integration

CareGraph uses **RocketRide AI pipelines** (`.pipe` files) to orchestrate AI reasoning. Each pipeline follows the pattern:

```
Webhook (input) → Prompt (template) → Gemini LLM → Response (output)
```

### Pipelines

| Pipeline | File | Purpose |
|----------|------|---------|
| Check-in Analysis | `pipelines/checkin_analysis.pipe` | Extracts symptoms, mood, urgency from transcripts |
| Drug Interaction | `pipelines/drug_interaction.pipe` | Explains medication interactions for caregivers |
| Care Recommendation | `pipelines/care_recommendation.pipe` | Generates personalized care plans from graph data |
| Condition Suggestion | `pipelines/condition_suggestion.pipe` | Suggests conditions from symptom clusters |

### How It Connects

1. Backend calls `POST {ROCKETRIDE_URI}/webhook` with `{"text": "..."}`
2. RocketRide routes through the pipeline: prompt template → Gemini 2.5 Flash
3. Response returned at `resp["data"]["objects"]["body"]["answers"]`
4. If RocketRide is unavailable, falls back to **GMI Cloud** direct inference
5. If neither is configured, graph queries still work (AI explanations are empty)

### Inference Chain

```
RocketRide Pipeline (.pipe webhook) → GMI Cloud (api.gmi-serving.com) → empty fallback
```

### Setup

**RocketRide (primary):**
1. Install **RocketRide VS Code extension** from Marketplace
2. Click rocket icon → Connect → **Local** (runs on port 5565)
3. Open any `.pipe` file → visual pipeline canvas appears
4. Configure the Gemini node with your API key
5. Click play to start the pipeline
6. Set `ROCKETRIDE_APIKEY` in the environment to the key from the extension (e.g. Codespaces secret or `export`)

**GMI Cloud (fallback):**
1. Sign up at [console.gmicloud.ai](https://console.gmicloud.ai)
2. Create an API key in organization settings
3. Set `GMI_API_KEY` in the environment
4. Optionally change `GMI_MODEL` (default: `deepseek-ai/DeepSeek-R1`)

## Tech Stack

| Tool | Role |
|------|------|
| **Neo4j** | Graph database — models care relationships, drug interactions, symptoms |
| **CrewAI** | Multi-agent orchestration — 5 specialized agents collaborate on check-ins |
| **Bland AI** | Voice agent — automated phone calls to seniors for check-ins |
| **RocketRide AI** | Pipeline orchestration — webhook → prompt → Gemini LLM → response |
| **GMI Cloud** | LLM inference — powers CrewAI agents and direct API fallback |
| **FastAPI** | Python backend API |
| **Chart.js** | Dashboard visualization |

## Project Structure

```
CareGraph/
├── main.py                    # FastAPI app
├── pipelines/                 # RocketRide AI pipelines (.pipe files)
│   ├── checkin_analysis.pipe  # Transcript analysis pipeline
│   ├── drug_interaction.pipe  # Drug interaction explainer pipeline
│   ├── care_recommendation.pipe # Care plan generation pipeline
│   └── condition_suggestion.pipe # Condition suggester pipeline
├── app/
│   ├── config.py              # Settings
│   ├── graph_db.py            # Neo4j database layer (all Cypher queries)
│   ├── crew/                  # CrewAI multi-agent system
│   │   ├── agents.py          # 5 specialized agent definitions
│   │   ├── tasks.py           # Task definitions for each pipeline
│   │   ├── tools.py           # Custom tools wrapping CareGraph services
│   │   └── care_crew.py       # Crew orchestration (3 pipeline configs)
│   ├── models/
│   │   └── senior.py          # Pydantic models
│   ├── routers/
│   │   ├── seniors.py         # Senior CRUD
│   │   ├── checkins.py        # Check-in processing
│   │   ├── alerts.py          # Alert management
│   │   ├── graph.py           # Graph intelligence + RocketRide AI
│   │   ├── voice.py           # Bland AI voice agent endpoints
│   │   └── crew.py            # CrewAI multi-agent endpoints
│   └── services/
│       ├── bland_voice.py     # Bland AI voice call client
│       ├── rocketride.py      # RocketRide webhook + GMI Cloud fallback
│       ├── gmi_inference.py   # GMI Cloud direct inference client
│       ├── call_analyzer.py   # Transcript NLP (local fallback)
│       └── alert_engine.py    # Rule-based alerts
├── frontend/                  # Dashboard
├── data/                      # EHR sample data from HuggingFace
├── scripts/
│   └── seed_data.py           # Demo data with drug interactions
└── tests/
```
