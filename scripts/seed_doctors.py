"""Seed doctor and dermatologist data from BetaFund-CareCompanion into Neo4j."""

import sys
import os
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph_db import get_driver, setup_schema

DOCTORS_CSV = "/Users/sankar/hackathons/BetaFund-CareCompanion/crawling_agent/doctors_data.csv"
DERMATOLOGISTS_CSV = "/Users/sankar/hackathons/BetaFund-CareCompanion/crawling_agent/dermatologists_data.csv"


def clean(val):
    """Clean a CSV value."""
    if not val or val in ("Not specified", "Not displayed", "0.0", "0.0 out of 5"):
        return None
    return val.strip()


def parse_rating(val):
    """Parse rating like '4.9' or '4.9 out of 5'."""
    if not val or val in ("Not specified", "Not displayed"):
        return None
    val = val.replace(" out of 5", "").strip()
    try:
        r = float(val)
        return r if r > 0 else None
    except ValueError:
        return None


def seed_doctors():
    driver = get_driver()
    setup_schema()

    # Create constraints for Doctor and Clinic
    with driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Doctor) REQUIRE d.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Clinic) REQUIRE c.name IS UNIQUE")
        session.run("CREATE INDEX IF NOT EXISTS FOR (d:Doctor) ON (d.specialty)")

    count = 0

    # ── Primary Care Doctors ──
    print("Loading primary care doctors...")
    with open(DOCTORS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = clean(row.get("Name"))
            if not name:
                continue

            specialty = clean(row.get("Specialty")) or "Internal medicine"
            rating = parse_rating(row.get("Rating"))
            title = clean(row.get("Clinical Title"))
            clinic_name = clean(row.get("Clinic Name"))
            address = clean(row.get("Address"))
            city = clean(row.get("City"))
            state = clean(row.get("State"))
            zipcode = clean(row.get("Zip"))
            phone = clean(row.get("Phone"))
            languages = clean(row.get("Additional Languages"))
            interests = clean(row.get("Areas of Interest"))

            with driver.session() as session:
                # Create Doctor node
                session.run("""
                    MERGE (d:Doctor {name: $name})
                    SET d.specialty = $specialty,
                        d.rating = $rating,
                        d.clinical_title = $title,
                        d.phone = $phone,
                        d.city = $city,
                        d.state = $state,
                        d.zip = $zipcode,
                        d.address = $address,
                        d.languages = $languages,
                        d.areas_of_interest = $interests,
                        d.accepting_patients = true,
                        d.source = 'stanford_primary_care'
                """, name=name, specialty=specialty, rating=rating, title=title,
                    phone=phone, city=city, state=state, zipcode=zipcode,
                    address=address, languages=languages, interests=interests)

                # Create Clinic and link
                if clinic_name:
                    session.run("""
                        MERGE (c:Clinic {name: $clinic_name})
                        SET c.address = $address, c.city = $city,
                            c.state = $state, c.zip = $zipcode, c.phone = $phone
                        WITH c
                        MATCH (d:Doctor {name: $name})
                        MERGE (d)-[:PRACTICES_AT]->(c)
                    """, clinic_name=clinic_name, address=address, city=city,
                        state=state, zipcode=zipcode, phone=phone, name=name)

                # Link senior health doctors to Senior nodes
                if interests and "senior health" in interests.lower():
                    session.run("""
                        MATCH (d:Doctor {name: $name})
                        SET d.senior_care = true
                    """, name=name)

                count += 1

    print(f"  Loaded {count} primary care doctors")

    # ── Dermatologists ──
    derm_count = 0
    print("Loading dermatologists...")
    with open(DERMATOLOGISTS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = clean(row.get("Name"))
            if not name:
                continue

            credentials = clean(row.get("Credentials"))
            rating = parse_rating(row.get("Rating"))
            num_reviews = clean(row.get("Number of Reviews"))
            group = clean(row.get("Medical Group"))
            facility = clean(row.get("Location/Facility"))
            address = clean(row.get("Address"))
            phone = clean(row.get("Phone"))
            specialty = clean(row.get("Specialty")) or "Dermatology"
            accepting = row.get("Accepting New Patients", "")

            full_name = f"{name}, {credentials}" if credentials else name
            is_accepting = "yes" in accepting.lower() if accepting else True

            with driver.session() as session:
                session.run("""
                    MERGE (d:Doctor {name: $name})
                    SET d.specialty = $specialty,
                        d.rating = $rating,
                        d.num_reviews = $num_reviews,
                        d.phone = $phone,
                        d.address = $address,
                        d.medical_group = $group,
                        d.accepting_patients = $accepting,
                        d.source = 'palo_alto_dermatology'
                """, name=full_name, specialty=specialty, rating=rating,
                    num_reviews=num_reviews, phone=phone, address=address,
                    group=group, accepting=is_accepting)

                # Create clinic link
                clinic = facility or group
                if clinic:
                    session.run("""
                        MERGE (c:Clinic {name: $clinic_name})
                        SET c.address = $address, c.phone = $phone
                        WITH c
                        MATCH (d:Doctor {name: $name})
                        MERGE (d)-[:PRACTICES_AT]->(c)
                    """, clinic_name=clinic, address=address, phone=phone, name=full_name)

                derm_count += 1

    print(f"  Loaded {derm_count} dermatologists")

    # ── Link doctors to conditions via specialty ──
    print("\nLinking doctors to conditions...")
    with driver.session() as session:
        # Internal medicine / Family medicine → general conditions
        session.run("""
            MATCH (d:Doctor)
            WHERE d.specialty CONTAINS 'Internal medicine' OR d.specialty CONTAINS 'Family medicine'
            MATCH (c:Condition)
            WHERE c.name IN ['Hypertension', 'Dehydration', 'Cardiac Event', 'Cognitive Decline', 'Depression Risk', 'Fall Risk']
            MERGE (d)-[:CAN_TREAT]->(c)
        """)

        # Dermatologists → skin conditions
        session.run("""
            MERGE (c:Condition {name: 'Skin Condition'})
            WITH c
            MATCH (d:Doctor) WHERE d.specialty CONTAINS 'Dermatology'
            MERGE (d)-[:CAN_TREAT]->(c)
        """)

        # Senior health specialists → link to senior nodes
        session.run("""
            MATCH (d:Doctor) WHERE d.senior_care = true
            MATCH (s:Senior)
            MERGE (d)-[:RECOMMENDED_FOR]->(s)
        """)

    # ── Summary stats ──
    with driver.session() as session:
        result = session.run("MATCH (d:Doctor) RETURN count(d) AS total")
        total = result.single()["total"]
        result = session.run("MATCH (c:Clinic) RETURN count(c) AS total")
        clinics = result.single()["total"]
        result = session.run("MATCH (d:Doctor)-[:CAN_TREAT]->(c:Condition) RETURN count(DISTINCT d) AS total")
        linked = result.single()["total"]

    print(f"\nDone! {total} doctors, {clinics} clinics in Neo4j graph")
    print(f"  {linked} doctors linked to conditions via CAN_TREAT")
    print(f"\nGraph queries:")
    print(f"  Find a doctor: MATCH (d:Doctor) WHERE d.specialty CONTAINS 'Internal medicine' AND d.city = 'San Jose' RETURN d")
    print(f"  Senior care doctors: MATCH (d:Doctor {{senior_care: true}}) RETURN d.name, d.phone, d.city")
    print(f"  Dermatologists: MATCH (d:Doctor) WHERE d.specialty CONTAINS 'Dermatology' RETURN d.name, d.phone")


if __name__ == "__main__":
    seed_doctors()
