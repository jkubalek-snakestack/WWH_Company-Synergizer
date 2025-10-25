"""Integration tests for the FastAPI graph wrapper."""

from __future__ import annotations

from typing import Dict, List

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from services.graph.main import create_app


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def sample_dataset() -> Dict[str, List[Dict[str, object]]]:
    return {
        "companies": [
            {
                "id": "comp-mentor",
                "orgId": "org-mentors",
                "slug": "mentor-hub",
                "name": "Mentor Hub",
                "region": "Kenya",
                "mission": "Equip youth with digital learning pathways.",
                "wwhKeys": ["Education", "Community Dev"],
                "capabilities": ["education", "digital"],
                "visibility": "PARTNER",
            },
            {
                "id": "comp-studio",
                "orgId": "org-creators",
                "slug": "studio-labs",
                "name": "Studio Labs",
                "region": "USA",
                "mission": "Create immersive storytelling for social impact.",
                "wwhKeys": ["Education", "Energy"],
                "capabilities": ["storytelling", "technology"],
                "visibility": "PUBLIC",
            },
        ],
        "needs": [
            {
                "id": "need-1",
                "companyId": "comp-mentor",
                "title": "Digital Learning Platform",
                "description": "Seeking partners to co-design digital learning experiences.",
                "tags": ["service", "technology"],
                "urgency": "HIGH",
                "visibility": "PARTNER",
            }
        ],
        "offers": [
            {
                "id": "offer-1",
                "companyId": "comp-studio",
                "title": "Digital Learning Platform",
                "description": "Immersive storytelling modules ready for partnership.",
                "tags": ["service", "knowledge"],
                "capacity": "MED",
                "visibility": "PUBLIC",
            }
        ],
        "contacts": [
            {
                "id": "contact-1",
                "companyId": "comp-mentor",
                "name": "Lina Okoth",
                "role": "Partnership Lead",
                "privacyLevel": "PRIVATE",
            }
        ],
    }


def test_recompute_returns_summary_counts(client: TestClient) -> None:
    response = client.post("/recompute", json=sample_dataset())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["companies"] == 2
    assert body["needs"] == 1
    assert body["offers"] == 1
    assert body["contacts"] == 1
    assert body["opportunities"] >= 1


def test_opportunities_filtering(client: TestClient) -> None:
    client.post("/recompute", json=sample_dataset())

    response = client.get("/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    first = data["items"][0]
    assert first["score"] > 0
    assert set(first["orgIds"]) == {"org-mentors", "org-creators"}

    filtered_org = client.get("/opportunities", params={"orgId": "org-mentors"})
    assert filtered_org.status_code == 200
    assert filtered_org.json()["count"] >= 1

    filtered_company = client.get("/opportunities", params={"companyId": "comp-mentor"})
    assert filtered_company.status_code == 200
    assert filtered_company.json()["count"] >= 1

    status_filtered = client.get("/opportunities", params={"status": "OPEN"})
    assert status_filtered.status_code == 200
    assert status_filtered.json()["count"] == data["count"]


def test_playbook_generation_uses_cached_opportunity(client: TestClient) -> None:
    client.post("/recompute", json=sample_dataset())
    opportunities = client.get("/opportunities").json()["items"]
    payload = {"opportunity": opportunities[0]}

    response = client.post("/playbook", json=payload)
    assert response.status_code == 200
    playbook = response.json()
    assert "summary" in playbook
    sections = playbook["sections"]
    required_sections = {
        "summary",
        "actors",
        "angles",
        "steps",
        "timeline",
        "risks",
        "collateral",
        "wwh_alignment",
    }
    assert required_sections.issubset(sections.keys())
    assert sections["actors"], "Expected actors to be populated from cached companies"
