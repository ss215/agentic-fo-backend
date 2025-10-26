"""
Main FastAPI Application for Agentic F&O Execution System
Production-ready backend with enterprise features
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime

from database.connection import get_db, create_tables, test_connection
from app.routes import auth, trading, monitoring, admin, breakdown_monitor
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Agentic F&O Execution System...")
    
    # Test database connection
    if not test_connection():
        logger.warning("Database connection failed - continuing without database")
        logger.info("Application will start in limited mode")
    else:
        # Create tables only if database is available
        create_tables()
        logger.info("Database tables created/verified")
    
    # Initialize Redis connection
    # await init_redis()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agentic F&O Execution System...")

# Create FastAPI application
app = FastAPI(
    title="Agentic F&O Execution System API",
    description="Production-ready Indian derivatives trading system with SEBI/NSE compliance",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(breakdown_monitor.router, tags=["Breakdown Monitor"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic F&O Execution System API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    from database.connection import get_db_health
    
    db_health = get_db_health()
    
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_health,
        "version": "1.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # This would typically return Prometheus-formatted metrics
    return {
        "status": "metrics_endpoint",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
