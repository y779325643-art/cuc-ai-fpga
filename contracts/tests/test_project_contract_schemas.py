import copy
import json
from pathlib import Path, PurePosixPath

import pytest
from jsonschema import Draft202012Validator, ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_ROOT = REPO_ROOT / "contracts"
PACKAGE_SCHEMA_PATH = (
    CONTRACTS_ROOT / "project-package" / "project-package-v1.schema.json"
)
ENVELOPE_SCHEMA_PATH = (
    CONTRACTS_ROOT / "project-envelope" / "project-envelope-v1.schema.json"
)
MANIFEST_PATH = CONTRACTS_ROOT / "manifest.json"
HASH = "a" * 64


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(schema_path: Path, instance: dict) -> None:
    Draft202012Validator(load_json(schema_path)).validate(instance)


def minimal_package() -> dict:
    return {
        "contract_version": "project-package-v1",
        "project_name": "counter",
        "top": {
            "module": "counter_top",
            "source": "src/counter_top.sv",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {
                "path": "src/counter_top.sv",
                "role": "rtl_source",
                "language": "systemverilog",
            }
        ],
        "artifacts": [],
        "build": {
            "toolchain_id": "generic-synthesis-v1",
            "language_standard": "systemverilog-2017",
        },
    }


def model_file() -> dict:
    return {
        "path": "src/counter_top.sv",
        "sha256": HASH,
        "file_role": "rtl_source",
        "owner": "model",
        "origin": "model_generated",
        "editable": True,
        "snapshot_id": "snapshot-001",
    }


def minimal_envelope() -> dict:
    return {
        "contract_version": "project-envelope-v1",
        "integrity_scheme": "sr2fpga-json-sortkeys-merkle-sha256-v1",
        "envelope_sha256": HASH,
        "episode_id": "episode-001",
        "method_condition_id": "M0-direct",
        "method_policy_sha256": HASH,
        "project_package_sha256": HASH,
        "project_merkle_root_sha256": HASH,
        "files": [
            {
                "path": "manifest.json",
                "sha256": HASH,
                "file_role": "project_manifest",
                "owner": "trusted_builder",
                "origin": "deterministic",
                "editable": False,
                "snapshot_id": "snapshot-001",
            },
            model_file(),
        ],
        "evaluator_material_refs": [],
    }


@pytest.mark.parametrize(
    ("schema_path", "schema_id"),
    [
        (
            PACKAGE_SCHEMA_PATH,
            "https://sr2fpga.local/contracts/project-package/v1",
        ),
        (
            ENVELOPE_SCHEMA_PATH,
            "https://sr2fpga.local/contracts/project-envelope/v1",
        ),
    ],
)
def test_project_schemas_are_closed_draft_2020_12(
    schema_path: Path,
    schema_id: str,
) -> None:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == schema_id
    assert schema["additionalProperties"] is False


def test_project_contracts_are_registered_with_contained_paths() -> None:
    manifest = load_json(MANIFEST_PATH)
    expected = {
        "project_package": (
            "project-package-v1",
            "contracts/project-package/project-package-v1.schema.json",
        ),
        "project_envelope": (
            "project-envelope-v1",
            "contracts/project-envelope/project-envelope-v1.schema.json",
        ),
    }

    for key, (version, expected_path) in expected.items():
        record = manifest["contracts"][key]
        path = record["path"]
        posix_path = PurePosixPath(path)
        assert record["version"] == version
        assert path == expected_path
        assert not Path(path).is_absolute()
        assert not posix_path.is_absolute()
        assert ".." not in posix_path.parts
        assert (REPO_ROOT / path).resolve().is_relative_to(REPO_ROOT)
        assert (REPO_ROOT / path).is_file()


def test_minimal_project_package_needs_no_conditional_artifacts() -> None:
    package = minimal_package()
    validate(PACKAGE_SCHEMA_PATH, package)

    artifact_roles = {artifact["role"] for artifact in package["artifacts"]}
    assert "candidate_testbench" not in artifact_roles
    assert "predicted_qor" not in artifact_roles
    assert "system_his" not in artifact_roles


def test_project_package_accepts_nonstandard_top_path() -> None:
    validate(PACKAGE_SCHEMA_PATH, minimal_package())


def test_contract_identifiers_accept_underscores() -> None:
    package = minimal_package()
    package["project_name"] = "direct_counter"
    package["build"]["toolchain_id"] = "open_source_synthesis_v1"
    validate(PACKAGE_SCHEMA_PATH, package)

    envelope = minimal_envelope()
    envelope["method_condition_id"] = "M0_direct"
    validate(ENVELOPE_SCHEMA_PATH, envelope)


