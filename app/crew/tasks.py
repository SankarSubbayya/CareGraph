"""CareGraph CrewAI task definitions.

Tasks define what each agent should do and in what order.
Two main workflows:
1. Full check-in pipeline (call → analyze → graph → recommend → alert)
2. Analysis-only pipeline (transcript → analyze → graph → recommend → alert)
"""

from crewai import Task, Agent


def create_checkin_call_task(agent: Agent, phone: str) -> Task:
    """Task: Initiate a voice call to the senior."""
    return Task(
        description=(
            f"Call the senior at phone number {phone} for a wellness check-in. "
            f"First look up their profile to get their name and medications, "
            f"then initiate the call via Bland AI. "
            f"Report the call_id and status."
        ),
        expected_output=(
            "JSON with call_id, senior name, and call status. "
            "Example: {\"call_id\": \"abc123\", \"senior\": \"Dorothy Williams\", \"status\": \"success\"}"
        ),
        agent=agent,
    )


def create_analysis_task(agent: Agent, phone: str, transcript: str) -> Task:
    """Task: Analyze a check-in transcript and store results."""
    return Task(
        description=(
            f"Analyze this check-in transcript for the senior at {phone}:\n\n"
            f"\"{transcript}\"\n\n"
            f"Use the analyze_transcript tool to extract mood, symptoms, wellness score, "
            f"medication adherence, concerns, and service needs. "
            f"Then store the check-in in the Neo4j graph using the store_checkin tool."
        ),
        expected_output=(
            "JSON analysis with mood, wellness_score (1-10), medication_taken (true/false), "
            "symptoms list, concerns list, service_needs list, and summary. "
            "Plus confirmation that check-in was stored in the graph."
        ),
        agent=agent,
    )


def create_graph_analysis_task(agent: Agent, phone: str) -> Task:
    """Task: Query Neo4j graph for health insights."""
    return Task(
        description=(
            f"Query the CareGraph Neo4j database for the senior at {phone}. "
            f"Find:\n"
            f"1. Drug interactions between their medications\n"
            f"2. Side effects that match reported symptoms\n"
            f"3. Other seniors with similar symptoms\n"
            f"4. Their full care network\n\n"
            f"Compile all graph insights into a comprehensive report."
        ),
        expected_output=(
            "Structured report with:\n"
            "- drug_interactions: list of interacting drug pairs\n"
            "- side_effect_matches: symptoms that match medication side effects\n"
            "- similar_seniors: other seniors with shared symptoms\n"
            "- care_network_summary: overview of nodes and relationships"
        ),
        agent=agent,
    )


def create_recommendation_task(agent: Agent, phone: str) -> Task:
    """Task: Generate care recommendations from analysis + graph insights."""
    return Task(
        description=(
            f"Using the transcript analysis and graph insights from previous tasks, "
            f"generate personalized care recommendations for the senior at {phone}. "
            f"If there are drug interactions, explain each one in plain language. "
            f"Provide:\n"
            f"1. Top 3 actionable recommendations for the family\n"
            f"2. Any drug interaction explanations\n"
            f"3. Concerns to discuss with their doctor\n"
            f"4. Suggested schedule adjustments"
        ),
        expected_output=(
            "Care plan with:\n"
            "- recommendations: list of 3 actionable items\n"
            "- drug_interaction_explanations: plain-language explanations\n"
            "- doctor_concerns: items to discuss with physician\n"
            "- schedule_changes: suggested adjustments"
        ),
        agent=agent,
    )


def create_alert_task(agent: Agent, phone: str, senior_name: str) -> Task:
    """Task: Evaluate check-in for safety alerts."""
    return Task(
        description=(
            f"Evaluate the check-in results for {senior_name} ({phone}) "
            f"for safety concerns. Use the analysis from previous tasks to check for:\n"
            f"1. Emergency symptoms (chest pain, falls, breathing difficulty)\n"
            f"2. Low wellness score (below 4)\n"
            f"3. Missed medications\n"
            f"4. Signs of loneliness or depression\n"
            f"5. Service requests that need follow-up\n\n"
            f"Trigger appropriate alerts using the evaluate_alerts tool."
        ),
        expected_output=(
            "List of alerts triggered with severity levels (critical/high/medium/low) "
            "and recommended actions. If no alerts needed, state 'No alerts triggered.'"
        ),
        agent=agent,
    )
