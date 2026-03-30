"""Alert endpoints — stored in Neo4j."""

from fastapi import APIRouter, HTTPException

from app.graph_db import get_alerts, acknowledge_alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(acknowledged: bool = False):
    return get_alerts(acknowledged)


@router.put("/{alert_id}/acknowledge")
async def ack_alert(alert_id: str):
    result = acknowledge_alert(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result
