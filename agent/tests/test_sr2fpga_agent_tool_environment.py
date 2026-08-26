import copy
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from sr2fpga_agent.artifact_store import ArtifactConflictError, ArtifactStore
from sr2fpga_agent.tool_environment import (
    CORE_TOOL_VERSION_COMMANDS,
    collect_development_tool_environment,
    tool_version_projection,
    validate_development_tool_environment,
)


def _executables(tmp_path: Path) -> dict[str, Path]:
    result = {}
    for name in CORE_TOOL_VERSION_COMMANDS:
        path = tmp_path / f"{name}.exe"
        path.write_bytes(f"fake executable for {name}\n".encode())
        result[name] = path
    return result


def _resolver(executables: dict[str, Path]):
    return lambda name: executables.get(name)


def _successful_executor(command, **_kwargs):
    name = Path(command[0]).stem
    return SimpleNamespace(
        returncode=0,
        stdout=f"{name} version 1.2.3\nextra detail\n",
        stderr="",
    )


def test_collects_complete_content_addressable_snapshot_without_local_paths(tmp_path):
    executables = _executables(tmp_path)

    snapshot = collect_development_tool_environment(
        resolver=_resolver(executables),
        command_executor=_successful_executor,
    )

    assert snapshot["authority_status"] == "complete"
    assert [record["name"] for record in snapshot["tools"]] == list(
        CORE_TOOL_VERSION_COMMANDS
    )
    encoded = json.dumps(snapshot, sort_keys=True)
    assert str(tmp_path) not in encoded
    assert all(record["resolved_executable_sha256"] for record in snapshot["tools"])
    assert tool_version_projection(snapshot) == {
        name: f"{name} version 1.2.3" for name in CORE_TOOL_VERSION_COMMANDS
    }

    store = ArtifactStore(tmp_path / "store")
    first = store.put_validated_json(
        "tool-environments/preflight",
        snapshot,
        contract_key="development_tool_environment",
    )
    second = store.put_validated_json(
        "tool-environments/preflight",
        snapshot,
        contract_key="development_tool_environment",
    )
    assert first == second

    changed = collect_development_tool_environment(
        resolver=_resolver(executables),
        command_executor=lambda command, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=f"{Path(command[0]).stem} version 9.9.9\n",
            stderr="",
        ),
    )
    with pytest.raises(ArtifactConflictError, match="different content"):
        store.put_validated_json(
            "tool-environments/preflight",
            changed,
            contract_key="development_tool_environment",
        )


def test_missing_tool_is_explicit_and_makes_snapshot_incomplete(tmp_path):
    executables = _executables(tmp_path)
    executables.pop("yosys")

    snapshot = collect_development_tool_environment(
        resolver=_resolver(executables),
        command_executor=_successful_executor,
    )

    record = next(item for item in snapshot["tools"] if item["name"] == "yosys")
    assert snapshot["authority_status"] == "incomplete"
    assert record["status"] == "missing"
    assert record["probe_failure_type"] == "missing_executable"
    assert record["resolved_executable_basename"] is None
    assert tool_version_projection(snapshot)["yosys"] == "missing"


@pytest.mark.parametrize(
    ("exception", "failure_type"),
    (
        (subprocess.TimeoutExpired(["yosys", "-V"], 10), "probe_timeout"),
        (OSError("launch failed"), "probe_os_error"),
    ),
)
def test_probe_infrastructure_failure_is_not_reported_as_a_version(
    tmp_path,
    exception,
    failure_type,
):
    executables = _executables(tmp_path)

    def fail_yosys(command, **kwargs):
        if Path(command[0]).stem == "yosys":
            raise exception
        return _successful_executor(command, **kwargs)

    snapshot = collect_development_tool_environment(
        resolver=_resolver(executables),
        command_executor=fail_yosys,
    )

    record = next(item for item in snapshot["tools"] if item["name"] == "yosys")
    assert record["status"] == "probe_failed"
    assert record["probe_failure_type"] == failure_type
    assert tool_version_projection(snapshot)["yosys"] == f"unavailable:{failure_type}"


def test_nonzero_and_empty_probes_remain_distinct(tmp_path):
    executables = _executables(tmp_path)

    def mixed_executor(command, **_kwargs):
        name = Path(command[0]).stem
        if name == "iverilog":
            return SimpleNamespace(returncode=2, stdout="bad version\n", stderr="")
        if name == "vvp":
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return _successful_executor(command)

    snapshot = collect_development_tool_environment(
        resolver=_resolver(executables),
        command_executor=mixed_executor,
    )
    by_name = {record["name"]: record for record in snapshot["tools"]}

    assert by_name["iverilog"]["probe_failure_type"] == "nonzero_exit"
    assert by_name["vvp"]["probe_failure_type"] == "empty_version_output"


@pytest.mark.parametrize(
    "version_line",
    (
        "yosys build C:\\Users\\private-name\\toolchain\\yosys.exe",
        "yosys build /home/private-name/toolchain/yosys",
    ),
)
def test_version_line_redacts_tool_reported_absolute_paths(tmp_path, version_line):
    executables = _executables(tmp_path)

    def executor(command, **_kwargs):
        name = Path(command[0]).stem
        output = version_line if name == "yosys" else f"{name} version 1.2.3"
        return SimpleNamespace(returncode=0, stdout=output + "\n", stderr="")

    snapshot = collect_development_tool_environment(
        resolver=_resolver(executables),
        command_executor=executor,
    )
    yosys = next(record for record in snapshot["tools"] if record["name"] == "yosys")

    assert yosys["version_line"] == "yosys build <absolute-path-redacted>"
    assert "private-name" not in json.dumps(snapshot)
    assert yosys["version_output_sha256"]


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload["tools"].reverse(),
        lambda payload: payload["tools"][0].update(
            {"version_command": ["iverilog", "--invented"]}
        ),
        lambda payload: payload.update({"authority_status": "incomplete"}),
        lambda payload: payload.update({"terminal_binding": True}),
        lambda payload: payload.update({"official_authority": True}),
        lambda payload: payload["tools"][0].update(
            {"resolved_executable_basename": "C:\\private\\iverilog.exe"}
        ),
    ),
)
def test_snapshot_rejects_order_command_status_and_authority_tamper(tmp_path, mutation):
    snapshot = collect_development_tool_environment(
        resolver=_resolver(_executables(tmp_path)),
        command_executor=_successful_executor,
    )
    tampered = copy.deepcopy(snapshot)
    mutation(tampered)

    with pytest.raises(ValueError):
        validate_development_tool_environment(tampered)
