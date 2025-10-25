"""Synergizer package

This package powers the WWH multi-company synergy intelligence environment.
It provides data models, storage utilities, analytical engines, and reporting helpers
that can be wired into APIs, UIs, or automations.
"""

from .analysis import SynergyEngine
from .models import CompanyProfile, EngagementChannel, SynergyOpportunity
from .narrative import NarrativeParser, NarrativePromptBuilder, OpenAIChatModel
from .reporting import OpportunityReport
from .storage import SynergyGraph
from .templates import ProfileTemplateLibrary

__all__ = [
    "CompanyProfile",
    "SynergyOpportunity",
    "EngagementChannel",
    "SynergyEngine",
    "SynergyGraph",
    "ProfileTemplateLibrary",
    "OpportunityReport",
    "NarrativeParser",
    "NarrativePromptBuilder",
    "OpenAIChatModel",
]
