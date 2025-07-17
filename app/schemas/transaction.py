from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from app.models.transaction import TransactionType, TransactionStatus, PaymentMethod


class TransactionBase(BaseModel):
    transaction_type: TransactionType
    amount: float = Field(..., gt=0)
    description: Optional[str] = None


class EscrowFund(TransactionBase):
    project_id: int
    transaction_type: TransactionType = TransactionType.ESCROW_FUND


class MilestoneFund(TransactionBase):
    project_id: int
    milestone_id: int
    transaction_type: TransactionType = TransactionType.MILESTONE_FUND


class WithdrawalRequest(BaseModel):
    amount: float = Field(..., gt=0)
    is_express: bool = False
    card_number: str = Field(..., pattern=r'^\d{16}$')
    
    @property
    def fee(self) -> int:
        from app.config import settings
        return settings.WITHDRAWAL_FEE_EXPRESS if self.is_express else settings.WITHDRAWAL_FEE_REGULAR


class TransactionInDBBase(TransactionBase):
    id: int
    payer_id: Optional[int]
    payee_id: Optional[int]
    project_id: Optional[int]
    status: TransactionStatus
    payment_method: Optional[PaymentMethod]
    commission_amount: float
    commission_rate: float
    net_amount: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class Transaction(TransactionInDBBase):
    payer: Optional[Dict] = None
    payee: Optional[Dict] = None
    project: Optional[Dict] = None
    metadata: Optional[Dict] = None


class TransactionList(BaseModel):
    id: int
    transaction_type: TransactionType
    amount: float
    status: TransactionStatus
    description: Optional[str]
    created_at: datetime
    
    # Simplified info
    other_party_name: Optional[str]
    project_title: Optional[str]
    
    class Config:
        from_attributes = True


class PaymentInvoice(BaseModel):
    invoice_id: str
    payment_url: str
    amount: float
    description: str
    expires_at: datetime