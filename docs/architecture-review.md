# SOVEREIGN-X — Architectural Peer Review & Risk Assessment

---

## 1. Executive Evaluation Summary

This document performs a comprehensive critical review of the SOVEREIGN-X system design against the target constraints:
1. **Target Hardware**: Single Windows 11 host with **16 GB RAM** and **NVIDIA RTX 3050 Laptop GPU (4 GB VRAM)**.
2. **Operational Constraint**: 100% Air-Gapped / Disconnected runtime (`OLLAMA_NO_CLOUD=1`).
3. **Domain Requirement**: High-consequence industrial, defense, and manufacturing compliance.
4. **Hackathon Feasibility**: Maintainable and demonstrable by a focused student engineering team for **Smart India Hackathon 2026 (SIH26117)**.

---

## 2. Architectural Strengths

1. **Hardware-Realistic Model Selection**:
   - Choosing `qwen3:4b` (~2.5 GB VRAM) and `gemma3:4b` (~3.3 GB VRAM) ensures that the models run fast (~20–35 tokens/sec) on consumer RTX 3050 mobile silicon.
   - Rejecting 14B/32B/70B models eliminates unmanageable CPU RAM offloading latency (which would reduce speed to $< 1.5\text{ tok/s}$).
2. **Explicit VRAM Swapping Arbitrator**:
   - The architecture does not assume both models can reside concurrently in 4 GB VRAM. Explicit unloading (`keep_alive=0`) prevents CUDA OOM crashes.
3. **Zero-Trust Tool Execution Model**:
   - LLMs are completely walled off from the host operating system. Shell execution is prohibited; Python code executes in an ephemeral Docker micro-container with `--network none` and strict memory limits.
4. **Verifiable Citations & Provenance**:
   - By embedding document IDs, page numbers, and bounding boxes directly into chunk payloads, the system prevents generative hallucinations from entering safety-critical compliance reports.
5. **Radical Architectural Simplicity**:
   - Avoiding heavy enterprise middleware (Postgres, Redis, Kafka, Kubernetes, Elasticsearch) in favor of SQLite WAL, Qdrant local storage, and FastAPI keeps memory consumption under 8.5 GB RAM total, easily fitting within the 16 GB budget.

---

## 3. Critical Resource & Bottleneck Analysis

### 3.1. 16 GB System RAM Validation
- **Windows 11 OS Baseline**: ~4.0 GB
- **Ollama Engine & Model Weights**: ~3.5 GB
- **FastAPI Core & FastEmbed (CPU ONNX)**: ~1.5 GB
- **Qdrant Vector Engine (In-Memory HNSW)**: ~0.8 GB
- **Docker Sandbox Container Cap**: ~0.5 GB
- **Total Peak Utilization**: $\approx 10.3\text{ GB}$ ($\le 65\%$ of 16 GB).
- **Verdict**: **SAFE & VERIFIED**. Ample headroom remains for disk caching and multi-tab browser rendering.

### 3.2. 4.0 GB GPU VRAM Validation
- **Windows DWM / Display Overhead**: ~550 MB – 700 MB
- **Available GPU VRAM**: ~3,350 MB – 3,500 MB
- **Peak Model Footprint**:
  - `qwen3:4b`: 2,560 MB $\rightarrow$ Fits comfortably with ~800 MB buffer.
  - `gemma3:4b`: 3,350 MB $\rightarrow$ Tight fit (~100 MB buffer).
- **Risk Mitigation**: The backend model manager must monitor `pynvml` free VRAM before loading `gemma3:4b`. If free VRAM is $< 3,300\text{ MB}$, it must force-kill stale CUDA contexts.

---

## 4. Security & Vulnerability Analysis

| Risk Area | Threat Level | Architectural Mitigation | Status |
| :--- | :--- | :--- | :--- |
| **Indirect Prompt Injection** (Hidden text in PDFs) | HIGH | Document text is quarantined inside `<untrusted_document_context>` XML tags. Tool invocation is gated by strict Pydantic schemas and a deterministic Policy Engine. | **MITIGATED** |
| **Path Traversal / Host Escape** | HIGH | `resolve_secure_workspace_path()` checks reject any relative paths containing `..`, absolute drive letters, or symlinks. | **MITIGATED** |
| **Container Escape / Fork Bomb** | MEDIUM | Docker sandbox runs `--cap-drop=ALL`, `--security-opt=no-new-privileges`, `pids-limit=64`, `--read-only`, and non-root user `10001`. | **MITIGATED** |
| **Data Exfiltration** | LOW | `--network none` on sandbox, local socket binding (`127.0.0.1`), `OLLAMA_NO_CLOUD=1`. Physical air-gap verification. | **MITIGATED** |

---

## 5. Potential Single Points of Failure & Simplifications

1. **Ollama Daemon Dependency**:
   - *Risk*: If the Ollama background process crashes or hangs during model swapping, API calls will stall.
   - *Mitigation*: Implement a health-check watchdog with automatic retry and subprocess restart capabilities in `OllamaProvider`.
2. **Docker Requirement on Windows 11**:
   - *Risk*: On some corporate laptops, Docker Desktop cannot be installed or WSL2 is disabled by group policy.
   - *Mitigation*: Provide a secondary `SubprocessSandbox` fallback using native Windows Restricted Job Objects for environments where Docker is unavailable.
3. **Heavy OCR Frameworks**:
   - *Risk*: Standard PaddleOCR can drag in heavy PyTorch dependencies that consume excessive disk space and RAM.
   - *Mitigation*: Use lightweight `tesseract` or quantized ONNX OCR models (`paddleocr-light` via ONNX Runtime) to keep RAM usage low.

---

## 6. MVP Scope vs. Post-Hackathon Recommendations

```
+---------------------------------------------------------------------------------------------+
|                                    MVP SCOPE (SIH 2026)                                     |
+---------------------------------------------------------------------------------------------+
 * Local Ollama Provider (Qwen3 4B & Gemma3 4B with VRAM swap arbitrator)
 * SQLite (WAL) metadata + Qdrant local vector search
 * Local ONNX embeddings (`bge-small-en-v1.5`) via FastEmbed
 * PyMuPDF parser + Local OCR + openpyxl spreadsheet analyzer
 * 10 Typed Tools + Ephemeral Docker Sandbox (`--network none`)
 * ReAct Agent loop (Max 15 steps, loop guard, HITL approval gate)
 * Immutable SHA-256 hash-chained audit logging
 * React 19 Frontend (Command Center, AI Workspace, Vault, Split Evidence Viewer, Telemetry)
 * Flagship 5-Asset Industrial Inspection Package Demo
+---------------------------------------------------------------------------------------------+
                                              │
                                              ▼
+---------------------------------------------------------------------------------------------+
|                                  POST-HACKATHON EXTENSIONS                                  |
+---------------------------------------------------------------------------------------------+
 * Multi-GPU distributed inference (vLLM / TensorRT-LLM)
 * Hardware Security Module (HSM / TPM 2.0) signed audit logs
 * Distributed multi-tenant RBAC with Active Directory / LDAP integration
 * Real-time audio transcription for field technician verbal inspection logs
+---------------------------------------------------------------------------------------------+
```
