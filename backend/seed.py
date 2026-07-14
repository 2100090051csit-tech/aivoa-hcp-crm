import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models import User, HCP, Product, Interaction, FollowUp

def seed_data(db: Session):
    # Check if database is already seeded
    if db.query(User).first() is not None:
        print("Database already seeded.")
        return

    print("Seeding database...")

    # 1. Create a default User (Sales Rep)
    rep = User(
        id=1,
        name="Aarav Sharma",
        email="aarav.sharma@pharma.com",
        territory="Mumbai Metro West"
    )
    db.add(rep)
    db.commit()

    # 2. Create Products
    products = [
        Product(id=1, name="Keytruda", therapeutic_area="Oncology", indication="Non-Small Cell Lung Cancer & Melanoma"),
        Product(id=2, name="Jardiance", therapeutic_area="Cardiology", indication="Type 2 Diabetes & Heart Failure Reduction"),
        Product(id=3, name="Humira", therapeutic_area="Immunology", indication="Moderate to Severe Rheumatoid Arthritis"),
        Product(id=4, name="Gardasil 9", therapeutic_area="Immunology", indication="Human Papillomavirus Prevention"),
        Product(id=5, name="Entresto", therapeutic_area="Cardiology", indication="Chronic Heart Failure"),
    ]
    for p in products:
        db.merge(p)
    db.commit()

    # 3. Create HCPs (Indian Physicians & Hospital Affiliations)
    hcps = [
        HCP(
            id=1,
            name="Dr. Rajesh Kumar",
            specialty="Oncology",
            hospital="Tata Memorial Hospital, Mumbai",
            npi="1982736450",
            tier="Tier 1 (High Value)",
            phone="022-24177000",
            email="rajesh.kumar@tmc.gov.in",
            current_sentiment=0.8
        ),
        HCP(
            id=2,
            name="Dr. Ananya Sharma",
            specialty="Cardiology",
            hospital="AIIMS, New Delhi",
            npi="1029384756",
            tier="Tier 1 (High Value)",
            phone="011-26588500",
            email="ananya.sharma@aiims.edu",
            current_sentiment=0.4
        ),
        HCP(
            id=3,
            name="Dr. Vikram Adiga",
            specialty="Immunology",
            hospital="Apollo Hospitals, Chennai",
            npi="1564738290",
            tier="Tier 2 (Moderate Value)",
            phone="044-28290200",
            email="dr_vikram@apollohospitals.com",
            current_sentiment=0.0
        ),
        HCP(
            id=4,
            name="Dr. Priya Patel",
            specialty="Cardiology",
            hospital="Fortis Escorts Heart Institute, Okhla",
            npi="1144225588",
            tier="Tier 3 (Standard)",
            phone="011-47135000",
            email="priya.patel@fortishealthcare.com",
            current_sentiment=-0.2
        ),
        HCP(
            id=5,
            name="Dr. Smith",
            specialty="Oncology",
            hospital="Memorial Sloan Kettering, NY",
            npi="1000200030",
            tier="Tier 1 (High Value)",
            phone="212-639-2000",
            email="smith@mskcc.org",
            current_sentiment=0.5
        ),
        HCP(
            id=6,
            name="Dr. John",
            specialty="Cardiology",
            hospital="Johns Hopkins Hospital, MD",
            npi="4000500060",
            tier="Tier 2 (Moderate Value)",
            phone="410-955-5000",
            email="john@jhmi.edu",
            current_sentiment=0.0
        )
    ]
    for h in hcps:
        db.merge(h)
    db.commit()

    # 4. Create Interactions (Modified with Indian doctor details)
    today = datetime.date.today()
    interactions = [
        Interaction(
            id=1,
            hcp_id=1,
            user_id=1,
            date=today - datetime.timedelta(days=5),
            interaction_type="In-Person",
            notes="Discussed Keytruda efficacy clinical trials for stage III NSCLC. Dr. Kumar was highly interested in the 5-year survival statistics. He mentioned he has 3 patients who could benefit immediately.",
            sentiment="Positive",
            outcome="Excellent response. Dr. Kumar requested the full Phase III clinical trial report and asked for sample vouchers.",
            ai_summary="Rep Aarav Sharma met with oncologist Dr. Rajesh Kumar in-person to discuss Keytruda's clinical trial results for stage III NSCLC. The doctor showed strong positive interest and asked for survival data reports and drug samples.",
            products_discussed="Keytruda",
            next_steps="Follow up by sending the trial data PDF and deliver samples on the next visit.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=5)
        ),
        Interaction(
            id=2,
            hcp_id=2,
            user_id=1,
            date=today - datetime.timedelta(days=10),
            interaction_type="Call",
            notes="Followed up on Entresto prescription trends. Dr. Sharma mentioned he has concerns about patient copays under certain insurance schemes. Discussed patient access programs in India.",
            sentiment="Neutral",
            outcome="Dr. Sharma agreed to keep Entresto in mind for newly diagnosed heart failure patients, but requested assistance materials for his office staff.",
            ai_summary="Phone call with cardiologist Dr. Ananya Sharma regarding Entresto insurance coverage and copays. Dr. Sharma requested support cards for patients to ease copay friction.",
            products_discussed="Entresto",
            next_steps="Deliver copay access cards to office manager.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=10)
        ),
        Interaction(
            id=3,
            hcp_id=3,
            user_id=1,
            date=today - datetime.timedelta(days=15),
            interaction_type="Email",
            notes="Emailed clinical updates on Humira indications. Dr. Adiga replied asking if there's any update on pediatric dosing guidelines.",
            sentiment="Positive",
            outcome="Opened dialogue on pediatric dosing. She will review the materials.",
            ai_summary="Email interaction with pediatric immunologist Dr. Vikram Adiga. He raised questions about pediatric Humira dosing guidelines.",
            products_discussed="Humira",
            next_steps="Mail the pediatric dosage charts.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=15)
        )
    ]
    for i in interactions:
        db.merge(i)
    db.commit()

    # 5. Create Follow-Ups
    followups = [
        FollowUp(
            id=1,
            interaction_id=1,
            hcp_id=1,
            due_date=today + datetime.timedelta(days=2),
            task_description="Email Phase III Keytruda Clinical Trial dossier to Dr. Rajesh Kumar.",
            priority="High",
            completed=False
        ),
        FollowUp(
            id=2,
            interaction_id=2,
            hcp_id=2,
            due_date=today + datetime.timedelta(days=5),
            task_description="Drop off Entresto patient copay cards and brochures with Dr. Ananya Sharma's office manager.",
            priority="Medium",
            completed=False
        ),
        FollowUp(
            id=3,
            interaction_id=3,
            hcp_id=3,
            due_date=today - datetime.timedelta(days=2),
            task_description="Email pediatric Humira dosing PDF.",
            priority="Low",
            completed=True
        )
    ]
    for f in followups:
        db.merge(f)
    db.commit()

    print("Database seeded successfully!")

if __name__ == "__main__":
    print("Dropping tables to sync new Indian-origin seed names...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    seed_data(db_session)
    db_session.close()
