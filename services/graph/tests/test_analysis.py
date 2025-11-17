"""Tests for the synergy engine."""

from pathlib import Path
import json

import pytest

from synergizer.analysis import SynergyEngine
from synergizer.cli import build_engine
from synergizer.models import CompanyProfile


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def build_profiles() -> list[CompanyProfile]:
    path = DATA_DIR / "sample_profiles.json"
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return [CompanyProfile.from_dict(payload) for payload in data["companies"]]


def test_engine_generates_opportunities():
    profiles = build_profiles()
    engine = build_engine(profiles, DATA_DIR / "templates.json")

    opportunities = engine.build_opportunities()

    assert opportunities, "Expected at least one opportunity"
    participant_sets = {tuple(sorted(opportunity.participants)) for opportunity in opportunities}
    assert ("company-a", "company-b") in participant_sets
    assert any("triad" in opportunity.summary.lower() for opportunity in opportunities)


def test_high_priority_opportunities_present():
    profiles = build_profiles()
    engine = SynergyEngine()
    engine.register_companies(profiles)

    opportunities = engine.build_opportunities()
    high_priority = [opp for opp in opportunities if opp.priority == "High"]

    assert high_priority, "Expected high priority opportunities for urgent needs"
    for opp in high_priority:
        assert opp.expected_outcomes, "High priority items should propose outcomes"
        assert opp.summary, "High priority opportunities must include summaries"


def test_engine_register_companies_duplicate_slugs():
    """Verify duplicate slugs are handled explicitly (overwrite behavior)."""
    from synergizer.models import CompanyProfile
    
    # Create two companies with the same slug
    company1 = CompanyProfile.from_dict({
        "slug": "duplicate-company",
        "name": "First Company",
        "description": "First description",
    })
    company2 = CompanyProfile.from_dict({
        "slug": "duplicate-company",
        "name": "Second Company",
        "description": "Second description",
    })
    
    engine = SynergyEngine()
    engine.register_companies([company1, company2])
    
    # The graph should only contain one company (last one overwrites)
    companies = list(engine.graph.companies())
    assert len(companies) == 1
    
    # The registered company should be the second one (last registered)
    registered = engine.graph.company("duplicate-company")
    assert registered.name == "Second Company"
    assert registered.description == "Second description"


def test_engine_profile_missing_company():
    """Verify accessing a missing company raises KeyError."""
    engine = SynergyEngine()
    
    # Register some companies
    profiles = build_profiles()
    engine.register_companies(profiles)
    
    # Try to access a non-existent company
    with pytest.raises(KeyError):
        engine.profile("non-existent-company")
    
    # Verify the error is clear
    try:
        engine.profile("missing-slug")
    except KeyError as e:
        assert "missing-slug" in str(e) or "missing-slug" in repr(e)
