"""Persist tool output while running bounded development subprocess trees."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

from sr2fpga_agent.local_tools import executable_env, resolve_executable
from sr2fpga_agent.models import ToolResult


def run_recorded(command: list[str], cwd: Path, stage: str, *, timeout_seconds: int) -> ToolResult:
    """Use files rather than pipes, so orphaned child handles cannot hang cleanup.

    A timeout terminates only the newly spawned tool process group/tree. Partial
    stdout/stderr remain on disk even if the controlling Python process stops.
    """
    if timeout_seconds <= 0 or not stage.replace("_", "").isalnum():
        raise ValueError("invalid development tool limit or stage")
    start = time.monotonic()
    resolved = list(command)
    executable = resolve_executable(command[0])
    if executable is not None:
        resolved[0] = str(executable)
    stdout_path, stderr_path = cwd / (stage + ".stdout.log"), cwd / (stage + ".stderr.log")
    exit_code = None
    status = "failed"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
            process = subprocess.Popen(resolved, cwd=cwd, env=executable_env(), stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, **options)
        except FileNotFoundError:
            status = "missing_tool"
        else:
            try:
                exit_code = process.wait(timeout=timeout_seconds)
                status = "passed" if exit_code == 0 else "failed"
            except subprocess.TimeoutExpired:
                status = "timeout"
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=10, check=False)
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
    return ToolResult(stage=stage, command=resolved, status=status, exit_code=exit_code,
                      stdout=stdout_path.read_text(encoding="utf-8", errors="replace"),
                      stderr=stderr_path.read_text(encoding="utf-8", errors="replace"),
                      duration_seconds=time.monotonic() - start)
