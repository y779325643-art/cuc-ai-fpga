"""Evaluator-owned exact integer Q/K/V oracle, independent of the RTL machine."""

from __future__ import annotations

from fractions import Fraction

from .task import (TOKENS, INPUT_DIM, INPUT_ZERO, WEIGHTS, BIASES,
                   OUTPUT_DENOMINATORS, OUTPUT_ZEROS, HEAD_DIM)


def evaluate_token(values: list[int] | tuple[int, ...]) -> dict[str, tuple[int, ...]]:
    if len(values) != INPUT_DIM or any(type(x) is not int or not -128 <= x <= 127 for x in values):
        raise ValueError("one complete token of five signed INT8 values required")
    return {branch: tuple(max(-128, min(127, round(Fraction(
        bias + sum((value - INPUT_ZERO) * weight for value, weight in zip(values, row)),
        OUTPUT_DENOMINATORS[branch])) + OUTPUT_ZEROS[branch]))
        for row, bias in zip(weights, BIASES[branch])) for branch, weights in WEIGHTS.items()}


def evaluate(values: list[int] | tuple[int, ...]) -> dict[str, tuple[int, ...]]:
    if len(values) != TOKENS * INPUT_DIM:
        raise ValueError("two complete tokens required")
    projected = [evaluate_token(values[i:i + INPUT_DIM]) for i in range(0, len(values), INPUT_DIM)]
    return {branch: tuple(value for token in projected for value in token[branch]) for branch in WEIGHTS}


def pack_tensor(values: list[int] | tuple[int, ...], row_width: int) -> tuple[int, ...]:
    if type(row_width) is not int or row_width < 1 or len(values) % row_width:
        raise ValueError("complete positive-width rows required")
    if any(type(value) is not int or not -128 <= value <= 127 for value in values):
        raise ValueError("signed INT8 values required")
    beats = []
    for start in range(0, len(values), row_width):
        for offset in range(0, row_width, 2):
            valid = min(2, row_width - offset)
            beats.append((((1 << valid) - 1) << 16) | (values[start + offset] & 255) |
                         ((values[start + offset + 1] & 255) << 8 if valid == 2 else 0))
    return tuple(beats)


def unpack_tensor(beats: list[int] | tuple[int, ...], row_width: int) -> tuple[int, ...]:
    if type(row_width) is not int or row_width < 1 or len(beats) % ((row_width + 1) // 2):
        raise ValueError("complete positive-width rows required")
    result = []
    for index, beat in enumerate(beats):
        if type(beat) is not int or not 0 <= beat < 1 << 18:
            raise ValueError("18-bit packed values required")
        valid = min(2, row_width - 2 * (index % ((row_width + 1) // 2)))
        if beat >> 16 != (1 << valid) - 1 or valid == 1 and beat & 0xFF00:
            raise ValueError("invalid mask or nonzero tail lane")
        for lane in range(valid):
            raw = beat >> (8 * lane) & 255
            result.append(raw - 256 if raw >= 128 else raw)
    return tuple(result)


def packed_outputs(values: list[int] | tuple[int, ...]) -> dict[str, tuple[int, ...]]:
    return {branch: pack_tensor(projected, HEAD_DIM) for branch, projected in evaluate(values).items()}
