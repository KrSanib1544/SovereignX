# SOVEREIGN-X — Flagship Demonstration Workflow & Industrial Scenario

---

## 1. Flagship Demonstration Context

- **Scenario**: Critical Industrial Plant Inspection Package (Chemical Processing / Hydrocarbon Reflux Unit).
- **Goal**: Autonomous, air-gapped cross-modal analysis of heterogeneous engineering data to identify equipment wall degradation and surface fatigue, verify OEM safety tolerances, calculate remaining component lifespan, and compile a verifiable **Engineering Approval Note (.docx)** with source citations.
- **Hardware Requirement**: Single Windows 11 Laptop, 16 GB RAM, NVIDIA RTX 3050 Laptop GPU (4 GB VRAM), 100% Offline (Wi-Fi OFF).

---

## 2. Ingested Inspection Package Assets

| Asset Filename | File Type | Content Description | Ingestion Engine |
| :--- | :--- | :--- | :--- |
| **`inspection_report.pdf`** | Digital Vector PDF (12 pages) | Recent non-destructive testing (NDT) report for Reflux Pump 3B. Contains ultrasonic wall thickness tables. | PyMuPDF Text & Vector Table Extractor |
| **`scanned_report.pdf`** | Scanned Raster PDF (2 pages) | Field technician's handwritten & stamped dye-penetrant inspection log indicating weld seam porosity. | Offline PaddleOCR-light / Tesseract |
| **`equipment_photo.jpg`** | High-Res Color Image | Close-up macro photograph of Reflux Pump 3B casing weld seam showing visible crack. | Local Gemma3 4B Vision Model (`inspect_image`) |
| **`maintenance_history.xlsx`** | Excel Workbook (3 sheets) | 5-year longitudinal records of wall thickness measurements, vibration levels, and maintenance dates. | `openpyxl` / `pandas` in Docker Sandbox |
| **`maintenance_manual.pdf`** | OEM Technical Manual (140 pages) | Manufacturer specification document containing safety tolerances, minimum wall thickness tables, and replacement criteria. | PyMuPDF + FastEmbed + Qdrant Index |

---

## 3. The Demonstration Execution Trace

### Phase 1: Ingestion & Multi-Modal Indexing (Time: ~15s)
1. The operator drags and drops the 5 files into the **Knowledge Vault**.
2. **PyMuPDF** parses `inspection_report.pdf` and `maintenance_manual.pdf`.
3. **OCR Engine** processes `scanned_report.pdf`, extracting coordinates for stamped notes.
4. **FastEmbed (`bge-small-en-v1.5`)** computes 384-dimensional dense vectors on CPU and indexes them into local **Qdrant**.
5. Metadata records and SHA-256 file hashes are committed to **SQLite**.

---

### Phase 2: Agent Task Initiation
**Operator Prompt**:
> *"Analyze the inspection package, identify significant findings, cross-check them against the maintenance manual and historical data, assess the risk, and prepare an approval note."*

The **Agent Orchestrator** launches `qwen3:4b` in 2.5 GB VRAM and generates a 5-step operational plan:

```
[PLAN]
1. Search indexed documents for recent NDT ultrasonic thickness readings for Pump 3B.
2. Unload reasoning model, load Gemma3 4B, and visually inspect `equipment_photo.jpg` for crack dimensions.
3. Execute statistical regression script in Docker sandbox to calculate annual wall thinning rate from `maintenance_history.xlsx`.
4. Query knowledge vault for OEM minimum allowable shell thickness from `maintenance_manual.pdf`.
5. Synthesize findings, calculate remaining asset lifespan, and generate formal `Approval_Note_Pump3B.docx`.
```

---

### Phase 3: Step-by-Step Tool Execution

#### Step 1: Query Recent Inspection Findings
- **Tool**: `search_knowledge(query="Pump 3B ultrasonic wall thickness measurements node C-12", top_k=3)`
- **Observation**:
  - `inspection_report.pdf` (Page 4, Section 3.2): Minimum measured wall thickness is **3.42 mm** at Casing Node C-12. Baseline was 4.80 mm.

