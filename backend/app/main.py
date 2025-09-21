"""FastAPI entrypoint for the Wind Market Wallboard backend service."""

from fastapi import FastAPI

from .api import config, data, health


def create_app() -> FastAPI:
    """Instantiate FastAPI application with router registrations."""

    app = FastAPI(title="Wind Market Wallboard API", version="0.1.0")

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(data.router, prefix="/data", tags=["data"])
    app.include_router(config.router, prefix="/config", tags=["config"])

    return app


app = create_app()
