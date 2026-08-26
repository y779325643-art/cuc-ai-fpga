"""Exact, auditable selection of optional task-family prompt recipes.

The selector never asks a model to classify a request and never chooses a
nearest family.  It accepts only registered identifiers or whole-phrase
triggers, reconciles them with the catalog/runtime ownership tables, and
fails closed on ambiguity or the candidate Paper-1 held-out deny policy.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Iterable

from sr2fpga_agent.models import ProjectRequest
from sr2fpga_agent.requirement_envelope import RequirementEnvelope
from sr2fpga_agent.task_catalog import (
    FamilyRecipeDenyPolicy,
    load_exact_task_family_aliases,
    load_family_recipe_deny_policy,
    load_task_family_specs,
    resolve_exact_task_family,
)
from sr2fpga_agent.task_families import SUPPORTED_TASK_TYPES, family_id_for_task_type


@dataclass(frozen=True)
class FamilyRecipeSpec:
    """One versioned architecture recipe and its exact recognition surface."""

    recipe_id: str
    version: str
    task_type: str
    family_id: str
    identifiers: tuple[str, ...]
    phrases: tuple[str, ...]


@dataclass(frozen=True)
class FamilyRecipeDecision:
    """JSON-safe result of applying the automatic recipe policy."""

    recipe_id: str | None
    version: str | None
    sha256: str | None
    family_id: str | None
    matched_alias: str | None
    status: str
    reason: str
    policy_id: str
    policy_version: str
    policy_sha256: str
    policy_status: str
    catalog_version: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_RECIPE_VERSION = "1.0.0"


def _spec(
    task_type: str,
    *identifiers: str,
    phrases: tuple[str, ...] = (),
) -> FamilyRecipeSpec:
    family_id = family_id_for_task_type(task_type)
    return FamilyRecipeSpec(
        recipe_id=f"sr2fpga-family-recipe:{task_type}",
        version=_RECIPE_VERSION,
        task_type=task_type,
        family_id=family_id,
        identifiers=tuple(dict.fromkeys((task_type, *identifiers))),
        phrases=tuple(dict.fromkeys(phrases)),
    )


_RECIPES = (
    _spec(
        "alu_control_unit",
        phrases=("alu control unit",),
    ),
    _spec(
        "crc_stream_checker",
        phrases=("crc stream checker", "streaming crc checker"),
    ),
    _spec(
        "composed_event_counter",
        "t1_event_counter",
        phrases=("event counter topology", "event counter"),
    ),
    _spec(
        "composed_stream_accumulator",
        "t2_stream_accumulator",
        phrases=(
            "stream accumulator",
            "valid ready stream accumulator",
            "valid-ready 流式累加器",
            "流式累加器",
        ),
    ),
    _spec(
        "composed_stream_fork",
        "t3_stream_fork",
        phrases=("stream fork", "数据流分叉"),
    ),
    _spec(
        "composed_dual_stream_join",
        "t4_dual_stream_join",
        phrases=("dual stream join", "双流汇合"),
    ),
    _spec(
        "composed_vector_mac_pipeline",
        "t5_vector_mac_pipeline",
        phrases=("vector mac pipeline", "乘加阵列 mac"),
    ),
    _spec(
        "composed_td_update_core",
        "t6_td_update_core",
        phrases=("td update core", "q table update core", "q-table 更新核心"),
    ),
    _spec(
        "composed_policy_value_shell",
        "t7_policy_value_shell",
        phrases=("policy value shell", "奖励计算与策略更新模块"),
    ),
    _spec(
        "composed_replay_sample_shell",
        "t8_replay_sample_shell",
        phrases=("replay sample shell",),
    ),
    _spec(
        "composed_host_protocol_shell",
        "t9_host_protocol_shell",
        phrases=("host protocol shell",),
    ),
    _spec(
        "composed_rl_accelerator_shell",
        "t10_rl_accelerator_shell",
        phrases=("integrated rl accelerator shell",),
    ),
    _spec(
        "composed_batch_rl_accelerator_shell",
        "t11_batch_rl_accelerator_shell",
        phrases=("batch rl accelerator shell", "two lane batch rl accelerator shell"),
    ),
    _spec(
        "composed_replay_arbiter_shell",
        "t12_replay_arbiter_shell",
        phrases=("replay arbiter shell",),
    ),
)


def family_recipe_specs() -> tuple[FamilyRecipeSpec, ...]:
    """Return the frozen recipe registry after checking catalog ownership."""

    catalog_family_ids = {spec.family_id for spec in load_task_family_specs()}
    catalog_aliases = load_exact_task_family_aliases()
    for recipe in _RECIPES:
        if recipe.family_id not in catalog_family_ids:
            raise ValueError(
                f"family recipe {recipe.recipe_id} references unknown family {recipe.family_id}"
            )
        runtime_family_id = family_id_for_task_type(recipe.task_type)
        if runtime_family_id != recipe.family_id:
            raise ValueError(
                f"family recipe {recipe.recipe_id} ownership mismatch: "
                f"{recipe.family_id} != {runtime_family_id}"
            )
        for identifier in recipe.identifiers:
            resolution = resolve_exact_task_family(
                identifier,
                exact_catalog_aliases=catalog_aliases,
            )
            if resolution.status != "exact" or resolution.family_id != recipe.family_id:
                raise ValueError(
                    f"family recipe {recipe.recipe_id} identifier {identifier!r} "
                    "does not have one matching exact family owner"
                )
    return _RECIPES


def select_family_recipe(
    request: ProjectRequest,
    envelope: RequirementEnvelope,
    *,
    deny_policy: FamilyRecipeDenyPolicy | None = None,
) -> FamilyRecipeDecision:
    """Select one exact recipe or return an auditable generic fallback."""

    policy = deny_policy if deny_policy is not None else load_family_recipe_deny_policy()
    recipes = family_recipe_specs()
    identifier_owners = _recipe_identifier_owners(recipes)
    catalog_aliases = load_exact_task_family_aliases()

    declared = request.task_type.strip()
    declared_normalized = _normalize(declared)
    declared_resolution = (
        resolve_exact_task_family(
            declared_normalized,
            exact_catalog_aliases=catalog_aliases,
        )
        if declared_normalized
        else None
    )
    if declared_resolution is not None and declared_resolution.status == "conflict":
        return _decision(
            policy,
            status="not_applied",
            reason="conflicting_exact_owners",
            matched_alias=declared,
        )

    recipe_matches: dict[str, tuple[FamilyRecipeSpec, str, int]] = {}
    family_matches: dict[str, list[str]] = {}

    declared_recipe = identifier_owners.get(declared_normalized)
    if declared_recipe is not None:
        recipe_matches[declared_recipe.recipe_id] = (declared_recipe, declared, 0)
    if declared_resolution is not None and declared_resolution.status == "exact":
        _add_family_match(family_matches, declared_resolution.family_id, declared)

    text = envelope.raw_requirement
    normalized_text = _normalize(text)
    matched_recipe_phrases: list[str] = []
    for recipe in recipes:
        for phrase in (*recipe.identifiers, *recipe.phrases):
            normalized_phrase = _normalize(phrase)
            if not normalized_phrase or not _contains_phrase(normalized_text, normalized_phrase):
                continue
            matched_recipe_phrases.append(normalized_phrase)
            current = recipe_matches.get(recipe.recipe_id)
            candidate = (recipe, phrase, 1)
            if current is None or (candidate[2], -len(normalized_phrase), phrase) < (
                current[2],
                -len(_normalize(current[1])),
                current[1],
            ):
                recipe_matches[recipe.recipe_id] = candidate
            _add_family_match(family_matches, recipe.family_id, phrase)

    for alias in _all_exact_family_aliases(catalog_aliases):
        normalized_alias = _normalize(alias)
        if not normalized_alias or not _contains_phrase(normalized_text, normalized_alias):
            continue
        if any(
            normalized_alias != recipe_phrase
            and _contains_phrase(recipe_phrase, normalized_alias)
            for recipe_phrase in matched_recipe_phrases
        ):
            continue
        resolution = resolve_exact_task_family(
            alias,
            exact_catalog_aliases=catalog_aliases,
        )
        if resolution.status == "conflict":
            return _decision(
                policy,
                status="not_applied",
                reason="conflicting_exact_owners",
                matched_alias=alias,
            )
        if resolution.status == "exact":
            _add_family_match(family_matches, resolution.family_id, alias)

    matched_families = tuple(sorted(family_matches))
    if len(matched_families) > 1:
        return _decision(
            policy,
            status="not_applied",
            reason="conflicting_exact_matches",
            matched_alias=_joined_aliases(family_matches),
        )
    if len(recipe_matches) > 1:
        return _decision(
            policy,
            status="not_applied",
            reason="multiple_recipe_matches",
            family_id=matched_families[0] if matched_families else None,
            matched_alias=",".join(
                sorted(match[1] for match in recipe_matches.values())
            ),
        )

    family_id = matched_families[0] if matched_families else None
    if not recipe_matches:
        return _decision(
            policy,
            status="not_applied",
            reason="no_registered_recipe" if family_id else "no_exact_match",
            family_id=family_id,
            matched_alias=_joined_aliases(family_matches) if family_id else None,
        )

    recipe, matched_alias, _priority = next(iter(recipe_matches.values()))
    if family_id is not None and recipe.family_id != family_id:
        return _decision(
            policy,
            status="not_applied",
            reason="conflicting_exact_matches",
            matched_alias=matched_alias,
        )
    if recipe.family_id in policy.family_ids:
        return _decision(
            policy,
            recipe=recipe,
            status="not_applied",
            reason=policy.deny_reason,
            family_id=recipe.family_id,
            matched_alias=matched_alias,
        )
    return _decision(
        policy,
        recipe=recipe,
        status="applied",
        reason="unique_exact_match",
        family_id=recipe.family_id,
        matched_alias=matched_alias,
    )


def _decision(
    policy: FamilyRecipeDenyPolicy,
    *,
    recipe: FamilyRecipeSpec | None = None,
    status: str,
    reason: str,
    family_id: str | None = None,
    matched_alias: str | None = None,
) -> FamilyRecipeDecision:
    return FamilyRecipeDecision(
        recipe_id=recipe.recipe_id if recipe else None,
        version=recipe.version if recipe else None,
        sha256=_recipe_sha256(recipe) if recipe else None,
        family_id=family_id,
        matched_alias=matched_alias,
        status=status,
        reason=reason,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        policy_sha256=policy.policy_sha256,
        policy_status=policy.status,
        catalog_version=policy.catalog_version,
    )


def recipe_task_type(decision: FamilyRecipeDecision) -> str | None:
    """Return the registered recipe task type only for an applied decision."""

    if decision.status != "applied" or not decision.recipe_id:
        return None
    for recipe in family_recipe_specs():
        if recipe.recipe_id == decision.recipe_id:
            return recipe.task_type
    raise ValueError(f"unknown applied family recipe id: {decision.recipe_id}")


def _recipe_identifier_owners(
    recipes: Iterable[FamilyRecipeSpec],
) -> dict[str, FamilyRecipeSpec]:
    owners: dict[str, FamilyRecipeSpec] = {}
    for recipe in recipes:
        for identifier in recipe.identifiers:
            normalized = _normalize(identifier)
            previous = owners.get(normalized)
            if previous is not None and previous.recipe_id != recipe.recipe_id:
                raise ValueError(f"duplicate family recipe identifier: {identifier}")
            owners[normalized] = recipe
    return owners


def _all_exact_family_aliases(catalog_aliases: dict[str, str]) -> tuple[str, ...]:
    aliases = set(catalog_aliases)
    aliases.update(SUPPORTED_TASK_TYPES)
    return tuple(sorted(aliases, key=lambda item: (-len(_normalize(item)), item)))


def _add_family_match(
    matches: dict[str, list[str]],
    family_id: str | None,
    alias: str,
) -> None:
    if family_id is None:
        return
    matches.setdefault(family_id, [])
    if alias not in matches[family_id]:
        matches[family_id].append(alias)


def _joined_aliases(matches: dict[str, list[str]]) -> str:
    return ",".join(sorted({alias for aliases in matches.values() for alias in aliases}))


def _contains_phrase(normalized_text: str, normalized_phrase: str) -> bool:
    if not normalized_text or not normalized_phrase:
        return False
    if any("\u4e00" <= character <= "\u9fff" for character in normalized_phrase):
        return normalized_phrase in normalized_text
    return f"_{normalized_phrase}_" in f"_{normalized_text}_"


def _normalize(value: str) -> str:
    return re.sub(r"[^\w]+", "_", value.strip().casefold(), flags=re.UNICODE).strip("_")


def _recipe_sha256(recipe: FamilyRecipeSpec) -> str:
    # Imported lazily to keep prompt construction and recipe selection acyclic.
    from sr2fpga_agent.prompts import (
        _system_his_v12_retry_guidance,
        _system_his_v12_task_guidance,
    )

    payload = {
        "recipe_id": recipe.recipe_id,
        "version": recipe.version,
        "task_type": recipe.task_type,
        "family_id": recipe.family_id,
        "identifiers": list(recipe.identifiers),
        "phrases": list(recipe.phrases),
        "initial_guidance": _system_his_v12_task_guidance(recipe.task_type),
        "retry_guidance": _system_his_v12_retry_guidance(recipe.task_type),
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
