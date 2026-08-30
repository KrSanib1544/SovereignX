# SOVEREIGN-X — System Architecture Document
**Confidential Industrial Agentic AI Workbench**

---

## 1. System Vision & Core Invariants

SOVEREIGN-X is an on-premise, air-gapped agentic AI workbench built for mission-critical industrial manufacturing, defense compliance, and infrastructure engineering. The architecture guarantees:

1. **Air-Gap Sovereignty**: Zero runtime network egress (`0 bytes sent over WAN`). Absolute local inference using open-weight models (`Qwen3 4B` and `Gemma3 4B`).
2. **Zero-Trust Host Execution**: The LLM *never* interacts directly with the host OS, filesystem root, or command shell. All tool invocations are policy-checked, and all dynamic code executions are isolated within an ephemeral Docker sandbox container with `--net=none` and strict cgroups limits.
3. **Hardware Determinism**: Engineered specifically for execution on a single standard Windows 11 host with **16 GB RAM** and **4 GB VRAM (NVIDIA RTX 3050)**.
4. **Verifiable Provenance & Evidence**: No synthetic hallucinations allowed for critical industrial findings. Every generated claim must cite an explicit source (Document ID, filename, page number, bounding box, or spreadsheet cell range).
5. **Auditable Lifecycle**: Every state transition, prompt, tool parameter, policy approval, and artifact generation is logged to an immutable hash-chained audit log.

---

## 2. High-Level System Architecture

```
                                  +-------------------------------------------------------------+
                                  |                     CLIENT LAYER (Browser)                  |
                                  |   React 19 + TypeScript + Vite + Tailwind CSS + Lucide Icons|
                                  |   (Command Center, Workspace, Vault, Audits, Security Dash) |
                                  +------------------------------+------------------------------+
                                                                 |  HTTP REST & Server-Sent Events
                                                                 v
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                SOVEREIGN CORE BACKEND (FastAPI / Python 3.11)                                |
|                                                                                                                               |
|  +---------------------------+    +---------------------------+    +----------------------------+    +---------------------+  |
|  |     API Gateway / Routers |    |   Security & Auth Guard   |    |    System Telemetry Engine |    | File / Storage Vault|  |
|  |   - Workspaces / Tasks    |--->|   - Session Auth          |    |   - VRAM / RAM Profiler    |    |   - Path Sanitizer  |  |
|  |   - Ingestion / Vault     |    |   - Workspace RBAC        |    |   - Air-Gap Network Probe  |    |   - Quarantine Zone |  |
|  |   - Models / Telemetry    |    |   - Token Bucket Throttler|    |   - Model Memory Monitor   |    |   - Artifact Store  |  |
|  +---------------------------+    +---------------------------+    +----------------------------+    +---------------------+  |
|                                                 |                                                                             |
|                                                 v                                                                             |
|  +-------------------------------------------------------------------------------------------------------------------------+  |
|  |                                                 AGENTIC ORCHESTRATION LAYER                                             |  |
|  |                                                                                                                         |  |
|  |  +-----------------------+     +--------------------------+     +------------------------+    +---------------------+  |  |
|  |  | Task Planner & State  |     |  Policy Evaluation Engine|     |  Resource-Aware Router |    | Tool Execution Mgr  |  |  |
|  |  | - ReAct State Machine |---->|  - Action Risk Level     |---->|  - Context Budgeter    |--->| - Typed Arguments   |  |  |
|  |  | - Step Budget (<=15)  |     |  - Human Approval Gate   |     |  - VRAM Swap Scheduler |    | - Timeout Controller|  |  |
|  |  | - Cycle / Loop Guard  |     |  - Path Boundary Enforcer|     |  - Fallback Switcher   |    | - Event Streamer    |  |  |
|  |  +-----------------------+     +--------------------------+     +------------------------+    +---------------------+  |  |
|  +-------------------------------------------------------------------------------------------------------------------------+  |
|                                                 |                                       |                                     |
|                                                 |                                       |                                     |
|               +---------------------------------+                                       +------------------+                  |
|               v                                                                                            v                  |
|  +----------------------------+   +------------------------------------+   +-----------------------------------------------+  |
|  |     TYPED TOOL REGISTRY    |   |     DOCUMENT PROCESSING & RAG      |   |            LOCAL MODEL INFERENCE              |  |
|  |  - read_file / write_file  |   |  - PyMuPDF (PDF Parser)            |   |  - Model Registry Adapter                     |  |
|  |  - search_knowledge (RAG)  |   |  - PaddleOCR-light / Tesseract     |   |  - Ollama Local Client (http://localhost:11434|  |
|  |  - inspect_image (Gemma3)  |   |  - openpyxl / pandas Analyzer      |   |  - Dynamic Model Unloader/Loader              |  |
|  |  - generate_docx / pptx    |   |  - Recursive Character Chunker     |   |    * Qwen3:4b (Text/Reasoning, 2.5GB)         |  |
|  |  - run_python_sandbox      |   |  - FastEmbed / ONNX MiniLM Embedder|   |    * Gemma3:4b (Vision/Multimodal, 3.3GB)     |  |
|  +--------------+-------------+   +-----------------+------------------+   +-----------------------------------------------+  |
|                 |                                   |                                                                         |
+-----------------|-----------------------------------|-------------------------------------------------------------------------+
                  |                                   |
                  v                                   v
+------------------------------------+   +------------------------------------+   +---------------------------------------------+
|    ISOLATED MICRO-CONTAINER        |   |      LOCAL VECTOR DATABASE         |   |          PERSISTENCE LAYER (Local)          |
|        (Docker Sandbox)            |   |             (Qdrant)               |   |                                             |
| - python:3.11-slim (Hardened)      |   | - Embedded / Local Single-Node     |   | - SQLite Metadata Database                  |
| - --net=none (Zero Network)        |   | - Cosine Metric, HNSW Index        |   |   (Workspaces, Tasks, Audit Trails, Files)  |
| - 512MB RAM cap, 1 CPU Core        |   | - Hybrid In-Memory Vector Search   |   | - Local Workspace Directory (`./data/`)     |
| - Read-Only Inputs, Temp Output    |   | - Strict Workspace ID Partitioning |   | - Immutable JSON-Lines Audit Log Vault      |
| - 30s Hard Execution Timeout       |   | - Provenance Metadata Indexing     |   | - Generated Deliverables Artifact Vault     |
+------------------------------------+   +------------------------------------+   +---------------------------------------------+
```

