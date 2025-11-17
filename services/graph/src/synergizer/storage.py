"""In-memory graph store using standard library data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Tuple

from .models import CompanyProfile, EngagementChannel, SynergyMatch
from .utils import slugify


@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float
    label: str
    rationale: str
    engagement_channels: List[EngagementChannel]


class SynergyGraph:
    """Directed multigraph capturing how companies can support one another."""

    def __init__(self) -> None:
        self._profiles: Dict[str, CompanyProfile] = {}
        self._edges: Dict[str, List[GraphEdge]] = {}

    def upsert_company(self, company: CompanyProfile) -> None:
        slug = company.slug or slugify(company.name)
        company.slug = slug
        self._profiles[slug] = company
        self._edges.setdefault(slug, [])

    def remove_company(self, slug: str) -> None:
        self._profiles.pop(slug, None)
        self._edges.pop(slug, None)
        for edges in self._edges.values():
            edges[:] = [edge for edge in edges if edge.target != slug]

    def link_companies(
        self,
        source_slug: str,
        target_slug: str,
        weight: float,
        label: str,
        rationale: str,
        engagement_channels: List[EngagementChannel] | None = None,
    ) -> None:
        engagement_channels = engagement_channels or []
        edge = GraphEdge(
            source=source_slug,
            target=target_slug,
            weight=weight,
            label=label,
            rationale=rationale,
            engagement_channels=list(engagement_channels),
        )
        self._edges.setdefault(source_slug, []).append(edge)

    def company(self, slug: str) -> CompanyProfile:
        return self._profiles[slug]

    def companies(self) -> Iterator[CompanyProfile]:
        return iter(self._profiles.values())

    def edges(self) -> Iterator[GraphEdge]:
        for edges in self._edges.values():
            for edge in edges:
                yield edge

    def adjacency_matrix(self) -> Dict[Tuple[str, str], float]:
        matrix: Dict[Tuple[str, str], float] = {}
        for edges in self._edges.values():
            for edge in edges:
                matrix[(edge.source, edge.target)] = edge.weight
        return matrix

    def matches_for(self, slug: str) -> List[SynergyMatch]:
        return [
            SynergyMatch(
                source_company=edge.source,
                target_company=edge.target,
                description=edge.label,
                weight=edge.weight,
                engagement_channels=edge.engagement_channels,
            )
            for edge in self._edges.get(slug, [])
        ]

    def ingest(self, companies: Iterable[CompanyProfile]) -> None:
        for company in companies:
            self.upsert_company(company)
