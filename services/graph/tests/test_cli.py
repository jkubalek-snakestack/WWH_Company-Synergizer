"""Tests for the CLI interface."""

import json
import tempfile
from pathlib import Path

import pytest

from synergizer.cli import build_engine, load_profiles, main


def test_cli_load_profiles_valid_json():
    """Verify loading valid JSON file works."""
    # Create a temporary valid JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "companies": [
                {
                    "slug": "test-company",
                    "name": "Test Company",
                    "description": "A test company",
                }
            ]
        }
        json.dump(data, f)
        temp_path = Path(f.name)
    
    try:
        profiles = load_profiles(temp_path)
        
        assert len(profiles) == 1
        assert profiles[0].slug == "test-company"
        assert profiles[0].name == "Test Company"
    finally:
        temp_path.unlink()


def test_cli_build_engine_with_templates():
    """Verify engine builds correctly with templates."""
    # Create temporary profiles file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "companies": [
                {
                    "slug": "test-company",
                    "name": "Test Company",
                    "organization_type": "NonProfit",
                    "description": "A test company",
                }
            ]
        }
        json.dump(data, f)
        profiles_path = Path(f.name)
    
    # Use existing templates file
    templates_path = Path(__file__).parent.parent / "data" / "templates.json"
    
    try:
        profiles = load_profiles(profiles_path)
        engine = build_engine(profiles, templates_path)
        
        # Verify engine was built
        assert engine is not None
        # Verify companies were registered
        registered = list(engine.graph.companies())
        assert len(registered) == 1
        assert registered[0].slug == "test-company"
    finally:
        profiles_path.unlink()


def test_cli_build_engine_missing_template_file():
    """Verify missing template file is handled."""
    # Create temporary profiles file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "companies": [
                {
                    "slug": "test-company",
                    "name": "Test Company",
                    "description": "A test company",
                }
            ]
        }
        json.dump(data, f)
        profiles_path = Path(f.name)
    
    # Use non-existent template file
    missing_template_path = Path("/nonexistent/templates.json")
    
    try:
        profiles = load_profiles(profiles_path)
        
        # Current implementation may raise FileNotFoundError
        # This test documents the current behavior
        with pytest.raises((FileNotFoundError, OSError)):
            build_engine(profiles, missing_template_path)
    finally:
        profiles_path.unlink()


def test_cli_build_engine_invalid_template_file():
    """Verify invalid template JSON is handled."""
    # Create temporary profiles file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "companies": [
                {
                    "slug": "test-company",
                    "name": "Test Company",
                    "description": "A test company",
                }
            ]
        }
        json.dump(data, f)
        profiles_path = Path(f.name)
    
    # Create invalid template file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Invalid JSON structure - missing required "name" field in template
        invalid_data = {
            "templates": [
                {
                    "description": "Invalid template without name",
                }
            ]
        }
        json.dump(invalid_data, f)
        invalid_template_path = Path(f.name)
    
    try:
        profiles = load_profiles(profiles_path)
        
        # Current implementation may raise TypeError or ValueError
        # This test documents the current behavior
        with pytest.raises((TypeError, ValueError, KeyError)):
            build_engine(profiles, invalid_template_path)
    finally:
        profiles_path.unlink()
        invalid_template_path.unlink()


def test_cli_narrative_requires_model():
    """Verify --narrative requires --openai-model."""
    # Create temporary profiles file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "companies": [
                {
                    "slug": "test-company",
                    "name": "Test Company",
                    "description": "A test company",
                }
            ]
        }
        json.dump(data, f)
        profiles_path = Path(f.name)
    
    # Create temporary narrative file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test narrative about a company.")
        narrative_path = Path(f.name)
    
    try:
        # Call main with --narrative but without --openai-model
        # argparse should raise SystemExit with error message
        with pytest.raises(SystemExit) as exc_info:
            main([
                str(profiles_path),
                "--narrative", str(narrative_path),
            ])
        
        # argparse.error() typically exits with code 2
        assert exc_info.value.code == 2
    finally:
        profiles_path.unlink()
        narrative_path.unlink()


def test_cli_narrative_missing_file():
    """Verify missing narrative file is handled."""
    # Create temporary profiles file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "companies": [
                {
                    "slug": "test-company",
                    "name": "Test Company",
                    "description": "A test company",
                }
            ]
        }
        json.dump(data, f)
        profiles_path = Path(f.name)
    
    # Use non-existent narrative file
    missing_narrative_path = Path("/nonexistent/narrative.txt")
    
    try:
        # Current implementation may raise FileNotFoundError when reading narrative
        # This test documents the current behavior
        with pytest.raises((FileNotFoundError, OSError)):
            main([
                str(profiles_path),
                "--narrative", str(missing_narrative_path),
                "--openai-model", "gpt-4",
            ])
    finally:
        profiles_path.unlink()

