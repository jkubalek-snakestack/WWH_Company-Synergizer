"""Tests for the synergizer models."""

from __future__ import annotations

import pytest

from synergizer.models import (
    Capability,
    CompanyProfile,
    Contact,
    EngagementChannel,
    Location,
    Need,
)


def test_company_profile_requires_slug():
    """Verify CompanyProfile.from_dict() raises ValueError when slug is missing."""
    payload = {
        "name": "Test Company",
        "description": "A test company",
    }

    with pytest.raises(ValueError, match="CompanyProfile missing required field: slug"):
        CompanyProfile.from_dict(payload)


def test_company_profile_requires_name():
    """Verify CompanyProfile.from_dict() raises ValueError when name is missing."""
    payload = {
        "slug": "test-company",
        "description": "A test company",
    }

    with pytest.raises(ValueError, match="CompanyProfile missing required field: name"):
        CompanyProfile.from_dict(payload)


def test_capability_from_dict_with_invalid_channels():
    """Verify invalid engagement channels in Capability are handled gracefully."""
    payload = {
        "name": "Test Capability",
        "description": "A test capability",
        "engagement_channels": ["invalid_channel", "service"],
    }

    with pytest.raises(ValueError):
        Capability.from_dict(payload)


def test_need_from_dict_with_invalid_channels():
    """Verify invalid engagement channels in Need are handled gracefully."""
    payload = {
        "name": "Test Need",
        "description": "A test need",
        "urgency": 3,
        "engagement_channels": ["invalid_channel", "operations"],
    }

    with pytest.raises(ValueError):
        Need.from_dict(payload)


def test_engagement_channel_from_value_invalid():
    """Test EngagementChannel.from_value() with invalid values."""
    # The current implementation tries to lower() invalid values, which will still fail
    # if the lowercased value is also invalid
    with pytest.raises(ValueError):
        EngagementChannel.from_value("completely_invalid_channel")

    # Test with empty string (will try empty string after lower(), still invalid)
    with pytest.raises(ValueError):
        EngagementChannel.from_value("")


def test_company_profile_handles_optional_fields():
    """Verify all optional fields default correctly when missing."""
    # Minimal payload with only required fields
    payload = {
        "slug": "test-company",
        "name": "Test Company",
    }
    
    profile = CompanyProfile.from_dict(payload)
    
    # Verify optional fields have correct defaults
    assert profile.description is None
    assert profile.mission is None
    assert profile.organization_type is None
    assert profile.headquarters is None
    assert profile.regions_active == []
    assert profile.employee_count is None
    assert profile.expertise == []
    assert profile.industries == []
    assert profile.technologies == []
    assert profile.offerings == []
    assert profile.needs == []
    assert profile.assets == []
    assert profile.initiatives == []
    assert profile.key_contacts == []
    assert profile.cultural_notes == []
    assert profile.impact_metrics == []
    assert profile.goals == []
    assert profile.tags == []


def test_company_profile_validates_nested_objects():
    """Verify nested objects (Location, Capability, Need) parse correctly."""
    payload = {
        "slug": "test-company",
        "name": "Test Company",
        "headquarters": {
            "city": "Austin",
            "region": "TX",
            "country": "USA",
        },
        "offerings": [
            {
                "name": "Test Offering",
                "description": "A test offering",
                "engagement_channels": ["service", "product"],
            }
        ],
        "needs": [
            {
                "name": "Test Need",
                "description": "A test need",
                "urgency": 3,
                "engagement_channels": ["operations"],
            }
        ],
    }
    
    profile = CompanyProfile.from_dict(payload)
    
    # Verify nested objects are parsed correctly
    assert profile.headquarters is not None
    assert profile.headquarters.city == "Austin"
    assert profile.headquarters.region == "TX"
    assert profile.headquarters.country == "USA"
    
    assert len(profile.offerings) == 1
    assert profile.offerings[0].name == "Test Offering"
    assert len(profile.offerings[0].engagement_channels) == 2
    assert EngagementChannel.SERVICE in profile.offerings[0].engagement_channels
    
    assert len(profile.needs) == 1
    assert profile.needs[0].name == "Test Need"
    assert profile.needs[0].urgency == 3
    assert EngagementChannel.OPERATIONS in profile.needs[0].engagement_channels


def test_engagement_channel_from_value_valid():
    """Test EngagementChannel.from_value() with valid values."""
    # Test with exact enum value
    channel1 = EngagementChannel.from_value("product")
    assert channel1 == EngagementChannel.PRODUCT
    
    # Test with uppercase (should be lowercased)
    channel2 = EngagementChannel.from_value("SERVICE")
    assert channel2 == EngagementChannel.SERVICE
    
    # Test with mixed case
    channel3 = EngagementChannel.from_value("Knowledge")
    assert channel3 == EngagementChannel.KNOWLEDGE


def test_location_from_dict_none():
    """Verify Location.from_dict(None) returns None."""
    result = Location.from_dict(None)
    assert result is None


def test_contact_from_dict_minimal():
    """Verify Contact can be created with only name."""
    payload = {
        "name": "John Doe",
    }
    
    contact = Contact.from_dict(payload)
    assert contact.name == "John Doe"
    assert contact.title is None
    assert contact.email is None
    assert contact.phone is None
    assert contact.notes is None


def test_company_profile_vectorize_empty_fields():
    """Verify vectorize() handles empty/None fields gracefully."""
    payload = {
        "slug": "test-company",
        "name": "Test Company",
        # All optional fields missing or empty
    }
    
    profile = CompanyProfile.from_dict(payload)
    vector = profile.vectorize()
    
    # Should return at least the company name (as a single token, lowercased)
    assert len(vector) > 0
    # Name "Test Company" is added as a whole string and lowercased
    assert "test company" in vector
    # Should not crash on None/empty fields
    assert all(isinstance(token, str) for token in vector)
    assert all(len(token) > 0 for token in vector)  # No empty strings


def test_company_profile_plugin_points_plugs():
    """Verify plugin_points() and plugs() return correct lists."""
    payload = {
        "slug": "test-company",
        "name": "Test Company",
        "offerings": [
            {
                "name": "Offering 1",
                "description": "First offering",
            },
            {
                "name": "Offering 2",
                "description": "Second offering",
            },
        ],
        "needs": [
            {
                "name": "Need 1",
                "description": "First need",
            },
        ],
    }
    
    profile = CompanyProfile.from_dict(payload)
    
    plugin_points = profile.plugin_points()
    assert len(plugin_points) == 2
    assert plugin_points[0].name == "Offering 1"
    assert plugin_points[1].name == "Offering 2"
    
    plugs = profile.plugs()
    assert len(plugs) == 1
    assert plugs[0].name == "Need 1"
