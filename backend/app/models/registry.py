# backend/app/models/registry.py
"""
Local Model Registry
Centralized, verified catalog of supported local models, their modalities,
context capacities, and hardware profiles.
"""

from typing import Dict, List, Optional
from backend.app.models.types import ModelCapability, ModelMetadata


# Initial Verified Model Catalog
REGISTERED_MODELS: Dict[str, ModelMetadata] = {
    "qwen3:4b": ModelMetadata(
        model_id="qwen3:4b",
        provider="ollama",
        capabilities=[
            ModelCapability.TEXT,
            ModelCapability.REASONING,
            ModelCapability.CODE,
            ModelCapability.TOOL_CALLING,
            ModelCapability.JSON_MODE,
        ],
        context_window=8192,
        disk_size_gb=2.5,
        estimated_vram_mb=2560,
        preferred_use_cases=[
            "Agent task planning & ReAct loops",
            "Deterministic Python code & pandas analysis",
            "RAG factual citation & answer synthesis",
            "Structured JSON generation",
        ],
        enabled=True
    ),
    "gemma3:4b": ModelMetadata(
        model_id="gemma3:4b",
        provider="ollama",
        capabilities=[
            ModelCapability.TEXT,
            ModelCapability.VISION,
            ModelCapability.MULTIMODAL,
            ModelCapability.REASONING,
        ],
        context_window=4096,
        disk_size_gb=3.3,
        estimated_vram_mb=3350,
        preferred_use_cases=[
            "High-resolution industrial image inspection",
            "Visual crack, corrosion, and defect detection",
            "Scanned engineering blueprint & P&ID analysis",
        ],
        enabled=True
    ),
}


class ModelRegistry:
    """
    Manages and queries registered local model specifications.
    """

    @classmethod
    def get_model(cls, model_id: str) -> Optional[ModelMetadata]:
        """Lookup model metadata by exact ID or base name."""
        clean_id = model_id.split(":")[0] + ":4b" if ":" not in model_id else model_id
        return REGISTERED_MODELS.get(clean_id) or REGISTERED_MODELS.get(model_id)

    @classmethod
    def list_models(cls, only_enabled: bool = True) -> List[ModelMetadata]:
        """List all models registered in the catalog."""
        models = list(REGISTERED_MODELS.values())
        if only_enabled:
            return [m for m in models if m.enabled]
        return models

    @classmethod
    def is_registered(cls, model_id: str) -> bool:
        """Check if a model ID exists in the approved registry."""
        return cls.get_model(model_id) is not None

    @classmethod
    def supports_capability(cls, model_id: str, capability: ModelCapability) -> bool:
        """Check if a registered model explicitly supports the requested capability."""
        meta = cls.get_model(model_id)
        if not meta or not meta.enabled:
            return False
        return capability in meta.capabilities
