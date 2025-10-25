"""Core domain models for the synergizer platform using standard library types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, Iterable, List, Optional


class EngagementChannel(str, Enum):
    """Channels for coordination across companies."""

    PRODUCT = "product"
    SERVICE = "service"
    KNOWLEDGE = "knowledge"
    SOCIAL_IMPACT = "social_impact"
    FUNDING = "funding"
    TALENT = "talent"
    TECHNOLOGY = "technology"
    OPERATIONS = "operations"
    SALES = "sales"
    RESEARCH = "research"

    @staticmethod
    def from_value(value: str) -> "EngagementChannel":
        try:
            return EngagementChannel(value)
        except ValueError:
            return EngagementChannel(value.lower())


@dataclass
class Contact:
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

    @staticmethod
    def from_dict(payload: Dict) -> "Contact":
        return Contact(**payload)


@dataclass
class Location:
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @staticmethod
    def from_dict(payload: Optional[Dict]) -> "Location | None":
        if payload is None:
            return None
        return Location(**payload)


@dataclass
class Asset:
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None

    @staticmethod
    def from_dict(payload: Dict) -> "Asset":
        return Asset(**payload)


@dataclass
class Initiative:
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    outcomes: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(payload: Dict) -> "Initiative":
        return Initiative(**payload)


@dataclass
class Capability:
    name: str
    description: Optional[str] = None
    maturity: Optional[str] = None
    engagement_channels: List[EngagementChannel] = field(default_factory=list)

    @staticmethod
    def from_dict(payload: Dict) -> "Capability":
        channels = [EngagementChannel(channel) for channel in payload.get("engagement_channels", [])]
        return Capability(
            name=payload["name"],
            description=payload.get("description"),
            maturity=payload.get("maturity"),
            engagement_channels=channels,
        )


@dataclass
class Need:
    name: str
    description: Optional[str] = None
    urgency: Optional[int] = None
    desired_outcomes: List[str] = field(default_factory=list)
    engagement_channels: List[EngagementChannel] = field(default_factory=list)

    @staticmethod
    def from_dict(payload: Dict) -> "Need":
        channels = [EngagementChannel(channel) for channel in payload.get("engagement_channels", [])]
        return Need(
            name=payload["name"],
            description=payload.get("description"),
            urgency=payload.get("urgency"),
            desired_outcomes=payload.get("desired_outcomes", []),
            engagement_channels=channels,
        )


@dataclass
class CompanyProfile:
    slug: str
    name: str
    description: Optional[str] = None
    mission: Optional[str] = None
    organization_type: Optional[str] = None
    headquarters: Optional[Location] = None
    regions_active: List[str] = field(default_factory=list)
    employee_count: Optional[int] = None
    expertise: List[str] = field(default_factory=list)
    industries: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    offerings: List[Capability] = field(default_factory=list)
    needs: List[Need] = field(default_factory=list)
    assets: List[Asset] = field(default_factory=list)
    initiatives: List[Initiative] = field(default_factory=list)
    key_contacts: List[Contact] = field(default_factory=list)
    cultural_notes: List[str] = field(default_factory=list)
    impact_metrics: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(payload: Dict) -> "CompanyProfile":
        return CompanyProfile(
            slug=payload["slug"],
            name=payload["name"],
            description=payload.get("description"),
            mission=payload.get("mission"),
            organization_type=payload.get("organization_type"),
            headquarters=Location.from_dict(payload.get("headquarters")),
            regions_active=payload.get("regions_active", []),
            employee_count=payload.get("employee_count"),
            expertise=payload.get("expertise", []),
            industries=payload.get("industries", []),
            technologies=payload.get("technologies", []),
            offerings=[Capability.from_dict(item) for item in payload.get("offerings", [])],
            needs=[Need.from_dict(item) for item in payload.get("needs", [])],
            assets=[Asset.from_dict(item) for item in payload.get("assets", [])],
            initiatives=[Initiative.from_dict(item) for item in payload.get("initiatives", [])],
            key_contacts=[Contact.from_dict(item) for item in payload.get("key_contacts", [])],
            cultural_notes=payload.get("cultural_notes", []),
            impact_metrics=payload.get("impact_metrics", []),
            goals=payload.get("goals", []),
            tags=payload.get("tags", []),
        )

    def plugin_points(self) -> List[Capability]:
        return list(self.offerings)

    def plugs(self) -> List[Need]:
        return list(self.needs)

    def vectorize(self) -> List[str]:
        vector: List[str] = [
            self.name,
            *(self.mission or "").split(),
            *self.expertise,
            *self.industries,
            *self.technologies,
            *self.tags,
        ]
        for capability in self.offerings:
            vector.extend([capability.name, capability.description or ""])
        for need in self.needs:
            vector.extend([need.name, need.description or ""])
        return [token.lower() for token in vector if token]


@dataclass
class SynergyMatch:
    source_company: str
    target_company: str
    description: str
    weight: float
    engagement_channels: List[EngagementChannel] = field(default_factory=list)


@dataclass
class SynergyOpportunity:
    name: str
    summary: str
    participants: List[str]
    engagement_channels: List[EngagementChannel] = field(default_factory=list)
    rationale: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    priority: Optional[str] = None
    supporting_matches: List[SynergyMatch] = field(default_factory=list)


@dataclass
class ProfileTemplate:
    name: str
    description: str
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(payload: Dict) -> "ProfileTemplate":
        return ProfileTemplate(**payload)


@dataclass
class TieringRule:
    name: str
    description: str
    criteria: List[str]

    @staticmethod
    def from_dict(payload: Dict) -> "TieringRule":
        return TieringRule(**payload)

    def applies_to(self, company: CompanyProfile) -> bool:
        haystack = " ".join(company.vectorize())
        return all(term.lower() in haystack for term in self.criteria)


def normalize_terms(terms: Iterable[str]) -> List[str]:
    return sorted({term.lower().strip() for term in terms if term})
