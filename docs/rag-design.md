# SOVEREIGN-X — Retrieval-Augmented Generation (RAG) Architecture

---

## 1. Local RAG Pipeline Overview

The SOVEREIGN-X RAG subsystem provides 100% air-gapped, verifiable semantic search and structured technical retrieval over industrial engineering documents, scanned inspection logs, equipment manuals, and maintenance spreadsheets.

```
+-------------------------------------------------------------------------------------------------------------+
|                                        INGESTION & EXTRACTION STAGE                                         |
+-------------------------------------------------------------------------------------------------------------+
   Raw File (PDF / Scanned PDF / Image / XLSX / CSV)
       │
       ▼
   File Type Validator & Security Scanner (Magic Byte check, Path sanitizer)
       │
       ├── Digital PDF ────────> PyMuPDF (Extract native text, fonts, tables, bounding rects)
       ├── Scanned PDF / Image ─> PaddleOCR-light / Tesseract (Bounding boxes + text confidence)
       └── XLSX / CSV ─────────> openpyxl / pandas (Extract sheets, schema, rows into Markdown tables)
       │
       ▼
   Document Normalization Engine (Strip control characters, standardize whitespace, fix OCR artifacts)
       │
       ▼
   Hierarchical & Semantic Chunking Engine (500 tokens / 100 overlap + Heading / Page metadata preservation)
       │
       ▼
   Local ONNX Dense Embeddings (FastEmbed: `bge-small-en-v1.5`, 384 dimensions, CPU/ONNX runtime)
       │
       ▼
   Qdrant Vector Database (`sovereign_rag` collection, Cosine distance, HNSW Index)
       │
       ▼
   SQLite Document & Chunk Provenance Registry (Document ID, Page, Section, Bounding Box JSON)

+-------------------------------------------------------------------------------------------------------------+
|                                           RETRIEVAL & SYNTHESIS STAGE                                       |
+-------------------------------------------------------------------------------------------------------------+
   Agent Query: "What is the minimum allowable shell thickness for Pump Impeller 3B?"
       │
       ▼
   Query Vector Computation (FastEmbed local ONNX model)
       │
       ▼
   Pre-Retrieval Authorization Filter (Qdrant Payload Filter: workspace_id == active AND class <= user_role)
       │
       ▼
   Dense Vector Search (Top-K = 6 candidate chunks)
       │
       ▼
   Local Score Thresholding (Cosine similarity >= 0.65 filter to eliminate hallucinations)
       │
       ▼
   Provenance Assembly (Attach exact Document Name, Page Number, Section Title, BBox)
       │
       ▼
   Context Injection into Agent Prompt (Structured Citation Schema: `[CIT-X: doc.pdf#p=4]`)
       │
       ▼
   LLM Generates Finding with Verifiable Citations
```

---

## 2. Document Processing & Ingestion Engines

### 2.1. Digital PDF Processing (`PyMuPDF`)
- Extracts native text blocks with exact font size, bold flags, and coordinates $(x_0, y_0, x_1, y_1)$.
- Extracts embedded vector tables using table-structure detection.
- Preserves document hierarchy (e.g., `# Section 3.2 Ultrasonic Thickness Gauging`).

### 2.2. Scanned Document OCR Pipeline
- Automatic scanned-page detection: If text density on a page is $< 50$ characters, trigger the offline OCR engine.
- Extracts recognized words, line groupings, confidence scores ($0.0 - 1.0$), and bounding boxes normalized to $[0, 1000]$ coordinates.
- Low-confidence words ($< 0.40$) are flagged for manual verification in the UI.

### 2.3. Tabular & Spreadsheet Processing (`openpyxl` / `pandas`)
- Ingests `.xlsx`, `.xls`, and `.csv`.
- Generates a dual representation:
  1. **Schema & Statistical Summary Chunk**: Table name, column headers, data types, min/max/mean metrics for numerical columns.
  2. **Row Block Chunks**: Groupings of 20–30 rows rendered into clean Markdown table format with preserved column headers on every chunk.

---

## 3. Chunking Strategy & Provenance Schema

To prevent lost context and broken table structures, chunking is strictly hierarchical:

- **Target Chunk Size**: ~400–500 tokens (approx. 1,500–2,000 characters).
- **Chunk Overlap**: 80 tokens (~300 characters).
- **Separators (in order of priority)**:
  1. Header transitions (`\n# `, `\n## `, `\n### `)
  2. Table boundaries (`\n\n|`)
  3. Paragraph breaks (`\n\n`)
  4. Sentence endings (`. `, `! `, `? `)
  5. Whitespace (` `)

### Chunk Metadata Invariant
Every chunk stored in SQLite and Qdrant **must** carry the following immutable metadata:
```json
{
  "chunk_id": "chk_09f18b",
  "document_id": "doc_0192a3",
  "workspace_id": "ws_8f9c21",
  "filename": "inspection_report.pdf",
  "page_number": 4,
  "section_title": "3.2 Ultrasonic Thickness Gauging",
  "classification": "RESTRICTED_CONFIDENTIAL",
  "bbox": [45.2, 110.0, 520.5, 340.8],
  "token_count": 420
}
```

---

## 4. Local Embeddings Architecture

- **Model**: `BAAI/bge-small-en-v1.5`
- **Execution Engine**: `FastEmbed` (ONNX Runtime, Quantized INT8 / FP32 CPU execution).
- **Resource Footprint**:
  - Model disk size: ~130 MB
  - Inference RAM: ~200 MB
  - Embedding latency: ~15 ms per chunk on 8-core laptop CPU.
  - Zero GPU VRAM usage (leaving 100% of 4 GB VRAM for Qwen3 / Gemma3).
- **Vector Dimension**: 384 dimensions.
- **Distance Metric**: Cosine Similarity.

---

## 5. Pre-Retrieval Security & Authorization

To eliminate information disclosure across workspaces or permission levels:
1. Retrieval queries **never** perform broad global searches.
2. Every Qdrant query includes a mandatory strict payload filter:
   ```python
   Filter(
       must=[
           FieldCondition(key="workspace_id", match=MatchValue(value=current_workspace_id)),
           FieldCondition(key="classification", match=MatchAny(any=user_allowed_classifications)),
       ]
   )
   ```
3. Chunks from unauthorized documents are physically pruned before vector similarity calculation, ensuring the LLM never sees unauthorized fragments in its context.

---

## 6. Citation Binding & Evidence UI Model

When findings are returned to the user, every key claim is linked to an interactive citation token:

```
[Finding] Pump Impeller 3B shell wall thickness has degraded to 3.42mm.
[Citation: CIT-01]
├── Source Document: inspection_report.pdf
├── Page: 4
├── Section: 3.2 Ultrasonic Thickness Gauging
├── Extracted Excerpt: "Node C-12 measured thickness: 3.42mm (Baseline: 4.80mm)."
└── Bounding Box: [x: 45.2, y: 110.0, w: 475.3, h: 230.8]
```

In the React frontend, clicking **[CIT-01]** immediately splits the screen and renders the PDF viewer focused on Page 4 with the ultrasonic measurement table highlighted in yellow.
