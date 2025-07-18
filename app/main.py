from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
import logging
import sys
import os

from app.config import settings
from app.database import engine, test_connection
from app.models import *  # Import all models
from app.api import auth, users, projects, proposals, payments, reviews

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 0.0,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting up {settings.APP_NAME} API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Port: {settings.PORT}")
    
    # Test database connection
    db_connected = await test_connection()
    if db_connected:
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
        if settings.ENVIRONMENT == "production":
            raise Exception("Cannot start without database connection")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME} API...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Configure CORS
origins = []

# Add configured origins
if settings.CORS_ORIGINS:
    if settings.CORS_ORIGINS == "*":
        origins = ["*"]
    else:
        origins_list = settings.CORS_ORIGINS.split(",")
        origins.extend([origin.strip() for origin in origins_list])

# Add frontend URL
if settings.FRONTEND_URL and settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

# In development, add localhost origins
if settings.ENVIRONMENT == "development" and "*" not in origins:
    origins.extend([
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add Sentry middleware
if settings.SENTRY_DSN:
    app.add_middleware(SentryAsgiMiddleware)


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else "Disabled in production"
    }


# Health check
@app.get("/health")
async def health_check():
    # Check database connection
    db_status = await test_connection()
    
    if not db_status:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    return {
        "status": "healthy",
        "database": "connected" if db_status else "disconnected",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION
    }


# Debug endpoint - ONLY IN DEVELOPMENT
if settings.ENVIRONMENT != "production":
    @app.get("/debug/config")
    async def debug_config():
        """Debug configuration - NEVER enable in production"""
        return {
            "environment": settings.ENVIRONMENT,
            "database_url_set": bool(os.getenv("DATABASE_URL")),
            "redis_url_set": bool(os.getenv("REDIS_URL")),
            "port": settings.PORT,
            "secret_key_set": settings.SECRET_KEY != "development-secret-key-change-in-production",
            "monobank_token_set": bool(settings.MONOBANK_TOKEN),
            "frontend_url": settings.FRONTEND_URL,
            "cors_origins": origins,
        }


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["Projects"])
app.include_router(proposals.router, prefix=f"{settings.API_V1_STR}/proposals", tags=["Proposals"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["Payments"])
app.include_router(reviews.router, prefix=f"{settings.API_V1_STR}/reviews", tags=["Reviews"])


# Catch-all for API routes
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(path: str):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Endpoint '/{path}' not found"}
    )