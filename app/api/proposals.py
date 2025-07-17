from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Union
from app.database import get_db
from app.models.proposal import Proposal, ProposalStatus
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.user import User
from app.schemas.proposal import (
    ProposalCreateFixed,
    ProposalCreateHourly,
    ProposalUpdate,
    Proposal as ProposalSchema,
    ProposalListItem
)
from app.core.dependencies import get_current_user, get_current_freelancer, get_current_client

router = APIRouter()


@router.post("/", response_model=ProposalSchema)
async def create_proposal(
    proposal_data: Union[ProposalCreateFixed, ProposalCreateHourly],
    project_id: int,
    current_user: User = Depends(get_current_freelancer),
    db: AsyncSession = Depends(get_db)
):
    """Submit proposal to project"""
    
    # Get project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="Project is not open for proposals")
    
    # Check if already applied
    existing = await db.execute(
        select(Proposal).where(
            Proposal.project_id == project_id,
            Proposal.freelancer_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already submitted a proposal")
    
    # Check connects balance
    if current_user.connects_balance < project.connects_to_apply:
        raise HTTPException(status_code=400, detail="Insufficient connects balance")
    
    # Check project type matches proposal type
    if project.project_type == ProjectType.FIXED_PRICE and not isinstance(proposal_data, ProposalCreateFixed):
        raise HTTPException(status_code=400, detail="Fixed price proposal required")
    elif project.project_type == ProjectType.HOURLY and not isinstance(proposal_data, ProposalCreateHourly):
        raise HTTPException(status_code=400, detail="Hourly rate proposal required")
    
    # Create proposal
    proposal_dict = proposal_data.dict()
    proposal = Proposal(
        **proposal_dict,
        project_id=project_id,
        freelancer_id=current_user.id,
        connects_spent=project.connects_to_apply
    )
    
    # Deduct connects
    current_user.connects_balance -= project.connects_to_apply
    
    # Update project proposals count
    project.proposals_count += 1
    
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    
    # Load relationships
    await db.refresh(proposal, ['freelancer'])
    
    return proposal


@router.get("/my-proposals", response_model=List[ProposalListItem])
async def get_my_proposals(
    status: Optional[ProposalStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_freelancer),
    db: AsyncSession = Depends(get_db)
):
    """Get freelancer's proposals"""
    
    query = select(Proposal).where(Proposal.freelancer_id == current_user.id)
    
    if status:
        query = query.where(Proposal.status == status)
    
    query = query.order_by(Proposal.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query.options(selectinload(Proposal.project)))
    proposals = result.scalars().all()
    
    # Format response
    proposal_list = []
    for proposal in proposals:
        proposal_list.append({
            "id": proposal.id,
            "project_title": proposal.project.title,
            "proposed_amount": proposal.proposed_amount,
            "proposed_hourly_rate": proposal.proposed_hourly_rate,
            "estimated_duration": proposal.estimated_duration,
            "status": proposal.status,
            "connects_spent": proposal.connects_spent,
            "created_at": proposal.created_at
        })
    
    return proposal_list


@router.get("/project/{project_id}", response_model=List[ProposalListItem])
async def get_project_proposals(
    project_id: int,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Get proposals for a project (client only)"""
    
    # Check project ownership
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.client_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get proposals
    query = select(Proposal).where(Proposal.project_id == project_id)
    query = query.order_by(Proposal.created_at.desc())
    
    result = await db.execute(query.options(selectinload(Proposal.freelancer)))
    proposals = result.scalars().all()
    
    # Format response
    proposal_list = []
    for proposal in proposals:
        freelancer = proposal.freelancer
        proposal_list.append({
            "id": proposal.id,
            "project_title": project.title,
            "proposed_amount": proposal.proposed_amount,
            "proposed_hourly_rate": proposal.proposed_hourly_rate,
            "estimated_duration": proposal.estimated_duration,
            "status": proposal.status,
            "connects_spent": proposal.connects_spent,
            "created_at": proposal.created_at,
            "freelancer_id": freelancer.id,
            "freelancer_name": f"{freelancer.first_name} {freelancer.last_name}".strip() or freelancer.username,
            "freelancer_title": freelancer.title,
            "freelancer_rating": freelancer.rating,
            "freelancer_jobs_completed": freelancer.jobs_completed
        })
    
    return proposal_list


@router.get("/{proposal_id}", response_model=ProposalSchema)
async def get_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get proposal details"""
    
    query = select(Proposal).where(Proposal.id == proposal_id)
    result = await db.execute(query.options(selectinload(Proposal.freelancer), selectinload(Proposal.project)))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Check access rights
    project = proposal.project
    if current_user.id != proposal.freelancer_id and current_user.id != project.client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return proposal


@router.patch("/{proposal_id}", response_model=ProposalSchema)
async def update_proposal(
    proposal_id: int,
    proposal_update: ProposalUpdate,
    current_user: User = Depends(get_current_freelancer),
    db: AsyncSession = Depends(get_db)
):
    """Update proposal (freelancer only)"""
    
    result = await db.execute(
        select(Proposal).where(
            Proposal.id == proposal_id,
            Proposal.freelancer_id == current_user.id
        )
    )
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if proposal.status != ProposalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot update proposal in current status")
    
    # Update proposal
    update_data = proposal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proposal, field, value)
    
    await db.commit()
    await db.refresh(proposal)
    
    return proposal


@router.post("/{proposal_id}/withdraw")
async def withdraw_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_freelancer),
    db: AsyncSession = Depends(get_db)
):
    """Withdraw proposal"""
    
    result = await db.execute(
        select(Proposal).where(
            Proposal.id == proposal_id,
            Proposal.freelancer_id == current_user.id
        )
    )
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if proposal.status != ProposalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot withdraw proposal in current status")
    
    proposal.status = ProposalStatus.WITHDRAWN
    
    # Update project proposals count
    project_result = await db.execute(select(Project).where(Project.id == proposal.project_id))
    project = project_result.scalar_one()
    project.proposals_count -= 1
    
    await db.commit()
    
    return {"message": "Proposal withdrawn successfully"}


@router.post("/{proposal_id}/accept")
async def accept_proposal(
    proposal_id: int,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Accept proposal and hire freelancer"""
    
    # Get proposal with project
    result = await db.execute(
        select(Proposal).where(Proposal.id == proposal_id)
        .options(selectinload(Proposal.project))
    )
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    project = proposal.project
    
    # Check ownership
    if project.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="Project is not open")
    
    if proposal.status != ProposalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Proposal is not pending")
    
    # Accept proposal
    proposal.status = ProposalStatus.ACCEPTED
    project.selected_freelancer_id = proposal.freelancer_id
    project.status = ProjectStatus.IN_PROGRESS
    
    # Reject all other proposals
    await db.execute(
        select(Proposal)
        .where(
            Proposal.project_id == project.id,
            Proposal.id != proposal_id,
            Proposal.status == ProposalStatus.PENDING
        )
        .update({"status": ProposalStatus.REJECTED})
    )
    
    await db.commit()
    
    return {"message": "Proposal accepted successfully", "freelancer_id": proposal.freelancer_id}