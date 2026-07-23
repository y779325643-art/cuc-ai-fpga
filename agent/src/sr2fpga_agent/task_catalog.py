"""Runtime access to the authoritative SR2FPGA task-family catalog."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .repository_paths import RepositoryPaths


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
