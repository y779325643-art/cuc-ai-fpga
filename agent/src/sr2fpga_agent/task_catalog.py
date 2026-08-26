"""Runtime access to the authoritative SR2FPGA task-family catalog."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

from .repository_paths import RepositoryPaths
from .task_families import SUPPORTED_TASK_TYPES, family_id_for_task_type


CATALOG_PATH = RepositoryPaths.discover().task_catalog


@dataclass(frozen=True)
class TaskFamilySpec:
    """Immutable runtime fields for one catalog task family."""

    family_id: str
    sr2fpga_tier: str
    system_his_profile: str
    skeleton_level: str
    oracle_kind: tuple[str, ...]
    mutation_suite: tuple[str, ...]
    mutation_score_threshold: float
    benchmark_role: str
    l4_open_policy: str
    l4_commercial_policy: str
    current_generator_aliases: tuple[str, ...]


@dataclass(frozen=True)
class FamilyRecipeDenyPolicy:
    """Immutable catalog-backed policy that prevents held-out recipe leakage."""

    policy_id: str
    policy_version: str
    policy_sha256: str
    catalog_version: str
    status: str
    recommended_set: str
    family_ids: tuple[str, ...]
    deny_reason: str


@dataclass(frozen=True)
class ExactTaskFamilyResolution:
    """Result of reconciling catalog aliases with exact runtime task names."""

    status: str
    declared_alias: str
    family_id: str | None
    catalog_family_id: str | None
    runtime_family_id: str | None
    reason: str


def load_task_family_specs() -> tuple[TaskFamilySpec, ...]:
    """Load catalog family specs and reject aliases owned by multiple families."""
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        catalog = json.load(handle)

    specs = tuple(
        TaskFamilySpec(
            family_id=family["family_id"],
            sr2fpga_tier=family["sr2fpga_tier"],
            system_his_profile=family["system_his_profile"],
            skeleton_level=family["skeleton_level"],
            oracle_kind=tuple(family["oracle_kind"]),
            mutation_suite=tuple(family["mutation_suite"]),
            mutation_score_threshold=float(family["mutation_score_threshold"]),
            benchmark_role=family["benchmark_role"],
            l4_open_policy=family["target_l_level"]["l4_open_policy"],
            l4_commercial_policy=family["target_l_level"]["l4_commercial_policy"],
            current_generator_aliases=tuple(family.get("current_generator_aliases", [])),
        )
        for family in catalog["task_families"]
    )
    alias_owners: dict[str, str] = {}
    for spec in specs:
        for alias in spec.current_generator_aliases:
            if alias in alias_owners:
                raise ValueError(f"duplicate task catalog alias: {alias}")
            alias_owners[alias] = spec.family_id
    return specs


def task_family_spec_for_alias(alias: str) -> TaskFamilySpec:
    """Return the catalog family spec that uniquely owns ``alias``."""
    for spec in load_task_family_specs():
        if alias in spec.current_generator_aliases:
            return spec
    raise KeyError(f"unknown task catalog alias: {alias}")


def task_family_spec_for_family_id(family_id: str) -> TaskFamilySpec:
    """Return the unique catalog contract for ``family_id``."""
    for spec in load_task_family_specs():
        if spec.family_id == family_id:
            return spec
    raise KeyError(f"unknown task catalog family_id: {family_id}")


def load_exact_task_family_aliases() -> dict[str, str]:
    """Map each family id and declared generator alias to its owning family."""

    exact_aliases: dict[str, str] = {}
    for spec in load_task_family_specs():
        for alias in (spec.family_id, *spec.current_generator_aliases):
            owner = exact_aliases.get(alias)
            if owner is not None and owner != spec.family_id:
                raise ValueError(f"duplicate exact task-family alias: {alias}")
            exact_aliases[alias] = spec.family_id
    return exact_aliases


def resolve_exact_task_family(
    alias: str,
    *,
    exact_catalog_aliases: Mapping[str, str] | None = None,
) -> ExactTaskFamilyResolution:
    """Resolve one exact identifier without fuzzy or nearest-family matching.

    The catalog owns public family IDs and declared generator aliases, while
    the deterministic runtime also has exact internal task names such as
    ``composed_stream_accumulator``. Both authorities must agree when both
    recognize an identifier; a disagreement is returned as a conflict so a
    caller can fall back to generic guidance instead of choosing silently.
    """

    declared_alias = alias if isinstance(alias, str) else ""
    if not declared_alias or declared_alias != declared_alias.strip():
        return ExactTaskFamilyResolution(
            status="unknown",
            declared_alias=declared_alias,
            family_id=None,
            catalog_family_id=None,
            runtime_family_id=None,
            reason="unknown_alias",
        )

    catalog_family_id = (
        exact_catalog_aliases
        if exact_catalog_aliases is not None
        else load_exact_task_family_aliases()
    ).get(declared_alias)
    runtime_family_id = (
        family_id_for_task_type(declared_alias)
        if declared_alias in SUPPORTED_TASK_TYPES
        else None
    )
    if (
        catalog_family_id is not None
        and runtime_family_id is not None
        and catalog_family_id != runtime_family_id
    ):
        return ExactTaskFamilyResolution(
            status="conflict",
            declared_alias=declared_alias,
            family_id=None,
            catalog_family_id=catalog_family_id,
            runtime_family_id=runtime_family_id,
            reason="conflicting_exact_owners",
        )

    family_id = catalog_family_id or runtime_family_id
    if family_id is None:
        return ExactTaskFamilyResolution(
            status="unknown",
            declared_alias=declared_alias,
            family_id=None,
            catalog_family_id=None,
            runtime_family_id=None,
            reason="unknown_alias",
        )
    return ExactTaskFamilyResolution(
        status="exact",
        declared_alias=declared_alias,
        family_id=family_id,
        catalog_family_id=catalog_family_id,
        runtime_family_id=runtime_family_id,
        reason=(
            "exact_catalog_and_runtime"
            if catalog_family_id is not None and runtime_family_id is not None
            else "exact_catalog_alias"
            if catalog_family_id is not None
            else "exact_runtime_task_type"
        ),
    )


def load_family_recipe_deny_policy() -> FamilyRecipeDenyPolicy:
    """Load the candidate Paper-1 held-out recipe deny policy fail-closed.

    The registered set is deliberately labelled as a candidate G4a boundary,
    not a signed G4b split. Recipe selection may conservatively deny these
    families, but callers must not report the set as a frozen campaign split.
    """

    with CATALOG_PATH.open(encoding="utf-8") as handle:
        catalog = json.load(handle)

    try:
        raw_policy = catalog["global_policies"]["family_recipe_selection"]
        recommended_set = raw_policy["deny_recommended_set"]
        raw_family_ids = catalog["recommended_sets"][recommended_set]
    except (KeyError, TypeError) as exc:
        raise ValueError("task catalog family-recipe deny policy is incomplete") from exc

    if not isinstance(raw_policy, dict):
        raise ValueError("task catalog family-recipe deny policy must be an object")
    if not isinstance(raw_family_ids, list) or not raw_family_ids:
        raise ValueError("task catalog family-recipe deny set must be a non-empty list")

    family_ids = tuple(raw_family_ids)
    if any(
        not isinstance(family_id, str)
        or not family_id
        or family_id != family_id.strip()
        for family_id in family_ids
    ):
        raise ValueError("task catalog family-recipe deny set requires canonical family-id strings")
    if len(family_ids) != len(set(family_ids)):
        raise ValueError("task catalog family-recipe deny set contains duplicate family ids")

    catalog_family_ids = {
        family.get("family_id")
        for family in catalog.get("task_families", [])
        if isinstance(family, dict)
    }
    unknown_family_ids = sorted(set(family_ids).difference(catalog_family_ids))
    if unknown_family_ids:
        raise ValueError(
            "task catalog family-recipe deny set contains non-canonical family ids: "
            + ", ".join(unknown_family_ids)
        )

    string_fields = {
        "policy_id": raw_policy.get("policy_id"),
        "policy_version": raw_policy.get("policy_version"),
        "status": raw_policy.get("status"),
        "deny_reason": raw_policy.get("deny_reason"),
        "catalog_version": catalog.get("catalog_version"),
        "recommended_set": recommended_set,
    }
    invalid_fields = sorted(
        key
        for key, value in string_fields.items()
        if not isinstance(value, str) or not value or value != value.strip()
    )
    if invalid_fields:
        raise ValueError(
            "task catalog family-recipe deny policy has invalid fields: "
            + ", ".join(invalid_fields)
        )

    hash_payload = {
        **string_fields,
        "family_ids": list(family_ids),
    }
    policy_sha256 = hashlib.sha256(
        json.dumps(
            hash_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return FamilyRecipeDenyPolicy(
        policy_id=string_fields["policy_id"],
        policy_version=string_fields["policy_version"],
        policy_sha256=policy_sha256,
        catalog_version=string_fields["catalog_version"],
        status=string_fields["status"],
        recommended_set=string_fields["recommended_set"],
        family_ids=family_ids,
        deny_reason=string_fields["deny_reason"],
    )
