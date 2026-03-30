from pydantic import BaseModel


class EmergencyContact(BaseModel):
    name: str
    phone: str
    relation: str


class Senior(BaseModel):
    name: str
    phone: str
    medications: list[str] = []
    emergency_contacts: list[EmergencyContact] = []
    checkin_schedule: str = "09:00"
    notes: str = ""
