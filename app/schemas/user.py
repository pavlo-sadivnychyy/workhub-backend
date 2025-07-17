from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.models.user import UserRole, VerificationStatus, SubscriptionType


class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.FREELANCER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    hourly_rate: Optional[float] = None
    skills: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class FreelancerProfileUpdate(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    description: str = Field(..., min_length=50)
    hourly_rate: float = Field(..., gt=0)
    skills: List[str] = Field(..., min_items=1, max_items=20)
    categories: List[str] = Field(..., min_items=1, max_items=5)
    portfolio_items: Optional[List[Dict]] = None


class UserInDBBase(UserBase):
    id: int
    verification_status: VerificationStatus
    is_active: bool
    is_online: bool
    created_at: datetime
    updated_at: datetime
    
    # Stats
    total_earned: float
    total_spent: float
    jobs_completed: int
    rating: float
    reviews_count: int
    
    # Connects and subscription
    connects_balance: int
    subscription_type: SubscriptionType
    subscription_expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class UserPublicProfile(BaseModel):
    id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    title: Optional[str]
    description: Optional[str]
    hourly_rate: Optional[float]
    skills: List[str]
    categories: List[str]
    
    # Stats
    total_earned: float
    jobs_completed: int
    rating: float
    reviews_count: int
    
    # Status
    is_online: bool
    last_seen_at: datetime
    verification_status: VerificationStatus
    
    # For promoted profiles
    profile_promoted_until: Optional[datetime]
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User


class ConnectsPurchase(BaseModel):
    amount: int = Field(..., description="Number of connects to purchase (20, 40, 60, etc.)")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v % 20 != 0 or v <= 0:
            raise ValueError('Amount must be a positive multiple of 20')
        return v


class SubscriptionPurchase(BaseModel):
    subscription_type: SubscriptionType
    months: int = Field(1, ge=1, le=12)