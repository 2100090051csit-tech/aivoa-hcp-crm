from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    territory = Column(String(100), nullable=True)

    interactions = relationship("Interaction", back_populates="rep")

class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)  # e.g., Cardiology, Oncology
    hospital = Column(String(150), nullable=False)
    npi = Column(String(10), unique=True, nullable=False)  # National Provider Identifier
    tier = Column(String(100), default="Tier 2")  # Tier 1 (High Value), Tier 2, Tier 3
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    current_sentiment = Column(Float, default=0.0)  # average interaction score (-1.0 to 1.0 or 0 to 10)

    interactions = relationship("Interaction", back_populates="hcp")
    followups = relationship("FollowUp", back_populates="hcp")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    therapeutic_area = Column(String(100), nullable=False)  # e.g., Cardiovascular, Immunology
    indication = Column(String(200), nullable=True)  # e.g., Heart Failure, Plaque Psoriasis

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, default=datetime.date.today)
    interaction_type = Column(String(50), nullable=False)  # In-Person, Call, Email, Video
    notes = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)  # Positive, Neutral, Negative
    outcome = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    products_discussed = Column(String(200), nullable=True)  # Comma-separated list for simplicity in sqlite
    next_steps = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    rep = relationship("User", back_populates="interactions")
    followups = relationship("FollowUp", back_populates="interaction")

class FollowUp(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    due_date = Column(Date, nullable=False)
    task_description = Column(Text, nullable=False)
    priority = Column(String(20), default="Medium")  # High, Medium, Low
    completed = Column(Boolean, default=False)

    interaction = relationship("Interaction", back_populates="followups")
    hcp = relationship("HCP", back_populates="followups")
