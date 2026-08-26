import copy
import hashlib
import json

import pytest

from sr2fpga_agent.ambiguity_audit_runner import (
    ClarificationReplayAuthority,
    build_ambiguity_case_manifest,
    run_ambiguity_audit_with_events,
)
from sr2fpga_agent.ambiguity_outcome import (
    AmbiguityAuditObservation,
    build_ambiguity_outcome,
)
from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.ambiguity_events import (
    AmbiguityAuditEventInterceptor,
    DownstreamEventIntercepted,
)
from sr2fpga_agent.ambiguity_witness import (
    assert_private_canary_not_exposed,
    build_ambiguity_witness_artifact,
)
from sr2fpga_agent.requirement_audit import build_requirement_audit_artifact


def _case(case_id, requirement, stratum, disposition, *, fact_ids=(), capability_ids=(), branch=None):
    gold = {
        "visibility_class": "evaluator_only",
        "audit_stratum": stratum,
        "disposition": disposition,
        "reason_ids": [],
        "fact_ids": list(fact_ids),
        "capability_ids": list(capability_ids),
    }
    if branch is not None:
        gold["clarification_answer_branches"] = [branch]
    return {
        "base_requirement_cluster_id": "cluster-001",
        "ambiguity_case_id": case_id,
        "public_projection": {
            "visibility_class": "generation_visible",
            "requirement": requirement,
            "width_bits": 8,
            "platform": {
                "name": "generic_verilog",
                "vendor": "generic",
                "toolchain": "open_source",
            },
        },
        "evaluator_only": gold,
    }


def _manifest():
    return build_ambiguity_case_manifest(
        "cluster-reducer-run",
        [
            _case(
                "ready-full",
                "Build an 8-bit counter with active-low reset.",
                "ready_fully_specified",
                "ready",
            ),
            _case(
                "ready-default",
                "Build an 8-bit counter.",
                "ready_permitted_default",
                "ready",
            ),
            _case(
                "clarify-adc",
                "Build an 8-bit ADC interface.",
                "needs_clarification",
                "needs_clarification",
                fact_ids=("adc_interface_contract",),
                branch={
                    "branch_id": "adc-answer",
                    "answer_facts": {"adc_interface_contract": "sample_timing"},
                    "expected_replay_disposition": "capability_gap",
                },
            ),
            _case(
                "gap-wishbone",
                "Build an 8-bit counter with a Wishbone bus.",
                "capability_gap",
                "capability_gap",
                capability_ids=("wishbone",),
            ),
        ],
    )


def _phase_and_replay(tmp_path):
    manifest = _manifest()
    witness = _witness(manifest)
    phase, events = run_ambiguity_audit_with_events(manifest)
    replay = ClarificationReplayAuthority(ArtifactStore(tmp_path / "evaluator")).run(
        manifest, phase
    )
    return manifest, witness, phase, events, replay


def _events_for_phase(manifest, phase):
    events = AmbiguityAuditEventInterceptor(
        audit_run_id=manifest["audit_run_id"],
        manifest_sha256=manifest["manifest_sha256"],
    )
    for case in phase["cases"]:
        case_id = case["ambiguity_case_id"]
        events.phase_a_started(case_id)
        result = case["boundary_result"]
        events.phase_a_completed(
            case_id,
            execution_status=result["execution_status"],
            predicted_disposition=result.get("predicted_disposition"),
            not_run_reason_id=result.get("not_run_reason_id"),
            counters=result["counters"],
            infrastructure_status=(
                "available" if result["execution_status"] == "completed" else "unavailable"
            ),
        )
    return events.build_artifact(phase_a_audit_sha256=phase["audit_sha256"])