#### Step 2: Visual Flaw Inspection (Model Swap to Gemma3 4B)
- **Arbitrator Action**: Explicitly evicts `qwen3:4b` from VRAM ($2.5\text{ GB} \rightarrow 0\text{ MB}$), loads `gemma3:4b` ($3.3\text{ GB}$ into VRAM).
- **Tool**: `inspect_image(image_filename="equipment_photo.jpg", inspection_prompt="Detect weld seam anomalies, crack length and aperture")`
- **Observation**:
  - Surface defect detected along weld seam: **Longitudinal fatigue crack**, estimated length **48 mm**, aperture **1.4 mm**. Severity: **HIGH**.
- **Arbitrator Action**: Unloads `gemma3:4b`, reloads `qwen3:4b` into VRAM.

#### Step 3: Tabular Analysis in Isolated Docker Sandbox
- **Tool**: `run_python_sandbox(script="...")`
  ```python
  import pandas as pd
  import numpy as np

  df = pd.read_excel('/workspace/input/maintenance_history.xlsx', sheet_name='Thickness_Log')
  p3b = df[df['Component'] == 'Pump_3B_Casing']
  # Calculate linear annual corrosion rate
  years = p3b['Year'].values
  thickness = p3b['Thickness_mm'].values
  rate = -np.polyfit(years, thickness, 1)[0]
  print(f"Historical Wall Thinning Rate: {rate:.3f} mm/year")
  ```
- **Execution**: Micro-container starts with `--network none`, runs script in 1.1 seconds, and returns:
- **Observation**:
  - `Historical Wall Thinning Rate: 0.215 mm/year`.

#### Step 4: OEM Tolerance Cross-Check
- **Tool**: `search_knowledge(query="Pump 3B minimum allowable shell thickness replacement limit", filter_document="maintenance_manual.pdf")`
- **Observation**:
  - `maintenance_manual.pdf` (Page 88, Table 8.4): Mandatory replacement threshold for Pump 3B shell casing is **4.00 mm**. Current operation below 4.00 mm poses severe risk of catastrophic rupture.

#### Step 5: Risk Synthesis & Engineering Calculation
The agent performs deterministic comparative analysis:
- **Current Thickness**: $3.42\text{ mm}$ (Below OEM limit of $4.00\text{ mm}$ by $-0.58\text{ mm}$ / $-14.5\%$).
- **Weld Integrity**: 48 mm surface crack confirmed via Gemma3 visual analysis.
- **Risk Classification**: **LEVEL 5 — CRITICAL (IMMEDIATE SHUTDOWN & REPLACEMENT REQUIRED)**.

#### Step 6: Artifact Assembly & Audit Finalization
- **Tool**: `generate_docx(output_filename="Engineering_Approval_Note_Pump3B.docx", ...)`
- **Observation**:
  - File written to `./data/workspaces/ws_8f9c21/artifacts/Engineering_Approval_Note_Pump3B.docx` (48.2 KB).
  - SHA-256 Hash: `7f8a9...b012`.
  - Final audit record chained and committed to SQLite.

---

## 4. UI Final State & Deliverables

1. **Interactive Summary Tab**:
   - Displays executive verdict, risk matrix, and calculated parameters.
   - Every claim features clickable citation badges (`[CIT-01]`, `[CIT-02]`, `[CIT-03]`).
2. **Split-Screen Evidence Inspector**:
   - Clicking `[CIT-01]` loads `inspection_report.pdf` at Page 4 with the thickness table highlighted.
   - Clicking `[CIT-03]` displays the macro photograph with the crack region highlighted.
3. **Download Deliverables**:
   - One-click download for `Engineering_Approval_Note_Pump3B.docx`.
   - Direct export of the complete cryptographic Audit Trail (`audit_log_ws8f9c21.jsonl`).
