"""Independent signal-processing references and evaluator-local bundles."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Sequence

from sr2fpga_agent.oracles.bundle import write_oracle_bundle
from sr2fpga_agent.oracles.numeric import signed
from sr2fpga_agent.oracles.types import OracleBundle, OracleField, OracleScenarioSpec


MATCHED_TEMPLATE = (-1, 2, -3, 4)
PEAK_THRESHOLD = 10

_WITHHELD_SEEDS = {
    "matched_hidden": 0xC6BC279692B5CC83A5A3564E27F8862F,
    "matched_randomized": 0xD1342543DE82EF95F39CC0605CEDC835,
    "matched_stress": 0x94D049BB133111EBABC98388FB8FAC03,
    "peak_hidden": 0x9E3779B97F4A7C15A24BAED4963EE407,
    "peak_randomized": 0xDB4F0B9175AE2165B7E151628AED2A6B,
    "peak_stress": 0xA24BAED4963EE4079FB21C651E98DF25,
    "radar_hidden": 0xBF58476D1CE4E5B9D1B54A32D192ED03,
    "radar_randomized": 0x632BE59BD9B4E0198CB92BA72F3D8DD7,
    "radar_stress": 0x8CB92BA72F3D8DD7C6BC279692B5CC83,
}


def matched_filter_outputs(samples: Sequence[int], width: int) -> list[int]:
    """Correlate accepted samples against ``(-1, 2, -3, 4)`` with zero history."""

    history = [0, 0, 0, 0]
    outputs: list[int] = []
    for sample in samples:
        history = [signed(sample, width), *history[:3]]
        outputs.append(sum(value * coefficient for value, coefficient in zip(history, MATCHED_TEMPLATE)))
    return outputs


def detect_peak(values: Sequence[int], threshold: int) -> tuple[int, int, int]:
    """Return the threshold-qualified maximum using first-index tie breaking."""

    found = 0
    best_value = 0
    best_index = 0
    for index, value in enumerate(values):
        if value >= threshold and (not found or value > best_value):
            found, best_value, best_index = 1, value, index
    return found, best_value if found else 0, best_index if found else 0


def pulse_radar(samples: Sequence[int], width: int, threshold: int) -> tuple[int, int, int]:
    """Correlate every accepted frame sample, then select the frame peak."""

    return detect_peak(matched_filter_outputs(samples, width), threshold)


def build_matched_filter_bundle(width: int, root: Path) -> OracleBundle:
    acc_width = 2 * width + 2
    maximum = (1 << (width - 1)) - 1
    minimum = -(1 << (width - 1))
    scenarios = (
        _matched_scenario(
            "matched_public_smoke",
            "public_smoke",
            0,
            ((4, True, 0), (-3, False, 0), (2, False, 0), (-1, False, 0)),
            width,
            acc_width,
        ),
        _matched_scenario(
            "matched_hidden_edges",
            "hidden_deterministic",
            _WITHHELD_SEEDS["matched_hidden"],
            ((maximum, True, 0), (minimum, False, 0), (maximum, False, 0), (minimum, False, 0)),
            width,
            acc_width,
        ),
        _matched_scenario(
            "matched_randomized_seeded",
            "randomized_fixed_seed",
            _WITHHELD_SEEDS["matched_randomized"],
            _random_matched_events(width, _WITHHELD_SEEDS["matched_randomized"]),
            width,
            acc_width,
        ),
        _matched_scenario(
            "matched_stress_reset_stall",
            "stress",
            _WITHHELD_SEEDS["matched_stress"],
            (
                (4, True, 0),
                (-3, False, 0),
                (2, False, 0),
                (-1, False, 3),
                (maximum, True, 2),
                (minimum, False, 0),
            ),
            width,
            acc_width,
        ),
    )
    return write_oracle_bundle(
        root=Path(root),
        family_id="matched_filter",
        reference_model="python_signal_reference",
        reference_version="1.0.0",
        task_parameters={
            "width": width,
            "acc_width": acc_width,
            "template": list(MATCHED_TEMPLATE),
            "history_reset": "zero",
        },
        scenarios=scenarios,
    )


def build_peak_detector_bundle(width: int, root: Path) -> OracleBundle:
    scenarios = (
        _peak_scenario(
            "peak_public_smoke",
            "public_smoke",
            0,
            (
                (-3, True, False, 0), (0, False, False, 0), (9, True, False, 0),
                (11, False, False, 0), (16, False, False, 0), (16, False, False, 0), (14, True, False, 0),
                (11, False, False, 0), (14, False, False, 0), (19, True, False, 0),
                (10, True, False, 0),
            ),
            width,
        ),
        _peak_scenario(
            "peak_hidden_boundaries",
            "hidden_deterministic",
            _WITHHELD_SEEDS["peak_hidden"],
            ((9, False, True, 0), (10, True, False, 0), (127, False, False, 0), (127, True, False, 0)),
            width,
        ),
        _peak_scenario(
            "peak_randomized_seeded",
            "randomized_fixed_seed",
            _WITHHELD_SEEDS["peak_randomized"],
            _random_peak_events(width, _WITHHELD_SEEDS["peak_randomized"]),
            width,
        ),
        _peak_scenario(
            "peak_stress_reset_stall",
            "stress",
            _WITHHELD_SEEDS["peak_stress"],
            (
                (20, False, True, 0),
                (9, False, False, 0),
                (10, True, True, 3),
                (11, False, False, 0),
                (16, False, False, 0),
                (16, True, False, 2),
            ),
            width,
        ),
    )
    return write_oracle_bundle(
        root=Path(root),
        family_id="peak_detector",
        reference_model="python_signal_reference",
        reference_version="1.0.0",
        task_parameters={
            "width": width,
            "threshold": PEAK_THRESHOLD,
            "tie_break": "first_index",
            "empty_result": [0, 0, 0],
        },
        scenarios=scenarios,
    )


def build_pulse_radar_bundle(width: int, root: Path) -> OracleBundle:
    acc_width = 2 * width + 2
    scenarios = (
        _radar_scenario(
            "radar_public_smoke",
            "public_smoke",
            0,
            (
                (4, False, True, 0), (-3, False, False, 0), (2, False, False, 0), (-1, True, False, 0),
                (4, True, False, 0),
                (-10, True, False, 0),
            ),
            width,
            acc_width,
        ),
        _radar_scenario(
            "radar_hidden_tie_and_final",
            "hidden_deterministic",
            _WITHHELD_SEEDS["radar_hidden"],
            (
                (4, False, True, 0), (-3, False, False, 0), (2, False, False, 0), (-1, False, False, 0),
                (0, False, False, 0), (0, False, False, 0), (0, False, False, 0),
                (4, False, False, 0), (-3, False, False, 0), (2, False, False, 0), (-1, True, False, 0),
            ),
            width,
            acc_width,
        ),
        _radar_scenario(
            "radar_randomized_seeded",
            "randomized_fixed_seed",
            _WITHHELD_SEEDS["radar_randomized"],
            _random_radar_events(width, _WITHHELD_SEEDS["radar_randomized"]),
            width,
            acc_width,
        ),
        _radar_scenario(
            "radar_stress_reset_stall",
            "stress",
            _WITHHELD_SEEDS["radar_stress"],
            (
                (4, False, True, 0),
                (-3, False, False, 0),
                (-10, True, True, 3),
                (0, True, False, 0),
                (4, False, False, 0),
                (-3, False, False, 0),
                (2, False, False, 0),
                (-1, True, False, 2),
            ),
            width,
            acc_width,
        ),
    )
    return write_oracle_bundle(
        root=Path(root),
        family_id="p_pulse_radar_signal",
        reference_model="python_signal_reference",
        reference_version="1.0.0",
        task_parameters={
            "width": width,
            "acc_width": acc_width,
            "template": list(MATCHED_TEMPLATE),
            "threshold": PEAK_THRESHOLD,
            "tie_break": "first_index",
            "empty_result": [0, 0, 0],
        },
        scenarios=scenarios,
    )


def _matched_input_fields(width: int) -> tuple[OracleField, ...]:
    return (
        OracleField("sample", width - 1, 0, True),
        OracleField("reset_before", width, width, False),
        OracleField("stall_cycles", width + 2, width + 1, False),
    )


def _framed_input_fields(width: int) -> tuple[OracleField, ...]:
    return (
        OracleField("sample", width - 1, 0, True),
        OracleField("in_last", width, width, False),
        OracleField("reset_before", width + 1, width + 1, False),
        OracleField("stall_cycles", width + 3, width + 2, False),
    )


def _peak_expected_fields(value_width: int) -> tuple[OracleField, ...]:
    return (
        OracleField("value", value_width - 1, 0, True),
        OracleField("index", 2 * value_width - 1, value_width, False),
        OracleField("found", 2 * value_width, 2 * value_width, False),
        OracleField("expect_output", 2 * value_width + 1, 2 * value_width + 1, False),
    )


def _pack_matched_input(sample: int, reset_before: bool, stall_cycles: int, width: int) -> int:
    _validate_stall(stall_cycles)
    return (sample & ((1 << width) - 1)) | (int(reset_before) << width) | (stall_cycles << (width + 1))


def _pack_framed_input(sample: int, in_last: bool, reset_before: bool, stall_cycles: int, width: int) -> int:
    _validate_stall(stall_cycles)
    return (
        (sample & ((1 << width) - 1))
        | (int(in_last) << width)
        | (int(reset_before) << (width + 1))
        | (stall_cycles << (width + 2))
    )


def _pack_peak_expected(result: tuple[int, int, int], expect_output: bool, value_width: int) -> int:
    found, value, index = result if expect_output else (0, 0, 0)
    mask = (1 << value_width) - 1
    return (
        (value & mask)
        | ((index & mask) << value_width)
        | (int(found) << (2 * value_width))
        | (int(expect_output) << (2 * value_width + 1))
    )


def _matched_scenario(
    scenario_id: str,
    scenario_class: str,
    seed: int,
    events: Sequence[tuple[int, bool, int]],
    width: int,
    acc_width: int,
) -> OracleScenarioSpec:
    history = [0, 0, 0, 0]
    inputs: list[int] = []
    expected: list[int] = []
    for sample, reset_before, stall_cycles in events:
        if reset_before:
            history = [0, 0, 0, 0]
        history = [signed(sample, width), *history[:3]]
        correlation = sum(value * coefficient for value, coefficient in zip(history, MATCHED_TEMPLATE))
        inputs.append(_pack_matched_input(sample, reset_before, stall_cycles, width))
        expected.append(correlation & ((1 << acc_width) - 1))
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=width + 3,
        expected_record_width_bits=acc_width,
        input_fields=_matched_input_fields(width),
        expected_fields=(OracleField("correlation", acc_width - 1, 0, True),),
        input_records=tuple(inputs),
        expected_records=tuple(expected),
    )


def _peak_scenario(
    scenario_id: str,
    scenario_class: str,
    seed: int,
    events: Sequence[tuple[int, bool, bool, int]],
    width: int,
) -> OracleScenarioSpec:
    frame: list[int] = []
    inputs: list[int] = []
    expected: list[int] = []
    for sample, in_last, reset_before, stall_cycles in events:
        if reset_before:
            frame.clear()
        frame.append(signed(sample, width))
        result = detect_peak(frame, PEAK_THRESHOLD)
        inputs.append(_pack_framed_input(sample, in_last, reset_before, stall_cycles, width))
        expected.append(_pack_peak_expected(result, in_last, width))
        if in_last:
            frame.clear()
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=width + 4,
        expected_record_width_bits=2 * width + 2,
        input_fields=_framed_input_fields(width),
        expected_fields=_peak_expected_fields(width),
        input_records=tuple(inputs),
        expected_records=tuple(expected),
    )


def _radar_scenario(
    scenario_id: str,
    scenario_class: str,
    seed: int,
    events: Sequence[tuple[int, bool, bool, int]],
    width: int,
    acc_width: int,
) -> OracleScenarioSpec:
    history = [0, 0, 0, 0]
    correlations: list[int] = []
    inputs: list[int] = []
    expected: list[int] = []
    for sample, in_last, reset_before, stall_cycles in events:
        if reset_before:
            history = [0, 0, 0, 0]
            correlations.clear()
        history = [signed(sample, width), *history[:3]]
        correlations.append(sum(value * coefficient for value, coefficient in zip(history, MATCHED_TEMPLATE)))
        result = detect_peak(correlations, PEAK_THRESHOLD)
        inputs.append(_pack_framed_input(sample, in_last, reset_before, stall_cycles, width))
        expected.append(_pack_peak_expected(result, in_last, acc_width))
        if in_last:
            history = [0, 0, 0, 0]
            correlations.clear()
            if stall_cycles > 0:
                fill_sample = signed((~sample) & ((1 << width) - 1), width)
                history = [fill_sample, *history[:3]]
                correlations.append(
                    sum(value * coefficient for value, coefficient in zip(history, MATCHED_TEMPLATE))
                )
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=width + 4,
        expected_record_width_bits=2 * acc_width + 2,
        input_fields=_framed_input_fields(width),
        expected_fields=_peak_expected_fields(acc_width),
        input_records=tuple(inputs),
        expected_records=tuple(expected),
    )


def _random_matched_events(width: int, seed: int) -> tuple[tuple[int, bool, int], ...]:
    randomizer = random.Random(seed)
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    return tuple(
        (randomizer.randint(minimum, maximum), index in {0, 9}, 2 if index in {5, 13} else 0)
        for index in range(16)
    )


def _random_peak_events(width: int, seed: int) -> tuple[tuple[int, bool, bool, int], ...]:
    randomizer = random.Random(seed)
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    return tuple(
        (randomizer.randint(minimum, maximum), index % 6 == 5, index == 0, 2 if index in {5, 11} else 0)
        for index in range(18)
    )


def _random_radar_events(width: int, seed: int) -> tuple[tuple[int, bool, bool, int], ...]:
    randomizer = random.Random(seed)
    minimum = -(1 << (width - 1))
    maximum = (1 << (width - 1)) - 1
    return tuple(
        (randomizer.randint(minimum, maximum), index % 8 == 7, index == 0, 2 if index in {7, 15} else 0)
        for index in range(24)
    )


def _validate_stall(stall_cycles: int) -> None:
    if not isinstance(stall_cycles, int) or isinstance(stall_cycles, bool) or not 0 <= stall_cycles <= 3:
        raise ValueError("signal oracle stall_cycles must fit two bits")


__all__ = [
    "MATCHED_TEMPLATE",
    "PEAK_THRESHOLD",
    "build_matched_filter_bundle",
    "build_peak_detector_bundle",
    "build_pulse_radar_bundle",
    "detect_peak",
    "matched_filter_outputs",
    "pulse_radar",
]
