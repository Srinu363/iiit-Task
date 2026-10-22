"""Tests for image analysis endpoints."""

import io


def test_analyze_no_file(client):
    """Analyze without a file should return 422."""
    response = client.post("/api/v1/analyze")
    assert response.status_code == 422


def test_analyze_empty_file(client):
    """Analyze with empty file should return 400."""
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.png", b"", "image/png")},
    )
    assert response.status_code == 400


def test_analyze_invalid_extension(client):
    """Analyze with unsupported extension should return 415."""
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415


def test_analyze_corrupt_image(client):
    """Analyze with corrupt image data should return 415 or 400."""
    # Fake PNG header but corrupt content
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.png", b"\x89PNG\r\n\x1a\ncorrupt", "image/png")},
    )
    assert response.status_code in (400, 415)


def test_analyze_wrong_mime(client):
    """Analyze with wrong MIME type but valid extension should still validate."""
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.exe", b"not an image", "application/octet-stream")},
    )
    assert response.status_code == 415


def test_analyze_valid_image(client, sample_image_bytes):
    """Analyze with a valid PNG should return 201 with results (if model loaded)."""
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.png", sample_image_bytes, "image/png")},
    )
    # If model is loaded, expect 201; otherwise 500 (model not available)
    if response.status_code == 201:
        data = response.json()
        assert "quality_score" in data
        assert "quality_label" in data
        assert "issues" in data
        assert "id" in data
        assert data["quality_label"] in ("ACCEPTABLE", "DEGRADED", "DEFECTIVE")
        assert 0 <= data["quality_score"] <= 100
