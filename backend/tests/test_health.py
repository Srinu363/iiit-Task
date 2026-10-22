"""Tests for health endpoints."""


def test_health_check(client):
    """Health endpoint should return 200 with status info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "database_connected" in data
    assert data["database_connected"] is True
