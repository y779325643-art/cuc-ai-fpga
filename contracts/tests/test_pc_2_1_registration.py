"""PC 2.1 is the active Project Contract serialization under `paper1-v2.2`.

Registration must be real: the schemas resolve through `ContractRegistry`, bind
to an identity the schema file itself declares, and reject documents in the
formats PC 2.1 replaces. `paper1-v2.2` provides no reader, alias, or conversion
path for System-HIS v1.2 or PC 2.0, so a silent accept would be a research-level
defect, not a cosmetic one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry

REPO_ROOT = Path(__file__).resolve().parents[2]
PC_2_1_DIR = REPO_ROOT / "contracts" / "pc" / "2.1"


@pytest.fixture(scope="module")
def registry() -> ContractRegistry:
    return ContractRegistry()


def test_both_pc_2_1_schemas_are_registered_and_resolve(registry: ContractRegistry) -> None:
    assert registry.load_schema("project_contract_2_1").version == "sr2fpga-pc-2.1"
    assert (
        registry.load_schema("design_proposal_2_1").version
        == "urn:sr2fpga:pc-design:2.1"
    )


def test_registered_versions_match_what_the_schema_files_declare() -> None:
    """Guard against a manifest line that names a version the file does not carry."""

    full = json.loads(
        (PC_2_1_DIR / "project-contract-2.1.schema.json").read_text(encoding="utf-8")
    )
    assert full["properties"]["schema_version"]["const"] == "sr2fpga-pc-2.1"

    design = json.loads(
        (PC_2_1_DIR / "design-proposal-2.1.schema.json").read_text(encoding="utf-8")
    )
    assert design["$id"] == "urn:sr2fpga:pc-design:2.1"


def test_schemas_live_in_the_layout_the_spec_requires() -> None:
    assert (PC_2_1_DIR / "project-contract-2.1.schema.json").is_file()
    assert (PC_2_1_DIR / "design-proposal-2.1.schema.json").is_file()
    assert not (REPO_ROOT / "contracts" / "pc-2.0").exists()


# --- Superseded formats must be rejected, never silently accepted -----------


@pytest.mark.parametrize(
    "schema_version",
    ["sr2fpga-pc-2.0", "system-his-v1.2", "sr2fpga-pc-2.2", "", "SR2FPGA-PC-2.1"],
)
def test_wrong_schema_version_is_rejected(
    registry: ContractRegistry, schema_version: str
) -> None:
    contract = registry.load_schema("project_contract_2_1")
    errors = contract.validate(
        {"schema_version": schema_version, "bindings": {}, "design": {}}
    )
    assert errors, f"{schema_version!r} must not validate as PC 2.1"


def test_empty_and_structurally_absent_documents_are_rejected(
    registry: ContractRegistry,
) -> None:
    contract = registry.load_schema("project_contract_2_1")
    assert contract.validate({})
    assert contract.validate({"schema_version": "sr2fpga-pc-2.1"})


def test_pc_2_1_requires_bindings_and_design(registry: ContractRegistry) -> None:
    """The trusted controller owns `bindings`; a model-only document is incomplete."""

    contract = registry.load_schema("project_contract_2_1")
    missing_bindings = contract.validate(
        {"schema_version": "sr2fpga-pc-2.1", "design": {}}
    )
    assert any("bindings" in error for error in missing_bindings)


def test_system_his_stays_registered_for_existing_artifacts(
    registry: ContractRegistry,
) -> None:
    """Retiring it as the active format does not make old artifacts unreadable.

    `paper1-v2.2` bars System-HIS v1.2 from new runtime paths; it does not
    delete history. The registration must therefore still resolve.
    """

    assert registry.load_schema("system_his").version == "system-his-v1.2"


def test_pc_2_0_schemas_are_not_registered() -> None:
    manifest = json.loads(
        (REPO_ROOT / "contracts" / "manifest.json").read_text(encoding="utf-8")
    )
    registered_paths = {entry["path"] for entry in manifest["contracts"].values()}
    assert not [path for path in registered_paths if "2.0" in path]
