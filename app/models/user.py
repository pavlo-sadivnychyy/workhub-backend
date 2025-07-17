from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    FREELANCER = "freelancer"
    CLIENT = "client"
    BOTH = "both"
    ADMIN = "admin"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    EMAIL_VERIFIED = "email_verified"
    DIIA_VERIFIED = "diia_verified"


class SubscriptionType(str, enum.Enum):
    FREE = "free"
    FREELANCER_PLUS = "freelancer_plus"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Personal info
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String(500))
    
    # Role and verification
    role = Column(Enum(UserRole), default=UserRole.FREELANCER, nullable=False)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    diia_request_id = Column(String(255))  # For Diia verification
    
    # Freelancer specific
    title = Column(String(200))
    description = Column(Text)
    hourly_rate = Column(Float)
    skills = Column(JSON, default=list)  # List of skills
    portfolio_items = Column(JSON, default=list)  # List of portfolio items
    categories = Column(JSON, default=list)  # List of categories
    
    # Stats
    total_earned = Column(Float, default=0)
    total_spent = Column(Float, default=0)
    jobs_completed = Column(Integer, default=0)
    rating = Column(Float, default=0)
    reviews_count = Column(Integer, default=0)
    
    # Connects and subscription
    connects_balance = Column(Integer, default=10)
    subscription_type = Column(Enum(SubscriptionType), default=SubscriptionType.FREE)
    subscription_expires_at = Column(DateTime)
    
    # Profile promotion
    profile_promoted_until = Column(DateTime)
    
    # Earnings tracking for commission calculation
    earnings_with_client = Column(JSON, default=dict)  # {client_id: total_earned}
    
    # Status
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen_at = Column(DateTime, default=func.now())
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="client", foreign_keys="Project.client_id")
    proposals = relationship("Proposal", back_populates="freelancer")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    received_messages = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id")
    reviews_given = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    reviews_received = relationship("Review", back_populates="reviewee", foreign_keys="Review.reviewee_id")
    transactions_as_payer = relationship("Transaction", back_populates="payer", foreign_keys="Transaction.payer_id")
    transactions_as_payee = relationship("Transaction", back_populates="payee", foreign_keys="Transaction.payee_id")