# SOVEREIGN-X — Phase 3 Local Model & VRAM Swapping Benchmark Report

---

## 1. Executive Hardware & Environment Summary
- **Host Machine**: Windows 11 64-bit Laptop
- **System Memory**: 16 GB DDR4/DDR5 (Used: `10748.7 MB`)
- **GPU Accelerator**: NVIDIA GeForce RTX 3050 Laptop GPU
- **Physical VRAM**: 4096.0 MB (4.0 GB)
- **Local Inference Engine**: Ollama 0.33.1 (100% Offline, `OLLAMA_NO_CLOUD=1`)
- **API Endpoint**: `http://localhost:11434` (Strict Local Loopback)

---

## 2. Real Hardware Performance Benchmark

| Metric / Parameter | `qwen3:4b` (Reasoning Core) | `gemma3:4b` (Vision Specialist) | Reverse Swap `qwen3:4b` |
| :--- | :--- | :--- | :--- |
| **Model Size on Disk** | 2.5 GB | 3.3 GB | 2.5 GB |
| **Modality Tested** | Text Reasoning / Risk Analysis | Multimodal Image Inspection | Text State Ack |
| **Total Wall-Clock Latency** | `6.52s` | `30.56s` | `9.31s` |
| **Model Generation Time** | `5169.7 ms` | `28778.6 ms` | `7540.3 ms` |
| **Completion Tokens** | `150` | `73` | `30` |
| **Throughput Speed** | `29.0 tokens/sec` | `2.5 tokens/sec` | — |
| **Active VRAM Usage** | `3365.2 MB` | `3567.5 MB` | `3375.3 MB` |
| **Resident Model in Ollama** | `qwen3:4b` | `gemma3:4b` | `qwen3:4b` |
| **Single-Model Residency?** | **YES (Gemma evicted)** | **YES (Qwen evicted)** | **YES (Gemma evicted)** |

---

## 3. VRAM Arbitrator & Model Swapping Verification
1. **Zero Simultaneous Co-Residency**: When transitioning from `qwen3:4b` to `gemma3:4b`, the `ModelRouter` explicitly evicted `qwen3:4b` (`keep_alive: 0`) before loading `gemma3:4b`. At no point did cumulative VRAM usage exceed the 4.0 GB physical boundary.
2. **Deterministic Modality Routing**: Text queries automatically routed to `qwen3:4b`, while requests bearing visual base64 image payloads routed directly to `gemma3:4b`.
3. **Strict Air-Gap Isolation**: All model executions executed against `http://localhost:11434` with zero WAN network egress.
