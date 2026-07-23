"""Independent fixed-point RL references and evaluator-local oracle bundles."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import random
from typing import Iterable, Sequence

from sr2fpga_agent.oracles.bundle import write_oracle_bundle
from sr2fpga_agent.oracles.types import OracleBundle, OracleField, OracleScenarioSpec


FIXED_SHIFT = 4

OP_RESET = 0
OP_CFG_WRITE = 1
OP_SAMPLE = 2

_WITHHELD_SEEDS = {
    "td_hidden": 0xB195BFA7652F09CF7DA5446B38A11E47,
    "td_randomized": 0xEC7A467F388DC946D0568541BB7D33B1,
    "td_stress": 0xDB4F0B9175AE2165D618E9287B12C91D,
    "rl_hidden": 0xD83B09E1B5BD9F58C73F24B6A14DA257,
    "rl_randomized": 0x9CE38D3205F3A4E708FF24F0AB11CD59,
    "rl_stress": 0xF4A59B8DDE32531FEA02176C13B994A5,
}


@dataclass(frozen=True)
class RLConfig:
    weight0: int = 0
    bias0: int = 0
    weight1: int = 0
    bias1: int = 0
    alpha: int = 0
    enable: bool = False

    def write(self, address: int, data: int, *, width: int) -> "RLConfig":
        """Apply the declared config-register write at address 0 through 5."""

        _validate_width(width)
        _validate_unsigned("config data", data, width)
        if not isinstance(address, int) or isinstance(address, bool) or not 0 <= address <= 5:
            raise ValueError("RL config address must be an integer in [0, 5]")
        field = ("weight0", "bias0", "weight1", "bias1", "alpha", "enable")[address]
        return replace(self, **{field: bool(data & 1) if field == "enable" else data})


@dataclass(frozen=True)
class _RLOperation:
    operation: int
    cfg_addr: int = 0
    cfg_data: int = 0
    obs0: int = 0
    obs1: int = 0
    reward: int = 0
    next_value: int = 0
    done: bool = False
    stall_cycles: int = 0


def saturate_signed(value: int, width: int) -> int:
    _validate_width(width)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("signed value must be an integer")
    low = -(1 << (width - 1))
    high = (1 << (width - 1)) - 1
    return min(max(value, low), high)


def td_update(
    reward: int,
    value: int,
    next_value: int,
    gamma: int,
    alpha: int,
    width: int,
) -> tuple[int, int]:
    """Compute one signed Q4 temporal-difference update."""

    _validate_width(width)
    for name, operand in (("reward", reward), ("value", value), ("next_value", next_value)):
        _validate_signed(name, operand, width)
    _validate_unsigned("gamma", gamma, width)
    _validate_unsigned("alpha", alpha, width)
    target = reward + ((next_value * gamma) >> FIXED_SHIFT)
    error = saturate_signed(target - value, width)
    updated = saturate_signed(value + ((error * alpha) >> FIXED_SHIFT), width)
    return error, updated


def argmax_first(values: Sequence[int]) -> int:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        raise ValueError("argmax requires at least one value")
    return max(range(len(values)), key=lambda index: values[index])


def rl_accelerator_step(
    config: RLConfig,
    obs0: int,
    obs1: int,
    reward: int,
    next_value: int,
    done: bool,
    *,
    width: int = 8,
) -> tuple[int, int, int, bool, bool]:
    """Compute the declared unsigned policy/value and update shell result."""

    _validate_width(width)
    if not isinstance(config, RLConfig):
        raise ValueError("config must be an RLConfig")
    for name in ("weight0", "bias0", "weight1", "bias1", "alpha"):
        _validate_unsigned(name, getattr(config, name), width)
    for name, operand in (
        ("obs0", obs0),
        ("obs1", obs1),
        ("reward", reward),
        ("next_value", next_value),
    ):
        _validate_unsigned(name, operand, width)
    if not isinstance(done, bool):
        raise ValueError("done must be a bool")

    maximum = (1 << width) - 1
    score0 = min(obs0 * config.weight0 + config.bias0, maximum)
    score1 = min(obs1 * config.weight1 + config.bias1, maximum)
    selected_action = argmax_first((score0, score1))
    value_estimate = (score0 + score1) >> 1
    error = max(reward + next_value - value_estimate, 0)
    update_delta = min((config.alpha * error) >> FIXED_SHIFT, maximum)
    updated_value = (value_estimate + update_delta) & maximum
    episode_done = done
    irq = episode_done
    return selected_action, value_estimate, updated_value, episode_done, irq


def build_qtable_update_bundle(width: int, root: Path) -> OracleBundle:
    _validate_width(width)
    low, high = _signed_bounds(width)
    scenarios = (
        _td_scenario(
            scenario_id="td_public_declared_examples",
            scenario_class="public_smoke",
            seed=0,
            width=width,
            records=((4, 10, 20, 8, 4, True, 0), (2, 6, 16, 8, 8, False, 0)),
        ),
        _td_scenario(
            scenario_id="td_hidden_signed_saturation",
            scenario_class="hidden_deterministic",
            seed=_WITHHELD_SEEDS["td_hidden"],
            width=width,
            records=(
                (-8, 4, -3, 8, 8, True, 0),
                (high, low, high, 16, 16, False, 0),
                (low, low, low, 8, 8, False, 0),
                (high, high, high, 8, 8, False, 0),
            ),
        ),
        _td_scenario(
            scenario_id="td_randomized_seeded",
            scenario_class="randomized_fixed_seed",
            seed=_WITHHELD_SEEDS["td_randomized"],
            width=width,
            records=_random_td_records(width, _WITHHELD_SEEDS["td_randomized"], 6),
        ),
        _td_scenario(
            scenario_id="td_stress_reset_stall_bounds",
            scenario_class="stress",
            seed=_WITHHELD_SEEDS["td_stress"],
            width=width,
            records=(
                (low, high, low, 16, 16, True, 3),
                (high, low, high, 16, 16, False, 2),
                (-1, 0, -1, 15, 15, True, 1),
            ),
        ),
    )
    return write_oracle_bundle(
        root=Path(root),
        family_id="qtable_update_core",
        reference_model="python_rl_reference",
        reference_version="1.0.0",
        task_parameters={
            "width": width,
            "fixed_shift": FIXED_SHIFT,
            "signed_td": True,
            "shift": "arithmetic_right",
            "overflow": "saturate_to_width",
        },
        scenarios=scenarios,
    )


def build_rl_accelerator_bundle(width: int, root: Path) -> OracleBundle:
    _validate_width(width)
    maximum = (1 << width) - 1
    scenarios = (
        _rl_scenario(
            scenario_id="rl_public_config_samples",
            scenario_class="public_smoke",
            seed=0,
            width=width,
            operations=(
                _reset(),
                *_config_writes((2, 1, 3, 0, 4, 1)),
                _sample(4, 2, 1, 8, False),
                _sample(1, 5, 2, 15, True),
            ),
        ),
        _rl_scenario(
            scenario_id="rl_hidden_enable_tie_register_map",
            scenario_class="hidden_deterministic",
            seed=_WITHHELD_SEEDS["rl_hidden"],
            width=width,
            operations=(
                _reset(),
                *_config_writes((2, 1, 2, 1, 8, 0)),
                _sample(3, 3, 1, 1, False),
                _cfg(5, 1),
                _sample(3, 3, 0, 0, False),
            ),
        ),
        _rl_scenario(
            scenario_id="rl_randomized_seeded",
            scenario_class="randomized_fixed_seed",
            seed=_WITHHELD_SEEDS["rl_randomized"],
            width=width,
            operations=_random_rl_operations(width, _WITHHELD_SEEDS["rl_randomized"]),
        ),
        _rl_scenario(
            scenario_id="rl_stress_reset_stall_saturation_irq",
            scenario_class="stress",
            seed=_WITHHELD_SEEDS["rl_stress"],
            width=width,
            operations=(
                _reset(),
                *_config_writes((maximum, maximum, maximum, maximum, maximum, 1)),
                _sample(maximum, maximum, maximum, maximum, False, stall_cycles=3),
                _sample(0, 0, 0, 0, True, stall_cycles=2),
                _reset(),
                *_config_writes((2, 1, 3, 0, 4, 1)),
                _sample(4, 2, 0, 0, True, stall_cycles=1),
            ),
        ),
    )
    return write_oracle_bundle(
        root=Path(root),
        family_id="p_rl_qlearning_accel",
        reference_model="python_rl_reference",
        reference_version="1.0.0",
        task_parameters={
            "width": width,
            "fixed_shift": FIXED_SHIFT,
            "register_map": {
                "0": "weight0",
                "1": "bias0",
                "2": "weight1",
                "3": "bias1",
                "4": "alpha",
                "5": "enable",
            },
            "argmax_tie": "first_index",
            "score_overflow": "saturate_to_width",
            "negative_td_error": "clamp_to_zero",
            "updated_value": "wrap_to_width",
            "irq": "sticky_after_done_result_until_reset",
        },
        scenarios=scenarios,
    )


def _td_scenario(
    *,
    scenario_id: str,
    scenario_class: str,
    seed: int,
    width: int,
    records: Iterable[tuple[int, int, int, int, int, bool, int]],
) -> OracleScenarioSpec:
    inputs: list[int] = []
    expected: list[int] = []
    reset_bit = 5 * width
    stall_lsb = reset_bit + 1
    for reward, value, next_value, gamma, alpha, reset_before, stall_cycles in records:
        _validate_stall(stall_cycles)
        error, updated = td_update(reward, value, next_value, gamma, alpha, width)
        inputs.append(
            _pack_signed(reward, width)
            | (_pack_signed(value, width) << width)
            | (_pack_signed(next_value, width) << (2 * width))
            | (gamma << (3 * width))
            | (alpha << (4 * width))
            | (int(reset_before) << reset_bit)
            | (stall_cycles << stall_lsb)
        )
        expected.append(_pack_signed(error, width) | (_pack_signed(updated, width) << width))
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=(5 * width) + 3,
        expected_record_width_bits=2 * width,
        input_fields=(
            OracleField("reward", width - 1, 0, True),
            OracleField("value", (2 * width) - 1, width, True),
            OracleField("next_value", (3 * width) - 1, 2 * width, True),
            OracleField("gamma", (4 * width) - 1, 3 * width, False),
            OracleField("alpha", (5 * width) - 1, 4 * width, False),
            OracleField("reset_before", reset_bit, reset_bit, False),
            OracleField("stall_cycles", stall_lsb + 1, stall_lsb, False),
        ),
        expected_fields=(
            OracleField("td_error", width - 1, 0, True),
            OracleField("updated_value", (2 * width) - 1, width, True),
        ),
        input_records=tuple(inputs),
        expected_records=tuple(expected),
    )


def _rl_scenario(
    *,
    scenario_id: str,
    scenario_class: str,
    seed: int,
    width: int,
    operations: Sequence[_RLOperation],
) -> OracleScenarioSpec:
    cfg_data_lsb = 5
    obs0_lsb = cfg_data_lsb + width
    obs1_lsb = obs0_lsb + width
    reward_lsb = obs1_lsb + width
    next_value_lsb = reward_lsb + width
    done_bit = next_value_lsb + width
    stall_lsb = done_bit + 1
    value_lsb = 2
    updated_lsb = value_lsb + width
    episode_done_bit = updated_lsb + width
    irq_bit = episode_done_bit + 1

    config = RLConfig()
    sticky_irq = False
    inputs: list[int] = []
    expected: list[int] = []
    for operation in operations:
        _validate_operation(operation, width)
        inputs.append(
            operation.operation
            | (operation.cfg_addr << 2)
            | (operation.cfg_data << cfg_data_lsb)
            | (operation.obs0 << obs0_lsb)
            | (operation.obs1 << obs1_lsb)
            | (operation.reward << reward_lsb)
            | (operation.next_value << next_value_lsb)
            | (int(operation.done) << done_bit)
            | (operation.stall_cycles << stall_lsb)
        )
        if operation.operation == OP_RESET:
            config = RLConfig()
            sticky_irq = False
            expected.append(0)
        elif operation.operation == OP_CFG_WRITE:
            config = config.write(operation.cfg_addr, operation.cfg_data, width=width)
            expected.append(int(sticky_irq) << irq_bit)
        else:
            result = rl_accelerator_step(
                config,
                operation.obs0,
                operation.obs1,
                operation.reward,
                operation.next_value,
                operation.done,
                width=width,
            )
            expect_output = int(config.enable)
            if expect_output:
                selected, value_estimate, updated, episode_done, irq = result
                sticky_irq = sticky_irq or irq
                expected.append(
                    1
                    | (selected << 1)
                    | (value_estimate << value_lsb)
                    | (updated << updated_lsb)
                    | (int(episode_done) << episode_done_bit)
                    | (int(sticky_irq) << irq_bit)
                )
            else:
                expected.append(int(sticky_irq) << irq_bit)
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=(5 * width) + 8,
        expected_record_width_bits=(2 * width) + 4,
        input_fields=(
            OracleField("operation", 1, 0, False),
            OracleField("cfg_addr", 4, 2, False),
            OracleField("cfg_data", cfg_data_lsb + width - 1, cfg_data_lsb, False),
            OracleField("obs0", obs0_lsb + width - 1, obs0_lsb, False),
            OracleField("obs1", obs1_lsb + width - 1, obs1_lsb, False),
            OracleField("reward", reward_lsb + width - 1, reward_lsb, False),
            OracleField("next_value", next_value_lsb + width - 1, next_value_lsb, False),
            OracleField("done", done_bit, done_bit, False),
            OracleField("stall_cycles", stall_lsb + 1, stall_lsb, False),
        ),
        expected_fields=(
            OracleField("expect_output", 0, 0, False),
            OracleField("selected_action", 1, 1, False),
            OracleField("value_estimate", value_lsb + width - 1, value_lsb, False),
            OracleField("updated_value", updated_lsb + width - 1, updated_lsb, False),
            OracleField("episode_done", episode_done_bit, episode_done_bit, False),
            OracleField("irq", irq_bit, irq_bit, False),
        ),
        input_records=tuple(inputs),
        expected_records=tuple(expected),
    )


def _random_td_records(
    width: int,
    seed: int,
    count: int,
) -> tuple[tuple[int, int, int, int, int, bool, int], ...]:
    randomizer = random.Random(seed)
    low, high = _signed_bounds(width)
    scale_max = min((1 << width) - 1, 16)
    return tuple(
        (
            randomizer.randint(low, high),
            randomizer.randint(low, high),
            randomizer.randint(low, high),
            randomizer.randint(0, scale_max),
            randomizer.randint(0, scale_max),
            index == 0,
            randomizer.randint(0, 2),
        )
        for index in range(count)
    )


def _random_rl_operations(width: int, seed: int) -> tuple[_RLOperation, ...]:
    randomizer = random.Random(seed)
    maximum = (1 << width) - 1
    config_values = tuple(randomizer.randint(0, min(maximum, 15)) for _ in range(5)) + (1,)
    samples = tuple(
        _sample(
            randomizer.randint(0, maximum),
            randomizer.randint(0, maximum),
            randomizer.randint(0, maximum),
            randomizer.randint(0, maximum),
            index == 3,
            stall_cycles=randomizer.randint(0, 2),
        )
        for index in range(4)
    )
    return (_reset(), *_config_writes(config_values), *samples)


def _reset() -> _RLOperation:
    return _RLOperation(OP_RESET)


def _cfg(address: int, data: int) -> _RLOperation:
    return _RLOperation(OP_CFG_WRITE, cfg_addr=address, cfg_data=data)


def _config_writes(values: Sequence[int]) -> tuple[_RLOperation, ...]:
    if len(values) != 6:
        raise ValueError("RL config sequence must contain six register values")
    return tuple(_cfg(address, value) for address, value in enumerate(values))


def _sample(
    obs0: int,
    obs1: int,
    reward: int,
    next_value: int,
    done: bool,
    *,
    stall_cycles: int = 0,
) -> _RLOperation:
    return _RLOperation(
        OP_SAMPLE,
        obs0=obs0,
        obs1=obs1,
        reward=reward,
        next_value=next_value,
        done=done,
        stall_cycles=stall_cycles,
    )


def _validate_operation(operation: _RLOperation, width: int) -> None:
    if operation.operation not in {OP_RESET, OP_CFG_WRITE, OP_SAMPLE}:
        raise ValueError("unsupported RL oracle operation")
    _validate_stall(operation.stall_cycles)
    for name in ("cfg_data", "obs0", "obs1", "reward", "next_value"):
        _validate_unsigned(name, getattr(operation, name), width)
    if not 0 <= operation.cfg_addr <= 5:
        raise ValueError("RL config address must be in [0, 5]")
    if not isinstance(operation.done, bool):
        raise ValueError("RL done flag must be a bool")


def _validate_width(width: int) -> None:
    if not isinstance(width, int) or isinstance(width, bool) or not 2 <= width <= 16:
        raise ValueError("RL oracle width must be an integer in [2, 16]")


def _signed_bounds(width: int) -> tuple[int, int]:
    return -(1 << (width - 1)), (1 << (width - 1)) - 1


def _validate_signed(name: str, value: int, width: int) -> None:
    low, high = _signed_bounds(width)
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise ValueError(f"{name} must fit signed width {width}")


def _validate_unsigned(name: str, value: int, width: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < (1 << width):
        raise ValueError(f"{name} must fit unsigned width {width}")


def _validate_stall(stall_cycles: int) -> None:
    if not isinstance(stall_cycles, int) or isinstance(stall_cycles, bool) or not 0 <= stall_cycles <= 3:
        raise ValueError("RL oracle stall_cycles must fit two bits")


def _pack_signed(value: int, width: int) -> int:
    return value & ((1 << width) - 1)


__all__ = [
    "FIXED_SHIFT",
    "RLConfig",
    "argmax_first",
    "build_qtable_update_bundle",
    "build_rl_accelerator_bundle",
    "rl_accelerator_step",
    "saturate_signed",
    "td_update",
]
