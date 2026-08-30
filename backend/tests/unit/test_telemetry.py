# backend/tests/unit/test_telemetry.py
"""
Unit Tests for Resource Telemetry Module
Validates live hardware snapshotting and graceful degradation.
"""

from backend.app.models.telemetry import ResourceTelemetry, HardwareSnapshot


def test_system_telemetry_gathering():
    """Test gathering host RAM and CPU load metrics."""
    sys_telem = ResourceTelemetry.get_system_telemetry()

    assert sys_telem.ram_total_mb > 0
    assert sys_telem.ram_used_mb > 0
    assert sys_telem.ram_free_mb > 0
    assert 0.0 <= sys_telem.ram_utilization_pct <= 100.0
    assert sys_telem.cpu_core_count >= 1


def test_gpu_telemetry_gathering():
    """Test GPU telemetry gathering (either live GPU or graceful fallback)."""
    gpu = ResourceTelemetry.get_gpu_telemetry()
    assert isinstance(gpu.available, bool)
    if gpu.available:
        assert gpu.vram_total_mb > 0
        assert gpu.vram_free_mb >= 0


def test_unified_hardware_snapshot():
    """Test full hardware snapshot structure."""
    snapshot = ResourceTelemetry.snapshot()
    assert isinstance(snapshot, HardwareSnapshot)
    assert snapshot.timestamp is not None
    assert snapshot.system.ram_total_mb > 0
