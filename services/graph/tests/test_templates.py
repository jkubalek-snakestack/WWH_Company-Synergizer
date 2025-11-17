"""Tests for the template library."""

import json
import tempfile
from pathlib import Path

import pytest

from synergizer.templates import ProfileTemplateLibrary


def test_template_library_template_missing_raises():
    """Verify template() raises KeyError for missing template."""
    library = ProfileTemplateLibrary()
    
    # Load a template bundle with known templates
    templates_path = Path(__file__).parent.parent / "data" / "templates.json"
    library.load_from_file(str(templates_path))
    
    # Accessing a non-existent template should raise KeyError
    with pytest.raises(KeyError):
        library.template("NonExistentTemplate")
    
    # Verify the error message is clear
    try:
        library.template("missing-template")
    except KeyError as e:
        assert "missing-template" in str(e) or "missing-template" in repr(e)


def test_template_library_tier_missing_raises():
    """Verify tier() raises KeyError for missing tier."""
    library = ProfileTemplateLibrary()
    
    # Load a template bundle with known tiering rules
    templates_path = Path(__file__).parent.parent / "data" / "templates.json"
    library.load_from_file(str(templates_path))
    
    # Accessing a non-existent tier should raise KeyError
    with pytest.raises(KeyError):
        library.tier("NonExistentTier")
    
    # Verify the error message is clear
    try:
        library.tier("missing-tier")
    except KeyError as e:
        assert "missing-tier" in str(e) or "missing-tier" in repr(e)

