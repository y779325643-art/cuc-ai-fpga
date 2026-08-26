import json
import hashlib

import pytest

from sr2fpga_agent.ambiguity_audit_runner import (
    ClarificationReplayAuthority,
    build_ambiguity_case_manifest,
    load_ambiguity_case_manifest,
    main,
    run_ambiguity_audit_manifest,
)
from sr2fpga_agent.artifact_store import ArtifactStore, OneShotViolation
from sr2fpga_agent.ambiguity_witness import build_ambiguity_witness_artifact


def _public(requirement: str) -> dict:
    return {
        "visibility_class": "generation_visible",
        "requirement": requirement,
        "width_bits": 8,
        "platform": {
            "name": "generic_verilog",
            "vendor": "generic",
            "toolchain": "open_source",
        },
    }


def _gold(
    disposition: str,
    *,
    audit_stratum: str | None = None,
    fact_ids=(),
    capability_ids=(),
    branches=(),
) -> dict:
    value = {
        "visibility_class": "evaluator_only",
        "audit_stratum": audit_stratum
        or ("ready_fully_specified" if disposition == "ready" else disposition),
        "disposition": disposition,
        "reason_ids": [],
        "fact_ids": list(fact_ids),
        "capability_ids": list(capability_ids),
    }
    if branches:
        value["clarification_answer_branches"] = list(branches)
    return value


def _case(case_id: str, requirement: str, gold: dict) -> dict:
    return {
        "base_requirement_cluster_id": "cluster-001",
        "ambiguity_case_id": case_id,
        "public_projection": _public(requirement),
        "evaluator_only": gold,
    }


def _manifest() -> dict:
    return build_ambiguity_case_manifest(
        "development-audit-001",
        [
            _case(
                "case-ready",
                "Build an 8-bit counter with active-low reset.",
                _gold("ready"),
            ),
            _case(
                "case-clarify",
                "Build an 8-bit ADC interface.",
                _gold(
                    "needs_clarification",
                    fact_ids=("adc_interface_contract",),
                    branches=(
                        {
                            "branch_id": "answer-001",
                            "answer_facts": {"adc_interface_contract": "sample_timing"},
                            "expected_replay_disposition": "capability_gap",
                        },
                    ),
                ),
            ),
        ],
    )


def _witness(manifest):
    def digest(value):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    cases = []
    for case in manifest["cases"]:
        case_id = case["ambiguity_case_id"]
        gold = case["evaluator_only"]
        clarify = gold["disposition"] == "needs_clarification"
        material = [
            {
                "witness_id": f"{case_id}-witness-a",
                "interpretation_sha256": digest(f"{case_id}-witness-a"),
                "observable_consequence_ids": [f"{case_id}-observable-a"],
                "support_status": "unknown" if clarify else "supported",
            }
        ]
        if clarify:
            material.append(
                {
                    "witness_id": f"{case_id}-witness-b",
                    "interpretation_sha256": digest(f"{case_id}-witness-b"),
                    "observable_consequence_ids": [f"{case_id}-observable-b"],
                    "support_status": "unsupported",
                }
            )
        cases.append(
            {
                "base_requirement_cluster_id": case["base_requirement_cluster_id"],
                "ambiguity_case_id": case_id,
                "expected_disposition": gold["disposition"],
                "adjudication_basis": "material_interpretations" if clarify else "resolved_requirement",
                "fact_graph_sha256": digest(f"{case_id}-facts"),
                "capability_rationale_sha256": digest(f"{case_id}-capabilities"),
                "critical_fact_ids": gold["fact_ids"],
                "capability_ids": gold["capability_ids"],
                "permitted_default_ids": [
                    "clock_frequencies_hz",
                    "target_platform",
                    "acceptance_criteria",
                    *( [] if case_id == "case-ready" else ["reset_polarity"] ),
                ],
                "explicit_assumption_ids": [],
                "unknown_family_counterexample": case_id == "case-ready",
                "annotator_commitments": [
                    {"commitment_id": f"{case_id}-ann-a", "annotation_sha256": digest(f"{case_id}-ann-a")},
                    {"commitment_id": f"{case_id}-ann-b", "annotation_sha256": digest(f"{case_id}-ann-b")},
                ],
                "adjudicator_commitment": {
                    "commitment_id": f"{case_id}-adj",
                    "adjudication_sha256": digest(f"{case_id}-adj"),
                    "status": "adjudicated",
                },
                "material_interpretation_witnesses": material,
            }
        )
    return build_ambiguity_witness_artifact(
        manifest,
        private_canary="PRIVATE-RUNNER-CANARY-DO-NOT-EXPOSE",
        cases=cases,
    )


def test_runner_executes_phase_a_without_crossing_generation_boundary() -> None:
    artifact = run_ambiguity_audit_manifest(_manifest())

    assert artifact["summary"]["case_count"] == 2
    assert artifact["summary"]["generation_boundary_crossed_count"] == 0
    assert artifact["summary"]["counter_totals"]["model_calls"] == 0
    assert artifact["summary"]["counter_totals"]["tool_calls"] == 0
    assert [case["boundary_result"]["predicted_disposition"] for case in artifact["cases"]] == [
        "ready",
        "needs_clarification",
    ]


