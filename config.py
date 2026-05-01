import os

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medipure.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "medipure-super-secret-key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
