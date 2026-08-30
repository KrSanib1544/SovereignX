# backend/app/models/__init__.py
"""
SOVEREIGN-X Local Models Module
"""

from backend.app.models.types import (
    ModelCapability,
    ModelStatus,
    TaskModality,
    ModelMetadata,
    GenerationRequest,
    GenerationResponse,
    ModelHealthStatus,
    ModelResourceError,
    ModelExecutionError,
)
from backend.app.models.base import LLMProvider
from backend.app.models.ollama_provider import OllamaProvider
from backend.app.models.registry import ModelRegistry, REGISTERED_MODELS
from backend.app.models.telemetry import (
    ResourceTelemetry,
    GpuTelemetry,
    SystemTelemetry,
    HardwareSnapshot,
)
from backend.app.models.router import ModelRouter

__all__ = [
    "ModelCapability",
    "ModelStatus",
    "TaskModality",
    "ModelMetadata",
    "GenerationRequest",
    "GenerationResponse",
    "ModelHealthStatus",
    "ModelResourceError",
    "ModelExecutionError",
    "LLMProvider",
    "OllamaProvider",
    "ModelRegistry",
    "REGISTERED_MODELS",
    "ResourceTelemetry",
    "GpuTelemetry",
    "SystemTelemetry",
    "HardwareSnapshot",
    "ModelRouter",
]