def test_loader_rejects_tampered_sealed_manifest(tmp_path) -> None:
    manifest = _manifest()
    manifest["cases"][0]["public_projection"]["requirement"] = "tampered"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        load_ambiguity_case_manifest(path)


def test_runner_rejects_duplicate_case_ids() -> None:
    case = _case("duplicate", "Build an 8-bit counter.", _gold("ready"))
    manifest = build_ambiguity_case_manifest("duplicate-run", [case, case])

    with pytest.raises(ValueError, match="duplicate ambiguity_case_id"):
        run_ambiguity_audit_manifest(manifest)


def test_independent_cli_writes_valid_requirement_audit_artifact(tmp_path) -> None:
    manifest_path = tmp_path / "sealed.json"
    output_path = tmp_path / "outcome.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")

    main(["--manifest", str(manifest_path), "--output", str(output_path)])

    outcome = json.loads(output_path.read_text(encoding="utf-8"))
    assert outcome["audit_version"] == "requirement-audit-v1"
    assert outcome["visibility_class"] == "evaluator_only"
    assert outcome["summary"]["generation_boundary_crossed_count"] == 0


def test_clarification_replay_closes_once_without_generation(tmp_path) -> None:
    manifest = _manifest()
    phase_a = run_ambiguity_audit_manifest(manifest)
    authority = ClarificationReplayAuthority(ArtifactStore(tmp_path / "evaluator"))

    replay = authority.run(manifest, phase_a)

    assert replay["contract_version"] == "clarification-replay-v1"
    assert len(replay["replays"]) == 1
    record = replay["replays"][0]
    assert record["ambiguity_case_id"] == "case-clarify"
    assert record["actual_replay_disposition"] == "capability_gap"
    assert record["closure"] is True
    assert record["generation_boundary_crossed"] is False
    assert record["counters"]["model_calls"] == 0
    assert record["counters"]["tool_calls"] == 0
    assert len(record["lineage_sha256"]) == 64

    with pytest.raises(OneShotViolation, match="already consumed"):
        authority.run(manifest, phase_a)


def test_replay_rejects_answer_that_does_not_match_phase_a_requested_facts(tmp_path) -> None:
    case = _case(
        "case-wrong-answer",
        "Build an 8-bit ADC interface.",
        _gold(
            "needs_clarification",
            fact_ids=("adc_interface_contract",),
            branches=(
                {
                    "branch_id": "wrong-answer",
                    "answer_facts": {"reset_polarity": "active_low"},
                    "expected_replay_disposition": "capability_gap",
                },
            ),
        ),
    )
    manifest = build_ambiguity_case_manifest("wrong-answer-run", [case])
    phase_a = run_ambiguity_audit_manifest(manifest)

    with pytest.raises(ValueError, match="exactly match Phase A requested"):
        ClarificationReplayAuthority(ArtifactStore(tmp_path / "evaluator")).run(
            manifest, phase_a
        )


def test_replay_rejects_gold_clarification_when_phase_a_was_ready(tmp_path) -> None:
    case = _case(
        "case-ineligible",
        "Build an 8-bit counter with active-low reset.",
        _gold(
            "needs_clarification",
            fact_ids=("interface_protocols",),
            branches=(
                {
                    "branch_id": "ineligible-answer",
                    "answer_facts": {"interface_protocols": "valid_ready"},
                    "expected_replay_disposition": "ready",
                },
            ),
        ),
    )
    manifest = build_ambiguity_case_manifest("ineligible-run", [case])
    phase_a = run_ambiguity_audit_manifest(manifest)

    with pytest.raises(ValueError, match="requires Phase A needs_clarification"):
        ClarificationReplayAuthority(ArtifactStore(tmp_path / "evaluator")).run(
            manifest, phase_a
        )


def test_cli_can_write_phase_a_and_replay_artifacts(tmp_path) -> None:
    manifest_path = tmp_path / "sealed.json"
    phase_path = tmp_path / "phase-a.json"
    replay_path = tmp_path / "phase-b.json"
    outcome_path = tmp_path / "outcome.json"
    events_path = tmp_path / "events.json"
    witness_path = tmp_path / "witness.json"
    manifest = _manifest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    witness_path.write_text(json.dumps(_witness(manifest)), encoding="utf-8")

    main(
        [
            "--manifest",
            str(manifest_path),
            "--output",
            str(phase_path),
            "--replay-output",
            str(replay_path),
            "--evaluator-store",
            str(tmp_path / "evaluator"),
            "--outcome-output",
            str(outcome_path),
            "--observation-id",
            "seed-000",
            "--witness-artifact",
            str(witness_path),
            "--events-output",
            str(events_path),
        ]
    )

    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    assert replay["contract_version"] == "clarification-replay-v1"
    assert replay["replays"][0]["closure"] is True
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    assert outcome["contract_version"] == "ambiguity-outcome-v1"
    assert outcome["observations"][0]["observation_id"] == "seed-000"
    events = json.loads(events_path.read_text(encoding="utf-8"))
    assert events["contract_version"] == "ambiguity-audit-events-v1"
