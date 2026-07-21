from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Core API Keys
    LYZR_API_KEY: str
    GOOGLE_API_KEY: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    
    # Environment config
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance to be imported across the app
settings = Settings()
