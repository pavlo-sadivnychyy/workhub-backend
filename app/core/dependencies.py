from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from typing import Optional

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user"""
    from app.models.user import VerificationStatus
    
    if current_user.verification_status == VerificationStatus.UNVERIFIED:
        raise HTTPException(
            status_code=403,
            detail="Please verify your account to access this feature"
        )
    return current_user


async def get_current_freelancer(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with freelancer role"""
    from app.models.user import UserRole
    
    if current_user.role not in [UserRole.FREELANCER, UserRole.BOTH]:
        raise HTTPException(
            status_code=403,
            detail="This feature is only available for freelancers"
        )
    return current_user


async def get_current_client(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with client role"""
    from app.models.user import UserRole
    
    if current_user.role not in [UserRole.CLIENT, UserRole.BOTH]:
        raise HTTPException(
            status_code=403,
            detail="This feature is only available for clients"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user with admin role"""
    from app.models.user import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user