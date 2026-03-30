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

Three things happen every day:
1. **Bland AI calls the senior** — a warm, patient voice agent asks about mood, medications, symptoms, and needs
2. **Neo4j builds a knowledge graph** — every symptom, medication, and interaction is connected
3. **RocketRide AI reasons over the graph** — detects drug interactions, flags side effects, generates care plans

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
- Models the complete care network: seniors, medications, symptoms, conditions, family, services
- 9 node types, 9 relationship types — all connected
- Drug interaction detection via `INTERACTS_WITH` edges
- Side effect matching via graph traversal (not keyword search!)
- Cross-patient pattern detection: "3 seniors on Lisinopril all report dizziness"

**Demo:** Show the interactive graph visualization — drag nodes, see relationships light up

---

## Slide 4: How RocketRide AI Adds Intelligence (45 sec)

**Neo4j finds the patterns. RocketRide AI explains them.**

Four RocketRide pipelines (`.pipe` files):

| Pipeline | What it does |
|----------|-------------|
| Check-in Analysis | Extracts symptoms, mood, urgency from call transcripts |
| Drug Interaction | Explains interactions in plain language for families |
| Care Recommendation | Generates personalized care plans from graph data |
| Condition Suggestion | Suggests possible conditions from symptom clusters |

**How it works:**
```
Webhook (input) → Prompt Template → Gemini LLM → Response
```

**Demo:** Show RocketRide pipeline in VS Code — visual canvas, click play

**Fallback:** GMI Cloud (DeepSeek-R1) as backup inference

---

## Slide 5: The Daily Check-in Flow (45 sec)

**Live Demo — this is what happens every morning for Dorothy Williams:**

```
1. CareGraph triggers Bland AI → calls Dorothy at +14155551003
2. AI voice agent: "Hi Dorothy, how are you feeling today?"
3. Dorothy: "I've been dizzy all morning. Yes, I took my medications."
4. Call ends → transcript arrives via webhook
5. CrewAI agents kick in:
   → Analysis Agent: extracts "dizzy", mood=sad, meds=taken
   → Graph Agent: Neo4j query finds Lisinopril → SIDE_EFFECT → dizzy
   → Recommendation Agent: "Dizziness may be a side effect of Lisinopril. Talk to doctor."
   → Alert Agent: triggers medium-severity alert
6. Family dashboard updates in real-time
7. Son James gets notified
```

**Demo:** Run the simulate check-in flow live, show graph update, show alert appear

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
- Family gets immediate notification
- Care plan: "Immediate attention needed. Check for hip fracture."

**Demo:** Show the emergency alert cascade on dashboard

---

## Slide 7: CrewAI Multi-Agent Architecture (30 sec)

**Five AI agents collaborate on every check-in:**

```
Check-in Agent → Analysis Agent → Graph Agent → Recommendation Agent → Alert Agent
  (Bland AI)      (NLP extract)    (Neo4j)       (RocketRide/GMI)      (Alerts)
```

- Each agent has specialized tools and a clear role
- Sequential pipeline — each agent builds on the previous
- All powered by GMI Cloud (DeepSeek-R1) for reasoning

**Why CrewAI?** Single LLM call can't do it all. Specialized agents = better results.

---

## Slide 8: Tech Stack (15 sec)

| Layer | Technology |
|-------|-----------|
| Voice | **Bland AI** — automated phone calls |
| Graph | **Neo4j Aura** — cloud knowledge graph |
| AI Pipelines | **RocketRide AI** — visual LLM orchestration |
| LLM Inference | **GMI Cloud** — DeepSeek-R1 |
| Agent Orchestration | **CrewAI** — 5 specialized agents |
| Backend | **FastAPI** — Python REST API |
| Frontend | **HTML/JS/vis.js** — interactive dashboard |

---

## Slide 9: Impact (30 sec)

| Before CareGraph | After CareGraph |
|-------------------|-----------------|
| Family calls 1x/day (if they remember) | AI calls every morning automatically |
| Doctor sees patient every 3 months | Doctor gets weekly graph insights |
| Drug interactions discovered at ER | Drug interactions caught on day 1 |
| Falls discovered hours later | Emergency alert in 2 seconds |
| Care is reactive | Care is proactive |

**CareGraph doesn't replace caregivers — it gives them superpowers.**

---

## Slide 10: Demo (3-5 min live)

### Demo Flow:
1. **Dashboard** — show 3 seniors, their statuses, alerts banner
2. **Graph View** — select Dorothy, show interactive graph (vis.js), point out Lisinopril → dizzy connection
3. **AI Insights** — show drug interactions for Margaret (Metformin ↔ Lisinopril), side effects for Dorothy
4. **Simulate Check-in** — type "I fell and feel dizzy. I forgot my medications." — show emergency alerts fire
5. **Voice Calls** — show Bland AI call interface (initiate if time permits)
6. **CrewAI** — run analysis crew, show 5 agents working in sequence
7. **Neo4j Browser** — show the graph in Aura console (optional)

### Key talking points during demo:
- "Notice how Neo4j connected Dorothy's dizziness to Lisinopril — that's graph intelligence, not keyword matching"
- "RocketRide AI explained this interaction in plain English for the family"
- "This alert fired in 2 seconds — no human had to review anything"
- "Five AI agents collaborated to produce this care plan"

---

## Closing (15 sec)

**CareGraph: Because every senior deserves a daily check-in.**

Built with Neo4j + RocketRide AI + Bland AI + GMI Cloud + CrewAI

**Team:** [Your team name]
