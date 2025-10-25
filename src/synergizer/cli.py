"""Command line interface for exploring synergies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .analysis import SynergyEngine
from .models import CompanyProfile
from .reporting import OpportunityReport
from .templates import ProfileTemplateLibrary


def load_profiles(path: Path) -> List[CompanyProfile]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return [CompanyProfile.from_dict(item) for item in data["companies"]]


def build_engine(profiles: List[CompanyProfile], templates: Path | None) -> SynergyEngine:
    engine = SynergyEngine()
    if templates:
        library = ProfileTemplateLibrary()
        library.load_from_file(str(templates))
        enriched = []
        for profile in profiles:
            template_name = profile.organization_type or "General"
            if template_name in library.templates:
                enriched.append(
                    library.auto_complete_profile(
                        base=_profile_to_dict(profile),
                        template_name=template_name,
                    )
                )
            else:
                enriched.append(profile)
        profiles = enriched
    engine.register_companies(profiles)
    return engine


def _profile_to_dict(profile: CompanyProfile) -> dict:
    return {
        "slug": profile.slug,
        "name": profile.name,
        "description": profile.description,
        "mission": profile.mission,
        "organization_type": profile.organization_type,
        "headquarters": (
            {
                "city": profile.headquarters.city,
                "region": profile.headquarters.region,
                "country": profile.headquarters.country,
                "latitude": profile.headquarters.latitude,
                "longitude": profile.headquarters.longitude,
            }
            if profile.headquarters
            else None
        ),
        "regions_active": list(profile.regions_active),
        "employee_count": profile.employee_count,
        "expertise": list(profile.expertise),
        "industries": list(profile.industries),
        "technologies": list(profile.technologies),
        "offerings": [
            {
                "name": capability.name,
                "description": capability.description,
                "maturity": capability.maturity,
                "engagement_channels": [channel.value for channel in capability.engagement_channels],
            }
            for capability in profile.offerings
        ],
        "needs": [
            {
                "name": need.name,
                "description": need.description,
                "urgency": need.urgency,
                "desired_outcomes": list(need.desired_outcomes),
                "engagement_channels": [channel.value for channel in need.engagement_channels],
            }
            for need in profile.needs
        ],
        "assets": [asset.__dict__ for asset in profile.assets],
        "initiatives": [initiative.__dict__ for initiative in profile.initiatives],
        "key_contacts": [contact.__dict__ for contact in profile.key_contacts],
        "cultural_notes": list(profile.cultural_notes),
        "impact_metrics": list(profile.impact_metrics),
        "goals": list(profile.goals),
        "tags": list(profile.tags),
    }


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="WWH synergy explorer")
    parser.add_argument("profiles", type=Path, help="Path to company profiles data (JSON)")
    parser.add_argument(
        "--templates", type=Path, default=None, help="Optional templates configuration (JSON)"
    )
    parser.add_argument(
        "--report", type=Path, default=None, help="Optional output file for the report"
    )
    args = parser.parse_args(argv)

    profiles = load_profiles(args.profiles)
    engine = build_engine(profiles, args.templates)
    opportunities = engine.build_opportunities()
    report = OpportunityReport(opportunities)

    summary = report.executive_summary()
    if args.report:
        with open(args.report, "w", encoding="utf-8") as handle:
            handle.write(summary)
            handle.write("\n\n")
            for section in report.detail_sections():
                handle.write(f"# {section.title}\n{section.body}\n\n")
    else:
        print(summary)
        print()
        for section in report.detail_sections():
            print(f"# {section.title}\n{section.body}\n")


if __name__ == "__main__":  # pragma: no cover
    main()
