import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
# This ensures both backend and frontend use the same .env file
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # Fallback to default load_dotenv behavior
    load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smart_companion.db")
    
    # Encryption key for Fernet (must be 32 url-safe base64-encoded bytes)
    # Generate with: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # LLM Configuration (using local mock by default for privacy)
    LLM_API_URL: str = os.getenv("LLM_API_URL", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    
    # Gemini API Configuration (preferred LLM)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Application
    APP_NAME: str = "Smart Companion"
    APP_VERSION: str = "1.0.0"
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "60"))
    
    # Max upload size for images (in bytes) - default 10MB
    MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE", str(10 * 1024 * 1024)))
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    def validate(self) -> None:
        """Validate required settings for production."""
        if self.is_production:
            if not self.ENCRYPTION_KEY:
                raise ValueError("ENCRYPTION_KEY must be set in production")
            if self.CORS_ORIGINS == ["*"]:
                print("⚠️  Warning: CORS_ORIGINS is set to '*' in production")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.validate()
    return settings
