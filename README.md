# SOVEREIGN-X 🛡️⚡
### Sovereign On-Premise Agentic AI Workbench for Confidential Industrial Work
**Smart India Hackathon 2026 — Problem Statement SIH26117**

---

## 📌 Executive Summary
**SOVEREIGN-X** is an enterprise-grade, air-gapped, sovereign AI workbench designed for zero-trust, confidential industrial, defense, and manufacturing environments. Operating strictly on open-weight multimodal LLMs and local infrastructure, SOVEREIGN-X runs 100% offline on consumer-grade workstation/laptop hardware (single Windows 11 host with 16 GB RAM and NVIDIA RTX 3050 4 GB VRAM) without transmitting any telemetry, embeddings, or prompts to external cloud endpoints.

Unlike conversational chatbot interfaces or cloud API wrappers, SOVEREIGN-X implements an **Air-Gapped Agentic Execution Loop** governed by a deterministic **Security Policy Engine**, **Typed Tool Registry**, **Micro-Isolated Python Execution Sandbox**, and a **Provenance-Enforced RAG Subsystem** capable of deep technical document comprehension (PDFs, scanned blueprints, engineering tables, equipment imagery, and Excel sheets).

```
                      AIR-GAPPED SOVEREIGN BOUNDARY
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   [ React / Vite UI ] ──(REST/SSE)──> [ FastAPI Sovereign Core ]        │
│                                                   │                     │
│               ┌───────────────────────────────────┼─────────────┐       │
│               │                                   ▼             │       │
│               │                         [ Policy & Auth Guard ] │       │
│               │                                   │             │       │
│               │                                   ▼             │       │
│               │                       [ Agentic Orchestrator ]  │       │
│               │                             │         │         │       │
│               ▼                             ▼         ▼         │       │
│     [ Local Model Router ]          [ Tool Registry ] [ RAG ]   │       │
│       │ (Ollama 4GB VRAM)                   │         │ (Qdrant)│       │
│       ├── Qwen3 4B (Reasoning)              ▼         ▼         │       │
│       └── Gemma3 4B (Multimodal)      [ Isolated Docker ]       │       │
│                                         (Python Sandbox)        │       │
│                                                                 │       │
│   SQLite Metadata DB  │  Local Vault Storage  │  Audit Event Logger     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Target Hardware & System Footprint
SOVEREIGN-X is engineered for realistic execution on constrained laptop hardware:

| Component | Target Specification | SOVEREIGN-X Allocation / Design Limit |
| :--- | :--- | :--- |
| **Host OS** | Windows 11 64-bit | Local Native Host & Isolated Docker Backend |
| **CPU** | 4-8 Core Laptop x86_64 CPU | Quantized vector search, multithreaded OCR |
| **System RAM** | 16 GB DDR4/DDR5 | Peak process usage capped at ≤ 10 GB |
| **GPU & VRAM** | NVIDIA RTX 3050 Laptop (4 GB VRAM) | Dynamically swaps Qwen3:4B (2.5GB) / Gemma3:4B (3.3GB) |
| **CUDA Driver** | NVIDIA Driver 610.62 / CUDA UMD 13.3 | GPU-accelerated local inference via Ollama v0.33.1+ |
| **Storage** | 512 GB NVMe SSD | SQLite + Qdrant Embedded / Local Docker Volume |
| **Networking** | Offline / Air-Gapped (Wi-Fi OFF, No WAN) | Zero external network calls; localhost socket binding only |

---

## 🚀 Core Capabilities

1. **Deterministic Air-Gapped Operation (`OLLAMA_NO_CLOUD=1`)**:
   - Zero outbound WAN connections. All embeddings, OCR, visual document parsing, code execution, and inference happen locally.
2. **Resource-Aware Dynamic Model Router**:
   - Manages strict 4 GB VRAM headroom by routing text reasoning tasks to `qwen3:4b` (2.5 GB) and visual/multimodal inspection to `gemma3:4b` (3.3 GB), utilizing explicit memory eviction when necessary.
3. **Multi-Format Technical Document Ingestion**:
   - Dual-engine parsing for text and scanned documents using PyMuPDF and local OCR (Tesseract / PaddleOCR-light).
   - Spreadsheet engine (`openpyxl` / `pandas`) and technical imagery inspector.
4. **Provenance & Citation Enforced RAG Engine**:
   - Local dense vector retrieval powered by fast local embeddings (e.g., `bge-small-en-v1.5` / `all-MiniLM-L6-v2`) and Qdrant.
   - Every response links findings directly to document ID, page number, section header, and bounding box.
5. **Zero-Trust Tool Execution & Isolated Python Sandbox**:
   - LLMs never touch the host operating system. Sensitive code runs in an isolated ephemeral Docker container (`--net=none`, memory limit 512MB, CPU cap, non-root user, read-only mounts).
6. **Immutable Audit Trails & Telemetry**:
   - SHA-256 hash-chained JSON-Lines event audit logging recording all prompts, policy checks, tool invocations, and artifact generations.
7. **Industrial Document Generation**:
   - Generates production-ready DOCX and PPTX compliance summaries and engineering approval notes directly from verified findings.

---

## 📚 Complete Architecture Documentation Suite

Explore the system architecture, security specifications, and operational guides:

| Document | Purpose |
| :--- | :--- |
| **[docs/architecture.md](docs/architecture.md)** | Full System Architecture, Component Topologies, Dataflow & Invariants |
| **[docs/repository-structure.md](docs/repository-structure.md)** | Directory Layout, Layer Boundaries, Module Contracts |
| **[docs/api-contract.md](docs/api-contract.md)** | REST API Endpoints, OpenAPI Schemas, SSE Streaming Events |
| **[docs/database-design.md](docs/database-design.md)** | SQLite Schema, Vector DB Collections, Migrations & Indexing |
| **[docs/model-strategy.md](docs/model-strategy.md)** | Model Registry, VRAM Allocation, Ollama Orchestration & Fallback |
| **[docs/rag-design.md](docs/rag-design.md)** | Chunking Strategies, Local Embeddings, Retrieval Pipeline & Citations |
| **[docs/agent-design.md](docs/agent-design.md)** | ReAct Agent Loop, State Machine, Iteration Limits & Human Approvals |
| **[docs/tool-security.md](docs/tool-security.md)** | Tool Registry, Schema Validation, Policy Engine & Risk Levels |
| **[docs/sandbox-design.md](docs/sandbox-design.md)** | Docker Sandbox, Security Hardening, Resource Limits & IO Controls |
| **[docs/threat-model.md](docs/threat-model.md)** | STRIDE Assessment, Prompt Injection Defense, Path Traversal, Exfiltration |
| **[docs/offline-architecture.md](docs/offline-architecture.md)** | Air-Gap Guarantee, Offline Verification, Local Telemetry & Hardware State |
| **[docs/demo-workflow.md](docs/demo-workflow.md)** | Flagship Multi-Asset Industrial Inspection & Compliance Walkthrough |
| **[docs/testing-strategy.md](docs/testing-strategy.md)** | Unit, Integration, Security, and Offline Performance Test Suites |
| **[docs/deployment.md](docs/deployment.md)** | Single-Laptop Windows 11 Setup, Docker Packaging & Runbook |
| **[docs/roadmap.md](docs/roadmap.md)** | Hackathon MVP Milestones vs Post-Hackathon Enterprise Extensions |
| **[docs/architecture-review.md](docs/architecture-review.md)** | Rigorous Peer Review, Bottleneck Analysis & Risk Mitigations |

---

## 🏆 Flagship Use-Case: Industrial Multi-Asset Inspection Package
SOVEREIGN-X is benchmarked on a complex industrial inspection workflow:
- **Input Assets**: Mechanical Inspection PDF, Scanned NDT Ultrasonic Report, Equipment Surface Crack JPG, Maintenance History XLSX, Equipment Maintenance Manual PDF.
- **Task**: Cross-correlate wear measurements with historical degradation rates, verify OEM tolerance thresholds from the manual, assess failure probability, and draft an **Engineering Approval Note (.docx)** with exact page citations and verifiable evidence.
- **Guarantee**: Entire sequence completes locally in under 3 minutes on RTX 3050 (4 GB VRAM) with zero cloud network traffic.

---

## 🛡️ License & Compliance
Designed and developed for Smart India Hackathon 2026. Built in adherence to zero-trust sovereign AI standards for defense, aerospace, and industrial manufacturing sectors.
