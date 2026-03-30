"""CrewAI multi-agent endpoints for CareGraph."""

import asyncio

from fastapi import APIRouter, HTTPException

from app.graph_db import get_senior
from app.crew.care_crew import (
    run_full_checkin_crew,
    run_analysis_crew,
    run_graph_insights_crew,
)

router = APIRouter(prefix="/api/crew", tags=["crew"])


@router.post("/checkin/{phone}")
async def crew_full_checkin(phone: str):
    """Run the full CrewAI check-in pipeline: call → analyze → graph → recommend → alert.

    This kicks off all 5 agents in sequence:
    1. Check-in Agent calls the senior via Bland AI
    2. Analysis Agent extracts health data from transcript
    3. Graph Agent queries Neo4j for drug interactions and patterns
    4. Recommendation Agent generates a care plan
    5. Alert Agent evaluates urgency and triggers notifications
    """
    senior = get_senior(phone)
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    # Run crew in thread pool to avoid blocking the event loop
    result = await asyncio.to_thread(run_full_checkin_crew, phone)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/analyze/{phone}")
async def crew_analyze_transcript(phone: str, transcript: str = "I'm feeling a bit dizzy today. Yes I took my medications but my head hurts."):
    """Run the analysis CrewAI pipeline on a transcript.

    Skips the voice call — uses the provided transcript directly.
    Agents: Analysis → Graph → Recommendation → Alert
    """
    senior = get_senior(phone)
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    result = await asyncio.to_thread(run_analysis_crew, phone, transcript)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/insights/{phone}")
async def crew_graph_insights(phone: str):
    """Run graph analysis + recommendation crew (no call, no transcript).

    Agents: Graph Agent → Recommendation Agent
    Useful for on-demand care network analysis.
    """
    senior = get_senior(phone)
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    result = await asyncio.to_thread(run_graph_insights_crew, phone)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
