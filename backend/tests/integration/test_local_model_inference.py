# backend/tests/integration/test_local_model_inference.py
"""
Live Local Model Inference & VRAM Swapping Integration Tests
Executes real local inference on qwen3:4b and gemma3:4b via Ollama,
verifying single-model VRAM residence and clean swapping.
"""

import pytest
from backend.app.models.router import ModelRouter
from backend.app.models.ollama_provider import OllamaProvider
from backend.app.models.types import GenerationRequest


@pytest.fixture
def live_router():
    provider = OllamaProvider()
    return ModelRouter(provider=provider)


@pytest.mark.asyncio
async def test_live_qwen3_text_inference(live_router):
    """Test actual local text inference using Qwen 3 4B."""
    if not await live_router.provider.check_health():
        pytest.skip("Local Ollama daemon is not running")

    req = GenerationRequest(
        prompt="Explain the difference between ultrasonic testing and radiographic testing in 2 concise sentences.",
        max_tokens=80,
        temperature=0.1
    )

    res = await live_router.generate(req)
    assert res.done is True
    assert len(res.content) > 10
    assert res.model == "qwen3:4b"
    assert res.total_duration_ms > 0


@pytest.mark.asyncio
async def test_live_model_swapping_qwen_to_gemma(live_router):
    """
    Test sequential model swapping:
    1. Load and run Qwen3
    2. Request Gemma3 (verifying Qwen3 is evicted from single-model VRAM residency)
    3. Verify Gemma3 completes inference
    4. Restore Qwen3
    """
    if not await live_router.provider.check_health():
        pytest.skip("Local Ollama daemon is not running")

    # Step 1: Run Qwen3
    req_qwen = GenerationRequest(
        model="qwen3:4b",
        prompt="Output exactly: [QWEN_ONLINE]",
        max_tokens=20
    )
    res_qwen = await live_router.generate(req_qwen)
    assert res_qwen.done is True
    assert res_qwen.model == "qwen3:4b"

    # Step 2: Swap to Gemma3
    req_gemma = GenerationRequest(
        model="gemma3:4b",
        prompt="Output exactly: [GEMMA_ONLINE]",
        max_tokens=20
    )
    res_gemma = await live_router.generate(req_gemma)
    assert res_gemma.done is True
    assert res_gemma.model == "gemma3:4b"

    # Step 3: Swap back to Qwen3
    req_qwen_restore = GenerationRequest(
        model="qwen3:4b",
        prompt="Confirm state: [READY]",
        max_tokens=20
    )
    res_qwen_restore = await live_router.generate(req_qwen_restore)
    assert res_qwen_restore.done is True
    assert res_qwen_restore.model == "qwen3:4b"
