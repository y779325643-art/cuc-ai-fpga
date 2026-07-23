"""Command-line tool execution helpers."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from sr2fpga_agent.local_tools import executable_env, resolve_executable
from sr2fpga_agent.models import ToolResult


class CommandRunner:
    """Run external commands and convert outcomes into ToolResult objects."""

    def run(
        self,
        command: list[str],
        cwd: Path,
        stage: str,
        timeout_seconds: int = 30,
    ) -> ToolResult:
        start = time.monotonic()
        resolved_command = list(command)
        resolved_executable = resolve_executable(command[0])
        if resolved_executable is not None:
            resolved_command[0] = str(resolved_executable)
        try:
            completed = subprocess.run(
                resolved_command,
                cwd=cwd,
                env=executable_env(),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            return ToolResult(
                stage=stage,
                command=resolved_command,
                status="missing_tool",
                exit_code=None,
                stdout="",
                stderr=f"Missing executable: {command[0]}",
                duration_seconds=time.monotonic() - start,
            )
        except subprocess.TimeoutExpired as exc:
            return ToolResult(
                stage=stage,
                command=resolved_command,
                status="timeout",
                exit_code=None,
                stdout=exc.stdout or "",
                stderr=exc.stderr or f"Command timed out after {timeout_seconds} seconds",
                duration_seconds=time.monotonic() - start,
            )

        status = "passed" if completed.returncode == 0 else "failed"
        return ToolResult(
            stage=stage,
            command=resolved_command,
            status=status,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=time.monotonic() - start,
        )
