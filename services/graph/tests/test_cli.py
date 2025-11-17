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


def test_cli_build_engine_missing_template_file(capsys):
    """Verify missing template file is handled with friendly error and exit code 1."""
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
        
        # Should exit with code 1 and print friendly error
        with pytest.raises(SystemExit) as exc_info:
            build_engine(profiles, missing_template_path)
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Template file not found" in captured.err
        assert str(missing_template_path) in captured.err
    finally:
        profiles_path.unlink()


def test_cli_build_engine_invalid_template_file(capsys):
    """Verify invalid template JSON is handled with friendly error and exit code 1."""
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
        
        # Should exit with code 1 and print friendly error
        with pytest.raises(SystemExit) as exc_info:
            build_engine(profiles, invalid_template_path)
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Invalid template bundle" in captured.err
        assert str(invalid_template_path) in captured.err
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


def test_cli_narrative_missing_file(capsys):
    """Verify missing narrative file is handled with friendly error and exit code 1."""
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
        # Should exit with code 1 and print friendly error
        with pytest.raises(SystemExit) as exc_info:
            main([
                str(profiles_path),
                "--narrative", str(missing_narrative_path),
                "--openai-model", "gpt-4",
            ])
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Narrative file not found" in captured.err
        assert str(missing_narrative_path) in captured.err
    finally:
        profiles_path.unlink()


def test_cli_load_profiles_missing_file(capsys):
    """Verify missing profile file is handled with friendly error and exit code 1."""
    missing_path = Path("/nonexistent/profiles.json")
    
    # Should exit with code 1 and print friendly error
    with pytest.raises(SystemExit) as exc_info:
        main([str(missing_path)])
    
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Profile file not found" in captured.err
    assert str(missing_path) in captured.err


def test_cli_load_profiles_invalid_json(capsys):
    """Verify invalid JSON in profile file is handled with friendly error and exit code 1."""
    # Create temporary file with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        invalid_json_path = Path(f.name)
    
    try:
        # Should exit with code 1 and print friendly error
        with pytest.raises(SystemExit) as exc_info:
            main([str(invalid_json_path)])
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Invalid JSON in profile file" in captured.err
        assert str(invalid_json_path) in captured.err
    finally:
        invalid_json_path.unlink()


def test_cli_load_profiles_malformed_structure(capsys):
    """Verify malformed JSON structure (missing 'companies' key) is handled with friendly error."""
    # Create temporary file with valid JSON but missing 'companies' key
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "not_companies": [
                {
                    "slug": "test-company",
                    "name": "Test Company",
                }
            ]
        }
        json.dump(data, f)
        malformed_path = Path(f.name)
    
    try:
        # Should exit with code 1 and print friendly error
        with pytest.raises(SystemExit) as exc_info:
            main([str(malformed_path)])
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Profile file" in captured.err
        assert "missing required 'companies' key" in captured.err
        assert str(malformed_path) in captured.err
    finally:
        malformed_path.unlink()

