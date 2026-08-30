# backend/app/api/endpoints/models_api.py
"""
Models API Endpoints
Exposes model listing, active health, explicit VRAM swap, and local generation/streaming.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.models.router import ModelRouter
from backend.app.models.types import (
    GenerationRequest,
    GenerationResponse,
    ModelHealthStatus,
    ModelResourceError,
    ModelExecutionError,
)

router = APIRouter(prefix="/models", tags=["Models"])
model_router = ModelRouter()


class SwapModelRequest(BaseModel):
    target_model_id: str


@router.get("", response_model=List[ModelHealthStatus])
async def list_models():
    """
    List registered local models, their capabilities, and current VRAM residency state.
    """
    try:
        return await model_router.get_model_health_list()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query model health: {str(e)}"
        )


@router.post("/swap", response_model=ModelHealthStatus)
async def swap_model(request: SwapModelRequest):
    """
    Force an explicit model swap and VRAM eviction of inactive models.
    """
    try:
        return await model_router.force_swap(request.target_model_id)
    except ModelResourceError as mre:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "type": "https://sovereign-ai.local/errors/vram-exhaustion",
                "title": "GPU VRAM Allocation Limit Exceeded",
                "detail": str(mre),
                "error_code": mre.error_code
            }
        )
    except ModelExecutionError as mee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(mee)
        )


@router.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    """
    Execute non-streaming local inference with deterministic routing and VRAM safety.
    """
    try:
        return await model_router.generate(request)
    except ModelResourceError as mre:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(mre)
        )
    except ModelExecutionError as mee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(mee)
        )


@router.post("/generate/stream")
async def generate_stream(request: GenerationRequest):
    """
    Execute streaming local inference yielding Server-Sent Events (SSE).
    """
    try:
        async def event_generator():
            async for token in model_router.generate_stream(request):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
