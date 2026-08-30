# backend/tests/unit/test_model_router.py
"""
Unit Tests for Model Router
Tests deterministic routing rules, modality resolution, and invalid capability handling.
"""

import pytest
from unittest.mock import AsyncMock
from backend.app.models.router import ModelRouter
from backend.app.models.types import (
    GenerationRequest,
    ModelCapability,
    ModelExecutionError,
)


@pytest.fixture
def mock_provider():
    """Mock LLMProvider for unit testing router logic without live network."""
    provider = AsyncMock()
    provider.check_health.return_value = True
    provider.list_installed_models.return_value = ["qwen3:4b", "gemma3:4b"]
    provider.is_model_available.return_value = True
    provider.get_active_models.return_value = []
    provider.load_model.return_value = True
    provider.unload_model.return_value = True
    return provider


def test_router_text_defaults_to_qwen3(mock_provider):
    """Test that standard text requests route deterministically to qwen3:4b."""
    router = ModelRouter(provider=mock_provider)
    req = GenerationRequest(prompt="Explain non-destructive testing procedures.")
    target_model = router.route_request(req)

    assert target_model == "qwen3:4b"


def test_router_image_routes_to_gemma3(mock_provider):
    """Test that requests containing image payloads route deterministically to gemma3:4b."""
    router = ModelRouter(provider=mock_provider)
    req = GenerationRequest(
        prompt="Identify surface crack length in mm.",
        images=["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="]
    )
    target_model = router.route_request(req)

    assert target_model == "gemma3:4b"


def test_router_explicit_registered_model(mock_provider):
    """Test that valid explicit model selection from catalog is honored."""
    router = ModelRouter(provider=mock_provider)
    req = GenerationRequest(
        prompt="Quick text note",
        model="gemma3:4b"
    )
    target_model = router.route_request(req)
    assert target_model == "gemma3:4b"


def test_router_rejects_unregistered_model(mock_provider):
    """Test that arbitrary unregistered model names are strictly rejected."""
    router = ModelRouter(provider=mock_provider)
    req = GenerationRequest(
        prompt="Hello",
        model="gpt-4o-remote"
    )
    with pytest.raises(ModelExecutionError) as exc:
        router.route_request(req)
    assert "not registered" in str(exc.value)


def test_router_rejects_image_on_text_only_model(mock_provider):
    """Test that sending images to a model without vision capability raises error."""
    router = ModelRouter(provider=mock_provider)
    req = GenerationRequest(
        prompt="Look at this image",
        model="qwen3:4b",
        images=["fake_base64_image"]
    )
    with pytest.raises(ModelExecutionError) as exc:
        router.route_request(req)
    assert "does not support visual" in str(exc.value)
