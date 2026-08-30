# backend/app/models/types.py
"""
Local Model Types & Contracts
Defines universal schemas, capabilities, lifecycle states, and generation requests/responses.
Never exposes provider-specific (e.g., Ollama/vLLM) implementation details to higher layers.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelCapability(str, Enum):
    TEXT = "TEXT"
    REASONING = "REASONING"
    CODE = "CODE"
    VISION = "VISION"
    MULTIMODAL = "MULTIMODAL"
    TOOL_CALLING = "TOOL_CALLING"
    JSON_MODE = "JSON_MODE"


class ModelStatus(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    AVAILABLE = "AVAILABLE"
    LOADING = "LOADING"
    READY = "READY"
    RUNNING = "RUNNING"
    UNLOADING = "UNLOADING"
    FAILED = "FAILED"


class TaskModality(str, Enum):
    TEXT_ONLY = "TEXT_ONLY"
    VISION_ONLY = "VISION_ONLY"
    MULTIMODAL = "MULTIMODAL"
    STRUCTURED_DATA = "STRUCTURED_DATA"


class ModelMetadata(BaseModel):
    """
    Metadata specification for a registered local open-weight model.
    """
    model_id: str
    provider: str = "ollama"
    capabilities: List[ModelCapability]
    context_window: int = 4096
    disk_size_gb: float
    estimated_vram_mb: int
    preferred_use_cases: List[str] = Field(default_factory=list)
    enabled: bool = True


class GenerationRequest(BaseModel):
    """
    Universal input payload for text generation or multimodal reasoning.
    """
    prompt: str
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    images: Optional[List[str]] = None  # Base64-encoded image strings
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: Optional[int] = None
    format: Optional[str] = None       # e.g., "json" for strict JSON output
    keep_alive: Optional[str] = "5m"
    stream: bool = False


class GenerationResponse(BaseModel):
    """
    Universal result payload returned from local model inference.
    """
    model: str
    content: str
    thinking: Optional[str] = None
    total_duration_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    done: bool = True
    error: Optional[str] = None


class ModelHealthStatus(BaseModel):
    """
    Health, residency, and hardware allocation summary for a registered model.
    """
    model_id: str
    installed: bool
    available: bool
    is_active: bool
    capabilities: List[ModelCapability]
    provider: str
    last_invoked_at: Optional[str] = None
    vram_allocated_mb: Optional[float] = None
    error_state: Optional[str] = None


class ModelResourceError(Exception):
    """Raised when GPU VRAM or host memory cannot accommodate a model transition."""
    def __init__(
        self,
        required_model: str,
        reason: str,
        required_mb: int,
        available_mb: float,
        error_code: str = "SOV_ERR_VRAM_OOM"
    ):
        self.required_model = required_model
        self.reason = reason
        self.required_mb = required_mb
        self.available_mb = available_mb
        self.error_code = error_code
        super().__init__(
            f"Resource allocation failed for '{required_model}': {reason}. "
            f"Required: {required_mb} MB, Available: {available_mb:.1f} MB (Code: {error_code})"
        )


class ModelExecutionError(Exception):
    """Raised when local inference fails or times out."""
    pass
