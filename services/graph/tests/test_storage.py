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


def test_graph_upsert_company_basic():
    """Verify basic company insertion works."""
    graph = SynergyGraph()
    
    company = create_test_company("test-company", "Test Company")
    graph.upsert_company(company)
    
    # Verify company was added
    assert graph.company("test-company").name == "Test Company"
    assert graph.company("test-company").slug == "test-company"
    
    # Verify company appears in companies iterator
    companies = list(graph.companies())
    assert len(companies) == 1
    assert companies[0].slug == "test-company"


def test_graph_upsert_company_generates_slug():
    """Verify slug is auto-generated when missing."""
    graph = SynergyGraph()
    
    # Create company with slug first (required by from_dict)
    company = CompanyProfile.from_dict({
        "slug": "temp-slug",
        "name": "Test Company Name",
    })
    
    # Manually set slug to None to simulate missing slug scenario
    company.slug = None
    
    # Upsert should generate slug from name
    graph.upsert_company(company)
    
    # Slug should now be set
    assert company.slug is not None
    assert company.slug == "test-company-name"  # slugify normalizes to lowercase with hyphens
    
    # Should be able to access by generated slug
    retrieved = graph.company(company.slug)
    assert retrieved.name == "Test Company Name"


def test_graph_remove_company_removes_edges():
    """Verify removing company also removes all edges."""
    graph = SynergyGraph()
    
    # Create companies
    company1 = create_test_company("company-1")
    company2 = create_test_company("company-2")
    company3 = create_test_company("company-3")
    
    graph.upsert_company(company1)
    graph.upsert_company(company2)
    graph.upsert_company(company3)
    
    # Create edges: company1 -> company2, company1 -> company3, company2 -> company3
    graph.link_companies(
        source_slug="company-1",
        target_slug="company-2",
        weight=0.5,
        label="Link 1->2",
        rationale="Test",
        engagement_channels=[EngagementChannel.PRODUCT],
    )
    graph.link_companies(
        source_slug="company-1",
        target_slug="company-3",
        weight=0.6,
        label="Link 1->3",
        rationale="Test",
        engagement_channels=[EngagementChannel.SERVICE],
    )
    graph.link_companies(
        source_slug="company-2",
        target_slug="company-3",
        weight=0.7,
        label="Link 2->3",
        rationale="Test",
        engagement_channels=[EngagementChannel.KNOWLEDGE],
    )
    
    # Verify edges exist
    edges_before = list(graph.edges())
    assert len(edges_before) == 3
    
    # Remove company-1
    graph.remove_company("company-1")
    
    # Verify company-1 is removed
    with pytest.raises(KeyError):
        graph.company("company-1")
    
    # Verify edges from company-1 are removed
    edges_after = list(graph.edges())
    assert len(edges_after) == 1
    assert edges_after[0].source == "company-2"
    assert edges_after[0].target == "company-3"
    
    # Verify edges pointing to company-1 are also removed (if any existed)
    # In this case, we only had edges FROM company-1, so they're all gone


def test_graph_link_companies_valid():
    """Verify linking companies with valid slugs works."""
    graph = SynergyGraph()
    
    # Create companies
    source = create_test_company("source-company")
    target = create_test_company("target-company")
    
    graph.upsert_company(source)
    graph.upsert_company(target)
    
    # Link them
    graph.link_companies(
        source_slug="source-company",
        target_slug="target-company",
        weight=0.8,
        label="Valid link",
        rationale="Testing valid link",
        engagement_channels=[EngagementChannel.PRODUCT, EngagementChannel.SERVICE],
    )
    
    # Verify edge was created
    edges = list(graph.edges())
    assert len(edges) == 1
    edge = edges[0]
    assert edge.source == "source-company"
    assert edge.target == "target-company"
    assert edge.weight == 0.8
    assert edge.label == "Valid link"
    assert edge.rationale == "Testing valid link"
    assert len(edge.engagement_channels) == 2
    assert EngagementChannel.PRODUCT in edge.engagement_channels
    assert EngagementChannel.SERVICE in edge.engagement_channels


def test_graph_matches_for_returns_correct_matches():
    """Verify matches_for() returns correct matches."""
    graph = SynergyGraph()
    
    # Create companies
    company1 = create_test_company("company-1")
    company2 = create_test_company("company-2")
    company3 = create_test_company("company-3")
    
    graph.upsert_company(company1)
    graph.upsert_company(company2)
    graph.upsert_company(company3)
    
    # Create edges from company-1
    graph.link_companies(
        source_slug="company-1",
        target_slug="company-2",
        weight=0.5,
        label="Match 1->2",
        rationale="Test match",
        engagement_channels=[EngagementChannel.PRODUCT],
    )
    graph.link_companies(
        source_slug="company-1",
        target_slug="company-3",
        weight=0.7,
        label="Match 1->3",
        rationale="Test match",
        engagement_channels=[EngagementChannel.SERVICE],
    )
    
    # Create edge from company-2 (should not appear in company-1's matches)
    graph.link_companies(
        source_slug="company-2",
        target_slug="company-3",
        weight=0.6,
        label="Match 2->3",
        rationale="Test match",
        engagement_channels=[EngagementChannel.KNOWLEDGE],
    )
    
    # Get matches for company-1
    matches = graph.matches_for("company-1")
    
    # Should return 2 matches (company-1 -> company-2 and company-1 -> company-3)
    assert len(matches) == 2
    
    # Verify match details
    match_slugs = {(m.source_company, m.target_company) for m in matches}
    assert ("company-1", "company-2") in match_slugs
    assert ("company-1", "company-3") in match_slugs
    
    # Verify match properties
    match_1_2 = next(m for m in matches if m.target_company == "company-2")
    assert match_1_2.source_company == "company-1"
    assert match_1_2.weight == 0.5
    assert match_1_2.description == "Match 1->2"
    assert EngagementChannel.PRODUCT in match_1_2.engagement_channels
    
    # Get matches for company-2
    matches_2 = graph.matches_for("company-2")
    assert len(matches_2) == 1
    assert matches_2[0].target_company == "company-3"
    
    # Get matches for company-3 (should be empty)
    matches_3 = graph.matches_for("company-3")
    assert len(matches_3) == 0


def test_graph_ingest_multiple_companies():
    """Verify bulk company ingestion works."""
    graph = SynergyGraph()
    
    # Create multiple companies
    companies = [
        create_test_company("company-1", "Company One"),
        create_test_company("company-2", "Company Two"),
        create_test_company("company-3", "Company Three"),
        create_test_company("company-4", "Company Four"),
    ]
    
    # Ingest all at once
    graph.ingest(companies)
    
    # Verify all companies were added
    all_companies = list(graph.companies())
    assert len(all_companies) == 4
    
    # Verify each company is accessible
    assert graph.company("company-1").name == "Company One"
    assert graph.company("company-2").name == "Company Two"
    assert graph.company("company-3").name == "Company Three"
    assert graph.company("company-4").name == "Company Four"
    
    # Verify all have empty edge lists initially
    for company in companies:
        matches = graph.matches_for(company.slug)
        assert len(matches) == 0

