#!/usr/bin/env python
"""
Initialize database - create all tables without Alembic
This is useful for deployment when you don't need migration history
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.database import Base

# Import all models to register them
from app.models.user import User
from app.models.project import Project
from app.models.proposal import Proposal
from app.models.transaction import Transaction
from app.models.review import Review
from app.models.message import Message
from app.models.time_entry import TimeEntry


async def init_db():
    """Create all tables"""
    # Convert DATABASE_URL to async version if needed
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=True)
    
    async with engine.begin() as conn:
        # Drop all tables (optional, remove in production)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())