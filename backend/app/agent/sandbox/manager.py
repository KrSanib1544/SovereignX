# backend/app/agent/sandbox/manager.py
"""
Micro-Isolated Docker Sandbox Manager
Enforces strict container boundaries:
--network none, 512MB RAM limit, 1.0 CPU, 64 PIDs, read-only root, non-root UID 10001.
Strict Security Guarantee: If Docker is unavailable, Python code is NEVER executed on the Windows host.
"""

import asyncio
import os
from pathlib import Path
import shutil
import time
from typing import Dict, List, Optional, Tuple
import uuid
from pydantic import BaseModel

from backend.app.config import settings


class SandboxExecutionResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    generated_files: List[str]
    execution_time_ms: float
    timed_out: bool = False
    sandbox_backend: str = "docker"


class SandboxUnavailableError(Exception):
    """Raised when container isolation is requested but Docker is not installed or running."""
    def __init__(
        self,
        message: str = "Docker engine is not installed or running. Host execution is strictly blocked by mandatory security invariant #6.",
        details: Optional[str] = None
    ):
        self.details = details
        super().__init__(message)


class SandboxTimeoutError(Exception):
    """Raised when sandbox container execution exceeds wall-clock timeout."""
    pass


class SandboxManager:
    """
    Manages the lifecycle of ephemeral, locked-down execution containers.
    """

    def __init__(self, image_name: str = "sovereign-sandbox:1.0"):
        self.image_name = image_name
        self._docker_client = None
        self._docker_checked = False
        self._docker_available = False
        self._docker_error = ""

    def check_docker_available(self) -> Tuple[bool, str]:
        """
        Check if the Docker SDK can connect to a live local Docker daemon.
        """
        if self._docker_checked:
            return self._docker_available, self._docker_error

        try:
            import docker
            client = docker.from_env(timeout=2)
            client.ping()
            self._docker_client = client
            self._docker_available = True
            self._docker_error = ""
        except Exception as e:
            self._docker_client = None
            self._docker_available = False
            self._docker_error = f"Docker daemon unreachable: {str(e)}"

        self._docker_checked = True
        return self._docker_available, self._docker_error

    async def execute_python(
        self,
        workspace_id: str,
        script_code: str,
        timeout_seconds: int = 15
    ) -> SandboxExecutionResult:
        """
        Execute Python script inside an ephemeral micro-container.
        Guaranteed: If Docker is unavailable, raises SandboxUnavailableError.
        """
        docker_ok, docker_err = self.check_docker_available()
        if not docker_ok:
            raise SandboxUnavailableError(
                message="Docker daemon is not accessible. In accordance with Security Invariant #6, "
                        "Python execution on the Windows host is strictly forbidden.",
                details=docker_err
            )

        run_id = f"run_{uuid.uuid4().hex[:8]}"
        base_dir = (settings.WORKSPACES_DIR / workspace_id).resolve()
        scratch_dir = (base_dir / "scratch").resolve()
        sandbox_scratch = scratch_dir / run_id
        input_dir = sandbox_scratch / "input"
        output_dir = sandbox_scratch / "output"

        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write script to read-only input folder
        script_path = input_dir / "script.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_code)

        import docker
        client = self._docker_client or docker.from_env()

        container = None
        t0 = time.perf_counter()
        timed_out = False
        exit_code = -1
        stdout_str = ""
        stderr_str = ""

        try:
            # Create hardened ephemeral container
            container = client.containers.create(
                image=self.image_name,
                command=["/workspace/input/script.py"],
                network_mode="none",                    # Hard network isolation
                mem_limit="512m",                       # 512MB RAM ceiling
                memswap_limit="512m",                   # Disable swap expansion
                nano_cpus=1_000_000_000,                # 1.0 CPU limit
                pids_limit=64,                          # Fork-bomb prevention
                read_only=True,                         # Read-only root FS
                cap_drop=["ALL"],                       # Drop all capabilities
                security_opt=["no-new-privileges:true"],# Disallow setuid escalation
                volumes={
                    str(input_dir.resolve()): {"bind": "/workspace/input", "mode": "ro"},
                    str(output_dir.resolve()): {"bind": "/workspace/output", "mode": "rw"},
                },
                tmpfs={"/tmp": "size=64m,noexec"},      # In-memory temporary scratch
                user="10001:10001",                     # Non-root user
                detach=True
            )

            container.start()

            # Async polling with watchdog timeout
            loop = asyncio.get_running_loop()
            poll_interval = 0.2
            elapsed = 0.0

            while elapsed < timeout_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                c_status = await loop.run_in_executor(None, lambda: client.containers.get(container.id).status)
                if c_status in ("exited", "dead"):
                    break

            if elapsed >= timeout_seconds:
                timed_out = True
                try:
                    await loop.run_in_executor(None, lambda: container.kill())
                except Exception:
                    pass

            # Inspect exit code and logs
            res_info = await loop.run_in_executor(None, lambda: client.containers.get(container.id).attrs)
            exit_code = res_info.get("State", {}).get("ExitCode", -1) if not timed_out else 124

            raw_logs = await loop.run_in_executor(
                None, lambda: client.containers.get(container.id).logs(stdout=True, stderr=True)
            )
            log_text = raw_logs.decode("utf-8", errors="replace")
            stdout_str = log_text

        finally:
            t1 = time.perf_counter()
            duration_ms = round((t1 - t0) * 1000.0, 2)

            # Guaranteed destruction of ephemeral container
            if container:
                try:
                    await loop.run_in_executor(None, lambda: container.remove(force=True))
                except Exception:
                    pass

        # Harvest output artifacts from /output/
        generated_files = []
        if output_dir.exists():
            for f in output_dir.iterdir():
                if f.is_file():
                    generated_files.append(f.name)

        # Cap output string to 64KB
        max_bytes = 64 * 1024
        if len(stdout_str.encode("utf-8")) > max_bytes:
            stdout_str = stdout_str[:max_bytes] + "\n... [TRUNCATED: Output exceeded 64KB limit]"

        return SandboxExecutionResult(
            exit_code=exit_code,
            stdout=stdout_str,
            stderr=stderr_str,
            generated_files=generated_files,
            execution_time_ms=duration_ms,
            timed_out=timed_out,
            sandbox_backend="docker"
        )
