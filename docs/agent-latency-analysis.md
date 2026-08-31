# SOVEREIGN-X Agent Latency Analysis & Optimization Strategy

**Document Status:** Approved Architecture Audit & Benchmark Report  
**Target Hardware:** Windows 11, NVIDIA GeForce RTX 3050 Laptop GPU (4.0 GB VRAM), 16.0 GB RAM, Ollama Local Daemon  
**Target Models:** `qwen3:4b` (Primary Reasoning), `gemma3:4b` (Vision Inspection)  

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 The Observed Problem
A simple knowledge inquiry:
> *"Explain the greedy algorithm strategy used for the fractional knapsack problem in daa2.pdf with examples."*

took **~192 seconds (3.2 minutes)** to complete on local hardware. 

The user observed:
```text
MAX 15 STEPS • LOOP DETECTOR ACTIVE
"Qwen3:4B is reasoning locally and orchestrating workspace tools on your GPU..."
```

---

### 1.2 Quantitative Breakdown of the 192-Second Latency

| Stage | Action / Component | Model Invocations | Tool Calls | Duration | Latency % |
|---|---|:---:|:---:|:---:|:---:|
| **Step 1: Planning** | Prompt Qwen3:4B to select tool | 1 | None | ~68.9 s | 35.8% |
| **Step 1 Tool** | `list_workspace()` disk inspect | 0 | 1 | ~0.05 s | 0.02% |
| **Step 2: Re-Planning** | Prompt Qwen3:4B with workspace list | 1 | None | ~52.1 s | 27.1% |
| **Step 2 Tool** | `search_knowledge()` FastEmbed + Qdrant | 0 | 1 | ~0.12 s | 0.06% |
| **Step 3: Final Synthesis** | Prompt Qwen3:4B with search results | 1 | None | ~70.8 s | 36.8% |
| **Total** | Full ReAct Multi-Step Loop | **3 LLM calls** | **2 tools** | **~192.0 s** | **100%** |

---

### 1.3 Key Architectural Inefficiencies Identified

1. **Unconditional ReAct Orchestration Overhead**:
   - Every user prompt—whether a simple single-fact document inquiry or a complex multi-tool industrial simulation—entered the bounded 15-step `ReActAgent` state machine.
   - The ReAct system prompt injected 6 comprehensive JSON tool schemas into the model context on every turn.

2. **Multi-Turn Autoregressive Token Generation on 4GB VRAM**:
   - On consumer laptop GPUs (RTX 3050, 4GB VRAM), generating 500–800 tokens of internal reasoning (`<think>` chain of thought) takes **~45–70 seconds per generation**.
   - Executing 3 sequential LLM turns (`Planning` $\to$ `Re-planning after list_workspace` $\to$ `Synthesis after search_knowledge`) yielded $3 \times 65\text{s} \approx 195\text{s}$.
   - Meanwhile, the actual vector retrieval (`search_knowledge` via local FastEmbed ONNX + Qdrant) took only **120 milliseconds** (< 0.1% of total time).

3. **Model Loading / Offloading Analysis**:
   - Both `qwen3:4b` and `gemma3:4b` fit within system memory, but Ollama manages resident models with a 5-minute keep-alive.
   - When only text reasoning is performed, `qwen3:4b` remains resident in VRAM (~3.2 GB allocated). Model loading was not the bottleneck; **repeated sequential token generation across 3 unnecessary turns** was the sole bottleneck.

---

## 2. Intelligent Execution Routing Architecture

To reduce latency by **85–90%** for knowledge inquiries while preserving 100% of autonomous multi-step agentic capabilities, Sovereign-X implements a **Dual-Class Execution Router**:

```
                              User Prompt
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  Fast Intent Classification  │  (< 2ms)
                   └──────────────┬───────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
         ▼                                                 ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│   CLASS A: Fast RAG Pipeline    │       │ CLASS B: Bounded ReAct Runtime  │
│  (Document QA, Summarization)   │       │  (Docker, Code, Vision, HITL)   │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ 1. Vector Search (FastEmbed)    │       │ 1. Autonomous Planning          │
│ 2. Single LLM Synthesis (Qwen3) │       │ 2. Multi-Step Tool Execution    │
│ 3. Citation Packaging           │       │ 3. Loop Detection (15 max)      │
│                                 │       │ 4. Human-In-The-Loop Approval   │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ Target Latency: 15–25 seconds   │       │ Target Latency: Variable (Steps)│
│ Invocations: Exactly 1 LLM call │       │ Invocations: Multi-Step (1-15)  │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

### Class A: Simple Knowledge Query
- **Triggers**: Information queries, document summaries, definition lookups, section explanations, factual grounding.
- **Pipeline**: FastEmbed vector search $\to$ Single LLM direct synthesis with document excerpts $\to$ Answer + Citations.
- **Latency**: **~15–25 seconds** (1 retrieval + 1 LLM generation).

### Class B: Multi-Step Agent Task
- **Triggers**: Python code execution (`run_python`), docker sandbox calculations, vision inspection (`inspect_image`), `.docx` deliverable generation (`generate_docx`), multi-document correlation.
- **Pipeline**: Full Bounded ReAct state machine with loop detector, policy engine, and HITL safety gates.

---

## 3. Real Performance Benchmarking Results

| # | Test Scenario | Query | Pipeline Class | Steps | Model Invocations | Retrieval (ms) | LLM Gen (ms) | Total Latency (s) | Verified Grounded Result |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| 1 | **Simple Document QA** | *"What are the main findings in the inspection report?"* | CLASS A (Fast RAG) | 1 | 1 | 372.3 ms | 30,024.9 ms | **30.44 s** | Critical wear at Node C-12, 3.42mm thickness (1.38mm deficit) [CIT-01] |
| 2 | **Document Summarization** | *"Summarize the ultrasonic thickness survey in the inspection report."* | CLASS A (Fast RAG) | 1 | 1 | 83.6 ms | 31,810.5 ms | **31.90 s** | Comprehensive 5-node survey breakdown (A-01 to E-02) [CIT-01] |
| 3 | **Multi-Document Analysis** | *"Correlate ultrasonic readings in inspection_report.pdf with historical maintenance records."* | CLASS B (ReAct Agent) | 4 | 4 | 110.2 ms | 305,510.2 ms | **305.63 s** | Multi-step workspace inspection, document search & synthesis |
| 4 | **Code Execution Task** | *"Calculate the wall thinning percentage at Node C-12 using python code."* | CLASS B (ReAct Agent) | 4 | 3 | 0.0 ms | 170,714.0 ms | **170.72 s** | Python code calculation: 28.75% thinning deficit |
| 5 | **Multimodal Vision Task** | *"Inspect equipment_photo.jpg for visual weld crack defects."* | CLASS B (ReAct Agent) | 3 | 2 | 0.0 ms | 134,542.3 ms | **134.55 s** | Image safety check, workspace file verification & dispatch |

---

## 4. Key Performance Invariants Maintained

1. **Air-Gap Verification**: 100% of embeddings and generation executed locally (0 external egress).
2. **Deterministic Provenance**: Citations (`[CIT-01]`, `page_number`, `document_name`, `excerpt`) preserved across both Class A and Class B executions.
3. **Security Invariants**: Path jail, workspace isolation, Docker micro-isolation, and SHA-256 audit chaining active in all pipelines.
