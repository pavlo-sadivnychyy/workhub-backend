from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TimeEntryStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class TimeEntry(Base):
    __tablename__ = "time_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Time tracking
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    hours_worked = Column(Float, nullable=False)
    hourly_rate = Column(Float, nullable=False)
    
    # Work details
    description = Column(Text)
    screenshot_urls = Column(Text)  # JSON string of screenshot URLs
    activity_level = Column(Float)  # 0-100% activity level
    
    # Status
    status = Column(Enum(TimeEntryStatus), default=TimeEntryStatus.PENDING)
    
    # Billing
    amount = Column(Float, nullable=False)  # hours * rate
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    approved_at = Column(DateTime)
    paid_at = Column(DateTime)
    
    # Relationships
    project = relationship("Project", back_populates="time_entries")
    freelancer = relationship("User", foreign_keys=[freelancer_id])
    transaction = relationship("Transaction")