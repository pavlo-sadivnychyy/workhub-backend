from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from app.database import get_db
from app.models.review import Review
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    Review as ReviewSchema,
    ReviewListItem
)
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=ReviewSchema)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create review for completed project"""
    
    # Get project
    result = await db.execute(select(Project).where(Project.id == review_data.project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != ProjectStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Project must be completed to leave review")
    
    # Determine reviewer and reviewee
    if current_user.id == project.client_id:
        # Client reviewing freelancer
        reviewee_id = project.selected_freelancer_id
    elif current_user.id == project.selected_freelancer_id:
        # Freelancer reviewing client
        reviewee_id = project.client_id
    else:
        raise HTTPException(status_code=403, detail="You are not part of this project")
    
    if not reviewee_id:
        raise HTTPException(status_code=400, detail="No freelancer selected for this project")
    
    # Check if already reviewed
    existing = await db.execute(
        select(Review).where(
            Review.project_id == project.id,
            Review.reviewer_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already reviewed this project")
    
    # Create review
    review = Review(
        **review_data.dict(),
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id
    )
    
    db.add(review)
    
    # Update reviewee's rating
    reviewee_result = await db.execute(select(User).where(User.id == reviewee_id))
    reviewee = reviewee_result.scalar_one()
    
    # Calculate new rating
    total_rating = reviewee.rating * reviewee.reviews_count + review.rating
    reviewee.reviews_count += 1
    reviewee.rating = round(total_rating / reviewee.reviews_count, 2)
    
    await db.commit()
    await db.refresh(review)
    
    # Load relationships
    await db.refresh(review, ['project', 'reviewer', 'reviewee'])
    
    return review


@router.get("/user/{user_id}", response_model=List[ReviewListItem])
async def get_user_reviews(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get reviews for a user"""
    
    query = select(Review).where(Review.reviewee_id == user_id)
    query = query.order_by(Review.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    # Format response
    review_list = []
    for review in reviews:
        # Get reviewer and project info
        reviewer_result = await db.execute(select(User).where(User.id == review.reviewer_id))
        reviewer = reviewer_result.scalar_one()
        
        project_result = await db.execute(select(Project).where(Project.id == review.project_id))
        project = project_result.scalar_one()
        
        review_list.append({
            "id": review.id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at,
            "project_title": project.title,
            "reviewer_name": f"{reviewer.first_name} {reviewer.last_name}".strip() or reviewer.username,
            "reviewer_avatar": reviewer.avatar_url,
            "quality_rating": review.quality_rating,
            "communication_rating": review.communication_rating,
            "expertise_rating": review.expertise_rating,
            "professionalism_rating": review.professionalism_rating,
            "deadline_rating": review.deadline_rating,
            "would_hire_again": review.would_hire_again
        })
    
    return review_list


@router.get("/project/{project_id}", response_model=List[ReviewSchema])
async def get_project_reviews(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get reviews for a project"""
    
    query = select(Review).where(Review.project_id == project_id)
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return reviews


@router.get("/{review_id}", response_model=ReviewSchema)
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get review details"""
    
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return review


@router.patch("/{review_id}", response_model=ReviewSchema)
async def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update review (within 48 hours of creation)"""
    
    from datetime import datetime, timedelta
    
    result = await db.execute(
        select(Review).where(
            Review.id == review_id,
            Review.reviewer_id == current_user.id
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if within 48 hours
    if datetime.utcnow() - review.created_at > timedelta(hours=48):
        raise HTTPException(status_code=400, detail="Cannot update review after 48 hours")
    
    # Update review
    update_data = review_update.dict(exclude_unset=True)
    old_rating = review.rating
    
    for field, value in update_data.items():
        setattr(review, field, value)
    
    # Update reviewee's rating if rating changed
    if 'rating' in update_data and update_data['rating'] != old_rating:
        reviewee_result = await db.execute(select(User).where(User.id == review.reviewee_id))
        reviewee = reviewee_result.scalar_one()
        
        # Recalculate rating
        total_rating = reviewee.rating * reviewee.reviews_count - old_rating + review.rating
        reviewee.rating = round(total_rating / reviewee.reviews_count, 2)
    
    await db.commit()
    await db.refresh(review)
    
    return review


@router.get("/stats/{user_id}")
async def get_review_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get review statistics for a user"""
    
    # Get all reviews
    result = await db.execute(
        select(Review).where(Review.reviewee_id == user_id)
    )
    reviews = result.scalars().all()
    
    if not reviews:
        return {
            "total_reviews": 0,
            "average_rating": 0,
            "rating_breakdown": {
                "5": 0,
                "4": 0,
                "3": 0,
                "2": 0,
                "1": 0
            },
            "category_ratings": {}
        }
    
    # Calculate statistics
    rating_breakdown = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
    category_ratings = {
        "quality": [],
        "communication": [],
        "expertise": [],
        "professionalism": [],
        "deadline": []
    }
    
    for review in reviews:
        # Rating breakdown
        rating_key = str(int(review.rating))
        rating_breakdown[rating_key] += 1
        
        # Category ratings
        if review.quality_rating:
            category_ratings["quality"].append(review.quality_rating)
        if review.communication_rating:
            category_ratings["communication"].append(review.communication_rating)
        if review.expertise_rating:
            category_ratings["expertise"].append(review.expertise_rating)
        if review.professionalism_rating:
            category_ratings["professionalism"].append(review.professionalism_rating)
        if review.deadline_rating:
            category_ratings["deadline"].append(review.deadline_rating)
    
    # Calculate averages
    category_averages = {}
    for category, ratings in category_ratings.items():
        if ratings:
            category_averages[category] = round(sum(ratings) / len(ratings), 2)
        else:
            category_averages[category] = 0
    
    return {
        "total_reviews": len(reviews),
        "average_rating": round(sum(r.rating for r in reviews) / len(reviews), 2),
        "rating_breakdown": rating_breakdown,
        "category_ratings": category_averages
    }