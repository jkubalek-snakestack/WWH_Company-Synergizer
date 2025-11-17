"""Tests for the synergizer models."""

from __future__ import annotations

import pytest

from synergizer.models import (
    Capability,
    CompanyProfile,
    EngagementChannel,
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

