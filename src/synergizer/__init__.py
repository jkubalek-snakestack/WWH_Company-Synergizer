"""Synergizer package

This package powers the WWH multi-company synergy intelligence environment.
It provides data models, storage utilities, analytical engines, and reporting helpers
that can be wired into APIs, UIs, or automations.
"""

from .models import CompanyProfile, SynergyOpportunity, EngagementChannel
from .analysis import SynergyEngine
from .storage import SynergyGraph
from .templates import ProfileTemplateLibrary
from .reporting import OpportunityReport

__all__ = [
    "CompanyProfile",
    "SynergyOpportunity",
    "EngagementChannel",
    "SynergyEngine",
    "SynergyGraph",
    "ProfileTemplateLibrary",
    "OpportunityReport",
]
