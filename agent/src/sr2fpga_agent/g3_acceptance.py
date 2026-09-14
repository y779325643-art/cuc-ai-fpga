"""Artifact-rebuilt G3 development acceptance, separate from official outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.checkpoint_stop_outcome import read_verified_checkpoint_stop_outcome
from sr2fpga_agent.episode_outcome import read_verified_development_episode_outcome
from sr2fpga_agent.evaluator_dispatch import read_verified_development_hidden_conformance_outcome
from sr2fpga_agent.g3_test_evidence import G3TestEvidenceRecorder, read_test_evidence
from sr2fpga_agent.his_correction_outcome import read_verified_development_his_correction_outcome
from sr2fpga_agent.hidden_execution_state import read_verified_hidden_execution_state
from sr2fpga_agent.model_gateway_provenance import read_verified_model_gateway_provenance
from sr2fpga_agent.provider_seed_capability import read_verified_provider_seed_capability
from sr2fpga_agent.public_evaluator import read_verified_development_public_outcome
from sr2fpga_agent.pre_candidate_outcome import read_verified_development_pre_candidate_stop_outcome
from sr2fpga_agent.repository_paths import discover_repository_root
from sr2fpga_agent.pc_assembly import read_verified_pc_assembly


def _test(module: str, name: str) -> str:
    return f"agent/tests/test_sr2fpga_agent_{module}.py::test_{name}"


# This finite matrix is implementation policy, never supplied by the caller.
# Minimum counts preserve parameterized H0-H3 and independent order coverage.
REQUIRED_SCENARIOS = {
    "pc_interface_determinism": (_test("pc_assembly", "assembly_valid_pc_is_deterministic_and_inputs_unchanged"), 1),
    "pc_interface_controlled_fields": (_test("pc_assembly", "controlled_root_fields_are_rejected"), 4),
    "pc_interface_failed_inputs": (_test("pc_assembly", "invalid_input_is_retained_as_failure_not_a_pc"), 4),
    "pc_interface_unknown_owner": (_test("pc_assembly", "unknown_owner_is_not_repaired"), 1),
    "pc_interface_binding_lookup": (_test("pc_assembly", "missing_or_ambiguous_binding_is_not_inferred"), 1),
    "pc_interface_h3_preserved": (_test("pc_assembly", "semantically_wrong_binding_reaches_unchanged_h3"), 1),
    "pc_interface_record_replay": (_test("pc_assembly", "record_replays_and_summary_tampering_is_rejected"), 1),
    "pc_interface_single_call": (_test("pc_assembly", "generator_is_one_call_and_repeated_attempt_cannot_dispatch"), 1),
    "pc_interface_provider_failure": (_test("pc_assembly", "provider_failure_is_not_parsed_as_a_success"), 1),
    "pc_interface_context_integrity": (_test("pc_assembly", "corrupt_frozen_context_is_rejected_before_prompt_or_assembly"), 1),
    "pc_interface_owner_derivation": (_test("pc_assembly", "derived_ownership_never_reassigns_the_model_owner"), 2),
    "pc_interface_unique_paths": (_test("pc_assembly", "duplicate_names_and_reserved_sources_are_rejected"), 1),
    "pc_interface_no_host_override": (_test("pc_assembly", "model_cannot_supply_derived_ownership_or_host_bindings"), 1),
    "pc_interface_missing_assessment": (_test("pc_assembly", "missing_assessment_is_not_a_semantic_failure"), 1),
    "pc_interface_cli": (_test("pc_assembly", "offline_cli_and_independent_record_replay"), 2),
    "pc_interface_source_freeze": (_test("pc_assembly", "source_drift_during_call_retains_raw_but_cannot_commit_a_result"), 1),
    "pc_interface_version_guard": (_test("pc_assembly", "interface_version_drift_is_a_pre_call_integrity_error"), 1),
    "pc_owner_alias_binding": (_test("pc_review_regressions", "h1_checks_owner_for_bare_and_qualified_references"), 4),
    "pc_custom_unit_case": (_test("pc_review_regressions", "custom_acceptance_preserves_case_sensitive_units_in_full_h3"), 2),
    "m5_shared_correction_v2": (_test("pc_review_regressions", "paired_m3_m5_shared_pc_correction_closes_and_replays"), 1),
    "m5_invalid_fpp_retained": (_test("pc_review_regressions", "pc_correction_followed_by_invalid_fpp_is_retained"), 1),
    "m5_missing_trajectory_guard": (_test("pc_review_regressions", "missing_trajectory_is_not_silently_treated_as_a_normal_stop"), 1),
    "m5_variable_local_costs": (_test("pc_review_regressions", "correction_costs_rebuild_shared_and_repair_calls"), 3),
    "m5_cost_misattribution_guard": (_test("pc_review_regressions", "correction_costs_reject_extra_pc_repair_and_misattribution"), 3),
    "m5_no_terminal_retained": (_test("pre_candidate_stop_outcome", "real_runner_m5_h_correction_uses_distinct_budget_stage"), 1),
    "pc_trace_structure_prompt": (_test("pc_generation_structure", "initial_and_correction_prompts_show_nested_trace_and_actual_root_keys"), 2),
    "pc_ownership_fragment": (_test("pc_generation_structure", "ownership_example_is_resolvable_and_reproduces_wrong_owner_failure"), 1),
    "pc_no_silent_structure_repair": (_test("pc_generation_structure", "generation_preserves_misnested_trace_for_h0_rejection"), 1),
    "h3_acceptance_declaration_paraphrases": (_test("acceptance_declaration", "complete_default_declarations_pass_full_h3"), 5),
    "h3_acceptance_declaration_rejections": (_test("acceptance_declaration", "invalid_default_declarations_fail_full_h3"), 9),
    "h3_acceptance_fragment_rejection": (_test("acceptance_declaration", "fragments_cannot_be_joined_into_an_obligation"), 1),
    "h3_explicit_acceptance_preservation": (_test("acceptance_declaration", "explicit_criteria_require_preserved_declaration_not_word_overlap"), 4),
    "h3_prompt_value_alignment": (_test("acceptance_declaration", "both_prompt_paths_explain_and_satisfy_value_rules"), 1),
    "m5_runner_failed_correction": (_test("pre_candidate_stop_outcome", "runner_m5_failed_correction_retains_stop_without_success_receipt"), 4),
    "natural_m4_stop": (_test("pre_candidate_stop_outcome", "natural_m4_stop_preserves_origin_and_replays"), 4),
    "short_public_workspace": (_test("public_evaluator", "public_tool_evaluator_ignores_candidate_testbench_and_keeps_logs_private"), 1),
    "provider_output_controls": (_test("provider_output_controls", "deepseek_no_local_token_limit_and_explicit_thinking"), 1),
    "provider_length_stop": (_test("provider_output_controls", "length_stop_retains_raw_answer_and_is_not_transport_retried"), 2),
    "m2_text_output_mode": (_test("provider_output_controls", "m2_plan_uses_text_format_without_losing_global_budget"), 1),
    "m5_unparsed_his_correction": (_test("provider_output_controls", "m5_unparsed_his_correction_closes_with_existing_budget"), 2),
    "unparsed_his_nonrepair_stop": (_test("provider_output_controls", "unparsed_his_is_retained_and_cannot_bypass_h0"), 2),
    "m5_bad_correction_budget": (_test("provider_output_controls", "m5_bad_correction_stops_after_one_budgeted_attempt"), 1),
    "gold_ready_m0_m5_and_three_cost_views": (_test("full_pack_smoke", "real_runner_three_view_costs_are_order_invariant"), 1),
    "explicit_pairing_and_balanced_order": (_test("paired_block", "balanced_method_orders_balance_positions_and_predecessors"), 1),
    "requested_seed_provenance": (_test("model_gateway_provenance", "budgeted_calls_keep_zero_based_ids_in_runner_provenance"), 1),
    "m1_public_diagnosis_patch_rerun": (_test("repair_engineering_smoke", "runner_repair_engineering_smoke_is_budgeted_and_fail_closed"), 1),
    "m5_public_diagnosis_patch_rerun": (_test("g3_scenarios", "m5_public_failure_repair_closes"), 1),
    "m5_h0_h3_correction": (_test("pre_candidate_stop_outcome", "real_runner_m5_h_correction_acceptance_is_artifact_derived_and_fail_closed"), 4),
    "public_and_hidden_pass_fail": (_test("repair_engineering_smoke", "runner_hidden_fail_is_terminal_one_shot_and_never_repairs"), 1),
    "public_l2_fail": (_test("g3_scenarios", "public_l2_failure_closes_registered_outcome"), 1),
    "provider_infrastructure_not_run": (_test("g3_scenarios", "provider_failure_closes_without_candidate"), 1),
    "no_candidate_design_failure": (_test("g3_scenarios", "invalid_shared_output_is_design_failure_not_infrastructure"), 1),
    "public_infrastructure_not_run": (_test("public_evaluator", "public_authority_preserves_evaluator_exception_as_not_run"), 1),
    "hidden_infrastructure_not_run": (_test("evaluator_dispatch", "hidden_sanitizer_maps_invalid_private_result_to_not_run"), 1),
    "hidden_same_terminal_retry": (_test("hidden_execution_state", "hidden_precommit_retry_is_same_terminal_and_single_commit"), 2),
    "hidden_no_rescoring": (_test("hidden_execution_state", "hidden_subject_cannot_be_rescored_by_changing_identity"), 3),
    "hidden_exhausted_infrastructure": (_test("hidden_execution_state", "hidden_exhausted_infrastructure_has_no_semantic_commit"), 1),
    "hidden_integrity_error": (_test("hidden_execution_state", "hidden_integrity_error_never_retries_or_commits"), 1),
    "hidden_commit_tamper": (_test("hidden_execution_state", "hidden_companion_rejects_forged_counts_and_extra_events"), 1),
    "hidden_paired_case_seed": (_test("hidden_execution_state", "hidden_case_seed_is_shared_by_paired_methods_not_sample_ids"), 1),
    "hidden_retry_cost_reconciliation": (_test("g3_scenarios", "hidden_retry_cost_closes_without_new_model_or_repair_call"), 1),
    "l3_infrastructure_not_run": (_test("g3_scenarios", "l3_infrastructure_closes_registered_outcome"), 1),
    "tamper_and_lineage_rejection": (_test("pre_candidate_stop_outcome", "real_runner_m4_h_stage_stop_is_rebuilt_and_tamper_closed"), 4),
    "ordering_rejection": (_test("full_pack_smoke", "runner_k0_resume_rejects_reordered_frozen_samples_before_side_effects"), 1),
    "budget_rejection": (_test("full_pack_smoke", "real_runner_rejects_invalid_frozen_policy_before_preparation_effects"), 1),
    "trusted_edit_rejection": (_test("repair_engineering_smoke", "runner_repair_engineering_smoke_is_budgeted_and_fail_closed"), 1),
    "candidate_visibility": (_test("runner_method_dispatch", "m0_m5_prompt_spy_is_nonvacuous_and_hides_block_metadata"), 1),
    "provider_positive_guard": (_test("provider_seed_capability", "synthetic_independent_review_fixture_can_pass_development_guard"), 1),
    "provider_negative_classifier": (_test("provider_seed_capability", "best_effort_documented_probe_remains_ineligible"), 1),
    "provider_classifier_tamper": (_test("provider_seed_capability", "loader_recomputes_every_persisted_summary_field"), 1),
    "provider_predispatch_guard": (_test("runner_method_dispatch", "strict_paired_seed_control_stops_before_run_side_effects"), 1),
    "ambiguity_four_strata": (_test("g3_scenarios", "ambiguity_four_strata_replay_is_artifact_derived"), 1),
    "ambiguity_private_visibility": (_test("ambiguity_outcome", "private_canary_spy_rejects_runtime_leak"), 1),
    "stop_before_generation": (_test("ambiguity_audit_runner", "runner_executes_phase_a_without_crossing_generation_boundary"), 1),
}


def reconcile_g3_acceptance(root: Path, test_evidence_ref: ArtifactRef) -> tuple[dict, ArtifactRef]:
    """Rebuild finite coverage from actual test reports and verified artifacts.

    A green test report alone is insufficient for positive execution cells.
    Existing development contracts are read, not upgraded or rewritten.
    """
    evidence = read_test_evidence(root, test_evidence_ref)
    nodes = evidence["collected_node_ids"]
    reports: dict[str, list[dict]] = {node: [] for node in nodes}
    for report in evidence["test_reports"]:
        if report["node_id"] not in reports:
            raise ValueError("G3 report names an uncollected test")
        reports[report["node_id"]].append(report)
    matrix = []
    for scenario, (prefix, minimum) in REQUIRED_SCENARIOS.items():
        matching = [node for node in nodes if node == prefix or node.startswith(prefix + "[")]
        reasons = []
        if len(matching) < minimum:
            reasons.append("required_test_cases_missing")
        for node in matching:
            phases = reports[node]
            if sorted(item["phase"] for item in phases) != ["call", "setup", "teardown"]:
                reasons.append("incomplete_or_duplicate_test_lifecycle")
            if any(item["outcome"] != "passed" or item["was_xfail"] for item in phases):
                reasons.append("test_failed_skipped_or_xfailed")
        records = [record for record in evidence["artifact_records"] if record["node_id"] in matching]
        if not reasons:
            reasons.extend(_artifact_gaps(root, scenario, records))
        matrix.append({
            "scenario_id": scenario, "test_node_ids": matching,
            "status": "passed" if not reasons else "blocked",
            "reasons": sorted(set(reasons)),
            "source_artifacts": records,
        })
    accepted = evidence["pytest_exit_status"] == 0 and all(row["status"] == "passed" for row in matrix)
    payload = {
        "contract_version": "g3-acceptance-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "test_evidence_ref": test_evidence_ref.to_dict(),
        "required_matrix_sha256": _digest(REQUIRED_SCENARIOS),
        "matrix": matrix, "g3_accepted": accepted,
        "official_outcome": False, "official_authority": False,
        "pass_credit_authority": False, "g4b_authorized": False,
    }
    payload["acceptance_id"] = "g3-" + _digest(payload)
    ref = ArtifactStore(root / "evidence").put_validated_json(
        f"g3/acceptance/{payload['acceptance_id']}", payload, contract_key="g3_acceptance",
    )
    return payload, ref


def read_verified_g3_acceptance(root: Path, reference: ArtifactRef) -> dict:
    payload = json.loads(ArtifactStore(root / "evidence").read_verified(reference))
    errors = ContractRegistry().load_schema("g3_acceptance").validate(payload)
    if errors:
        raise ValueError("invalid G3 acceptance: " + "; ".join(errors))
    rebuilt, rebuilt_ref = reconcile_g3_acceptance(root, ArtifactRef(**payload["test_evidence_ref"]))
    if rebuilt != payload or rebuilt_ref != reference:
        raise ValueError("G3 acceptance does not match rebuilt evidence")
    return payload


def _artifact_gaps(root: Path, scenario: str, records: list[dict]) -> list[str]:
    verified: dict[str, list[dict]] = {}
    retry_costs = {}
    failure_origins = {}
    unparsed_corrections = 0
    seen = set()
    for record in records:
        key = record["contract_key"]
        identity = (record["store_id"], key, record["artifact_ref"]["sha256"])
        if identity in seen:
            continue
        seen.add(identity)
        # Negative tests intentionally create schema-valid forged summaries.
        # Only fully replayable positive records can satisfy execution cells.
        if key not in {"pc_assembly_record", "development_episode_outcome", "development_his_correction_outcome", "development_his_correction_outcome_v2",
                       "development_provider_seed_capability", "model_gateway_provenance",
                       "development_paired_block_cost_reconciliation", "development_checkpoint_stop_outcome",
                       "development_hidden_conformance_outcome", "development_terminal_public_outcome",
                       "ambiguity_outcome", "development_hidden_execution_state",
                       "development_pre_candidate_stop_outcome_v3"}:
            continue
        store = ArtifactStore(root / "snapshots" / record["store_id"])
        ref = ArtifactRef(**record["artifact_ref"])
        try:
            if key == "pc_assembly_record":
                payload = read_verified_pc_assembly(store, ref)
            elif key == "development_episode_outcome":
                payload = read_verified_development_episode_outcome(store, ref)
                trajectory = json.loads(store.read_verified(ArtifactRef(**payload["trajectory_ref"])))
                failure_origins[(payload["episode_id"], payload["method_condition"])] = trajectory["failure_origin"]
                retry_costs[(payload["episode_id"], payload["method_condition"])] = sum(
                    json.loads(store.read_verified(ArtifactRef(**raw)))["axes"]["hidden_infrastructure_retries"]["value"]
                    for raw in payload["cost_summary_refs"]
                )
            elif key == "development_pre_candidate_stop_outcome_v3":
                payload = read_verified_development_pre_candidate_stop_outcome(store, ref)
            elif key in {"development_his_correction_outcome", "development_his_correction_outcome_v2"}:
                payload = read_verified_development_his_correction_outcome(store, ref)
                initial = json.loads(store.read_verified(ArtifactRef(**payload["initial_his_ref"])))
                if initial.get("contract_version") == "unparsed-system-his-output-v1":
                    unparsed_corrections += 1
            elif key == "development_provider_seed_capability":
                payload = read_verified_provider_seed_capability(store, ref)
            elif key == "model_gateway_provenance":
                payload = read_verified_model_gateway_provenance(store, ref)
            elif key == "development_checkpoint_stop_outcome":
                payload = read_verified_checkpoint_stop_outcome(store, ref)
            elif key == "development_hidden_conformance_outcome":
                payload = read_verified_development_hidden_conformance_outcome(store, ref)
            elif key == "development_hidden_execution_state":
                payload = _replay_hidden_companion(root, store, ref)
            elif key == "development_terminal_public_outcome":
                payload = read_verified_development_public_outcome(store, ref)
            elif key == "ambiguity_outcome":
                from sr2fpga_agent.ambiguity_outcome import AmbiguityAuditObservation, build_ambiguity_outcome

                parts = {name: json.loads(store.read_verified("ambiguity/" + name))
                         for name in ("manifest", "witness", "phase", "events", "replay")}
                payload = build_ambiguity_outcome(parts["manifest"], parts["witness"], [
                    AmbiguityAuditObservation("g3", parts["phase"], parts["events"], parts["replay"])
                ])
                if payload != json.loads(store.read_verified(ref)):
                    raise ValueError("ambiguity outcome does not match raw audit evidence")
            else:
                from sr2fpga_agent.measurement_freeze import freeze_fingerprint
                from sr2fpga_agent.paired_cost_views import read_development_paired_block_cost_reconciliation
                raw = json.loads(store.read_verified(ref))
                block = json.loads(store.read_verified(ArtifactRef(**raw["paired_block_ref"])))
                freeze = json.loads(store.read_verified("g3/measurement-freeze"))
                if freeze["freeze_fingerprint"] != freeze_fingerprint(freeze):
                    raise ValueError("measurement freeze fingerprint mismatch")
                payload = read_development_paired_block_cost_reconciliation(
                    store, ref, expected_preparation_policy=freeze["block_preparation_policies"][block["paired_block_id"]],
                )
        except (ValueError, KeyError, RuntimeError, OSError, TypeError):
            continue
        verified.setdefault(key, []).append(payload)
    outcomes = verified.get("development_episode_outcome", [])
    if scenario == "pc_interface_record_replay" and not any(
        item["status"] == "pc_valid" for item in verified.get("pc_assembly_record", [])
    ):
        return ["replayable_pc_assembly_missing"]
    if scenario == "pc_interface_failed_inputs" and not any(
        item["status"] == "input_parse_failed" and item["pc_ref"] is None
        for item in verified.get("pc_assembly_record", [])
    ):
        return ["replayable_pc_input_failure_missing"]
    if scenario == "m5_shared_correction_v2" and not any(
        item["cost"]["logical_model_calls"] == 2 and "req2his" not in item["cost"]["logical_model_stages"]
        for item in verified.get("development_his_correction_outcome_v2", [])
    ):
        return ["replayed_shared_pc_correction_local_cost_missing"]
    if scenario == "natural_m4_stop":
        stops = verified.get("development_pre_candidate_stop_outcome_v3", [])
        if {item["failure"]["stage"] for item in stops if item["failure_origin"] == "natural_llm"} != {"h0", "h1", "h2", "h3"}:
            return ["replayable_natural_h0_h3_stops_missing"]
    if scenario == "m5_unparsed_his_correction" and unparsed_corrections < 1:
        return ["replayed_unparsed_his_correction_missing"]
    if scenario == "gold_ready_m0_m5_and_three_cost_views":
        if {item["method_condition"] for item in outcomes if item["development_vpp_l3"] is True} != {f"M{i}" for i in range(6)}:
            return ["complete_replayable_m0_m5_outcomes_missing"]
        if not any(_closed_gold_block(item, outcomes) for item in verified.get("development_paired_block_cost_reconciliation", [])):
            return ["replayable_three_cost_views_and_outcomes_do_not_share_one_block"]
        hidden = verified.get("development_hidden_execution_state", [])
        if {item["method_condition"] for item in hidden if item["semantic_commit_count"] == 1} != {f"M{i}" for i in range(6)}:
            return ["replayable_hidden_semantic_commits_missing"]
        seeds = {item["decoding_seed"] for item in verified.get("development_hidden_conformance_outcome", [])}
        if len(seeds) != 1:
            return ["paired_hidden_case_seed_mismatch"]
    if scenario in {"m1_public_diagnosis_patch_rerun", "m5_public_diagnosis_patch_rerun"}:
        method = "M1" if scenario.startswith("m1") else "M5"
        if not any(item["method_condition"] == method and all(item["repair"][field] > 0
                   for field in ("diagnosis_count", "valid_patch_count", "rerun_count", "transitions"))
                   and failure_origins.get((item["episode_id"], method)) == "synthetic_injected"
                   for item in outcomes):
            return ["replayable_public_repair_transition_missing"]
    if scenario == "m5_h0_h3_correction":
        stages = {item["correction_lineage"]["failed_stage"] for item in verified.get("development_his_correction_outcome", [])}
        if stages != {"h0", "h1", "h2", "h3"}:
            return ["replayable_h0_h3_corrections_missing"]
    if scenario == "provider_positive_guard" and not any(item["paired_confirmatory_eligible"]
            for item in verified.get("development_provider_seed_capability", [])):
        return ["recomputed_positive_capability_missing"]
    if scenario == "provider_negative_classifier" and not any(not item["paired_confirmatory_eligible"]
            for item in verified.get("development_provider_seed_capability", [])):
        return ["recomputed_negative_capability_missing"]
    if scenario == "requested_seed_provenance" and not verified.get("model_gateway_provenance"):
        return ["verified_call_provenance_missing"]
    if scenario == "provider_infrastructure_not_run" and not verified.get("development_checkpoint_stop_outcome"):
        return ["registered_no_candidate_outcome_missing"]
    if scenario == "no_candidate_design_failure" and not any(item["semantic_status"] == "design_failure"
            and item["development_vpp_l3"] is False for item in verified.get("development_checkpoint_stop_outcome", [])):
        return ["registered_no_candidate_design_failure_missing"]
    if scenario == "public_infrastructure_not_run" and not any(item["execution_status"] == "not_run"
            for item in verified.get("development_terminal_public_outcome", [])):
        return ["registered_public_not_run_missing"]
    if scenario == "hidden_infrastructure_not_run" and not any(item["execution_status"] == "not_run"
            for item in verified.get("development_hidden_conformance_outcome", [])):
        return ["registered_hidden_not_run_missing"]
    if scenario == "hidden_same_terminal_retry" and not any(item["infrastructure_retry_count"] == 1
            and item["semantic_commit_count"] == 1 for item in verified.get("development_hidden_execution_state", [])):
        return ["replayed_same_terminal_retry_missing"]
    if scenario == "hidden_retry_cost_reconciliation" and {
        item["method_condition"] for item in verified.get("development_hidden_execution_state", [])
        if item["infrastructure_retry_count"] == 1
        and retry_costs.get((item["episode_id"], item["method_condition"])) == 1
    } != {f"M{i}" for i in range(6)}:
        return ["hidden_retry_costs_do_not_match_private_execution_counts"]
    for cell, status in (("hidden_exhausted_infrastructure", "infrastructure_error"), ("hidden_integrity_error", "integrity_error")):
        if scenario == cell and not any(item["hidden_execution_status"] == status
                and item["semantic_commit_count"] == 0 for item in verified.get("development_hidden_execution_state", [])):
            return ["replayed_hidden_nonsemantic_closure_missing"]
    if scenario == "public_and_hidden_pass_fail" and not any(item["hidden_l2"]["status"] == "fail"
            for item in verified.get("development_hidden_conformance_outcome", [])):
        return ["registered_hidden_fail_missing"]
    if scenario == "public_l2_fail" and not any(item["stage_outcomes"]["public_l2"]["status"] == "fail" for item in outcomes):
        return ["registered_public_l2_fail_missing"]
    if scenario == "l3_infrastructure_not_run" and not any(item["stage_outcomes"]["l3"]["status"] == "not_run"
            and item["repair"]["calls_attempted"] == 0 for item in outcomes):
        return ["registered_l3_not_run_missing"]
    if scenario == "ambiguity_four_strata" and not any(
            item["summary"]["case_observation_count"] == 4
            and item["summary"]["cluster_primary_safety_failure"]["value"] == 0.0
            and item["summary"]["one_replay_closure"]["value"] == 1.0
            for item in verified.get("ambiguity_outcome", [])):
        return ["replayed_four_strata_confusion_matrix_missing"]
    return []


def _replay_hidden_companion(root, candidate_store, ref):
    raw = json.loads(candidate_store.read_verified(ref))
    legacy = json.loads(candidate_store.read_verified(ArtifactRef(**raw["legacy_outcome_ref"])))
    digest = legacy["opaque_outcome_ref"]["outcome_id"].removeprefix("hidden-outcome-")
    for directory in sorted((root / "snapshots").glob("store-*")):
        if directory == candidate_store.root:
            continue
        private = ArtifactStore(directory)
        if private.reference(f"private-outcomes/{digest}") is None:
            continue
        try:
            return read_verified_hidden_execution_state(candidate_store, private, ref)
        except (ValueError, KeyError, RuntimeError, OSError, TypeError):
            continue
    raise ValueError("hidden companion has no matching private execution replay")


def _closed_gold_block(costs, outcomes):
    return costs["reconciliation_status"] == "complete" and all(
        any(outcome["method_condition"] == method["method_condition"]
            and outcome["trajectory_ref"] == method["trajectory_ref"]
            and outcome["development_vpp_l3"] is True for outcome in outcomes)
        for method in costs["method_records"]
    )


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--verify", metavar="ACCEPTANCE_KEY", help="replay an existing acceptance artifact without running tests")
    args = parser.parse_args(argv)
    root = args.output_root.resolve()
    repository = discover_repository_root()
    if repository / "artifacts" not in root.parents:
        parser.error("G3 output must be a new directory below repository artifacts/")
    if args.verify:
        if not root.is_dir():
            parser.error("G3 evidence directory does not exist")
        ref = ArtifactStore(root / "evidence").reference(args.verify)
        if ref is None:
            parser.error("acceptance key is not present in the evidence store")
        report = read_verified_g3_acceptance(root, ref)
        print(json.dumps({"g3_accepted": report["g3_accepted"], "acceptance_ref": ref.to_dict()}, indent=2))
        return 0 if report["g3_accepted"] else 1
    if root.exists():
        parser.error("G3 output directory already exists; use a fresh run directory")
    import pytest

    recorder = G3TestEvidenceRecorder(root)
    selections = sorted({value[0] for value in REQUIRED_SCENARIOS.values()})
    result = pytest.main(["-q", "-p", "no:cacheprovider", "--basetemp", str(root / "pytest-tmp"),
                          *selections], plugins=[recorder])
    if not hasattr(recorder, "manifest_ref"):
        return int(result) or 1
    report, ref = reconcile_g3_acceptance(root, recorder.manifest_ref)
    print(json.dumps({"g3_accepted": report["g3_accepted"], "acceptance_ref": ref.to_dict(),
                      "blocked_cells": [row["scenario_id"] for row in report["matrix"] if row["status"] != "passed"]}, indent=2))
    return 0 if report["g3_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
