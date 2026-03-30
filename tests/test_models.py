"""Unit tests for Pydantic models."""

from app.models.senior import Senior, EmergencyContact


def test_senior_minimal():
    s = Senior(name="Dorothy Williams", phone="+14155551003")
    assert s.name == "Dorothy Williams"
    assert s.phone == "+14155551003"
    assert s.medications == []
    assert s.emergency_contacts == []
    assert s.checkin_schedule == "09:00"
    assert s.notes == ""


def test_senior_full():
    s = Senior(
        name="Margaret Johnson",
        phone="+14155551001",
        medications=["Metformin 500mg", "Lisinopril 10mg"],
        emergency_contacts=[
            EmergencyContact(name="Sarah", phone="+14155552001", relation="daughter")
        ],
        checkin_schedule="08:30",
        notes="Lives alone",
    )
    assert len(s.medications) == 2
    assert s.emergency_contacts[0].name == "Sarah"
    assert s.emergency_contacts[0].relation == "daughter"


def test_emergency_contact():
    c = EmergencyContact(name="James", phone="+14155552003", relation="son")
    assert c.name == "James"
    assert c.relation == "son"
