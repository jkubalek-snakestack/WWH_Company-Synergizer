"""Tools to craft executive-ready opportunity summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .models import CompanyProfile, SynergyOpportunity


@dataclass
class ReportSection:
    title: str
    body: str


class OpportunityReport:
    """Formats opportunity outputs for dashboards, PDFs, or slide decks."""

    def __init__(self, opportunities: Iterable[SynergyOpportunity]):
        self.opportunities = list(opportunities)

    def executive_summary(self, limit: int = 5) -> str:
        top = self.opportunities[:limit]
        lines = [
            "Top synergy opportunities:",
            *[
                f"- {opp.name} ({opp.priority or 'Emerging'}): {opp.summary}"
                for opp in top
            ],
        ]
        return "\n".join(lines)

    def detail_sections(self) -> List[ReportSection]:
        sections: List[ReportSection] = []
        for opportunity in self.opportunities:
            body_lines = [
                f"Participants: {', '.join(opportunity.participants)}",
                f"Priority: {opportunity.priority or 'Emerging'}",
                f"Engagement channels: {', '.join(channel.value for channel in opportunity.engagement_channels)}",
                "Rationale:",
                *[f"  • {line}" for line in opportunity.rationale],
                "Expected outcomes:",
                *[f"  • {line}" for line in opportunity.expected_outcomes],
            ]
            sections.append(
                ReportSection(
                    title=opportunity.name,
                    body="\n".join(body_lines),
                )
            )
        return sections

    @staticmethod
    def highlight_company(company: CompanyProfile) -> ReportSection:
        body_lines = [
            company.description or "",
            f"Mission: {company.mission or 'n/a'}",
            f"Primary industries: {', '.join(company.industries) or 'n/a'}",
            f"Key expertise: {', '.join(company.expertise) or 'n/a'}",
            f"Plugin points: {', '.join(cap.name for cap in company.plugin_points()) or 'n/a'}",
            f"Plugs: {', '.join(need.name for need in company.plugs()) or 'n/a'}",
        ]
        return ReportSection(title=company.name, body="\n".join(body_lines))
