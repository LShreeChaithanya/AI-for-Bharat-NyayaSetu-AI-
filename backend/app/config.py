"""
Configuration management for NyayaSetu AI Platform
Uses environment variables for sensitive data
"""
from pathlib import Path

from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve .env path: prefer project root (parent of backend), then backend, then cwd
_BASE_DIR = Path(__file__).resolve().parent.parent  # backend/app -> backend
_PROJECT_ROOT = _BASE_DIR.parent  # backend -> project root
_ENV_CANDIDATES = [_PROJECT_ROOT / ".env", _BASE_DIR / ".env", Path(".env")]


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "NyayaSetu AI Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # AWS Bedrock (auth via bearer token only)
    AWS_REGION: str = "ap-south-1"
    AWS_BEARER_TOKEN_BEDROCK: str = ""
    # Use inference profile ID (required for Converse on-demand). For ap-south-1 use global.*; for us-east-1 use us.amazon.*
    BEDROCK_MODEL_ID: str = "global.amazon.nova-2-lite-v1:0"
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "nyayasetu"
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_URL: str = "redis://localhost:6379/0"
    REDIS_BROKER_URL: str = "redis://localhost:6380/0"
    REDIS_PUBSUB_URL: str = "redis://localhost:6381/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: list = ["pdf", "jpg", "jpeg", "png"]
    
    # De-identification (optional override; default is resolved relative to app/ai package)
    DEIDENTIFICATION_PROMPT_PATH: str = ""
    # Deprecated: kept so .env can still contain it without validation error (not used)
    DEIDENTIFICATION_MAP_PATH: str = ""
    # Path to folder containing PDFs for testing (relative to backend or project root)
    DOC_FOLDER: str = "doc"
    
    class Config:
        env_file = str(next((p for p in _ENV_CANDIDATES if p.exists()), Path(".env")))
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses lru_cache to avoid reading .env file multiple times
    """
    return Settings()


# Global settings instance
settings = get_settings()
