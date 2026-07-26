"""
Main FastAPI application for Azure AI Infrastructure Platform

This module initializes the FastAPI application with:
- Middleware configuration
- CORS setup
- Route registration
- Error handlers
- OpenAPI/Swagger configuration
- Health checks
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging

from src.config.settings import get_settings
from src.api import routes, schemas
from src.api.routes import health
from src.api.routes import monitoring
from src.api.routes import chat
from src.api.routes import rag
from src.api.routes import prompts
from src.api.routes import guardrails
from src.api.routes import observability
from src.api.utilities_routes import router as utilities_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Production-grade AI platform deployed on Azure with full infrastructure-as-code, monitoring, and operational capabilities.",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_environment}")
    logger.info(f"Log level: {settings.log_level}")
    
    # Log Azure service configuration
    if settings.azure_openai_endpoint:
        logger.info(f"Azure OpenAI configured: {settings.azure_openai_endpoint}")
    if settings.azure_search_endpoint:
        logger.info(f"Azure Cognitive Search configured: {settings.azure_search_endpoint}")
    if settings.azure_storage_account:
        logger.info(f"Azure Storage configured: {settings.azure_storage_account}")
    if settings.azure_key_vault_name:
        logger.info(f"Azure Key Vault configured: {settings.azure_key_vault_name}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info(f"Shutting down {settings.app_name}")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "internal_error",
            "message": "An internal error occurred",
            "details": {"path": str(request.url)},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "validation_error",
            "message": "Invalid request parameters",
            "details": {"errors": exc.errors()},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "chat": "/chat",
            "rag": "/rag/query",
            "monitoring": "/monitoring/metrics",
            "prompts": "/prompts/templates",
            "guardrails": "/guardrails/check-input",
            "observability": "/observability/metrics",
            "utilities": "/utilities"
        }
    }


# Register routers
app.include_router(health.router)
app.include_router(monitoring.router)
app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(prompts.router)
app.include_router(guardrails.router)
app.include_router(observability.router)
app.include_router(utilities_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )