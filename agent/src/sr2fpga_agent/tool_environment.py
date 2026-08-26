"""Deterministic, path-sanitized development tool-environment snapshots."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
from typing import Any, Callable

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.local_tools import executable_env, resolve_executable


CORE_TOOL_VERSION_COMMANDS: dict[str, tuple[str, ...]] = {
    "iverilog": ("iverilog", "-V"),
    "verilator": ("verilator", "--version"),
    "vvp": ("vvp", "-V"),
    "yosys": ("yosys", "-V"),
}
_WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])[A-Z]:[\\/][^\s]+")
_POSIX_ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_:])/(?:[^/\s]+/)*[^/\s]+")


def collect_development_tool_environment(
    *,
    timeout_seconds: int = 10,
    resolver: Callable[[str], Path | None] = resolve_executable,
    command_executor: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Probe core tools once without persisting machine-local absolute paths."""

    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool):
        raise TypeError("tool probe timeout must be an integer")
    if not 1 <= timeout_seconds <= 60:
        raise ValueError("tool probe timeout must be between 1 and 60 seconds")
    records = [
        _probe_tool(
            name,
            command,
            timeout_seconds=timeout_seconds,
            resolver=resolver,
            command_executor=command_executor,
        )
        for name, command in CORE_TOOL_VERSION_COMMANDS.items()
    ]
    snapshot = {
        "contract_version": "development-tool-environment-v1",
        "collection_scope": "development_preflight",
        "collector_id": "sr2fpga-core-tool-probe-v1",
        "probe_timeout_seconds": timeout_seconds,
        "required_tool_names": sorted(CORE_TOOL_VERSION_COMMANDS),
        "authority_status": (
            "complete"
            if all(record["status"] == "available" for record in records)
            else "incomplete"
        ),
        "tools": records,
        "terminal_binding": False,
        "pass_credit_authority": False,
        "official_authority": False,
    }
    validate_development_tool_environment(snapshot)
    return snapshot


def validate_development_tool_environment(snapshot: dict[str, Any]) -> None:
    """Enforce schema plus exact logical-tool and status invariants."""

    errors = ContractRegistry().load_schema("development_tool_environment").validate(
        snapshot
    )
    if errors:
        raise ValueError("invalid development tool environment: " + "; ".join(errors))
    records = snapshot["tools"]
    names = [record["name"] for record in records]
    expected_names = list(CORE_TOOL_VERSION_COMMANDS)
    if names != expected_names:
        raise ValueError(
            "development tool records must use canonical order exactly once: "
            + ", ".join(expected_names)
        )
    for record in records:
        expected_command = list(CORE_TOOL_VERSION_COMMANDS[record["name"]])
        if record["version_command"] != expected_command:
            raise ValueError(f"unexpected version command for {record['name']}")
        _validate_tool_record_status(record)
    expected_status = (
        "complete"
        if all(record["status"] == "available" for record in records)
        else "incomplete"
    )
    if snapshot["authority_status"] != expected_status:
        raise ValueError("tool authority status contradicts tool records")


def tool_version_projection(snapshot: dict[str, Any]) -> dict[str, str]:
    """Return the legacy name-to-version view from a verified snapshot."""

    validate_development_tool_environment(snapshot)
    versions: dict[str, str] = {}
    for record in snapshot["tools"]:
        if record["status"] == "available":
            versions[record["name"]] = record["version_line"]
        elif record["status"] == "missing":
            versions[record["name"]] = "missing"
        else:
            versions[record["name"]] = (
                f"unavailable:{record['probe_failure_type']}"
            )
    return versions


def _probe_tool(
    name: str,
    command: tuple[str, ...],
    *,
    timeout_seconds: int,
    resolver: Callable[[str], Path | None],
    command_executor: Callable[..., Any],
) -> dict[str, Any]:
    record = _empty_record(name, command)
    resolved = resolver(command[0])
    if resolved is None:
        record["status"] = "missing"
        record["probe_failure_type"] = "missing_executable"
        return record
    resolved = Path(resolved)
    record["resolved_executable_basename"] = resolved.name
    try:
        executable_bytes = resolved.read_bytes()
    except OSError:
        record["status"] = "probe_failed"
        record["probe_failure_type"] = "executable_unreadable"
        return record
    record["resolved_executable_sha256"] = hashlib.sha256(executable_bytes).hexdigest()
    record["resolved_executable_size_bytes"] = len(executable_bytes)
    try:
        completed = command_executor(
            [str(resolved), *command[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=executable_env(),
        )
    except subprocess.TimeoutExpired:
        record["status"] = "probe_failed"
        record["probe_failure_type"] = "probe_timeout"
        return record
    except OSError:
        record["status"] = "probe_failed"
        record["probe_failure_type"] = "probe_os_error"
        return record
    record["exit_code"] = int(completed.returncode)
    combined_output = _combined_output(completed.stdout, completed.stderr)
    if combined_output:
        record["version_output_sha256"] = hashlib.sha256(
            combined_output.encode("utf-8")
        ).hexdigest()
        record["version_line"] = sanitize_version_line(
            next(line.strip() for line in combined_output.splitlines() if line.strip())
        )
    if completed.returncode != 0:
        record["status"] = "probe_failed"
        record["probe_failure_type"] = "nonzero_exit"
    elif not combined_output:
        record["status"] = "probe_failed"
        record["probe_failure_type"] = "empty_version_output"
    else:
        record["status"] = "available"
    return record


def _empty_record(name: str, command: tuple[str, ...]) -> dict[str, Any]:
    return {
        "name": name,
        "version_command": list(command),
        "status": "probe_failed",
        "resolved_executable_basename": None,
        "resolved_executable_sha256": None,
        "resolved_executable_size_bytes": None,
        "version_line": None,
        "version_output_sha256": None,
        "exit_code": None,
        "probe_failure_type": None,
    }


def _combined_output(stdout: Any, stderr: Any) -> str:
    parts = [value.strip() for value in (stdout, stderr) if isinstance(value, str) and value.strip()]
    return "\n".join(parts)


def sanitize_version_line(value: str) -> str:
    redacted = _WINDOWS_ABSOLUTE_PATH_RE.sub("<absolute-path-redacted>", value)
    return _POSIX_ABSOLUTE_PATH_RE.sub("<absolute-path-redacted>", redacted)


def _validate_tool_record_status(record: dict[str, Any]) -> None:
    status = record["status"]
    if status == "available":
        required = (
            "resolved_executable_basename",
            "resolved_executable_sha256",
            "resolved_executable_size_bytes",
            "version_line",
            "version_output_sha256",
            "exit_code",
        )
        if any(record[field] is None for field in required):
            raise ValueError(f"available tool record is incomplete: {record['name']}")
        if record["exit_code"] != 0 or record["probe_failure_type"] is not None:
            raise ValueError(f"available tool record contradicts probe result: {record['name']}")
    elif status == "missing":
        nullable = (
            "resolved_executable_basename",
            "resolved_executable_sha256",
            "resolved_executable_size_bytes",
            "version_line",
            "version_output_sha256",
            "exit_code",
        )
        if any(record[field] is not None for field in nullable):
            raise ValueError(f"missing tool record carries resolved data: {record['name']}")
        if record["probe_failure_type"] != "missing_executable":
            raise ValueError(f"missing tool record has wrong failure type: {record['name']}")
    elif record["probe_failure_type"] not in {
        "executable_unreadable",
        "probe_timeout",
        "probe_os_error",
        "nonzero_exit",
        "empty_version_output",
    }:
        raise ValueError(f"failed tool probe lacks a stable failure type: {record['name']}")
