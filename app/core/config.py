"""
Configuration management for Agentic F&O Execution System
Environment-based configuration with security
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Agentic F&O Execution System"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "chrome-extension://*"
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/agentic_fo"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Broker APIs
    KITE_API_KEY: Optional[str] = None
    KITE_API_SECRET: Optional[str] = None
    KITE_ACCESS_TOKEN: Optional[str] = None
    
    UPSTOX_API_KEY: Optional[str] = None
    UPSTOX_API_SECRET: Optional[str] = None
    UPSTOX_ACCESS_TOKEN: Optional[str] = None
    
    # Model API
    MODEL_API_URL: str = "https://your-model-api.com/v1"
    MODEL_API_KEY: Optional[str] = None
    
    # Risk Management
    MAX_DAILY_LOSS: float = 100000.0
    MAX_POSITION_SIZE: float = 1000000.0
    MAX_MARGIN_USAGE: float = 0.8  # 80%
    
    # Algo ID (SEBI/NSE Compliance)
    ALGO_ID: str = "AGENTIC_FO_001"
    STRATEGY_NAME: str = "AgenticF&OStrategy"
    
    # Notifications
    SLACK_WEBHOOK_URL: Optional[str] = None
    EMAIL_SMTP_HOST: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Environment-specific overrides
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.ALLOWED_ORIGINS = [
        "https://yourdomain.com",
        "chrome-extension://your-extension-id"
    ]
    settings.ALLOWED_HOSTS = ["yourdomain.com", "api.yourdomain.com"]
elif settings.ENVIRONMENT == "staging":
    settings.DEBUG = True
    settings.ALLOWED_ORIGINS = [
        "https://staging.yourdomain.com",
        "chrome-extension://your-extension-id"
    ]
