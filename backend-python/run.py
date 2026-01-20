#!/usr/bin/env python3
"""
Run script for Bright-Chat API server
"""
import os
import sys
import uvicorn

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


def main():
    """Main function to run the server."""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Server running on http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"API documentation available at http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.APP_DEBUG,
        workers=1 if settings.APP_DEBUG else settings.SERVER_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()