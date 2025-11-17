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


def test_engine_find_complementary_pairs_empty():
    """Verify find_complementary_pairs() returns empty list when no companies."""
    engine = SynergyEngine()
    
    pairs = engine.find_complementary_pairs()
    
    assert isinstance(pairs, list)
    assert len(pairs) == 0


def test_engine_find_complementary_pairs_single_company():
    """Verify find_complementary_pairs() returns empty list with single company."""
    engine = SynergyEngine()
    
    company = CompanyProfile.from_dict({
        "slug": "single-company",
        "name": "Single Company",
        "description": "A single company",
    })
    
    engine.register_companies([company])
    
    pairs = engine.find_complementary_pairs()
    
    # Need at least 2 companies to form pairs
    assert isinstance(pairs, list)
    assert len(pairs) == 0


def test_engine_build_opportunities_no_matches():
    """Verify build_opportunities() returns empty list when no matches exist."""
    engine = SynergyEngine()
    
    # Create two companies with no complementary needs/offerings
    company1 = CompanyProfile.from_dict({
        "slug": "company-1",
        "name": "Company One",
        "offerings": [],
        "needs": [],
    })
    company2 = CompanyProfile.from_dict({
        "slug": "company-2",
        "name": "Company Two",
        "offerings": [],
        "needs": [],
    })
    
    engine.register_companies([company1, company2])
    
    opportunities = engine.build_opportunities()
    
    # Should return empty list, not crash
    assert isinstance(opportunities, list)
    assert len(opportunities) == 0


def test_engine_term_indexing():
    """Verify _index_terms() correctly indexes company terms."""
    engine = SynergyEngine()
    
    company1 = CompanyProfile.from_dict({
        "slug": "tech-company",
        "name": "Tech Company",
        "expertise": ["technology", "software"],
        "industries": ["tech"],
    })
    company2 = CompanyProfile.from_dict({
        "slug": "education-company",
        "name": "Education Company",
        "expertise": ["education", "learning"],
        "industries": ["education"],
    })
    
    engine.register_companies([company1, company2])
    
    # Verify term index was created
    assert hasattr(engine, "_term_index")
    assert isinstance(engine._term_index, dict)
    
    # Verify some terms are indexed
    assert len(engine._term_index) > 0
    
    # Verify companies are indexed by their terms
    # "tech" should appear in index
    tech_terms = [term for term in engine._term_index.keys() if "tech" in term.lower()]
    assert len(tech_terms) > 0
    
    # Verify companies appear in term index
    for term, slugs in engine._term_index.items():
        assert isinstance(slugs, list)
        assert all(slug in ["tech-company", "education-company"] for slug in slugs)


def test_engine_triad_generation_requires_two_pairs():
    """Verify triad generation requires at least 2 pairs of matches."""
    engine = SynergyEngine()
    
    # Create three companies
    company1 = CompanyProfile.from_dict({
        "slug": "company-1",
        "name": "Company One",
        "offerings": [{"name": "Service A", "description": "Service A description"}],
        "needs": [],
    })
    company2 = CompanyProfile.from_dict({
        "slug": "company-2",
        "name": "Company Two",
        "offerings": [],
        "needs": [{"name": "Service A", "description": "Service A description", "urgency": 3}],
    })
    company3 = CompanyProfile.from_dict({
        "slug": "company-3",
        "name": "Company Three",
        "offerings": [],
        "needs": [],
    })
    
    engine.register_companies([company1, company2, company3])
    
    opportunities = engine.build_opportunities()
    
    # Should have pair opportunities but no triads (only 1 pair: company1->company2)
    # Triads require at least 2 pairs among the 3 companies
    pair_opportunities = [opp for opp in opportunities if len(opp.participants) == 2]
    triad_opportunities = [opp for opp in opportunities if len(opp.participants) == 3]
    
    # Should have at least one pair opportunity
    assert len(pair_opportunities) > 0
    
    # Should have no triads (only 1 pair exists, need 2+ pairs for triad)
    assert len(triad_opportunities) == 0


def test_engine_priority_scoring():
    """Verify priority scoring returns correct values."""
    from synergizer.analysis import SynergyEngine
    
    # Test static method
    assert SynergyEngine._priority_score("High") == 3
    assert SynergyEngine._priority_score("Medium") == 2
    assert SynergyEngine._priority_score("Emerging") == 1
    assert SynergyEngine._priority_score(None) == 0
    assert SynergyEngine._priority_score("") == 0
    
    # Test with actual opportunities
    engine = SynergyEngine()
    profiles = build_profiles()
    engine.register_companies(profiles)
    
    opportunities = engine.build_opportunities()
    
    # Verify opportunities are sorted by priority (High first)
    if len(opportunities) > 1:
        priorities = [opp.priority for opp in opportunities]
        # High priority should come before Medium/Emerging
        high_indices = [i for i, p in enumerate(priorities) if p == "High"]
        medium_indices = [i for i, p in enumerate(priorities) if p == "Medium"]
        emerging_indices = [i for i, p in enumerate(priorities) if p == "Emerging"]
        
        # If we have High and Medium, High should come first
        if high_indices and medium_indices:
            assert min(high_indices) < max(medium_indices)


def test_engine_expected_outcomes_generation():
    """Verify expected_outcomes() generates appropriate outcomes."""
    from synergizer.models import SynergyMatch, EngagementChannel
    
    engine = SynergyEngine()
    
    # Create matches with different descriptions to trigger different outcomes
    matches = [
        SynergyMatch(
            source_company="company-1",
            target_company="company-2",
            description="Impact-focused collaboration",
            weight=0.8,
            engagement_channels=[EngagementChannel.SOCIAL_IMPACT],
        ),
        SynergyMatch(
            source_company="company-2",
            target_company="company-3",
            description="Technology integration opportunity",
            weight=0.7,
            engagement_channels=[EngagementChannel.TECHNOLOGY],
        ),
    ]
    
    outcomes = engine._expected_outcomes(matches)
    
    # Should generate outcomes based on match descriptions
    assert isinstance(outcomes, list)
    assert len(outcomes) > 0
    
    # Should contain impact-related outcome
    impact_outcomes = [outcome for outcome in outcomes if "impact" in outcome.lower()]
    assert len(impact_outcomes) > 0
    
    # Should contain technology-related outcome
    tech_outcomes = [outcome for outcome in outcomes if "technology" in outcome.lower()]
    assert len(tech_outcomes) > 0
