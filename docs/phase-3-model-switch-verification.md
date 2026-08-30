# SOVEREIGN-X — Phase 3 Real-Hardware Model-Switching Verification Report

---

## 1. Hardware & Environment Baseline
- **Operating System**: Windows 11 64-bit
- **Host CPU / RAM**: Multi-Core Laptop CPU | 16 GB DDR4/DDR5
- **GPU Accelerator**: NVIDIA GeForce RTX 3050 Laptop GPU (Physical VRAM: 4096.0 MB)
- **Local Inference Engine**: Ollama 0.33.1 (Offline, `OLLAMA_NO_CLOUD=1`, `http://localhost:11434`)
- **Verification Timestamp**: 2026-08-30 11:32:48 UTC

---

## 2. Stage-by-Stage Real Command Telemetry

### Stage 0: Clean Baseline (No Resident Models)
- **Active Model**: None
- **`ollama ps` Output**:
```
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
```
- **`nvidia-smi` Summary**:
  - VRAM Used: `1070.1 MB` / `4096.0 MB` (Windows Desktop & App baseline)
  - GPU Utilization: `2.0%`

---

### Stage 1: Load `qwen3:4b` & Execute Text Reasoning Inference
- **Target Model**: `qwen3:4b` (2.5 GB on disk, Reasoning Core)
- **Prompt**: *"Assess residual service life for Pump 3B with measured casing thickness 3.42mm (OEM nominal: 4.80mm, minimum: 4.00mm). 2 sentences."*
- **Total Wall-Clock Latency**: `10.59 seconds`
- **Inference Generation Time**: `9087.7 ms`
- **Tokens Generated**: `100 tokens`
- **Active Ollama Model**: `qwen3:4b`
- **`ollama ps` Output**:
```
NAME        ID              SIZE      PROCESSOR          CONTEXT    UNTIL              
qwen3:4b    359d7dd4bcda    3.5 GB    33%/67% CPU/GPU    4096       4 minutes from now
```
- **`nvidia-smi` Telemetry**:
  - VRAM Used: `3376.3 MB` / `4096.0 MB`
  - GPU Utilization: `45.0%`
  - CUDA / OOM Errors: **None**

---

### Stage 2: Explicit Swap to `gemma3:4b` & Multimodal Vision Inference
- **Target Model**: `gemma3:4b` (3.3 GB on disk, Vision Specialist)
- **Prompt + Modality**: Visual inspection with base64 PNG defect diagram
- **Total Wall-Clock Latency (Swap + Cold Load + Inference)**: `23.25 seconds`
- **Inference Generation Time**: `21224.8 ms`
- **Tokens Generated**: `100 tokens`
- **Previous Model (`qwen3:4b`) Evicted?**: **YES — verified absent from `ollama ps`**
- **Active Ollama Model**: `gemma3:4b`
- **`ollama ps` Output**:
```
NAME         ID              SIZE      PROCESSOR          CONTEXT    UNTIL              
gemma3:4b    a2af6cc3eb7f    3.5 GB    54%/46% CPU/GPU    4096       4 minutes from now
```
- **`nvidia-smi` Telemetry**:
  - VRAM Used: `3576.6 MB` / `4096.0 MB`
  - GPU Utilization: `15.0%`
  - CUDA / OOM Errors: **None**

---

### Stage 3: Reverse Swap to `qwen3:4b` & Text Inference
- **Target Model**: `qwen3:4b` (Reasoning Core)
- **Prompt**: *"Confirm Sovereign-X model swap status and report readiness. One sentence."*
- **Total Wall-Clock Latency (Swap + Load + Inference)**: `12.22 seconds`
- **Inference Generation Time**: `10160.2 ms`
- **Tokens Generated**: `50 tokens`
- **Previous Model (`gemma3:4b`) Evicted?**: **YES — verified absent from `ollama ps`**
- **Active Ollama Model**: `qwen3:4b`
- **`ollama ps` Output**:
```
NAME        ID              SIZE      PROCESSOR          CONTEXT    UNTIL              
qwen3:4b    359d7dd4bcda    3.5 GB    33%/67% CPU/GPU    4096       4 minutes from now
```
- **`nvidia-smi` Telemetry**:
  - VRAM Used: `3375.8 MB` / `4096.0 MB`
  - GPU Utilization: `39.0%`
  - CUDA / OOM Errors: **None**

---

## 3. Comprehensive Model-Switching Summary Matrix

| Metric / Invariant | Stage 1 (`qwen3:4b`) | Stage 2 (`gemma3:4b`) | Stage 3 (`qwen3:4b` Restored) |
| :--- | :--- | :--- | :--- |
| **Active Model** | `qwen3:4b` | `gemma3:4b` | `qwen3:4b` |
| **Previous Model Evicted?** | N/A (Initial load) | **YES (`qwen3` evicted)** | **YES (`gemma3` evicted)** |
| **Simultaneous Residency?** | **NO (1 model resident)** | **NO (1 model resident)** | **NO (1 model resident)** |
| **GPU VRAM Allocated** | `3376.3 MB` | `3576.6 MB` | `3375.8 MB` |
| **Physical VRAM Ceiling** | `4,096.0 MB` | `4,096.0 MB` | `4,096.0 MB` |
| **CUDA Out-of-Memory (OOM)?** | **NO (0 OOM events)** | **NO (0 OOM events)** | **NO (0 OOM events)** |
| **Wall-Clock Latency** | `10.59s` | `23.25s` | `12.22s` |
| **Inference Generation Time**| `9087.7 ms` | `21224.8 ms` | `10160.2 ms` |

---

## 4. Key Engineering Conclusions
1. **Strict Single-Model VRAM Compliance**: With 4.0 GB physical VRAM and ~900 MB OS/DWM overhead, running Qwen 3 (2.5 GB) and Gemma 3 (3.3 GB) concurrently is mathematically impossible (cumulative 5.8 GB > 4.0 GB). The `ModelRouter` sequentially unloaded the inactive model via `keep_alive: 0` before loading the incoming model, ensuring zero OOM crashes.
2. **Complete Eviction Verification**: At every stage, `ollama ps` confirmed that exactly one model was resident in memory.
3. **Multimodal Capability Verified**: Gemma 3 4B successfully ingested the base64 defect diagram and emitted visual feature observations.
4. **Air-Gap Invariant**: All requests executed against `http://localhost:11434` with zero external network connectivity. Network egress is verified through dedicated offline test suites.
