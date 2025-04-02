"""
Centralized logging configuration for the Voice-TimeLogger-Agent.
Provides consistent logging setup across the application.
"""

import logging
import sys
import os
from typing import Optional, Dict, Any
import uuid
from functools import wraps
import traceback
import json

# Log levels dictionary for easy reference
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

class ContextAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to log messages.
    Allows adding request_id and other context to logs.
    """
    
    def process(self, msg, kwargs):
        # Add extra context to the log message
        extra = kwargs.get('extra', {})
        if self.extra:
            extra.update(self.extra)
            kwargs['extra'] = extra
        
        # Format the message with context if available
        if extra and extra.get('request_id'):
            return f"[{extra.get('request_id')}] {msg}", kwargs
        return msg, kwargs


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger with the specified name and optional context.
    
    Args:
        name: Name of the logger (usually __name__)
        context: Optional dictionary with context info
    
    Returns:
        Logger instance with proper configuration
    """
    logger = logging.getLogger(name)
    
    # If context is provided, return a context adapter
    if context:
        return ContextAdapter(logger, context)
    
    return logger


def configure_logging(
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string (if None, uses default format)
        log_file: Path to log file (if None, logs to stdout only)
    """
    # Get the numeric level from the name
    numeric_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    # Define default log format if not provided
    if not log_format:
        log_format = (
            "%(asctime)s - %(levelname)s - %(name)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # Basic configuration
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler if requested
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set third-party loggers to higher level to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def generate_request_id() -> str:
    """Generate a unique request ID for tracking operations in logs."""
    return str(uuid.uuid4())


def log_function_call(logger):
    """
    Decorator to log function entry/exit and exceptions.
    
    Args:
        logger: Logger instance to use
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            try:
                # Log entry
                logger.debug(f"Entering {func_name}")
                # Call the function
                result = func(*args, **kwargs)
                # Log exit
                logger.debug(f"Exiting {func_name}")
                return result
            except Exception as e:
                # Log exception with traceback
                logger.error(
                    f"Exception in {func_name}: {str(e)}",
                    exc_info=True
                )
                # Re-raise the exception
                raise
        return wrapper
    return decorator


def log_async_function_call(logger):
    """
    Decorator to log async function entry/exit and exceptions.
    
    Args:
        logger: Logger instance to use
    
    Returns:
        Decorated async function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            try:
                # Log entry
                logger.debug(f"Entering {func_name}")
                # Call the function
                result = await func(*args, **kwargs)
                # Log exit
                logger.debug(f"Exiting {func_name}")
                return result
            except Exception as e:
                # Log exception with traceback
                logger.error(
                    f"Exception in {func_name}: {str(e)}",
                    exc_info=True
                )
                # Re-raise the exception
                raise
        return wrapper
    return decorator


def format_structured_log(message: str, data: Dict[str, Any]) -> str:
    """
    Format a structured log message with JSON data.
    
    Args:
        message: Log message text
        data: Dictionary of data to include
    
    Returns:
        Formatted log message with JSON data
    """
    try:
        json_data = json.dumps(data)
        return f"{message} | {json_data}"
    except Exception:
        return f"{message} | {data!r}"