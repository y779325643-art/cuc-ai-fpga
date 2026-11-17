"""Evaluator-owned integer FFN oracle, separate from RTL state machines."""

from __future__ import annotations

from fractions import Fraction

from .task import (TOKENS, DIN, GATE_WEIGHTS, UP_WEIGHTS, DOWN_WEIGHTS,
                   GATE_BIAS, UP_BIAS, DOWN_BIAS, SILU_LUT)


def nearest_even(value: int, divisor: int) -> int:
    if type(value) is not int or type(divisor) is not int or divisor <= 0:
        raise ValueError("integer numerator and positive integer divisor required")
    return round(Fraction(value, divisor))


def saturate(value: int) -> int:
    return max(-128, min(127, value))


def evaluate_token(values: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    """One token is independent; no full-frame buffering is required of a DUT."""
    if len(values) != DIN or any(type(x) is not int or not -128 <= x <= 127 for x in values):
        raise ValueError("expected five signed INT8 token values")
    gate = [saturate(nearest_even(sum(a * b for a, b in zip(values, row)) + bias, 4))
            for row, bias in zip(GATE_WEIGHTS, GATE_BIAS)]
    up = [saturate(nearest_even(sum(a * b for a, b in zip(values, row)) + bias, 4))
          for row, bias in zip(UP_WEIGHTS, UP_BIAS)]
    product = [saturate(nearest_even(SILU_LUT[g + 128] * u, 4)) for g, u in zip(gate, up)]
    return tuple(saturate(nearest_even(sum(a * b for a, b in zip(product, row)) + bias, 4) + values[channel])
                 for channel, (row, bias) in enumerate(zip(DOWN_WEIGHTS, DOWN_BIAS)))


def evaluate(values: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    if len(values) != TOKENS * DIN:
        raise ValueError("expected ten signed INT8 input values")
    return tuple(value for start in range(0, len(values), DIN)
                 for value in evaluate_token(values[start:start + DIN]))


def pack_tensor(values: list[int] | tuple[int, ...], channels: int = DIN) -> tuple[int, ...]:
    if type(channels) is not int or channels <= 0 or len(values) % channels:
        raise ValueError("complete positive-channel tensors required")
    if any(type(x) is not int or not -128 <= x <= 127 for x in values):
        raise ValueError("signed INT8 values required")
    result = []
    for base in range(0, len(values), channels):
        for channel in range(0, channels, 2):
            count = min(2, channels - channel)
            result.append(((1 << count) - 1) << 16 | (values[base + channel] & 255)
                          | ((values[base + channel + 1] & 255) << 8 if count == 2 else 0))
    return tuple(result)


def unpack_tensor(beats: list[int] | tuple[int, ...], channels: int = DIN) -> tuple[int, ...]:
    if type(channels) is not int or channels <= 0 or len(beats) % ((channels + 1) // 2):
        raise ValueError("complete positive-channel tensor beats required")
    result = []
    groups = (channels + 1) // 2
    for index, beat in enumerate(beats):
        count = min(2, channels - 2 * (index % groups))
        if type(beat) is not int or not 0 <= beat < 2**18 or beat >> 16 != (1 << count) - 1:
            raise ValueError("invalid packed tensor mask or width")
        if count == 1 and beat & 0xFF00:
            raise ValueError("invalid tail lane must be raw0")
        for lane in range(count):
            raw = beat >> (8 * lane) & 255
            result.append(raw - 256 if raw >= 128 else raw)
    return tuple(result)
