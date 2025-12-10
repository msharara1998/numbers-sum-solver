"""
Main entry point for the Numbers Sum Solver backend API server.

This module starts the FastAPI application with Uvicorn.
"""

import uvicorn
from backend.logging_config import setup_logging


def main() -> None:
    """Start the FastAPI server with Uvicorn."""
    setup_logging()
    
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
