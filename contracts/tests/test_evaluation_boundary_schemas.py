import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
HASH = "a" * 64


def _schema(relative: str) -> dict:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(payload)
    return payload


def _official() -> dict:
    return {
        "contract_version": "official-hidden-outcome-v1",
        "evaluation_scope": "official_heldout",
        "episode_id": "episode-001",
        "method_condition_id": "M5",
        "decoding_seed": 7,
        "terminal_candidate_sha256": HASH,
        "hidden_evaluator_commitment_sha256": "b" * 64,
        "split_id": "paper1-heldout-v1",
        "purpose": "paper1_official_heldout",
        "public_pack_sha256": "c" * 64,
        "private_pack_sha256": "d" * 64,
        "one_shot_ledger_ref": "one-shot/hidden-key",
        "execution_status": "completed",
        "outcome": "pass",
    }


def _training() -> dict:
    return {
        "contract_version": "training-qualification-outcome-v1",
        "evaluation_scope": "training_qualification",
        "episode_id": "episode-001",
        "method_condition_id": "M5",
        "terminal_candidate_sha256": HASH,
        "training_split_id": "training-fold-v1",
        "purpose": "training_release_qualification",
        "public_pack_sha256": "c" * 64,
        "private_pack_sha256": "d" * 64,
        "execution_status": "completed",
        "outcome": "pass",
        "evaluator_evidence_refs": ["evidence/qualification-001"],
    }


def test_official_and_training_outcomes_are_incompatible_closed_contracts() -> None:
    official_schema = _schema("contracts/evaluation/official-hidden-outcome-v1.schema.json")
    training_schema = _schema(
        "contracts/evaluation/training-qualification-outcome-v1.schema.json"
    )
    Draft202012Validator(official_schema).validate(_official())
    Draft202012Validator(training_schema).validate(_training())

    with pytest.raises(ValidationError):
        Draft202012Validator(training_schema).validate(_official())
    with pytest.raises(ValidationError):
        Draft202012Validator(official_schema).validate(_training())


def test_official_outcome_rejects_hidden_raw_material_and_invalid_missingness() -> None:
    validator = Draft202012Validator(
        _schema("contracts/evaluation/official-hidden-outcome-v1.schema.json")
    )
    leaked = _official()
    leaked["stdout"] = "hidden case output"
    with pytest.raises(ValidationError):
        validator.validate(leaked)

    not_run = copy.deepcopy(_official())
    not_run["execution_status"] = "not_run"
    not_run.pop("outcome")
    not_run["infrastructure_reason"] = "tool_missing"
    validator.validate(not_run)
    not_run["outcome"] = "fail"
    with pytest.raises(ValidationError):
        validator.validate(not_run)


