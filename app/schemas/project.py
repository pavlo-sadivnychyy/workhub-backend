from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from app.models.project import ProjectStatus, ProjectType, ProjectDuration, ExperienceLevel


class MilestoneBase(BaseModel):
    title: str
    description: str
    amount: float
    due_date: Optional[datetime] = None


class MilestoneCreate(MilestoneBase):
    pass


class Milestone(MilestoneBase):
    id: int
    status: str = "pending"  # pending, funded, released, cancelled
    funded_at: Optional[datetime] = None
    released_at: Optional[datetime] = None


class ProjectBase(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    description: str = Field(..., min_length=100)
    category: str
    subcategory: Optional[str] = None
    project_type: ProjectType
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    skills_required: List[str] = Field(..., min_items=1, max_items=10)
    duration: Optional[ProjectDuration] = None
    deadline: Optional[datetime] = None
    is_urgent: bool = False


class ProjectCreateFixed(ProjectBase):
    project_type: ProjectType = ProjectType.FIXED_PRICE
    budget_min: float = Field(..., gt=0)
    budget_max: float = Field(..., gt=0)
    milestones: Optional[List[MilestoneCreate]] = None
    
    @validator('budget_max')
    def validate_budget_max(cls, v, values):
        if 'budget_min' in values and v < values['budget_min']:
            raise ValueError('budget_max must be greater than or equal to budget_min')
        return v


class ProjectCreateHourly(ProjectBase):
    project_type: ProjectType = ProjectType.HOURLY
    hourly_rate_min: float = Field(..., gt=0)
    hourly_rate_max: float = Field(..., gt=0)
    
    @validator('hourly_rate_max')
    def validate_hourly_rate_max(cls, v, values):
        if 'hourly_rate_min' in values and v < values['hourly_rate_min']:
            raise ValueError('hourly_rate_max must be greater than or equal to hourly_rate_min')
        return v


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=10, max_length=200)
    description: Optional[str] = Field(None, min_length=100)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    skills_required: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    is_urgent: Optional[bool] = None


class ProjectInDBBase(ProjectBase):
    id: int
    client_id: int
    status: ProjectStatus
    connects_to_apply: int
    views_count: int
    proposals_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    
    # For fixed price
    budget_min: Optional[float]
    budget_max: Optional[float]
    
    # For hourly
    hourly_rate_min: Optional[float]
    hourly_rate_max: Optional[float]
    
    class Config:
        from_attributes = True


class Project(ProjectInDBBase):
    client: Dict  # Basic client info
    selected_freelancer: Optional[Dict] = None
    escrow_funded: bool = False
    escrow_amount: float = 0
    milestones: List[Milestone] = []


class ProjectList(BaseModel):
    id: int
    title: str
    description: str  # Truncated
    category: str
    project_type: ProjectType
    status: ProjectStatus
    
    # Budget info
    budget_min: Optional[float]
    budget_max: Optional[float]
    hourly_rate_min: Optional[float]
    hourly_rate_max: Optional[float]
    
    # Basic info
    skills_required: List[str]
    connects_to_apply: int
    proposals_count: int
    created_at: datetime
    is_urgent: bool
    
    # Client info
    client_name: str
    client_rating: float
    client_jobs_posted: int
    
    class Config:
        from_attributes = True


class ProjectFilters(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    project_type: Optional[ProjectType] = None
    experience_level: Optional[ExperienceLevel] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    skills: Optional[List[str]] = None
    search: Optional[str] = None
    status: ProjectStatus = ProjectStatus.OPEN
    sort_by: str = "created_at"  # created_at, budget, proposals_count
    sort_order: str = "desc"