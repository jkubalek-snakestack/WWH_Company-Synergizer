"""In-memory orchestration layer for the synergy FastAPI service."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field

from synergizer.analysis import SynergyEngine
from synergizer.models import (
    Capability,
    CompanyProfile,
    EngagementChannel,
    Need,
)


class Visibility(str, Enum):
    PUBLIC = "PUBLIC"
    PARTNER = "PARTNER"
    PRIVATE = "PRIVATE"


class Urgency(str, Enum):
    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


class Capacity(str, Enum):
    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


@dataclass
class OpportunityRecord:
    """Serializable representation of an opportunity."""

    payload: Dict[str, Any]
    status: str = "OPEN"


class CompanyInput(BaseModel):
    id: str
    orgId: str
    slug: Optional[str] = None
    name: str
    region: Optional[str] = None
    mission: Optional[str] = None
    wwhKeys: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    visibility: Visibility = Visibility.PARTNER


class NeedInput(BaseModel):
    id: str
    companyId: str
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    urgency: Urgency = Urgency.MED
    visibility: Visibility = Visibility.PARTNER


class OfferInput(BaseModel):
    id: str
    companyId: str
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    capacity: Capacity = Capacity.MED
    visibility: Visibility = Visibility.PARTNER


class ContactInput(BaseModel):
    id: str
    companyId: str
    name: str
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    privacyLevel: Visibility = Visibility.PRIVATE


class DatasetPayload(BaseModel):
    companies: List[CompanyInput]
    needs: List[NeedInput] = Field(default_factory=list)
    offers: List[OfferInput] = Field(default_factory=list)
    contacts: List[ContactInput] = Field(default_factory=list)


class PlaybookRequest(BaseModel):
    opportunity: Dict[str, Any]
    adjustments: Dict[str, Any] | None = None


class GraphEngine:
    """Caches synergy results and exposes filtering helpers."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._companies: Dict[str, CompanyInput] = {}
        self._company_by_slug: Dict[str, CompanyInput] = {}
        self._needs: Dict[str, List[NeedInput]] = {}
        self._offers: Dict[str, List[OfferInput]] = {}
        self._contacts: Dict[str, List[ContactInput]] = {}
        self._opportunities: Dict[str, OpportunityRecord] = {}
        self._engine = SynergyEngine()

    def recompute(self, dataset: DatasetPayload) -> Dict[str, int]:
        """Rebuild the in-memory graph from a normalized dataset."""

        companies = list(dataset.companies)
        needs = self._index_by_company(dataset.needs)
        offers = self._index_by_company(dataset.offers)
        contacts = self._index_by_company(dataset.contacts)

        profiles = [
            self._to_profile(company, needs.get(company.id, []), offers.get(company.id, []))
            for company in companies
        ]

        engine = SynergyEngine()
        engine.register_companies(profiles)
        opportunities = self._build_records(engine, companies)

        with self._lock:
            self._engine = engine
            self._companies = {company.id: company for company in companies}
            self._company_by_slug = {
                self._slug_for(company): company for company in companies
            }
            self._needs = needs
            self._offers = offers
            self._contacts = contacts
            self._opportunities = opportunities

        return {
            "companies": len(companies),
            "needs": len(dataset.needs),
            "offers": len(dataset.offers),
            "contacts": len(dataset.contacts),
            "opportunities": len(opportunities),
        }

    def opportunities(
        self,
        *,
        org_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Return cached opportunities with optional filters."""

        with self._lock:
            items = list(self._opportunities.values())

        filtered: List[Dict[str, Any]] = []
        for record in items:
            payload = dict(record.payload)
            payload["status"] = record.status
            if status and record.status.lower() != status.lower():
                continue
            if org_id and org_id not in payload.get("orgIds", []):
                continue
            if company_id and company_id not in payload.get("companyIds", []):
                continue
            filtered.append(payload)

        filtered.sort(key=lambda item: item.get("score", 0), reverse=True)
        return filtered

    def playbook(self, request: PlaybookRequest) -> Dict[str, Any]:
        """Generate a structured playbook for the provided opportunity."""

        base = self._resolve_opportunity(request.opportunity)
        adjustments = request.adjustments or {}
        participants = base.get("participants", [])
        actor_entries = adjustments.get("actors") or self._default_actor_entries(participants)
        wwh_alignment = adjustments.get("wwh_alignment") or self._aggregate_keys(participants)

        summary = adjustments.get("summary") or base.get("summary") or base.get("name", "")
        rationale = base.get("breakdown", {}).get("rationale", [])
        matches = base.get("breakdown", {}).get("supporting_matches", [])

        sections = {
            "summary": summary,
            "actors": actor_entries,
            "angles": adjustments.get("angles")
            or base.get("breakdown", {}).get("engagement_channels", []),
            "steps": adjustments.get("steps")
            or self._default_steps(participants, rationale),
            "timeline": adjustments.get("timeline") or self._default_timeline(),
            "risks": adjustments.get("risks") or self._default_risks(participants),
            "collateral": adjustments.get("collateral") or self._default_collateral(matches),
            "wwh_alignment": wwh_alignment,
        }

        return {
            "summary": summary,
            "sections": sections,
        }

    def _resolve_opportunity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        identifier = payload.get("id")
        if identifier:
            with self._lock:
                record = self._opportunities.get(identifier)
            if record:
                result = dict(record.payload)
                result["status"] = record.status
                return result
        return payload

    def _default_actor_entries(self, participants: Iterable[str]) -> List[Dict[str, Any]]:
        actors: List[Dict[str, Any]] = []
        for slug in participants:
            company = self._company_by_slug.get(slug)
            if not company:
                continue
            actors.append(
                {
                    "companyId": company.id,
                    "slug": self._slug_for(company),
                    "name": company.name,
                    "orgId": company.orgId,
                    "visibility": company.visibility,
                }
            )
        return actors

    def _aggregate_keys(self, participants: Iterable[str]) -> List[str]:
        keys: List[str] = []
        for slug in participants:
            company = self._company_by_slug.get(slug)
            if not company:
                continue
            keys.extend(company.wwhKeys)
        return sorted({key for key in keys if key})

    @staticmethod
    def _default_steps(participants: Iterable[str], rationale: Iterable[str]) -> List[Dict[str, Any]]:
        names = ", ".join(participants)
        steps = [
            {
                "title": "Alignment Workshop",
                "detail": f"Gather {names} to confirm objectives and success metrics.",
            }
        ]
        for index, reason in enumerate(rationale, start=1):
            steps.append({"title": f"Opportunity Track {index}", "detail": reason})
        return steps

    @staticmethod
    def _default_timeline() -> List[Dict[str, Any]]:
        return [
            {"phase": "0-30 days", "focus": "Discovery", "actions": ["Kickoff session", "Map shared assets"]},
            {"phase": "30-90 days", "focus": "Pilot", "actions": ["Launch joint pilot", "Collect impact data"]},
        ]

    @staticmethod
    def _default_risks(participants: Iterable[str]) -> List[str]:
        names = list(participants)
        if len(names) >= 2:
            return [f"Alignment risk between {names[0]} and {names[1]} on delivery approach."]
        if names:
            return [f"Resourcing risk for {names[0]} if capacity shifts."]
        return ["Ensure clear ownership before execution."]

    @staticmethod
    def _default_collateral(matches: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        collateral: List[Dict[str, Any]] = []
        for match in matches:
            collateral.append(
                {
                    "title": match.get("description", "Insight"),
                    "source": match.get("source"),
                    "target": match.get("target"),
                }
            )
        return collateral

    def _index_by_company(self, items: Iterable[Any]) -> Dict[str, List[Any]]:
        indexed: Dict[str, List[Any]] = {}
        for item in items:
            bucket = indexed.setdefault(item.companyId, [])
            bucket.append(item)
        return indexed

    def _to_profile(
        self,
        company: CompanyInput,
        needs: Iterable[NeedInput],
        offers: Iterable[OfferInput],
    ) -> CompanyProfile:
        tags = sorted({*company.capabilities, *company.wwhKeys})
        profile = CompanyProfile(
            slug=self._slug_for(company),
            name=company.name,
            description=None,
            mission=company.mission,
            organization_type=None,
            headquarters=None,
            regions_active=[company.region] if company.region else [],
            employee_count=None,
            expertise=company.capabilities,
            industries=[],
            technologies=[],
            offerings=[self._to_capability(offer) for offer in offers],
            needs=[self._to_need(need) for need in needs],
            assets=[],
            initiatives=[],
            key_contacts=[],
            cultural_notes=[],
            impact_metrics=[],
            goals=[],
            tags=tags,
        )
        return profile

    def _build_records(
        self, engine: SynergyEngine, companies: Iterable[CompanyInput]
    ) -> Dict[str, OpportunityRecord]:
        opportunities: Dict[str, OpportunityRecord] = {}
        org_lookup = {self._slug_for(company): company.orgId for company in companies}
        id_lookup = {self._slug_for(company): company.id for company in companies}
        key_lookup = {self._slug_for(company): company.wwhKeys for company in companies}

        for opportunity in engine.build_opportunities():
            matches = [
                {
                    "source": match.source_company,
                    "target": match.target_company,
                    "description": match.description,
                    "weight": match.weight,
                    "engagement_channels": [channel.value for channel in match.engagement_channels],
                }
                for match in opportunity.supporting_matches
            ]
            rationale = opportunity.rationale or [match["description"] for match in matches]
            engagement_channels = [channel.value for channel in opportunity.engagement_channels]
            score = sum(match["weight"] for match in matches) if matches else 0.0
            participants = opportunity.participants
            identifier = self._opportunity_id(participants, opportunity.summary)
            payload = {
                "id": identifier,
                "name": opportunity.name,
                "summary": opportunity.summary,
                "participants": participants,
                "companyIds": [id_lookup.get(slug, slug) for slug in participants],
                "orgIds": sorted({org_lookup.get(slug) for slug in participants if org_lookup.get(slug)}),
                "score": round(score, 2),
                "priority": opportunity.priority,
                "breakdown": {
                    "rationale": rationale,
                    "engagement_channels": engagement_channels,
                    "supporting_matches": matches,
                    "expected_outcomes": opportunity.expected_outcomes,
                },
                "wwhKeys": sorted(
                    {
                        key
                        for slug in participants
                        for key in key_lookup.get(slug, [])
                        if key
                    }
                ),
            }
            opportunities[identifier] = OpportunityRecord(payload=payload)
        return opportunities

    @staticmethod
    def _slug_for(company: CompanyInput) -> str:
        if company.slug:
            return company.slug
        return company.name.lower().replace(" ", "-")

    def _to_need(self, need: NeedInput) -> Need:
        channels = self._channels_from_tags(need.tags)
        urgency_map = {Urgency.LOW: 2, Urgency.MED: 3, Urgency.HIGH: 5}
        urgency_value = urgency_map.get(need.urgency, 3)
        return Need(
            name=need.title,
            description=need.description,
            urgency=urgency_value,
            desired_outcomes=[],
            engagement_channels=channels,
        )

    def _to_capability(self, offer: OfferInput) -> Capability:
        channels = self._channels_from_tags(offer.tags)
        return Capability(
            name=offer.title,
            description=offer.description,
            maturity=offer.capacity,
            engagement_channels=channels,
        )

    @staticmethod
    def _channels_from_tags(tags: Iterable[str]) -> List[EngagementChannel]:
        lookup = {channel.value: channel for channel in EngagementChannel}
        channels: List[EngagementChannel] = []
        for tag in tags:
            key = tag.lower().replace(" ", "_")
            if key in lookup:
                channels.append(lookup[key])
        return channels

    @staticmethod
    def _opportunity_id(participants: Iterable[str], summary: str) -> str:
        key = "|".join(sorted(participants)) + "|" + summary
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        return f"opp_{digest}"
