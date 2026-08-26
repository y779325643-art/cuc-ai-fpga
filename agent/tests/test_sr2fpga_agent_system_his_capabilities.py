import json
from dataclasses import FrozenInstanceError
from pathlib import Path
import shutil
from uuid import uuid4

import pytest

from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.system_his_capabilities import (
    SystemHisCapabilityRegistryError,
    load_system_his_backend_capabilities,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_VERSION = "system-his-backend-capabilities-v1"

EXPECTED_SEMANTIC_KINDS = frozenset(
    {
        "accumulator",
        "buffer",
        "counter",
        "fifo",
        "fork",
        "fsm",
        "gate",
        "join",
        "mac",
        "pwm",
        "rtl_component",
        "spi",
        "stage",
        "top_integration",
    }
)
EXPECTED_SEMANTIC_ALIASES = {
    "arithmetic_accumulator": "accumulator",
    "dual_stream_join": "join",
    "elastic_stream_buffer": "buffer",
    "pipeline_stage": "stage",
    "registered_stream_stage": "stage",
    "stream_accumulator": "accumulator",
    "stream_buffer": "buffer",
    "synchronous_fifo": "fifo",
}
EXPECTED_PROTOCOLS = frozenset({"wire", "register", "valid_ready"})
EXPECTED_PROTOCOL_ALIASES = {
    "combinational": "wire",
    "combinational_operand": "wire",
    "registered_data": "register",
    "registered_enable": "register",
}
EXPECTED_SCENARIOS = frozenset(
    {
        "reset",
        "nominal_operation",
        "flat_image",
        "axis_sensitive_edges",
        "back_to_back_matches",
        "threshold_boundary",
        "border_policy",
        "boundary_match_index",
        "continuous_frames",
        "defect_present_absent",
        "exact_match",
        "first_defect_coordinate",
        "stall_stability",
        "frame_boundary",
        "input_stall",
        "missing_final_in_last",
        "no_false_positive",
        "no_match",
        "overlapping_match",
        "partial_match",
        "reset_during_frame",
        "reset_during_partial_match",
    }
)


@pytest.fixture
def registry_test_root() -> Path:
    root = (
        REPO_ROOT
        / "artifacts"
        / "agent"
        / "test-tmp"
        / f"capability-registry-{uuid4().hex}"
    )
    root.mkdir(parents=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_registered_capabilities_preserve_current_h2_behavior() -> None:
    capabilities = load_system_his_backend_capabilities()

    assert capabilities.registry_version == REGISTRY_VERSION
    assert capabilities.system_his_version == "system-his-v1.2"
    assert capabilities.supported_component_semantic_kinds == EXPECTED_SEMANTIC_KINDS
    assert dict(capabilities.component_semantic_kind_aliases) == EXPECTED_SEMANTIC_ALIASES
    assert capabilities.supported_data_flow_protocols == EXPECTED_PROTOCOLS
    assert dict(capabilities.data_flow_protocol_aliases) == EXPECTED_PROTOCOL_ALIASES
    assert capabilities.supported_verification_scenarios == EXPECTED_SCENARIOS
    assert capabilities.canonical_testbench == "sim/tb_top.v"


def test_loaded_capabilities_are_immutable() -> None:
    capabilities = load_system_his_backend_capabilities()

    with pytest.raises(FrozenInstanceError):
        capabilities.canonical_testbench = "sim/other.v"  # type: ignore[misc]
    with pytest.raises(TypeError):
        capabilities.component_semantic_kind_aliases["other"] = "counter"  # type: ignore[index]
    with pytest.raises(AttributeError):
        capabilities.supported_data_flow_protocols.add("other")  # type: ignore[attr-defined]


def test_loader_does_not_depend_on_process_cwd(
    registry_test_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(registry_test_root)

    capabilities = load_system_his_backend_capabilities(
        RepositoryPaths.discover(REPO_ROOT / "agent" / "src")
    )

    assert capabilities.registry_version == REGISTRY_VERSION


def test_loader_rejects_manifest_version_drift(registry_test_root: Path) -> None:
    payload = _canonical_registry_payload()
    paths = _write_registry_repository(
        registry_test_root,
        payload,
        registered_version="system-his-backend-capabilities-v2",
    )

    with pytest.raises(SystemHisCapabilityRegistryError, match="version does not match"):
        load_system_his_backend_capabilities(paths)


def test_loader_rejects_alias_to_unsupported_capability(
    registry_test_root: Path,
) -> None:
    payload = _canonical_registry_payload()
    payload["component_semantic_kinds"]["aliases"]["unknown"] = "unsupported"
    paths = _write_registry_repository(registry_test_root, payload)

    with pytest.raises(SystemHisCapabilityRegistryError, match="target unsupported names"):
        load_system_his_backend_capabilities(paths)


def test_loader_rejects_registry_path_escape(registry_test_root: Path) -> None:
    paths = _write_registry_repository(
        registry_test_root,
        _canonical_registry_payload(),
        registry_path="../outside.json",
    )

    with pytest.raises(SystemHisCapabilityRegistryError, match="relative POSIX path"):
        load_system_his_backend_capabilities(paths)


def _canonical_registry_payload() -> dict:
    registry_path = (
        REPO_ROOT
        / "contracts"
        / "system-his"
        / "system-his-backend-capabilities-v1.json"
    )
    return json.loads(registry_path.read_text(encoding="utf-8"))


def _write_registry_repository(
    root: Path,
    payload: dict,
    *,
    registered_version: str = REGISTRY_VERSION,
    registry_path: str = "contracts/system-his/system-his-backend-capabilities-v1.json",
) -> RepositoryPaths:
    contracts_dir = root / "contracts"
    registry_file = root.joinpath(*Path(registry_path).parts)
    if ".." not in Path(registry_path).parts:
        registry_file.parent.mkdir(parents=True, exist_ok=True)
        registry_file.write_text(json.dumps(payload), encoding="utf-8")
    contracts_dir.mkdir(parents=True, exist_ok=True)
    (contracts_dir / "manifest.json").write_text(
        json.dumps(
            {
                "contract_registry_version": "1.0",
                "contracts": {
                    "system_his": {
                        "version": "system-his-v1.2",
                        "path": "contracts/system-his/system-his-v1.2.schema.json",
                    },
                    "system_his_backend_capabilities": {
                        "version": registered_version,
                        "path": registry_path,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return RepositoryPaths(root=root)
