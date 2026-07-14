from pydantic import BaseModel
from typing import Optional, List
import datetime

# User Schemas
class UserBase(BaseModel):
    name: str
    email: str
    territory: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    therapeutic_area: str
    indication: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    class Config:
        from_attributes = True

# HCP Schemas
class HCPBase(BaseModel):
    name: str
    specialty: str
    hospital: str
    npi: str
    tier: Optional[str] = "Tier 2"
    phone: Optional[str] = None
    email: Optional[str] = None
    current_sentiment: Optional[float] = 0.0

class HCPCreate(HCPBase):
    pass

class HCP(HCPBase):
    id: int
    class Config:
        from_attributes = True

# FollowUp Schemas
class FollowUpBase(BaseModel):
    hcp_id: int
    due_date: datetime.date
    task_description: str
    priority: Optional[str] = "Medium"
    completed: Optional[bool] = False

class FollowUpCreate(FollowUpBase):
    interaction_id: Optional[int] = None

class FollowUp(FollowUpBase):
    id: int
    interaction_id: Optional[int] = None
    class Config:
        from_attributes = True

# Interaction Schemas
class InteractionBase(BaseModel):
    hcp_id: int
    user_id: int
    date: datetime.date
    interaction_type: str
    notes: Optional[str] = None
    sentiment: Optional[str] = "Neutral"
    outcome: Optional[str] = None
    ai_summary: Optional[str] = None
    products_discussed: Optional[str] = None
    next_steps: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    notes: Optional[str] = None
    sentiment: Optional[str] = None
    outcome: Optional[str] = None
    ai_summary: Optional[str] = None
    products_discussed: Optional[str] = None
    next_steps: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[datetime.date] = None

class Interaction(InteractionBase):
    id: int
    created_at: datetime.datetime
    hcp: Optional[HCP] = None
    rep: Optional[User] = None
    followups: List[FollowUp] = []

    class Config:
        from_attributes = True

# Chat Schemas
class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    id: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    user_id: int = 1

class ChatResponse(BaseModel):
    response: str
    history: List[ChatMessage]
    state_updates: Optional[dict] = None
