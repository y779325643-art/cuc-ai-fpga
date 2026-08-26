import copy
import json
from pathlib import Path, PurePosixPath

import pytest
from jsonschema import Draft202012Validator, ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT
    / "contracts"
    / "requirement-audit"
    / "requirement-audit-v1.schema.json"
)
MANIFEST_PATH = REPO_ROOT / "contracts" / "manifest.json"
HASH = "a" * 64


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def counters() -> dict:
    return {
        "model_calls": 0,
        "tool_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
        "wall_time_ms": 1.0,
    }


def ready_case() -> dict:
    return {
        "base_requirement_cluster_id": "cluster-001",
        "ambiguity_case_id": "cluster-001-clear",
        "generation_visible_projection": {
            "visibility_class": "generation_visible",
            "public_requirement": "Build an 8-bit counter with active-low reset.",
            "public_requirement_sha256": HASH,
            "width_bits": 8,
            "platform_profile_id": "generic-fpga-v1",
            "platform_profile_sha256": HASH,
            "capability_profile_id": "system-his-backend-v1",
            "capability_profile_sha256": HASH,
        },
        "preflight_projection": {
            "visibility_class": "audit_only",
            "envelope": {
                "envelope_version": "requirement-envelope-v1",
                "envelope_sha256": HASH,
                "requirement_id": "requirement-001",
                "facts": [
                    {
                        "fact_id": "data.width",
                        "origin": "user_explicit",
                        "value": 8,
                    }
                ],
                "ambiguity_fact_ids": [],
                "capability_ids": ["counter"],
            },
            "route": {
                "route_version": "requirement-route-v1",
                "route_sha256": HASH,
                "strategy_id": "generic",
                "reason_ids": ["requirements_resolved"],
                "fact_ids": ["data.width"],
                "capability_ids": ["counter"],
            },
        },
        "boundary_result": {
            "visibility_class": "audit_only",
            "execution_status": "completed",
            "predicted_disposition": "ready",
            "reason_ids": ["requirements_resolved"],
            "fact_ids": ["data.width"],
            "capability_ids": ["counter"],
            "generation_boundary_crossed": True,
            "counters": counters(),
        },
        "evaluator_only": {
            "visibility_class": "evaluator_only",
            "gold_disposition": "ready",
            "gold_reason_ids": ["requirements_resolved"],
            "gold_fact_ids": ["data.width"],
            "gold_capability_ids": ["counter"],
        },
    }


def artifact(case: dict | None = None) -> dict:
    case = case or ready_case()
    result = case["boundary_result"]
    gold = case["evaluator_only"]["gold_disposition"]
    predicted_counts = {
        "ready": 0,
        "needs_clarification": 0,
        "capability_gap": 0,
    }
    if result["execution_status"] == "completed":
        predicted_counts[result["predicted_disposition"]] = 1
    gold_counts = {
        "ready": 0,
        "needs_clarification": 0,
        "capability_gap": 0,
    }
    gold_counts[gold] = 1
    confusion = {
        expected: {
            "ready": 0,
            "needs_clarification": 0,
            "capability_gap": 0,
        }
        for expected in ("ready", "needs_clarification", "capability_gap")
    }
    if result["execution_status"] == "completed":
        confusion[gold][result["predicted_disposition"]] = 1
    crossed = result["generation_boundary_crossed"]
    return {
        "audit_version": "requirement-audit-v1",
        "audit_sha256": HASH,
        "audit_run_id": "oasa-test-run",
        "visibility_class": "evaluator_only",
        "cases": [case],
        "summary": {
            "visibility_class": "evaluator_only",
            "case_count": 1,
            "execution_status_counts": {
                "completed": int(result["execution_status"] == "completed"),
                "not_run": int(result["execution_status"] == "not_run"),
            },
            "predicted_disposition_counts": predicted_counts,
            "gold_disposition_counts": gold_counts,
            "confusion_matrix": confusion,
            "generation_boundary_crossed_count": int(crossed),
            "false_proceed_count": int(crossed and gold != "ready"),
            "false_block_count": int(not crossed and gold == "ready"),
            "counter_totals": counters(),
        },
    }


def validate(instance: dict) -> None:
    Draft202012Validator(load_schema()).validate(instance)


