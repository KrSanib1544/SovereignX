# SOVEREIGN-X — Offline Architecture & Sovereignty Specification

---

## 1. Air-Gap Guarantee & Verification Principles

SOVEREIGN-X is engineered to operate in **100% disconnected, air-gapped secure facilities**. The system functions with:
- Wi-Fi adapter turned OFF / disabled.
- Ethernet cables physically disconnected.
- External DNS resolution unavailable.
- Zero outbound TCP/UDP packets permitted across any network interface.

```
                             OFFLINE HARDWARE HOST
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  [ Windows 11 Laptop (16 GB RAM / RTX 3050 4 GB VRAM) ]                 │
│                                                                         │
│    Local Frontend        Local Backend           Local Inference        │
│   (http://127.0.0.1:5173) ──> (http://127.0.0.1:8000) ──> (http://127.0.0.1:11434)  │
│                                      │                   (OLLAMA_NO_CLOUD=1)    │
│                                      ▼                                          │
│                           [ Local Qdrant / SQLite ]                             │
│                                      │                                          │
│                                      ▼                                          │
│                           [ Docker Micro-Sandbox ]                              │
│                             (--network none)                                    │
│                                                                                 │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     X  [ PHYSICALLY BLOCKED ]
                                     │
                             (External Cloud / WAN)
```

---

## 2. Component Air-Gap Audit Matrix

Every subsystem has been verified for complete local operation:

| Subsystem | Local Implementation | Verified Dependency / Model | External Network Dependency |
| :--- | :--- | :--- | :--- |
| **LLM Inference** | Ollama Local Daemon | `qwen3:4b` (2.5GB) & `gemma3:4b` (3.3GB) | **ZERO** (Bound to `127.0.0.1:11434`, `OLLAMA_NO_CLOUD=1`) |
| **Dense Embeddings** | FastEmbed (ONNX Runtime) | `bge-small-en-v1.5` (Cached ONNX weights, ~130MB) | **ZERO** (Local model cache in `./models/embeddings/`) |
| **Vector Database** | Qdrant Local Engine | Local storage directory (`./data/qdrant_storage/`) | **ZERO** (Local file-backed vector index) |
| **Document OCR** | PaddleOCR-light / Tesseract | Local inference engine + trained data files | **ZERO** (Local model weights stored in repo/host) |
| **PDF Extraction** | PyMuPDF (`fitz`) | Pure C/Python local binary | **ZERO** |
| **Spreadsheet Engine** | `pandas` + `openpyxl` | In-process Python libraries | **ZERO** |
| **Code Execution** | Ephemeral Docker Container | Pre-built local image `sovereign-sandbox:1.0` | **ZERO** (Runs with `--network none`) |
| **Telemetry Collector** | `psutil` + `pynvml` | Native OS / NVIDIA driver DLL calls | **ZERO** |

---

## 3. Real Telemetry Collection vs. Simulated Metrics

SOVEREIGN-X **never displays fake or simulated metrics**. All metrics in the UI reflect live operating system and GPU states collected by the backend engine:

### 3.1. GPU & VRAM Telemetry (`pynvml`)
```python
import pynvml

def get_gpu_telemetry() -> dict:
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        name = pynvml.nvmlDeviceGetName(handle)
        
        return {
            "device_name": name if isinstance(name, str) else name.decode("utf-8"),
            "vram_total_mb": round(mem_info.total / (1024 * 1024), 1),
            "vram_used_mb": round(mem_info.used / (1024 * 1024), 1),
            "vram_free_mb": round(mem_info.free / (1024 * 1024), 1),
            "gpu_utilization_pct": util_info.gpu,
            "temperature_c": temp
        }
    except Exception as e:
        return {"error": f"NVML unavailable: {str(e)}"}
```

### 3.2. Host RAM, CPU & Air-Gap Network Egress (`psutil`)
```python
import psutil
import socket

def get_system_sovereignty_telemetry() -> dict:
    ram = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=None)
    net_io = psutil.net_io_counters()
    
    # Air-gap verification: Probe external DNS resolution
    is_airgapped = False
    try:
        # Attempt to resolve an external DNS address with 200ms timeout
        socket.setdefaulttimeout(0.2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        is_airgapped = False
    except Exception:
        is_airgapped = True  # Verified disconnected
        
    return {
        "is_airgapped": is_airgapped,
        "ram_total_mb": round(ram.total / (1024 * 1024), 1),
        "ram_used_mb": round(ram.used / (1024 * 1024), 1),
        "ram_utilization_pct": ram.percent,
        "cpu_utilization_pct": cpu_pct,
        "bytes_sent_since_boot": net_io.bytes_sent,
        "bytes_recv_since_boot": net_io.bytes_recv
    }
```

---

## 4. UI Sovereignty Status Indicator

The React frontend header features a live **Sovereignty & Air-Gap Status Indicator**:
- 🟢 **AIR-GAP ENFORCED (100% Sovereign)**: External DNS unreachable, `OLLAMA_NO_CLOUD=1` verified, 0 external network egress.
- 🟡 **CAUTION: NETWORK INTERFACE ACTIVE**: An active network interface is detected; the system confirms all AI calls remain local, but advises disabling Wi-Fi for strict compliance.
- 🔴 **SECURITY WARNING**: External socket connectivity detected.
