from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Union
from datetime import datetime
from app.database import get_db
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.user import User
from app.schemas.project import (
    ProjectCreateFixed,
    ProjectCreateHourly,
    ProjectUpdate,
    Project as ProjectSchema,
    ProjectList,
    ProjectFilters
)
from app.core.dependencies import get_current_user, get_current_client
import json

router = APIRouter()


@router.post("/", response_model=ProjectSchema)
async def create_project(
    project_data: Union[ProjectCreateFixed, ProjectCreateHourly],
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Create new project"""
    
    # Create project
    project_dict = project_data.dict()
    
    # Handle milestones for fixed price projects
    milestones = None
    if isinstance(project_data, ProjectCreateFixed) and project_data.milestones:
        milestones = [m.dict() for m in project_data.milestones]
        project_dict.pop('milestones', None)
    
    project = Project(
        **project_dict,
        client_id=current_user.id,
        status=ProjectStatus.DRAFT
    )
    
    if milestones:
        project.milestones = milestones
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # Load relationships
    await db.refresh(project, ['client'])
    
    return project


@router.get("/", response_model=List[ProjectList])
async def get_projects(
    filters: ProjectFilters = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get projects list with filters"""
    
    query = select(Project).where(Project.status == filters.status)
    
    # Apply filters
    if filters.category:
        query = query.where(Project.category == filters.category)
    
    if filters.subcategory:
        query = query.where(Project.subcategory == filters.subcategory)
    
    if filters.project_type:
        query = query.where(Project.project_type == filters.project_type)
    
    if filters.experience_level:
        query = query.where(Project.experience_level == filters.experience_level)
    
    if filters.budget_min:
        query = query.where(
            or_(
                and_(Project.project_type == ProjectType.FIXED_PRICE, Project.budget_max >= filters.budget_min),
                and_(Project.project_type == ProjectType.HOURLY, Project.hourly_rate_max >= filters.budget_min)
            )
        )
    
    if filters.budget_max:
        query = query.where(
            or_(
                and_(Project.project_type == ProjectType.FIXED_PRICE, Project.budget_min <= filters.budget_max),
                and_(Project.project_type == ProjectType.HOURLY, Project.hourly_rate_min <= filters.budget_max)
            )
        )
    
    if filters.skills:
        for skill in filters.skills:
            query = query.where(Project.skills_required.contains([skill]))
    
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.where(
            or_(
                Project.title.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )
    
    # Join with users to get client info
    query = query.join(User, Project.client_id == User.id)
    
    # Sort
    if filters.sort_by == "budget":
        if filters.sort_order == "desc":
            query = query.order_by(Project.budget_max.desc().nullslast(), Project.hourly_rate_max.desc().nullslast())
        else:
            query = query.order_by(Project.budget_min.asc().nullsfirst(), Project.hourly_rate_min.asc().nullsfirst())
    elif filters.sort_by == "proposals_count":
        if filters.sort_order == "desc":
            query = query.order_by(Project.proposals_count.desc())
        else:
            query = query.order_by(Project.proposals_count.asc())
    else:  # created_at
        if filters.sort_order == "desc":
            query = query.order_by(Project.created_at.desc())
        else:
            query = query.order_by(Project.created_at.asc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # Format response
    project_list = []
    for project in projects:
        # Get client info
        client_result = await db.execute(select(User).where(User.id == project.client_id))
        client = client_result.scalar_one()
        
        project_list.append({
            "id": project.id,
            "title": project.title,
            "description": project.description[:200] + "..." if len(project.description) > 200 else project.description,
            "category": project.category,
            "project_type": project.project_type,
            "status": project.status,
            "budget_min": project.budget_min,
            "budget_max": project.budget_max,
            "hourly_rate_min": project.hourly_rate_min,
            "hourly_rate_max": project.hourly_rate_max,
            "skills_required": project.skills_required,
            "connects_to_apply": project.connects_to_apply,
            "proposals_count": project.proposals_count,
            "created_at": project.created_at,
            "is_urgent": project.is_urgent,
            "client_name": f"{client.first_name} {client.last_name}".strip() or client.username,
            "client_rating": client.rating,
            "client_jobs_posted": client.jobs_completed
        })
    
    return project_list


@router.get("/my-projects", response_model=List[ProjectSchema])
async def get_my_projects(
    status: Optional[ProjectStatus] = None,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's projects"""
    
    query = select(Project).where(Project.client_id == current_user.id)
    
    if status:
        query = query.where(Project.status == status)
    
    query = query.order_by(Project.created_at.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return projects


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get project details"""
    
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.client))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Increment views count
    project.views_count += 1
    await db.commit()
    
    return project


@router.patch("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Update project"""
    
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.client_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status not in [ProjectStatus.DRAFT, ProjectStatus.OPEN]:
        raise HTTPException(status_code=400, detail="Cannot update project in current status")
    
    # Update project
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.post("/{project_id}/publish", response_model=ProjectSchema)
async def publish_project(
    project_id: int,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Publish draft project"""
    
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.client_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != ProjectStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Project is not in draft status")
    
    project.status = ProjectStatus.OPEN
    project.published_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.post("/{project_id}/close", response_model=ProjectSchema)
async def close_project(
    project_id: int,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Close project"""
    
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.client_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="Project is not open")
    
    project.status = ProjectStatus.CANCELLED
    
    await db.commit()
    await db.refresh(project)
    
    return project