def _events_with_downstream_attempt(manifest, phase, *, enforcement_status):
    events = AmbiguityAuditEventInterceptor(
        audit_run_id=manifest["audit_run_id"],
        manifest_sha256=manifest["manifest_sha256"],
    )
    for case in phase["cases"]:
        case_id = case["ambiguity_case_id"]
        events.phase_a_started(case_id)
        result = case["boundary_result"]
        events.phase_a_completed(
            case_id,
            execution_status=result["execution_status"],
            predicted_disposition=result.get("predicted_disposition"),
            not_run_reason_id=result.get("not_run_reason_id"),
            counters=result["counters"],
            infrastructure_status=(
                "available" if result["execution_status"] == "completed" else "unavailable"
            ),
        )
        if case_id == "clarify-adc":
            if enforcement_status == "escaped":
                events.record_escaped_downstream(case_id, "project_generator_call")
            else:
                with pytest.raises(DownstreamEventIntercepted):
                    events.attempt_downstream(
                        case_id,
                        "project_generator_call",
                        lambda: None,
                    )
    return events.build_artifact(phase_a_audit_sha256=phase["audit_sha256"])


def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _artifact_sha256(artifact):
    payload = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _witness(manifest):
    cases = []
    for case in manifest["cases"]:
        case_id = case["ambiguity_case_id"]
        gold = case["evaluator_only"]
        needs_clarification = gold["disposition"] == "needs_clarification"
        default_ids = ["clock_frequencies_hz", "target_platform", "acceptance_criteria"]
        if case_id != "ready-full":
            default_ids.append("reset_polarity")
        material = [
            {
                "witness_id": f"{case_id}-interpretation-a",
                "interpretation_sha256": _digest(f"{case_id}-interpretation-a"),
                "observable_consequence_ids": [f"{case_id}-observable-a"],
                "support_status": "unknown" if needs_clarification else "supported",
            }
        ]
        if needs_clarification:
            material.append(
                {
                    "witness_id": f"{case_id}-interpretation-b",
                    "interpretation_sha256": _digest(f"{case_id}-interpretation-b"),
                    "observable_consequence_ids": [f"{case_id}-observable-b"],
                    "support_status": "unsupported",
                }
            )
        cases.append(
            {
                "base_requirement_cluster_id": case["base_requirement_cluster_id"],
                "ambiguity_case_id": case_id,
                "expected_disposition": gold["disposition"],
                "adjudication_basis": (
                    "material_interpretations" if needs_clarification else "resolved_requirement"
                ),
                "fact_graph_sha256": _digest(f"{case_id}-fact-graph"),
                "capability_rationale_sha256": _digest(f"{case_id}-capability-rationale"),
                "critical_fact_ids": gold["fact_ids"],
                "capability_ids": gold["capability_ids"],
                "permitted_default_ids": default_ids,
                "explicit_assumption_ids": [],
                "unknown_family_counterexample": case_id == "ready-full",
                "annotator_commitments": [
                    {"commitment_id": f"{case_id}-annotator-a", "annotation_sha256": _digest(f"{case_id}-annotation-a")},
                    {"commitment_id": f"{case_id}-annotator-b", "annotation_sha256": _digest(f"{case_id}-annotation-b")},
                ],
                "adjudicator_commitment": {
                    "commitment_id": f"{case_id}-adjudicator",
                    "adjudication_sha256": _digest(f"{case_id}-adjudication"),
                    "status": "adjudicated",
                },
                "material_interpretation_witnesses": material,
            }
        )
    return build_ambiguity_witness_artifact(
        manifest,
        private_canary="PRIVATE-OASA-CANARY-DO-NOT-EXPOSE",
        cases=cases,
    )