def clarification_case(*, boundary_crossed: bool = False) -> dict:
    case = ready_case()
    case["ambiguity_case_id"] = "cluster-001-reset-ambiguous"
    case["preflight_projection"]["envelope"]["facts"].append(
        {
            "fact_id": "reset.polarity",
            "origin": "unresolved",
            "value": None,
        }
    )
    case["preflight_projection"]["envelope"]["ambiguity_fact_ids"] = [
        "reset.polarity"
    ]
    case["boundary_result"].update(
        {
            "predicted_disposition": "needs_clarification",
            "reason_ids": ["critical_fact_unresolved"],
            "fact_ids": ["reset.polarity"],
            "generation_boundary_crossed": boundary_crossed,
        }
    )
    case["evaluator_only"] = {
        "visibility_class": "evaluator_only",
        "gold_disposition": "needs_clarification",
        "gold_reason_ids": ["critical_fact_unresolved"],
        "gold_fact_ids": ["reset.polarity"],
        "gold_capability_ids": [],
        "clarification_answer_branches": [
            {
                "branch_id": "active-low",
                "visibility_class": "evaluator_only",
                "answer_sha256": HASH,
                "answer_facts": {"reset.polarity": "active_low"},
                "expected_replay_disposition": "ready",
            }
        ],
    }
    return case


def test_requirement_audit_schema_is_draft_2020_12() -> None:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == (
        "https://sr2fpga.local/contracts/requirement-audit/v1"
    )
    assert schema["additionalProperties"] is False


def test_requirement_audit_is_registered_with_contained_path() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    record = manifest["contracts"]["requirement_audit"]
    path = record["path"]
    posix_path = PurePosixPath(path)

    assert record["version"] == "requirement-audit-v1"
    assert path == "contracts/requirement-audit/requirement-audit-v1.schema.json"
    assert not Path(path).is_absolute()
    assert not posix_path.is_absolute()
    assert ".." not in posix_path.parts
    assert (REPO_ROOT / path).resolve().is_relative_to(REPO_ROOT)
    assert (REPO_ROOT / path).is_file()


def test_minimal_requirement_audit_artifact_validates() -> None:
    validate(artifact())


def test_schema_freezes_dispositions_and_visibility_classes() -> None:
    schema = load_schema()
    assert schema["$defs"]["disposition"]["enum"] == [
        "ready",
        "needs_clarification",
        "capability_gap",
    ]
    assert set(schema["$defs"]["visibility_class"]["enum"]) == {
        "generation_visible",
        "audit_only",
        "evaluator_only",
    }
    assert schema["properties"]["visibility_class"]["const"] == (
        "evaluator_only"
    )


@pytest.mark.parametrize(
    "forbidden_field",
    ["gold_disposition", "clarification_answer_branches", "task_type"],
)
def test_generation_visible_projection_rejects_evaluator_only_fields(
    forbidden_field: str,
) -> None:
    instance = artifact()
    projection = instance["cases"][0]["generation_visible_projection"]
    projection[forbidden_field] = "must-not-leak"

    with pytest.raises(ValidationError):
        validate(instance)


def test_generation_visible_projection_requires_structured_public_width() -> None:
    instance = artifact()
    instance["cases"][0]["generation_visible_projection"].pop("width_bits")

    with pytest.raises(ValidationError):
        validate(instance)


def test_clarification_gold_requires_evaluator_only_answer_branch() -> None:
    case = clarification_case()
    validate(artifact(case))

    case["evaluator_only"].pop("clarification_answer_branches")
    with pytest.raises(ValidationError):
        validate(artifact(case))


def test_audit_can_record_false_proceed_without_rejecting_the_artifact() -> None:
    validate(artifact(clarification_case(boundary_crossed=True)))


def test_capability_gap_requires_a_capability_id() -> None:
    case = ready_case()
    case["boundary_result"].update(
        {
            "predicted_disposition": "capability_gap",
            "reason_ids": ["unsupported_capability"],
            "capability_ids": [],
        }
    )

    with pytest.raises(ValidationError):
        validate(artifact(case))


def test_not_run_has_reason_and_no_predicted_disposition() -> None:
    case = ready_case()
    result = case["boundary_result"]
    result["execution_status"] = "not_run"
    result["not_run_reason_id"] = "profile_unavailable"
    result["generation_boundary_crossed"] = False
    result.pop("predicted_disposition")
    validate(artifact(case))

    invalid = copy.deepcopy(case)
    invalid["boundary_result"]["predicted_disposition"] = "ready"
    with pytest.raises(ValidationError):
        validate(artifact(invalid))
