import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts/evaluation/full-pack-smoke-report-v1.schema.json"
HASH = "a" * 64


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _method_record(method: str) -> dict:
    planning_kind = None
    planning_sha256 = None
    h_status = "not_applicable"
    skeleton_mode = "none"
    if method == "M2":
        planning_kind = "untyped_plan"
        planning_sha256 = "b" * 64
    elif method in {"M3", "M4", "M5"}:
        planning_kind = "system_his"
        planning_sha256 = "c" * 64
        h_status = "pass"
        skeleton_mode = "none_free_full_project" if method == "M3" else "behavior_files"
    return {
        "method_condition": method,
        "analysis_population": "excluded",
        "pack_sha256": HASH,
        "public_projection_sha256": HASH,
        "candidate_artifact_key": f"candidates/{method.lower()}",
        "candidate_artifact_sha256": HASH,
        "project_package_sha256": HASH,
        "skeleton_artifact_sha256": HASH if method in {"M4", "M5"} else None,
        "planning_kind": planning_kind,
        "planning_artifact_sha256": planning_sha256,
        "h_status": h_status,
        "skeleton_mode": skeleton_mode,
    }


def _scenario(kind: str, method: str | None, status: str, facts: dict) -> dict:
    return {
        "scenario_id": f"scenario-{kind.replace('_', '-')}",
        "scenario_kind": kind,
        "analysis_population": "excluded",
        "public_projection_sha256": HASH,
        "method_condition": method,
        "status": status,
        "facts": facts,
    }


def _report() -> dict:
    return {
        "contract_version": "full-pack-smoke-report-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "smoke_id": "contract-test",
        "analysis_population": "excluded",
        "registered_evidence_contract": True,
        "g3_accepted": False,
        "g4b_authorized": False,
        "official_outcome": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "public_projection_sha256": HASH,
        "method_records": [_method_record(method) for method in ("M0", "M1", "M2", "M3", "M4", "M5")],
        "scenario_records": [
            _scenario(
                "success",
                None,
                "passed",
                {"method_count": 6, "scope": "pre_candidate_emission_conformance"},
            ),
            _scenario(
                "h_repair",
                "M5",
                "passed",
                {"his_corrections_used": 1, "rerun_complete_h_validation": True},
            ),
            _scenario(
                "project_repair",
                "M1",
                "passed",
                {
                    "repair_calls_attempted": 1,
                    "repair_transitions": 1,
                    "rerun_performed": True,
                    "automatic_pass_credit": True,
                },
            ),
            _scenario("non_ready", None, "needs_clarification", {"generation_calls": 0}),
            _scenario(
                "hidden_fail",
                "M0",
                "fail",
                {
                    "opaque_outcome_only": True,
                    "opaque_outcome_id": "development-outcome-1",
                    "repair_after_hidden": False,
                },
            ),
            _scenario(
                "infrastructure_not_run",
                "M1",
                "not_run",
                {
                    "reason": "evaluator_exception",
                    "opaque_outcome_id": "development-outcome-2",
                    "replacement_episode": False,
                },
            ),
        ],
        "reconciliation": {
            "method_set": ["M0", "M1", "M2", "M3", "M4", "M5"],
            "same_public_projection": True,
            "m0_m1_initial_project_matched": True,
            "m3_m4_system_his_matched": True,
            "m3_m4_candidate_artifacts_separate": True,
            "m4_m5_skeleton_project_matched": True,
            "required_scenarios": [
                "h_repair",
                "hidden_fail",
                "infrastructure_not_run",
                "non_ready",
                "project_repair",
                "success",
            ],
            "all_required_scenarios_present": True,
            "full_axis_costs_reconciled": False,
            "blocking_gaps": [
                "full_axis_event_derived_cost_reconciliation",
                "runner_owned_public_terminal_hidden_pipeline",
            ],
        },
    }


def test_full_pack_smoke_report_accepts_closed_excluded_shape() -> None:
    _validator().validate(_report())


def test_full_pack_smoke_report_rejects_claim_escalation_and_private_details() -> None:
    validator = _validator()
    escalated = copy.deepcopy(_report())
    escalated["g3_accepted"] = True
    with pytest.raises(ValidationError):
        validator.validate(escalated)

    leaked = copy.deepcopy(_report())
    leaked["scenario_records"][4]["facts"]["stdout"] = "private hidden output"
    with pytest.raises(ValidationError):
        validator.validate(leaked)


def test_full_pack_smoke_report_rejects_unregistered_or_incomplete_pack() -> None:
    validator = _validator()
    unregistered = copy.deepcopy(_report())
    unregistered["registered_evidence_contract"] = False
    with pytest.raises(ValidationError):
        validator.validate(unregistered)

    incomplete = copy.deepcopy(_report())
    incomplete["method_records"].pop()
    with pytest.raises(ValidationError):
        validator.validate(incomplete)
