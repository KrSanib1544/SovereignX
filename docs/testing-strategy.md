# SOVEREIGN-X — Comprehensive Testing & Quality Assurance Strategy

---

## 1. Testing Pyramid & Verification Objectives

SOVEREIGN-X operates in zero-trust, high-consequence industrial environments. The testing strategy enforces four strict test tiers:

```
                          ▲
                         / \
                        /   \     TIER 4: Offline & Air-Gap Verification (Zero WAN sockets)
                       / T4  \
                      /───────\
                     /  TIER 3 \   TIER 3: Security & Penetration Suite (Path traversal, Sandbox escapes)
                    /    T3     \
                   /─────────────\
                  /    TIER 2     \  TIER 2: End-to-End Agentic Integration & Model Swapping
                 /       T2        \
                /───────────────────\
               /       TIER 1        \ TIER 1: Fast Unit & Ingestion Tests (Parsers, Schemas, ORM)
              /───────────────────────\
```

---

## 2. Test Suites Specification

### 2.1. Tier 1: Unit & Ingestion Tests (`tests/unit/`)
- **FastEmbed & Vector Dimensions**: Validates that `bge-small-en-v1.5` outputs exactly 384-dimensional unit vectors.
- **PyMuPDF Document Parser**: Validates extraction of text blocks, page numbers, and bounding boxes on vector PDFs.
- **OCR Engine Mock & Local Runner**: Tests PaddleOCR-light / Tesseract bounding box normalization to $[0, 1000]$.
- **Pydantic Tool Schemas**: Validates strict type checking and regex constraints on all tool inputs.
- **SQLite ORM & Hash Chaining**: Tests that inserting $N$ audit records produces an unbroken SHA-256 chain and that modifying a single byte in an old record causes immediate verification failure.

### 2.2. Tier 2: Agentic Integration & Model Swapping (`tests/integration/`)
- **VRAM Swapping State Machine**: Tests transitioning from `qwen3:4b` to `gemma3:4b` and back. Validates that Ollama unloads the inactive model and peak VRAM remains $\le 3.5\text{ GB}$.
- **ReAct Loop Termination**: Tests that task loops terminate gracefully when maximum steps ($15$) or timeouts ($180\text{s}$) are reached.
- **SSE Stream Contract**: Validates that all events emitted on `/tasks` follow the RFC EventSource format and match Pydantic schemas.

### 2.3. Tier 3: Security, Sandbox & Vulnerability Tests (`tests/security/`)
- **Path Traversal Jailbreak Test**:
  ```python
  def test_path_traversal_prevention():
      dangerous_paths = [
          "../../Windows/System32/cmd.exe",
          "/etc/passwd",
          "..\\..\\sensitive.txt",
          "C:\\Windows\\win.ini",
          "uploads/../../../sovereign.db"
      ]
      for path in dangerous_paths:
          with pytest.raises(SecurityPolicyViolationError):
              resolve_secure_workspace_path("ws_test", path)
  ```
- **Docker Sandbox Isolation Test**:
  - Validates that a script executing `urllib.request.urlopen("https://google.com")` fails with `Network is unreachable` (`--network none`).
  - Validates that attempts to write outside `/workspace/output` or `/tmp` fail with `Read-only file system`.
  - Validates that fork-bomb scripts (`while True: os.fork()`) are killed by `pids_limit=64`.
  - Validates that memory-hungry scripts (`"a" * 10**9`) trigger OOM termination without crashing the host.

### 2.4. Tier 4: Offline & Air-Gap Verification (`tests/offline/`)
- **Socket Egress Test**: Runs the full application test suite with outbound network traffic monitored via `psutil`. Asserts that external WAN packets sent equal **0**.
- **OLLAMA_NO_CLOUD Guarantee**: Confirms that environment variable `OLLAMA_NO_CLOUD=1` is active and no outbound telemetry is initiated.

---

## 3. Automated Test Execution Commands

```bash
# 1. Run all unit and parser tests
pytest backend/tests/unit -v

# 2. Run security and path traversal tests
pytest backend/tests/security -v

# 3. Run full integration & sandbox tests (requires Docker daemon)
pytest backend/tests/integration -v

# 4. Run air-gap & offline socket verification
python scripts/verify_airgap.py
```