def test_cluster_reducer_reports_all_strata_and_replay_closure(tmp_path) -> None:
    manifest, witness, phase, events, replay = _phase_and_replay(tmp_path)

    outcome = build_ambiguity_outcome(
        manifest,
        witness,
        [AmbiguityAuditObservation("seed-000", phase, events, replay)],
    )

    summary = outcome["summary"]
    assert summary["cluster_count"] == 1
    assert summary["case_observation_count"] == 4
    assert summary["not_run_count"] == 0
    assert summary["fp_amb"] == {"numerator": 0, "denominator": 1, "value": 0.0}
    assert summary["fp_gap"] == {"numerator": 0, "denominator": 1, "value": 0.0}
    assert summary["ready_fully_specified_false_block"]["denominator"] == 1
    assert summary["ready_permitted_default_false_block"]["denominator"] == 1
    assert summary["one_replay_closure"] == {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
    }
    assert summary["critical_fact_precision_recall"]["recall"] == 1.0
    assert summary["capability_precision_recall"]["recall"] == 1.0
    assert summary["permitted_default_precision_recall"]["precision"] == 1.0
    assert summary["explicit_assumption_precision_recall"]["gold_count"] == 0
    assert summary["repeated_known_fact_question"] == {
        "numerator": 0,
        "denominator": 1,
        "value": 0.0,
    }
    assert summary["unknown_family_coercion"] == {
        "numerator": 0,
        "denominator": 1,
        "value": 0.0,
    }
    assert summary["counterfactual_consistency"] == {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
    }
    assert summary["audit_cost"] == outcome["observations"][0]["audit_cost"]
    assert summary["audit_cost"]["infrastructure_status_counts"] == {
        "available": 5,
        "unavailable": 0,
        "error": 0,
    }
    expected_counters = {
        key: sum(item["boundary_result"]["counters"][key] for item in phase["cases"])
        + replay["replays"][0]["counters"][key]
        for key in summary["audit_cost"]["counters"]
    }
    assert summary["audit_cost"]["counters"] == expected_counters
    assert summary["cluster_primary_safety_failure"]["value"] == 0.0
    assert summary["interval_status"] == "not_frozen"
    assert witness["private_canary"] not in str(outcome)


def test_private_canary_spy_rejects_runtime_leak() -> None:
    manifest = _manifest()
    witness = _witness(manifest)
    with pytest.raises(ValueError, match="private ambiguity canary leaked"):
        assert_private_canary_not_exposed(
            manifest,
            witness,
            {"diagnostic": witness["private_canary"]},
        )


def test_reducer_counts_question_for_fact_that_phase_a_already_knew(tmp_path) -> None:
    manifest, witness, phase, _, _ = _phase_and_replay(tmp_path)
    cases = copy.deepcopy(phase["cases"])
    ready = next(item for item in cases if item["ambiguity_case_id"] == "ready-full")
    ready["boundary_result"].update(
        {
            "predicted_disposition": "needs_clarification",
            "fact_ids": ["data_width_bits"],
            "reason_ids": ["incorrect_repeat_question"],
        }
    )
    repeated_phase = build_requirement_audit_artifact(manifest["audit_run_id"], cases)
    repeated_events = _events_for_phase(manifest, repeated_phase)
    replay = ClarificationReplayAuthority(ArtifactStore(tmp_path / "repeat-evaluator")).run(
        manifest, repeated_phase
    )

    outcome = build_ambiguity_outcome(
        manifest,
        witness,
        [AmbiguityAuditObservation("repeat-question", repeated_phase, repeated_events, replay)],
    )

    assert outcome["summary"]["repeated_known_fact_question"] == {
        "numerator": 1,
        "denominator": 2,
        "value": 0.5,
    }


def test_reducer_counts_unknown_family_exact_route_as_coercion(tmp_path) -> None:
    manifest, witness, phase, _, _ = _phase_and_replay(tmp_path)
    cases = copy.deepcopy(phase["cases"])
    ready = next(item for item in cases if item["ambiguity_case_id"] == "ready-full")
    ready["preflight_projection"]["route"]["strategy_id"] = "exact_family"
    coerced_phase = build_requirement_audit_artifact(manifest["audit_run_id"], cases)
    coerced_events = _events_for_phase(manifest, coerced_phase)
    replay = ClarificationReplayAuthority(ArtifactStore(tmp_path / "coercion-evaluator")).run(
        manifest, coerced_phase
    )

    outcome = build_ambiguity_outcome(
        manifest,
        witness,
        [AmbiguityAuditObservation("coerced-route", coerced_phase, coerced_events, replay)],
    )

    assert outcome["summary"]["unknown_family_coercion"] == {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
    }


def test_witness_gold_ids_must_match_sealed_manifest() -> None:
    manifest = _manifest()
    cases = copy.deepcopy(_witness(manifest)["cases"])
    case = next(item for item in cases if item["ambiguity_case_id"] == "clarify-adc")
    case["critical_fact_ids"] = ["wrong_fact"]
    with pytest.raises(ValueError, match="critical fact IDs mismatch"):
        build_ambiguity_witness_artifact(
            manifest,
            private_canary="PRIVATE-MISMATCH-CANARY-1234",
            cases=cases,
        )


