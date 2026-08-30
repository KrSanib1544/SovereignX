# SOVEREIGN-X — SIH 2026 Flagship Demo Script & Presentation Guide

**Target Duration**: 5 to 7 Minutes
**Presentation Audience**: SIH Jury & Industrial AI Evaluators
**Scenario**: Autonomous Multi-Modal Integrity Assessment for Reflux Pump 3B (Hydrocarbon Processing Unit)
**Host Environment**: 100% Offline Windows 11 Workstation (RTX 3050 4GB VRAM, Ollama Local-Only)

---

## 🎬 Act 1: The Sovereign Problem & Zero-Trust Boundary (Minute 0:00 – 1:00)

### Operator Action:
1. Open the SOVEREIGN-X Command Center at `http://127.0.0.1:5173`.
2. Point out the live telemetry bar in the top navigation header:
   - **GPU**: NVIDIA RTX 3050 Laptop GPU (4.0 GB VRAM)
   - **VRAM Residency**: Sequential Model Arbitration Active
   - **Network**: **AIR-GAPPED (0 B WAN Egress)**
   - **Audit Chain**: **VALID (Continuous SHA-256 Hash Chain)**

### Pitch & Talking Points:
> *"Good morning, esteemed jury. High-security defense, nuclear, aerospace, and petrochemical plants possess millions of pages of classified schematics, NDT logs, and sensor feeds. Today, standard cloud AI solutions represent a catastrophic data exfiltration risk."*
>
> *"SOVEREIGN-X is our answer: a 100% sovereign, air-gapped agentic AI workbench running entirely on standard laptop hardware (4GB VRAM). Not a chatbot, and not a cloud wrapper—a verifiable multi-modal engineering agent that executes Python in a micro-isolated Docker container, retrieves facts with strict provenance, and records every action in a tamper-evident cryptographic ledger."*

---

## 🎬 Act 2: Multi-Modal Ingestion & The Knowledge Vault (Minute 1:00 – 2:30)

### Operator Action:
1. Navigate to the **Knowledge Vault** tab.
2. Select or create the workspace `ws_reflux_unit` (Classification: `RESTRICTED_CONFIDENTIAL`).
3. Showcase the 5 heterogeneous engineering assets:
   - `inspection_report.pdf`: Digital vector PDF with NDT ultrasonic thickness readings.
   - `scanned_report.pdf`: Scanned technician dye-penetrant examination sheet.
   - `equipment_photo.jpg`: Macro photograph of casing weld seam W-202.
   - `maintenance_history.xlsx`: 5-year longitudinal historical thickness workbook.
   - `maintenance_manual.pdf`: OEM technical manual with mandatory replacement tolerances.
4. Highlight that PyMuPDF parses digital PDFs, local OCR parses scanned blue-collar logs, and FastEmbed ONNX indexes dense vectors locally into Qdrant in under 5 seconds.

### Pitch & Talking Points:
> *"Industrial data is messy and multi-format. Here we have five distinct assets: digital vector tables, a scanned paper dye-penetrant log, macro defect photos, a 5-year Excel log, and an OEM technical manual. Our ingestion pipeline parses and indexes all five locally in under 5 seconds without a single byte leaving this computer."*

---

## 🎬 Act 3: Agentic Task Execution & Real VRAM Model Swapping (Minute 2:30 – 4:30)

### Operator Action:
1. Navigate to the **AI Workspace** tab.
2. Enter the prompt:
   ```text
   Assess structural integrity of Reflux Pump 3B. Correlate ultrasonic thickness measurements, visual weld defects, and 5-year historical thinning rate against OEM limits. Compile a certified Engineering Approval Note (.docx) with citations.
   ```
3. Click **Execute Task**.
4. Observe the live ReAct reasoning stream:
   - **Step 1**: Agent calls `search_vault` to extract ultrasonic thickness (Finds Node C-12 = $3.42\text{ mm}$).
   - **Step 2**: Agent selects `inspect_image`. Watch the VRAM Arbitrator evict `qwen3:4b` and load `gemma3:4b` into VRAM (Peak VRAM: 3.47 GB). Gemma 3 detects the $48\text{ mm}$ longitudinal fatigue crack.
   - **Step 3**: Agent swaps back to `qwen3:4b` and requests `run_python` to compute the linear regression degradation slope on `maintenance_history.xlsx`.
   - **Step 4**: Highlight the Docker Sandbox security envelope (`--network none`, non-root UID 10001, 512MB RAM cap). Regression calculates $0.259\text{ mm/year}$ thinning rate.
   - **Step 5**: Agent cross-checks Table 8.4 of OEM manual, discovering the $4.00\text{ mm}$ mandatory replacement threshold.
   - **Step 6**: Agent synthesizes the **Level 5 Critical Failure Risk** ($3.42\text{ mm}$ vs $4.00\text{ mm}$, $-14.5\%$ deficit) and invokes `generate_docx`.

### Pitch & Talking Points:
> *"Notice what is happening under the hood: on our 4GB GPU, running both reasoning and vision models simultaneously would trigger a CUDA Out-of-Memory crash. SOVEREIGN-X's Model Router sequentially orchestrates model residency in seconds. When data analysis is required, the LLM NEVER executes code on Windows—it runs inside a sandboxed Linux container with zero network access and a 512MB memory ceiling."*

---

## 🎬 Act 4: Verifiable Artifacts & Evidence Inspection (Minute 4:30 – 5:30)

### Operator Action:
1. Navigate to the **Evidence Viewer** tab.
2. Click on the citations `[CIT-01]` through `[CIT-04]`.
3. Show the exact page numbers, extracted quotes, and provenance links.
4. Open the generated `Engineering_Approval_Note_Pump3B.docx` artifact in `data/workspaces/.../artifacts/` or via the UI.
5. Highlight the structured findings table, computed regression statistics, emergency shutdown recommendation, and sign-off block.

### Pitch & Talking Points:
> *"In safety-critical manufacturing, hallucinations cause plant explosions. Every single statement in this generated Engineering Approval Note is grounded by an explicit citation linking to the exact page and row of source evidence."*

---

## 🎬 Act 5: Cryptographic Audit Trail & Closing (Minute 5:30 – 6:30)

### Operator Action:
1. Navigate to the **Audit Monitor** tab.
2. Click **Verify Cryptographic Chain**.
3. Point out the SHA-256 hash chaining across every prompt, tool call, policy gate, and artifact generation.
4. Show the mathematical verification result: **100% UNTAMPERED (VALID)**.

### Pitch & Talking Points:
> *"Finally, compliance officers require absolute transparency. SOVEREIGN-X binds every prompt, policy evaluation, sandbox output, and deliverable into an immutable SHA-256 hash chain. If a single byte in the database is modified, the mathematical verification immediately flags the break."*
>
> *"SOVEREIGN-X delivers true AI sovereignty: air-gapped, verifiable, resource-efficient, and enterprise-ready today. Thank you!"*
