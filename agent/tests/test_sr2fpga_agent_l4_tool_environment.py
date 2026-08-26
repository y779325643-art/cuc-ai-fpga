import copy
import hashlib
import json
from types import SimpleNamespace

import pytest

from sr2fpga_agent.l4_tool_environment import (
    collect_development_l4_tool_environment,
    l4_tool_version_projection,
    validate_development_l4_tool_environment,
)


def _tool_record(name: str) -> dict:
    executable = f"fake {name} executable".encode()
    output = f"{name} version 1.2.3"
    return {
        "name": name,
        "resolved_executable_basename": f"{name}.exe",
        "resolved_executable_sha256": hashlib.sha256(executable).hexdigest(),
        "resolved_executable_size_bytes": len(executable),
        "version_line": output,
        "version_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
    }


def _open_probe_output() -> str:
    return json.dumps(
        {
            "probe_contract": "openxc7-tool-probe-v1",
            "tools": [
                _tool_record("yosys"),
                _tool_record("nextpnr-xilinx"),
                _tool_record("python3"),
            ],
        }
    )


def test_unauthorized_probe_executes_nothing_and_preserves_enabled_lanes():
    calls = []

    snapshot = collect_development_l4_tool_environment(
        open_enabled=True,
        commercial_enabled=True,
        probe_authorized=False,
        open_probe_command=["wsl", "bash", "openxc7_pnr.sh", "--probe-tool-environment"],
        vivado_command="vivado",
        resolver=lambda name: calls.append(("resolve", name)),
        command_executor=lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    assert calls == []
    assert snapshot["authority_status"] == "incomplete"
    assert snapshot["lanes"]["l4_open"]["status"] == "probe_not_authorized"
    assert snapshot["lanes"]["l4_commercial"]["status"] == "probe_not_authorized"
    assert l4_tool_version_projection(snapshot) == {
        "l4_open": "unavailable:probe_not_authorized",
        "l4_commercial": "unavailable:probe_not_authorized",
    }


def test_authorized_probe_captures_exact_openxc7_and_vivado_versions(tmp_path):
    vivado = tmp_path / "vivado.bat"
    vivado.write_bytes(b"fake vivado executable")

    def execute(command, **_kwargs):
        if command[-1] == "--probe-tool-environment":
            return SimpleNamespace(returncode=0, stdout="nix prelude\n" + _open_probe_output(), stderr="")
        return SimpleNamespace(returncode=0, stdout="Vivado v2026.1\n", stderr="")

    snapshot = collect_development_l4_tool_environment(
        open_enabled=True,
        commercial_enabled=True,
        probe_authorized=True,
        open_probe_command=["bash", "openxc7_pnr.sh", "--probe-tool-environment"],
        vivado_command="vivado",
        resolver=lambda _name: vivado,
        command_executor=execute,
    )

    assert snapshot["authority_status"] == "complete"
    assert snapshot["lanes"]["l4_open"]["status"] == "complete"
    assert snapshot["lanes"]["l4_commercial"]["tools"][0]["version_line"] == (
        "Vivado v2026.1"
    )
    projection = l4_tool_version_projection(snapshot)
    assert projection["l4_open.nextpnr-xilinx"] == "nextpnr-xilinx version 1.2.3"
    assert projection["l4_commercial.vivado"] == "Vivado v2026.1"
    assert str(tmp_path) not in json.dumps(snapshot)


@pytest.mark.parametrize(
    ("returncode", "stdout", "failure_type"),
    (
        (1, "", "nonzero_exit"),
        (0, "not JSON", "invalid_probe_output"),
    ),
)
def test_openxc7_probe_failures_remain_infrastructure_missingness(
    returncode,
    stdout,
    failure_type,
):
    snapshot = collect_development_l4_tool_environment(
        open_enabled=True,
        commercial_enabled=False,
        probe_authorized=True,
        open_probe_command=["bash", "openxc7_pnr.sh", "--probe-tool-environment"],
        vivado_command="vivado",
        command_executor=lambda *_args, **_kwargs: SimpleNamespace(
            returncode=returncode,
            stdout=stdout,
            stderr="",
        ),
    )

    assert snapshot["authority_status"] == "incomplete"
    assert snapshot["lanes"]["l4_open"]["failure_type"] == failure_type


def test_custom_openxc7_launcher_is_not_probed_generically():
    snapshot = collect_development_l4_tool_environment(
        open_enabled=True,
        commercial_enabled=False,
        probe_authorized=True,
        open_probe_command=None,
        vivado_command="vivado",
    )

    assert snapshot["lanes"]["l4_open"]["failure_type"] == (
        "unsupported_custom_launcher"
    )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload.update({"official_authority": True}),
        lambda payload: payload.update({"authority_status": "complete"}),
        lambda payload: payload["lanes"]["l4_open"].update(
            {"status": "complete", "failure_type": None}
        ),
    ),
)
def test_l4_tool_environment_rejects_authority_and_status_tamper(mutation):
    snapshot = collect_development_l4_tool_environment(
        open_enabled=True,
        commercial_enabled=False,
        probe_authorized=False,
        open_probe_command=None,
        vivado_command="vivado",
    )
    tampered = copy.deepcopy(snapshot)
    mutation(tampered)

    with pytest.raises(ValueError):
        validate_development_l4_tool_environment(tampered)
