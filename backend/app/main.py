"""FastAPI entrypoint for the Wind Market Wallboard backend service."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from .api import config, data, health, websocket


def create_app() -> FastAPI:
    """Instantiate FastAPI application with router registrations."""

    app = FastAPI(title="Wind Market Wallboard API", version="0.1.0")

    # Add CORS middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(data.router, prefix="/data", tags=["data"])
    app.include_router(config.router, prefix="/config", tags=["config"])
    app.include_router(websocket.router, tags=["websocket"])

    # Serve static files (frontend)
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    return app


app = create_app()
