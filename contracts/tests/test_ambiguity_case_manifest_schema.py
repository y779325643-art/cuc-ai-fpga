import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/requirement-audit/ambiguity-case-manifest-v1.schema.json").read_text(
        encoding="utf-8"
    )
)


def _manifest() -> dict:
    return {
        "contract_version": "ambiguity-case-manifest-v1",
        "manifest_sha256": "a" * 64,
        "audit_run_id": "audit-001",
        "visibility_class": "evaluator_only",
        "cases": [
            {
                "base_requirement_cluster_id": "cluster-001",
                "ambiguity_case_id": "case-001",
                "public_projection": {
                    "visibility_class": "generation_visible",
                    "requirement": "Build an 8-bit counter.",
                    "width_bits": 8,
                    "platform": {
                        "name": "generic_verilog",
                        "vendor": "generic",
                        "toolchain": "open_source",
                    },
                },
                "evaluator_only": {
                    "visibility_class": "evaluator_only",
                    "audit_stratum": "ready_fully_specified",
                    "disposition": "ready",
                    "reason_ids": [],
                    "fact_ids": [],
                    "capability_ids": [],
                },
            }
        ],
    }


def test_ambiguity_case_manifest_schema_is_closed_and_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    Draft202012Validator(SCHEMA).validate(_manifest())
    assert SCHEMA["additionalProperties"] is False


@pytest.mark.parametrize("field", ["disposition", "gold_fact_ids", "answer_facts"])
def test_public_projection_rejects_private_fields(field: str) -> None:
    manifest = copy.deepcopy(_manifest())
    manifest["cases"][0]["public_projection"][field] = "private"
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(manifest)


def test_clarification_case_requires_one_precommitted_answer_branch() -> None:
    manifest = _manifest()
    gold = manifest["cases"][0]["evaluator_only"]
    gold["disposition"] = "needs_clarification"
    gold["fact_ids"] = ["interface_protocols"]
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(manifest)


def test_clarification_case_rejects_multiple_answer_branches() -> None:
    manifest = _manifest()
    gold = manifest["cases"][0]["evaluator_only"]
    gold["disposition"] = "needs_clarification"
    gold["fact_ids"] = ["interface_protocols"]
    branch = {
        "branch_id": "answer-001",
        "answer_facts": {"interface_protocols": "valid_ready"},
        "expected_replay_disposition": "ready",
    }
    gold["clarification_answer_branches"] = [branch, {**branch, "branch_id": "answer-002"}]
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(manifest)


def test_audit_stratum_must_match_gold_disposition() -> None:
    manifest = _manifest()
    manifest["cases"][0]["evaluator_only"]["audit_stratum"] = "capability_gap"
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(manifest)
