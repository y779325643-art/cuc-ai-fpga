import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "contracts"
    / "evaluation"
    / "development-oracle-run-evidence-v1.schema.json"
)
HASH = "a" * 64
SCENARIO_CLASSES = (
    "public_smoke",
    "hidden_deterministic",
    "randomized_fixed_seed",
    "stress",
)


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _scenario(scenario_class: str) -> dict:
    return {
        "scenario_id": f"{scenario_class}_001",
        "scenario_class": scenario_class,
        "status": "passed",
        "failure_origin": None,
        "failure_type": None,
        "command": ["vvp", "sim.out"],
        "exit_code": 0,
        "stdout": "TEST_PASS\n",
        "stderr": "",
        "duration_seconds": 0.01,
        "mismatch_detail": [],
    }


def _payload() -> dict:
    return {
        "contract_version": "development-oracle-run-evidence-v1",
        "evaluation_scope": "development_independent_oracle",
        "family_id": "fir_filter",
        "bundle_sha256": HASH,
        "status": "passed",
        "failure_origin": None,
        "failure_type": None,
        "scenario_counts": {item: 1 for item in SCENARIO_CLASSES},
        "class_status": {item: "pass" for item in SCENARIO_CLASSES},
        "scenario_results": [_scenario(item) for item in SCENARIO_CLASSES],
        "diagnostics": [],
        "pass_credit_authority": False,
        "official_outcome": False,
    }


def test_development_oracle_run_evidence_accepts_current_payload() -> None:
    _validator().validate(_payload())


@pytest.mark.parametrize(
    ("failure_origin", "failure_type"),
    (
        ("natural_model_failure", "functional_mismatch"),
        ("toolchain_environment_failure", "simulator_execution_failure"),
        ("oracle_environment_failure", "oracle_vector_read_failure"),
    ),
)
def test_failed_run_accepts_each_registered_execution_origin(
    failure_origin,
    failure_type,
) -> None:
    payload = _payload()
    payload["status"] = "failed"
    payload["failure_origin"] = failure_origin
    payload["failure_type"] = failure_type
    payload["class_status"]["public_smoke"] = "fail"
    scenario = payload["scenario_results"][0]
    scenario["status"] = "failed"
    scenario["failure_origin"] = failure_origin
    scenario["failure_type"] = failure_type
    scenario["exit_code"] = 1

    _validator().validate(payload)


@pytest.mark.parametrize(
    ("failure_origin", "failure_type"),
    (
        (None, "functional_mismatch"),
        ("provider_specific_free_text", "functional_mismatch"),
        ("natural_model_failure", None),
    ),
)
def test_failed_run_requires_registered_origin_and_fine_grained_type(
    failure_origin,
    failure_type,
) -> None:
    payload = _payload()
    payload["status"] = "failed"
    payload["failure_origin"] = failure_origin
    payload["failure_type"] = failure_type

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_passed_scenario_cannot_carry_failure_metadata() -> None:
    payload = _payload()
    payload["scenario_results"][0]["failure_origin"] = "natural_model_failure"
    payload["scenario_results"][0]["failure_type"] = "functional_mismatch"

    with pytest.raises(ValidationError):
        _validator().validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("pass_credit_authority", True),
        ("official_outcome", True),
        ("evaluation_scope", "official_heldout"),
    ),
)
def test_development_oracle_evidence_cannot_claim_authority(field, value) -> None:
    payload = _payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        _validator().validate(payload)


def test_development_oracle_evidence_is_closed_against_hidden_material_fields() -> None:
    payload = copy.deepcopy(_payload())
    payload["private_pack_sha256"] = "b" * 64

    with pytest.raises(ValidationError):
        _validator().validate(payload)
