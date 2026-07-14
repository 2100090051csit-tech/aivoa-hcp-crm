import os
import sys
import datetime
import json
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Ensure the backend directory is in python search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base, SessionLocal, get_db
from models import User, HCP, Product, Interaction, FollowUp
from schemas import (
    HCP as HCPSchema,
    Interaction as InteractionSchema,
    InteractionCreate,
    InteractionUpdate,
    FollowUp as FollowUpSchema,
    Product as ProductSchema,
    ChatRequest,
    ChatResponse,
    ChatMessage
)
from seed import seed_data
from agent.graph import compiled_graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

# Initialize DB tables
Base.metadata.create_all(bind=engine)

# Auto seed database on startup
db = SessionLocal()
try:
    seed_data(db)
finally:
    db.close()

app = FastAPI(
    title="AI-First HCP CRM Backend",
    description="FastAPI Backend for HCP CRM with LangGraph Agentic Orchestrator",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- REST REST Routes -----------------

@app.get("/")
def read_root():
    return {"status": "ok", "app": "AI-First HCP CRM Backend API", "groq_configured": os.getenv("GROQ_API_KEY") is not None}

# HCP Endpoints
@app.get("/api/hcps", response_model=List[HCPSchema])
def get_hcps(db: Session = Depends(get_db)):
    return db.query(HCP).all()

@app.get("/api/hcps/{hcp_id}", response_model=HCPSchema)
def get_hcp_details(hcp_id: int, db: Session = Depends(get_db)):
    hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found.")
    return hcp

# Product Endpoints
@app.get("/api/products", response_model=List[ProductSchema])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

# Interactions Endpoints
@app.get("/api/interactions", response_model=List[InteractionSchema])
def get_interactions(db: Session = Depends(get_db)):
    return db.query(Interaction).order_by(Interaction.date.desc(), Interaction.id.desc()).all()

@app.post("/api/interactions", response_model=InteractionSchema, status_code=status.HTTP_201_CREATED)
def create_interaction(interaction: InteractionCreate, db: Session = Depends(get_db)):
    hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=400, detail="Invalid HCP ID.")
        
    # Calculate sentiment weight: Positive=1.0, Neutral=0.0, Negative=-1.0
    sentiment_score = 1.0 if interaction.sentiment == "Positive" else (-1.0 if interaction.sentiment == "Negative" else 0.0)
    hcp.current_sentiment = round((hcp.current_sentiment + sentiment_score) / 2.0, 2)
    
    # Auto AI summary standard mapping
    ai_summary = f"{interaction.interaction_type} interaction with Dr. {hcp.name.replace('Dr. ', '')} regarding {interaction.products_discussed or 'products'}. Notes: {interaction.notes}"

    db_interaction = Interaction(
        hcp_id=interaction.hcp_id,
        user_id=interaction.user_id,
        date=interaction.date,
        interaction_type=interaction.interaction_type,
        notes=interaction.notes,
        sentiment=interaction.sentiment,
        outcome=interaction.outcome,
        ai_summary=ai_summary,
        products_discussed=interaction.products_discussed,
        next_steps=interaction.next_steps
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@app.put("/api/interactions/{interaction_id}", response_model=InteractionSchema)
def update_interaction(interaction_id: int, updates: InteractionUpdate, db: Session = Depends(get_db)):
    db_interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not db_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found.")
        
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_interaction, key, value)
        
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

# Follow-Up Endpoints
@app.get("/api/followups", response_model=List[FollowUpSchema])
def get_followups(completed: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(FollowUp)
    if completed is not None:
        query = query.filter(FollowUp.completed == completed)
    return query.order_by(FollowUp.due_date.asc()).all()

@app.put("/api/followups/{followup_id}/toggle", response_model=FollowUpSchema)
def toggle_followup_status(followup_id: int, db: Session = Depends(get_db)):
    followup = db.query(FollowUp).filter(FollowUp.id == followup_id).first()
    if not followup:
        raise HTTPException(status_code=404, detail="Followup task not found.")
    followup.completed = not followup.completed
    db.commit()
    db.refresh(followup)
    return followup

# LangGraph AI Agent Integration Endpoint
@app.post("/api/chat", response_model=ChatResponse)
def chat_agent(chat_req: ChatRequest):
    """
    HTTP route to send conversational logs to the LangGraph executor.
    Supports chat history context.
    """
    try:
        # Convert schemas.ChatMessage back into LangChain message instances
        # Keep only the last 2 history messages to prevent rate limits and token accumulation
        trimmed_history = chat_req.history[-2:] if len(chat_req.history) > 2 else chat_req.history
        lc_history = []
        for msg in trimmed_history:
            if msg.role == "user":
                lc_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_history.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                lc_history.append(SystemMessage(content=msg.content))
                
        # Append the new user prompt
        lc_history.append(HumanMessage(content=chat_req.message))

        # Run the LangGraph execution flow
        result_state = compiled_graph.invoke({"messages": lc_history})
        
        # Extract the last agent response
        messages = result_state["messages"]
        last_agent_msg = messages[-1]
        
        # Build responding message chain
        updated_history = []
        for m in messages:
            if isinstance(m, HumanMessage):
                updated_history.append(ChatMessage(role="user", content=m.content))
            elif isinstance(m, AIMessage) and m.content:
                updated_history.append(ChatMessage(role="assistant", content=m.content))

        # Prepare state updates and extract tool calls for form synchronization
        triggered_db_updates = False
        extracted_tools = []
        for m in messages:
            # Check standard tool_calls attribute first
            tcalls = getattr(m, "tool_calls", None)
            if not tcalls and hasattr(m, "additional_kwargs"):
                tcalls = m.additional_kwargs.get("tool_calls", None)
                
            if tcalls:
                triggered_db_updates = True
                for tc in tcalls:
                    # Resolve differences in standard ToolMessage formats vs raw dict formats
                    name = tc.name if hasattr(tc, "name") else (tc.get("name") if isinstance(tc, dict) else "")
                    args = tc.args if hasattr(tc, "args") else (tc.get("args") if isinstance(tc, dict) else {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            pass
                    extracted_tools.append({
                        "name": name,
                        "args": args
                    })
                
        return ChatResponse(
            response=last_agent_msg.content,
            history=updated_history,
            state_updates={
                "db_mutated": triggered_db_updates,
                "tool_calls": extracted_tools
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph Error: {str(e)}")

# WebSocket Connection Manager for real-time dashboard updates & persistent chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/api/chat/ws")
async def chat_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            parsed_data = json.loads(data)
            message = parsed_data.get("message")
            history_data = parsed_data.get("history", [])
            
            # Translate message history
            lc_history = []
            for h in history_data:
                role = h.get("role")
                content = h.get("content")
                if role == "user":
                    lc_history.append(HumanMessage(content=content))
                elif role == "assistant":
                    lc_history.append(AIMessage(content=content))
            
            lc_history.append(HumanMessage(content=message))
            
            # LangGraph processing
            result = compiled_graph.invoke({"messages": lc_history})
            last_agent_msg = result["messages"][-1]
            
            # Respond to client
            await websocket.send_json({
                "response": last_agent_msg.content,
                "db_mutated": "tool_calls" in getattr(result["messages"][-2], "additional_kwargs", {}) or "tool_calls" in getattr(last_agent_msg, "additional_kwargs", {})
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        manager.disconnect(websocket)
