# SOVEREIGN-X — Database & Storage Design

---

## 1. Storage Architecture Overview

SOVEREIGN-X utilizes a dual-engine local storage pattern optimized for a single-node laptop deployment:
1. **SQLite (WAL Mode)**: High-performance relational engine for application state, workspace boundaries, task timelines, steps, tool parameters, human approvals, and cryptographic audit records.
2. **Qdrant (Local Embedded/Storage)**: Vector database engine storing dense embedding vectors with strict payload metadata filtering for access control and page-level provenance.
3. **Local File Vault (`./data/workspaces/{workspace_id}/`)**: Sanitized disk directories storing original source files and generated output artifacts.

```
                                      +---------------------------------------------+
                                      |            PERSISTENCE BOUNDARY             |
                                      +---------------------------------------------+
                                                             |
                    +----------------------------------------+----------------------------------------+
                    |                                        |                                        |
                    v                                        v                                        v
     +------------------------------+         +------------------------------+         +------------------------------+
     |   SQLite Database            |         |   Qdrant Vector Database     |         |   File Vault Storage         |
     |   (`sovereign.db` - WAL)     |         |   (`qdrant_storage/`)        |         |   (`./data/workspaces/`)     |
     |                              |         |                              |         |                              |
     | - workspaces                 |         | - Collection: `sovereign_rag`|         | - /uploads (Raw documents)   |
     | - documents & chunks         |         | - Vectors: 384-dim (Cosine)  |         | - /ocr (Extracted layers)    |
     | - tasks & steps              |         | - Payload: doc_id, page,     |         | - /scratch (Sandbox temp)    |
     | - tool_executions            |         |            section, bbox,    |         | - /artifacts (DOCX/PPTX)     |
     | - audit_events (Hash Chain)  |         |            classification    |         |                              |
     +------------------------------+         +------------------------------+         +------------------------------+
```

---

## 2. SQLite Relational Schema (DDL)

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;

-- Workspaces
CREATE TABLE workspaces (
    id TEXT PRIMARY KEY,                       -- e.g., 'ws_8f9c21'
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    classification_level TEXT DEFAULT 'INTERNAL_ENGINEERING' CHECK(classification_level IN ('PUBLIC', 'INTERNAL_ENGINEERING', 'RESTRICTED_CONFIDENTIAL')),
    storage_path TEXT NOT NULL
);

