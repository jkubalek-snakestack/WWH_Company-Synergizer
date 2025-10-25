"""FastAPI service that wraps the synergy engine for external consumers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .analysis import SynergyEngine
from .models import CompanyProfile
from .templates import ProfileTemplateLibrary
from .utils import serialize_dataclass


class SynergyRequest(BaseModel):
    """Request payload for executing the synergy engine."""

    profiles: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Structured company profiles conforming to the CompanyProfile schema.",
    )
    companies: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Alias for `profiles` supporting the CLI dataset format.",
    )
    template_bundle: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional template + tiering rule bundle to support grouping in the response.",
    )

    model_config = ConfigDict(extra="ignore")


class SynergyResponse(BaseModel):
    """Response payload summarising matches and opportunities."""

    opportunities: List[Dict[str, Any]]
    matches: List[Dict[str, Any]]
    groups: Optional[Dict[str, List[str]]] = None

    model_config = ConfigDict(extra="ignore")


def _load_companies(request: SynergyRequest) -> List[CompanyProfile]:
    payload = request.profiles or request.companies or []
    companies = [CompanyProfile.from_dict(profile) for profile in payload]
    if not companies:
        raise HTTPException(status_code=400, detail="At least one profile is required")
    return companies


def _load_templates(bundle: Optional[Dict[str, Any]]) -> Optional[ProfileTemplateLibrary]:
    if not bundle:
        return None
    library = ProfileTemplateLibrary()
    library.load_from_dict(bundle)
    return library


def create_app() -> FastAPI:
    """Create a FastAPI application wrapping the synergy engine."""

    app = FastAPI(title="Synergizer Service", version="0.1.0")

    @app.post("/synergy/analyze", response_model=SynergyResponse)
    def analyze(request: SynergyRequest) -> SynergyResponse:
        companies = _load_companies(request)
        engine = SynergyEngine()
        engine.register_companies(companies)

        matches = [serialize_dataclass(match) for match in engine.find_complementary_pairs()]
        opportunities = [
            serialize_dataclass(opportunity) for opportunity in engine.build_opportunities()
        ]

        groups: Optional[Dict[str, List[str]]] = None
        library = _load_templates(request.template_bundle)
        if library and library.tiering_rules:
            grouped = library.group_companies(companies)
            groups = {
                name: [company.slug for company in bucket]
                for name, bucket in grouped.items()
                if bucket
            }

        return SynergyResponse(
            opportunities=opportunities,
            matches=matches,
            groups=groups,
        )

    return app


app = create_app()
