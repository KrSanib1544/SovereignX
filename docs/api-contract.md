# SOVEREIGN-X — API Contract & Endpoint Specifications

---

## 1. Protocol & Transport Guidelines

- **Base URL**: `http://localhost:8000/api/v1`
- **Format**: JSON (`Content-Type: application/json`) for standard REST operations.
- **Streaming**: Server-Sent Events (`text/event-stream`) for real-time agent execution traces, token generation, and telemetry.
- **Authentication**: Local Session Bearer Token / Workspace Header (`X-Sovereign-Session-ID`).
- **Error Standard**: RFC 7807 Problem Details compliant error structures.

---

## 2. API Endpoint Matrix

| Method | Endpoint | Description | Auth Scope |
| :--- | :--- | :--- | :--- |
| **GET** | `/health` | Core system liveness and air-gap verification | Public |
| **GET** | `/telemetry` | Real-time GPU VRAM, RAM, CPU, and network egress stats | Operator |
| **GET** | `/models` | List registered local models, VRAM usage, and active state | Operator |
| **POST** | `/models/swap` | Force explicit model swap / VRAM eviction | Admin |
| **POST** | `/workspaces` | Create an isolated workspace container | Operator |
| **GET** | `/workspaces` | List all active local workspaces | Operator |
| **GET** | `/workspaces/{id}` | Retrieve workspace details and ingested file tree | Operator |
| **DELETE** | `/workspaces/{id}` | Wipe workspace, vectors, and ephemeral data | Operator |
| **POST** | `/workspaces/{id}/documents` | Multi-part upload and ingest documents | Operator |
| **GET** | `/workspaces/{id}/documents` | List indexed documents with parsing status & chunks | Operator |
| **GET** | `/workspaces/{id}/documents/{doc_id}` | Get document metadata and extracted text/OCR | Operator |
| **POST** | `/workspaces/{id}/query` | Direct semantic search / vector retrieval test | Operator |
| **POST** | `/workspaces/{id}/tasks` | Launch an autonomous agent task (Returns SSE stream) | Operator |
| **GET** | `/workspaces/{id}/tasks/{task_id}` | Get task execution state, plan, and observations | Operator |
| **POST** | `/workspaces/{id}/tasks/{task_id}/approve` | Approve or reject a paused high-risk tool call | Operator |
| **POST** | `/workspaces/{id}/tasks/{task_id}/cancel` | Abort a running agent task loop | Operator |
| **GET** | `/workspaces/{id}/artifacts/{artifact_id}` | Download generated artifact (DOCX, PPTX, chart) | Operator |
| **GET** | `/audit` | Retrieve immutable audit event log with hash verification | Auditor |

---

## 3. Request & Response Payloads

### 3.1. Telemetry & Hardware State (`GET /api/v1/telemetry`)
**Response (200 OK):**
```json
{
  "timestamp": "2026-08-30T16:00:00Z",
  "airgap_status": {
    "is_isolated": true,
    "active_interfaces": ["Ethernet (Disconnected)", "Wi-Fi (Disabled)"],
    "external_dns_reachable": false,
    "wan_bytes_transmitted": 0
  },
  "hardware": {
    "gpu": {
      "device_name": "NVIDIA GeForce RTX 3050 Laptop GPU",
      "vram_total_mb": 4096,
      "vram_used_mb": 2560,
      "vram_free_mb": 1536,
      "gpu_utilization_pct": 67.0,
      "temperature_c": 58
    },
    "ram": {
      "total_mb": 16384,
      "used_mb": 8420,
      "free_mb": 7964,
      "system_utilization_pct": 51.4
    },
    "cpu": {
      "core_count": 8,
      "utilization_pct": 14.2
    }
  },
  "active_model": {
    "model_id": "qwen3:4b",
    "vram_allocated_mb": 2560,
    "status": "LOADED"
  }
}
```

### 3.2. Document Ingestion (`POST /api/v1/workspaces/{id}/documents`)
**Content-Type:** `multipart/form-data`  
**Form Parameters:**
- `files`: File payload list (PDF, XLSX, JPG, CSV, DOCX)
- `classification`: `"RESTRICTED_CONFIDENTIAL" | "INTERNAL_ENGINEERING" | "PUBLIC"`
- `enable_ocr`: `true | false` (Defaults to true for image/scanned PDF)

**Response (201 Created):**
```json
{
  "workspace_id": "ws_8f9c21",
  "ingested_count": 2,
  "documents": [
    {
      "id": "doc_0192a3",
      "filename": "inspection_report.pdf",
      "size_bytes": 1450230,
      "mime_type": "application/pdf",
      "page_count": 12,
      "chunk_count": 48,
      "ocr_applied": false,
      "status": "INDEXED",
      "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ]
}
```

