"""Uvicorn entrypoint for the synergy FastAPI service."""

from synergizer.api import create_app

app = create_app()

__all__ = ["app", "create_app"]
