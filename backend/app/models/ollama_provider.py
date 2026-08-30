# backend/app/models/ollama_provider.py
"""
Local Ollama Model Provider
Interacts with the offline Ollama HTTP API (http://localhost:11434).
Guarantees strictly local execution, explicit keep_alive control, and structured error handling.
"""

import json
from typing import AsyncIterator, Dict, List, Optional
from urllib.parse import urlparse
import httpx

from backend.app.config import settings
from backend.app.models.base import LLMProvider
from backend.app.models.types import (
    GenerationRequest,
    GenerationResponse,
    ModelExecutionError,
)


class OllamaProvider(LLMProvider):
    """
    Local Ollama API client providing async non-streaming and streaming generation.
    """

    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        connect_timeout: float = 10.0,
        generate_timeout: float = 180.0
    ):
        # Security invariant: Ensure endpoint is strictly localhost
        parsed = urlparse(base_url)
        hostname = (parsed.hostname or "").lower()
        if hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError(
                f"Security violation: Remote Ollama endpoints ({base_url}) are forbidden. "
                "Only local loopback (localhost/127.0.0.1) is permitted."
            )

        self.base_url = base_url.rstrip("/")
        self.connect_timeout = connect_timeout
        self.generate_timeout = generate_timeout

    def _get_client(self, timeout: Optional[float] = None) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                timeout or self.generate_timeout,
                connect=self.connect_timeout
            )
        )

    async def check_health(self) -> bool:
        """Check if local Ollama service is reachable and responsive."""
        try:
            async with self._get_client(timeout=5.0) as client:
                res = await client.get("/api/version")
                return res.status_code == 200
        except Exception:
            return False

    async def list_installed_models(self) -> List[str]:
        """List all models currently installed in local Ollama storage."""
        try:
            async with self._get_client(timeout=10.0) as client:
                res = await client.get("/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return [m for m in models if m]
                return []
        except Exception as e:
            raise ModelExecutionError(f"Failed to query Ollama models: {str(e)}") from e

    async def is_model_available(self, model_id: str) -> bool:
        """Check whether a specific model tag or base name is available locally."""
        installed = await self.list_installed_models()
        return any(
            m == model_id or m.startswith(f"{model_id}:") or model_id.startswith(f"{m}:")
            for m in installed
        )

    async def load_model(self, model_id: str, keep_alive: str = "5m") -> bool:
        """Preload a model into GPU memory via empty prompt."""
        try:
            async with self._get_client(timeout=self.generate_timeout) as client:
                payload = {
                    "model": model_id,
                    "prompt": "",
                    "keep_alive": keep_alive
                }
                res = await client.post("/api/generate", json=payload)
                return res.status_code == 200
        except Exception as e:
            raise ModelExecutionError(f"Failed to preload model '{model_id}': {str(e)}") from e

    async def unload_model(self, model_id: str) -> bool:
        """Immediately evict a model from VRAM by setting keep_alive to 0."""
        try:
            async with self._get_client(timeout=30.0) as client:
                payload = {
                    "model": model_id,
                    "keep_alive": 0
                }
                res = await client.post("/api/generate", json=payload)
                return res.status_code == 200
        except Exception as e:
            raise ModelExecutionError(f"Failed to unload model '{model_id}': {str(e)}") from e

    async def get_active_models(self) -> List[Dict[str, any]]:
        """Query currently active resident models in Ollama memory."""
        try:
            async with self._get_client(timeout=5.0) as client:
                res = await client.get("/api/ps")
                if res.status_code == 200:
                    data = res.json()
                    return data.get("models", [])
                return []
        except Exception:
            return []

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Execute a non-streaming completion request against local Ollama."""
        model_name = request.model or settings.REASONING_MODEL
        payload: Dict[str, any] = {
            "model": model_name,
            "prompt": request.prompt,
            "stream": False,
            "keep_alive": request.keep_alive or "5m",
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
            }
        }

        if request.system_prompt:
            payload["system"] = request.system_prompt
        if request.images:
            payload["images"] = request.images
        if request.format:
            payload["format"] = request.format
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        try:
            async with self._get_client() as client:
                res = await client.post("/api/generate", json=payload)
                if res.status_code != 200:
                    raise ModelExecutionError(
                        f"Ollama returned HTTP {res.status_code}: {res.text}"
                    )

                data = res.json()
                total_duration_ms = float(data.get("total_duration", 0)) / 1_000_000.0

                raw_response = data.get("response", "")
                raw_thinking = data.get("thinking", "")
                content = raw_response if raw_response.strip() else raw_thinking

                return GenerationResponse(
                    model=model_name,
                    content=content,
                    thinking=raw_thinking if raw_thinking else None,
                    total_duration_ms=round(total_duration_ms, 2),
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    done=data.get("done", True),
                    error=None
                )
        except httpx.TimeoutException as te:
            raise ModelExecutionError(
                f"Generation timed out after {self.generate_timeout}s on model '{model_name}'"
            ) from te
        except Exception as e:
            raise ModelExecutionError(
                f"Inference failed on model '{model_name}': {str(e)}"
            ) from e

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Execute a streaming generation request, yielding token chunks as strings."""
        model_name = request.model or settings.REASONING_MODEL
        payload: Dict[str, any] = {
            "model": model_name,
            "prompt": request.prompt,
            "stream": True,
            "keep_alive": request.keep_alive or "5m",
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
            }
        }

        if request.system_prompt:
            payload["system"] = request.system_prompt
        if request.images:
            payload["images"] = request.images
        if request.format:
            payload["format"] = request.format
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        try:
            async with self._get_client() as client:
                async with client.stream("POST", "/api/generate", json=payload) as response:
                    if response.status_code != 200:
                        err_body = await response.aread()
                        raise ModelExecutionError(
                            f"Ollama stream error {response.status_code}: {err_body.decode('utf-8')}"
                        )

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk_data = json.loads(line)
                        token = chunk_data.get("response") or chunk_data.get("thinking") or ""
                        if token:
                            yield token
                        if chunk_data.get("done", False):
                            break
        except Exception as e:
            raise ModelExecutionError(
                f"Streaming failed on model '{model_name}': {str(e)}"
            ) from e
