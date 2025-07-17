from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.project import Project, ProjectStatus
from app.models.user import User, SubscriptionType
from app.schemas.transaction import (
    EscrowFund,
    MilestoneFund,
    WithdrawalRequest,
    Transaction as TransactionSchema,
    TransactionList,
    PaymentInvoice
)
from app.core.dependencies import get_current_user, get_current_client
from app.services.monobank import monobank_service
import json

router = APIRouter()


@router.post("/escrow/fund", response_model=PaymentInvoice)
async def fund_escrow(
    escrow_data: EscrowFund,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Fund project escrow"""
    
    # Get project
    result = await db.execute(
        select(Project).where(
            Project.id == escrow_data.project_id,
            Project.client_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != ProjectStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Project must be in progress")
    
    if project.escrow_funded:
        raise HTTPException(status_code=400, detail="Escrow already funded")
    
    # Create invoice
    invoice = await monobank_service.create_invoice(
        amount=int(escrow_data.amount * 100),  # Convert to kopiykas
        order_id=f"escrow_{project.id}_{current_user.id}",
        destination=f"Фінансування проекту: {project.title}"
    )
    
    # Create transaction
    transaction = Transaction(
        payer_id=current_user.id,
        project_id=project.id,
        transaction_type=TransactionType.ESCROW_FUND,
        amount=escrow_data.amount,
        monobank_invoice_id=invoice["invoice_id"],
        description=escrow_data.description or f"Escrow for project: {project.title}"
    )
    
    db.add(transaction)
    await db.commit()
    
    return PaymentInvoice(
        invoice_id=invoice["invoice_id"],
        payment_url=invoice["payment_url"],
        amount=escrow_data.amount,
        description=transaction.description,
        expires_at=invoice["expires_at"]
    )


@router.post("/milestone/fund", response_model=PaymentInvoice)
async def fund_milestone(
    milestone_data: MilestoneFund,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Fund specific milestone"""
    
    # Get project
    result = await db.execute(
        select(Project).where(
            Project.id == milestone_data.project_id,
            Project.client_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check milestone exists
    milestone = None
    for m in project.milestones:
        if m.get("id") == milestone_data.milestone_id:
            milestone = m
            break
    
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    if milestone.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Milestone already funded")
    
    # Create invoice
    invoice = await monobank_service.create_invoice(
        amount=int(milestone_data.amount * 100),
        order_id=f"milestone_{project.id}_{milestone_data.milestone_id}",
        destination=f"Оплата етапу: {milestone.get('title')}"
    )
    
    # Create transaction
    transaction = Transaction(
        payer_id=current_user.id,
        project_id=project.id,
        transaction_type=TransactionType.MILESTONE_FUND,
        amount=milestone_data.amount,
        monobank_invoice_id=invoice["invoice_id"],
        description=milestone_data.description or f"Milestone: {milestone.get('title')}",
        meta_data=json.dumps({"milestone_id": milestone_data.milestone_id})
    )
    
    db.add(transaction)
    await db.commit()
    
    return PaymentInvoice(
        invoice_id=invoice["invoice_id"],
        payment_url=invoice["payment_url"],
        amount=milestone_data.amount,
        description=transaction.description,
        expires_at=invoice["expires_at"]
    )


@router.post("/withdraw", response_model=dict)
async def request_withdrawal(
    withdrawal: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request withdrawal to card"""
    
    # Check balance
    # Calculate available balance (total earned - pending withdrawals - fees)
    pending_withdrawals = await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.payee_id == current_user.id,
            Transaction.transaction_type == TransactionType.WITHDRAWAL,
            Transaction.status.in_([TransactionStatus.PENDING, TransactionStatus.PROCESSING])
        )
    )
    pending_amount = pending_withdrawals.scalar() or 0
    
    available_balance = current_user.total_earned - pending_amount
    total_amount = withdrawal.amount + withdrawal.fee
    
    if available_balance < total_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create withdrawal
    result = await monobank_service.create_withdrawal(
        card_number=withdrawal.card_number,
        amount=int(withdrawal.amount * 100),
        order_id=f"withdrawal_{current_user.id}_{datetime.utcnow().timestamp()}"
    )
    
    # Create transaction
    transaction = Transaction(
        payee_id=current_user.id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount=withdrawal.amount,
        commission_amount=withdrawal.fee,
        net_amount=withdrawal.amount - withdrawal.fee,
        status=TransactionStatus.PROCESSING,
        description=f"Withdrawal to card {result['card']}",
        meta_data=json.dumps({
            "card": result["card"],
            "is_express": withdrawal.is_express
        })
    )
    
    db.add(transaction)
    await db.commit()
    
    return {
        "transaction_id": transaction.id,
        "amount": withdrawal.amount,
        "fee": withdrawal.fee,
        "net_amount": transaction.net_amount,
        "status": "processing",
        "card": result["card"]
    }


@router.get("/transactions", response_model=List[TransactionList])
async def get_transactions(
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's transactions"""
    
    query = select(Transaction).where(
        or_(
            Transaction.payer_id == current_user.id,
            Transaction.payee_id == current_user.id
        )
    )
    
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    
    if status:
        query = query.where(Transaction.status == status)
    
    query = query.order_by(Transaction.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Format response
    transaction_list = []
    for transaction in transactions:
        # Determine other party and project
        other_party_name = None
        project_title = None
        
        if transaction.payer_id == current_user.id and transaction.payee_id:
            # User is payer
            payee_result = await db.execute(select(User).where(User.id == transaction.payee_id))
            payee = payee_result.scalar_one_or_none()
            if payee:
                other_party_name = f"{payee.first_name} {payee.last_name}".strip() or payee.username
        elif transaction.payee_id == current_user.id and transaction.payer_id:
            # User is payee
            payer_result = await db.execute(select(User).where(User.id == transaction.payer_id))
            payer = payer_result.scalar_one_or_none()
            if payer:
                other_party_name = f"{payer.first_name} {payer.last_name}".strip() or payer.username
        
        if transaction.project_id:
            project_result = await db.execute(select(Project).where(Project.id == transaction.project_id))
            project = project_result.scalar_one_or_none()
            if project:
                project_title = project.title
        
        transaction_list.append({
            "id": transaction.id,
            "transaction_type": transaction.transaction_type,
            "amount": transaction.amount,
            "status": transaction.status,
            "description": transaction.description,
            "created_at": transaction.created_at,
            "other_party_name": other_party_name,
            "project_title": project_title
        })
    
    return transaction_list


@router.post("/webhook/monobank")
async def monobank_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Monobank payment webhooks"""
    
    # Get webhook data
    body = await request.body()
    data = await request.json()
    
    # Verify signature (implement in production)
    x_sign = request.headers.get("X-Sign")
    if not monobank_service.verify_webhook_signature(body, x_sign):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Process webhook
    webhook_data = await monobank_service.process_webhook(data)
    
    # Find transaction
    result = await db.execute(
        select(Transaction).where(Transaction.monobank_invoice_id == webhook_data["invoice_id"])
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        return {"status": "ignored"}
    
    # Update transaction status
    if webhook_data["status"] == "success":
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = datetime.utcnow()
        
        # Handle different transaction types
        if transaction.transaction_type == TransactionType.ESCROW_FUND:
            # Mark project escrow as funded
            project_result = await db.execute(select(Project).where(Project.id == transaction.project_id))
            project = project_result.scalar_one()
            project.escrow_funded = True
            project.escrow_amount = transaction.amount
            
        elif transaction.transaction_type == TransactionType.CONNECTS_PURCHASE:
            # Add connects to user
            metadata = json.loads(transaction.meta_data or "{}")
            connects_amount = metadata.get("connects_amount", 0)
            
            user_result = await db.execute(select(User).where(User.id == transaction.payer_id))
            user = user_result.scalar_one()
            user.connects_balance += connects_amount
            
        elif transaction.transaction_type == TransactionType.SUBSCRIPTION_PAYMENT:
            # Activate subscription
            metadata = json.loads(transaction.meta_data or "{}")
            subscription_type = metadata.get("subscription_type")
            months = metadata.get("months", 1)
            
            user_result = await db.execute(select(User).where(User.id == transaction.payer_id))
            user = user_result.scalar_one()
            user.subscription_type = SubscriptionType(subscription_type)
            
            # Set expiration date
            if user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow():
                user.subscription_expires_at += timedelta(days=30 * months)
            else:
                user.subscription_expires_at = datetime.utcnow() + timedelta(days=30 * months)
            
        elif transaction.transaction_type == TransactionType.PROFILE_PROMOTION:
            # Activate profile promotion
            metadata = json.loads(transaction.meta_data or "{}")
            weeks = metadata.get("weeks", 1)
            
            user_result = await db.execute(select(User).where(User.id == transaction.payer_id))
            user = user_result.scalar_one()
            
            if user.profile_promoted_until and user.profile_promoted_until > datetime.utcnow():
                user.profile_promoted_until += timedelta(weeks=weeks)
            else:
                user.profile_promoted_until = datetime.utcnow() + timedelta(weeks=weeks)
    
    elif webhook_data["status"] in ["failure", "expired"]:
        transaction.status = TransactionStatus.FAILED
    
    await db.commit()
    
    return {"status": "ok"}