from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "WorkHub.ua"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Database - Railway provides DATABASE_URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/workhub"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Monobank API
    MONOBANK_TOKEN: str = os.getenv("MONOBANK_TOKEN", "")
    MONOBANK_WEBHOOK_URL: Optional[str] = os.getenv("MONOBANK_WEBHOOK_URL", None)
    MONOBANK_MERCHANT_ID: Optional[str] = os.getenv("MONOBANK_MERCHANT_ID", None)
    
    # Diia API
    DIIA_CLIENT_ID: Optional[str] = os.getenv("DIIA_CLIENT_ID", None)
    DIIA_CLIENT_SECRET: Optional[str] = os.getenv("DIIA_CLIENT_SECRET", None)
    DIIA_REDIRECT_URI: Optional[str] = os.getenv("DIIA_REDIRECT_URI", None)
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_S3_BUCKET_NAME: Optional[str] = os.getenv("AWS_S3_BUCKET_NAME", None)
    AWS_S3_REGION: str = os.getenv("AWS_S3_REGION", "eu-central-1")
    
    # Email
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", None)
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@workhub.ua")
    
    # Commissions
    COMMISSION_TIER_1_LIMIT: int = 20000  # 20k UAH
    COMMISSION_TIER_1_RATE: float = 0.20  # 20%
    COMMISSION_TIER_2_LIMIT: int = 400000  # 400k UAH
    COMMISSION_TIER_2_RATE: float = 0.10  # 10%
    COMMISSION_TIER_3_RATE: float = 0.05  # 5%
    
    # Connects
    FREE_CONNECTS_PER_MONTH: int = 10
    CONNECTS_PRICE_20: int = 100  # 100 UAH for 20 connects
    
    # Subscriptions
    FREELANCER_PLUS_PRICE: int = 199  # 199 UAH/month
    
    # Withdrawals
    WITHDRAWAL_FEE_REGULAR: int = 20  # 20 UAH
    WITHDRAWAL_FEE_EXPRESS: int = 50  # 50 UAH
    
    # Profile promotion
    PROFILE_PROMOTION_WEEKLY_PRICE: int = 299  # 299 UAH/week
    
    # Sentry
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    
    # Frontend URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    @validator("DATABASE_URL", pre=True)
    def fix_database_url(cls, v):
        # Handle Railway's postgres:// URLs
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        # Handle standard postgresql:// URLs
        elif v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    class Config:
        env_file = ".env" if os.path.exists(".env") else None
        case_sensitive = True


settings = Settings()