---

## 3. Subsystem Breakdown

### 3.1. Client Presentation Layer (Frontend)
- **Tech Stack**: React 19, TypeScript, Vite, Tailwind CSS, Lucide React, Shadcn/UI primitives.
- **Key Modules**:
  - **Command Center**: Real-time agent status, active subtasks, live execution timeline, token consumption, and system hardware gauges (VRAM/RAM/CPU/Air-gap status).
  - **AI Workspace**: Interactive multi-turn interface supporting step-by-step reasoning transparency, tool call visualization, diff viewers, and human-in-the-loop action approval modals.
  - **Knowledge Vault**: Document drag-and-drop ingestion, OCR preview, chunk inspector, semantic similarity explorer, and metadata tagger.
  - **Evidence Viewer**: Side-by-side split screen showing generated assertions matched to highlighted PDF pages, OCR bounding boxes, and spreadsheet ranges.
  - **Audit & Sovereignty Monitor**: Immutable log viewer, cryptographic hash chain validator, air-gap egress validator, and active VRAM footprint analyzer.

### 3.2. Sovereign Core Backend (FastAPI Application)
- **Framework**: FastAPI with asynchronous endpoints (`asyncio`), Pydantic v2 data models, and SSE (Server-Sent Events) streaming.
- **Responsibilities**:
  - Expose authenticated, validated REST endpoints for UI actions.
  - Stream agent thought processes, tool calls, and partial outputs via SSE.
  - Manage workspace isolation and file uploads with zero path traversal vulnerabilities.
  - Collect local hardware telemetry via `pynvml` (NVIDIA VRAM/temperature) and `psutil` (RAM/CPU/Disk/Network interfaces).

