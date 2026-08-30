# backend/app/models/router.py
"""
Resource-Aware Model Router & VRAM Arbitrator
Coordinates deterministic capability routing, sequential single-model VRAM residence,
hardware safety checks, and local model inference.
"""

import asyncio
from typing import AsyncIterator, Dict, List, Optional
from backend.app.config import settings
from backend.app.models.base import LLMProvider
from backend.app.models.ollama_provider import OllamaProvider
from backend.app.models.registry import ModelRegistry
from backend.app.models.telemetry import ResourceTelemetry
from backend.app.models.types import (
    GenerationRequest,
    GenerationResponse,
    ModelCapability,
    ModelHealthStatus,
    ModelMetadata,
    ModelResourceError,
    ModelExecutionError,
    TaskModality,
)


class ModelRouter:
    """
    Core Model Router and Hardware Resource Arbitrator.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider: LLMProvider = provider or OllamaProvider()
        self._active_model_id: Optional[str] = None
        self._last_invoked_map: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    def route_request(self, request: GenerationRequest) -> str:
        """
        Deterministically select the appropriate registered model based on request modality.
        """
        # 1. If an explicit model is requested, validate against registry
        if request.model:
            meta = ModelRegistry.get_model(request.model)
            if not meta:
                raise ModelExecutionError(
                    f"Model '{request.model}' is not registered in the approved catalog."
                )
            if not meta.enabled:
                raise ModelExecutionError(f"Model '{request.model}' is currently disabled.")

            # Validate multimodal request capability
            if request.images and ModelCapability.VISION not in meta.capabilities:
                raise ModelExecutionError(
                    f"Model '{request.model}' does not support visual / multimodal inputs."
                )
            return meta.model_id

        # 2. Multimodal / Image Input Routing -> Gemma 3 4B
        if request.images and len(request.images) > 0:
            return settings.VISION_MODEL

        # 3. Standard Text / Reasoning / Code Routing -> Qwen 3 4B
        return settings.REASONING_MODEL

    async def prepare_model(self, target_model_id: str) -> None:
        """
        Enforce sequential single-model VRAM residence.
        Evicts inactive models before loading the target model into GPU memory.
        """
        async with self._lock:
            # 1. Verify model is installed in local provider
            is_available = await self.provider.is_model_available(target_model_id)
            if not is_available:
                raise ModelExecutionError(
                    f"Target model '{target_model_id}' is not installed in the local provider."
                )

            # 2. Check currently resident models in memory
            active_models = await self.provider.get_active_models()
            target_base = target_model_id.split(":")[0]
            for active_info in active_models:
                active_name = active_info.get("name", "")
                active_base = active_name.split(":")[0]
                if active_name and active_base != target_base and active_name != target_model_id:
                    # Explicitly unload active model to free GPU VRAM
                    await self.provider.unload_model(active_name)

            # 3. Check hardware safety thresholds
            meta = ModelRegistry.get_model(target_model_id)
            required_vram_mb = meta.estimated_vram_mb if meta else 2560
            gpu = ResourceTelemetry.get_gpu_telemetry()

            if gpu.available and gpu.vram_total_mb > 0:
                if gpu.vram_total_mb < (required_vram_mb * 0.8):
                    raise ModelResourceError(
                        required_model=target_model_id,
                        reason="Total physical GPU VRAM is below model minimum requirements",
                        required_mb=required_vram_mb,
                        available_mb=gpu.vram_total_mb,
                        error_code="SOV_ERR_VRAM_INSUFFICIENT_HARDWARE"
                    )

            self._active_model_id = target_model_id

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Route, arbitrate VRAM, and execute generation request.
        """
        target_model = self.route_request(request)
        await self.prepare_model(target_model)

        # Update request with resolved target model
        exec_request = request.model_copy(update={"model": target_model})

        from datetime import datetime, timezone
        self._last_invoked_map[target_model] = datetime.now(timezone.utc).isoformat()

        return await self.provider.generate(exec_request)

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """
        Route, arbitrate VRAM, and execute streaming generation.
        """
        target_model = self.route_request(request)
        await self.prepare_model(target_model)

        exec_request = request.model_copy(update={"model": target_model})

        from datetime import datetime, timezone
        self._last_invoked_map[target_model] = datetime.now(timezone.utc).isoformat()

        async for chunk in self.provider.generate_stream(exec_request):
            yield chunk

    async def inspect_image(
        self,
        image_base64: str,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> GenerationResponse:
        """
        Convenience method for vision inspection tasks via Gemma 3.
        """
        req = GenerationRequest(
            model=settings.VISION_MODEL,
            prompt=prompt,
            system_prompt=system_prompt,
            images=[image_base64],
            temperature=0.1
        )
        return await self.generate(req)

    async def get_model_health_list(self) -> List[ModelHealthStatus]:
        """
        Query all registered models with their live installation, residency, and VRAM states.
        """
        registered = ModelRegistry.list_models(only_enabled=False)
        installed_list = await self.provider.list_installed_models()
        active_list = await self.provider.get_active_models()

        active_dict = {
            m.get("name", "").split(":")[0]: m for m in active_list if "name" in m
        }

        results: List[ModelHealthStatus] = []
        for reg in registered:
            base_name = reg.model_id.split(":")[0]
            is_installed = any(
                inst == reg.model_id or inst.startswith(f"{base_name}:")
                for inst in installed_list
            )
            is_active = (
                self._active_model_id == reg.model_id or
                base_name in active_dict or
                reg.model_id in [m.get("name") for m in active_list]
            )

            vram_alloc = None
            if is_active and base_name in active_dict:
                vram_bytes = active_dict[base_name].get("size_vram", 0)
                vram_alloc = round(vram_bytes / (1024 * 1024), 1) if vram_bytes else reg.estimated_vram_mb

            results.append(ModelHealthStatus(
                model_id=reg.model_id,
                installed=is_installed,
                available=is_installed and reg.enabled,
                is_active=is_active,
                capabilities=reg.capabilities,
                provider=reg.provider,
                last_invoked_at=self._last_invoked_map.get(reg.model_id),
                vram_allocated_mb=vram_alloc,
                error_state=None
            ))

        return results

    async def force_swap(self, target_model_id: str) -> ModelHealthStatus:
        """
        Explicitly evict resident models and load target model.
        """
        meta = ModelRegistry.get_model(target_model_id)
        if not meta:
            raise ModelExecutionError(f"Model '{target_model_id}' is not registered.")

        await self.prepare_model(target_model_id)
        await self.provider.load_model(target_model_id, keep_alive="5m")
        health_list = await self.get_model_health_list()
        for h in health_list:
            if h.model_id == target_model_id:
                return h

        return ModelHealthStatus(
            model_id=target_model_id,
            installed=True,
            available=True,
            is_active=True,
            capabilities=meta.capabilities,
            provider=meta.provider
        )
