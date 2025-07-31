import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./textbook_management.db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # QR Codes
    QR_CODE_SIZE: int = 300
    QR_CODES_PER_ROW: int = 3
    QR_CODES_PER_COLUMN: int = 7
    
    # Damage Check Period
    DAMAGE_CHECK_DAYS: int = 7
    
    # File Storage
    STATIC_DIR: str = "static"
    QR_CODES_DIR: str = "static/qr_codes"
    UPLOADS_DIR: str = "static/uploads"
    
    class Config:
        env_file = ".env"


settings = Settings()