### 3.3. Security & Policy Enforcement Engine
- **Principle**: Zero-trust pipeline between LLM reasoning and system action.
- **Workflow**:
  ```
  LLM Proposes Tool Call -> Schema Validation -> Policy Engine (Risk Check) -> [If HIGH RISK: Pause & Request Human Approval] -> Sandboxed / Controlled Execution -> Output Sanitization -> Return to Agent Loop
  ```
- **Policy Rules**:
  - `READ_ONLY` actions (`read_file`, `search_knowledge`, `inspect_image`): Auto-approved within active workspace scope.
  - `FILE_MUTATION` actions (`write_file`, `generate_docx`, `generate_pptx`): Auto-approved in scratch directories; requires workspace lock.
  - `EXECUTION` actions (`run_python_sandbox`): Verified for no host escapes, executed inside ephemeral container, output capped at 64 KB.

### 3.4. Agentic Orchestration Layer
- **Pattern**: Deterministic ReAct (Reasoning + Action) state machine with strict loop termination guards.
- **Controls**:
  - Max iterations per task: `15 steps`.
  - Max tool calls per step: `3 calls`.
  - Execution timeout: `180 seconds` total task budget.
  - State persistence: All intermediate thoughts, plans, and observations are committed to SQLite after each step.

### 3.5. Model Routing & Memory Management
- **Hardware Constraint**: 4 GB VRAM on NVIDIA RTX 3050 Laptop GPU.
- **Design**:
  - **Primary Reasoning Model**: `qwen3:4b` (~2.5 GB VRAM footprint). Handles task decomposition, tool generation, SQL/Python generation, text synthesis, and citation formatting.
  - **Visual Multimodal Model**: `gemma3:4b` (~3.3 GB VRAM footprint). Handles visual document analysis, inspection photos, P&ID diagrams, and technical drawings.
  - **VRAM Arbitrator**: Because `2.5 GB + 3.3 GB = 5.8 GB > 4.0 GB`, both models cannot reside concurrently in VRAM. The backend model manager issues explicit Ollama unload requests (`keep_alive=0`) when switching modalities to prevent CUDA Out-Of-Memory (OOM) crashes.

### 3.6. Local RAG & Ingestion Subsystem
- **Parsing**:
  - Digital PDFs: `PyMuPDF` (`fitz`) for native text and structural coordinates.
  - Scanned PDFs & Images: `PaddleOCR-light` / `Tesseract` for offline OCR with bounding box retention.
  - Spreadsheets: `openpyxl` / `pandas` converted into structured Markdown tables and JSON schema summaries.
- **Embeddings**: `FastEmbed` running `bge-small-en-v1.5` (384-dim, ONNX runtime, CPU-accelerated, ~130MB RAM footprint).
- **Vector Database**: `Qdrant` (local embedded or lightweight single-node container, memory-mapped storage).

### 3.7. Ephemeral Execution Sandbox
- **Implementation**: Ephemeral Docker micro-container running `python:3.11-slim`.
- **Security Boundaries**:
  - `--network none` (Hard physical network block).
  - `--memory 512m` and `--cpus 1.0`.
  - Read-only volume mount for workspace input files (`/workspace/input:ro`).
  - Ephemeral scratch directory for output artifacts (`/workspace/output:rw`).
  - Non-root user (`sandboxuser:10001`).
  - `no-new-privileges`, `seccomp=default`, read-only root filesystem (`--read-only`).

---

## 4. Architectural Dataflow: End-to-End Execution

