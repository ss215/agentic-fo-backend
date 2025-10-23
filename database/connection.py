"""
Database Connection and Session Management
Production-ready database configuration
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from .schemas import Base

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/agentic_fo"
)

# Redis configuration for caching
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create database engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables created successfully")

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    Used with FastAPI dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    Use this for manual database operations
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    try:
        with get_db_session() as db:
            db.execute("SELECT 1")
        logging.info("Database connection successful")
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False

# Database health check
def get_db_health():
    """Get database health status"""
    try:
        with get_db_session() as db:
            result = db.execute("SELECT version()").fetchone()
            return {
                "status": "healthy",
                "database": "postgresql",
                "version": result[0] if result else "unknown"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
