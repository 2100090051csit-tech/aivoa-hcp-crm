import datetime
import json
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from database import SessionLocal
from models import HCP, Interaction, FollowUp, Product, User

# Helper to execute queries safely with self-contained DB sessions
class DBSession:
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        self.db.close()

@tool
def get_hcp_profile(name_query: str) -> str:
    """
    Search and retrieve the complete profile of a Healthcare Professional (HCP) by name.
    Use this to find NPI, hospital, specialty, average current sentiment, and interaction history.
    """
    with DBSession() as db:
        hcp = db.query(HCP).filter(HCP.name.like(f"%{name_query}%")).first()
        if not hcp:
            # Try a split search
            parts = name_query.replace("Dr.", "").strip().split()
            if parts:
                hcp = db.query(HCP).filter(HCP.name.like(f"%{parts[0]}%")).first()
        
        if not hcp:
            # Let's list some known HCPs to help the LLM correct itself
            all_hcps = db.query(HCP).limit(5).all()
            hcp_names = [h.name for h in all_hcps]
            return json.dumps({
                "status": "error",
                "message": f"HCP '{name_query}' not found.",
                "known_hcps": hcp_names
            })

        # Fetch recent interactions
        interactions = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).order_by(Interaction.date.desc()).limit(3).all()
        inter_list = []
        for i in interactions:
            inter_list.append({
                "id": i.id,
                "date": str(i.date),
                "type": i.interaction_type,
                "sentiment": i.sentiment,
                "products": i.products_discussed,
                "summary": i.ai_summary
            })

        # Fetch pending follow-ups
        followups = db.query(FollowUp).filter(FollowUp.hcp_id == hcp.id, FollowUp.completed == False).all()
        f_list = [{
            "id": f.id,
            "due_date": str(f.due_date),
            "task": f.task_description,
            "priority": f.priority
        } for f in followups]

        profile = {
            "id": hcp.id,
            "name": hcp.name,
            "specialty": hcp.specialty,
            "hospital": hcp.hospital,
            "npi": hcp.npi,
            "tier": hcp.tier,
            "phone": hcp.phone,
            "email": hcp.email,
            "current_sentiment": hcp.current_sentiment,
            "recent_interactions": inter_list,
            "pending_followups": f_list
        }
        return json.dumps({"status": "success", "data": profile}, indent=2)

@tool
def log_interaction(
    hcp_id: int,
    interaction_type: str,
    notes: str,
    sentiment: str = "Neutral",
    products_discussed: Optional[str] = None,
    outcome: Optional[str] = None,
    next_steps: Optional[str] = None,
    date_str: Optional[str] = None
) -> str:
    """
    Log a new interaction with an HCP.
    
    Inputs:
    - hcp_id: Database ID of the HCP.
    - interaction_type: 'In-Person', 'Call', 'Email', or 'Video'.
    - notes: Raw conversation notes.
    - sentiment: 'Positive', 'Neutral', or 'Negative'.
    - products_discussed: Comma separated products discussed, e.g., 'Keytruda' or 'Jardiance'.
    - outcome: Short summary of the discussion outcome.
    - next_steps: Planned next steps.
    - date_str: Optional date (YYYY-MM-DD), default is today.
    """
    if date_str:
        try:
            interaction_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            interaction_date = datetime.date.today()
    else:
        interaction_date = datetime.date.today()

    with DBSession() as db:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"status": "error", "message": f"HCP with ID {hcp_id} does not exist."})
        
        # Simple AI Summary generation if not provided (mocking a mini LLM summary for speed, backend main can enrich it)
        ai_summary = f"{interaction_type} interaction with Dr. {hcp.name.replace('Dr. ', '')} discussing {products_discussed or 'products'}. Notes: {notes[:100]}..."

        new_interaction = Interaction(
            hcp_id=hcp_id,
            user_id=1,  # Default Rep ID
            date=interaction_date,
            interaction_type=interaction_type,
            notes=notes,
            sentiment=sentiment,
            outcome=outcome,
            ai_summary=ai_summary,
            products_discussed=products_discussed,
            next_steps=next_steps,
            created_at=datetime.datetime.utcnow()
        )
        
        db.add(new_interaction)
        db.flush()
        interaction_id = new_interaction.id

        # Update HCP's average sentiment
        # Calculate numeric sentiment weight: Positive=1.0, Neutral=0.0, Negative=-1.0
        sentiment_score = 1.0 if sentiment == "Positive" else (-1.0 if sentiment == "Negative" else 0.0)
        hcp.current_sentiment = (hcp.current_sentiment + sentiment_score) / 2.0
        
        db.commit()
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully logged {interaction_type} interaction under ID {interaction_id} for {hcp.name}.",
            "interaction_id": interaction_id
        })

