"""
Main application module for Voice-TimeLogger-Agent.
Responsible for initializing the application and services.
"""

import os
from typing import List, Optional
import logging

from config.config import get_settings, validate_settings
from src.utils import configure_logging, get_logger
from src.utils.exceptions import ConfigurationError

# First configure basic logging before we do anything else
configure_logging()
logger = get_logger(__name__)

def init_app():
    """
    Initialize the application.
    Sets up configuration, logging, and dependencies.
    
    Raises:
        ConfigurationError: If required settings are missing
    """
    logger.info("Initializing Voice-TimeLogger-Agent application")
    
    try:
        # Load settings
        settings = get_settings()
        logger.info(f"Application: {settings.APP_NAME} v{settings.APP_VERSION}")
        
        # Configure logging based on settings
        configure_logging(
            level=settings.LOG_LEVEL,
            log_file=settings.LOG_FILE
        )
        
        # Validate required settings
        missing_settings = validate_settings()
        if missing_settings:
            missing_str = ", ".join(missing_settings)
            logger.error(f"Missing required settings: {missing_str}")
            raise ConfigurationError(
                f"Missing required settings: {missing_str}",
                details={"missing_settings": missing_settings}
            )
        
        # Create temp directory if it doesn't exist
        if not os.path.exists(settings.TEMP_DIR):
            logger.info(f"Creating temp directory: {settings.TEMP_DIR}")
            os.makedirs(settings.TEMP_DIR, exist_ok=True)
        
        logger.info("Application initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        raise