"""Explicitly authorized exact-version probes for development L4 tools."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Callable

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.local_tools import executable_env, resolve_executable
from sr2fpga_agent.tool_environment import sanitize_version_line


L4_VERSION_PROBE_ENV = "SR2FPGA_L4_VERSION_PROBE"
_OPEN_TOOL_NAMES = ("yosys", "nextpnr-xilinx", "python3")


def collect_development_l4_tool_environment(
    *,
    open_enabled: bool,
    commercial_enabled: bool,
    probe_authorized: bool,
    open_probe_command: list[str] | None,
    vivado_command: str,
    timeout_seconds: int = 30,
    resolver: Callable[[str], Path | None] = resolve_executable,
    command_executor: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    if not isinstance(probe_authorized, bool):
        raise TypeError("L4 version probe authorization must be boolean")
    lanes = {
        "l4_open": _collect_open_lane(
            enabled=open_enabled,
            authorized=probe_authorized,
            command=open_probe_command,
            timeout_seconds=timeout_seconds,
            command_executor=command_executor,
        ),
        "l4_commercial": _collect_commercial_lane(
            enabled=commercial_enabled,
            authorized=probe_authorized,
            command=vivado_command,
            timeout_seconds=timeout_seconds,
            resolver=resolver,
            command_executor=command_executor,
        ),
    }
    enabled_lanes = [lane for lane in lanes.values() if lane["enabled"]]
    authority_status = (
        "not_run"
        if not enabled_lanes
        else "complete"
        if all(lane["status"] == "complete" for lane in enabled_lanes)
        else "incomplete"
    )
    snapshot = {
        "contract_version": "development-l4-tool-environment-v1",
        "collection_scope": "development_l4_preflight",
        "collector_id": "sr2fpga-l4-tool-probe-v1",
        "probe_authorized": probe_authorized,
        "authority_status": authority_status,
        "lanes": lanes,
        "terminal_binding": False,
        "pass_credit_authority": False,
        "official_authority": False,
    }
    validate_development_l4_tool_environment(snapshot)
    return snapshot


def validate_development_l4_tool_environment(snapshot: dict[str, Any]) -> None:
    errors = ContractRegistry().load_schema(
        "development_l4_tool_environment"
    ).validate(snapshot)
    if errors:
        raise ValueError("invalid development L4 tool environment: " + "; ".join(errors))
    lanes = snapshot["lanes"]
    for lane_name, lane in lanes.items():
        if not lane["enabled"]:
            if lane != {
                "enabled": False,
                "status": "disabled",
                "failure_type": None,
                "tools": [],
            }:
                raise ValueError(f"disabled {lane_name} lane carries probe data")
            continue
        if not snapshot["probe_authorized"]:
            if lane["status"] != "probe_not_authorized" or lane[
                "failure_type"
            ] != "probe_not_authorized":
                raise ValueError(f"unauthorized {lane_name} lane cannot contain a probe")
            if lane["tools"]:
                raise ValueError(f"unauthorized {lane_name} lane carries tool data")
    open_lane = lanes["l4_open"]
    if open_lane["status"] == "complete":
        if [record["name"] for record in open_lane["tools"]] != list(
            _OPEN_TOOL_NAMES
        ):
            raise ValueError("complete L4-open probe lacks exact tool set")
    commercial_lane = lanes["l4_commercial"]
    if commercial_lane["status"] == "complete":
        if [record["name"] for record in commercial_lane["tools"]] != ["vivado"]:
            raise ValueError("complete L4-commercial probe lacks Vivado")
    enabled_lanes = [lane for lane in lanes.values() if lane["enabled"]]
    expected_status = (
        "not_run"
        if not enabled_lanes
        else "complete"
        if all(lane["status"] == "complete" for lane in enabled_lanes)
        else "incomplete"
    )
    if snapshot["authority_status"] != expected_status:
        raise ValueError("L4 tool authority status contradicts lane records")


def l4_tool_version_projection(snapshot: dict[str, Any]) -> dict[str, str]:
    validate_development_l4_tool_environment(snapshot)
    versions: dict[str, str] = {}
    for lane_name, lane in snapshot["lanes"].items():
        if lane["status"] == "complete":
            for record in lane["tools"]:
                versions[f"{lane_name}.{record['name']}"] = record["version_line"]
        else:
            versions[lane_name] = (
                "disabled"
                if lane["status"] == "disabled"
                else f"unavailable:{lane['failure_type']}"
            )
    return versions


def _collect_open_lane(
    *,
    enabled: bool,
    authorized: bool,
    command: list[str] | None,
    timeout_seconds: int,
    command_executor: Callable[..., Any],
) -> dict[str, Any]:
    initial = _initial_lane(enabled, authorized)
    if initial is not None:
        return initial
    if not command:
        return _failed_lane("unsupported_custom_launcher")
    try:
        completed = command_executor(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=executable_env(),
        )
    except subprocess.TimeoutExpired:
        return _failed_lane("probe_timeout")
    except OSError:
        return _failed_lane("probe_os_error")
    if completed.returncode != 0:
        return _failed_lane("nonzero_exit")
    payload = _last_probe_payload(completed.stdout)
    if payload is None:
        return _failed_lane("invalid_probe_output")
    records = payload.get("tools")
    if payload.get("probe_contract") != "openxc7-tool-probe-v1" or not isinstance(
        records, list
    ):
        return _failed_lane("invalid_probe_output")
    try:
        normalized = [_normalize_tool_record(record) for record in records]
    except (KeyError, TypeError, ValueError):
        return _failed_lane("invalid_probe_output")
    if [record["name"] for record in normalized] != list(_OPEN_TOOL_NAMES):
        return _failed_lane("invalid_probe_output")
    return {"enabled": True, "status": "complete", "failure_type": None, "tools": normalized}


def _collect_commercial_lane(
    *,
    enabled: bool,
    authorized: bool,
    command: str,
    timeout_seconds: int,
    resolver: Callable[[str], Path | None],
    command_executor: Callable[..., Any],
) -> dict[str, Any]:
    initial = _initial_lane(enabled, authorized)
    if initial is not None:
        return initial
    resolved = resolver(command)
    if resolved is None:
        return _failed_lane("missing_executable")
    resolved = Path(resolved)
    try:
        executable = resolved.read_bytes()
        completed = command_executor(
            [str(resolved), "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=executable_env(),
        )
    except subprocess.TimeoutExpired:
        return _failed_lane("probe_timeout")
    except OSError:
        return _failed_lane("probe_os_error")
    if completed.returncode != 0:
        return _failed_lane("nonzero_exit")
    output = _combined_output(completed.stdout, completed.stderr)
    if not output:
        return _failed_lane("invalid_probe_output")
    record = {
        "name": "vivado",
        "resolved_executable_basename": resolved.name,
        "resolved_executable_sha256": hashlib.sha256(executable).hexdigest(),
        "resolved_executable_size_bytes": len(executable),
        "version_line": sanitize_version_line(
            next(line.strip() for line in output.splitlines() if line.strip())
        ),
        "version_output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }
    return {"enabled": True, "status": "complete", "failure_type": None, "tools": [record]}


def _initial_lane(enabled: bool, authorized: bool) -> dict[str, Any] | None:
    if not enabled:
        return {"enabled": False, "status": "disabled", "failure_type": None, "tools": []}
    if not authorized:
        return {
            "enabled": True,
            "status": "probe_not_authorized",
            "failure_type": "probe_not_authorized",
            "tools": [],
        }
    return None


def _failed_lane(failure_type: str) -> dict[str, Any]:
    return {"enabled": True, "status": "incomplete", "failure_type": failure_type, "tools": []}


def _last_probe_payload(stdout: Any) -> dict[str, Any] | None:
    if not isinstance(stdout, str):
        return None
    for line in reversed(stdout.splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _normalize_tool_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("tool record must be an object")
    record = {
        "name": str(value["name"]),
        "resolved_executable_basename": str(value["resolved_executable_basename"]),
        "resolved_executable_sha256": str(value["resolved_executable_sha256"]),
        "resolved_executable_size_bytes": int(value["resolved_executable_size_bytes"]),
        "version_line": sanitize_version_line(str(value["version_line"])),
        "version_output_sha256": str(value["version_output_sha256"]),
    }
    if "/" in record["resolved_executable_basename"] or "\\" in record[
        "resolved_executable_basename"
    ]:
        raise ValueError("tool record exposes a path")
    for field in ("resolved_executable_sha256", "version_output_sha256"):
        if len(record[field]) != 64 or any(character not in "0123456789abcdef" for character in record[field]):
            raise ValueError("tool record has an invalid digest")
    if record["resolved_executable_size_bytes"] < 0 or not record["version_line"]:
        raise ValueError("tool record is incomplete")
    return record


def _combined_output(stdout: Any, stderr: Any) -> str:
    return "\n".join(
        value.strip()
        for value in (stdout, stderr)
        if isinstance(value, str) and value.strip()
    )
