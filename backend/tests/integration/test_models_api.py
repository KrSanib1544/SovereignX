# backend/tests/integration/test_models_api.py
"""
Integration Tests for Models & Telemetry REST API
Validates FastAPI endpoints /api/v1/health, /api/v1/telemetry, and /api/v1/models.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_health_endpoint():
    """Test GET /api/v1/health returns air-gap and service status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["airgap_mode"] is True
    assert "localhost" in data["ollama_endpoint"]


def test_api_telemetry_endpoint():
    """Test GET /api/v1/telemetry returns structured hardware state."""
    response = client.get("/api/v1/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "hardware" in data
    assert "ram" in data["hardware"]
    assert "cpu" in data["hardware"]
    assert data["hardware"]["ram"]["total_mb"] > 0


def test_api_list_models_endpoint():
    """Test GET /api/v1/models returns registered model list with capabilities."""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    model_ids = [m["model_id"] for m in data]
    assert "qwen3:4b" in model_ids
    assert "gemma3:4b" in model_ids
