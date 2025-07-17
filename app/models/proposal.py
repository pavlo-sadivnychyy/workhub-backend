from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Proposal(Base):
    __tablename__ = "proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Proposal details
    cover_letter = Column(Text, nullable=False)
    proposed_amount = Column(Float, nullable=False)  # For fixed price
    proposed_hourly_rate = Column(Float)  # For hourly
    estimated_duration = Column(String(100))  # e.g., "2 weeks", "1 month"
    
    # Milestones proposed by freelancer (for fixed price)
    proposed_milestones = Column(Text)  # JSON string of milestones
    
    # Attachments
    attachments = Column(Text)  # JSON string of attachment URLs
    
    # Status
    status = Column(Enum(ProposalStatus), default=ProposalStatus.PENDING)
    connects_spent = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="proposals")
    freelancer = relationship("User", back_populates="proposals")