# backend/app/models/telemetry.py
"""
Hardware & System Resource Telemetry
Measures actual GPU VRAM, system RAM, CPU load, and hardware availability.
Provides graceful degradation if NVML is not present.
"""

import os
from typing import Any, Dict, Optional, Tuple
import psutil
from pydantic import BaseModel


class GpuTelemetry(BaseModel):
    available: bool = False
    device_name: str = "N/A"
    vram_total_mb: float = 0.0
    vram_used_mb: float = 0.0
    vram_free_mb: float = 0.0
    gpu_utilization_pct: float = 0.0
    temperature_c: Optional[int] = None
    driver_version: Optional[str] = None


class SystemTelemetry(BaseModel):
    ram_total_mb: float
    ram_used_mb: float
    ram_free_mb: float
    ram_utilization_pct: float
    cpu_utilization_pct: float
    cpu_core_count: int


class HardwareSnapshot(BaseModel):
    timestamp: str
    gpu: GpuTelemetry
    system: SystemTelemetry


class ResourceTelemetry:
    """
    Real-time hardware profiler and telemetry collector.
    """

    _nvml_initialized: bool = False
    _nvml_handle: Any = None

    @classmethod
    def _init_nvml(cls) -> bool:
        """Initialize NVML subsystem once."""
        if cls._nvml_initialized:
            return cls._nvml_handle is not None
        try:
            try:
                import pynvml
                pynvml.nvmlInit()
                cls._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                cls._nvml_initialized = True
                return True
            except ImportError:
                import nvidia_ml_py as pynvml
                pynvml.nvmlInit()
                cls._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                cls._nvml_initialized = True
                return True
        except Exception:
            cls._nvml_initialized = True
            cls._nvml_handle = None
            return False

    @classmethod
    def get_gpu_telemetry(cls) -> GpuTelemetry:
        """Collect live GPU VRAM, utilization, and temperature."""
        if not cls._init_nvml() or cls._nvml_handle is None:
            return GpuTelemetry(
                available=False,
                device_name="No NVML / CUDA GPU detected",
                vram_total_mb=0.0,
                vram_used_mb=0.0,
                vram_free_mb=0.0,
                gpu_utilization_pct=0.0
            )

        try:
            try:
                import pynvml
            except ImportError:
                import nvidia_ml_py as pynvml

            handle = cls._nvml_handle
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode("utf-8")

            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except Exception:
                temp = None

            try:
                driver = pynvml.nvmlSystemGetDriverVersion()
                if isinstance(driver, bytes):
                    driver = driver.decode("utf-8")
            except Exception:
                driver = None

            return GpuTelemetry(
                available=True,
                device_name=name,
                vram_total_mb=round(mem.total / (1024 * 1024), 1),
                vram_used_mb=round(mem.used / (1024 * 1024), 1),
                vram_free_mb=round(mem.free / (1024 * 1024), 1),
                gpu_utilization_pct=float(util.gpu),
                temperature_c=temp,
                driver_version=driver
            )
        except Exception:
            return GpuTelemetry(
                available=False,
                device_name="GPU Telemetry Error",
                vram_total_mb=0.0,
                vram_used_mb=0.0,
                vram_free_mb=0.0,
                gpu_utilization_pct=0.0
            )

    @classmethod
    def get_system_telemetry(cls) -> SystemTelemetry:
        """Collect host RAM and CPU utilization."""
        vmem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        cores = psutil.cpu_count(logical=True) or 1

        return SystemTelemetry(
            ram_total_mb=round(vmem.total / (1024 * 1024), 1),
            ram_used_mb=round(vmem.used / (1024 * 1024), 1),
            ram_free_mb=round(vmem.available / (1024 * 1024), 1),
            ram_utilization_pct=vmem.percent,
            cpu_utilization_pct=cpu_pct,
            cpu_core_count=cores
        )

    @classmethod
    def snapshot(cls) -> HardwareSnapshot:
        """Capture unified timestamped hardware telemetry snapshot."""
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        return HardwareSnapshot(
            timestamp=now_iso,
            gpu=cls.get_gpu_telemetry(),
            system=cls.get_system_telemetry()
        )