def test_conditional_artifact_requires_a_condition_id() -> None:
    package = minimal_package()
    package["artifacts"].append(
        {
            "path": "constraints/board.xdc",
            "role": "constraint",
            "applicability": "conditional",
        }
    )
    with pytest.raises(ValidationError):
        validate(PACKAGE_SCHEMA_PATH, package)

    package["artifacts"][0]["condition_id"] = "episode-requires-l4"
    validate(PACKAGE_SCHEMA_PATH, package)


@pytest.mark.parametrize(
    "path",
    ["/tmp/top.sv", "C:/tmp/top.sv", "../top.sv", "src/../../top.sv"],
)
def test_project_package_rejects_unsafe_paths(path: str) -> None:
    package = minimal_package()
    package["sources"][0]["path"] = path
    with pytest.raises(ValidationError):
        validate(PACKAGE_SCHEMA_PATH, package)


def test_project_package_rejects_unregistered_fields() -> None:
    package = minimal_package()
    package["top"]["owner"] = "model"
    with pytest.raises(ValidationError):
        validate(PACKAGE_SCHEMA_PATH, package)


def test_minimal_trusted_outer_envelope_validates() -> None:
    validate(ENVELOPE_SCHEMA_PATH, minimal_envelope())


def test_envelope_integrity_scheme_is_frozen() -> None:
    schema = load_json(ENVELOPE_SCHEMA_PATH)
    assert schema["properties"]["integrity_scheme"]["const"] == (
        "sr2fpga-json-sortkeys-merkle-sha256-v1"
    )


def test_project_manifest_role_is_bound_to_manifest_path() -> None:
    envelope = minimal_envelope()
    envelope["files"][0]["path"] = "metadata/project.json"
    with pytest.raises(ValidationError):
        validate(ENVELOPE_SCHEMA_PATH, envelope)

    envelope = minimal_envelope()
    envelope["files"][0]["file_role"] = "helper"
    with pytest.raises(ValidationError):
        validate(ENVELOPE_SCHEMA_PATH, envelope)


def test_envelope_digest_contract_omits_its_own_value() -> None:
    schema = load_json(ENVELOPE_SCHEMA_PATH)
    description = schema["properties"]["envelope_sha256"]["description"]
    assert "envelope_sha256 omitted" in description


def test_envelope_rejects_evaluator_as_a_candidate_file_owner() -> None:
    envelope = minimal_envelope()
    envelope["files"][0]["owner"] = "evaluator"
    with pytest.raises(ValidationError):
        validate(ENVELOPE_SCHEMA_PATH, envelope)


def test_evaluator_material_is_an_opaque_reference_without_a_path() -> None:
    envelope = minimal_envelope()
    envelope["evaluator_material_refs"].append(
        {
            "opaque_ref_id": "hidden-harness-commitment-001",
            "kind": "hidden_harness",
            "commitment_sha256": HASH,
        }
    )
    validate(ENVELOPE_SCHEMA_PATH, envelope)

    envelope["evaluator_material_refs"][0]["path"] = "hidden/tb.sv"
    with pytest.raises(ValidationError):
        validate(ENVELOPE_SCHEMA_PATH, envelope)


def test_composite_file_requires_model_and_trusted_region_provenance() -> None:
    envelope = minimal_envelope()
    envelope["files"][1] = {
        "path": "src/counter_top.sv",
        "sha256": HASH,
        "file_role": "rtl_source",
        "owner": "composite",
        "origin": "deterministic",
        "editable": True,
        "snapshot_id": "snapshot-001",
        "regions": [
            {
                "region_id": "trusted-shell",
                "owner": "trusted_builder",
                "start_byte": 0,
                "end_byte": 10,
                "sha256": HASH,
                "editable": False,
                "event_refs": ["event-compose-001"],
            },
            {
                "region_id": "model-behavior",
                "owner": "model",
                "start_byte": 10,
                "end_byte": 20,
                "sha256": HASH,
                "editable": True,
                "event_refs": ["event-generate-001"],
            },
        ],
    }
    validate(ENVELOPE_SCHEMA_PATH, envelope)

    invalid = copy.deepcopy(envelope)
    invalid["files"][1]["regions"] = invalid["files"][1]["regions"][:1]
    with pytest.raises(ValidationError):
        validate(ENVELOPE_SCHEMA_PATH, invalid)


def test_noncomposite_file_cannot_claim_region_ownership() -> None:
    envelope = minimal_envelope()
    envelope["files"][0]["regions"] = [
        {
            "region_id": "model-behavior",
            "owner": "model",
            "sha256": HASH,
            "editable": True,
            "event_refs": ["event-generate-001"],
        }
    ]
    with pytest.raises(ValidationError):
        validate(ENVELOPE_SCHEMA_PATH, envelope)
