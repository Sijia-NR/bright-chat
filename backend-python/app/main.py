import os
import sys
import logging
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .core.config import settings
from .core.database import init_db, check_db_connection
from .api.middleware import setup_middleware
from .api import auth, users, sessions, ias

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure basic logging
logging.basicConfig(
    format=settings.LOG_FORMAT,
    level=getattr(logging, settings.LOG_LEVEL),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
    ]
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Bright-Chat API server")

    # Check database connection
    if not check_db_connection():
        logger.error("Database connection failed")
        sys.exit(1)

    # Initialize database
    init_db()
    logger.info("Database initialized successfully")

    # Yield to application
    yield

    # Shutdown
    logger.info("Shutting down Bright-Chat API server")


# Create FastAPI app
app = FastAPI(
    title=settings.OPENAPI_TITLE,
    description=settings.OPENAPI_DESCRIPTION,
    version=settings.OPENAPI_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.OPENAPI_TITLE,
        version=settings.OPENAPI_VERSION,
        description=settings.OPENAPI_DESCRIPTION,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://bright-chat.com/logo.png"
    }
    openapi_schema["servers"] = [
        {
            "url": f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}",
            "description": "Development server"
        }
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Setup middleware
setup_middleware(app)

# Include API routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(sessions.router, prefix=settings.API_PREFIX)
app.include_router(ias.router, prefix=settings.API_PREFIX)


# Health check endpoint
@app.get("/health", summary="Health Check", tags=["General"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": logger.new().bind(timestamp=True).get("timestamp")
    }


# Root endpoint
@app.get("/", summary="API Information", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": "/api/v1"
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=str(request.url),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include Prometheus metrics if enabled
if settings.PROMETHEUS_ENABLED:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(app, should_gzip=True, endpoint="/metrics")
        logger.info("Prometheus metrics enabled at /metrics")
    except ImportError:
        logger.warning("Prometheus client not installed, skipping metrics")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.APP_DEBUG,
        workers=1 if settings.APP_DEBUG else settings.SERVER_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )