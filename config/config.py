import os
from pydantic import BaseSettings, Field, ValidationError as PydanticValidationError
from typing import Optional, List
from functools import lru_cache
from dotenv import load_dotenv, find_dotenv
import logging
from src.utils.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    env_file = find_dotenv()
    load_dotenv(env_file, override=True)
    if env_file:
        logger.info(f"Loaded environment from {env_file}")
    else:
        logger.warning("No .env file found, using environment variables")
except Exception as e:
    logger.warning(f"Error loading .env file: {str(e)}")

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App settings
    APP_NAME: str = Field(default="Voice-TimeLogger-Agent")
    APP_VERSION: str = Field(default="1.0.0")
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
    ENABLE_EMAIL_NOTIFICATIONS: bool = Field(default=False)
    ENABLE_SLACK_NOTIFICATIONS: bool = Field(default=False)
    
    # Slack notification settings
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # Email notification settings
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = Field(default=587)
    SENDER_EMAIL: Optional[str] = None
    SENDER_PASSWORD: Optional[str] = None
    RECIPIENT_EMAILS: str = Field(default="")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Create a cached instance of the settings.
    
    Returns:
        Settings instance
    
    Raises:
        ConfigurationError: If settings cannot be loaded
    """
    try:
        settings = Settings()
        logger.debug("Settings loaded successfully")
        return settings
    except PydanticValidationError as e:
        error_details = {"validation_errors": e.errors()}
        logger.error(f"Settings validation error: {error_details}")
        raise ConfigurationError(
            "Failed to load application settings",
            details=error_details,
            original_exception=e
        )
    except Exception as e:
        logger.error(f"Unexpected error loading settings: {str(e)}")
        raise ConfigurationError(
            "Unexpected error loading application settings",
            original_exception=e
        )


def validate_settings() -> List[str]:
    """
    Validate that all required settings are present.
    
    Returns:
        List of missing required settings
    
    Raises:
        ConfigurationError: If the settings cannot be accessed
    """
    try:
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
        
        # Check email notification settings
        if settings.ENABLE_EMAIL_NOTIFICATIONS:
            if not settings.SMTP_SERVER:
                missing.append("SMTP_SERVER")
            if not settings.SENDER_EMAIL:
                missing.append("SENDER_EMAIL")
            if not settings.SENDER_PASSWORD:
                missing.append("SENDER_PASSWORD")
            if not settings.RECIPIENT_EMAILS:
                missing.append("RECIPIENT_EMAILS")
        
        # Check Slack notification settings
        if settings.ENABLE_SLACK_NOTIFICATIONS:
            if not settings.SLACK_WEBHOOK_URL:
                missing.append("SLACK_WEBHOOK_URL")
        
        # Log the results
        if missing:
            logger.warning(f"Missing required settings: {', '.join(missing)}")
        else:
            logger.info("All required settings are present")
        
        return missing
        
    except Exception as e:
        logger.error(f"Error validating settings: {str(e)}")
        raise ConfigurationError(
            "Failed to validate application settings",
            original_exception=e
        )