### 3.3. Launch Agent Task (`POST /api/v1/workspaces/{id}/tasks`)
**Request Body:**
```json
{
  "prompt": "Analyze the inspection package, identify significant findings, cross-check them against the maintenance manual and historical data, assess the risk, and prepare an approval note.",
  "max_steps": 15,
  "auto_approve_risk_level": "MEDIUM",
  "requested_artifacts": ["DOCX_APPROVAL_NOTE", "DEFECT_TREND_CHART"]
}
```

**Server-Sent Events (SSE) Stream Structure:**
Every event transmitted over the SSE stream follows a standard typed envelope:
```
event: agent_event
data: {
  "task_id": "tsk_a98e10",
  "step_index": 1,
  "type": "THOUGHT | TOOL_CALL | APPROVAL_REQUIRED | OBSERVATION | ARTIFACT_GENERATED | COMPLETE | ERROR",
  "timestamp": "2026-08-30T16:01:10Z",
  "payload": {}
}
```

#### Example SSE Stream Traces:

1. **Agent Thought Event:**
```json
{
  "task_id": "tsk_a98e10",
  "step_index": 1,
  "type": "THOUGHT",
  "payload": {
    "reasoning": "We need to read the inspection report and extracted findings first. I will invoke search_knowledge to extract defect measurements.",
    "plan": [
      "1. Search knowledge vault for inspection report findings",
      "2. Extract historical thickness measurements from XLSX",
      "3. Cross-reference OEM wear tolerances from manual",
      "4. Calculate degradation velocity in sandbox",
      "5. Generate DOCX approval note"
    ]
  }
}
```

2. **Tool Invocation Event:**
```json
{
  "task_id": "tsk_a98e10",
  "step_index": 2,
  "type": "TOOL_CALL",
  "payload": {
    "tool_name": "run_python_sandbox",
    "call_id": "call_f901a",
    "arguments": {
      "script": "import pandas as pd\ndf = pd.read_excel('/workspace/input/maintenance_history.xlsx')\nprint(df.describe())"
    },
    "risk_level": "HIGH",
    "policy_status": "APPROVED_AUTOMATIC"
  }
}
```

3. **Approval Request (If Risk is Critical or Manual Gate Triggered):**
```json
{
  "task_id": "tsk_a98e10",
  "step_index": 4,
  "type": "APPROVAL_REQUIRED",
  "payload": {
    "approval_id": "appr_7710bc",
    "action_name": "run_python_sandbox",
    "description": "Execute statistical risk regression model on historical maintenance data.",
    "code_preview": "import statsmodels.api as sm\n...",
    "risk_reasons": ["Dynamic code execution inside Docker sandbox"]
  }
}
```

4. **Task Completion Event:**
```json
{
  "task_id": "tsk_a98e10",
  "step_index": 6,
  "type": "COMPLETE",
  "payload": {
    "summary": "Inspection analysis completed. Identified 2 critical wear points on Pump Impeller 3B exceeding OEM limits by 14.2%. Risk classified as Level 4 (High).",
    "citations": [
      {
        "citation_id": "CIT-01",
        "document_name": "inspection_report.pdf",
        "page_number": 4,
        "section": "3.2 Ultrasonic Thickness Gauging",
        "excerpt": "Minimum measured wall thickness: 3.42mm at node C-12."
      },
      {
        "citation_id": "CIT-02",
        "document_name": "maintenance_manual.pdf",
        "page_number": 88,
        "section": "Table 8.4 Minimum Allowable Shell Thickness",
        "excerpt": "Minimum allowable shell thickness before mandatory replacement is 4.00mm."
      }
    ],
    "artifacts": [
      {
        "id": "art_190f7",
        "filename": "Engineering_Approval_Note_Pump3B.docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "size_bytes": 48210
      }
    ]
  }
}
```

---

## 4. Error Responses

All API errors return RFC 7807 problem details:

```json
{
  "type": "https://sovereign-ai.local/errors/vram-exhaustion",
  "title": "GPU VRAM Allocation Limit Exceeded",
  "status": 503,
  "detail": "Failed to load gemma3:4b (requires 3.3 GB). Current free VRAM is 1.2 GB. Explicit eviction of qwen3:4b failed.",
  "instance": "/api/v1/models/swap",
  "error_code": "SOV_ERR_VRAM_OOM",
  "timestamp": "2026-08-30T16:02:40Z"
}
```