def test_development_outcome_contracts_are_closed_and_non_official() -> None:
    public_schema = _schema(
        "contracts/evaluation/development-public-evaluation-v1.schema.json"
    )
    outcome_schema = _schema(
        "contracts/evaluation/development-episode-outcome-v1.schema.json"
    )
    pre_candidate_stop_schema = _schema(
        "contracts/evaluation/development-pre-candidate-stop-outcome-v1.schema.json"
    )
    pre_candidate_stop_v2_schema = _schema(
        "contracts/evaluation/development-pre-candidate-stop-outcome-v2.schema.json"
    )
    his_correction_schema = _schema(
        "contracts/evaluation/development-his-correction-outcome-v1.schema.json"
    )
    pack_schema = _schema(
        "contracts/evaluation/full-pack-outcome-reconciliation-v1.schema.json"
    )
    pack_v2_schema = _schema(
        "contracts/evaluation/full-pack-outcome-reconciliation-v2.schema.json"
    )
    runner_v2_schema = _schema(
        "contracts/evaluation/full-pack-runner-reconciliation-v2.schema.json"
    )
    terminal_public_schema = _schema(
        "contracts/evaluation/development-terminal-public-outcome-v1.schema.json"
    )
    for schema in (
        public_schema,
        outcome_schema,
        pre_candidate_stop_schema,
        pre_candidate_stop_v2_schema,
        his_correction_schema,
        pack_schema,
        pack_v2_schema,
        runner_v2_schema,
        terminal_public_schema,
    ):
        assert schema["additionalProperties"] is False
    assert public_schema["properties"]["official_outcome"] == {"const": False}
    assert public_schema["properties"]["vpp_l3"] == {"type": "null"}
    assert outcome_schema["properties"]["vpp_l3_status"] == {
        "const": "not_evaluated"
    }
    assert outcome_schema["properties"]["official_outcome"] == {"const": False}
    assert pre_candidate_stop_schema["properties"]["method_condition"] == {
        "const": "M4"
    }
    assert pre_candidate_stop_schema["properties"]["analysis_population"] == {
        "const": "excluded"
    }
    assert pre_candidate_stop_schema["properties"]["development_vpp_l3"] == {
        "const": False
    }
    assert pre_candidate_stop_schema["properties"]["vpp_l3"] == {"type": "null"}
    assert pre_candidate_stop_v2_schema["properties"]["method_condition"] == {
        "const": "M4"
    }
    assert pre_candidate_stop_v2_schema["properties"]["h_validation"][
        "properties"
    ]["failed_stage"] == {"enum": ["h0", "h1", "h2", "h3"]}
    assert pre_candidate_stop_v2_schema["properties"]["development_vpp_l3"] == {
        "const": False
    }
    assert pre_candidate_stop_v2_schema["properties"]["vpp_l3"] == {
        "type": "null"
    }
    assert his_correction_schema["properties"]["evaluation_scope"] == {
        "const": "excluded_development_conformance_only"
    }
    assert his_correction_schema["properties"]["method_condition"] == {
        "const": "M5"
    }
    assert his_correction_schema["properties"]["analysis_population"] == {
        "const": "excluded"
    }
    assert his_correction_schema["properties"]["cost"]["properties"][
        "logical_model_stages"
    ] == {
        "const": {"req2his": 1, "system_his_repair": 1, "his2project": 1}
    }
    for field in (
        "official_outcome",
        "official_authority",
        "pass_credit_authority",
        "rq1_evidence",
        "rq2_evidence",
        "g3_accepted",
        "g4b_authorized",
        "generation_visible",
        "repair_visible",
    ):
        assert his_correction_schema["properties"][field] == {"const": False}
    assert his_correction_schema["properties"]["reducer_visible"] == {
        "const": True
    }
    for field in (
        "official_outcome",
        "official_authority",
        "pass_credit_authority",
        "rq1_evidence",
        "rq2_evidence",
        "g3_accepted",
        "g4b_authorized",
        "generation_visible",
        "repair_visible",
        "terminal_selection_authority",
    ):
        assert pre_candidate_stop_schema["properties"][field] == {"const": False}
        assert pre_candidate_stop_v2_schema["properties"][field] == {
            "const": False
        }
    assert pre_candidate_stop_schema["properties"]["reducer_visible"] == {
        "const": True
    }
    assert pre_candidate_stop_v2_schema["properties"]["reducer_visible"] == {
        "const": True
    }
    assert pack_schema["properties"]["g3_accepted"] == {"const": False}
    assert pack_schema["properties"]["g4b_authorized"] == {"const": False}
    assert pack_v2_schema["properties"]["blocking_gaps"]["const"][0] == (
        "runtime_scenario_evidence_reconciliation"
    )
    assert runner_v2_schema["$defs"]["reconciliation"]["properties"][
        "blocking_gaps"
    ]["const"][0] == "runtime_scenario_evidence_reconciliation"
    assert terminal_public_schema["properties"]["repair_visible"] == {"const": False}
    assert terminal_public_schema["properties"]["pass_credit_authority"] == {
        "const": False
    }
    assert terminal_public_schema["properties"]["official_outcome"] == {
        "const": False
    }
