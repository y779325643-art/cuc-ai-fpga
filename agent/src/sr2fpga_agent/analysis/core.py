"""Paired, stratified design-cluster analysis with explicit missingness.

The frozen plan supplies the denominator. Results never redefine task identity,
groups or configuration weights. Numerical inference is a development analysis,
not permission to publish an official or confirmatory research claim.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
import math
import random
import re
from statistics import mean, variance
from typing import Any, Mapping, Sequence

from sr2fpga_agent.models import sha256_json


METHODS = ("M0", "M1", "M2", "M3", "M4", "M5")
FAMILIES = (
    "llm_quantized_qkv_projection",
    "llm_kv_cache_decode_attention",
    "llm_gated_ffn",
)
CONTRASTS = (("system", "M5", "M1"), ("build", "M4", "M3"))
ENDPOINTS = {
    method: "B4" if method in {"M1", "M5"} else "initial" for method in METHODS
}
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_QUALIFICATION = {"compliant", "exceeded", "unverifiable"}
_INTEGRITY = {"intact", "violation", "unverifiable"}


class AnalysisInputError(ValueError):
    """The analysis input cannot represent the declared population faithfully."""


def canonical_sha256(value: Any) -> str:
    # Reuse the repository's newline-free UTF8 identity convention. The strict
    # check rejects nonfinite numbers without introducing another hash format.
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise AnalysisInputError("analysis identity requires finite JSON") from error
    return sha256_json(value)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisInputError(message)


def _identifier(value: Any, field: str) -> str:
    _require(
        isinstance(value, str) and bool(value) and value == value.strip(),
        f"{field} must be a nonempty, trimmed string",
    )
    return value


def _hash(value: Any, field: str) -> str:
    _require(
        isinstance(value, str) and _SHA.fullmatch(value) is not None,
        f"{field} must be a lowercase SHA256",
    )
    return value


def _number(
    value: Any, field: str, *, low: float, high: float, exclusive_low: bool = False
) -> float:
    _require(
        type(value) in {int, float} and math.isfinite(value),
        f"{field} must be finite numeric",
    )
    _require(
        (value > low if exclusive_low else value >= low) and value <= high,
        f"{field} outside its allowed range",
    )
    return float(value)


def _integer(value: Any, field: str, low: int, high: int) -> int:
    _require(
        type(value) is int and low <= value <= high,
        f"{field} must be an integer in [{low},{high}]",
    )
    return value


@dataclass(frozen=True)
class AnalysisPolicy:
    deltas: Mapping[str, float]
    target_effects: Mapping[str, float]
    alpha: float
    max_missing_fraction: float
    max_missing_difference: float
    bootstrap_resamples: int
    seed: int
    min_clusters_per_family: int
    min_discordant_clusters: int
    max_degenerate_fraction: float

    def __post_init__(self) -> None:
        _require(
            isinstance(self.deltas, Mapping)
            and isinstance(self.target_effects, Mapping),
            "effect boundaries and targets must be maps",
        )
        expected = {item[0] for item in CONTRASTS}
        _require(
            set(self.deltas) == set(self.target_effects) == expected,
            "deltas and target_effects must explicitly name system and build",
        )
        for name in expected:
            delta = _number(self.deltas[name], f"deltas.{name}", low=-1, high=1)
            target = _number(
                self.target_effects[name], f"target_effects.{name}", low=-1, high=1
            )
            _require(
                target > delta, f"target_effects.{name} must exceed its null boundary"
            )
        _number(self.alpha, "alpha", low=0, high=0.5, exclusive_low=True)
        _number(self.max_missing_fraction, "max_missing_fraction", low=0, high=1)
        _number(self.max_missing_difference, "max_missing_difference", low=0, high=1)
        _number(
            self.max_degenerate_fraction, "max_degenerate_fraction", low=0, high=0.99
        )
        _integer(self.bootstrap_resamples, "bootstrap_resamples", 99, 1_000_000)
        _integer(self.seed, "seed", 0, (1 << 63) - 1)
        _integer(self.min_clusters_per_family, "min_clusters_per_family", 2, 1_000_000)
        _integer(self.min_discordant_clusters, "min_discordant_clusters", 2, 1_000_000)
        # Copy caller-owned maps; analyze revalidates an independent snapshot.
        object.__setattr__(self, "deltas", dict(self.deltas))
        object.__setattr__(self, "target_effects", dict(self.target_effects))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AnalysisPolicy":
        payload = dict(payload)
        if "contract_version" in payload:
            _require(
                payload.pop("contract_version") == "pc21-analysis-policy-v1",
                "unsupported analysis policy version",
            )
        fields = set(cls.__dataclass_fields__)
        _require(
            set(payload) == fields,
            "analysis policy must specify every registered field, without extras",
        )
        return cls(**dict(payload))

    def to_dict(self) -> dict[str, Any]:
        return {"contract_version": "pc21-analysis-policy-v1", **asdict(self)}


@dataclass(frozen=True)
class JoinedDataset:
    manifest_sha256: str
    research_plan_version: str
    population_id: str
    analysis_population: str
    rows: tuple[dict[str, Any], ...]

    def summary(self) -> dict[str, Any]:
        return {
            "manifest_sha256": self.manifest_sha256,
            "research_plan_version": self.research_plan_version,
            "population_id": self.population_id,
            "analysis_population": self.analysis_population,
            "planned_slots": len(self.rows),
            "present_results": sum(row["record_present"] for row in self.rows),
            "missing_result_records": sum(
                not row["record_present"] for row in self.rows
            ),
            "outcome_classes": dict(Counter(row["outcome_class"] for row in self.rows)),
            "budget_statuses": dict(Counter(row["budget_status"] for row in self.rows)),
            "integrity_statuses": dict(
                Counter(row["integrity_status"] for row in self.rows)
            ),
            "retained_denominator": True,
        }


def validate_dataset(
    manifest: Mapping[str, Any], results: Sequence[Mapping[str, Any]]
) -> JoinedDataset:
    """Validate identities and left-join every planned slot, retaining absent rows."""
    _require(isinstance(manifest, Mapping), "manifest must be an object")
    _require(
        manifest.get("contract_version") == "pc21-analysis-manifest-v1",
        "unsupported analysis manifest",
    )
    _require(
        manifest.get("research_plan_version") == "paper1-v2.3",
        "analysis requires the current LLM plan",
    )
    _require(
        manifest.get("population_id") == "llm_inference_subsystems_v1",
        "analysis population mismatch",
    )
    population = manifest.get("analysis_population")
    _require(
        population in {"development", "excluded", "pilot", "formal_test"},
        "unknown analysis population",
    )
    slots = manifest.get("slots")
    _require(
        isinstance(slots, list) and bool(slots),
        "manifest slots must be a nonempty list",
    )
    _require(
        isinstance(results, Sequence) and not isinstance(results, (str, bytes)),
        "results must be a list",
    )
    raw_manifest = dict(manifest)
    claimed_hash = raw_manifest.pop("manifest_sha256", None)
    manifest_hash = canonical_sha256(raw_manifest)
    if claimed_hash is not None:
        _require(
            _hash(claimed_hash, "manifest_sha256") == manifest_hash,
            "manifest content hash mismatch",
        )
    by_slot = {}
    natural = set()
    block_methods: dict[tuple[Any, ...], set[str]] = defaultdict(set)
    instance_mapping = {}
    task_clusters = {}
    configuration_weights = {}
    dependency_members: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for position, item in enumerate(slots):
        _require(isinstance(item, Mapping), f"slots[{position}] must be an object")
        row = dict(item)
        slot_id = _identifier(row.get("slot_id"), "slot_id")
        _require(slot_id not in by_slot, "duplicate planned slot_id")
        for field in (
            "family_id",
            "design_cluster_id",
            "semantic_instance_id",
            "replicate_id",
        ):
            _identifier(row.get(field), field)
        _require(row["family_id"] in FAMILIES, "unregistered LLM analysis family")
        method = row.get("method_condition")
        _require(method in METHODS, "unknown method condition")
        _require(row.get("endpoint") == ENDPOINTS[method], "method endpoint mismatch")
        _hash(row.get("task_sha256"), "task_sha256")
        _hash(row.get("suite_sha256"), "suite_sha256")
        cluster_identity = (row["family_id"], row["design_cluster_id"])
        _require(
            task_clusters.setdefault(row["task_sha256"], cluster_identity)
            == cluster_identity,
            "identical task bytes cannot be assigned to independent design clusters",
        )
        dependency = row.get("dependency_group_id")
        if dependency is not None:
            _identifier(dependency, "dependency_group_id")
            dependency_members[dependency].add(
                (row["family_id"], row["design_cluster_id"])
            )
        weight = _number(
            row.get("configuration_weight", 1),
            "configuration_weight",
            low=0,
            high=1_000_000,
            exclusive_low=True,
        )
        row["configuration_weight"] = weight
        identity = (
            row["family_id"],
            row["semantic_instance_id"],
            row["replicate_id"],
            method,
            row["endpoint"],
        )
        _require(
            identity not in natural,
            "duplicate natural result identity under different slot IDs",
        )
        natural.add(identity)
        mapping = (
            row["family_id"],
            row["design_cluster_id"],
            dependency,
            row["task_sha256"],
            row["suite_sha256"],
        )
        previous = instance_mapping.setdefault(row["semantic_instance_id"], mapping)
        _require(
            previous == mapping,
            "semantic instance identity/hash/group mapping conflicts",
        )
        weight_key = (
            row["family_id"],
            row["design_cluster_id"],
            row["semantic_instance_id"],
        )
        _require(
            configuration_weights.setdefault(weight_key, weight) == weight,
            "configuration weight changes across methods or replicates",
        )
        block = (
            row["family_id"],
            row["design_cluster_id"],
            row["semantic_instance_id"],
            row["replicate_id"],
        )
        block_methods[block].add(method)
        by_slot[slot_id] = row
    _require(
        {row["family_id"] for row in by_slot.values()} == set(FAMILIES),
        "all three LLM families must be planned",
    )
    _require(
        all(methods == set(METHODS) for methods in block_methods.values()),
        "each paired block must plan all six methods",
    )
    _require(
        all(len(members) == 1 for members in dependency_members.values()),
        "shared dependency groups across design clusters require coordinated inference; unsupported, refusing independence",
    )
    by_result = {}
    bound_fields = (
        "family_id",
        "design_cluster_id",
        "dependency_group_id",
        "semantic_instance_id",
        "replicate_id",
        "method_condition",
        "endpoint",
    )
    for result in results:
        _require(isinstance(result, Mapping), "result must be an object")
        slot_id = _identifier(result.get("slot_id"), "result.slot_id")
        _require(slot_id in by_slot, "result references an unplanned slot")
        _require(slot_id not in by_result, "duplicate result for a planned slot")
        slot = by_slot[slot_id]
        for field in ("task_sha256", "suite_sha256"):
            _require(
                _hash(result.get(field), "result." + field) == slot[field],
                "result task/suite hash mismatch",
            )
        if "manifest_sha256" in result:
            _require(
                result["manifest_sha256"] == manifest_hash,
                "result manifest binding mismatch",
            )
        for field in bound_fields:
            if field in result:
                _require(
                    result[field] == slot.get(field),
                    "result identity override: " + field,
                )
        value = result.get("value")
        _require(
            value is None or type(value) is int and value in (0, 1),
            "result value must be 0, 1 or null",
        )
        outcome = result.get("outcome_class")
        _require(
            outcome
            in {"design_outcome", "infrastructure_unscorable", "not_applicable"},
            "unknown outcome class",
        )
        _require(
            (outcome == "design_outcome") == (value is not None),
            "outcome class and semantic value disagree",
        )
        _require(
            result.get("budget_status") in _QUALIFICATION,
            "unknown budget qualification",
        )
        _require(
            result.get("integrity_status") in _INTEGRITY,
            "unknown integrity qualification",
        )
        candidate = result.get("candidate_sha256")
        if candidate is not None:
            _hash(candidate, "candidate_sha256")
        _require(
            value != 1 or candidate is not None,
            "successful outcome requires a sealed candidate hash",
        )
        by_result[slot_id] = {
            **slot,
            "value": value,
            "outcome_class": outcome,
            "budget_status": result["budget_status"],
            "integrity_status": result["integrity_status"],
            "candidate_sha256": candidate,
            "reason": result.get("reason"),
            "record_present": True,
        }
    rows = []
    for slot_id, slot in by_slot.items():
        rows.append(
            by_result.get(
                slot_id,
                {
                    **slot,
                    "value": None,
                    "outcome_class": "infrastructure_unscorable",
                    "budget_status": "unverifiable",
                    "integrity_status": "unverifiable",
                    "candidate_sha256": None,
                    "reason": "missing_result_record",
                    "record_present": False,
                },
            )
        )
    return JoinedDataset(
        manifest_hash,
        "paper1-v2.3",
        "llm_inference_subsystems_v1",
        population,
        tuple(sorted(rows, key=lambda row: row["slot_id"])),
    )


def holm_adjust(p_values: Sequence[float | None]) -> list[float | None]:
    """Holm step-down adjustment, retaining unavailable members in the family."""
    for value in p_values:
        if value is not None:
            _number(value, "p value", low=0, high=1)
    ordered = sorted(
        range(len(p_values)),
        key=lambda index: 1.0 if p_values[index] is None else p_values[index],
    )
    adjusted: list[float | None] = [None] * len(p_values)
    running = 0.0
    for rank, index in enumerate(ordered):
        value = 1.0 if p_values[index] is None else p_values[index]
        running = max(running, min(1.0, (len(p_values) - rank) * value))
        if p_values[index] is not None:
            adjusted[index] = running
    return adjusted


def _aggregate(
    dataset: JoinedDataset, mode: str
) -> dict[str, list[tuple[float, float]]]:
    by_block: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(dict)
    for row in dataset.rows:
        key = (
            row["family_id"],
            row["design_cluster_id"],
            row["semantic_instance_id"],
            row["replicate_id"],
        )
        by_block[key][row["method_condition"]] = row
    configurations: dict[tuple[Any, ...], list[tuple[float, float]]] = defaultdict(list)
    weights = {}
    for key, methods in sorted(by_block.items()):
        vector = []
        for _, x, y in CONTRASTS:
            a, b = methods[x]["value"], methods[y]["value"]
            if a is None or b is None:
                if mode == "complete":
                    break
                a = (0 if mode == "lower" else 1) if a is None else a
                b = (1 if mode == "lower" else 0) if b is None else b
            vector.append(float(a - b))
        if len(vector) != len(CONTRASTS):
            continue
        configurations[key[:3]].append(tuple(vector))
        weights[key[:3]] = methods["M0"]["configuration_weight"]
    expected_per_cluster: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in dataset.rows:
        expected_per_cluster[(row["family_id"], row["design_cluster_id"])].add(
            row["semantic_instance_id"]
        )
    clusters: dict[tuple[str, str], list[tuple[float, tuple[float, float]]]] = (
        defaultdict(list)
    )
    for key, values in sorted(configurations.items()):
        # Complete-case sensitivity retains only entirely observed clusters.
        expected_replicates = sum(block[:3] == key for block in by_block)
        if mode == "complete" and len(values) != expected_replicates:
            continue
        vector = tuple(
            mean(row[index] for row in values) for index in range(len(CONTRASTS))
        )
        clusters[key[:2]].append((weights[key], vector))
    result = {family: [] for family in FAMILIES}
    for key, values in sorted(clusters.items()):
        if mode == "complete" and len(values) != len(expected_per_cluster[key]):
            continue
        total = sum(weight for weight, _ in values)
        result[key[0]].append(
            tuple(
                sum(weight * vector[index] for weight, vector in values) / total
                for index in range(len(CONTRASTS))
            )
        )
    return result


def _estimate(
    vectors: Mapping[str, Sequence[tuple[float, float]]], index: int
) -> tuple[float | None, float | None]:
    if any(not vectors[family] for family in FAMILIES):
        return None, None
    estimates = [mean(row[index] for row in vectors[family]) for family in FAMILIES]
    effect = mean(estimates)
    if any(len(vectors[family]) < 2 for family in FAMILIES):
        return effect, None
    standard_error = math.sqrt(
        sum(
            variance([row[index] for row in vectors[family]]) / len(vectors[family])
            for family in FAMILIES
        )
    ) / len(FAMILIES)
    return effect, standard_error


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = math.floor(position)
    fraction = position - low
    return ordered[low] + fraction * (
        ordered[min(low + 1, len(ordered) - 1)] - ordered[low]
    )


def _bootstrap(
    vectors: Mapping[str, Sequence[tuple[float, float]]], policy: AnalysisPolicy
) -> list[dict[str, Any]]:
    """Joint draw indices preserve both contrasts and every within-cluster pair."""
    observed = [_estimate(vectors, index) for index in range(len(CONTRASTS))]
    output = []
    for index, (name, _, _) in enumerate(CONTRASTS):
        effect, se = observed[index]
        reasons = []
        if any(
            len(vectors[family]) < policy.min_clusters_per_family for family in FAMILIES
        ):
            reasons.append("too_few_independent_clusters")
        if (
            sum(row[index] != 0 for rows in vectors.values() for row in rows)
            < policy.min_discordant_clusters
        ):
            reasons.append("sparse_cluster_discordance")
        if se is None or se <= 0:
            reasons.append("zero_or_unavailable_standard_error")
        output.append(
            {
                "contrast": name,
                "estimate": effect,
                "standard_error": se,
                "status": "degenerate" if reasons else "computed",
                "reasons": reasons,
                "raw_p": None,
                "confidence_interval_95": None,
                "valid_bootstrap_samples": 0,
                "degenerate_bootstrap_samples": 0,
            }
        )
    statistics: list[list[float]] = [[] for _ in CONTRASTS]
    rng = random.Random(policy.seed)
    if any(item["status"] == "computed" for item in output):
        for _ in range(policy.bootstrap_resamples):
            sample = {
                family: [
                    vectors[family][rng.randrange(len(vectors[family]))]
                    for _ in vectors[family]
                ]
                for family in FAMILIES
            }
            for index, item in enumerate(output):
                if item["status"] != "computed":
                    continue
                star, se_star = _estimate(sample, index)
                if se_star is None or se_star <= 0:
                    item["degenerate_bootstrap_samples"] += 1
                    continue
                statistics[index].append((star - item["estimate"]) / se_star)
    for index, item in enumerate(output):
        if item["status"] != "computed":
            continue
        values = statistics[index]
        item["valid_bootstrap_samples"] = len(values)
        if (
            not values
            or item["degenerate_bootstrap_samples"] / policy.bootstrap_resamples
            > policy.max_degenerate_fraction
        ):
            item["status"] = "degenerate"
            item["reasons"].append("excess_degenerate_resamples")
            continue
        observed_t = (item["estimate"] - policy.deltas[item["contrast"]]) / item[
            "standard_error"
        ]
        # Boundary-null centering: bootstrap t uses star - observed estimate.
        item["raw_p"] = (1 + sum(value >= observed_t for value in values)) / (
            len(values) + 1
        )
        q_low, q_high = _quantile(values, 0.025), _quantile(values, 0.975)
        item["confidence_interval_95"] = [
            min(1.0, max(-1.0, item["estimate"] - q_high * item["standard_error"])),
            min(1.0, max(-1.0, item["estimate"] - q_low * item["standard_error"])),
        ]
    return output


def _qualification(
    dataset: JoinedDataset, policy: AnalysisPolicy, x: str, y: str
) -> dict[str, Any]:
    rates = {}
    reasons = []
    if any(row["integrity_status"] == "violation" for row in dataset.rows):
        reasons.append("dataset_integrity_violation_requires_scope_review")
    for method in (x, y):
        rows = [row for row in dataset.rows if row["method_condition"] == method]
        rates[method] = sum(row["value"] is None for row in rows) / len(rows)
        if rates[method] > policy.max_missing_fraction:
            reasons.append("method_missingness_exceeds_policy:" + method)
        if any(row["outcome_class"] == "not_applicable" for row in rows):
            reasons.append("primary_endpoint_not_applicable:" + method)
        if any(row["budget_status"] != "compliant" for row in rows):
            reasons.append("budget_not_verifiably_compliant:" + method)
        if any(row["integrity_status"] != "intact" for row in rows):
            reasons.append("integrity_not_verified:" + method)
    if abs(rates[x] - rates[y]) > policy.max_missing_difference:
        reasons.append("differential_missingness_exceeds_policy")
    return {"eligible": not reasons, "reasons": reasons, "missing_fractions": rates}


def _rates(dataset: JoinedDataset) -> dict[str, Any]:
    output = {}
    for method in METHODS:
        families = {}
        for family in FAMILIES:
            # Average repeats within configuration, then configurations within
            # clusters, then clusters; do not weight large clusters by row count.
            configs: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
            for row in dataset.rows:
                if row["method_condition"] == method and row["family_id"] == family:
                    configs[
                        (row["design_cluster_id"], row["semantic_instance_id"])
                    ].append(row)
            clusters: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
            for (cluster, _), rows in configs.items():
                lower = mean(
                    0 if row["value"] is None else row["value"] for row in rows
                )
                upper = mean(
                    1 if row["value"] is None else row["value"] for row in rows
                )
                clusters[cluster].append(
                    (rows[0]["configuration_weight"], lower, upper)
                )
            bounds = [
                (
                    sum(w * low for w, low, _ in values) / sum(w for w, _, _ in values),
                    sum(w * high for w, _, high in values)
                    / sum(w for w, _, _ in values),
                )
                for values in clusters.values()
            ]
            families[family] = {
                "lower": mean(pair[0] for pair in bounds),
                "upper": mean(pair[1] for pair in bounds),
                "clusters": len(bounds),
            }
        output[method] = {
            "families": families,
            "macro_lower": mean(item["lower"] for item in families.values()),
            "macro_upper": mean(item["upper"] for item in families.values()),
        }
    return output


def analyze(
    manifest: Mapping[str, Any],
    results: Sequence[Mapping[str, Any]],
    policy: AnalysisPolicy | Mapping[str, Any],
) -> dict[str, Any]:
    """Compute both primary contrasts without modifying observations or authority."""
    policy = AnalysisPolicy.from_dict(
        policy.to_dict() if isinstance(policy, AnalysisPolicy) else policy
    )
    dataset = validate_dataset(manifest, results)
    lower = _aggregate(dataset, "lower")
    upper = _aggregate(dataset, "upper")
    complete = _aggregate(dataset, "complete")
    inference = _bootstrap(lower, policy)
    adjusted = holm_adjust([item["raw_p"] for item in inference])
    for index, (_, x, y) in enumerate(CONTRASTS):
        item = inference[index]
        item["methods"] = [x, y]
        item["endpoints"] = [ENDPOINTS[x], ENDPOINTS[y]]
        item["null_boundary"] = policy.deltas[item["contrast"]]
        item["target_effect_for_planning"] = policy.target_effects[item["contrast"]]
        item["holm_adjusted_p"] = adjusted[index]
        item["qualification"] = _qualification(dataset, policy, x, y)
        item["reject_null_numerically"] = (
            (adjusted[index] <= policy.alpha) if adjusted[index] is not None else None
        )
        item["eligible_numerical_decision"] = (
            item["reject_null_numerically"]
            if item["qualification"]["eligible"] and item["status"] == "computed"
            else None
        )
        item["full_denominator_bounds"] = [
            _estimate(lower, index)[0],
            _estimate(upper, index)[0],
        ]
        item["complete_cluster_sensitivity"] = {
            "estimate": _estimate(complete, index)[0],
            "clusters_per_family": {
                family: len(complete[family]) for family in FAMILIES
            },
            "role": "sensitivity_only_not_the_primary_denominator",
        }
        item["family_estimates_lower"] = {
            family: mean(row[index] for row in lower[family]) for family in FAMILIES
        }
    return {
        "contract_version": "pc21-cluster-analysis-v1",
        "analysis_scope": "offline_development_analysis",
        "official": False,
        "claim_authorized": False,
        "model_calls": 0,
        "dataset": dataset.summary(),
        "policy": policy.to_dict(),
        "policy_sha256": canonical_sha256(policy.to_dict()),
        "weighting": "replicate_mean_then_configuration_weight_then_cluster_mean_then_equal_family_mean",
        "resampling_unit": "complete_independent_design_cluster_with_joint_contrast_vector",
        "dependency_policy": "shared_groups_across_clusters_rejected",
        "confidence_interval_scope": "marginal_two_sided_95_percent_not_simultaneous",
        "missingness_primary": "comparison_direction_conservative_bounds_without_rewriting_null_observations",
        "method_rate_bounds": _rates(dataset),
        "contrasts": inference,
        "joint_eligible_numerical_rejection": (
            all(item["eligible_numerical_decision"] is True for item in inference)
            if all(
                item["eligible_numerical_decision"] is not None for item in inference
            )
            else None
        ),
    }
