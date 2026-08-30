# backend/app/models/base.py
"""
Abstract Local Model Provider Interface
Defines the contract all local LLM engines (Ollama, llama.cpp, vLLM) must satisfy.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional
from backend.app.models.types import (
    GenerationRequest,
    GenerationResponse,
    ModelHealthStatus,
    ModelMetadata,
)


class LLMProvider(ABC):
    """
    Abstract interface for local offline LLM providers.
    """

    @abstractmethod
    async def check_health(self) -> bool:
        """Verify provider process connectivity and daemon liveness."""
        pass

    @abstractmethod
    async def list_installed_models(self) -> List[str]:
        """List model IDs currently installed on the local provider daemon."""
        pass

    @abstractmethod
    async def is_model_available(self, model_id: str) -> bool:
        """Check if a specific model is installed and accessible locally."""
        pass

    @abstractmethod
    async def load_model(self, model_id: str, keep_alive: str = "5m") -> bool:
        """Explicitly load a model into GPU memory."""
        pass

    @abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        """Explicitly evict a model from GPU memory (set keep_alive: 0)."""
        pass

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Execute non-streaming local inference."""
        pass

    @abstractmethod
    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Execute streaming local inference yielding token chunks."""
        pass

    @abstractmethod
    async def get_active_models(self) -> List[Dict[str, any]]:
        """Query currently active in-memory models and their VRAM allocations."""
        pass
