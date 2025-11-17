"""Tests for the graph storage layer."""

import pytest

from synergizer.models import CompanyProfile, EngagementChannel
from synergizer.storage import SynergyGraph


def create_test_company(slug: str, name: str = None) -> CompanyProfile:
    """Helper to create a minimal CompanyProfile for testing."""
    return CompanyProfile.from_dict({
        "slug": slug,
        "name": name or slug.replace("-", " ").title(),
    })


def test_graph_upsert_company_duplicate_slug():
    """Verify duplicate slugs overwrite existing company (current behavior)."""
    graph = SynergyGraph()
    
    company1 = create_test_company("test-company", "Original Company")
    company2 = create_test_company("test-company", "Updated Company")
    
    # First upsert
    graph.upsert_company(company1)
    assert graph.company("test-company").name == "Original Company"
    
    # Second upsert with same slug - should overwrite
    graph.upsert_company(company2)
    assert graph.company("test-company").name == "Updated Company"
    
    # Verify only one company exists
    companies = list(graph.companies())
    assert len(companies) == 1
    assert companies[0].name == "Updated Company"


def test_graph_company_raises_keyerror_missing():
    """Verify company() raises KeyError for non-existent slug."""
    graph = SynergyGraph()
    
    # Accessing a company that doesn't exist should raise KeyError
    with pytest.raises(KeyError):
        graph.company("non-existent-company")
    
    # Verify the error message is clear
    try:
        graph.company("missing-slug")
    except KeyError as e:
        assert "missing-slug" in str(e) or "missing-slug" in repr(e)


def test_graph_link_companies_invalid_source():
    """Verify linking with invalid source slug raises error or handles gracefully."""
    graph = SynergyGraph()
    
    # Create target company
    target = create_test_company("target-company")
    graph.upsert_company(target)
    
    # Try to link with non-existent source
    # Current implementation doesn't validate, but we should document the behavior
    # If it doesn't raise, we'll test that it creates orphaned edges
    graph.link_companies(
        source_slug="non-existent-source",
        target_slug="target-company",
        weight=0.5,
        label="Test link",
        rationale="Testing invalid source",
        engagement_channels=[EngagementChannel.PRODUCT],
    )
    
    # The current implementation allows this, creating an edge with invalid source
    # This test documents that behavior - edges can reference non-existent companies
    edges = list(graph.edges())
    assert len(edges) == 1
    assert edges[0].source == "non-existent-source"
    assert edges[0].target == "target-company"
    
    # However, accessing the source company should fail
    with pytest.raises(KeyError):
        graph.company("non-existent-source")


def test_graph_link_companies_invalid_target():
    """Verify linking with invalid target slug raises error or handles gracefully."""
    graph = SynergyGraph()
    
    # Create source company
    source = create_test_company("source-company")
    graph.upsert_company(source)
    
    # Try to link with non-existent target
    # Current implementation doesn't validate, but we should document the behavior
    graph.link_companies(
        source_slug="source-company",
        target_slug="non-existent-target",
        weight=0.5,
        label="Test link",
        rationale="Testing invalid target",
        engagement_channels=[EngagementChannel.SERVICE],
    )
    
    # The current implementation allows this, creating an edge with invalid target
    # This test documents that behavior - edges can reference non-existent companies
    edges = list(graph.edges())
    assert len(edges) == 1
    assert edges[0].source == "source-company"
    assert edges[0].target == "non-existent-target"
    
    # However, accessing the target company should fail
    with pytest.raises(KeyError):
        graph.company("non-existent-target")