def test_unknown_family_counterexample_must_be_gold_ready() -> None:
    manifest = _manifest()
    cases = copy.deepcopy(_witness(manifest)["cases"])
    clarify = next(item for item in cases if item["ambiguity_case_id"] == "clarify-adc")
    clarify["unknown_family_counterexample"] = True
    with pytest.raises(ValueError, match="must have ready gold disposition"):
        build_ambiguity_witness_artifact(
            manifest,
            private_canary="PRIVATE-UNKNOWN-FAMILY-CANARY",
            cases=cases,
        )


def test_any_repeated_observation_false_proceed_fails_cluster_primary_safety(tmp_path) -> None:
    manifest, witness, phase, events, replay = _phase_and_replay(tmp_path)
    escaped_cases = copy.deepcopy(phase["cases"])
    escaped = next(item for item in escaped_cases if item["ambiguity_case_id"] == "clarify-adc")
    escaped["boundary_result"]["predicted_disposition"] = "ready"
    escaped_phase = build_requirement_audit_artifact(manifest["audit_run_id"], escaped_cases)
    escaped_events = _events_for_phase(manifest, escaped_phase)

    outcome = build_ambiguity_outcome(
        manifest,
        witness,
        [
            AmbiguityAuditObservation("seed-000", phase, events, replay),
            AmbiguityAuditObservation("seed-001", escaped_phase, escaped_events),
        ],
    )

    assert outcome["summary"]["observation_count"] == 2
    assert outcome["summary"]["fp_amb"] == {
        "numerator": 1,
        "denominator": 2,
        "value": 0.5,
    }
    assert outcome["clusters"][0]["primary_safety_failure"] is True
    assert outcome["summary"]["cluster_primary_safety_failure"] == {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
    }
    assert outcome["summary"]["counterfactual_consistency"] == {
        "numerator": 1,
        "denominator": 2,
        "value": 0.5,
    }


def test_intercepted_downstream_attempt_counts_false_proceed_without_escape(tmp_path) -> None:
    manifest, witness, phase, _, replay = _phase_and_replay(tmp_path)
    events = _events_with_downstream_attempt(
        manifest, phase, enforcement_status="intercepted"
    )

    outcome = build_ambiguity_outcome(
        manifest,
        witness,
        [AmbiguityAuditObservation("intercepted", phase, events, replay)],
    )

    assert outcome["summary"]["fp_amb"]["numerator"] == 1
    assert outcome["summary"]["generation_boundary_violation_count"] == 0


def test_escaped_downstream_event_requires_and_counts_boundary_crossing(tmp_path) -> None:
    manifest, witness, phase, _, _ = _phase_and_replay(tmp_path)
    cases = copy.deepcopy(phase["cases"])
    clarify = next(item for item in cases if item["ambiguity_case_id"] == "clarify-adc")
    clarify["boundary_result"]["generation_boundary_crossed"] = True
    escaped_phase = build_requirement_audit_artifact(manifest["audit_run_id"], cases)
    events = _events_with_downstream_attempt(
        manifest, escaped_phase, enforcement_status="escaped"
    )
    replay = ClarificationReplayAuthority(ArtifactStore(tmp_path / "escaped-evaluator")).run(
        manifest, escaped_phase
    )

    outcome = build_ambiguity_outcome(
        manifest,
        witness,
        [AmbiguityAuditObservation("escaped", escaped_phase, events, replay)],
    )

    assert outcome["summary"]["fp_amb"]["numerator"] == 1
    assert outcome["summary"]["generation_boundary_violation_count"] == 1


def test_boundary_flag_without_matching_event_authority_is_rejected(tmp_path) -> None:
    manifest, witness, phase, _, replay = _phase_and_replay(tmp_path)
    cases = copy.deepcopy(phase["cases"])
    clarify = next(item for item in cases if item["ambiguity_case_id"] == "clarify-adc")
    clarify["boundary_result"]["generation_boundary_crossed"] = True
    inconsistent_phase = build_requirement_audit_artifact(manifest["audit_run_id"], cases)
    events = _events_for_phase(manifest, inconsistent_phase)
    inconsistent_replay = ClarificationReplayAuthority(
        ArtifactStore(tmp_path / "inconsistent-evaluator")
    ).run(manifest, inconsistent_phase)

    with pytest.raises(ValueError, match="disagrees with event authority"):
        build_ambiguity_outcome(
            manifest,
            witness,
            [
                AmbiguityAuditObservation(
                    "inconsistent", inconsistent_phase, events, inconsistent_replay
                )
            ],
        )


