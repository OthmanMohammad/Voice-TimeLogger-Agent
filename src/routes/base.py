"""
Base router definition and common middleware setup.
"""

from fastapi import APIRouter, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from typing import Callable
from config.config import get_settings
from src.utils import get_logger


logger = get_logger(__name__)

# Create the root API router
api_router = APIRouter()

# Create the versioned router for v1
v1_router = APIRouter(prefix="/api/v1")

settings = get_settings()

# Add CORS middleware setup
def setup_cors(app):
    """
    Setup CORS middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS middleware configured with origins: {settings.CORS_ORIGINS}")


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to add request ID to each request.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware or endpoint handler
        
    Returns:
        Response with request ID header
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    request_logger = get_logger(__name__, {"request_id": request_id})
    
    # Log the request
    start_time = time.time()
    request_logger.info(
        f"Request started: {request.method} {request.url.path}"
    )
    
    # Process the request
    response = await call_next(request)
    
    # Log the response
    process_time = time.time() - start_time
    status_code = response.status_code
    request_logger.info(
        f"Request completed: {request.method} {request.url.path} "
        f"[{status_code}] in {process_time:.3f}s"
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response


# Setup middleware for FastAPI app
def setup_middleware(app):
    """
    Setup all middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    # Add the request ID middleware
    app.middleware("http")(request_id_middleware)
    
    # Add CORS middleware
    setup_cors(app)
    
    logger.info("Application middleware configured")