"""
Authentication API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import jwt
# from passlib.context import CryptContext  # Commented out for now

from database.connection import get_db
from app.core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Password hashing (commented out for now)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    """User login"""
    # Mock implementation
    return {"access_token": "mock_token", "token_type": "bearer"}

@router.post("/logout")
async def logout():
    """User logout"""
    return {"message": "Logged out successfully"}

@router.post("/refresh")
async def refresh_token():
    """Refresh access token"""
    return {"access_token": "new_mock_token", "token_type": "bearer"}
