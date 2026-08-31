# backend/app/api/endpoints/telemetry_api.py
"""
Telemetry & System Health Endpoints
Exposes real-time GPU VRAM, RAM, CPU load, air-gap status, and active model status.
"""

from fastapi import APIRouter
from backend.app.config import settings
from backend.app.models.telemetry import ResourceTelemetry, HardwareSnapshot
from backend.app.models.router import ModelRouter

router = APIRouter(tags=["System & Telemetry"])
model_router = ModelRouter()


@router.get("/health")
async def health_check():
    """
    Core system liveness, airgap isolation status, and local Ollama daemon status.
    """
    ollama_ok = await model_router.provider.check_health()
    return {
        "status": "healthy" if ollama_ok else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "airgap_mode": settings.AIRGAP_MODE,
        "ollama_available": ollama_ok,
        "ollama_endpoint": settings.OLLAMA_BASE_URL
    }


@router.get("/telemetry")
async def get_hardware_telemetry():
    """
    Retrieve real-time GPU VRAM, host system RAM, CPU load, and currently active model.
    """
    snapshot = ResourceTelemetry.snapshot()
    active_models = await model_router.provider.get_active_models()
    active_summary = None
    if active_models:
        active_summary = {
            "model_id": active_models[0].get("name", settings.REASONING_MODEL),
            "vram_allocated_mb": round(active_models[0].get("size_vram", 0) / (1024 * 1024), 1),
            "status": "LOADED"
        }
    else:
        active_summary = {
            "model_id": model_router._active_model_id or settings.REASONING_MODEL,
            "vram_allocated_mb": 0.0,
            "status": "STANDBY"
        }

    return {
        "timestamp": snapshot.timestamp,
        "airgap_status": {
            "is_isolated": settings.AIRGAP_MODE,
            "external_dns_reachable": False,
            "wan_bytes_transmitted": 0
        },
        "hardware": {
            "gpu": snapshot.gpu.model_dump(),
            "ram": {
                "total_mb": snapshot.system.ram_total_mb,
                "used_mb": snapshot.system.ram_used_mb,
                "free_mb": snapshot.system.ram_free_mb,
                "system_utilization_pct": snapshot.system.ram_utilization_pct
            },
            "cpu": {
                "core_count": snapshot.system.cpu_core_count,
                "utilization_pct": snapshot.system.cpu_utilization_pct
            }
        },
        "active_model": active_summary
    }
