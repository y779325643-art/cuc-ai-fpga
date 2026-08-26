"""Closed Paper-1 method vocabulary; adapters are introduced in CD4."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum


class MethodConditionId(str, Enum):
    M0 = "M0"
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"


class PlanningRepresentation(str, Enum):
    NONE = "none"
    UNTYPED_PLAN = "untyped_plan"
    SYSTEM_HIS = "system_his"


class ProjectGenerationKind(str, Enum):
    DIRECT = "direct"
    FREE_FROM_PLAN = "free_from_plan"
    FREE_FROM_HIS = "free_from_his"
    SKELETON_FILL = "skeleton_fill"


class ModelStageId(str, Enum):
    DIRECT_PROJECT = "direct_project"
    UNTYPED_PLAN = "untyped_plan"
    PROJECT_FROM_PLAN = "project_from_plan"
    REQ2HIS = "req2his"
    PROJECT_FROM_HIS = "project_from_his"
    HIS_CORRECTION = "his_correction"
    PROJECT_REPAIR = "project_repair"


class HStageApplicability(str, Enum):
    REQUIRED = "required"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class MethodContract:
    method_condition: MethodConditionId
    declared_model_stages: tuple[ModelStageId, ...]
    planning_representation: PlanningRepresentation
    project_generation_kind: ProjectGenerationKind
    emits_system_his: bool
    h_stage_applicability: HStageApplicability
    uses_deterministic_skeleton: bool
    allows_his_correction: bool
    allows_project_repair: bool
    model_visible_field_ids: tuple[str, ...]
    allowed_edit_surface_id: str
    budget_allocation_id: str

    def __post_init__(self) -> None:
        if self.emits_system_his != (
            self.planning_representation is PlanningRepresentation.SYSTEM_HIS
        ):
            raise ValueError("System-HIS applicability must match planning representation")
        expected_h = (
            HStageApplicability.REQUIRED
            if self.emits_system_his
            else HStageApplicability.NOT_APPLICABLE
        )
        if self.h_stage_applicability is not expected_h:
            raise ValueError("H-stage applicability must match System-HIS emission")
        if self.uses_deterministic_skeleton != (
            self.project_generation_kind is ProjectGenerationKind.SKELETON_FILL
        ):
            raise ValueError("skeleton flag must match project generation kind")
        if self.allows_his_correction and not self.emits_system_his:
            raise ValueError("HIS correction requires a System-HIS method")
        if not self.model_visible_field_ids:
            raise ValueError("method contract requires a non-empty visibility allowlist")


COMMON_PUBLIC_FIELDS = (
    "requirement_id",
    "revision_id",
    "public_text",
    "fact_records",
    "platform_profile_id",
    "platform_profile_sha256",
    "capability_profile_id",
    "capability_profile_sha256",
    "disposition",
    "public_projection_sha256",
)


METHOD_CONTRACTS = {
    MethodConditionId.M0: MethodContract(
        MethodConditionId.M0,
        (ModelStageId.DIRECT_PROJECT,),
        PlanningRepresentation.NONE,
        ProjectGenerationKind.DIRECT,
        False,
        HStageApplicability.NOT_APPLICABLE,
        False,
        False,
        False,
        COMMON_PUBLIC_FIELDS,
        "direct-project-v1",
        "paper1-at1-v1",
    ),
    MethodConditionId.M1: MethodContract(
        MethodConditionId.M1,
        (ModelStageId.DIRECT_PROJECT, ModelStageId.PROJECT_REPAIR),
        PlanningRepresentation.NONE,
        ProjectGenerationKind.DIRECT,
        False,
        HStageApplicability.NOT_APPLICABLE,
        False,
        False,
        True,
        COMMON_PUBLIC_FIELDS,
        "direct-project-repair-v1",
        "paper1-online-repair-v1",
    ),
    MethodConditionId.M2: MethodContract(
        MethodConditionId.M2,
        (ModelStageId.UNTYPED_PLAN, ModelStageId.PROJECT_FROM_PLAN),
        PlanningRepresentation.UNTYPED_PLAN,
        ProjectGenerationKind.FREE_FROM_PLAN,
        False,
        HStageApplicability.NOT_APPLICABLE,
        False,
        False,
        False,
        COMMON_PUBLIC_FIELDS,
        "free-project-v1",
        "paper1-two-stage-v1",
    ),
    MethodConditionId.M3: MethodContract(
        MethodConditionId.M3,
        (ModelStageId.REQ2HIS, ModelStageId.PROJECT_FROM_HIS),
        PlanningRepresentation.SYSTEM_HIS,
        ProjectGenerationKind.FREE_FROM_HIS,
        True,
        HStageApplicability.REQUIRED,
        False,
        False,
        False,
        COMMON_PUBLIC_FIELDS,
        "free-project-v1",
        "paper1-two-stage-v1",
    ),
    MethodConditionId.M4: MethodContract(
        MethodConditionId.M4,
        (ModelStageId.REQ2HIS, ModelStageId.PROJECT_FROM_HIS),
        PlanningRepresentation.SYSTEM_HIS,
        ProjectGenerationKind.SKELETON_FILL,
        True,
        HStageApplicability.REQUIRED,
        True,
        False,
        False,
        COMMON_PUBLIC_FIELDS,
        "skeleton-behavior-v1",
        "paper1-two-stage-v1",
    ),
    MethodConditionId.M5: MethodContract(
        MethodConditionId.M5,
        (
            ModelStageId.REQ2HIS,
            ModelStageId.PROJECT_FROM_HIS,
            ModelStageId.HIS_CORRECTION,
            ModelStageId.PROJECT_REPAIR,
        ),
        PlanningRepresentation.SYSTEM_HIS,
        ProjectGenerationKind.SKELETON_FILL,
        True,
        HStageApplicability.REQUIRED,
        True,
        True,
        True,
        COMMON_PUBLIC_FIELDS,
        "skeleton-behavior-repair-v1",
        "paper1-online-repair-v1",
    ),
}


def method_contract(condition: MethodConditionId | str) -> MethodContract:
    try:
        key = condition if isinstance(condition, MethodConditionId) else MethodConditionId(condition)
    except ValueError as exc:
        raise KeyError(f"unknown method condition: {condition!r}") from exc
    return METHOD_CONTRACTS[key]


def method_policy_sha256(condition: MethodConditionId | str) -> str:
    """Return the canonical digest of one registered method policy."""

    contract = method_contract(condition)
    payload = {
        "method_condition": contract.method_condition.value,
        "declared_model_stages": [stage.value for stage in contract.declared_model_stages],
        "planning_representation": contract.planning_representation.value,
        "project_generation_kind": contract.project_generation_kind.value,
        "emits_system_his": contract.emits_system_his,
        "h_stage_applicability": contract.h_stage_applicability.value,
        "uses_deterministic_skeleton": contract.uses_deterministic_skeleton,
        "allows_his_correction": contract.allows_his_correction,
        "allows_project_repair": contract.allows_project_repair,
        "model_visible_field_ids": list(contract.model_visible_field_ids),
        "allowed_edit_surface_id": contract.allowed_edit_surface_id,
        "budget_allocation_id": contract.budget_allocation_id,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
