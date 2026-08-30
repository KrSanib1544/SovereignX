# SOVEREIGN-X — Tool Registry & Security Policy Specification

---

## 1. Zero-Trust Tool Architecture

In SOVEREIGN-X, tools are strictly typed, declarative, isolated execution units. The LLM cannot invoke arbitrary functions or call operating system APIs. Every tool invocation passes through a mandatory 4-stage pipeline:

```
[ LLM Proposed Action ] 
         │
         ▼
 1. Typed Pydantic Schema Validation (Strict type checking, regex constraint on paths)
         │
         ▼
 2. Policy Engine & Access Boundary Check (Workspace jail, Risk evaluation, Human approval gate)
         │
         ▼
 3. Sandboxed / Controlled Service Execution (Ephemeral Docker for code, localized parsers)
         │
         ▼
 4. Output Sanitization & Truncation (Max 64KB, strip control sequences, log SHA-256 audit entry)
```

---

## 2. Tool Risk Matrix & Governance

Every tool has an immutable Risk Level and execution boundary:

| Tool Name | Purpose | Risk Level | Execution Boundary | Requires Human Gate? |
| :--- | :--- | :--- | :--- | :--- |
| **`list_workspace`** | List ingested files and artifacts | `LOW` | Read-only SQLite / FS query | No (Auto) |
| **`read_file`** | Read text/markdown/CSV files | `LOW` | Read-only inside `./data/workspaces/{id}/` | No (Auto) |
| **`search_knowledge`** | Dense vector search with citations | `LOW` | Read-only Qdrant query | No (Auto) |
| **`read_pdf`** | Extract text & structure from PDF | `LOW` | PyMuPDF in-memory parser | No (Auto) |
| **`read_excel`** | Extract sheet names & headers | `LOW` | openpyxl read-only mode | No (Auto) |
| **`analyze_csv`** | Return statistical summary of CSV | `LOW` | pandas in-memory read | No (Auto) |
| **`inspect_image`** | Multimodal visual flaw analysis | `MEDIUM` | Gemma3 VRAM-swapped inference | No (Auto) |
| **`write_file`** | Save text/JSON file in scratch area | `MEDIUM` | Write restricted to `./data/workspaces/{id}/scratch/` | No (Auto) |
| **`generate_docx`** | Build structured Word document | `MEDIUM` | python-docx builder in artifacts dir | No (Auto) |
| **`generate_pptx`** | Build executive presentation slides | `MEDIUM` | python-pptx builder in artifacts dir | No (Auto) |
| **`run_python_sandbox`** | Execute Python data/math script | `HIGH` | Isolated Docker Container (`--net=none`, 512MB RAM) | Configurable / Yes |

---

## 3. Tool Specifications & Pydantic Schemas

### 3.1. `search_knowledge`
- **Description**: Perform dense semantic vector retrieval over indexed workspace documents.
- **Input Schema**:
  ```json
  {
    "query": { "type": "string", "description": "The natural language search query" },
    "top_k": { "type": "integer", "default": 4, "minimum": 1, "maximum": 8 },
    "filter_document": { "type": "string", "description": "Optional filename to restrict search" }
  }
  ```
- **Output Schema**:
  ```json
  {
    "results": [
      {
        "citation_id": "CIT-01",
        "document_name": "maintenance_manual.pdf",
        "page_number": 88,
        "section": "Table 8.4",
        "content": "Minimum allowable shell thickness...",
        "score": 0.884
      }
    ]
  }
  ```

### 3.2. `inspect_image`
- **Description**: Trigger local multimodal model (`gemma3:4b`) to inspect an image, engineering drawing, or photo for physical cracks, rust, or layout details.
- **Input Schema**:
  ```json
  {
    "image_filename": { "type": "string", "description": "Relative filename within workspace" },
    "inspection_prompt": { "type": "string", "description": "Specific visual features to look for" }
  }
  ```
- **Output Schema**:
  ```json
  {
    "visual_findings": "Identified longitudinal surface crack near weld seam...",
    "estimated_dimensions": "Approx. 45mm length, 1.2mm aperture",
    "severity": "CRITICAL_DEFECT",
    "confidence": 0.92
  }
  ```

### 3.3. `run_python_sandbox`
- **Description**: Execute a Python data analysis, statistical regression, or plotting script inside an isolated micro-container.
- **Input Schema**:
  ```json
  {
    "script": { "type": "string", "description": "Complete executable Python 3.11 code snippet" },
    "timeout_seconds": { "type": "integer", "default": 15, "maximum": 30 }
  }
  ```
- **Output Schema**:
  ```json
  {
    "exit_code": 0,
    "stdout": "Calculated annual corrosion rate: 0.18mm/yr. Remaining life: 1.8 years.\n",
    "stderr": "",
    "generated_files": ["corrosion_trend_chart.png"],
    "execution_time_ms": 1240
  }
  ```

### 3.4. `generate_docx`
- **Description**: Assemble a formal industrial Engineering Approval Note or Inspection Compliance Summary document.
- **Input Schema**:
  ```json
  {
    "output_filename": { "type": "string", "description": "Deliverable filename (e.g., Approval_Note_Pump3B.docx)" },
    "title": { "type": "string" },
    "executive_summary": { "type": "string" },
    "findings_table": [
      {
        "component": "string",
        "observed_defect": "string",
        "oem_threshold": "string",
        "risk_level": "string",
        "citation": "string"
      }
    ],
    "recommendations": [{ "type": "string" }],
    "signoff_block": { "author": "string", "role": "string", "date": "string" }
  }
  ```

---

## 4. Path Traversal & File Jail Policy

To permanently prevent directory traversal vulnerabilities (e.g., `../../Windows/System32`):

```python
def resolve_secure_workspace_path(workspace_id: str, relative_path: str, must_exist: bool = True) -> Path:
    base_dir = (Path("./data/workspaces") / workspace_id).resolve()
    
    # Strip dangerous characters & sanitize
    clean_relative = os.path.normpath(relative_path).lstrip("\\/.")
    target_path = (base_dir / clean_relative).resolve()
    
    # Enforce strict jail containment
    if not str(target_path).startswith(str(base_dir)):
        raise SecurityPolicyViolationError(
            f"Path traversal detected! Path '{relative_path}' attempts to escape workspace root '{base_dir}'."
        )
        
    if must_exist and not target_path.exists():
        raise FileNotFoundError(f"Requested file '{relative_path}' not found in workspace.")
        
    return target_path
```

---

## 5. Audit Logging Invariant

Every tool execution emits an immutable audit event:
$$\text{Event} = \{\text{UUID}, \text{Timestamp}, \text{TaskID}, \text{ToolName}, \text{RiskLevel}, \text{ArgumentsHash}, \text{ExitCode}, \text{DurationMS}\}$$
This event is cryptographically linked to the preceding entry in SQLite before results are returned to the agent loop.
