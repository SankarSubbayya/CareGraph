"""Alert endpoints — stored in Neo4j."""

from fastapi import APIRouter, HTTPException, Request

from app.graph_db import get_alerts, acknowledge_alert, dedupe_alerts
from app.security import verify_admin_token

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


@router.post("/dedupe")
async def dedupe_stored_alerts(request: Request):
    """Deduplicate stored alert nodes. Requires ADMIN_API_TOKEN."""
    verify_admin_token(request)
    return dedupe_alerts()
