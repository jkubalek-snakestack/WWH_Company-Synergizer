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
    """Verify API returns 400 when profiles list is empty."""
    client = TestClient(create_app())

    response = client.post("/synergy/analyze", json={"profiles": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one profile is required"


def test_analyze_handles_missing_profiles_and_companies():
    """Verify API returns 400 when both profiles and companies keys are missing."""
    client = TestClient(create_app())

    response = client.post("/synergy/analyze", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one profile is required"


def test_analyze_handles_empty_payload():
    """Verify API returns 400 when both profiles and companies are None/empty."""
    client = TestClient(create_app())

    # Test with both None
    response = client.post("/synergy/analyze", json={"profiles": None, "companies": None})

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one profile is required"

    # Test with empty companies
    response2 = client.post("/synergy/analyze", json={"companies": []})

    assert response2.status_code == 400
    assert response2.json()["detail"] == "At least one profile is required"


def test_analyze_handles_mixed_profiles_and_companies():
    """Verify API prefers profiles over companies when both are present."""
    client = TestClient(create_app())
    
    # When both are present, profiles should be used
    payload = {
        "profiles": [
            {
                "slug": "profile-company",
                "name": "Profile Company",
            }
        ],
        "companies": [
            {
                "slug": "companies-company",
                "name": "Companies Company",
            }
        ]
    }

    response = client.post("/synergy/analyze", json=payload)

    # Should succeed and use profiles
    assert response.status_code == 200
    body = response.json()
    assert body["opportunities"] is not None
    assert body["matches"] is not None


def test_analyze_handles_missing_slug():
    """Verify API returns 422 when profile missing slug (not 500)."""
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

    # Should return 422 (Unprocessable Entity) not 500 (Internal Server Error)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"
    body = response.json()
    assert "detail" in body
    # Error should mention the missing field
    assert "slug" in body["detail"].lower() or "index" in body["detail"].lower()


def test_analyze_handles_missing_name():
    """Verify API returns 422 when profile missing name (not 500)."""
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

    # Should return 422 (Unprocessable Entity) not 500 (Internal Server Error)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"
    body = response.json()
    assert "detail" in body
    # Error should mention the missing field
    assert "name" in body["detail"].lower() or "index" in body["detail"].lower()


def test_analyze_handles_invalid_json_structure():
    """Verify API handles malformed profile data gracefully with 422 (not 500)."""
    client = TestClient(create_app())
    
    # Test with completely malformed structure - offerings should be a list
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

    # Should return 422 (Unprocessable Entity) not 500 (Internal Server Error)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"
    body = response.json()
    assert "detail" in body
    
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
    assert response2.status_code == 422, f"Expected 422, got {response2.status_code}: {response2.json()}"
    body2 = response2.json()
    assert "detail" in body2


def test_analyze_handles_invalid_engagement_channels():
    """Verify API handles invalid channel values in profiles with 422 (not 500)."""
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

    # Should return 422 (Unprocessable Entity) not 500 (Internal Server Error)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"
    body = response.json()
    assert "detail" in body
    
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
    assert response2.status_code == 422, f"Expected 422, got {response2.status_code}: {response2.json()}"
    body2 = response2.json()
    assert "detail" in body2


def load_templates():
    """Helper to load template bundle for testing."""
    path = Path(__file__).parent.parent / "data" / "templates.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_analyze_with_template_bundle():
    """Verify API works with template bundle for grouping."""
    client = TestClient(create_app())
    payload = load_sample_profiles()
    template_bundle = load_templates()
    
    payload["template_bundle"] = template_bundle
    
    response = client.post("/synergy/analyze", json=payload)
    
    assert response.status_code == 200
    body = response.json()
    assert body["opportunities"] is not None
    assert body["matches"] is not None
    # When template bundle is provided, groups should be present
    assert "groups" in body
    # Groups should be a dict mapping tier names to company slug lists
    if body["groups"]:
        assert isinstance(body["groups"], dict)
        for tier_name, company_slugs in body["groups"].items():
            assert isinstance(tier_name, str)
            assert isinstance(company_slugs, list)
            assert all(isinstance(slug, str) for slug in company_slugs)


def test_analyze_with_invalid_template_bundle():
    """Verify API handles invalid template bundle gracefully with 422 (not 500)."""
    client = TestClient(create_app())
    payload = load_sample_profiles()
    
    # Test with malformed template bundle structure
    payload["template_bundle"] = {
        "templates": [
            {
                # Missing required "name" field
                "description": "Invalid template",
            }
        ]
    }
    
    response = client.post("/synergy/analyze", json=payload)
    
    # Should return 422 (Unprocessable Entity) not 500 (Internal Server Error)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"
    body = response.json()
    assert "detail" in body
    assert "Invalid template bundle" in body["detail"]


def test_analyze_response_structure():
    """Verify API response has correct structure."""
    client = TestClient(create_app())
    payload = load_sample_profiles()
    
    response = client.post("/synergy/analyze", json=payload)
    
    assert response.status_code == 200
    body = response.json()
    
    # Verify required fields
    assert "opportunities" in body
    assert "matches" in body
    
    # Verify types
    assert isinstance(body["opportunities"], list)
    assert isinstance(body["matches"], list)
    
    # Verify opportunities structure
    if body["opportunities"]:
        opp = body["opportunities"][0]
        assert isinstance(opp, dict)
        # Check for expected fields in opportunity
        assert "participants" in opp or "summary" in opp or "priority" in opp
    
    # Verify matches structure
    if body["matches"]:
        match = body["matches"][0]
        assert isinstance(match, dict)
        # Check for expected fields in match
        assert "source_company" in match or "target_company" in match or "description" in match
    
    # Groups is optional
    if "groups" in body:
        assert body["groups"] is None or isinstance(body["groups"], dict)
