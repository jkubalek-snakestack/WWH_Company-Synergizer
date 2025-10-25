import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from synergizer.api import create_app


def load_sample_profiles():
    path = Path(__file__).parent.parent / "data" / "sample_profiles.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_analyze_returns_opportunities_and_matches():
    client = TestClient(create_app())
    payload = load_sample_profiles()

    response = client.post("/synergy/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["opportunities"], "expected at least one opportunity"
    assert body["matches"], "expected pairwise matches"


def test_analyze_requires_profiles():
    client = TestClient(create_app())

    response = client.post("/synergy/analyze", json={"profiles": []})

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one profile is required"
