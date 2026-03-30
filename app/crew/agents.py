"""CareGraph CrewAI agent definitions.

Five specialized agents that collaborate on senior care check-ins:
1. Check-in Agent — initiates voice calls via Bland AI
2. Analysis Agent — extracts health data from transcripts
3. Graph Agent — queries Neo4j for relationships and patterns
4. Recommendation Agent — generates AI-powered care plans
5. Alert Agent — evaluates urgency and triggers notifications
"""

from crewai import Agent, LLM

from app.config import settings
from app.crew.tools import (
    MakeCheckInCallTool,
    AnalyzeTranscriptTool,
    GetSeniorInfoTool,
    FindDrugInteractionsTool,
    FindSideEffectsTool,
    FindSimilarSymptomsTool,
    GetCareNetworkTool,
    StoreCheckInTool,
    ExplainDrugInteractionTool,
    GenerateCareRecommendationTool,
    EvaluateAlertsTool,
)


def _get_llm() -> LLM:
    """Create LLM instance using GMI Cloud."""
    return LLM(
        model="openai/deepseek-ai/DeepSeek-R1",
        base_url=settings.gmi_base_url,
        api_key=settings.gmi_api_key,
        temperature=0.3,
        max_tokens=2000,
    )


def create_checkin_agent() -> Agent:
    """Agent that initiates voice calls to seniors via Bland AI."""
    return Agent(
        role="Senior Care Caller",
        goal=(
            "Initiate wellness check-in calls to seniors and collect their responses. "
            "Ensure each senior is contacted warmly and their transcript is captured."
        ),
        backstory=(
            "You are a compassionate care coordinator who manages daily phone check-ins "
            "with elderly patients. You use Bland AI to make automated but warm phone calls "
            "and ensure every senior feels heard and cared for."
        ),
        tools=[MakeCheckInCallTool(), GetSeniorInfoTool()],
        llm=_get_llm(),
        verbose=True,
    )


def create_analysis_agent() -> Agent:
    """Agent that analyzes transcripts for health signals."""
    return Agent(
        role="Health Transcript Analyst",
        goal=(
            "Analyze check-in call transcripts to extract mood, symptoms, medication adherence, "
            "wellness scores, and service needs. Identify any concerning patterns."
        ),
        backstory=(
            "You are a trained health analyst specializing in senior care. "
            "You carefully review call transcripts to identify health signals — "
            "symptoms like dizziness or chest pain, medication compliance issues, "
            "mood changes, and requests for services like meals or transportation."
        ),
        tools=[AnalyzeTranscriptTool(), StoreCheckInTool()],
        llm=_get_llm(),
        verbose=True,
    )


def create_graph_agent() -> Agent:
    """Agent that queries Neo4j for care network insights."""
    return Agent(
        role="Care Network Graph Analyst",
        goal=(
            "Query the Neo4j care graph to find drug interactions, side effect matches, "
            "symptom patterns, and related seniors. Build a complete picture of the "
            "senior's health relationships."
        ),
        backstory=(
            "You are a graph intelligence specialist who analyzes the CareGraph knowledge graph. "
            "You traverse relationships between seniors, medications, symptoms, and conditions "
            "to find hidden patterns — like a reported symptom matching a known side effect, "
            "or multiple seniors experiencing the same issue."
        ),
        tools=[
            FindDrugInteractionsTool(),
            FindSideEffectsTool(),
            FindSimilarSymptomsTool(),
            GetCareNetworkTool(),
            GetSeniorInfoTool(),
        ],
        llm=_get_llm(),
        verbose=True,
    )


def create_recommendation_agent() -> Agent:
    """Agent that generates AI-powered care recommendations."""
    return Agent(
        role="Care Plan Advisor",
        goal=(
            "Generate personalized, actionable care recommendations for the senior's family "
            "based on transcript analysis and graph insights. Explain drug interactions, "
            "suggest next steps, and flag anything to discuss with their doctor."
        ),
        backstory=(
            "You are an experienced senior care advisor who combines health data with AI "
            "to create practical care plans. You translate complex medical graph data into "
            "simple, actionable advice for family caregivers. You always recommend "
            "consulting a doctor for medical decisions."
        ),
        tools=[ExplainDrugInteractionTool(), GenerateCareRecommendationTool()],
        llm=_get_llm(),
        verbose=True,
    )


def create_alert_agent() -> Agent:
    """Agent that evaluates urgency and triggers alerts."""
    return Agent(
        role="Safety Monitor",
        goal=(
            "Evaluate every check-in for safety concerns. Trigger alerts for emergencies, "
            "low wellness scores, missed medications, and loneliness. Ensure no urgent "
            "issue goes unnoticed."
        ),
        backstory=(
            "You are a vigilant safety monitor for senior patients. You evaluate every "
            "check-in against safety rules: emergency symptoms trigger critical alerts, "
            "low mood or missed medications trigger warnings, and service requests are "
            "flagged for follow-up. Your top priority is patient safety."
        ),
        tools=[EvaluateAlertsTool()],
        llm=_get_llm(),
        verbose=True,
    )
