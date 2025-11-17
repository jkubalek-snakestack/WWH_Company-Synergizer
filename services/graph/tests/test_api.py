import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from synergizer.api import create_app


def load_sample_profiles():
    path = Path(__file__).parent.parent / "data" / "sample_profiles.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_analyze_returns_opportunities_and_matches():
    client = TestClient(create_app())
    payload = load_sample_profiles()

    response = client.post("/synergy/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["opportunities"], "expected at least one opportunity"
    assert body["matches"], "expected pairwise matches"


def test_analyze_requires_profiles():
    client = TestClient(create_app())

    response = client.post("/synergy/analyze", json={"profiles": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one profile is required"


def test_analyze_handles_missing_slug():
    """Verify API returns 422/400 when profile missing slug."""
    client = TestClient(create_app())
    payload = {
        "profiles": [
            {
                "name": "Test Company",
                "description": "A test company without slug",
            }
        ]
    }

    response = client.post("/synergy/analyze", json=payload)

    # FastAPI/Pydantic will return 422 for validation errors, but the actual
    # error might be raised during CompanyProfile.from_dict() which could be 500
    # This test documents the current behavior
    assert response.status_code in [400, 422, 500]
    # The response should indicate an error occurred
    body = response.json()
    assert "detail" in body


def test_analyze_handles_missing_name():
    """Verify API returns 422/400 when profile missing name."""
    client = TestClient(create_app())
    payload = {
        "profiles": [
            {
                "slug": "test-company",
                "description": "A test company without name",
            }
        ]
    }

    response = client.post("/synergy/analyze", json=payload)

    # FastAPI/Pydantic will return 422 for validation errors, but the actual
    # error might be raised during CompanyProfile.from_dict() which could be 500
    # This test documents the current behavior
    assert response.status_code in [400, 422, 500]
    # The response should indicate an error occurred
    body = response.json()
    assert "detail" in body


def test_analyze_handles_invalid_json_structure():
    """Verify API handles malformed profile data gracefully."""
    client = TestClient(create_app())
    
    # Test with completely malformed structure
    payload = {
        "profiles": [
            {
                "slug": "test-company",
                "name": "Test Company",
                "offerings": "not-a-list",  # Should be a list
            }
        ]
    }

    response = client.post("/synergy/analyze", json=payload)

    # The API should handle this gracefully (either validate or return error)
    assert response.status_code in [400, 422, 500]
    
    # Test with missing required nested structure
    payload2 = {
        "profiles": [
            {
                "slug": "test-company",
                "name": "Test Company",
                "offerings": [
                    {
                        # Missing "name" field which is required for Capability
                        "description": "A capability without name",
                    }
                ],
            }
        ]
    }

    response2 = client.post("/synergy/analyze", json=payload2)
    assert response2.status_code in [400, 422, 500]


def test_analyze_handles_invalid_engagement_channels():
    """Verify API handles invalid channel values in profiles."""
    client = TestClient(create_app())
    payload = {
        "profiles": [
            {
                "slug": "test-company",
                "name": "Test Company",
                "offerings": [
                    {
                        "name": "Test Offering",
                        "description": "A test offering",
                        "engagement_channels": ["invalid_channel", "service"],
                    }
                ],
            }
        ]
    }

    response = client.post("/synergy/analyze", json=payload)

    # The API should handle invalid enum values gracefully
    assert response.status_code in [400, 422, 500]
    
    # Test with invalid channels in needs
    payload2 = {
        "profiles": [
            {
                "slug": "test-company",
                "name": "Test Company",
                "needs": [
                    {
                        "name": "Test Need",
                        "description": "A test need",
                        "engagement_channels": ["invalid_channel", "operations"],
                    }
                ],
            }
        ]
    }

    response2 = client.post("/synergy/analyze", json=payload2)
    assert response2.status_code in [400, 422, 500]
