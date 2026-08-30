# SOVEREIGN-X — Development Roadmap & Milestone Schedule

---

## 1. Roadmap Overview & Timeline

SOVEREIGN-X is scheduled for development in structured, test-driven phases tailored for Smart India Hackathon 2026 (SIH26117):

```
+-------------------------------------------------------------------------------------------------------------+
|                                        SIH 2026 MVP DEVELOPMENT TIMELINE                                    |
+-------------------------------------------------------------------------------------------------------------+
 [Phase 1: Architecture] ──> [Phase 2: Ingestion/RAG] ──> [Phase 3: Sandbox/Tools] ──> [Phase 4: Agent Core]
        (Complete)                (Sprint 1)                   (Sprint 2)                   (Sprint 3)
                                                                                                  │
                                                                                                  ▼
 [Phase 7: Enterprise] <── [Phase 6: Flagship Demo] <── [Phase 5: React Frontend] <───────────────┘
     (Post-Hackathon)             (Sprint 5)                   (Sprint 4)
```

---

## 2. Phase Breakdown & Deliverables

### Phase 1: Architecture & Security Specifications (CURRENT)
- [x] Complete system architecture document (`docs/architecture.md`)
- [x] Monorepo repository design (`docs/repository-structure.md`)
- [x] REST & SSE API contract (`docs/api-contract.md`)
- [x] SQLite & Qdrant database schema (`docs/database-design.md`)
- [x] Model strategy & 4 GB VRAM swapping arbitrator (`docs/model-strategy.md`)
- [x] Ingestion & local RAG pipeline specification (`docs/rag-design.md`)
- [x] ReAct agent design & safety budgeting (`docs/agent-design.md`)
- [x] Typed tool registry & security policy (`docs/tool-security.md`)
- [x] Micro-isolated Docker sandbox design (`docs/sandbox-design.md`)
- [x] Comprehensive threat model & STRIDE matrix (`docs/threat-model.md`)
- [x] Offline air-gap & live telemetry architecture (`docs/offline-architecture.md`)
- [x] Flagship industrial demonstration walkthrough (`docs/demo-workflow.md`)
- [x] Architecture review & risk assessment (`docs/architecture-review.md`)

---

### Phase 2: Ingestion, Local RAG & Persistence Layer
- [ ] Implement SQLite async session manager and ORM entities (`workspaces`, `documents`, `chunks`, `tasks`, `audit_events`).
- [ ] Implement PyMuPDF digital PDF parser and text extractor.
- [ ] Implement offline OCR pipeline (PaddleOCR-light / Tesseract) with bounding box normalization.
- [ ] Implement openpyxl spreadsheet analyzer and tabular Markdown generator.
- [ ] Implement FastEmbed ONNX embedding pipeline (`bge-small-en-v1.5`) and local Qdrant collection setup.
- [ ] Build unit tests for chunking, embedding, and vector similarity retrieval.

---

### Phase 3: Typed Tool Registry & Docker Sandbox
- [ ] Implement `LLMProvider` abstract base class and `OllamaProvider` with VRAM memory tracking.
- [ ] Implement `ModelRegistry` and resource-aware VRAM model swapping state machine.
- [ ] Build typed tool registry with Pydantic schemas for `search_knowledge`, `inspect_image`, `read_file`, `write_file`, `generate_docx`, `generate_pptx`.
- [ ] Build `docker/sandbox-python/Dockerfile` hardened image (`--network none`, 512MB RAM, non-root user).
- [ ] Implement `SandboxManager` with container lifecycle control, timeouts, and artifact harvesting.
- [ ] Build security integration tests for path traversal attacks and container network block.

---

### Phase 4: ReAct Agent Orchestrator & Policy Engine
- [ ] Implement ReAct agent execution loop with step budgeting ($N \le 15$) and loop detection.
- [ ] Implement Policy Engine risk evaluation and Human-in-the-Loop (HITL) pause/resume state handler.
- [ ] Implement SHA-256 hash-chained immutable audit logger.
- [ ] Expose FastAPI REST endpoints and Server-Sent Events (SSE) streaming for real-time thoughts, tool calls, and observations.

---

### Phase 5: React 19 Frontend & Real Telemetry Dashboards
- [ ] Scaffold React 19 + TypeScript + Vite + Tailwind CSS client.
- [ ] Build **Command Center**: Real-time agent status, active subtasks, live execution timeline, token consumption, and system hardware gauges.
- [ ] Build **AI Workspace**: Interactive multi-turn interface with step visualizer, tool call previews, diff viewers, and human approval modals.
- [ ] Build **Knowledge Vault**: Document dropzone, OCR status badge, chunk viewer, and vector similarity search tester.
- [ ] Build **Evidence Viewer**: Side-by-side split screen showing generated assertions matched to highlighted PDF pages, OCR bounding boxes, and spreadsheet ranges.
- [ ] Build **Audit & Sovereignty Monitor**: Live VRAM/RAM gauges (`pynvml`/`psutil`), air-gap status LED, and cryptographic hash chain validator.

---

### Phase 6: Flagship Demo Validation & Polish
- [ ] Assemble the 5 flagship industrial test assets (`inspection_report.pdf`, `scanned_report.pdf`, `equipment_photo.jpg`, `maintenance_history.xlsx`, `maintenance_manual.pdf`).
- [ ] Execute full end-to-end multi-modal inspection workflow with Wi-Fi disabled.
- [ ] Benchmark execution latency, VRAM swapping overhead, and token efficiency.
- [ ] Package one-click Windows 11 installation and startup batch scripts.

---

### Post-Hackathon Phase: Enterprise Enhancements
- [ ] Multi-GPU cluster support (vLLM / TensorRT-LLM backend).
- [ ] Hardware Security Module (HSM) / TPM 2.0 cryptographic audit signing.
- [ ] On-premise fine-tuning pipeline for domain-specific industrial maintenance terminology.
