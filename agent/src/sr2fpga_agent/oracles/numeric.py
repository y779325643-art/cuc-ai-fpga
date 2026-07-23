"""Independent numeric reference models and evaluator-local scenario bundles."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Sequence

from sr2fpga_agent.oracles.bundle import write_oracle_bundle
from sr2fpga_agent.oracles.types import OracleBundle, OracleField, OracleScenarioSpec


FIR_COEFFICIENTS = (3, -2, 1)
MATRIX_VECTOR_COEFFICIENTS = (2, -1, 3, 1)

_WITHHELD_SEEDS = {
    "fir_hidden": 0xB7E151628AED2A6ABF7158809CF4F3C7,
    "fir_randomized": 0x9E3779B97F4A7C15F39CC0605CEDC835,
    "fir_stress": 0xD1B54A32D192ED03ABC98388FB8FAC03,
    "matrix_hidden": 0x94D049BB133111EBE8D4A510B73A3C59,
    "matrix_randomized": 0xDB4F0B9175AE2165A5A3564E27F8862F,
    "matrix_stress": 0xA24BAED4963EE4079FB21C651E98DF25,
}


def signed(value: int, width: int) -> int:
    """Interpret the low ``width`` bits of value as two's complement."""

    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        raise ValueError("numeric oracle width must be a positive integer")
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("numeric oracle values must be integers")
    masked = value & ((1 << width) - 1)
    return masked - (1 << width) if masked & (1 << (width - 1)) else masked


def fir_outputs(samples: Sequence[int], width: int) -> list[int]:
    """Evaluate a three-tap FIR with coefficients ``(3, -2, 1)``."""

    d0 = d1 = 0
    outputs: list[int] = []
    for sample in samples:
        current = signed(sample, width)
        outputs.append(3 * current - 2 * d0 + d1)
        d1, d0 = d0, current
    return outputs


def matrix_vector_outputs(samples: Sequence[int], width: int) -> list[int]:
    """Evaluate groups of four samples against the fixed coefficient ROM."""

    if len(samples) % 4:
        raise ValueError("matrix-vector scenarios require groups of four samples")
    return [
        sum(
            signed(value, width) * coefficient
            for value, coefficient in zip(samples[index : index + 4], MATRIX_VECTOR_COEFFICIENTS)
        )
        for index in range(0, len(samples), 4)
    ]


def build_fir_filter_bundle(width: int, root: Path) -> OracleBundle:
    result_width = width + 3
    scenarios = (
        _fir_scenario(
            "fir_public_smoke",
            "public_smoke",
            0,
            ((5, True, 0), (-4, False, 0), (7, False, 0)),
            width,
            result_width,
        ),
        _fir_scenario(
            "fir_hidden_edges",
            "hidden_deterministic",
            _WITHHELD_SEEDS["fir_hidden"],
            ((-128, True, 0), (127, False, 0), (-1, False, 0), (0, False, 0)),
            width,
            result_width,
        ),
        _fir_scenario(
            "fir_randomized_seeded",
            "randomized_fixed_seed",
            _WITHHELD_SEEDS["fir_randomized"],
            _random_fir_events(width, _WITHHELD_SEEDS["fir_randomized"]),
            width,
            result_width,
        ),
        _fir_scenario(
            "fir_stress_reset_stall",
            "stress",
            _WITHHELD_SEEDS["fir_stress"],
            (
                ((1 << (width - 1)) - 1, True, 3),
                (-(1 << (width - 1)), False, 2),
                ((1 << (width - 1)) - 1, False, 0),
                (-(1 << (width - 1)), True, 1),
                (-1, False, 0),
            ),
            width,
            result_width,
        ),
    )
    return write_oracle_bundle(
        root=Path(root),
        family_id="fir_filter",
        reference_model="python_numeric_reference",
        reference_version="1.0.0",
        task_parameters={
            "width": width,
            "result_width": result_width,
            "coefficients": list(FIR_COEFFICIENTS),
            "history_reset": "zero",
            "result_overflow": f"two_complement_{result_width}_bit",
        },
        scenarios=scenarios,
    )


