import json
from dataclasses import FrozenInstanceError
from pathlib import Path
import shutil
from uuid import uuid4

import pytest

from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.system_his_compatibility import (
    CONTRACT_VERSION,
    SystemHisCompatibilityError,
    load_system_his_compatibility_envelope,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT / "contracts" / "system-his" / "system-his-compatibility-v1.json"
)


@pytest.fixture
def compatibility_test_root() -> Path:
    root = (
        REPO_ROOT
        / "artifacts"
        / "agent"
        / "test-tmp"
        / f"system-his-compatibility-{uuid4().hex}"
    )
    root.mkdir(parents=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_canonical_v12_is_active_and_condition_eligible() -> None:
    envelope = load_system_his_compatibility_envelope()

    disposition = envelope.classify("system-his-v1.2")

    assert envelope.contract_version == CONTRACT_VERSION
    assert envelope.canonical_system_his_version == "system-his-v1.2"
    assert disposition.status == "canonical"
    assert disposition.registered_h_stage_policy == "required"
    assert disposition.common_l0_policy == "eligible"
    assert disposition.training_partition == "clean"
    assert disposition.positive_system_his_view_policy == "condition_eligible"


def test_legacy_v11_is_quarantined_and_forbidden_for_positive_his_views() -> None:
    disposition = load_system_his_compatibility_envelope().classify("system-his-v1.1")

    assert disposition.status == "legacy_quarantine"
    assert disposition.registered_h_stage_policy == "reject"
    assert disposition.common_l0_policy == "eligible"
    assert disposition.training_partition == "quarantine"
    assert disposition.positive_system_his_view_policy == "forbidden"


def test_method_inapplicable_his_keeps_direct_common_l0_eligible() -> None:
    disposition = load_system_his_compatibility_envelope().classify("not_applicable")

    assert disposition.status == "method_not_applicable"
    assert disposition.registered_h_stage_policy == "not_applicable"
    assert disposition.common_l0_policy == "eligible"
    assert disposition.training_partition == "quarantine"
    assert disposition.positive_system_his_view_policy == "method_neutral_only"


def test_unknown_representation_fails_closed_into_quarantine() -> None:
    disposition = load_system_his_compatibility_envelope().classify("system-his-v9")

    assert disposition.representation_id == "system-his-v9"
    assert disposition.status == "unknown_quarantine"
    assert disposition.registered_h_stage_policy == "reject"
    assert disposition.training_partition == "quarantine"
    assert disposition.positive_system_his_view_policy == "forbidden"


def test_loaded_envelope_is_immutable() -> None:
    envelope = load_system_his_compatibility_envelope()

    with pytest.raises(FrozenInstanceError):
        envelope.canonical_system_his_version = "system-his-v9"  # type: ignore[misc]
    with pytest.raises(TypeError):
        envelope.representations["other"] = envelope.unknown_representation  # type: ignore[index]


def test_loader_rejects_manifest_version_drift(compatibility_test_root: Path) -> None:
    paths = _write_contract_repository(
        compatibility_test_root,
        _canonical_payload(),
        registered_version="system-his-compatibility-v2",
    )

    with pytest.raises(SystemHisCompatibilityError, match="unsupported"):
        load_system_his_compatibility_envelope(paths)


def test_loader_rejects_canonical_schema_drift(compatibility_test_root: Path) -> None:
    payload = _canonical_payload()
    payload["canonical_system_his_version"] = "system-his-v1.1"
    paths = _write_contract_repository(compatibility_test_root, payload)

    with pytest.raises(SystemHisCompatibilityError, match="registered schema"):
        load_system_his_compatibility_envelope(paths)


def test_loader_rejects_legacy_clean_partition(compatibility_test_root: Path) -> None:
    payload = _canonical_payload()
    legacy = next(
        item for item in payload["representations"] if item["representation_id"] == "system-his-v1.1"
    )
    legacy["training_partition"] = "clean"
    paths = _write_contract_repository(compatibility_test_root, payload)

    with pytest.raises(SystemHisCompatibilityError, match="quarantined"):
        load_system_his_compatibility_envelope(paths)


def _canonical_payload() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _write_contract_repository(
    root: Path,
    payload: dict,
    *,
    registered_version: str = CONTRACT_VERSION,
) -> RepositoryPaths:
    contract_path = root / "contracts" / "system-his" / "system-his-compatibility-v1.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(json.dumps(payload), encoding="utf-8")
    (root / "contracts" / "manifest.json").write_text(
        json.dumps(
            {
                "contract_registry_version": "1.0",
                "contracts": {
                    "system_his": {
                        "version": "system-his-v1.2",
                        "path": "contracts/system-his/system-his-v1.2.schema.json",
                    },
                    "system_his_compatibility": {
                        "version": registered_version,
                        "path": "contracts/system-his/system-his-compatibility-v1.json",
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return RepositoryPaths(root=root)
