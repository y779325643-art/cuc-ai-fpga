"""Independent 5x5 image references and evaluator-local oracle bundles."""

from __future__ import annotations

from dataclasses import dataclass
import random
from pathlib import Path
from typing import Sequence

from sr2fpga_agent.oracles.bundle import write_oracle_bundle
from sr2fpga_agent.oracles.types import OracleBundle, OracleField, OracleScenarioSpec


IMAGE_WIDTH = 5
IMAGE_HEIGHT = 5
IMAGE_THRESHOLD = 100

GX = ((-1, 0, 1), (-2, 0, 2), (-1, 0, 1))
GY = ((-1, -2, -1), (0, 0, 0), (1, 2, 1))

_WITHHELD_SEEDS = {
    "sobel_hidden": 0xE7037ED1A0B428DB7137449123EF65CD,
    "sobel_randomized": 0x8EBC6AF09C88C6E3D5A79147930AA725,
    "sobel_stress": 0x589965CC75374CC35E2D58D8B3BCDEF1,
    "vision_hidden": 0x1D8E4E27C47D124F9E3779B97F4A7C15,
    "vision_randomized": 0xEB44ACCAB455D165BF58476D1CE4E5B9,
    "vision_stress": 0xA4093822299F31D0D1342543DE82EF95,
}


@dataclass(frozen=True)
class SobelResult:
    edges: tuple[int, ...]
    axes: tuple[int, ...]


@dataclass(frozen=True)
class VisionDefectResult:
    edges: tuple[int, ...]
    axes: tuple[int, ...]
    defect_present: bool
    first_x: int
    first_y: int


@dataclass(frozen=True)
class _ImageOperation:
    frame: tuple[tuple[int, ...], ...]
    pixel_count: int = IMAGE_WIDTH * IMAGE_HEIGHT
    reset_before: bool = False
    last_index: int | None = IMAGE_WIDTH * IMAGE_HEIGHT - 1
    stalls: tuple[tuple[int, int], ...] = ()


def sobel_frame(frame: Sequence[Sequence[int]], threshold: int) -> SobelResult:
    """Return row-major threshold and dominant-axis bits with a zero border."""

    pixels = _validate_5x5_u8(frame)
    if not isinstance(threshold, int) or isinstance(threshold, bool) or not 0 <= threshold <= 4080:
        raise ValueError("image threshold must be an integer in [0, 4080]")
    edges = [0] * (IMAGE_WIDTH * IMAGE_HEIGHT)
    axes = [0] * (IMAGE_WIDTH * IMAGE_HEIGHT)
    for y in range(1, IMAGE_HEIGHT - 1):
        for x in range(1, IMAGE_WIDTH - 1):
            gx = sum(
                pixels[y + dy - 1][x + dx - 1] * GX[dy][dx]
                for dy in range(3)
                for dx in range(3)
            )
            gy = sum(
                pixels[y + dy - 1][x + dx - 1] * GY[dy][dx]
                for dy in range(3)
                for dx in range(3)
            )
            index = y * IMAGE_WIDTH + x
            edges[index] = int(abs(gx) + abs(gy) >= threshold)
            axes[index] = int(abs(gx) >= abs(gy))
    return SobelResult(tuple(edges), tuple(axes))


def vision_defect_frame(frame: Sequence[Sequence[int]], threshold: int) -> VisionDefectResult:
    """Report the first thresholded pixel; no CCA or bounding-box semantics are implied."""

    sobel = sobel_frame(frame, threshold)
    first_index = next((index for index, edge in enumerate(sobel.edges) if edge), None)
    if first_index is None:
        return VisionDefectResult(sobel.edges, sobel.axes, False, 0, 0)
    return VisionDefectResult(
        sobel.edges,
        sobel.axes,
        True,
        first_index % IMAGE_WIDTH,
        first_index // IMAGE_WIDTH,
    )


def build_sobel_threshold_bundle(width: int, root: Path) -> OracleBundle:
    _validate_pixel_width(width)
    scenarios = (
        _scenario(
            scenario_id="sobel_public_flat_vertical",
            scenario_class="public_smoke",
            seed=0,
            operations=(
                _ImageOperation(_flat_frame(0), reset_before=True),
                _ImageOperation(_shifted_vertical_step_frame(25)),
            ),
            vision=False,
        ),
        _scenario(
            scenario_id="sobel_hidden_horizontal_maximum",
            scenario_class="hidden_deterministic",
            seed=_WITHHELD_SEEDS["sobel_hidden"],
            operations=(_ImageOperation(_horizontal_step_frame(25), reset_before=True, last_index=23),),
            vision=False,
        ),
        _scenario(
            scenario_id="sobel_randomized_seeded",
            scenario_class="randomized_fixed_seed",
            seed=_WITHHELD_SEEDS["sobel_randomized"],
            operations=tuple(
                _ImageOperation(frame, reset_before=index == 0)
                for index, frame in enumerate(_random_frames(_WITHHELD_SEEDS["sobel_randomized"], 2))
            ),
            vision=False,
        ),
        _scenario(
            scenario_id="sobel_stress_reset_stall",
            scenario_class="stress",
            seed=_WITHHELD_SEEDS["sobel_stress"],
            operations=(
                _ImageOperation(
                    _shifted_vertical_step_frame(25),
                    pixel_count=10,
                    reset_before=True,
                    last_index=None,
                ),
                _ImageOperation(
                    _shifted_vertical_step_frame(25),
                    reset_before=True,
                    stalls=((12, 3),),
                ),
            ),
            vision=False,
        ),
    )
    return _write_bundle(root, "sobel_threshold", scenarios)


