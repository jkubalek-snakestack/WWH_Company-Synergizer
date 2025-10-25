"""Synergy reasoning engine."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Dict, Iterable, List, Sequence

from .models import (
    CompanyProfile,
    EngagementChannel,
    Need,
    SynergyMatch,
    SynergyOpportunity,
)
from .storage import SynergyGraph


class SynergyEngine:
    """Searches across profiles and proposes creative collaboration concepts."""

    def __init__(self, graph: SynergyGraph | None = None) -> None:
        self.graph = graph or SynergyGraph()

    def register_companies(self, companies: Iterable[CompanyProfile]) -> None:
        self.graph.ingest(companies)
        self._index_terms()

    def _index_terms(self) -> None:
        self._term_index: Dict[str, List[str]] = defaultdict(list)
        for company in self.graph.companies():
            for token in company.vectorize():
                self._term_index[token].append(company.slug)

    def profile(self, slug: str) -> CompanyProfile:
        return self.graph.company(slug)

    def find_complementary_pairs(self) -> List[SynergyMatch]:
        matches: List[SynergyMatch] = []
        companies = list(self.graph.companies())
        for a, b in combinations(companies, 2):
            match_ab = self._match_companies(a, b)
            if match_ab:
                matches.extend(match_ab)
            match_ba = self._match_companies(b, a)
            if match_ba:
                matches.extend(match_ba)
        return matches

    def _match_companies(
        self, source: CompanyProfile, target: CompanyProfile
    ) -> List[SynergyMatch]:
        matches: List[SynergyMatch] = []
        for need in target.needs:
            reason = self._reason_for_need(source, target, need)
            if reason:
                matches.append(reason)
        return matches

    def _reason_for_need(
        self, source: CompanyProfile, target: CompanyProfile, need: Need
    ) -> SynergyMatch | None:
        offering_overlap = [
            capability
            for capability in source.offerings
            if _term_overlap(capability, need)
        ]
        if offering_overlap:
            channels = need.engagement_channels or [EngagementChannel.SERVICE]
            description = (
                f"{source.name} can support {target.name}'s need '{need.name}' via "
                f"{', '.join(cap.name for cap in offering_overlap)}"
            )
            weight = 0.5 + 0.1 * len(offering_overlap)
            if need.urgency:
                weight += min(need.urgency, 5) * 0.1
            return SynergyMatch(
                source_company=source.slug,
                target_company=target.slug,
                description=description,
                weight=weight,
                engagement_channels=channels,
            )
        vector_overlap = set(source.vectorize()) & set(target.vectorize())
        if vector_overlap:
            return SynergyMatch(
                source_company=source.slug,
                target_company=target.slug,
                description=(
                    f"Shared focus on {', '.join(sorted(vector_overlap))} "
                    f"could unlock joint programs"
                ),
                weight=0.3 + 0.02 * len(vector_overlap),
                engagement_channels=[EngagementChannel.KNOWLEDGE],
            )
        return None

    def build_opportunities(self) -> List[SynergyOpportunity]:
        pair_matches = self.find_complementary_pairs()
        grouped: Dict[frozenset[str], List[SynergyMatch]] = defaultdict(list)
        for match in pair_matches:
            key = frozenset([match.source_company, match.target_company])
            grouped[key].append(match)

        opportunities: List[SynergyOpportunity] = []
        for participants, matches in grouped.items():
            participants_list = sorted(participants)
            summary = self._compose_summary(participants_list, matches)
            opportunities.append(
                SynergyOpportunity(
                    name=f"{participants_list[0]}-{participants_list[-1]} strategic lane",
                    summary=summary,
                    participants=participants_list,
                    engagement_channels=self._collect_channels(matches),
                    rationale=[match.description for match in matches],
                    expected_outcomes=self._expected_outcomes(matches),
                    priority=self._prioritize(matches),
                    supporting_matches=matches,
                )
            )

        opportunities.extend(self._generate_triads(pair_matches))
        return sorted(
            opportunities,
            key=lambda opp: self._priority_score(opp.priority),
            reverse=True,
        )

    def _generate_triads(self, matches: Sequence[SynergyMatch]) -> List[SynergyOpportunity]:
        companies = list(self.graph.companies())
        opportunities: List[SynergyOpportunity] = []
        match_lookup: Dict[frozenset[str], List[SynergyMatch]] = defaultdict(list)
        for match in matches:
            key = frozenset([match.source_company, match.target_company])
            match_lookup[key].append(match)

        for trio in combinations(companies, 3):
            slugs = [company.slug for company in trio]
            pair_keys = [
                frozenset([slugs[i], slugs[j]]) for i, j in combinations(range(3), 2)
            ]
            supporting = [match_lookup[key] for key in pair_keys if key in match_lookup]
            if len(supporting) < 2:
                continue

            participants = sorted(slugs)
            names = [self.profile(slug).name for slug in participants]
            rationale = [
                match.description for bucket in supporting for match in bucket
            ]
            channels = sorted(
                {
                    channel
                    for bucket in supporting
                    for match in bucket
                    for channel in match.engagement_channels or []
                },
                key=lambda channel: channel.value,
            )
            summary = (
                f"Triad synergy linking {names[0]}, {names[1]}, and {names[2]}"
                if len(names) == 3
                else "Triad synergy"
            )
            shared_terms = self._shared_terms_for_trio(trio)
            if shared_terms:
                summary += f" around {', '.join(sorted(shared_terms))[:100]}"
            total_weight = sum(match.weight for bucket in supporting for match in bucket)
            priority = "High" if total_weight >= 4 else "Medium"

            opportunities.append(
                SynergyOpportunity(
                    name="-".join(participants),
                    summary=summary,
                    participants=participants,
                    engagement_channels=channels or [EngagementChannel.KNOWLEDGE],
                    rationale=rationale,
                    expected_outcomes=self._expected_outcomes(
                        [match for bucket in supporting for match in bucket]
                    ),
                    priority=priority,
                )
            )
        return opportunities

    @staticmethod
    def _shared_terms_for_trio(trio: Sequence[CompanyProfile]) -> List[str]:
        tokens = [set(company.vectorize()) for company in trio]
        shared = set.intersection(*tokens) if tokens else set()
        if shared:
            return sorted(shared)
        # fallback: highlight the most common tokens across the trio
        counter: Dict[str, int] = defaultdict(int)
        for bucket in tokens:
            for token in bucket:
                counter[token] += 1
        frequent = [term for term, count in counter.items() if count >= 2]
        return sorted(frequent)[:5]

    def _compose_summary(
        self, participants: Sequence[str], matches: Sequence[SynergyMatch]
    ) -> str:
        if not matches:
            return "Exploratory collaboration"
        dominant_channels = ", ".join(
            sorted({channel.value for match in matches for channel in match.engagement_channels})
        )
        return (
            f"Collaboration between {', '.join(participants)} across {dominant_channels}"
        )

    def _collect_channels(
        self, matches: Sequence[SynergyMatch]
    ) -> List[EngagementChannel]:
        channels = {
            channel
            for match in matches
            for channel in (match.engagement_channels or [])
        }
        return sorted(channels, key=lambda channel: channel.value)

    def _expected_outcomes(
        self, matches: Sequence[SynergyMatch]
    ) -> List[str]:
        outcomes = []
        for match in matches:
            if "impact" in match.description.lower():
                outcomes.append("Amplify social impact with shared channels")
            if "technology" in match.description.lower():
                outcomes.append("Integrate technology stacks for scalable delivery")
            if "talent" in match.description.lower():
                outcomes.append("Talent exchange and mentorship pipelines")
        if not outcomes:
            outcomes.append("Joint planning workshop to scope initiatives")
        return sorted(set(outcomes))

    def _prioritize(self, matches: Sequence[SynergyMatch]) -> str:
        total = sum(match.weight for match in matches)
        if total >= 1.8:
            return "High"
        if total >= 1:
            return "Medium"
        return "Emerging"

    @staticmethod
    def _priority_score(priority: str | None) -> int:
        mapping = {"High": 3, "Medium": 2, "Emerging": 1, None: 0, "": 0}
        return mapping.get(priority, 0)


def _term_overlap(capability, need: Need) -> bool:
    capability_terms = {
        token.lower()
        for phrase in [capability.name, capability.description or ""]
        for token in phrase.split()
        if token
    }
    need_terms = {
        token.lower()
        for phrase in [need.name, need.description or ""]
        for token in phrase.split()
        if token
    }
    return bool(capability_terms & need_terms)
