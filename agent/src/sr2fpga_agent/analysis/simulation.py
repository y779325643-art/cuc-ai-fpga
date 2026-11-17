"""Small, explicitly synthetic checks of the statistical procedure.

These exercise dependence and missingness behavior. They are not a calibrated
power guarantee for the as-yet-unfrozen real LLM task population.
"""

from __future__ import annotations

import math
import random
from typing import Any

from .core import (
    AnalysisInputError,
    AnalysisPolicy,
    ENDPOINTS,
    FAMILIES,
    METHODS,
    analyze,
    canonical_sha256,
)


def synthetic_dataset(
    *,
    clusters_per_family: int,
    configurations: int,
    replicates: int,
    seed: int,
    system_effect: float,
    build_effect: float,
    baseline_probability: float = 0.4,
    cluster_heterogeneity: float = 0.2,
    missing_probability: float = 0.0,
    effect_heterogeneity: float = 0.0,
    shared_pair_fraction: float = 0.0,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    for name, value, minimum, maximum in (
        ("clusters_per_family", clusters_per_family, 2, 1000),
        ("configurations", configurations, 1, 100),
        ("replicates", replicates, 1, 100),
    ):
        if type(value) is not int or not minimum <= value <= maximum:
            raise AnalysisInputError(f"invalid synthetic {name}")
    for value in (
        system_effect,
        build_effect,
        baseline_probability,
        cluster_heterogeneity,
        missing_probability,
        effect_heterogeneity,
        shared_pair_fraction,
    ):
        if type(value) not in {int, float} or not math.isfinite(value):
            raise AnalysisInputError("synthetic probabilities/effects must be finite")
    if not (
        -1 <= system_effect <= 1
        and -1 <= build_effect <= 1
        and 0 <= baseline_probability <= 1
        and 0 <= cluster_heterogeneity <= 1
        and 0 <= missing_probability <= 1
        and 0 <= effect_heterogeneity <= 1
        and 0 <= shared_pair_fraction <= 1
    ):
        raise AnalysisInputError("synthetic probability/effect outside range")
    lower, upper = (
        baseline_probability - cluster_heterogeneity,
        baseline_probability + cluster_heterogeneity,
    )
    if (
        lower < 0
        or upper > 1
        or lower
        + min(
            0, system_effect - effect_heterogeneity, build_effect - effect_heterogeneity
        )
        < 0
        or upper
        + max(
            0, system_effect + effect_heterogeneity, build_effect + effect_heterogeneity
        )
        > 1
    ):
        raise AnalysisInputError(
            "requested synthetic effects require probability clipping; choose feasible parameters"
        )
    if type(seed) is not int or not 0 <= seed < (1 << 63):
        raise AnalysisInputError("invalid synthetic seed")
    rng = random.Random(seed)
    slots, results = [], []
    for family in FAMILIES:
        for cluster in range(clusters_per_family):
            probability = baseline_probability + rng.uniform(
                -cluster_heterogeneity, cluster_heterogeneity
            )
            cluster_effect = rng.uniform(-effect_heterogeneity, effect_heterogeneity)
            for configuration in range(configurations):
                instance = f"{family}-c{cluster}-j{configuration}"
                task = canonical_sha256({"synthetic_task": instance})
                suite = canonical_sha256({"synthetic_suite": instance})
                for replicate in range(replicates):
                    # Common uniforms create paired within-task dependence.
                    direct_uniform, pc_uniform = rng.random(), rng.random()
                    if rng.random() < shared_pair_fraction:
                        pc_uniform = direct_uniform
                    probabilities = {
                        "M0": probability,
                        "M1": probability,
                        "M2": probability,
                        "M3": probability,
                        "M4": probability + build_effect + cluster_effect,
                        "M5": probability + system_effect + cluster_effect,
                    }
                    for method in METHODS:
                        slot_id = f"{instance}-r{replicate}-{method}"
                        slot = {
                            "slot_id": slot_id,
                            "family_id": family,
                            "design_cluster_id": f"c{cluster}",
                            "dependency_group_id": None,
                            "semantic_instance_id": instance,
                            "replicate_id": str(replicate),
                            "method_condition": method,
                            "endpoint": ENDPOINTS[method],
                            "task_sha256": task,
                            "suite_sha256": suite,
                        }
                        slots.append(slot)
                        if rng.random() < missing_probability:
                            continue
                        uniform = (
                            pc_uniform if method in {"M3", "M4"} else direct_uniform
                        )
                        value = int(uniform < probabilities[method])
                        results.append(
                            {
                                "slot_id": slot_id,
                                "task_sha256": task,
                                "suite_sha256": suite,
                                "value": value,
                                "outcome_class": "design_outcome",
                                "budget_status": "compliant",
                                "integrity_status": "intact",
                                "candidate_sha256": canonical_sha256(
                                    {"synthetic_candidate": slot_id}
                                )
                                if value
                                else None,
                            }
                        )
    manifest = {
        "contract_version": "pc21-analysis-manifest-v1",
        "research_plan_version": "paper1-v2.3",
        "population_id": "llm_inference_subsystems_v1",
        "analysis_population": "development",
        "slots": slots,
    }
    return manifest, results


def simulate(
    policy: AnalysisPolicy,
    *,
    trials: int,
    clusters_per_family: int,
    configurations: int = 1,
    replicates: int = 2,
    seed: int = 0,
    boundary_null: bool = False,
    baseline_probability: float = 0.4,
    cluster_heterogeneity: float = 0.2,
    missing_probability: float = 0.0,
    effect_heterogeneity: float = 0.0,
    shared_pair_fraction: float = 0.0,
) -> dict[str, Any]:
    if type(trials) is not int or not 1 <= trials <= 10_000:
        raise AnalysisInputError("synthetic trials must be 1..10000")
    effects = policy.deltas if boundary_null else policy.target_effects
    rejections = {"system": 0, "build": 0}
    computed = {"system": 0, "build": 0}
    joint = 0
    for trial in range(trials):
        manifest, results = synthetic_dataset(
            clusters_per_family=clusters_per_family,
            configurations=configurations,
            replicates=replicates,
            seed=seed + trial,
            system_effect=effects["system"],
            build_effect=effects["build"],
            baseline_probability=baseline_probability,
            cluster_heterogeneity=cluster_heterogeneity,
            missing_probability=missing_probability,
            effect_heterogeneity=effect_heterogeneity,
            shared_pair_fraction=shared_pair_fraction,
        )
        report = analyze(manifest, results, policy)
        decisions = []
        for contrast in report["contrasts"]:
            name = contrast["contrast"]
            decision = contrast["eligible_numerical_decision"]
            computed[name] += decision is not None
            rejections[name] += decision is True
            decisions.append(decision is True)
        joint += all(decisions)
    return {
        "simulation_scope": "synthetic_development_check",
        "official": False,
        "claim_authorized": False,
        "model_calls": 0,
        "trials": trials,
        "boundary_null_requested": boundary_null,
        "effects_requested": dict(effects),
        "policy": policy.to_dict(),
        "seed": seed,
        "clusters_per_family": clusters_per_family,
        "configurations": configurations,
        "replicates": replicates,
        "baseline_probability": baseline_probability,
        "cluster_heterogeneity": cluster_heterogeneity,
        "missing_probability": missing_probability,
        "effect_heterogeneity": effect_heterogeneity,
        "shared_pair_fraction": shared_pair_fraction,
        "computed_trials": computed,
        "rejection_counts": rejections,
        "rejection_fractions_all_trials": {
            name: count / trials for name, count in rejections.items()
        },
        "joint_rejection_fraction_all_trials": joint / trials,
        "calibration_validated": False,
        "limitations": [
            "finite synthetic runs do not establish real-population power or type-I-error control",
            "degenerate/ineligible trials stay in the reported trial denominator",
        ],
    }
