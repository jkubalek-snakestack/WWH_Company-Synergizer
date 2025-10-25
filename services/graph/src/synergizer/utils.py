"""Utility helpers for the synergizer package."""

from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

_slug_pattern = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    value = value.lower()
    value = _slug_pattern.sub("-", value)
    return value.strip("-")


def serialize_dataclass(instance: Any) -> Any:
    """Convert a dataclass into JSON-serializable primitives."""

    if not is_dataclass(instance):
        raise TypeError("serialize_dataclass expects a dataclass instance")

    def _convert(value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, list):
            return [_convert(item) for item in value]
        if isinstance(value, tuple):
            return tuple(_convert(item) for item in value)
        if isinstance(value, dict):
            return {key: _convert(val) for key, val in value.items()}
        return value

    raw = asdict(instance)
    return _convert(raw)
