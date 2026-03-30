"""CRUD endpoints for senior profiles — stored in Neo4j."""

from fastapi import APIRouter, HTTPException

from app.models.senior import Senior
from app.graph_db import create_senior, get_senior, list_seniors, delete_senior

router = APIRouter(prefix="/api/seniors", tags=["seniors"])


@router.post("", status_code=201)
async def add_senior(senior: Senior):
    existing = get_senior(senior.phone)
    if existing:
        raise HTTPException(status_code=409, detail="Senior already exists")
    contacts = [c.model_dump() for c in senior.emergency_contacts]
    return create_senior(senior.name, senior.phone, senior.medications,
                         senior.checkin_schedule, senior.notes, contacts)


@router.get("")
async def get_all_seniors():
    return list_seniors()


@router.get("/{phone}")
async def get_one_senior(phone: str):
    s = get_senior(phone)
    if not s:
        raise HTTPException(status_code=404, detail="Senior not found")
    return s


@router.delete("/{phone}")
async def remove_senior(phone: str):
    if not delete_senior(phone):
        raise HTTPException(status_code=404, detail="Senior not found")
    return {"status": "deleted"}
