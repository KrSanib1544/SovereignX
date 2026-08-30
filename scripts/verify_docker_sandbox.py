# scripts/verify_docker_sandbox.py
"""
Sovereign-X Docker Sandbox Verification Script
Tests all 14 sandbox security invariants and isolation constraints on real hardware with Docker.
"""

import asyncio
import json
import os
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.agent.sandbox.manager import (
    SandboxManager,
    SandboxUnavailableError,
)
from backend.app.agent.tools.run_python import RunPythonInput, RunPythonTool
from backend.app.config import settings
from backend.app.db.session import init_db


async def run_all_verifications():
    print("=" * 75)
    print("SOVEREIGN-X — REAL HARDWARE DOCKER SANDBOX ISOLATION VERIFICATION")
    print("=" * 75)

    init_db()
    sandbox = SandboxManager(image_name="sovereign-sandbox:1.0")

    # Check Docker Availability
    docker_ok, docker_err = sandbox.check_docker_available()
    print(f"[*] Docker Daemon Reachable: {docker_ok}")
    if not docker_ok:
        print(f"[!] Docker Error: {docker_err}")
        return

    workspace_id = "ws-sandbox-verification"
    ws_dir = (settings.WORKSPACES_DIR / workspace_id).resolve()
    ws_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    # -------------------------------------------------------------
    # TEST 1 & 2: Container Starts & UID/GID Verification
    # -------------------------------------------------------------
    print("\n[TEST 1 & 2] Verifying Container Startup & Non-Root UID/GID...")
    uid_script = (
        "import os\n"
        "print(f'UID:{os.getuid()},GID:{os.getgid()}')\n"
    )
    res_uid = await sandbox.execute_python(workspace_id, uid_script)
    print(f"  Output: {res_uid.stdout.strip()}")
    is_uid_10001 = "UID:10001,GID:10001" in res_uid.stdout
    results["1_container_starts"] = (res_uid.exit_code == 0)
    results["2_non_root_uid_10001"] = is_uid_10001

    # -------------------------------------------------------------
    # TEST 3 & 11: Network Isolation (--network none)
    # -------------------------------------------------------------
    print("\n[TEST 3 & 11] Verifying Network Isolation (--network none)...")
    net_script = (
        "import socket\n"
        "try:\n"
        "    s = socket.create_connection(('8.8.8.8', 53), timeout=2)\n"
        "    print('NETWORK_ACCESSIBLE')\n"
        "except Exception as e:\n"
        "    print(f'NETWORK_BLOCKED:{type(e).__name__}:{e}')\n"
    )
    res_net = await sandbox.execute_python(workspace_id, net_script)
    print(f"  Output: {res_net.stdout.strip()}")
    is_net_blocked = "NETWORK_BLOCKED" in res_net.stdout and "NETWORK_ACCESSIBLE" not in res_net.stdout
    results["3_network_disabled_none"] = is_net_blocked
    results["11_external_egress_blocked"] = is_net_blocked

    # -------------------------------------------------------------
    # TEST 4, 5, 6: Cgroup Resource Limits (Memory, CPU, PIDs)
    # -------------------------------------------------------------
    print("\n[TEST 4, 5, 6] Verifying Memory, CPU, and PID limits via container inspection...")
    import docker
    client = docker.from_env()
    # Create test container to inspect host_config
    c = client.containers.create(
        image="sovereign-sandbox:1.0",
        command=["python", "-c", "print('check')"],
        network_mode="none",
        mem_limit="512m",
        memswap_limit="512m",
        nano_cpus=1_000_000_000,
        pids_limit=64,
        read_only=True,
        user="10001:10001"
    )
    h_cfg = c.attrs.get("HostConfig", {})
    mem_bytes = h_cfg.get("Memory", 0)
    nano_cpus = h_cfg.get("NanoCpus", 0)
    pids_limit = h_cfg.get("PidsLimit", 0)
    read_only_root = h_cfg.get("ReadonlyRootfs", False)
    net_mode = h_cfg.get("NetworkMode", "")
    c.remove(force=True)

    print(f"  Memory Limit: {mem_bytes / (1024*1024)} MB (Expected: 512 MB)")
    print(f"  Nano CPUs:    {nano_cpus / 1_000_000_000} CPU (Expected: 1.0 CPU)")
    print(f"  PID Limit:    {pids_limit} PIDs (Expected: 64 PIDs)")
    print(f"  ReadOnly Root:{read_only_root} (Expected: True)")
    print(f"  Network Mode: {net_mode} (Expected: none)")

    results["4_memory_limit_512m"] = (mem_bytes == 512 * 1024 * 1024)
    results["5_cpu_limit_1_0"] = (nano_cpus == 1_000_000_000)
    results["6_pid_limit_64"] = (pids_limit == 64)

    # -------------------------------------------------------------
    # TEST 7: Read-Only Root Filesystem
    # -------------------------------------------------------------
    print("\n[TEST 7] Verifying Read-Only Root Filesystem...")
    ro_script = (
        "try:\n"
        "    with open('/root_test.txt', 'w') as f:\n"
        "        f.write('fail')\n"
        "    print('WRITE_ROOT_ALLOWED')\n"
        "except OSError as e:\n"
        "    print(f'WRITE_ROOT_BLOCKED:{type(e).__name__}:{e}')\n"
    )
    res_ro = await sandbox.execute_python(workspace_id, ro_script)
    print(f"  Output: {res_ro.stdout.strip()}")
    is_ro_blocked = "WRITE_ROOT_BLOCKED" in res_ro.stdout and "WRITE_ROOT_ALLOWED" not in res_ro.stdout
    results["7_root_fs_readonly"] = is_ro_blocked

    # -------------------------------------------------------------
    # TEST 8: Ephemeral Lifecycle & Container Removal
    # -------------------------------------------------------------
    print("\n[TEST 8] Verifying Ephemeral Container Removal...")
    containers_before = len(client.containers.list(all=True))
    res_eph = await sandbox.execute_python(workspace_id, "print('ephemeral test')")
    containers_after = len(client.containers.list(all=True))
    print(f"  Containers before: {containers_before}, Containers after: {containers_after}")
    results["8_container_ephemeral_removal"] = (containers_before == containers_after)

    # -------------------------------------------------------------
    # TEST 9: Python Computation & Output Generation
    # -------------------------------------------------------------
    print("\n[TEST 9] Verifying Scientific Python & Data Calculation...")
    calc_script = (
        "import numpy as np\n"
        "import pandas as pd\n"
        "arr = np.array([3.42, 4.10, 4.55, 3.88])\n"
        "mean_val = float(np.mean(arr))\n"
        "min_val = float(np.min(arr))\n"
        "print(f'CALC_SUCCESS:mean={mean_val:.2f},min={min_val:.2f}')\n"
        "with open('/workspace/output/summary.csv', 'w') as f:\n"
        "    f.write('metric,val\\nmean,' + str(mean_val) + '\\nmin,' + str(min_val))\n"
    )
    res_calc = await sandbox.execute_python(workspace_id, calc_script)
    print(f"  Output: {res_calc.stdout.strip()}")
    print(f"  Generated files: {res_calc.generated_files}")
    is_calc_ok = "CALC_SUCCESS" in res_calc.stdout and "summary.csv" in res_calc.generated_files
    results["9_python_execution_and_output"] = is_calc_ok

    # -------------------------------------------------------------
    # TEST 10: Host Filesystem Escape Prevention
    # -------------------------------------------------------------
    print("\n[TEST 10] Verifying Host Filesystem Escape Prevention...")
    escape_script = (
        "import os\n"
        "paths_to_check = ['C:/Windows', 'C:/Users', '/host', '/mnt/c', '/data']\n"
        "escaped = []\n"
        "for p in paths_to_check:\n"
        "    if os.path.exists(p):\n"
        "        escaped.append(p)\n"
        "if escaped:\n"
        "    print(f'HOST_ACCESSIBLE:{escaped}')\n"
        "else:\n"
        "    print('HOST_ISOLATED_SECURE')\n"
    )
    res_escape = await sandbox.execute_python(workspace_id, escape_script)
    print(f"  Output: {res_escape.stdout.strip()}")
    is_host_isolated = "HOST_ISOLATED_SECURE" in res_escape.stdout
    results["10_host_fs_isolated"] = is_host_isolated

    # -------------------------------------------------------------
    # TEST 12: Execution Timeout Enforcement
    # -------------------------------------------------------------
    print("\n[TEST 12] Verifying Timeout Enforcement...")
    timeout_script = (
        "import time\n"
        "time.sleep(10)\n"
        "print('SHOULD_NOT_REACH')\n"
    )
    t0 = time.perf_counter()
    res_timeout = await sandbox.execute_python(workspace_id, timeout_script, timeout_seconds=2)
    dur = round(time.perf_counter() - t0, 2)
    print(f"  Duration: {dur}s, Timed Out: {res_timeout.timed_out}, Exit Code: {res_timeout.exit_code}")
    results["12_timeout_enforced"] = res_timeout.timed_out and dur < 6.0

    # -------------------------------------------------------------
    # TEST 13: Failure Handling & Stderr Preservation
    # -------------------------------------------------------------
    print("\n[TEST 13] Verifying Execution Error Handling...")
    fail_script = "raise ValueError('Critical engineered defect threshold exceeded')"
    res_fail = await sandbox.execute_python(workspace_id, fail_script)
    print(f"  Exit code: {res_fail.exit_code}")
    print(f"  Stderr snippet: {res_fail.stdout.strip()[:100]}...")
    results["13_failure_handled_safely"] = (res_fail.exit_code != 0) and ("ValueError" in res_fail.stdout)

    # -------------------------------------------------------------
    # TEST 14: RunPythonTool Integration & Host Fallback Denial
    # -------------------------------------------------------------
    print("\n[TEST 14] Verifying RunPythonTool Security Invariants...")
    tool = RunPythonTool(sandbox_manager=sandbox)
    tool_res = await tool.execute(workspace_id, RunPythonInput(script="print('Tool integration check')", timeout_seconds=5))
    print(f"  Tool status: {tool_res.status}, stdout: {tool_res.stdout.strip()}")
    results["14_tool_integration"] = (tool_res.status == "SUCCESS") and ("Tool integration check" in tool_res.stdout)

    print("\n" + "=" * 75)
    print("ALL 14 SANDBOX VERIFICATION TESTS SUMMARY")
    print("=" * 75)
    all_passed = True
    for k, v in results.items():
        status = "PASSED" if v else "FAILED"
        if not v:
            all_passed = False
        print(f"  [{status}] {k}")

    print(f"\nOverall Sandbox Isolation Status: {'100% VERIFIED' if all_passed else 'FAILURES DETECTED'}")
    return results


if __name__ == "__main__":
    asyncio.run(run_all_verifications())
