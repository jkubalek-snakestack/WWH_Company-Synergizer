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
        self.load_from_dict(data)

    def load_from_dict(self, data: Dict) -> None:
        """Load templates and tiering rules from a dictionary with validation."""
        if not isinstance(data, dict):
            raise ValueError("Template bundle must be a dictionary")
        
        # Validate and load templates
        templates = data.get("templates", [])
        if not isinstance(templates, list):
            raise ValueError("'templates' must be a list")
        
        for idx, template in enumerate(templates):
            if not isinstance(template, dict):
                raise ValueError(f"Template at index {idx} must be a dictionary")
            if "name" not in template or not template.get("name"):
                raise ValueError(f"Template at index {idx} is missing required field 'name'")
            if "description" not in template:
                raise ValueError(f"Template at index {idx} is missing required field 'description'")
            
            try:
                profile = ProfileTemplate.from_dict(template)
                self.templates[profile.name] = profile
            except (TypeError, ValueError, KeyError) as e:
                raise ValueError(f"Invalid template at index {idx}: {str(e)}") from e
        
        # Validate and load tiering rules
        tiering_rules = data.get("tiering_rules", [])
        if not isinstance(tiering_rules, list):
            raise ValueError("'tiering_rules' must be a list")
        
        for idx, rule in enumerate(tiering_rules):
            if not isinstance(rule, dict):
                raise ValueError(f"Tiering rule at index {idx} must be a dictionary")
            if "name" not in rule or not rule.get("name"):
                raise ValueError(f"Tiering rule at index {idx} is missing required field 'name'")
            if "description" not in rule:
                raise ValueError(f"Tiering rule at index {idx} is missing required field 'description'")
            if "criteria" not in rule:
                raise ValueError(f"Tiering rule at index {idx} is missing required field 'criteria'")
            
            try:
                tier = TieringRule.from_dict(rule)
                self.tiering_rules[tier.name] = tier
            except (TypeError, ValueError, KeyError) as e:
                raise ValueError(f"Invalid tiering rule at index {idx}: {str(e)}") from e

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
