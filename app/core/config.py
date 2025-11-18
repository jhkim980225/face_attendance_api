"""
Application configuration management
Loads environment variables and provides global settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Global application settings"""
    
    # MySQL Configuration
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "attendance_db")
    MYSQL_POOL_SIZE: int = int(os.getenv("MYSQL_POOL_SIZE", "5"))
    MYSQL_MAX_OVERFLOW: int = int(os.getenv("MYSQL_MAX_OVERFLOW", "10"))
    
    # Face Recognition Settings
    TOLERANCE: float = float(os.getenv("TOLERANCE", "0.6"))
    
    # Storage Paths
    IMAGE_DIR: str = os.getenv("IMAGE_DIR", "app/static/images")
    ENCODING_DIR: str = os.getenv("ENCODING_DIR", "app/static/encodings")
    
    # Camera Settings
    STREAM_FPS: int = int(os.getenv("STREAM_FPS", "20"))
    CAMERA_DEVICE_INDEX: int = int(os.getenv("CAMERA_DEVICE_INDEX", "0"))
    
    # Application Settings
    APP_NAME: str = "Face Attendance API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
    
    class Config:
        case_sensitive = True


# Global settings instance
settings = Settings()
