from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from app.database import get_db
from app.models.user import User, UserRole, SubscriptionType
from app.schemas.user import (
    User as UserSchema,
    UserUpdate,
    UserPublicProfile,
    FreelancerProfileUpdate,
    ConnectsPurchase,
    SubscriptionPurchase
)
from app.core.dependencies import get_current_user, get_current_active_user
import json

router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return current_user


@router.patch("/me", response_model=UserSchema)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.put("/freelancer-profile", response_model=UserSchema)
async def update_freelancer_profile(
    profile_data: FreelancerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update freelancer profile"""
    
    if current_user.role not in [UserRole.FREELANCER, UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Not a freelancer")
    
    # Update profile
    current_user.title = profile_data.title
    current_user.description = profile_data.description
    current_user.hourly_rate = profile_data.hourly_rate
    current_user.skills = profile_data.skills
    current_user.categories = profile_data.categories
    
    if profile_data.portfolio_items:
        current_user.portfolio_items = profile_data.portfolio_items
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/freelancers", response_model=List[UserPublicProfile])
async def get_freelancers(
    category: Optional[str] = None,
    skill: Optional[str] = None,
    min_rate: Optional[float] = None,
    max_rate: Optional[float] = None,
    min_rating: float = 0,
    search: Optional[str] = None,
    promoted_first: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get freelancers list with filters"""
    
    query = select(User).where(
        User.role.in_([UserRole.FREELANCER, UserRole.BOTH]),
        User.is_active == True
    )
    
    # Apply filters
    if category:
        query = query.where(User.categories.contains([category]))
    
    if skill:
        query = query.where(User.skills.contains([skill]))
    
    if min_rate:
        query = query.where(User.hourly_rate >= min_rate)
    
    if max_rate:
        query = query.where(User.hourly_rate <= max_rate)
    
    if min_rating > 0:
        query = query.where(User.rating >= min_rating)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.title.ilike(search_term),
                User.description.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    # Sort by promoted profiles first if enabled
    if promoted_first:
        query = query.order_by(
            User.profile_promoted_until.desc().nullslast(),
            User.rating.desc(),
            User.jobs_completed.desc()
        )
    else:
        query = query.order_by(User.rating.desc(), User.jobs_completed.desc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    freelancers = result.scalars().all()
    
    return freelancers


@router.get("/{user_id}", response_model=UserPublicProfile)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user public profile"""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/connects/purchase")
async def purchase_connects(
    purchase: ConnectsPurchase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Purchase connects"""
    
    from app.services.monobank import monobank_service
    from app.models.transaction import Transaction, TransactionType
    
    # Calculate price
    price = (purchase.amount // 20) * 100  # 100 UAH per 20 connects
    
    # Create invoice
    invoice = await monobank_service.create_invoice(
        amount=price * 100,  # Convert to kopiykas
        order_id=f"connects_{current_user.id}_{purchase.amount}",
        destination=f"Купівля {purchase.amount} connects на WorkHub.ua"
    )
    
    # Create pending transaction
    transaction = Transaction(
        payer_id=current_user.id,
        transaction_type=TransactionType.CONNECTS_PURCHASE,
        amount=price,
        monobank_invoice_id=invoice["invoice_id"],
        description=f"Purchase of {purchase.amount} connects",
        metadata=json.dumps({"connects_amount": purchase.amount})
    )
    
    db.add(transaction)
    await db.commit()
    
    return {
        "invoice_id": invoice["invoice_id"],
        "payment_url": invoice["payment_url"],
        "amount": price,
        "connects": purchase.amount
    }


@router.post("/subscription/purchase")
async def purchase_subscription(
    purchase: SubscriptionPurchase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Purchase or upgrade subscription"""
    
    from app.services.monobank import monobank_service
    from app.models.transaction import Transaction, TransactionType
    from datetime import datetime, timedelta
    
    if purchase.subscription_type == SubscriptionType.FREE:
        raise HTTPException(status_code=400, detail="Cannot purchase free subscription")
    
    # Calculate price
    price = 199 * purchase.months  # 199 UAH per month
    
    # Create invoice
    invoice = await monobank_service.create_invoice(
        amount=price * 100,  # Convert to kopiykas
        order_id=f"subscription_{current_user.id}_{purchase.subscription_type}_{purchase.months}",
        destination=f"Підписка Freelancer Plus на {purchase.months} міс. - WorkHub.ua"
    )
    
    # Create pending transaction
    transaction = Transaction(
        payer_id=current_user.id,
        transaction_type=TransactionType.SUBSCRIPTION_PAYMENT,
        amount=price,
        monobank_invoice_id=invoice["invoice_id"],
        description=f"{purchase.subscription_type} subscription for {purchase.months} months",
        metadata=json.dumps({
            "subscription_type": purchase.subscription_type,
            "months": purchase.months
        })
    )
    
    db.add(transaction)
    await db.commit()
    
    return {
        "invoice_id": invoice["invoice_id"],
        "payment_url": invoice["payment_url"],
        "amount": price,
        "subscription_type": purchase.subscription_type,
        "months": purchase.months
    }


@router.post("/profile/promote")
async def promote_profile(
    weeks: int = Query(1, ge=1, le=4),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Promote freelancer profile"""
    
    from app.services.monobank import monobank_service
    from app.models.transaction import Transaction, TransactionType
    
    if current_user.role not in [UserRole.FREELANCER, UserRole.BOTH]:
        raise HTTPException(status_code=403, detail="Only freelancers can promote profiles")
    
    # Calculate price
    price = 299 * weeks  # 299 UAH per week
    
    # Create invoice
    invoice = await monobank_service.create_invoice(
        amount=price * 100,  # Convert to kopiykas
        order_id=f"promotion_{current_user.id}_{weeks}w",
        destination=f"Просування профілю на {weeks} тижн. - WorkHub.ua"
    )
    
    # Create pending transaction
    transaction = Transaction(
        payer_id=current_user.id,
        transaction_type=TransactionType.PROFILE_PROMOTION,
        amount=price,
        monobank_invoice_id=invoice["invoice_id"],
        description=f"Profile promotion for {weeks} weeks",
        metadata=json.dumps({"weeks": weeks})
    )
    
    db.add(transaction)
    await db.commit()
    
    return {
        "invoice_id": invoice["invoice_id"],
        "payment_url": invoice["payment_url"],
        "amount": price,
        "weeks": weeks
    }