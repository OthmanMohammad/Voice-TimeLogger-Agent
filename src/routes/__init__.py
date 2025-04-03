"""
Routes package for the Voice-TimeLogger-Agent API.
"""

from fastapi import APIRouter
from src.routes.base import api_router, v1_router
from src.routes.speech import router as speech_router
from src.routes.extraction import router as extraction_router
from src.utils import get_logger


logger = get_logger(__name__)

# Include all routers
v1_router.include_router(speech_router)
v1_router.include_router(extraction_router)

# Include versioned router in the main API router
api_router.include_router(v1_router)

# Root endpoint
@api_router.get("/", tags=["status"])
async def root():
    """Root endpoint for API health check."""
    return {
        "status": "ok",
        "message": "Voice-TimeLogger-Agent API is running"
    }

# API health check
@api_router.get("/health", tags=["status"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1"
    }

logger.info("API routes initialized")