# CareGraph

**AI-powered senior care intelligence built with Neo4j + RocketRide AI + GMI Cloud + Bland AI + CrewAI**

CareGraph calls seniors every day, builds a health knowledge graph, and alerts families before problems become emergencies.

> Built for HackWithBay 2.0 Hackathon — Theme: Building Intelligent, Graph-Powered Applications with Neo4j and RocketRide AI

---

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- Neo4j Aura account (or local Docker) — [console.neo4j.io](https://console.neo4j.io)
- GMI Cloud API key — [console.gmicloud.ai](https://console.gmicloud.ai)
- Bland AI API key (optional, for voice calls) — [bland.ai](https://www.bland.ai)

### 1. Clone and install

```bash
git clone https://github.com/SankarSubbayya/CareGraph.git
cd CareGraph
uv sync
```

### 2. Configure environment

Copy `.env.example` or create `.env`:

```env
# Neo4j (Aura or local)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# GMI Cloud (required for AI features)
GMI_BASE_URL=https://api.gmi-serving.com/v1
GMI_API_KEY=your-gmi-api-key
GMI_MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507-FP8

# Bland AI (optional, for voice calls)
BLAND_API_KEY=your-bland-api-key

# RocketRide AI (optional, for pipeline orchestration)
ROCKETRIDE_URI=http://localhost:5565
ROCKETRIDE_APIKEY=

# App
BASE_URL=http://localhost:8000
SKIP_AUTH=true
```

**Using local Neo4j instead of Aura:**
```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password neo4j:5
```
Then set `NEO4J_URI=bolt://localhost:7687` and `NEO4J_PASSWORD=password`.

### 3. Seed demo data and start

```bash
# Start the server
uv run python main.py

# In another terminal — seed demo data
uv run python scripts/seed_data.py     # 4 seniors, medications, check-ins, alerts
uv run python scripts/seed_doctors.py  # 159 doctors, 38 clinics
```

### 4. Open in browser

| URL | Page |
|-----|------|
| http://localhost:8000 | Landing page |
| http://localhost:8000/dashboard | Full dashboard |

### 5. Run tests

```bash
uv run python -m pytest tests/ -v
```

---

## What CareGraph Does

```
1. Bland AI calls the senior every morning
2. Voice agent asks about mood, medications, symptoms, doctor needs
3. Transcript is analyzed → symptoms extracted → stored in Neo4j graph
4. Graph detects drug interactions, side effect matches, condition suggestions
5. GMI Cloud (Qwen3-235B) generates care plans from graph data
6. Alerts notify family members based on severity
```

### Example: Dorothy reports dizziness

```
Dorothy TAKES Lisinopril
Dorothy REPORTED dizziness
Lisinopril HAS_SIDE_EFFECT dizziness
→ Neo4j connects the dots automatically
→ Qwen3-235B explains: "Dizziness may be a side effect of Lisinopril. Discuss with doctor."
→ Family gets notified
```

---

## Architecture

```mermaid
flowchart TB
    subgraph Users["Users"]
        Family["Family\n(Dashboard)"]
        SeniorPhone["Senior\n(Phone)"]
    end

    subgraph BlandAI["Bland AI (Voice Agent)"]
        VoiceCall["Automated\nPhone Call"]
        Webhook["Webhook\n(Transcript)"]
    end

    subgraph CrewAI["CrewAI (Multi-Agent Orchestration)"]
        Agent1["Check-in Agent\n(Bland AI calls)"]
        Agent2["Analysis Agent\n(NLP extraction)"]
        Agent3["Graph Agent\n(Neo4j queries)"]
        Agent4["Recommendation Agent\n(AI care plans)"]
        Agent5["Alert Agent\n(Safety monitor)"]

        Agent1 -->|transcript| Agent2
        Agent2 -->|symptoms, mood| Agent3
        Agent3 -->|graph insights| Agent4
        Agent4 -->|care plan| Agent5
    end

    subgraph API["FastAPI Backend"]
        CRUD["Senior CRUD"]
        CheckinAPI["Check-in\nProcessing"]
        GraphAPI["Graph\nIntelligence"]
        AlertAPI["Alert Engine"]
        VoiceAPI["Voice\nEndpoints"]
        CrewAPI["Crew\nEndpoints"]
    end

    subgraph Neo4j["Neo4j Aura (Graph Database)"]
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

    subgraph Inference["LLM Inference"]
        RocketRide["RocketRide AI\n(.pipe pipelines)"]
        GMI["GMI Cloud\n(Qwen3-235B)"]
        RocketRide -.->|fallback| GMI
    end

    Family --> API
    SeniorPhone <--> BlandAI
    BlandAI -->|webhook| API
    API --> CrewAI
    CrewAI --> Neo4j
    CrewAI --> Inference
    CrewAI --> BlandAI
    Agent1 -->|"initiate call"| VoiceCall
    Webhook -->|"transcript"| CheckinAPI
    Agent3 -->|"Cypher queries"| Neo4j
    Agent4 -->|"prompts"| Inference
    Agent5 -->|"alerts"| AlertAPI
    GraphAPI -->|"Query"| Neo4j
    GraphAPI -->|"Reason"| Inference
```

### Data Flow

```mermaid
sequenceDiagram
    participant F as Family Dashboard
    participant A as FastAPI
    participant C as CrewAI Crew
    participant B as Bland AI
    participant S as Senior (Phone)
    participant N as Neo4j Aura
    participant L as GMI Cloud LLM

    F->>A: POST /api/crew/checkin/{phone}
    A->>C: Start Full Check-in Crew
    C->>N: Look up senior profile
    N-->>C: Name, medications, contacts
    C->>B: Initiate voice call
    B->>S: Automated phone call
    S-->>B: Conversation (mood, meds, symptoms)
    B-->>A: Webhook: transcript + recording
    A->>C: Analysis Agent processes transcript
    C->>N: Store check-in + symptoms in graph
    C->>N: Query drug interactions & side effects
    N-->>C: Graph insights (interactions, matches)
    C->>L: Generate care recommendations
    L-->>C: Personalized care plan
    C->>N: Evaluate & store alerts
    C-->>A: Complete crew output
    A-->>F: Results + alerts + care plan
```

---

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Graph Database | **Neo4j Aura** | Knowledge graph — 10 node types, 159 doctors, 38 clinics, 1000+ relationships |
| Voice Agent | **Bland AI** | Automated phone calls to seniors with doctor recommendations |
| AI Pipelines | **RocketRide AI** | Visual pipeline orchestration (.pipe files) |
| LLM Inference | **GMI Cloud (Qwen3-235B)** | 235B parameter model for care plans, drug explanations |
| Agent Orchestration | **CrewAI** | 5 specialized agents with 11 custom tools |
| Backend | **FastAPI** | Python REST API — 33 endpoints |
| Frontend | **HTML/JS/vis.js** | Interactive dashboard with graph visualization |

---

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
(:Condition)<-[:CAN_TREAT]-(:Doctor)
(:Doctor)-[:PRACTICES_AT]->(:Clinic)
(:CheckIn)-[:TRIGGERED]->(:Alert)
```

---

## Dashboard Pages

| Page | Features |
|------|----------|
| **Home** | Landing page — problem statement, solution flow, live Neo4j stats |
| **Seniors** | List seniors, wellness scores, family contacts, action buttons |
| **Graph View** | Interactive vis.js graph — Care Network + Doctors Network views |
| **Graph Reasoning** | Animated step-by-step walkthrough of Neo4j reasoning chain |
| **AI Insights** | Drug interactions, side effects, condition suggestions, doctor recommendations, cross-senior search |
| **Voice Calls** | Initiate Bland AI calls, voice selection, call history, save to graph |
| **CrewAI Agents** | Visual 5-agent pipeline, run full check-in / analyze / insights |
| **Alerts** | Severity-coded alerts with family notification targets |
| **Simulate** | Enter transcript, see analysis + alerts + family notifications |

---

## Key Demo Scenarios

| Scenario | What Neo4j Does | What AI Does |
|----------|----------------|-------------|
| Margaret takes Metformin + Lisinopril | Detects INTERACTS_WITH relationship | Qwen3-235B explains the interaction risk |
| Dorothy reports dizziness | Matches symptom to Lisinopril SIDE_EFFECT | Suggests talking to doctor |
| 3 seniors report similar symptoms | Finds shared symptom paths in graph | Identifies potential cause |
| Senior needs a doctor | Traverses Symptom → Condition → Doctor → Clinic | Recommends specific doctors |

---

## API Endpoints (33 total)

### Seniors
- `POST /api/seniors` — Add senior
- `GET /api/seniors` — List all
- `GET /api/seniors/{phone}` — Get one
- `DELETE /api/seniors/{phone}` — Remove

### Check-ins
- `POST /api/checkins/simulate/{phone}` — Simulate with transcript
- `GET /api/checkins/{phone}` — History
- `GET /api/checkins/latest/all` — Latest per senior

### Graph Intelligence
- `GET /api/graph/stats` — Live graph statistics
- `GET /api/graph/care-network/{phone}` — Care network visualization
- `GET /api/graph/doctors-network/{phone}` — Doctors network visualization
- `GET /api/graph/drug-interactions/{phone}` — Drug interactions + AI explanation
- `GET /api/graph/side-effects/{phone}` — Side effect matches
- `GET /api/graph/similar-symptoms/{phone}` — Cross-senior symptom patterns
- `GET /api/graph/condition-suggestions/{phone}` — AI condition suggestions
- `GET /api/graph/care-recommendation/{phone}` — AI care plan
- `GET /api/graph/doctors` — Search doctors by specialty/city
- `GET /api/graph/doctors/for-senior/{phone}` — Recommended doctors
- `GET /api/graph/seniors-by-symptom/{symptom}` — Find by symptom
- `GET /api/graph/seniors-by-medication/{med}` — Find by medication

### Voice Agent (Bland AI)
- `POST /api/voice/call/{phone}` — Call a senior
- `POST /api/voice/call-all` — Call all seniors
- `GET /api/voice/call/{call_id}` — Call details + transcript
- `POST /api/voice/call/{call_id}/analyze` — Post-call AI analysis
- `POST /api/voice/call/{call_id}/stop` — Stop call
- `POST /api/voice/process/{call_id}` — Save call transcript to graph
- `GET /api/voice/calls` — Recent calls
- `POST /api/voice/webhook` — Bland AI callback

### CrewAI Agents
- `POST /api/crew/checkin/{phone}` — Full 5-agent pipeline
- `POST /api/crew/analyze/{phone}` — Analysis pipeline (4 agents)
- `POST /api/crew/insights/{phone}` — Graph insights (2 agents)

### Alerts
- `GET /api/alerts` — Active alerts
- `PUT /api/alerts/{id}/acknowledge` — Acknowledge

---

## RocketRide AI Pipelines

5 visual pipelines in `pipelines/` directory:

| Pipeline | Purpose | Use Case for Doctors |
|----------|---------|----------------------|
| `checkin_analysis.pipe` | Transcript → symptoms, mood, urgency | Automatic symptom extraction from patient calls |
| `drug_interaction.pipe` | Drug pair → plain-language explanation | Explaining *why* two meds interact based on graph data |
| `care_recommendation.pipe` | Graph data → personalized care plan | Generating tailored clinical steps for family caregivers |
| `condition_suggestion.pipe` | Symptom cluster → possible conditions | Differential reasoning based on reported trends |
| `neo4j_graph_chat.pipe` | **Natural Language Graph Chat** | **Clinical Data Retrieval**: Doctors can chat directly to get patient data, symptoms, and medical history across the entire graph. |

Each follows: `Webhook → Question/Prompt → Gemini LLM → Response`

### 🏥 Pipeline Workflow: Neo4j Graph Chat
The **Neo4j Graph Chat** follows a simple visual flow in RocketRide:
1.  **Chat Source Box**: Captures the doctor's question in the chat interface.
2.  **Neo4j Database Tool Box**: Connects to the Neo4j graph and receives the question.
3.  **Gemini LLM Box**: Connected directly to the Neo4j box to handle query generation and provide the final response to the doctor.

---

## CrewAI Agents

5 agents collaborate on every check-in:

```
Check-in Agent → Analysis Agent → Graph Agent → Recommendation Agent → Alert Agent
  (Bland AI)      (NLP extract)    (Neo4j)       (Qwen3-235B)          (Alerts)
```

| Agent | Tools |
|-------|-------|
| Check-in Agent | Bland AI voice calls, senior lookup |
| Analysis Agent | NLP transcript analyzer, Neo4j store |
| Graph Agent | Drug interactions, side effects, similar symptoms, care network |
| Recommendation Agent | GMI Cloud LLM for explanations and care plans |
| Alert Agent | Severity evaluation, family notification |

---

## Project Structure

```
CareGraph/
├── main.py                        # FastAPI app entry point
├── .env                           # Configuration (gitignored)
├── pipelines/                     # RocketRide AI pipelines
│   ├── checkin_analysis.pipe
│   ├── drug_interaction.pipe
│   ├── care_recommendation.pipe
│   └── condition_suggestion.pipe
├── app/
│   ├── config.py                  # Pydantic settings
│   ├── graph_db.py                # Neo4j Cypher queries (467 lines)
│   ├── crew/                      # CrewAI multi-agent system
│   │   ├── agents.py              # 5 agent definitions
│   │   ├── tasks.py               # Task definitions
│   │   ├── tools.py               # 11 custom tools
│   │   └── care_crew.py           # 3 crew pipelines
│   ├── models/
│   │   └── senior.py              # Pydantic models
│   ├── routers/
│   │   ├── seniors.py             # Senior CRUD
│   │   ├── checkins.py            # Check-in processing
│   │   ├── alerts.py              # Alert management
│   │   ├── graph.py               # Graph intelligence + AI
│   │   ├── voice.py               # Bland AI voice endpoints
│   │   └── crew.py                # CrewAI endpoints
│   └── services/
│       ├── bland_voice.py         # Bland AI client + doctor lookup
│       ├── rocketride.py          # RocketRide + GMI Cloud fallback
│       ├── gmi_inference.py       # GMI Cloud API client
│       ├── call_analyzer.py       # Local NLP analysis
│       └── alert_engine.py        # Alert rules + family notifications
├── frontend/
│   ├── landing.html               # Landing page
│   ├── index.html                 # Dashboard
│   ├── app.js                     # Frontend logic
│   └── style.css                  # Styles
├── scripts/
│   ├── seed_data.py               # Demo seniors + medical knowledge
│   └── seed_doctors.py            # 159 doctors + 38 clinics
├── tests/                         # 56 tests (unit + integration)
├── data/                          # EHR sample data
└── presentation/
    └── DEMO_SCRIPT.md             # 10-slide demo script
```

---

## Tests

56 tests — all passing:

```bash
uv run python -m pytest tests/ -v
```

| Test File | Count | What |
|-----------|-------|------|
| test_models.py | 3 | Pydantic models |
| test_call_analyzer.py | 19 | NLP: mood, meds, symptoms, services |
| test_alert_engine.py | 10 | Alert rules + severity |
| test_config.py | 2 | Settings |
| test_integration.py | 22 | Neo4j queries, API endpoints, full pipelines |

---

## Open Source Contribution

We contributed a **Bland AI tool node** to the RocketRide project:
- PR: [rocketride-org/rocketride-server#521](https://github.com/rocketride-org/rocketride-server/pull/521)
- Adds `make_call`, `get_call`, `analyze_call` tools for RocketRide agents