def build_vision_defect_bundle(width: int, root: Path) -> OracleBundle:
    _validate_pixel_width(width)
    scenarios = (
        _scenario(
            scenario_id="vision_public_absent_present",
            scenario_class="public_smoke",
            seed=0,
            operations=(
                _ImageOperation(_flat_frame(0), reset_before=True),
                _ImageOperation(_shifted_vertical_step_frame(25)),
            ),
            vision=True,
        ),
        _scenario(
            scenario_id="vision_hidden_order_threshold",
            scenario_class="hidden_deterministic",
            seed=_WITHHELD_SEEDS["vision_hidden"],
            operations=(_ImageOperation(_horizontal_step_frame(25), reset_before=True, last_index=23),),
            vision=True,
        ),
        _scenario(
            scenario_id="vision_randomized_seeded",
            scenario_class="randomized_fixed_seed",
            seed=_WITHHELD_SEEDS["vision_randomized"],
            operations=tuple(
                _ImageOperation(frame, reset_before=index == 0)
                for index, frame in enumerate(_random_frames(_WITHHELD_SEEDS["vision_randomized"], 2))
            ),
            vision=True,
        ),
        _scenario(
            scenario_id="vision_stress_reset_stall",
            scenario_class="stress",
            seed=_WITHHELD_SEEDS["vision_stress"],
            operations=(
                _ImageOperation(
                    _shifted_vertical_step_frame(25),
                    pixel_count=10,
                    reset_before=True,
                    last_index=None,
                ),
                _ImageOperation(
                    _shifted_vertical_step_frame(25),
                    reset_before=True,
                    stalls=((12, 3),),
                ),
            ),
            vision=True,
        ),
    )
    return _write_bundle(root, "p_vision_defect_core", scenarios)


def _write_bundle(root: Path, family_id: str, scenarios: tuple[OracleScenarioSpec, ...]) -> OracleBundle:
    return write_oracle_bundle(
        root=Path(root),
        family_id=family_id,
        reference_model="python_image_reference",
        reference_version="1.1.0",
        task_parameters={
            "image_width": IMAGE_WIDTH,
            "image_height": IMAGE_HEIGHT,
            "pixel_width": 8,
            "threshold": IMAGE_THRESHOLD,
            "border": "one_pixel_zero",
            "magnitude": "abs_gx_plus_abs_gy",
            "threshold_comparison": "greater_or_equal",
            "axis_tie": "gx",
            "defect_report": "first_row_major_thresholded_pixel",
            "connected_components": False,
            "bounding_boxes": False,
            "frame_contract": "fixed_5x5_row_major",
            "operation_record": "pixel_with_reset_drain_and_output_count_padding",
        },
        scenarios=scenarios,
    )


def _scenario(
    *,
    scenario_id: str,
    scenario_class: str,
    seed: int,
    operations: Sequence[_ImageOperation],
    vision: bool,
) -> OracleScenarioSpec:
    inputs: list[int] = []
    expected_outputs: list[int] = []
    for operation in operations:
        pixels = _validate_5x5_u8(operation.frame)
        _validate_operation(operation)
        stalls = dict(operation.stalls)
        result = vision_defect_frame(pixels, IMAGE_THRESHOLD)
        drain_target = len(expected_outputs)
        flat_pixels = tuple(value for row in pixels for value in row)
        for index, pixel in enumerate(flat_pixels[: operation.pixel_count]):
            stall_cycles = stalls.get(index, 0)
            _validate_stall(stall_cycles)
            inputs.append(
                pixel
                | (int(index == operation.last_index) << 8)
                | (int(operation.reset_before and index == 0) << 9)
                | (stall_cycles << 10)
                | (drain_target << 12)
            )
        output_count = _operation_output_count(operation)
        for index in range(output_count):
            out_last = int(index == 24)
            if vision:
                expected_outputs.append(
                    result.edges[index]
                    | (out_last << 1)
                    | (int(result.defect_present and out_last) << 2)
                    | ((result.first_x if out_last else 0) << 3)
                    | ((result.first_y if out_last else 0) << 19)
                    | (1 << 35)
                )
            else:
                expected_outputs.append(
                    result.edges[index] | (result.axes[index] << 1) | (out_last << 2) | (1 << 3)
                )
    if len(expected_outputs) > len(inputs):
        raise ValueError("image operation outputs cannot exceed input record capacity")
    expected = expected_outputs + [0] * (len(inputs) - len(expected_outputs))
    expected_fields = (
        (
            OracleField("edge", 0, 0, False),
            OracleField("out_last", 1, 1, False),
            OracleField("defect_present", 2, 2, False),
            OracleField("first_x", 18, 3, False),
            OracleField("first_y", 34, 19, False),
            OracleField("expect_output", 35, 35, False),
        )
        if vision
        else (
            OracleField("edge", 0, 0, False),
            OracleField("axis", 1, 1, False),
            OracleField("out_last", 2, 2, False),
            OracleField("expect_output", 3, 3, False),
        )
    )
    return OracleScenarioSpec(
        scenario_id=scenario_id,
        scenario_class=scenario_class,
        seed=seed,
        input_record_width_bits=24,
        expected_record_width_bits=36 if vision else 4,
        input_fields=(
            OracleField("pixel", 7, 0, False),
            OracleField("in_last", 8, 8, False),
            OracleField("reset_before", 9, 9, False),
            OracleField("stall_cycles", 11, 10, False),
            OracleField("drain_target", 23, 12, False),
        ),
        expected_fields=expected_fields,
        input_records=tuple(inputs),
        expected_records=tuple(expected),
    )


