from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, Enum, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class ProjectType(str, enum.Enum):
    FIXED_PRICE = "fixed_price"
    HOURLY = "hourly"


class ProjectDuration(str, enum.Enum):
    LESS_THAN_WEEK = "less_than_week"
    LESS_THAN_MONTH = "less_than_month"
    ONE_TO_THREE_MONTHS = "one_to_three_months"
    THREE_TO_SIX_MONTHS = "three_to_six_months"
    MORE_THAN_SIX_MONTHS = "more_than_six_months"


class ExperienceLevel(str, enum.Enum):
    ENTRY = "entry"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic info
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100))
    
    # Project details
    project_type = Column(Enum(ProjectType), nullable=False)
    budget_min = Column(Float)
    budget_max = Column(Float)
    hourly_rate_min = Column(Float)
    hourly_rate_max = Column(Float)
    duration = Column(Enum(ProjectDuration))
    experience_level = Column(Enum(ExperienceLevel), default=ExperienceLevel.INTERMEDIATE)
    
    # Requirements
    skills_required = Column(JSON, default=list)  # List of required skills
    attachments = Column(JSON, default=list)  # List of attachment URLs
    
    # Proposal settings
    connects_to_apply = Column(Integer, default=2)  # Number of connects needed to apply
    proposals_limit = Column(Integer)  # Max number of proposals
    
    # Status
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    is_urgent = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Selected freelancer
    selected_freelancer_id = Column(Integer, ForeignKey("users.id"))
    
    # Stats
    views_count = Column(Integer, default=0)
    proposals_count = Column(Integer, default=0)
    
    # Escrow
    escrow_funded = Column(Boolean, default=False)
    escrow_amount = Column(Float, default=0)
    
    # Milestones for fixed price projects
    milestones = Column(JSON, default=list)  # List of milestone objects
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published_at = Column(DateTime)
    deadline = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    client = relationship("User", back_populates="projects", foreign_keys=[client_id])
    selected_freelancer = relationship("User", foreign_keys=[selected_freelancer_id])
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="project")
    reviews = relationship("Review", back_populates="project")
    transactions = relationship("Transaction", back_populates="project")
    time_entries = relationship("TimeEntry", back_populates="project")