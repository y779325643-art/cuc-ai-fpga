"""The runner's model-call ceilings must follow the selected budget policy."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from sr2fpga_agent import runner as runner_module
from sr2fpga_agent.budget_allocation import BUDGET_POLICY_ID
from sr2fpga_agent.runner import RunnerConfig, TaskConfig, _sample_model_call_ceiling


def _config(**overrides) -> RunnerConfig:
    base = RunnerConfig(
        dataset_root=Path("dataset"),
        export_root=Path("export"),
        run_root=Path("run"),
        provider="deterministic",
        repair_provider="none",
        max_attempts=1,
        refresh_exports=False,
        line_b_targets={},
        tasks=[],
    )
    return dataclasses.replace(base, **overrides)


ALL_METHODS = ("M0", "M1", "M2", "M3", "M4", "M5")

# Plan section 6.4 standalone ceilings.
B4_CEILINGS = {"M0": 1, "M1": 4, "M2": 2, "M3": 2, "M4": 2, "M5": 4}


@pytest.mark.parametrize("method", ALL_METHODS)
@pytest.mark.parametrize("max_attempts", (1, 3, 4, 7))
def test_b4_ceilings_do_not_depend_on_max_attempts(method: str, max_attempts: int) -> None:
    """B4 is a total-call budget, so the attempt count must not move it."""

    config = _config(budget_policy=BUDGET_POLICY_ID, max_attempts=max_attempts)
    assert _sample_model_call_ceiling(None, config, method) == B4_CEILINGS[method]


@pytest.mark.parametrize("max_attempts", (1, 2, 3, 4, 7))
def test_b4_gives_m1_and_m5_equal_total_calls(max_attempts: int) -> None:
    config = _config(budget_policy=BUDGET_POLICY_ID, max_attempts=max_attempts)
    m1 = _sample_model_call_ceiling(None, config, "M1")
    m5 = _sample_model_call_ceiling(None, config, "M5")
    assert m1 == m5 == 4


@pytest.mark.parametrize("max_attempts", (1, 2, 3, 5))
def test_legacy_policy_can_give_m1_and_m5_different_totals(max_attempts: int) -> None:
    """Regression witness for the unfairness B4 replaces.

    The superseded formula gives M5 one more call than M1 at every attempt
    count, which is exactly the matched-repair-count budget `paper1-v2.1`
    section 6.4 rejects. The legacy path is retained deliberately, so this
    records its behaviour rather than asserting it is acceptable.
    """

    config = _config(budget_policy="legacy-attempts-v1", max_attempts=max_attempts)
    m1 = _sample_model_call_ceiling(None, config, "M1")
    m5 = _sample_model_call_ceiling(None, config, "M5")
    assert m1 != m5


def test_legacy_is_the_default_so_existing_configs_are_unchanged() -> None:
    config = _config()
    assert config.budget_policy == "legacy-attempts-v1"
    assert _sample_model_call_ceiling(None, config, "M5") == 2


def test_b4_rejects_a_contradicting_max_model_calls_override() -> None:
    config = _config(budget_policy=BUDGET_POLICY_ID, max_model_calls=9)
    with pytest.raises(SystemExit, match="contradicts"):
        _sample_model_call_ceiling(None, config, "M1")


def test_b4_accepts_a_redundant_but_matching_override() -> None:
    config = _config(budget_policy=BUDGET_POLICY_ID, max_model_calls=4)
    assert _sample_model_call_ceiling(None, config, "M5") == 4


def test_legacy_override_still_wins_under_the_legacy_policy() -> None:
    config = _config(budget_policy="legacy-attempts-v1", max_model_calls=9)
    assert _sample_model_call_ceiling(None, config, "M1") == 9


@pytest.mark.parametrize("method", ("reference_deterministic", "oracle_his_ceiling"))
def test_non_method_conditions_keep_their_fixed_ceilings_under_b4(method: str) -> None:
    config = _config(budget_policy=BUDGET_POLICY_ID)
    expected = 0 if method == "reference_deterministic" else 1
    assert _sample_model_call_ceiling(None, config, method) == expected


def test_unregistered_method_is_rejected_under_b4() -> None:
    config = _config(budget_policy=BUDGET_POLICY_ID)
    with pytest.raises(SystemExit, match="No registered"):
        _sample_model_call_ceiling(None, config, "M6")


def test_unknown_budget_policy_is_rejected_at_planning_time() -> None:
    config = _config(budget_policy="made-up-policy")
    with pytest.raises(SystemExit, match="unknown budget_policy"):
        runner_module.planned_samples(config)


def test_supported_policies_are_exactly_b4_and_legacy() -> None:
    assert runner_module._SUPPORTED_BUDGET_POLICIES == frozenset(
        {BUDGET_POLICY_ID, "legacy-attempts-v1"}
    )
