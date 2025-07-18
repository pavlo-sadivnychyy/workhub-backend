#!/usr/bin/env python
"""
Initialize database - create all tables without Alembic
This is useful for deployment when you don't need migration history
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
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
    print("Starting database initialization...")
    
    # Convert DATABASE_URL to async version if needed
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    print(f"Connecting to database...")
    
    engine = create_async_engine(database_url, echo=True)
    
    async with engine.begin() as conn:
        print("Dropping existing tables and types...")
        
        # Drop all tables first
        await conn.run_sync(Base.metadata.drop_all)
        
        # Drop all enum types
        await conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS verificationstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS subscriptiontype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS projectstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS projecttype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS projectduration CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS experiencelevel CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS proposalstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS transactiontype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS transactionstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS paymentmethod CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS timeentrystatus CASCADE"))
        
        print("Creating tables...")
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")
    
    await engine.dispose()
    print("Database initialized successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(init_db())
        sys.exit(0)
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)