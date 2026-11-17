"""Research-contract goldens and synthetic checks; no real experiment data."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from uuid import uuid4

import pytest

from sr2fpga_agent.analysis import (
    AnalysisInputError,
    AnalysisPolicy,
    analyze,
    canonical_sha256,
    holm_adjust,
    validate_dataset,
)
from sr2fpga_agent.analysis.core import ENDPOINTS, FAMILIES, METHODS
from sr2fpga_agent.analysis.simulation import simulate, synthetic_dataset


def policy(**changes):
    payload = {
        "deltas": {"system": 0.05, "build": 0.03},
        "target_effects": {"system": 0.15, "build": 0.10},
        "alpha": 0.05,
        "max_missing_fraction": 0.05,
        "max_missing_difference": 0.03,
        "bootstrap_resamples": 199,
        "seed": 913,
        "min_clusters_per_family": 2,
        "min_discordant_clusters": 2,
        "max_degenerate_fraction": 0.5,
    }
    payload.update(changes)
    return AnalysisPolicy.from_dict(payload)


def fixture_data(clusters=8):
    slots, results = [], []
    system = (1, 1, 0, 0, 1, 0, 1, 0)
    build = (0, 1, 0, 1, 1, 0, 0, 1)
    for family in FAMILIES:
        for cluster in range(clusters):
            instance = f"{family}-c{cluster}"
            task, suite = (
                canonical_sha256(instance),
                canonical_sha256(instance + "suite"),
            )
            for method in METHODS:
                slot_id = instance + "-" + method
                slots.append(
                    {
                        "slot_id": slot_id,
                        "family_id": family,
                        "design_cluster_id": str(cluster),
                        "dependency_group_id": None,
                        "semantic_instance_id": instance,
                        "replicate_id": "0",
                        "method_condition": method,
                        "endpoint": ENDPOINTS[method],
                        "task_sha256": task,
                        "suite_sha256": suite,
                    }
                )
                value = (
                    system[cluster % 8]
                    if method == "M5"
                    else build[cluster % 8]
                    if method == "M4"
                    else 0
                )
                results.append(
                    {
                        "slot_id": slot_id,
                        "task_sha256": task,
                        "suite_sha256": suite,
                        "value": value,
                        "outcome_class": "design_outcome",
                        "budget_status": "compliant",
                        "integrity_status": "intact",
                        "candidate_sha256": canonical_sha256(slot_id)
                        if value
                        else None,
                    }
                )
    return {
        "contract_version": "pc21-analysis-manifest-v1",
        "research_plan_version": "paper1-v2.3",
        "population_id": "llm_inference_subsystems_v1",
        "analysis_population": "development",
        "slots": slots,
    }, results


def test_manifest_drives_denominator_and_missing_results_remain_unknown():
    manifest, results = fixture_data(2)
    lost = next(row for row in manifest["slots"] if row["method_condition"] == "M5")
    results = [row for row in results if row["slot_id"] != lost["slot_id"]]
    dataset = validate_dataset(manifest, results)
    assert len(dataset.rows) == 3 * 2 * 6
    missing = next(row for row in dataset.rows if row["slot_id"] == lost["slot_id"])
    assert missing["value"] is None
    assert missing["record_present"] is False
    assert missing["reason"] == "missing_result_record"
    report = analyze(manifest, results, policy())
    effect = report["contrasts"][0]
    assert effect["full_denominator_bounds"][1] - effect["full_denominator_bounds"][
        0
    ] == pytest.approx(1 / 6)
    assert effect["qualification"]["eligible"] is False
    assert report["joint_eligible_numerical_rejection"] is None


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate_slot",
        "duplicate_natural",
        "duplicate_result",
        "unplanned",
        "task_hash",
        "suite_hash",
        "identity",
        "endpoint",
        "mapping",
        "missing_method",
    ],
)
def test_crossed_duplicate_and_unplanned_identities_are_rejected(damage):
    manifest, results = fixture_data(2)
    if damage == "duplicate_slot":
        manifest["slots"].append(deepcopy(manifest["slots"][0]))
    elif damage == "duplicate_natural":
        extra = deepcopy(manifest["slots"][0])
        extra["slot_id"] += "-renamed"
        manifest["slots"].append(extra)
    elif damage == "duplicate_result":
        results.append(deepcopy(results[0]))
    elif damage == "unplanned":
        results[0]["slot_id"] = "unplanned"
    elif damage in {"task_hash", "suite_hash"}:
        results[0][damage.replace("hash", "sha256")] = "f" * 64
    elif damage == "identity":
        results[0]["method_condition"] = "M5"
    elif damage == "endpoint":
        manifest["slots"][0]["endpoint"] = "B4"
    elif damage == "mapping":
        manifest["slots"][0]["design_cluster_id"] = "moved"
    else:
        manifest["slots"].pop()
        results.pop()
    with pytest.raises(AnalysisInputError):
        validate_dataset(manifest, results)


def test_manifest_and_result_content_bindings_are_verified():
    manifest, results = fixture_data(2)
    digest = canonical_sha256(manifest)
    manifest["manifest_sha256"] = digest
    results[0]["manifest_sha256"] = digest
    assert validate_dataset(manifest, results).manifest_sha256 == digest
    results[0]["manifest_sha256"] = "f" * 64
    with pytest.raises(AnalysisInputError, match="manifest binding"):
        validate_dataset(manifest, results)
    results[0]["manifest_sha256"] = digest
    manifest["slots"][0]["configuration_weight"] = 2
    with pytest.raises(AnalysisInputError, match="manifest content hash"):
        validate_dataset(manifest, results)


@pytest.mark.parametrize("cross_family", [False, True])
def test_identical_task_bytes_cannot_manufacture_independent_clusters(cross_family):
    manifest, results = fixture_data(2)
    original = next(
        row
        for row in manifest["slots"]
        if row["family_id"] == FAMILIES[0] and row["design_cluster_id"] == "0"
    )
    target_family = FAMILIES[1] if cross_family else FAMILIES[0]
    target_cluster = "0" if cross_family else "1"
    targets = set()
    for row in manifest["slots"]:
        if (
            row["family_id"] == target_family
            and row["design_cluster_id"] == target_cluster
        ):
            row["task_sha256"] = original["task_sha256"]
            targets.add(row["slot_id"])
    for row in results:
        if row["slot_id"] in targets:
            row["task_sha256"] = original["task_sha256"]
    with pytest.raises(AnalysisInputError, match="identical task bytes"):
        validate_dataset(manifest, results)


def test_unicode_identity_reuses_repository_canonical_json_convention():
    from sr2fpga_agent.models import sha256_json

    value = {"source": "量化推理", "nested": {"a": 1}}
    assert canonical_sha256(value) == sha256_json(value)
    with pytest.raises(AnalysisInputError, match="finite JSON"):
        canonical_sha256({"x": float("nan")})


@pytest.mark.parametrize("cross_family", [False, True])
def test_shared_dependency_groups_fail_closed_instead_of_assuming_independence(
    cross_family,
):
    manifest, results = fixture_data(2)
    selected = {
        FAMILIES[0] + "-c0",
        (FAMILIES[1] if cross_family else FAMILIES[0]) + "-c1",
    }
    for slot in manifest["slots"]:
        if slot["semantic_instance_id"] in selected:
            slot["dependency_group_id"] = "common-model-source"
    with pytest.raises(AnalysisInputError, match="coordinated inference"):
        validate_dataset(manifest, results)


def test_failure_unknown_not_applicable_and_qualification_are_separate():
    manifest, results = fixture_data(2)
    selected = next(row for row in results if row["value"] == 1)
    selected["budget_status"] = "unverifiable"
    dataset = validate_dataset(manifest, results)
    assert (
        next(row for row in dataset.rows if row["slot_id"] == selected["slot_id"])[
            "value"
        ]
        == 1
    )
    result = analyze(manifest, results, policy())
    assert any(
        "budget_not_verifiably_compliant" in reason
        for contrast in result["contrasts"]
        for reason in contrast["qualification"]["reasons"]
    )
    selected.update(value=None, candidate_sha256=None, outcome_class="not_applicable")
    result = analyze(manifest, results, policy())
    assert result["dataset"]["outcome_classes"]["not_applicable"] == 1
    assert result["dataset"]["planned_slots"] == 36


@pytest.mark.parametrize(
    "damage",
    [
        "bool_value",
        "false_success_class",
        "missing_candidate",
        "bad_budget",
        "bad_integrity",
    ],
)
def test_results_cannot_claim_inconsistent_success(damage):
    manifest, results = fixture_data(2)
    selected = next(row for row in results if row["value"] == 1)
    if damage == "bool_value":
        selected["value"] = True
    elif damage == "false_success_class":
        selected["outcome_class"] = "infrastructure_unscorable"
    elif damage == "missing_candidate":
        selected["candidate_sha256"] = None
    elif damage == "bad_budget":
        selected["budget_status"] = "trusted"
    else:
        selected["integrity_status"] = "probably-intact"
    with pytest.raises(AnalysisInputError):
        validate_dataset(manifest, results)


def test_configuration_replicate_cluster_and_family_weighting_has_hand_golden():
    manifest, results = fixture_data(2)
    original = deepcopy(manifest["slots"])
    # Cluster0: configuration A has two repeats at +1; B at -1 with weight3.
    # Cluster1: one configuration at +1. Thus cluster means -.5 and +1,
    # family means .25, and the three-family macro mean is also .25.
    for slot, result in zip(manifest["slots"], results):
        if slot["method_condition"] == "M5":
            result["value"] = 1
    for family in FAMILIES:
        block = [
            deepcopy(slot)
            for slot in original
            if slot["family_id"] == family and slot["design_cluster_id"] == "0"
        ]
        for kind in ("repeat", "config"):
            for template in block:
                slot = deepcopy(template)
                if kind == "repeat":
                    slot["replicate_id"] = "1"
                else:
                    slot["semantic_instance_id"] += "-B"
                    slot["configuration_weight"] = 3
                slot["slot_id"] += "-" + kind
                manifest["slots"].append(slot)
                value = int(
                    slot["method_condition"] == ("M5" if kind == "repeat" else "M1")
                )
                results.append(
                    {
                        "slot_id": slot["slot_id"],
                        "task_sha256": slot["task_sha256"],
                        "suite_sha256": slot["suite_sha256"],
                        "value": value,
                        "outcome_class": "design_outcome",
                        "budget_status": "compliant",
                        "integrity_status": "intact",
                        "candidate_sha256": canonical_sha256(slot["slot_id"])
                        if value
                        else None,
                    }
                )
    report = analyze(manifest, results, policy())
    assert report["contrasts"][0]["estimate"] == pytest.approx(0.25)
    assert all(
        value == pytest.approx(0.25)
        for value in report["contrasts"][0]["family_estimates_lower"].values()
    )


def test_holm_known_values_and_missing_hypothesis_retains_family_size():
    assert holm_adjust([0.01, 0.04]) == pytest.approx([0.02, 0.04])
    assert holm_adjust([0.025, 0.025]) == pytest.approx([0.05, 0.05])
    assert holm_adjust([0.02, None]) == [0.04, None]
    assert holm_adjust([None, None]) == [None, None]
    with pytest.raises(AnalysisInputError):
        holm_adjust([float("nan"), 0.1])
    with pytest.raises(AnalysisInputError):
        holm_adjust([True, 0.1])


def test_family_means_are_equal_weight_with_unequal_cluster_counts():
    manifest, results = fixture_data(4)
    limits = dict(zip(FAMILIES, (2, 3, 4)))
    manifest["slots"] = [
        row
        for row in manifest["slots"]
        if int(row["design_cluster_id"]) < limits[row["family_id"]]
    ]
    selected = {row["slot_id"]: row for row in manifest["slots"]}
    results = [row for row in results if row["slot_id"] in selected]
    for row in results:
        slot = selected[row["slot_id"]]
        row["value"] = int(
            slot["family_id"] == FAMILIES[0] and slot["method_condition"] == "M5"
        )
        row["candidate_sha256"] = (
            canonical_sha256(row["slot_id"]) if row["value"] else None
        )
    report = analyze(manifest, results, policy())
    assert report["contrasts"][0]["estimate"] == pytest.approx(1 / 3)
    assert report["method_rate_bounds"]["M5"]["macro_lower"] == pytest.approx(1 / 3)


def test_analysis_preserves_observations_and_differential_missingness_guard():
    manifest, results = fixture_data()
    lost = next(row for row in manifest["slots"] if row["method_condition"] == "M5")
    results = [row for row in results if row["slot_id"] != lost["slot_id"]]
    before = deepcopy((manifest, results))
    report = analyze(manifest, results, policy())
    assert (manifest, results) == before
    reason = report["contrasts"][0]["qualification"]["reasons"]
    assert "differential_missingness_exceeds_policy" in reason
    assert "method_missingness_exceeds_policy:M5" not in reason


def test_actual_integrity_violation_blocks_all_main_decisions_without_rewriting_values():
    manifest, results = fixture_data()
    results[0]["integrity_status"] = "violation"
    report = analyze(manifest, results, policy())
    assert report["dataset"]["integrity_statuses"]["violation"] == 1
    assert report["dataset"]["outcome_classes"] == {"design_outcome": 144}
    assert all(
        "dataset_integrity_violation_requires_scope_review"
        in row["qualification"]["reasons"]
        for row in report["contrasts"]
    )


def test_shared_synthetic_pairs_preserve_contrast_covariance():
    manifest, results = synthetic_dataset(
        clusters_per_family=8,
        configurations=1,
        replicates=3,
        seed=81,
        system_effect=0.15,
        build_effect=0.15,
        effect_heterogeneity=0.05,
        shared_pair_fraction=1,
    )
    chosen = policy(
        deltas={"system": 0.03, "build": 0.03},
        target_effects={"system": 0.15, "build": 0.15},
    )
    report = analyze(manifest, results, chosen)
    a, b = report["contrasts"]
    for field in (
        "estimate",
        "standard_error",
        "raw_p",
        "confidence_interval_95",
        "valid_bootstrap_samples",
        "degenerate_bootstrap_samples",
    ):
        assert a[field] == b[field]


def test_bootstrap_is_reproducible_joint_and_centered_at_boundary_null():
    manifest, results = fixture_data()
    chosen = policy(
        deltas={"system": 0.5, "build": 0.5},
        target_effects={"system": 0.7, "build": 0.7},
        bootstrap_resamples=999,
    )
    first = analyze(manifest, results, chosen)
    second = analyze(manifest, list(reversed(results)), chosen)
    assert first == second
    for contrast in first["contrasts"]:
        assert contrast["status"] == "computed"
        assert contrast["estimate"] == 0.5
        assert 0.25 < contrast["raw_p"] < 0.75
        assert (
            contrast["confidence_interval_95"][0]
            <= 0.5
            <= contrast["confidence_interval_95"][1]
        )
        assert contrast["valid_bootstrap_samples"] > 900
    assert first["official"] is False and first["claim_authorized"] is False
    assert first["model_calls"] == 0


def test_constant_and_small_cluster_data_report_degeneracy_without_fake_p():
    manifest, results = fixture_data(2)
    for row in results:
        row["value"] = int(row["slot_id"].endswith("M5"))
        row["candidate_sha256"] = (
            canonical_sha256(row["slot_id"]) if row["value"] else None
        )
    report = analyze(manifest, results, policy(min_clusters_per_family=3))
    for contrast in report["contrasts"]:
        assert contrast["status"] == "degenerate"
        assert contrast["raw_p"] is None
        assert contrast["holm_adjusted_p"] is None
        assert contrast["confidence_interval_95"] is None
    assert report["joint_eligible_numerical_rejection"] is None


def test_effect_and_missing_policy_must_be_explicit_and_valid():
    valid = policy().to_dict()
    assert AnalysisPolicy.from_dict(valid).to_dict() == valid
    for key in (
        "deltas",
        "target_effects",
        "max_missing_fraction",
        "max_missing_difference",
    ):
        wrong = dict(valid)
        wrong.pop(key)
        with pytest.raises(AnalysisInputError):
            AnalysisPolicy.from_dict(wrong)
    wrong = deepcopy(valid)
    wrong["target_effects"]["system"] = wrong["deltas"]["system"]
    with pytest.raises(AnalysisInputError):
        AnalysisPolicy.from_dict(wrong)
    wrong = dict(valid)
    wrong["contract_version"] = "unknown"
    with pytest.raises(AnalysisInputError):
        AnalysisPolicy.from_dict(wrong)


def test_synthetic_simulation_is_labelled_and_keeps_degenerate_trial_denominator():
    chosen = policy(
        deltas={"system": 0, "build": 0}, target_effects={"system": 0.15, "build": 0.1}
    )
    report = simulate(
        chosen, trials=3, clusters_per_family=4, seed=9, boundary_null=True
    )
    assert report["model_calls"] == 0 and report["official"] is False
    assert (
        report["claim_authorized"] is False and report["calibration_validated"] is False
    )
    assert report["trials"] == 3
    assert report["computed_trials"] == {"system": 0, "build": 0}
    assert report["rejection_fractions_all_trials"] == {"system": 0.0, "build": 0.0}
    assert report == simulate(
        chosen, trials=3, clusters_per_family=4, seed=9, boundary_null=True
    )
    with pytest.raises(AnalysisInputError, match="clipping"):
        synthetic_dataset(
            clusters_per_family=4,
            configurations=1,
            replicates=2,
            seed=2,
            system_effect=0.5,
            build_effect=0.5,
        )


def test_synthetic_dataset_obeys_the_registered_manifest_exchange():
    from sr2fpga_agent.contract_registry import ContractRegistry

    manifest, results = synthetic_dataset(
        clusters_per_family=3,
        configurations=1,
        replicates=2,
        seed=1,
        system_effect=0.15,
        build_effect=0.1,
    )
    assert (
        not ContractRegistry().load_schema("pc21_analysis_manifest").validate(manifest)
    )
    assert validate_dataset(manifest, results).summary()["planned_slots"] == 108


def test_cli_rejects_duplicate_json_without_running_analysis(tmp_path):
    from sr2fpga_agent.analysis.__main__ import _load

    path = tmp_path / "duplicate.json"
    path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
    with pytest.raises(AnalysisInputError, match="duplicate"):
        _load(path)
    path.write_text('{"x":NaN}', encoding="utf-8")
    with pytest.raises(AnalysisInputError, match="nonfinite"):
        _load(path)


def test_cli_analyze_registered_inputs_and_preserves_existing_output(tmp_path):
    # Root integrates the registered schemas; this is a real offline CLI path.
    from sr2fpga_agent.analysis.__main__ import main

    manifest, results = fixture_data()
    manifest_path, results_path, policy_path = (
        tmp_path / name for name in ("manifest.json", "results.json", "policy.json")
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    results_path.write_text(
        json.dumps(
            {
                "contract_version": "pc21-analysis-results-v1",
                "manifest_sha256": canonical_sha256(manifest),
                "results": results,
            }
        ),
        encoding="utf-8",
    )
    policy_path.write_text(json.dumps(policy().to_dict()), encoding="utf-8")
    repository = Path(__file__).resolve().parents[2]
    output = (
        repository
        / "artifacts"
        / "paper1-ai"
        / "pc21-runtime-implementation-20261028"
        / ("analysis-cli-" + uuid4().hex + ".json")
    )
    args = [
        "analyze",
        "--manifest",
        str(manifest_path),
        "--results",
        str(results_path),
        "--policy",
        str(policy_path),
        "--output",
        str(output),
    ]
    assert main(args) == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["dataset"]["planned_slots"] == 3 * 8 * 6
    with pytest.raises(SystemExit):
        main(args)
