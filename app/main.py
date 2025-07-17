from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.config import settings
from app.database import engine
from app.models import *  # Import all models
from app.api import auth, users, projects, proposals, payments, reviews

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up WorkHub.ua API...")
    # You can add startup tasks here
    yield
    # Shutdown
    print("Shutting down WorkHub.ua API...")
    # Close database connections
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL] if settings.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to WorkHub.ua API",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["Projects"])
app.include_router(proposals.router, prefix=f"{settings.API_V1_STR}/proposals", tags=["Proposals"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["Payments"])
app.include_router(reviews.router, prefix=f"{settings.API_V1_STR}/reviews", tags=["Reviews"])