@tool
def edit_interaction(
    interaction_id: int,
    interaction_type: Optional[str] = None,
    notes: Optional[str] = None,
    sentiment: Optional[str] = None,
    products_discussed: Optional[str] = None,
    outcome: Optional[str] = None,
    next_steps: Optional[str] = None,
    date_str: Optional[str] = None
) -> str:
    """
    Modify an existing interaction record by ID.
    Only pass the fields that need of modification.
    """
    with DBSession() as db:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"status": "error", "message": f"Interaction with ID {interaction_id} not found."})

        # Keep tracking change logs
        updates = []
        if interaction_type is not None:
            interaction.interaction_type = interaction_type
            updates.append("type")
        if notes is not None:
            interaction.notes = notes
            updates.append("notes")
        if sentiment is not None:
            interaction.sentiment = sentiment
            updates.append("sentiment")
        if products_discussed is not None:
            interaction.products_discussed = products_discussed
            updates.append("products_discussed")
        if outcome is not None:
            interaction.outcome = outcome
            updates.append("outcome")
        if next_steps is not None:
            interaction.next_steps = next_steps
            updates.append("next_steps")
        if date_str is not None:
            try:
                interaction.date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                updates.append("date")
            except ValueError:
                pass

        if updates:
            db.commit()
            return json.dumps({
                "status": "success",
                "message": f"Successfully updated fields {updates} for interaction ID {interaction_id}."
            })
        else:
            return json.dumps({
                "status": "warning",
                "message": "No new values provided; interaction records were not mutated."
            })

@tool
def schedule_followup(
    hcp_id: str,  # accept string or int, will be cast to int
    task_description: str,
    days_from_now: Optional[int] = None,
    due_date_str: Optional[str] = None,
    priority: str = "Medium",
    interaction_id: Optional[int] = None
) -> str:
    """
    Schedules a follow-up reminder task for an HCP.

    Inputs:
    - hcp_id: The database ID of the HCP (string or int).
    - task_description: What needs to be done.
    - days_from_now: Days until due (e.g. 3, 7). Or specify due_date_str.
    - due_date_str: Specific due date (YYYY-MM-DD).
    - priority: 'High', 'Medium', or 'Low'.
    - interaction_id: Optional related interaction ID.
    """
    # Cast hcp_id to int if it's a string
    try:
        hcp_id_int = int(hcp_id)
    except (ValueError, TypeError):
        return json.dumps({"status": "error", "message": f"Invalid hcp_id '{hcp_id}'. Must be an integer."})

    if due_date_str:
        try:
            target_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.date.today() + datetime.timedelta(days=days_from_now or 3)
    else:
        days = days_from_now if days_from_now is not None else 3
        target_date = datetime.date.today() + datetime.timedelta(days=days)

    with DBSession() as db:
        hcp = db.query(HCP).filter(HCP.id == hcp_id_int).first()
        if not hcp:
            return json.dumps({"status": "error", "message": f"HCP ID {hcp_id} not found."})

        new_followup = FollowUp(
            hcp_id=hcp_id_int,
            interaction_id=interaction_id,
            due_date=target_date,
            task_description=task_description,
            priority=priority,
            completed=False
        )
        db.add(new_followup)
        db.commit()
        
        return json.dumps({
            "status": "success",
            "message": f"Follow-up task scheduled for Dr. {hcp.name.replace('Dr. ', '')} on {str(target_date)}: '{task_description}'."
        })

@tool
def search_interactions(
    query: str,
    hcp_id: Optional[int] = None,
    product_name: Optional[str] = None
) -> str:
    """
    Search past HCP interactions using a search term (checks notes, outcomes, summaries) 
    and optional filters like hcp_id or product_name discussed.
    """
    with DBSession() as db:
        q = db.query(Interaction)
        
        if hcp_id:
            q = q.filter(Interaction.hcp_id == hcp_id)
        if product_name:
            q = q.filter(Interaction.products_discussed.like(f"%{product_name}%"))
        
        # Keyword search
        q = q.filter(
            (Interaction.notes.like(f"%{query}%")) |
            (Interaction.outcome.like(f"%{query}%")) |
            (Interaction.ai_summary.like(f"%{query}%")) |
            (Interaction.products_discussed.like(f"%{query}%"))
        )

        results = q.order_by(Interaction.date.desc()).limit(10).all()
        
        serial = []
        for i in results:
            serial.append({
                "id": i.id,
                "hcp_name": i.hcp.name,
                "date": str(i.date),
                "type": i.interaction_type,
                "products": i.products_discussed,
                "summary": i.ai_summary,
                "sentiment": i.sentiment,
                "next_steps": i.next_steps
            })
            
        return json.dumps({
            "status": "success",
            "query": query,
            "count": len(serial),
            "results": serial
        }, indent=2)

# Group tools list for LangGraph compilation
tools_list = [
    get_hcp_profile,
    log_interaction,
    edit_interaction,
    schedule_followup,
    search_interactions
]