def build_matrix_vector_mac_bundle(width: int, root: Path) -> OracleBundle:
    result_width = width + 4
    maximum = (1 << (width - 1)) - 1
    minimum = -(1 << (width - 1))
    scenarios = (
        _matrix_scenario(
            "matrix_public_smoke",
            "public_smoke",
            0,
            ((1, True, 0), (2, False, 0), (3, False, 0), (4, False, 0)),
            width,
            result_width,
        ),
        _matrix_scenario(
            "matrix_hidden_edges",
            "hidden_deterministic",
            _WITHHELD_SEEDS["matrix_hidden"],
            (
                (maximum, True, 0),
                (minimum, False, 0),
                (maximum, False, 0),
                (maximum, False, 0),
                (minimum, False, 0),
                (maximum, False, 0),
                (minimum, False, 0),
                (minimum, False, 0),
            ),
            width,
            result_width,
        ),
        _matrix_scenario(
            "matrix_randomized_seeded",
            "randomized_fixed_seed",
            _WITHHELD_SEEDS["matrix_randomized"],
            _random_matrix_events(width, _WITHHELD_SEEDS["matrix_randomized"]),
            width,
            result_width,
        ),
        _matrix_scenario(
            "matrix_stress_reset_stall",
            "stress",
            _WITHHELD_SEEDS["matrix_stress"],
            (
                (9, True, 0),
                (-7, False, 0),
                (maximum, True, 0),
                (minimum, False, 0),
                (maximum, False, 0),
                (maximum, False, 3),
                (minimum, False, 0),
                (maximum, False, 0),
                (minimum, False, 0),
                (maximum, False, 2),
            ),
            width,
            result_width,
        ),
    )
    return write_oracle_bundle(
        root=Path(root),
        family_id="matrix_vector_mac",
        reference_model="python_numeric_reference",
        reference_version="1.0.0",
        task_parameters={
            "width": width,
            "result_width": result_width,
            "coefficients": list(MATRIX_VECTOR_COEFFICIENTS),
            "samples_per_result": 4,
            "result_overflow": f"two_complement_{result_width}_bit",
        },
        scenarios=scenarios,
    )


def _input_fields(width: int) -> tuple[OracleField, ...]:
    return (
        OracleField("sample", width - 1, 0, True),
        OracleField("reset_before", width, width, False),
        OracleField("stall_cycles", width + 2, width + 1, False),
    )


def _expected_fields(result_width: int) -> tuple[OracleField, ...]:
    return (
        OracleField("result", result_width - 1, 0, True),
        OracleField("expect_output", result_width, result_width, False),
    )


def _pack_input(sample: int, reset_before: bool, stall_cycles: int, width: int) -> int:
    if not 0 <= stall_cycles <= 3:
        raise ValueError("numeric oracle stall_cycles must fit two bits")
    return (
        (sample & ((1 << width) - 1))
        | (int(reset_before) << width)
        | (stall_cycles << (width + 1))
    )


def _pack_expected(result: int, expect_output: bool, result_width: int) -> int:
    return (result & ((1 << result_width) - 1)) | (int(expect_output) << result_width)


def _fir_scenario(
    scenario_id: str,
    scenario_class: str,
    seed: int,
    events: Sequence[tuple[int, bool, int]],
    width: int,
    result_width: int,
) -> OracleScenarioSpec:
    d0 = d1 = 0
    input_records: list[int] = []
    expected_records: list[int] = []
    for sample, reset_before, stall_cycles in events:
        if reset_before:
            d0 = d1 = 0
        current = signed(sample, width)
        result = 3 * current - 2 * d0 + d1
        d1, d0 = d0, current
        input_records.append(_pack_input(sample, reset_before, stall_cycles, width))
        expected_records.append(_pack_expected(result, True, result_width))
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=width + 3,
        expected_record_width_bits=result_width + 1,
        input_fields=_input_fields(width),
        expected_fields=_expected_fields(result_width),
        input_records=tuple(input_records),
        expected_records=tuple(expected_records),
    )


def _matrix_scenario(
    scenario_id: str,
    scenario_class: str,
    seed: int,
    events: Sequence[tuple[int, bool, int]],
    width: int,
    result_width: int,
) -> OracleScenarioSpec:
    group: list[int] = []
    input_records: list[int] = []
    expected_records: list[int] = []
    for sample, reset_before, stall_cycles in events:
        if reset_before:
            group.clear()
        group.append(signed(sample, width))
        expect_output = len(group) == 4
        result = matrix_vector_outputs(group, width)[0] if expect_output else 0
        if expect_output:
            group.clear()
        input_records.append(_pack_input(sample, reset_before, stall_cycles, width))
        expected_records.append(_pack_expected(result, expect_output, result_width))
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=width + 3,
        expected_record_width_bits=result_width + 1,
        input_fields=_input_fields(width),
        expected_fields=_expected_fields(result_width),
        input_records=tuple(input_records),
        expected_records=tuple(expected_records),
    )


def _random_fir_events(width: int, seed: int) -> tuple[tuple[int, bool, int], ...]:
    randomizer = random.Random(seed)
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    return tuple(
        (
            randomizer.randint(minimum, maximum),
            index in {0, 8},
            2 if index in {3, 11} else 0,
        )
        for index in range(16)
    )


def _random_matrix_events(width: int, seed: int) -> tuple[tuple[int, bool, int], ...]:
    randomizer = random.Random(seed)
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    return tuple(
        (
            randomizer.randint(minimum, maximum),
            index == 0,
            2 if index in {3, 11} else 0,
        )
        for index in range(12)
    )


__all__ = [
    "FIR_COEFFICIENTS",
    "MATRIX_VECTOR_COEFFICIENTS",
    "build_fir_filter_bundle",
    "build_matrix_vector_mac_bundle",
    "fir_outputs",
    "matrix_vector_outputs",
    "signed",
]
