# SOVEREIGN-X — Repository Structure & Monorepo Design

---

## 1. Directory Layout Overview

The repository is organized as a clean, modular monorepo. It isolates core concerns into strict layer boundaries without introducing complex microservice overhead.

```
SovereignAI/
├── .github/                       # CI/CD workflows (linting, offline test suites)
│   └── workflows/
│       ├── test-backend.yml
│       ├── test-frontend.yml
│       └── security-scan.yml
│
├── frontend/                      # React 19 + Vite + TypeScript Client
│   ├── public/                    # Static assets, icons, fonts
│   ├── src/
│   │   ├── assets/                # Logos, UI styling assets
│   │   ├── components/            # Reusable UI primitives (Shadcn/UI based)
│   │   │   ├── ui/                # Buttons, Dialogs, Cards, Badges, Tabs
│   │   │   ├── layout/            # Sidebar, Header, StatusBanner, SplitPanes
│   │   │   ├── command/           # Command Center widgets, metrics gauges
│   │   │   ├── workspace/         # Chat stream, Step visualizer, Plan tracker
│   │   │   ├── vault/             # File dropzone, Document tree, Chunk viewer
│   │   │   ├── evidence/          # PDF splitter, OCR highlight, Bounding box
│   │   │   ├── audit/             # Hash chain visualizer, Event timeline
│   │   │   └── security/          # Sovereignty monitor, VRAM gauge, Air-gap LED
│   │   ├── hooks/                 # Custom React hooks (useSSE, useTelemetry)
│   │   ├── services/              # Typed API clients (Axios/Fetch + EventSource)
│   │   ├── stores/                # State management (Zustand)
│   │   │   ├── workspaceStore.ts
│   │   │   ├── taskStore.ts
│   │   │   ├── telemetryStore.ts
│   │   │   └── auditStore.ts
│   │   ├── types/                 # Shared TypeScript interfaces & API contracts
│   │   ├── utils/                 # Formatters, date utils, byte helpers
│   │   ├── App.tsx                # App entrypoint with tab routing
│   │   └── main.tsx               # Root DOM mount
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── backend/                       # Python 3.11 FastAPI Sovereign Core
│   ├── app/
│   │   ├── main.py                # FastAPI app initialization & middleware
│   │   ├── config.py              # Application settings (Pydantic BaseSettings)
│   │   │
│   │   ├── api/                   # API Routing Layer
│   │   │   ├── deps.py            # FastAPI dependency injections
│   │   │   ├── v1/
│   │   │   │   ├── router.py      # Master v1 router aggregator
│   │   │   │   ├── workspaces.py  # Workspace CRUD & active context
│   │   │   │   ├── documents.py   # Ingestion, parsing, metadata extraction
│   │   │   │   ├── tasks.py       # Agent task execution & SSE streaming
│   │   │   │   ├── approvals.py   # Human-in-the-loop action approvals
│   │   │   │   ├── models.py      # Local model registry & VRAM status
│   │   │   │   ├── artifacts.py   # Deliverable download (DOCX/PPTX/reports)
│   │   │   │   ├── audit.py       # Immutable audit logs & verification
│   │   │   │   └── telemetry.py   # Hardware gauges (GPU/VRAM/RAM/Network)
│   │   │
│   │   ├── core/                  # Core Engine Infrastructure
│   │   │   ├── security.py        # Path traversal guard, quarantine scanner
│   │   │   ├── policy.py          # Action risk evaluation & policy rules
│   │   │   ├── audit_logger.py    # SHA-256 hash-chained log writer
│   │   │   └── telemetry.py       # psutil and pynvml hardware collector
│   │   │
│   │   ├── models/                # Pydantic Schemas & Domain Entities
│   │   │   ├── workspace.py       # Workspace definitions & schemas
│   │   │   ├── document.py        # Document, Chunk, Provenance schemas
│   │   │   ├── task.py            # Task, Step, Observation, Plan schemas
│   │   │   ├── tool.py            # Tool definition & invocation schemas
│   │   │   └── telemetry.py       # VRAM/RAM/Air-gap status schemas
│   │   │
│   │   ├── db/                    # Database Persistence Layer
│   │   │   ├── session.py         # SQLite connection pool & async engine
│   │   │   ├── base.py            # SQLAlchemy Base & metadata
│   │   │   ├── models/            # SQLAlchemy ORM models
│   │   │   │   ├── workspace_orm.py
│   │   │   │   ├── document_orm.py
│   │   │   │   ├── task_orm.py
│   │   │   │   └── audit_orm.py
│   │   │   └── migrations/        # Lightweight migration scripts / init SQL
│   │   │
│   │   ├── llm/                   # Model Provider & Routing Layer
│   │   │   ├── base.py            # Abstract Base Class: LLMProvider
│   │   │   ├── ollama_client.py   # Ollama API client with VRAM swap manager
│   │   │   ├── model_registry.py  # Model catalog, capacities & status
│   │   │   └── router.py          # Resource-aware task-to-model router
│   │   │
│   │   ├── rag/                   # Retrieval-Augmented Generation Engine
│   │   │   ├── chunking.py        # Hierarchical & recursive chunking
│   │   │   ├── embeddings.py      # Local FastEmbed (bge-small-en-v1.5)
│   │   │   ├── vector_store.py    # Qdrant client & collection manager
│   │   │   ├── retriever.py       # Pre-filtering & semantic search
│   │   │   └── provenance.py      # Citation binder & bounding box mapper
│   │   │
│   │   ├── ingestion/             # Multi-Modal Document Processors
│   │   │   ├── pdf_parser.py      # PyMuPDF digital PDF text & layout
│   │   │   ├── ocr_engine.py      # PaddleOCR-light / Tesseract offline OCR
│   │   │   ├── excel_parser.py    # openpyxl / pandas tabular processor
│   │   │   └── image_parser.py    # Metadata, EXIF, and resolution inspector
│   │   │
│   │   ├── agent/                 # Agentic Execution Subsystem
│   │   │   ├── orchestrator.py    # Master ReAct execution loop & budgeter
│   │   │   ├── state.py           # Agent state machine & memory
│   │   │   ├── planner.py         # Dynamic multi-step task planning
│   │   │   └── prompt_builder.py  # Zero-leakage system prompt synthesizer
│   │   │
│   │   ├── tools/                 # Typed Tool Implementation Registry
│   │   │   ├── registry.py        # Tool registration decorator & dispatcher
│   │   │   ├── file_tools.py      # read_file, list_workspace, write_file
│   │   │   ├── rag_tools.py       # search_knowledge
│   │   │   ├── vision_tools.py    # inspect_image (Gemma3 router)
│   │   │   ├── doc_tools.py       # read_pdf, read_excel, analyze_csv
│   │   │   ├── export_tools.py    # generate_docx, generate_pptx
│   │   │   └── sandbox_tools.py   # run_python_sandbox
│   │   │
│   │   └── sandbox/               # Docker Ephemeral Execution Isolation
│   │       ├── manager.py         # Docker SDK container lifecycle manager
│   │       ├── container_spec.py  # Hardened container flags (--net=none, etc.)
│   │       └── execution_guard.py # Timeouts, stdout limits, artifact cleaner
│   │
│   ├── tests/                     # Automated Test Suites
│   │   ├── unit/                  # Unit tests (models, chunker, tools)
│   │   ├── integration/           # API integration & agent loops
│   │   ├── security/              # Path traversal, sandbox escape, injection
│   │   └── offline/               # Air-gap verification test suite
│   ├── Dockerfile                 # Backend container definition
│   ├── requirements.txt           # Production Python dependencies
│   └── requirements-dev.txt       # Dev/test tooling (pytest, ruff, bandit)
│
├── docker/                        # Container & Sandbox Infrastructure
│   ├── sandbox-python/            # Isolated Python Execution Image
│   │   ├── Dockerfile             # Hardened Python 3.11 slim image
│   │   └── entrypoint.sh          # Non-root unprivileged runner script
│   └── docker-compose.yml         # Local stack orchestration (FastAPI + Qdrant)
│
├── docs/                          # Comprehensive Technical Documentation
│   ├── architecture.md
│   ├── repository-structure.md
│   ├── api-contract.md
│   ├── database-design.md
│   ├── model-strategy.md
│   ├── rag-design.md
│   ├── agent-design.md
│   ├── tool-security.md
│   ├── sandbox-design.md
│   ├── threat-model.md
│   ├── offline-architecture.md
│   ├── demo-workflow.md
│   ├── testing-strategy.md
│   ├── deployment.md
│   ├── roadmap.md
│   └── architecture-review.md
│
├── scripts/                       # Operational & Setup Utility Scripts
│   ├── setup_offline_models.bat   # Pulls Qwen3 & Gemma3 into local Ollama
│   ├── download_embeddings.py     # Caches FastEmbed ONNX weights locally
│   ├── build_sandbox_image.bat    # Builds sovereign-sandbox:latest Docker image
│   ├── verify_airgap.py           # Validates zero external socket egress
│   └── run_dev.bat                # Starts backend & frontend locally
│
├── data/                          # Local Storage (Git Ignored)
│   ├── workspaces/                # Per-workspace isolated file storage
│   ├── qdrant_storage/            # Local vector DB data files
│   ├── audit_logs/                # Immutable JSON-Lines audit records
│   └── sovereign.db               # SQLite application database
│
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git ignore rules (data, cache, models)
└── README.md                      # Primary project overview
```

---

## 2. Layer Separation & Import Invariants

To maintain strict modularity, the following unidirectional import boundaries are enforced:

1. **`api/`** depends on `core/`, `models/`, `agent/`, `db/`, and `llm/`. It contains zero business logic.
2. **`agent/`** depends on `tools/`, `llm/`, `models/`, and `core/policy.py`. It has no knowledge of FastAPI or HTTP routes.
3. **`tools/`** depends on `rag/`, `ingestion/`, `sandbox/`, and `models/`. Tools are isolated, stateless callable units.
4. **`sandbox/`** communicates with Docker via standard Python Docker SDK or native CLI sub-process calls. It has zero access to host workspace paths outside its mounted volumes.
5. **`llm/`** contains abstract model interfaces. The rest of the application imports `LLMProvider` and never binds directly to Ollama implementation details.