-- Ingested Documents
CREATE TABLE documents (
    id TEXT PRIMARY KEY,                       -- e.g., 'doc_0192a3'
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256_hash TEXT NOT NULL,
    page_count INTEGER DEFAULT 1,
    ocr_applied BOOLEAN DEFAULT FALSE,
    parsing_status TEXT DEFAULT 'PENDING' CHECK(parsing_status IN ('PENDING', 'PARSING', 'INDEXED', 'FAILED')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_docs_workspace ON documents(workspace_id);
CREATE INDEX idx_docs_hash ON documents(sha256_hash);

-- Document Chunks with Provenance
CREATE TABLE document_chunks (
    id TEXT PRIMARY KEY,                       -- e.g., 'chk_99ab12'
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    section_title TEXT,
    bbox_json TEXT,                            -- JSON array: [x0, y0, x1, y1] for OCR/PDF highlight
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding_id TEXT,                         -- Qdrant Point ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_doc ON document_chunks(document_id);
CREATE INDEX idx_chunks_workspace ON document_chunks(workspace_id);

-- Agent Tasks
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,                       -- e.g., 'tsk_a98e10'
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    status TEXT DEFAULT 'QUEUED' CHECK(status IN ('QUEUED', 'PLANNING', 'EXECUTING', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED')),
    max_steps INTEGER DEFAULT 15,
    current_step INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    summary_result TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_workspace ON tasks(workspace_id);

-- Step-by-step Agent Reasoning & Observations
CREATE TABLE task_steps (
    id TEXT PRIMARY KEY,                       -- e.g., 'stp_0012bc'
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    thought_reasoning TEXT,
    plan_snapshot TEXT,                        -- JSON array of planned checklist items
    model_used TEXT NOT NULL,
    vram_used_mb INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_steps_task ON task_steps(task_id);

-- Tool Invocations
CREATE TABLE tool_executions (
    id TEXT PRIMARY KEY,                       -- e.g., 'tex_44bc99'
    step_id TEXT NOT NULL REFERENCES task_steps(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    risk_level TEXT NOT NULL CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    arguments_json TEXT NOT NULL,
    output_json TEXT,
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXECUTING', 'SUCCESS', 'FAILED', 'TIMED_OUT')),
    requires_human_approval BOOLEAN DEFAULT FALSE,
    approval_reason TEXT,
    approved_by TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tool_exec_task ON tool_executions(task_id);

-- Generated Artifacts (DOCX, PPTX, Charts)
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,                       -- e.g., 'art_190f7'
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256_hash TEXT NOT NULL,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_artifacts_task ON artifacts(task_id);

-- Immutable Hash-Chained Audit Log
CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_uuid TEXT UNIQUE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actor TEXT NOT NULL DEFAULT 'SYSTEM_AGENT',
    workspace_id TEXT REFERENCES workspaces(id),
    task_id TEXT REFERENCES tasks(id),
    event_type TEXT NOT NULL,                  -- 'INGEST', 'RETRIEVE', 'TOOL_EXEC', 'APPROVAL', 'ARTIFACT_GEN', 'SECURITY_ALERT'
    payload_json TEXT NOT NULL,
    client_ip TEXT DEFAULT '127.0.0.1',
    previous_hash TEXT NOT NULL,               -- SHA-256 hash of previous row
    current_hash TEXT NOT NULL                 -- SHA-256(previous_hash + event_uuid + timestamp + event_type + payload_json)
);

CREATE INDEX idx_audit_task ON audit_events(task_id);
CREATE INDEX idx_audit_workspace ON audit_events(workspace_id);
```

---

## 3. Qdrant Vector Collection Schema

### 3.1. Collection Configuration: `sovereign_rag`
```json
{
  "name": "sovereign_rag",
  "vectors": {
    "size": 384,
    "distance": "Cosine",
    "on_disk": true
  },
  "optimizers_config": {
    "default_segment_number": 2,
    "memmap_threshold": 20000
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 100,
    "full_scan_threshold": 10000,
    "on_disk": true
  }
}
```

### 3.2. Vector Payload Data Structure
Every vector in Qdrant contains rich payload metadata for pre-retrieval authorization and source bounding:
```json
{
  "id": "chk_99ab12",
  "vector": [0.041, -0.092, 0.118, "...", 0.005],
  "payload": {
    "workspace_id": "ws_8f9c21",
    "document_id": "doc_0192a3",
    "filename": "inspection_report.pdf",
    "chunk_index": 4,
    "page_number": 4,
    "section_title": "3.2 Ultrasonic Thickness Gauging",
    "classification": "RESTRICTED_CONFIDENTIAL",
    "bbox": [45.2, 110.0, 520.5, 340.8],
    "is_table": false,
    "text_preview": "Minimum measured wall thickness: 3.42mm at node C-12..."
  }
}
```

### 3.3. Pre-Retrieval Filter Query Pattern
To enforce strict zero-leakage authorization across workspaces and classifications:
```json
{
  "filter": {
    "must": [
      { "key": "workspace_id", "match": { "value": "ws_8f9c21" } },
      { "key": "classification", "match": { "any": ["PUBLIC", "INTERNAL_ENGINEERING", "RESTRICTED_CONFIDENTIAL"] } }
    ]
  },
  "limit": 5,
  "with_payload": true
}
```

---

## 4. Cryptographic Hash Chain Validation

Audit entries maintain mathematical tamper evidence:
$$\text{Entry Hash}_i = \text{SHA256}(\text{Entry Hash}_{i-1} \,\|\, \text{UUID}_i \,\|\, \text{Timestamp}_i \,\|\, \text{EventType}_i \,\|\, \text{Payload}_i)$$

If any record in `audit_events` is manually edited, inserted, or deleted in the SQLite file, running the audit validator will immediately flag the mismatch at the exact tampered index.
