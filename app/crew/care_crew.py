"""CareGraph Crew — multi-agent care check-in pipeline.

Two crew configurations:
1. FullCheckInCrew: Bland AI call → analyze → graph → recommend → alert
2. AnalysisOnlyCrew: transcript → analyze → graph → recommend → alert
"""

from __future__ import annotations

import logging

from crewai import Crew, Process

from app.crew.agents import (
    create_checkin_agent,
    create_analysis_agent,
    create_graph_agent,
    create_recommendation_agent,
    create_alert_agent,
)
from app.crew.tasks import (
    create_checkin_call_task,
    create_analysis_task,
    create_graph_analysis_task,
    create_recommendation_task,
    create_alert_task,
)
from app.graph_db import get_senior

logger = logging.getLogger(__name__)


def run_full_checkin_crew(phone: str) -> dict:
    """Run the full check-in pipeline: call → analyze → graph → recommend → alert.

    This initiates a Bland AI voice call, waits for the transcript,
    then runs the full analysis pipeline.
    """
    senior = get_senior(phone)
    if not senior:
        return {"error": f"Senior not found: {phone}"}

    senior_name = senior["name"]
    logger.info("Starting full check-in crew for %s (%s)", senior_name, phone)

    # Create agents
    checkin_agent = create_checkin_agent()
    graph_agent = create_graph_agent()
    recommendation_agent = create_recommendation_agent()
    alert_agent = create_alert_agent()

    # Create tasks (call + graph analysis + recommendation + alerts)
    call_task = create_checkin_call_task(checkin_agent, phone)
    graph_task = create_graph_analysis_task(graph_agent, phone)
    rec_task = create_recommendation_task(recommendation_agent, phone)
    alert_task = create_alert_task(alert_agent, phone, senior_name)

    # Assemble crew
    crew = Crew(
        agents=[checkin_agent, graph_agent, recommendation_agent, alert_agent],
        tasks=[call_task, graph_task, rec_task, alert_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    return {
        "status": "complete",
        "senior": senior_name,
        "phone": phone,
        "crew_output": str(result),
    }


def run_analysis_crew(phone: str, transcript: str) -> dict:
    """Run the analysis-only pipeline: transcript → analyze → graph → recommend → alert.

    Used when we already have a transcript (from webhook or simulation).
    """
    senior = get_senior(phone)
    if not senior:
        return {"error": f"Senior not found: {phone}"}

    senior_name = senior["name"]
    logger.info("Starting analysis crew for %s (%s)", senior_name, phone)

    # Create agents
    analysis_agent = create_analysis_agent()
    graph_agent = create_graph_agent()
    recommendation_agent = create_recommendation_agent()
    alert_agent = create_alert_agent()

    # Create tasks
    analysis_task = create_analysis_task(analysis_agent, phone, transcript)
    graph_task = create_graph_analysis_task(graph_agent, phone)
    rec_task = create_recommendation_task(recommendation_agent, phone)
    alert_task = create_alert_task(alert_agent, phone, senior_name)

    # Assemble crew
    crew = Crew(
        agents=[analysis_agent, graph_agent, recommendation_agent, alert_agent],
        tasks=[analysis_task, graph_task, rec_task, alert_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    return {
        "status": "complete",
        "senior": senior_name,
        "phone": phone,
        "crew_output": str(result),
    }


def run_graph_insights_crew(phone: str) -> dict:
    """Run graph analysis + recommendation only (no call, no transcript).

    Used for on-demand graph intelligence queries.
    """
    senior = get_senior(phone)
    if not senior:
        return {"error": f"Senior not found: {phone}"}

    senior_name = senior["name"]
    logger.info("Starting graph insights crew for %s (%s)", senior_name, phone)

    # Create agents
    graph_agent = create_graph_agent()
    recommendation_agent = create_recommendation_agent()

    # Create tasks
    graph_task = create_graph_analysis_task(graph_agent, phone)
    rec_task = create_recommendation_task(recommendation_agent, phone)

    crew = Crew(
        agents=[graph_agent, recommendation_agent],
        tasks=[graph_task, rec_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    return {
        "status": "complete",
        "senior": senior_name,
        "phone": phone,
        "crew_output": str(result),
    }
