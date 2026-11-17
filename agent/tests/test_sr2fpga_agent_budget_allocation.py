"""Registered B4 allocations must match `paper1-v2.1` section 6.4 exactly."""

from __future__ import annotations

import dataclasses

import pytest

from sr2fpga_agent.budget_allocation import (
    B4_ALLOCATIONS,
    B4_TOTAL_MODEL_CALLS,
    BUDGET_POLICY_ID,
    BudgetAllocation,
    BudgetAllocationError,
    assert_b4_conformant,
    budget_allocation,
    budget_policy_sha256,
)
from sr2fpga_agent.method_contract import MethodConditionId, method_contract


# Plan section 6.4: (initial stage calls, remaining calls, total).
PLAN_SECTION_6_4 = {
    "M0": (1, 0, 1),
    "M1": (1, 3, 4),
    "M2": (2, 0, 2),
    "M3": (2, 0, 2),
    "M4": (2, 0, 2),
    "M5": (2, 2, 4),
}


@pytest.mark.parametrize("condition", sorted(PLAN_SECTION_6_4))
def test_allocation_matches_the_plan_table(condition: str) -> None:
    initial, remaining, total = PLAN_SECTION_6_4[condition]
    allocation = budget_allocation(condition)
    assert allocation.initial_stage_calls == initial
    assert allocation.remaining_calls == remaining
    assert allocation.standalone_max_model_calls == total


def test_every_method_condition_is_registered() -> None:
    assert set(B4_ALLOCATIONS) == set(MethodConditionId)


def test_repair_methods_share_the_b4_ceiling() -> None:
    """The point of B4: M1 and M5 get equal total calls, not equal repair counts."""

    m1 = budget_allocation("M1")
    m5 = budget_allocation("M5")
    assert m1.standalone_max_model_calls == m5.standalone_max_model_calls
    assert m1.standalone_max_model_calls == B4_TOTAL_MODEL_CALLS
    # They differ in how the budget splits, which is what makes the comparison
    # meaningful rather than a matched-repair-count budget.
    assert m1.remaining_calls != m5.remaining_calls


def test_no_allocation_exceeds_the_b4_ceiling() -> None:
    for allocation in B4_ALLOCATIONS.values():
        assert allocation.standalone_max_model_calls <= B4_TOTAL_MODEL_CALLS


def test_initial_calls_match_declared_non_repair_stages() -> None:
    for condition, allocation in B4_ALLOCATIONS.items():
        contract = method_contract(condition)
        non_repair = [
            stage
            for stage in contract.declared_model_stages
            if stage.value not in {"project_repair", "his_correction"}
        ]
        assert allocation.initial_stage_calls == len(non_repair)


def test_repair_permission_agrees_with_the_method_contract() -> None:
    for condition, allocation in B4_ALLOCATIONS.items():
        contract = method_contract(condition)
        may_repair = contract.allows_project_repair or contract.allows_his_correction
        assert allocation.allows_repair == may_repair


def test_method_contracts_reference_registered_allocation_ids() -> None:
    registered = {allocation.allocation_id for allocation in B4_ALLOCATIONS.values()}
    for condition in MethodConditionId:
        assert method_contract(condition).budget_allocation_id in registered


def test_method_contract_allocation_id_matches_its_own_allocation() -> None:
    for condition in MethodConditionId:
        assert (
            method_contract(condition).budget_allocation_id
            == budget_allocation(condition).allocation_id
        )


# --- Unresolved axes must stay visible -------------------------------------


def test_unresolved_axes_are_reported_and_block_freeze() -> None:
    """Plan appendix A: placeholders must not pass as an approved configuration."""

    allocation = budget_allocation("M5")
    assert allocation.unresolved_axes
    assert allocation.is_freeze_ready is False
    assert allocation.to_dict()["freeze_ready"] is False
    assert set(allocation.to_dict()["unresolved_axes"]) == set(allocation.unresolved_axes)


def test_allocation_becomes_freeze_ready_only_when_every_axis_is_set() -> None:
    allocation = budget_allocation("M0")
    resolved = dataclasses.replace(
        allocation,
        max_total_input_tokens=1,
        max_total_output_tokens=1,
        max_single_output_tokens=1,
        max_public_tool_calls=1,
        max_active_runtime_seconds=1.0,
        max_eda_seconds=1.0,
    )
    assert resolved.unresolved_axes == ()
    assert resolved.is_freeze_ready is True

    # One missing axis is still not freeze-ready.
    partial = dataclasses.replace(resolved, max_eda_seconds=None)
    assert partial.is_freeze_ready is False
    assert partial.unresolved_axes == ("max_eda_seconds",)


# --- Negative cases ---------------------------------------------------------


def test_unknown_method_condition_is_rejected() -> None:
    with pytest.raises(BudgetAllocationError):
        budget_allocation("M6")
    with pytest.raises(BudgetAllocationError):
        budget_allocation("not-a-condition")


def test_allocation_above_the_b4_ceiling_is_rejected() -> None:
    with pytest.raises(ValueError, match="exceeds the B4 ceiling"):
        BudgetAllocation("over-budget", MethodConditionId.M1, 1, 4, True)


def test_negative_allocation_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        BudgetAllocation("negative", MethodConditionId.M1, 1, -1, True)


def test_repair_flag_must_match_remaining_calls() -> None:
    with pytest.raises(ValueError, match="repair permission"):
        BudgetAllocation("mismatch", MethodConditionId.M1, 1, 3, False)
    with pytest.raises(ValueError, match="repair permission"):
        BudgetAllocation("mismatch", MethodConditionId.M0, 1, 0, True)


def test_initial_calls_must_match_declared_stages() -> None:
    with pytest.raises(ValueError, match="initial-stage calls"):
        BudgetAllocation("wrong-stages", MethodConditionId.M3, 1, 0, False)


def test_remaining_calls_require_a_repair_capable_method() -> None:
    with pytest.raises(ValueError, match="permits neither repair nor PC correction"):
        BudgetAllocation("no-repair-surface", MethodConditionId.M3, 2, 1, True)


# --- Conformance enforcement ------------------------------------------------


@pytest.mark.parametrize("condition", sorted(PLAN_SECTION_6_4))
def test_conformant_ceiling_is_accepted(condition: str) -> None:
    assert_b4_conformant(condition, PLAN_SECTION_6_4[condition][2])


def test_ceiling_above_the_allocation_is_rejected() -> None:
    with pytest.raises(ValueError, match="does not match its B4 allocation"):
        assert_b4_conformant("M1", 5)


def test_ceiling_below_the_allocation_is_rejected() -> None:
    """Under-budgeting one arm breaks the comparison as surely as over-budgeting."""

    with pytest.raises(ValueError, match="does not match its B4 allocation"):
        assert_b4_conformant("M5", 3)
    with pytest.raises(ValueError, match="does not match its B4 allocation"):
        assert_b4_conformant("M1", 1)


# --- Policy identity --------------------------------------------------------


def test_policy_digest_is_stable_and_distinguishes_policies() -> None:
    assert budget_policy_sha256() == budget_policy_sha256()
    assert len(budget_policy_sha256()) == 64
    assert BUDGET_POLICY_ID == "paper1-b4-v1"


def test_allocation_ids_carry_the_b4_marker_not_the_superseded_labels() -> None:
    superseded = {"paper1-at1-v1", "paper1-two-stage-v1", "paper1-online-repair-v1"}
    for allocation in B4_ALLOCATIONS.values():
        assert allocation.allocation_id not in superseded
        assert "b4" in allocation.allocation_id
