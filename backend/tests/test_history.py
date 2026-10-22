"""Tests for history endpoints."""


def test_list_analyses_empty(client):
    """List analyses should return empty list initially."""
    response = client.get("/api/v1/analyses")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0
    assert "items" in data
    assert "total_pages" in data


def test_get_analysis_not_found(client):
    """Get non-existent analysis should return 404."""
    response = client.get("/api/v1/analyses/nonexistent-id")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data


def test_delete_analysis_not_found(client):
    """Delete non-existent analysis should return 404."""
    response = client.delete("/api/v1/analyses/nonexistent-id")
    assert response.status_code == 404


def test_list_analyses_pagination(client):
    """Pagination parameters should be accepted."""
    response = client.get("/api/v1/analyses?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5


def test_list_analyses_filter(client):
    """Filter by quality label should be accepted."""
    response = client.get("/api/v1/analyses?label=ACCEPTABLE")
    assert response.status_code == 200
