import os
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smart_companion.db")
    
    # Encryption key for Fernet (must be 32 url-safe base64-encoded bytes)
    # Generate with: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
    ENCRYPTION_KEY: str = os.getenv(
        "ENCRYPTION_KEY", 
        "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY="  # Default for dev only
    )
    
    # LLM Configuration (using local mock by default for privacy)
    LLM_API_URL: str = os.getenv("LLM_API_URL", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    
    # Gemini API Configuration (preferred LLM)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Application
    APP_NAME: str = "Smart Companion"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
