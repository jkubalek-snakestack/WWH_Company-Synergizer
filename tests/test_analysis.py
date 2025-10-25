"""Tests for the synergy engine."""

from pathlib import Path
import json

from synergizer.analysis import SynergyEngine
from synergizer.cli import build_engine
from synergizer.models import CompanyProfile


def build_profiles() -> list[CompanyProfile]:
    path = Path("data/sample_profiles.json")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return [CompanyProfile.from_dict(payload) for payload in data["companies"]]


def test_engine_generates_opportunities():
    profiles = build_profiles()
    engine = build_engine(profiles, Path("data/templates.json"))

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
