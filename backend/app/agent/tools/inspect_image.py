# backend/app/agent/tools/inspect_image.py
"""
Inspect Image Tool
Integrates directly with Phase 3 ModelRouter to execute multimodal vision inspection
using the local gemma3:4b open-weight model with automatic VRAM arbitration.
"""

import base64
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from backend.app.agent.tools.base import (
    BaseTool,
    ToolDefinition,
    ToolRiskLevel,
    resolve_secure_workspace_path,
)
from backend.app.config import settings
from backend.app.models.router import ModelRouter
from backend.app.models.types import GenerationRequest


class InspectImageInput(BaseModel):
    image_filename: str = Field(..., description="Relative path of the image inside the workspace")
    inspection_prompt: str = Field(
        "Inspect this industrial engineering image for flaws, cracks, weld anomalies, or equipment details.",
        description="Detailed prompt instructing the multimodal model what to analyze"
    )


class InspectImageOutput(BaseModel):
    image_filename: str
    visual_findings: str
    model_used: str
    total_duration_ms: float


class InspectImageTool(BaseTool):
    def __init__(self, model_router: Optional[ModelRouter] = None):
        self.model_router = model_router or ModelRouter()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="inspect_image",
            description="Inspect an engineering drawing, photo, or scan using the local multimodal vision model (Gemma 3).",
            input_schema=InspectImageInput,
            output_schema=InspectImageOutput,
            risk_level=ToolRiskLevel.MEDIUM,
            required_permissions=["workspace:read", "model:vision"],
            requires_human_approval=False
        )

    async def execute(self, workspace_id: str, input_data: InspectImageInput) -> InspectImageOutput:
        target_path = resolve_secure_workspace_path(
            workspace_id=workspace_id,
            relative_path=input_data.image_filename,
            must_exist=True
        )

        try:
            with open(target_path, "rb") as img_file:
                image_bytes = img_file.read()
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to read image '{input_data.image_filename}': {str(e)}") from e

        # Formulate multimodal request
        req = GenerationRequest(
            model=settings.VISION_MODEL,
            prompt=input_data.inspection_prompt,
            images=[image_b64],
            temperature=0.1,
            max_tokens=300
        )

        res = await self.model_router.generate(req)

        return InspectImageOutput(
            image_filename=input_data.image_filename,
            visual_findings=res.content,
            model_used=res.model,
            total_duration_ms=res.total_duration_ms
        )
