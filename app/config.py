from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "WorkHub.ua"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Monobank API
    MONOBANK_TOKEN: str
    MONOBANK_WEBHOOK_URL: Optional[str] = None
    MONOBANK_MERCHANT_ID: Optional[str] = None
    
    # Diia API
    DIIA_CLIENT_ID: Optional[str] = None
    DIIA_CLIENT_SECRET: Optional[str] = None
    DIIA_REDIRECT_URI: Optional[str] = None
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET_NAME: Optional[str] = None
    AWS_S3_REGION: str = "eu-central-1"
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@workhub.ua"
    
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
    SENTRY_DSN: Optional[str] = None
    
    # Frontend URL
    FRONTEND_URL: str = "https://workhub.ua"
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()