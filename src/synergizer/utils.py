"""Utility helpers for the synergizer package."""

from __future__ import annotations

import re

_slug_pattern = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    value = value.lower()
    value = _slug_pattern.sub("-", value)
    return value.strip("-")
