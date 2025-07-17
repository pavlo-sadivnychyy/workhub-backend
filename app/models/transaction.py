from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TransactionType(str, enum.Enum):
    ESCROW_FUND = "escrow_fund"  # Client funds escrow
    ESCROW_RELEASE = "escrow_release"  # Release to freelancer
    ESCROW_REFUND = "escrow_refund"  # Refund to client
    MILESTONE_FUND = "milestone_fund"  # Fund specific milestone
    MILESTONE_RELEASE = "milestone_release"  # Release milestone payment
    CONNECTS_PURCHASE = "connects_purchase"
    SUBSCRIPTION_PAYMENT = "subscription_payment"
    PROFILE_PROMOTION = "profile_promotion"
    WITHDRAWAL = "withdrawal"
    COMMISSION = "commission"  # Platform commission


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    MONOBANK = "monobank"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Transaction parties
    payer_id = Column(Integer, ForeignKey("users.id"))
    payee_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="UAH")
    
    # Commission tracking
    commission_amount = Column(Float, default=0)
    commission_rate = Column(Float, default=0)
    net_amount = Column(Float)  # Amount after commission
    
    # Payment details
    payment_method = Column(Enum(PaymentMethod))
    monobank_invoice_id = Column(String(255), unique=True)
    monobank_transaction_id = Column(String(255))
    
    # Status
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Additional info
    description = Column(Text)
    extra_data = Column(Text)  # JSON string for additional data
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    payer = relationship("User", back_populates="transactions_as_payer", foreign_keys=[payer_id])
    payee = relationship("User", back_populates="transactions_as_payee", foreign_keys=[payee_id])
    project = relationship("Project", back_populates="transactions")