```mermaid
sequenceDiagram
    autonumber
    actor User as Engineer / Auditor
    participant UI as React Frontend
    participant Core as FastAPI Backend
    participant Pol as Policy Engine
    participant Agent as Agent Orchestrator
    participant Model as Model Router (Ollama)
    participant Tool as Tool Manager
    participant Box as Docker Sandbox
    participant DB as SQLite & Qdrant

    User->>UI: Uploads Inspection Package & Enters Task
    UI->>Core: POST /api/v1/workspaces/{id}/ingest
    Core->>DB: Store Documents & Compute Embeddings
    User->>UI: Clicks "Run Autonomous Analysis"
    UI->>Core: POST /api/v1/tasks (Stream SSE)
    Core->>Agent: Initialize Task State
    
    loop ReAct Agent Iteration (Max 15)
        Agent->>Model: Prompt with Context, Tools & System Invariants
        Model-->>Agent: Proposes Action: run_python_sandbox(script)
        Agent->>Pol: Validate Action & Check Permissions
        
        alt Action is High Risk
            Pol-->>UI: Event: APPROVAL_REQUIRED
            UI-->>User: Display Script Diff & Security Risk
            User->>UI: Approves Action
            UI->>Pol: POST /api/v1/tasks/{id}/approve
        end
        
        Pol->>Tool: Authorize Tool Call
        Tool->>Box: Execute Script in Isolated Container (--net=none)
        Box-->>Tool: Return stdout, stderr, & generated chart.png
        Tool-->>Agent: Observation Data
    end

    Agent->>Tool: generate_docx(findings, citations)
    Tool-->>Agent: Artifact Created (approval_note.docx)
    Agent->>Core: Finalize Task & Write Audit Hash
    Core->>DB: Commit Task State & SHA-256 Event Chain
    Core-->>UI: Event: TASK_COMPLETE with Deliverable Artifacts
    UI-->>User: Render Interactive Findings, Evidence Splitter & Download
```

---

## 5. Security & Sovereignty Invariants

| Invariant | Implementation Mechanism | Validation Rule |
| :--- | :--- | :--- |
| **No Cloud Dependency** | `OLLAMA_NO_CLOUD=1`, pure local ONNX/PyTorch embeddings, local Qdrant | Wi-Fi disabled socket test returns 100% test pass |
| **No OS Shell Execution** | Strict parameter validation; zero `subprocess.Popen(shell=True)` | Bandit and Semgrep static analysis |
| **Path Traversal Immunity** | `pathlib.Path.resolve()` checks ensuring paths reside in `./data/workspaces/{id}` | Reject any path containing `..`, absolute drive letters, or symlinks |
| **Tamper-Evident Auditing** | Each audit log entry includes `sha256(prev_hash + entry_data)` | Cryptographic validator rejects modified entries |
| **Pre-Retrieval Authorization** | Access control filters applied in Qdrant query filters *before* semantic search | Zero data leakage across unauthorized document tiers |

---

## 6. Hardware Budget Allocation (16 GB RAM / 4 GB VRAM)

```
================================================================================
TOTAL SYSTEM MEMORY BUDGET (16.0 GB RAM)
================================================================================
[ Host OS & Background Services (Windows 11) ]   : 4.0 GB  (25.0%)
[ Ollama Server & Model Swapping Buffer ]       : 3.5 GB  (21.9%)
[ FastAPI Core, Ingestion Engine & FastEmbed ]   : 2.0 GB  (12.5%)
[ Qdrant Vector Engine (In-Memory HNSW Cache) ]  : 1.0 GB  (6.25%)
[ Ephemeral Docker Sandbox Execution Cap ]       : 0.5 GB  (3.12%)
[ Free Operating Headroom & Disk Cache ]        : 5.0 GB  (31.25%)
================================================================================

================================================================================
GPU VRAM ALLOCATION (4.0 GB NVIDIA RTX 3050)
================================================================================
[ Windows DWM / Display Output Buffer ]         : 0.6 GB  (15.0%)
[ Active Model: Qwen3 4B (Reasoning / Tools) ]   : 2.5 GB  (62.5%)  <-- Active
  OR
[ Active Model: Gemma3 4B (Multimodal Vision) ] : 3.3 GB  (82.5%)  <-- Swapped
[ PyTorch / CUDA Context Headroom ]              : 0.4 GB  (10.0%)
================================================================================
```
*Note: Strict sequential scheduling ensures Qwen3 and Gemma3 are never loaded simultaneously.*
