"""Registered B4 model-call allocations from `paper1-v2.1` section 6.4.

`paper1-v2.1` replaced the v1.7/v1.8 notion of budget fairness. The old rule gave
the repair methods a matched *repair count*; B4 instead gives every independent
method the same ceiling on **logical model calls**, so that M1 may legitimately
spend its remainder on re-generation rather than only on patches. Section 6.4
states the call ceilings; it deliberately leaves the token, tool-subcall,
runtime, and EDA-time ceilings to be measured in the development sandbox and
locked before the exclusionary pilot.

This module registers only what the plan actually fixes. The unresolved axes are
represented as `None` and reported by :attr:`BudgetAllocation.unresolved_axes`,
so an allocation cannot silently look complete. Appendix A of the plan requires
that such placeholders never appear in an approved official configuration;
:attr:`BudgetAllocation.is_freeze_ready` is the corresponding check.

Registering an allocation proves a budget policy exists. It never proves a run
respected it, and it grants no implementation or experiment authorization.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from sr2fpga_agent.method_contract import MethodConditionId, method_contract

#: Identifier of the budget policy these allocations implement.
BUDGET_POLICY_ID = "paper1-b4-v1"

#: Total logical model calls allowed to one independent method under B4.
B4_TOTAL_MODEL_CALLS = 4

#: Cost axes the plan requires but does not fix numerically in section 6.4.
UNRESOLVED_AXIS_NAMES = (
    "max_total_input_tokens",
    "max_total_output_tokens",
    "max_single_output_tokens",
    "max_public_tool_calls",
    "max_active_runtime_seconds",
    "max_eda_seconds",
)


class BudgetAllocationError(KeyError):
    """No registered B4 allocation exists for the requested method condition."""


@dataclass(frozen=True)
class BudgetAllocation:
    """One method condition's B4 allocation.

    `initial_stage_calls` is the plan's `@initial` terminal: one call per
    declared model stage. `remaining_calls` is what the method may still spend
    on repair, PC correction, or re-generation. Their sum is the standalone
    ceiling that budget enforcement must use.
    """

    allocation_id: str
    method_condition: MethodConditionId
    initial_stage_calls: int
    remaining_calls: int
    allows_repair: bool
    max_total_input_tokens: int | None = None
    max_total_output_tokens: int | None = None
    max_single_output_tokens: int | None = None
    max_public_tool_calls: int | None = None
    max_active_runtime_seconds: float | None = None
    max_eda_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.initial_stage_calls < 0 or self.remaining_calls < 0:
            raise ValueError("B4 allocations must be non-negative")
        if self.standalone_max_model_calls > B4_TOTAL_MODEL_CALLS:
            raise ValueError(
                f"{self.method_condition.value} exceeds the B4 ceiling of "
                f"{B4_TOTAL_MODEL_CALLS} logical model calls"
            )
        if self.allows_repair != (self.remaining_calls > 0):
            raise ValueError(
                "repair permission must match the presence of remaining calls"
            )
        contract = method_contract(self.method_condition)
        if self.initial_stage_calls != len(_initial_stages(contract)):
            raise ValueError(
                f"{self.method_condition.value} initial-stage calls must equal its "
                "declared non-repair model stages"
            )
        if self.allows_repair and not (
            contract.allows_project_repair or contract.allows_his_correction
        ):
            raise ValueError(
                f"{self.method_condition.value} has remaining calls but its method "
                "contract permits neither repair nor PC correction"
            )

    @property
    def standalone_max_model_calls(self) -> int:
        """The ceiling budget enforcement must apply to an independent run."""

        return self.initial_stage_calls + self.remaining_calls

    @property
    def unresolved_axes(self) -> tuple[str, ...]:
        """Axes the plan requires but that are not yet locked."""

        return tuple(name for name in UNRESOLVED_AXIS_NAMES if getattr(self, name) is None)

    @property
    def is_freeze_ready(self) -> bool:
        """Whether this allocation may enter an approved official configuration."""

        return not self.unresolved_axes

    def to_dict(self) -> dict:
        payload = {
            "budget_policy_id": BUDGET_POLICY_ID,
            "allocation_id": self.allocation_id,
            "method_condition": self.method_condition.value,
            "initial_stage_calls": self.initial_stage_calls,
            "remaining_calls": self.remaining_calls,
            "standalone_max_model_calls": self.standalone_max_model_calls,
            "allows_repair": self.allows_repair,
            "unresolved_axes": list(self.unresolved_axes),
            "freeze_ready": self.is_freeze_ready,
        }
        for name in UNRESOLVED_AXIS_NAMES:
            payload[name] = getattr(self, name)
        return payload


def _initial_stages(contract) -> tuple:
    """Declared model stages that belong to the `@initial` terminal."""

    from sr2fpga_agent.method_contract import ModelStageId

    repair_stages = {ModelStageId.PROJECT_REPAIR, ModelStageId.HIS_CORRECTION}
    return tuple(
        stage for stage in contract.declared_model_stages if stage not in repair_stages
    )


# Plan section 6.4. M1 spends one Direct generation and keeps three; M5 spends
# one PC-planning call and one behaviour-generation call and keeps two. M0 uses
# a single call. M2/M3/M4 use one call per declared stage with no outer repair.
B4_ALLOCATIONS: dict[MethodConditionId, BudgetAllocation] = {
    MethodConditionId.M0: BudgetAllocation(
        "paper1-b4-initial-only-v1", MethodConditionId.M0, 1, 0, False
    ),
    MethodConditionId.M1: BudgetAllocation(
        "paper1-b4-repair-v1", MethodConditionId.M1, 1, 3, True
    ),
    MethodConditionId.M2: BudgetAllocation(
        "paper1-b4-two-stage-v1", MethodConditionId.M2, 2, 0, False
    ),
    MethodConditionId.M3: BudgetAllocation(
        "paper1-b4-two-stage-v1", MethodConditionId.M3, 2, 0, False
    ),
    MethodConditionId.M4: BudgetAllocation(
        "paper1-b4-two-stage-v1", MethodConditionId.M4, 2, 0, False
    ),
    MethodConditionId.M5: BudgetAllocation(
        "paper1-b4-repair-v1", MethodConditionId.M5, 2, 2, True
    ),
}


def budget_allocation(condition: MethodConditionId | str) -> BudgetAllocation:
    """Return the registered B4 allocation for one method condition."""

    try:
        key = (
            condition
            if isinstance(condition, MethodConditionId)
            else MethodConditionId(condition)
        )
    except ValueError as exc:
        raise BudgetAllocationError(f"unknown method condition: {condition!r}") from exc
    try:
        return B4_ALLOCATIONS[key]
    except KeyError as exc:  # pragma: no cover - every condition is registered
        raise BudgetAllocationError(
            f"no registered B4 allocation for {key.value}"
        ) from exc


def assert_b4_conformant(condition: MethodConditionId | str, standalone_ceiling: int) -> None:
    """Raise unless a configured standalone ceiling matches its B4 allocation.

    Enforcement is exact, not an upper bound: a method configured below its
    allocation is not running B4 either, and silently accepting it would make
    `M5-M1@B4` compare two different budgets.
    """

    allocation = budget_allocation(condition)
    expected = allocation.standalone_max_model_calls
    if standalone_ceiling != expected:
        raise ValueError(
            f"{allocation.method_condition.value} standalone model-call ceiling "
            f"{standalone_ceiling} does not match its B4 allocation {expected}"
        )


def budget_policy_sha256() -> str:
    """Canonical digest of the whole registered B4 policy."""

    payload = {
        "budget_policy_id": BUDGET_POLICY_ID,
        "b4_total_model_calls": B4_TOTAL_MODEL_CALLS,
        "allocations": [
            B4_ALLOCATIONS[condition].to_dict() for condition in MethodConditionId
        ],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
