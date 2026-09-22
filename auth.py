from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
import database
import config


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash. Supports legacy SHA-256 migration."""
    import hashlib
    # Support legacy SHA-256 hashes (64-char hex)
    if len(hashed_password) == 64 and all(c in '0123456789abcdef' for c in hashed_password):
        legacy = hashlib.sha256(plain_password.encode()).hexdigest()
        if legacy == hashed_password:
            return True
    # Bcrypt check
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a real JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=config.Config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.Config.SECRET_KEY, algorithm=config.Config.ALGORITHM)


def get_current_user(authorization: str = Header(None), db: Session = Depends(database.get_db)):
    """Get current user from JWT Bearer token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        scheme, token = authorization.split(" ", 1)
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

    # Decode JWT
    try:
        payload = jwt.decode(token, config.Config.SECRET_KEY, algorithms=[config.Config.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = db.query(database.User).filter(database.User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user
