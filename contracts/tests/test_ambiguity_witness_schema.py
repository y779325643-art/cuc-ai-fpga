import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/requirement-audit/ambiguity-witness-v1.schema.json").read_text(
        encoding="utf-8"
    )
)
HASH = "a" * 64


def _witness():
    return {
        "contract_version": "ambiguity-witness-v1",
        "artifact_sha256": HASH,
        "audit_run_id": "audit-001",
        "manifest_sha256": "b" * 64,
        "visibility_class": "evaluator_only",
        "private_canary": "PRIVATE-CANARY-123456",
        "cases": [
            {
                "base_requirement_cluster_id": "cluster-001",
                "ambiguity_case_id": "case-001",
                "expected_disposition": "needs_clarification",
                "adjudication_basis": "material_interpretations",
                "fact_graph_sha256": HASH,
                "capability_rationale_sha256": HASH,
                "critical_fact_ids": ["interface_protocols"],
                "capability_ids": [],
                "permitted_default_ids": ["reset_polarity"],
                "explicit_assumption_ids": [],
                "unknown_family_counterexample": False,
                "annotator_commitments": [
                    {"commitment_id": "annotator-a", "annotation_sha256": HASH},
                    {"commitment_id": "annotator-b", "annotation_sha256": HASH},
                ],
                "adjudicator_commitment": {
                    "commitment_id": "adjudicator-c",
                    "adjudication_sha256": HASH,
                    "status": "adjudicated",
                },
                "material_interpretation_witnesses": [
                    {
                        "witness_id": "interpretation-a",
                        "interpretation_sha256": HASH,
                        "observable_consequence_ids": ["observable-a"],
                        "support_status": "supported",
                    },
                    {
                        "witness_id": "interpretation-b",
                        "interpretation_sha256": HASH,
                        "observable_consequence_ids": ["observable-b"],
                        "support_status": "unsupported",
                    },
                ],
            }
        ],
    }


def test_ambiguity_witness_schema_is_closed_and_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    Draft202012Validator(SCHEMA).validate(_witness())
    assert SCHEMA["additionalProperties"] is False


def test_material_interpretation_adjudication_requires_two_witnesses() -> None:
    artifact = copy.deepcopy(_witness())
    artifact["cases"][0]["material_interpretation_witnesses"].pop()
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(artifact)


def test_non_ready_gold_cannot_claim_resolved_requirement_basis() -> None:
    artifact = copy.deepcopy(_witness())
    artifact["cases"][0]["adjudication_basis"] = "resolved_requirement"
    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(artifact)
