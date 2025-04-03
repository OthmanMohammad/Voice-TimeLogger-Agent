"""
Main application entry point for Voice-TimeLogger-Agent API.
"""

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from typing import Dict, Any, Optional
import os

from config.config import get_settings
from src.app import init_app
from src.routes import api_router
from src.routes.base import setup_middleware
from src.utils import get_logger, BaseAppException, ErrorCode
from src.utils.exceptions import ConfigurationError


logger = get_logger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Voice-TimeLogger-Agent API",
    description="API for automating consultant work hours using voice messages",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Initialize the app with middleware
setup_middleware(app)

# Include API routes
app.include_router(api_router)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    logger.warning(f"Validation error: {error_details}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "error_details": error_details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle application exceptions."""
    logger.error(f"Application error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": exc.message,
            "error_code": exc.code_value,
            "error_details": exc.details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": f"Unexpected error: {str(exc)}",
            "error_code": ErrorCode.UNKNOWN_ERROR.value,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Voice-TimeLogger-Agent API")
    try:
        init_app()  # calls existing app.py initialization
        logger.info("Application initialized successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}", exc_info=True)
        # Exit the application if critical configuration is missing
        os._exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        # Exit the application if initialization fails
        os._exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Voice-TimeLogger-Agent API")

if __name__ == "__main__":
    try:
        host = settings.API_HOST
        port = settings.API_PORT
        
        logger.info(f"Starting API server on {host}:{port}")
        
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=settings.DEBUG
        )
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}", exc_info=True)
        os._exit(1)