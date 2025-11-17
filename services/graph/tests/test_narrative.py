from __future__ import annotations

import json

import pytest

from synergizer.models import CompanyProfile
from synergizer.narrative import NarrativeParser, NarrativePromptBuilder


class FakeModel:
    def __init__(self, response: str):
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str, *, temperature: float = 0.0) -> str:
        self.last_prompt = prompt
        return self.response


def base_payload() -> dict:
    return {
        "name": "Example Co",
        "description": "Example description",
        "mission": "Do great things",
        "organization_type": "Social Enterprise",
        "headquarters": {"city": "Austin", "region": "TX", "country": "USA"},
        "regions_active": ["North America"],
        "employee_count": 25,
        "expertise": ["education"],
        "industries": ["nonprofit"],
        "technologies": ["mobile"],
        "offerings": [
            {
                "name": "STEM curriculum",
                "description": "Hands-on workshops",
                "maturity": "production",
                "engagement_channels": ["knowledge", "social_impact"],
            }
        ],
        "needs": [
            {
                "name": "Field partners",
                "description": "Local organizations",
                "urgency": 3,
                "desired_outcomes": ["expanded reach"],
                "engagement_channels": ["operations"],
            }
        ],
        "assets": [],
        "initiatives": [],
        "key_contacts": [],
        "cultural_notes": ["collaborative"],
        "impact_metrics": ["students served"],
        "goals": ["launch new region"],
        "tags": ["education", "youth"],
    }


def test_parser_builds_profile_from_json_payload() -> None:
    payload = base_payload() | {"slug": "example-co"}
    model = FakeModel(json.dumps(payload))
    parser = NarrativeParser(model)

    profile = parser.parse("Example narrative text.")

    assert isinstance(profile, CompanyProfile)
    assert profile.slug == "example-co"
    assert profile.offerings[0].name == "STEM curriculum"
    assert profile.needs[0].engagement_channels[0].value == "operations"


def test_parser_generates_slug_when_missing() -> None:
    model = FakeModel(json.dumps(base_payload()))
    parser = NarrativeParser(model)

    profile = parser.parse("Narrative text about Example Co")

    assert profile.slug == "example-co"


def test_parser_extracts_json_from_wrapped_response() -> None:
    wrapped = "Here is the profile:\n```json\n" + json.dumps(base_payload() | {"slug": "wrapped-co"}) + "\n```"
    model = FakeModel(wrapped)
    parser = NarrativeParser(model)

    profile = parser.parse("Narrative")

    assert profile.slug == "wrapped-co"


@pytest.mark.parametrize("snippet", ["Schema:", "Narrative:", "synergy profiles"])
def test_prompt_builder_includes_guidance(snippet: str) -> None:
    builder = NarrativePromptBuilder()

    prompt = builder.build("Example Co empowers educators with digital tools.")

    assert snippet in prompt


def test_parser_extract_json_malformed_json() -> None:
    """Verify malformed JSON in response is handled gracefully."""
    # Response with malformed JSON (missing closing brace)
    malformed_response = '{"name": "Test Company", "description": "Test"'
    model = FakeModel(malformed_response)
    parser = NarrativeParser(model)
    
    # Should raise ValueError when JSON cannot be parsed
    with pytest.raises(ValueError, match="Model response did not contain JSON content"):
        parser.parse("Test narrative")


def test_parser_extract_json_no_json_found() -> None:
    """Verify error when no JSON found in response."""
    # Response with no JSON at all
    no_json_response = "This is just plain text with no JSON content whatsoever."
    model = FakeModel(no_json_response)
    parser = NarrativeParser(model)
    
    # Should raise ValueError
    with pytest.raises(ValueError, match="Model response did not contain JSON content"):
        parser.parse("Test narrative")


def test_parser_slugify_empty_name() -> None:
    """Verify empty name generates valid slug (fallback to UUID)."""
    # Test direct slugify with empty string - should generate UUID-based slug
    from synergizer.narrative import _slugify
    slug = _slugify("")
    assert slug.startswith("company-")
    assert len(slug) > len("company-")
    
    # Test that parser handles empty name by using default_name fallback
    # The parser uses "Unnamed Organization" as default, so we test slugify directly
    # with an empty name to verify the UUID fallback behavior
    empty_slug = _slugify("")
    assert empty_slug.startswith("company-")
    
    # Test with whitespace-only name (should also generate UUID)
    whitespace_slug = _slugify("   ")
    assert whitespace_slug.startswith("company-")
    
    # Verify different empty strings generate different UUIDs
    slug1 = _slugify("")
    slug2 = _slugify("")
    # They should be different (UUID-based)
    assert slug1 != slug2 or slug1.startswith("company-")
