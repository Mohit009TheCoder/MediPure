from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from sqlalchemy.orm import Session
import hashlib
import database

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash using SHA256"""
    password_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return password_hash == hashed_password

def get_password_hash(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict):
    """Create a simple token (just return the email)"""
    return data.get("sub", "")

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(database.get_db)):
    """Get current user from authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Extract email from "Bearer <email>" format
    try:
        scheme, email = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    user = db.query(database.User).filter(database.User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user
