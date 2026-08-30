# backend/app/api/router.py
"""
Master API Router
Consolidates all modular endpoint routers under /api/v1.
"""

from fastapi import APIRouter
from backend.app.api.endpoints.agent_api import router as agent_router
from backend.app.api.endpoints.audit_api import router as audit_router
from backend.app.api.endpoints.models_api import router as models_router
from backend.app.api.endpoints.telemetry_api import router as telemetry_router
from backend.app.api.endpoints.workspace_api import router as workspace_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(telemetry_router)
api_router.include_router(models_router)
api_router.include_router(agent_router)
api_router.include_router(workspace_router)
api_router.include_router(audit_router)
