import os
import secrets

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medipure.db")
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))  # Random key per startup if not set
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
