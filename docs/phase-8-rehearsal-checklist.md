# SOVEREIGN-X — Phase 8 Rehearsal & Live Demonstration Checklist

---

## 1. Pre-Presentation Environmental Setup (T-minus 15 Minutes)

- [ ] **Physical Hardware & Power**:
  - Laptop plugged into AC mains power (High Performance / Ultimate GPU power profile enabled in Windows Settings).
  - External display / projector connected and configured to Duplicate or Extend mode ($1920 \times 1080$ resolution recommended).
- [ ] **Network Air-Gap Status**:
  - Wi-Fi switched **OFF** or disconnected to prove air-gap capabilities to evaluators.
- [ ] **Ollama Local Daemon**:
  - Ensure Ollama is running: `curl http://127.0.0.1:11434/api/tags`
  - Verify required models are pulled:
    ```bash
    ollama list
    # Expected: qwen3:4b, gemma3:4b
    ```
- [ ] **Docker Desktop Daemon**:
  - Docker Desktop is running.
  - Verify sandbox image exists:
    ```bash
    docker images sovereign-sandbox:1.0
    ```
- [ ] **Run Pre-Release Verification Script**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\verify_release.ps1
  ```
  *(Confirm all 8 checks pass with 0 errors)*.

---

## 2. Service Launch & Clean State

- [ ] **Start Sovereign-X Services**:
  ```cmd
  scripts\run_dev.bat
  ```
  - Backend running at: `http://127.0.0.1:8000/docs`
  - Frontend running at: `http://127.0.0.1:5173`
- [ ] **Browser Tabs Prepared**:
  - Tab 1: Sovereign-X Workbench (`http://127.0.0.1:5173`)
  - Tab 2: Terminal open for `nvidia-smi` or `ollama ps` live demonstrations if requested by technical judges.

---

## 3. Live Demo Rehearsal Flow & Verification

| Step | Action | Expected Outcome | Failure Mitigation |
| :--- | :--- | :--- | :--- |
| **1. Command Center** | View System Telemetry | RTX 3050 GPU detected, Air-Gap status green, Audit chain valid | Click "Refresh Hardware Telemetry" if polling was paused. |
| **2. Knowledge Vault** | Ingest Demo Package | 5 assets parsed, indexed, and displayed in < 5s | Assets exist in `demo/assets/`; re-upload if workspace is empty. |
| **3. AI Workspace** | Execute Task Prompt | Agent streams 6 reasoning steps with tool calls | Ensure Ollama is active on `127.0.0.1:11434`. |
| **4. Model Swapping** | Gemma3 Vision Tool | Gemma3 loads into VRAM (3.47 GB), inspects image, swaps back | Router handles eviction automatically with 5m keepalive. |
| **5. Docker Sandbox** | Tabular Regression | Pandas script calculates $0.259\text{ mm/yr}$ slope in < 1.5s | Verify Docker Desktop icon is green in system tray. |
| **6. Evidence & Output** | View Artifacts & Citations | `Engineering_Approval_Note_Pump3B.docx` created ($38\text{ KB}$) | Artifact resides at `./data/workspaces/<ws_id>/artifacts/`. |
| **7. Audit Monitor** | Cryptographic Verification | Traverses audit chain $\rightarrow$ **100% UNTAMPERED (VALID)** | Continuous hash chain validates all logged operations. |

---

## 4. Emergency Backup & Fallback Strategies

1. **CLI Headless Demonstration**:
   - If frontend browser hangs or encounters an unexpected UI issue, execute the master CLI harness in terminal:
     ```cmd
     .venv\Scripts\python scripts\run_flagship_demo.py
     ```
   - Prints full hardware benchmarks, model residency logs, Docker stdout, and verifies audit chain in 48 seconds.
2. **Clean Process Reset**:
   - If port conflict occurs:
     ```cmd
     scripts\stop_dev.bat
     scripts\run_dev.bat
     ```
3. **Database Reset**:
   - Workspaces and audit logs are safely stored in SQLite at `./data/sovereign.db`. If corrupted during tests, delete `data/sovereign.db` and re-run backend to reinitialize clean tables.
