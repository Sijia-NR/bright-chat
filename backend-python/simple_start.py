#!/usr/bin/env python3
"""
Simple start script for Bright-Chat API
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))

# Import and run the app
from app.main import app

if __name__ == "__main__":
    import uvicorn

    print(f"Starting Bright-Chat API...")
    print(f"Server running on: http://0.0.0.0:18080")
    print(f"API Documentation: http://localhost:18080/docs")
    print(f"Press Ctrl+C to stop")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=18080,
        reload=False,
        log_level="info"
    )