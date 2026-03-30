# CareGraph — Hackathon Demo Presentation

## Slide 1: The Problem (30 sec)

**"Who takes care of our elders when no one's around?"**

- 55 million seniors in the US live with chronic conditions
- Family caregivers spend 24+ hours/week on care — many burn out
- Doctors and nurses are overwhelmed — 15-minute appointments can't catch everything
- Medication errors cause 125,000+ deaths/year — drug interactions go undetected
- Seniors living alone miss daily check-ins — emergencies go unnoticed for hours

**The gap:** Between doctor visits, no one is watching. Symptoms build up silently. Drug interactions go unchecked. Falls happen with no one to call.

---

## Slide 2: Our Solution — CareGraph (30 sec)

**CareGraph is an AI-powered care companion that checks in on seniors daily — so families and doctors don't have to do it alone.**

Four things happen every day:
1. **Bland AI calls the senior** — a warm, patient voice agent asks about mood, medications, symptoms, and needs
2. **Neo4j builds a knowledge graph** — every symptom, medication, and interaction is connected
3. **RocketRide AI orchestrates pipelines** — visual pipeline canvas routes data through AI reasoning
4. **GMI Cloud (Qwen3-235B) generates intelligence** — drug interaction explanations, care plans, condition suggestions

**Result:** Family gets a dashboard. Doctors get insights. Seniors get care. 24/7.

---

## Slide 3: How Neo4j Powers CareGraph (45 sec)

**Why a graph database? Because healthcare is about relationships.**

```
Dorothy TAKES Lisinopril
Dorothy REPORTED dizziness
Lisinopril HAS_SIDE_EFFECT dizziness
→ Graph connects the dots: "Dorothy's dizziness may be caused by Lisinopril"
```

**What Neo4j does:**
- Models the complete care network: seniors, medications, symptoms, conditions, doctors, clinics, family, services
- 10 node types, 11 relationship types — all connected
- Drug interaction detection via `INTERACTS_WITH` edges
- Side effect matching via graph traversal (not keyword search!)
- Doctor recommendations via `CAN_TREAT` → `Condition` → `Symptom` path
- 159 real doctors + 38 clinics in the knowledge graph
- Cross-patient pattern detection: "3 seniors on Lisinopril all report dizziness"

**Demo:** Show the interactive graph visualization — drag nodes, see relationships light up. Switch between "Care Network" and "Doctors Network" views.

---

## Slide 4: How RocketRide AI + GMI Cloud Add Intelligence (45 sec)

**Neo4j finds the patterns. AI explains them.**

### RocketRide AI — Pipeline Orchestration
Four visual pipelines (`.pipe` files) in VS Code:

| Pipeline | What it does |
|----------|-------------|
| Check-in Analysis | Extracts symptoms, mood, urgency from call transcripts |
| Drug Interaction | Explains interactions in plain language for families |
| Care Recommendation | Generates personalized care plans from graph data |
| Condition Suggestion | Suggests possible conditions from symptom clusters |

**How it works:**
```
Webhook (input) → Prompt Template → LLM → Response
```

### GMI Cloud — LLM Inference (Qwen3-235B)
- **Model:** Qwen3-235B-A22B-Instruct — 235 billion parameter model
- **API:** OpenAI-compatible at `api.gmi-serving.com`
- **Role:** Powers all AI reasoning — drug explanations, care plans, condition suggestions
- **Inference chain:** RocketRide pipeline → GMI Cloud (Qwen3-235B) → structured response

**Demo:** Show AI Insights page — click "AI Care Plan" and watch Qwen3-235B generate a personalized care recommendation in real-time using Neo4j graph data.

**Key point:** "The AI doesn't just chat — it reasons over the graph. It knows Dorothy takes Lisinopril, that Lisinopril causes dizziness, and that Dorothy reported dizziness. It connects all three to generate a specific recommendation."

---

## Slide 5: The Daily Check-in Flow (45 sec)

**Live Demo — this is what happens every morning:**

```
1. CareGraph triggers Bland AI → calls the senior
2. AI voice agent: "Good morning! This is your daily check-in from CareGraph."
3. Asks about mood, medications, symptoms, and doctor needs
4. Voice agent has 159 doctors from Neo4j — can recommend specific doctors by name and phone
5. Call ends → transcript processed
6. CrewAI agents kick in:
   → Analysis Agent: extracts symptoms, mood, medication adherence
   → Graph Agent: Neo4j finds drug interactions, side effects, matching conditions
   → Recommendation Agent: GMI Cloud (Qwen3-235B) generates care plan
   → Alert Agent: evaluates urgency, triggers notifications
7. Family dashboard updates — alerts appear in real-time
```

**Demo:** Make a LIVE phone call to a real person using Bland AI. Then show the transcript being processed into the graph.

---

## Slide 6: Emergency Detection (30 sec)

