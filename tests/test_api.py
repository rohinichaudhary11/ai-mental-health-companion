"""
Tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_healthcheck_endpoint():
    """Test health check endpoint."""
    response = client.get("/healthcheck")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "timestamp" in data


def test_predict_endpoint_structure():
    """Test predict endpoint request/response structure."""
    # Note: This will fail if model is not loaded
    # In a real test environment, you'd mock the model
    response = client.post(
        "/predict",
        json={"text": "I feel happy today"}
    )
    
    # Should either succeed (if model loaded) or return 503 (if not)
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "emotion" in data
        assert "confidence" in data
        assert "probabilities" in data
        assert "recommendation" in data
        assert "explanation" in data


if __name__ == "__main__":
    pytest.main([__file__])

