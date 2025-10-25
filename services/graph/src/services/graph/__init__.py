"""Graph service package exposing the FastAPI app."""

from .main import app, create_app

__all__ = ["app", "create_app"]
