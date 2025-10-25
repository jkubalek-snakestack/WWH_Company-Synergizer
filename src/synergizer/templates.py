"""Template-driven profile scaffolding and tiering helpers."""

from __future__ import annotations

import json
from typing import Dict, Iterable, List

from .models import CompanyProfile, ProfileTemplate, TieringRule, normalize_terms


class ProfileTemplateLibrary:
    """Holds reusable profile templates and tiering rules."""

    def __init__(self) -> None:
        self.templates: Dict[str, ProfileTemplate] = {}
        self.tiering_rules: Dict[str, TieringRule] = {}

    def load_from_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        for template in data.get("templates", []):
            profile = ProfileTemplate.from_dict(template)
            self.templates[profile.name] = profile
        for rule in data.get("tiering_rules", []):
            tier = TieringRule.from_dict(rule)
            self.tiering_rules[tier.name] = tier

    def template(self, name: str) -> ProfileTemplate:
        return self.templates[name]

    def tier(self, name: str) -> TieringRule:
        return self.tiering_rules[name]

    def auto_complete_profile(self, base: Dict, template_name: str) -> CompanyProfile:
        template = self.template(template_name)
        payload = dict(base)
        for field in template.required_fields:
            payload.setdefault(field, [])
        payload.setdefault("tags", []).extend(template.tags)
        payload["tags"] = normalize_terms(payload["tags"])
        return CompanyProfile.from_dict(payload)

    def group_companies(
        self, companies: Iterable[CompanyProfile]
    ) -> Dict[str, List[CompanyProfile]]:
        buckets: Dict[str, List[CompanyProfile]] = {name: [] for name in self.tiering_rules}
        for company in companies:
            for name, rule in self.tiering_rules.items():
                if rule.applies_to(company):
                    buckets[name].append(company)
        return buckets
