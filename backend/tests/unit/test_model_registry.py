# backend/tests/unit/test_model_registry.py
"""
Unit Tests for Local Model Registry
Validates catalog consistency, capability checking, and unknown model rejection.
"""

import pytest
from backend.app.models.registry import ModelRegistry, REGISTERED_MODELS
from backend.app.models.types import ModelCapability


def test_registered_models_exist():
    """Test that core models qwen3:4b and gemma3:4b are present in the catalog."""
    models = ModelRegistry.list_models()
    model_ids = [m.model_id for m in models]

    assert "qwen3:4b" in model_ids
    assert "gemma3:4b" in model_ids


def test_model_capabilities_mapping():
    """Test capability mappings for reasoning and vision models."""
    qwen = ModelRegistry.get_model("qwen3:4b")
    assert qwen is not None
    assert ModelCapability.TEXT in qwen.capabilities
    assert ModelCapability.REASONING in qwen.capabilities
    assert ModelCapability.CODE in qwen.capabilities
    assert ModelCapability.VISION not in qwen.capabilities

    gemma = ModelRegistry.get_model("gemma3:4b")
    assert gemma is not None
    assert ModelCapability.VISION in gemma.capabilities
    assert ModelCapability.MULTIMODAL in gemma.capabilities
    assert ModelCapability.TEXT in gemma.capabilities


def test_unknown_model_lookup():
    """Test that unregistered models return None and fail capability checks."""
    assert ModelRegistry.get_model("unknown-cloud-gpt-99") is None
    assert ModelRegistry.is_registered("unknown-cloud-gpt-99") is False
    assert ModelRegistry.supports_capability("unknown-cloud-gpt-99", ModelCapability.TEXT) is False