def _validate_5x5_u8(frame: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    if not isinstance(frame, Sequence) or isinstance(frame, (str, bytes)) or len(frame) != IMAGE_HEIGHT:
        raise ValueError("image frame must contain exactly five rows")
    rows: list[tuple[int, ...]] = []
    for row in frame:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)) or len(row) != IMAGE_WIDTH:
            raise ValueError("each image row must contain exactly five pixels")
        normalized: list[int] = []
        for pixel in row:
            if not isinstance(pixel, int) or isinstance(pixel, bool) or not 0 <= pixel <= 255:
                raise ValueError("image pixels must be unsigned eight-bit integers")
            normalized.append(pixel)
        rows.append(tuple(normalized))
    return tuple(rows)


def _flat_frame(level: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(level for _ in range(IMAGE_WIDTH)) for _ in range(IMAGE_HEIGHT))


def _vertical_step_frame(level: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(0 if x < 2 else level for x in range(IMAGE_WIDTH)) for _ in range(IMAGE_HEIGHT))


def _horizontal_step_frame(level: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(0 if y < 2 else level for _ in range(IMAGE_WIDTH)) for y in range(IMAGE_HEIGHT))


def _shifted_vertical_step_frame(level: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(0 if x < 3 else level for x in range(IMAGE_WIDTH)) for _ in range(IMAGE_HEIGHT))


def _random_frames(seed: int, count: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    randomizer = random.Random(seed)
    return tuple(
        tuple(
            tuple(randomizer.randint(0, 255) for _ in range(IMAGE_WIDTH))
            for _ in range(IMAGE_HEIGHT)
        )
        for _ in range(count)
    )


def _validate_pixel_width(width: int) -> None:
    if width != 8:
        raise ValueError("image oracle families require eight-bit pixels")


def _validate_stall(stall_cycles: int) -> None:
    if not isinstance(stall_cycles, int) or isinstance(stall_cycles, bool) or not 0 <= stall_cycles <= 3:
        raise ValueError("image oracle stall_cycles must fit two bits")


def _validate_operation(operation: _ImageOperation) -> None:
    if operation.pixel_count not in {10, IMAGE_WIDTH * IMAGE_HEIGHT}:
        raise ValueError("image operations must be a full 5x5 frame or a ten-pixel partial frame")
    if operation.pixel_count < IMAGE_WIDTH * IMAGE_HEIGHT and operation.last_index is not None:
        raise ValueError("partial image operations cannot assert in_last")
    if operation.last_index is not None and not 0 <= operation.last_index < operation.pixel_count:
        raise ValueError("image in_last position must address an emitted pixel")
    stall_indexes = [index for index, _ in operation.stalls]
    if len(stall_indexes) != len(set(stall_indexes)):
        raise ValueError("image operation stall indexes must be unique")
    for index, stall_cycles in operation.stalls:
        if not 0 <= index < operation.pixel_count - 1:
            raise ValueError("image output stalls require a pending next input pixel")
        _validate_stall(stall_cycles)


def _operation_output_count(operation: _ImageOperation) -> int:
    if operation.pixel_count == 10:
        return 5
    return 25 if operation.last_index == 24 else 20


__all__ = [
    "GX",
    "GY",
    "IMAGE_HEIGHT",
    "IMAGE_THRESHOLD",
    "IMAGE_WIDTH",
    "SobelResult",
    "VisionDefectResult",
    "build_sobel_threshold_bundle",
    "build_vision_defect_bundle",
    "sobel_frame",
    "vision_defect_frame",
]