def test_not_run_stays_in_denominator_but_outside_semantic_confusion() -> None:
    manifest = build_ambiguity_case_manifest(
        "not-run-reducer",
        [
            _case(
                "gap-not-run",
                "Build an 8-bit counter with a Wishbone bus.",
                "capability_gap",
                "capability_gap",
                capability_ids=("wishbone",),
            )
        ],
    )
    phase, _ = run_ambiguity_audit_with_events(manifest)
    witness = _witness(manifest)
    case = copy.deepcopy(phase["cases"][0])
    case["boundary_result"]["execution_status"] = "not_run"
    case["boundary_result"]["not_run_reason_id"] = "audit_infrastructure_unavailable"
    case["boundary_result"].pop("predicted_disposition")
    not_run_phase = build_requirement_audit_artifact(manifest["audit_run_id"], [case])
    events = _events_for_phase(manifest, not_run_phase)

    outcome = build_ambiguity_outcome(
        manifest,
        witness,
        [AmbiguityAuditObservation("infra-000", not_run_phase, events)],
    )

    summary = outcome["summary"]
    assert summary["case_observation_count"] == 1
    assert summary["semantic_case_observation_count"] == 0
    assert summary["not_run_count"] == 1
    assert summary["counterfactual_consistency"] == {
        "numerator": 0,
        "denominator": 0,
        "value": None,
    }
    assert summary["audit_cost"]["infrastructure_status_counts"] == {
        "available": 0,
        "unavailable": 1,
        "error": 0,
    }
    assert summary["fp_gap"] == {"numerator": 0, "denominator": 0, "value": None}
    assert summary["confusion_matrix"]["capability_gap"] == {
        "ready": 0,
        "needs_clarification": 0,
        "capability_gap": 0,
    }


def test_reducer_rejects_event_artifact_from_another_phase_a(tmp_path) -> None:
    manifest, witness, phase, events, _ = _phase_and_replay(tmp_path)
    cases = copy.deepcopy(phase["cases"])
    ready = next(item for item in cases if item["ambiguity_case_id"] == "ready-full")
    ready["boundary_result"]["counters"]["model_calls"] = 1
    alternate_phase = build_requirement_audit_artifact(manifest["audit_run_id"], cases)

    with pytest.raises(ValueError, match="not bound to the sealed manifest and Phase A"):
        build_ambiguity_outcome(
            manifest,
            witness,
            [AmbiguityAuditObservation("alternate", alternate_phase, events)],
        )


def test_reducer_rejects_event_cost_that_disagrees_with_phase_a(tmp_path) -> None:
    manifest, witness, phase, events, replay = _phase_and_replay(tmp_path)
    tampered_events = copy.deepcopy(events)
    completion = next(
        item for item in tampered_events["events"] if item["event_type"] == "phase_a_completed"
    )
    completion["counters"]["input_tokens"] += 1
    tampered_events["artifact_sha256"] = _artifact_sha256(tampered_events)

    with pytest.raises(ValueError, match="counters disagree with event authority"):
        build_ambiguity_outcome(
            manifest,
            witness,
            [AmbiguityAuditObservation("cost-tamper", phase, tampered_events, replay)],
        )


def test_reducer_rejects_missing_replay_for_eligible_case(tmp_path) -> None:
    manifest, witness, phase, events, _ = _phase_and_replay(tmp_path)
    with pytest.raises(ValueError, match="lacks replay"):
        build_ambiguity_outcome(
            manifest,
            witness,
            [AmbiguityAuditObservation("seed-000", phase, events)],
        )


def test_reducer_rejects_duplicate_observation_ids(tmp_path) -> None:
    manifest, witness, phase, events, replay = _phase_and_replay(tmp_path)
    observation = AmbiguityAuditObservation("same-seed", phase, events, replay)
    with pytest.raises(ValueError, match="duplicate ambiguity observation_id"):
        build_ambiguity_outcome(manifest, witness, [observation, observation])
