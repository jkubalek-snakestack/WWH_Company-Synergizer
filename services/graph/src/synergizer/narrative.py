"""Narrative-to-profile conversion utilities powered by large language models."""

from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from .models import CompanyProfile


class LanguageModel(Protocol):
    """Protocol describing the minimal interface required by the parser."""

    def generate(self, prompt: str, *, temperature: float = 0.0) -> str:
        """Return a model completion for the supplied prompt."""


@dataclass
class NarrativePromptBuilder:
    """Compose structured prompts instructing the LLM to emit JSON data."""

    instructions: str = (
        "You are an analyst who turns free-form company narratives into structured "
        "synergy profiles. Extract explicit details, infer missing but reasonable "
        "attributes, and capture potential offerings and partnership needs. "
        "Respond with a single JSON object that conforms to the provided schema."
    )

    def build(self, narrative: str) -> str:
        schema_description = textwrap.dedent(
            """
            Schema:
            {
              "name": string,
              "description": string,
              "mission": string,
              "organization_type": string,
              "headquarters": {
                "city": string,
                "region": string,
                "country": string
              },
              "regions_active": [string],
              "employee_count": integer,
              "expertise": [string],
              "industries": [string],
              "technologies": [string],
              "offerings": [
                {
                  "name": string,
                  "description": string,
                  "maturity": string,
                  "engagement_channels": ["product"|"service"|"knowledge"|"social_impact"|"funding"|"talent"|"technology"|"operations"|"sales"|"research"]
                }
              ],
              "needs": [
                {
                  "name": string,
                  "description": string,
                  "urgency": integer,
                  "desired_outcomes": [string],
                  "engagement_channels": ["product"|"service"|"knowledge"|"social_impact"|"funding"|"talent"|"technology"|"operations"|"sales"|"research"]
                }
              ],
              "assets": [
                {
                  "name": string,
                  "description": string,
                  "type": string,
                  "url": string
                }
              ],
              "initiatives": [
                {
                  "name": string,
                  "description": string,
                  "start_date": string,
                  "end_date": string,
                  "status": string,
                  "outcomes": [string]
                }
              ],
              "key_contacts": [
                {
                  "name": string,
                  "title": string,
                  "email": string,
                  "phone": string,
                  "notes": string
                }
              ],
              "cultural_notes": [string],
              "impact_metrics": [string],
              "goals": [string],
              "tags": [string]
            }
            """
        ).strip()
        narrative_block = narrative.strip()
        return textwrap.dedent(
            f"""
            {self.instructions}

            Narrative:
            \"\"\"
            {narrative_block}
            \"\"\"

            {schema_description}
            """
        ).strip()


class NarrativeParser:
    """Convert narrative company descriptions into structured profiles."""

    def __init__(self, model: LanguageModel, prompt_builder: NarrativePromptBuilder | None = None):
        self._model = model
        self._prompt_builder = prompt_builder or NarrativePromptBuilder()

    def parse(self, narrative: str, *, slug: str | None = None, default_name: str | None = None) -> CompanyProfile:
        prompt = self._prompt_builder.build(narrative)
        raw_response = self._model.generate(prompt, temperature=0.1)
        payload = self._extract_json(raw_response)
        payload.setdefault("name", default_name or "Unnamed Organization")
        payload.setdefault("description", narrative.strip())
        payload.setdefault("slug", slug or _slugify(payload["name"]))
        return CompanyProfile.from_dict(payload)

    @staticmethod
    def _extract_json(response: str) -> dict:
        """Parse the model response, tolerating surrounding prose."""

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if not match:
                raise ValueError("Model response did not contain JSON content") from None
            return json.loads(match.group(0))


def _slugify(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return normalized or f"company-{uuid4().hex[:8]}"


class OpenAIChatModel:
    """Thin wrapper around the OpenAI Chat Completions API."""

    def __init__(self, model: str = "gpt-4o-mini", *, api_key: str | None = None):
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str, *, temperature: float = 0.0) -> str:
        try:
            import openai
        except ModuleNotFoundError as exc:  # pragma: no cover - requires optional dep
            raise RuntimeError("openai package is not installed") from exc

        client = openai.OpenAI(api_key=self.api_key)  # type: ignore[attr-defined]
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You convert narratives into JSON profiles."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
