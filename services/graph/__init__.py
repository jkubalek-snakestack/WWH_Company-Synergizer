"""FastAPI graph service exposing synergy analytics."""

from __future__ import annotations

from typing import Any

__all__ = ["create_app"]


def create_app(*args: Any, **kwargs: Any):
    """Lazily import the FastAPI factory to avoid hard dependency during tests."""

    from .main import create_app as _create_app

    return _create_app(*args, **kwargs)
