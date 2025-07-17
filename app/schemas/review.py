from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
from datetime import datetime


class ReviewBase(BaseModel):
    rating: float = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=10)
    
    # Specific ratings (optional)
    quality_rating: Optional[float] = Field(None, ge=1, le=5)
    communication_rating: Optional[float] = Field(None, ge=1, le=5)
    expertise_rating: Optional[float] = Field(None, ge=1, le=5)
    professionalism_rating: Optional[float] = Field(None, ge=1, le=5)
    deadline_rating: Optional[float] = Field(None, ge=1, le=5)
    
    # For clients rating freelancers
    would_hire_again: Optional[bool] = None


class ReviewCreate(ReviewBase):
    project_id: int


class ReviewUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=10)


class ReviewInDBBase(ReviewBase):
    id: int
    project_id: int
    reviewer_id: int
    reviewee_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Review(ReviewInDBBase):
    project: Dict  # Basic project info
    reviewer: Dict  # Basic reviewer info
    reviewee: Dict  # Basic reviewee info


class ReviewListItem(BaseModel):
    id: int
    rating: float
    comment: Optional[str]
    created_at: datetime
    
    # Related info
    project_title: str
    reviewer_name: str
    reviewer_avatar: Optional[str]
    
    # Specific ratings if available
    quality_rating: Optional[float]
    communication_rating: Optional[float]
    expertise_rating: Optional[float]
    professionalism_rating: Optional[float]
    deadline_rating: Optional[float]
    would_hire_again: Optional[bool]
    
    class Config:
        from_attributes = True