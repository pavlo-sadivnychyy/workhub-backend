from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.models.proposal import ProposalStatus


class ProposalBase(BaseModel):
    cover_letter: str = Field(..., min_length=50)
    estimated_duration: str


class ProposalCreateFixed(ProposalBase):
    proposed_amount: float = Field(..., gt=0)
    proposed_milestones: Optional[str] = None


class ProposalCreateHourly(ProposalBase):
    proposed_hourly_rate: float = Field(..., gt=0)


class ProposalUpdate(BaseModel):
    cover_letter: Optional[str] = None
    proposed_amount: Optional[float] = None
    proposed_hourly_rate: Optional[float] = None
    estimated_duration: Optional[str] = None


class ProposalInDBBase(ProposalBase):
    id: int
    project_id: int
    freelancer_id: int
    proposed_amount: Optional[float]
    proposed_hourly_rate: Optional[float]
    status: ProposalStatus
    connects_spent: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Proposal(ProposalInDBBase):
    freelancer: Dict  # Basic freelancer info
    attachments: List[str] = []


class ProposalListItem(BaseModel):
    id: int
    project_title: str
    proposed_amount: Optional[float]
    proposed_hourly_rate: Optional[float]
    estimated_duration: str
    status: ProposalStatus
    connects_spent: int
    created_at: datetime
    
    # Freelancer info (for client view)
    freelancer_id: Optional[int]
    freelancer_name: Optional[str]
    freelancer_title: Optional[str]
    freelancer_rating: Optional[float]
    freelancer_jobs_completed: Optional[int]
    
    class Config:
        from_attributes = True