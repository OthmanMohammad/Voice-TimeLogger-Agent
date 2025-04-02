import os
from pydantic import BaseSettings, Field
from typing import Optional, List
from functools import lru_cache
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App settings
    APP_NAME: str = "Voice-TimeLogger-Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    
    # API settings
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    CORS_ORIGINS: List[str] = Field(default=["*"])
    
    # Temp directory
    TEMP_DIR: str = Field(default="./tmp/meeting_recordings")
    
    # Speech-to-text settings
    SPEECH_PROVIDER: str = Field(default="openai") # "openai" or "google"
    OPENAI_API_KEY: Optional[str] = None
    
    # Data extraction settings
    USE_LLM: bool = Field(default=True)
    
    # Google Sheets settings
    GOOGLE_CREDENTIALS_FILE: Optional[str] = None
    GOOGLE_SPREADSHEET_ID: Optional[str] = None
    
    # Notification settings
    NOTIFICATION_TYPE: str = Field(default="none") # "none", "slack", or "email"
    SLACK_WEBHOOK_URL: Optional[str] = None
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = Field(default=587)
    SENDER_EMAIL: Optional[str] = None
    SENDER_PASSWORD: Optional[str] = None
    RECIPIENT_EMAILS: str = Field(default="")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Create a cached instance of the settings."""
    return Settings()


def validate_settings() -> List[str]:
    """
    Validate that all required settings are present.
    
    Returns:
        List of missing required settings
    """
    settings = get_settings()
    missing = []
    
    # Check for required settings
    if settings.SPEECH_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    
    if settings.USE_LLM and not settings.OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    
    if not settings.GOOGLE_CREDENTIALS_FILE or not os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
        missing.append("GOOGLE_CREDENTIALS_FILE")
    
    if not settings.GOOGLE_SPREADSHEET_ID:
        missing.append("GOOGLE_SPREADSHEET_ID")
    
    if settings.NOTIFICATION_TYPE == "slack" and not settings.SLACK_WEBHOOK_URL:
        missing.append("SLACK_WEBHOOK_URL")
    
    if settings.NOTIFICATION_TYPE == "email":
        if not settings.SMTP_SERVER:
            missing.append("SMTP_SERVER")
        if not settings.SENDER_EMAIL:
            missing.append("SENDER_EMAIL")
        if not settings.SENDER_PASSWORD:
            missing.append("SENDER_PASSWORD")
        if not settings.RECIPIENT_EMAILS:
            missing.append("RECIPIENT_EMAILS")
    
    return missing
