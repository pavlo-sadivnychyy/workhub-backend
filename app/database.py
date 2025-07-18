from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData
from app.config import settings
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Database URL is already converted in settings
database_url = settings.DATABASE_URL

# Log the database connection (without password)
if settings.DEBUG:
    # Hide password in logs
    safe_url = database_url.split('@')[0].rsplit(':', 1)[0] + ':***@' + database_url.split('@')[1]
    logger.info(f"Connecting to database: {safe_url}")

# Create async engine with Railway-optimized settings
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "server_settings": {"jit": "off"},
        "command_timeout": 60,
        "ssl": "prefer" if settings.ENVIRONMENT == "production" else "disable"
    }
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create base class for models
metadata = MetaData()
Base = declarative_base(metadata=metadata)


# Dependency to get DB session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Test database connection
async def test_connection():
    """Test if database connection works"""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False