**When seconds matter:**

```
Margaret: "I fell yesterday. My hip hurts. I forgot my medications."
```

**What CareGraph does in 2 seconds:**
- Detects "fell" → CRITICAL emergency alert
- Detects missed medications → MEDIUM alert
- Neo4j checks: Margaret takes Metformin + Lisinopril → interaction risk
- GMI Cloud (Qwen3-235B) explains: "Metformin and Lisinopril can increase risk of lactic acidosis, especially with kidney concerns"
- Family gets immediate notification
- Doctor recommended from graph: matched by condition

**Demo:** Simulate the check-in, show alerts cascade on dashboard

---

## Slide 7: CrewAI Multi-Agent Architecture (30 sec)

**Five AI agents collaborate on every check-in:**

```
Check-in Agent → Analysis Agent → Graph Agent → Recommendation Agent → Alert Agent
  (Bland AI)      (NLP extract)    (Neo4j)       (Qwen3-235B/GMI)      (Alerts)
```

- Each agent has specialized tools and a clear role
- Sequential pipeline — each agent builds on the previous
- All AI reasoning powered by **GMI Cloud** running **Qwen3-235B** (235B parameter model)
- Graph Agent queries Neo4j with Cypher — drug interactions, side effects, doctor matching
- Recommendation Agent feeds graph insights to Qwen3-235B for personalized care plans

**Why CrewAI?** Single LLM call can't do it all. Specialized agents = better results.

---

## Slide 8: Tech Stack (15 sec)

| Layer | Technology | Role |
|-------|-----------|------|
| Voice | **Bland AI** | Automated phone calls to seniors |
| Graph | **Neo4j Aura** | Cloud knowledge graph — 10 node types, 159 doctors, 38 clinics |
| AI Pipelines | **RocketRide AI** | Visual pipeline orchestration (.pipe files) |
| LLM Inference | **GMI Cloud (Qwen3-235B)** | 235B parameter model for reasoning |
| Agent Orchestration | **CrewAI** | 5 specialized agents with 11 custom tools |
| Backend | **FastAPI** | Python REST API — 34 endpoints |
| Frontend | **HTML/JS/vis.js** | Interactive dashboard + graph visualization |

**Open source contribution:** We also submitted a Bland AI tool node to the RocketRide project — [PR #521](https://github.com/rocketride-org/rocketride-server/pull/521).

---

## Slide 9: Impact (30 sec)

| Before CareGraph | After CareGraph |
|-------------------|-----------------|
| Family calls 1x/day (if they remember) | AI calls every morning automatically |
| Doctor sees patient every 3 months | Doctor gets weekly graph insights |
| Drug interactions discovered at ER | Drug interactions caught on day 1 |
| Falls discovered hours later | Emergency alert in 2 seconds |
| "Why am I dizzy?" — no answer | Neo4j: "Dizziness is a side effect of Lisinopril" |
| Need a doctor? Search Google | Graph recommends rated doctors who treat your condition |
| Care is reactive | Care is proactive |

**CareGraph doesn't replace caregivers — it gives them superpowers.**

---

## Slide 10: Live Demo (3-5 min)

### Demo Flow:
1. **Landing Page** — show problem statement, solution flow, tech stack
2. **Dashboard** — show 4 seniors, their statuses, alerts banner (11 active alerts)
3. **Graph View → Care Network** — select Dorothy, show interactive vis.js graph (medications, symptoms, family)
4. **Graph View → Doctors Network** — switch to doctors view (symptoms → conditions → 110 doctors → clinics)
5. **AI Insights → Drug Interactions** — select Margaret, show Metformin ↔ Lisinopril with Qwen3-235B explanation
6. **AI Insights → AI Care Plan** — select Dorothy, show full AI-generated care recommendation (live from GMI Cloud)
7. **Simulate Check-in** — type "I fell and feel dizzy. I forgot my medications. I need to see a doctor." → show emergency alerts + doctor appointment request
8. **Voice Calls** — make a LIVE Bland AI call (already tested with Josh Xavier)
9. **CrewAI Agents** — show the 5-agent pipeline visualization

### Key talking points during demo:
- "Neo4j connected Dorothy's dizziness to Lisinopril — that's graph intelligence, not keyword matching"
- "GMI Cloud's Qwen3-235B model explained this interaction in plain English for the family"
- "159 real doctors are in the knowledge graph — the voice agent recommends specific doctors by name"
- "This alert fired in 2 seconds — no human had to review anything"
- "Five AI agents collaborated to produce this care plan"
- "We contributed a Bland AI tool node back to RocketRide — PR #521"

---

## Closing (15 sec)

**CareGraph: Because every senior deserves a daily check-in.**

Built with Neo4j + RocketRide AI + GMI Cloud (Qwen3-235B) + Bland AI + CrewAI

**Team:** [Your team name]
