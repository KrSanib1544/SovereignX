# SOVEREIGN-X — Micro-Isolated Python Execution Sandbox

---

## 1. Sandbox Purpose & Threat Boundaries

In confidential industrial workflows, LLMs frequently need to perform complex calculations, linear regressions, degradation forecasting, and tabular data transformations. **Under zero circumstances may AI-generated Python code execute directly on the Windows host.**

The SOVEREIGN-X Sandbox executes dynamic code inside an ephemeral, locked-down micro-container managed via the Docker Engine on the host.

```
+---------------------------------------------------------------------------------------------------+
|                                      WINDOWS 11 HOST MACHINE                                      |
|                                                                                                   |
|   +-----------------------+              +----------------------------------------------------+   |
|   |  FastAPI Backend Core |              |              Docker Engine (Local Daemon)          |   |
|   |  (Sandbox Manager)    |              |                                                    |   |
|   +-----------+-----------+              |   +--------------------------------------------+   |   |
|               │                          |   |   Micro-Container: `sovereign-sandbox:1.0` |   |   |
|               │ Python Docker SDK        |   |                                            |   |   |
|               ▼                          |   |  - Linux python:3.11-slim base             |   |   |
|   +-----------------------+              |   |  - User: `sandboxuser` (UID 10001)         |   |   |
|   | 1. Write script.py    |              |   |  - Network: NONE (--network none)          |   |   |
|   | 2. Mount Input Volume |─────────────>|   |  - RAM Limit: 512 MB (--memory 512m)       |   |   |
|   | 3. Set Constraints    |              |   |  - CPU Limit: 1.0 Core (--cpus 1.0)        |   |   |
|   | 4. Start Container    |              |   |  - Root FS: Read-Only (--read-only)        |   |   |
|   +-----------------------+              |   |  - Capabilities: --cap-drop=ALL            |   |   |
|               │                          |   |  - No New Privileges: true                 |   |   |
|               │ Poll / Wait (Max 30s)    |   |                                            |   |   |
|               ▼                          |   |  Mounted Volumes:                          |   |   |
|   +-----------------------+              |   |  * /workspace/input:ro (Read-Only Source)  |   |   |
|   | 5. Collect Stdout     |<─────────────|   |  * /workspace/output:rw (Temp Scratch)     |   |   |
|   | 6. Collect Artifacts  |              |   |  * /tmp:rw (Tmpfs memory mount)            |   |   |
|   | 7. Force Destroy      |              |   +--------------------------------------------+   |   |
|   +-----------------------+              +----------------------------------------------------+   |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Hardened Container Specification

### 2.1. Dockerfile (`docker/sandbox-python/Dockerfile`)
```dockerfile
FROM python:3.11-slim-bookworm

# Create non-root unprivileged execution user
RUN groupadd -g 10001 sandboxgroup && \
    useradd -u 10001 -g sandboxgroup -s /bin/false -m sandboxuser

# Install pre-compiled standard scientific dependencies
RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.2.2 \
    openpyxl==3.1.2 \
    scipy==1.13.0 \
    matplotlib==3.8.4 \
    statsmodels==0.14.2

# Set working directory & permissions
WORKDIR /workspace
RUN mkdir -p /workspace/input /workspace/output /tmp && \
    chown -R sandboxuser:sandboxgroup /workspace /tmp

USER sandboxuser:sandboxgroup

# Execution entrypoint
ENTRYPOINT ["python", "-u"]
```

---

## 3. Host Container Execution Flags

When the `SandboxManager` creates an execution container, it enforces the following security flags via the Docker SDK:

```python
container = docker_client.containers.create(
    image="sovereign-sandbox:1.0",
    command=["/workspace/input/script.py"],
    network_mode="none",                    # Hard physical network block (no loopback to host)
    mem_limit="512m",                       # Hard memory ceiling
    memswap_limit="512m",                   # Disable swap expansion
    nano_cpus=1_000_000_000,                # 1.0 CPU Core limit
    pids_limit=64,                          # Prevent fork-bomb attacks
    read_only=True,                         # Read-only root filesystem
    cap_drop=["ALL"],                       # Drop all Linux capabilities
    security_opt=["no-new-privileges:true"],# Prevent SUID privilege escalation
    volumes={
        str(input_host_dir): {"bind": "/workspace/input", "mode": "ro"},
        str(output_host_dir): {"bind": "/workspace/output", "mode": "rw"},
    },
    tmpfs={"/tmp": "size=64m,noexec"},      # In-memory temporary scratch
    user="10001:10001",
    detach=True
)
```

---

## 4. Execution Guard & Lifecycle Guarantees

1. **Timeout Watchdog**:
   - A host-side Python timer enforces a strict timeout (Default: `15 seconds`, Max: `30 seconds`).
   - If the container does not exit before the timeout, `container.kill()` is immediately sent, and a `SandboxTimeoutError` is raised.
2. **Stdout / Stderr Buffer Capping**:
   - Streams are captured up to a maximum of `64 KB`.
   - Any excessive logging is trimmed to prevent host memory exhaustion, preserving the first 2 KB and last 4 KB.
3. **Artifact Harvesting & Validation**:
   - Only recognized output formats (`.png`, `.csv`, `.json`, `.txt`) in `/workspace/output/` are harvested.
   - Files are validated against magic bytes and moved into the workspace artifact vault.
4. **Guaranteed Destruction**:
   - The container is created with `remove=False` for log capture, and wrapped in a Python `finally` block ensuring `container.remove(force=True)` runs even if the backend encounters an exception.

---

## 5. Host Fallback Mode (For Environments Without Docker)

For edge laptops where Docker Desktop cannot run due to restricted corporate policies:
- SOVEREIGN-X provides an optional secondary `SubprocessSandbox` utilizing Windows Restricted Tokens (`CreateRestrictedToken`), job objects with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, memory limits, and custom filesystem sandboxing.
- *Recommendation*: Docker containerization is the primary, production-certified sandbox.
