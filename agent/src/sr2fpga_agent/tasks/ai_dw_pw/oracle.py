"""Evaluator-owned, exact integer reference. Never imported by generated RTL."""

from __future__ import annotations

from fractions import Fraction

from .task import (HEIGHT, WIDTH, CIN, COUT, DW_WEIGHTS, DW_BIAS, PW_WEIGHTS,
                   PW_BIAS, INPUT_ZERO, MID_ZERO, OUTPUT_DENOMINATORS, OUTPUT_ZEROS)


def nearest_even(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("positive denominator required")
    # Python's Fraction round implements exact signed round-to-nearest/ties-even.
    return round(Fraction(numerator, denominator))


def saturate(value: int) -> int:
    return max(-128, min(127, value))


def evaluate(values: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    """Flat NHWC raw INT8 input to flat NHWC output, no physical mask lanes."""
    if len(values) != HEIGHT * WIDTH * CIN or any(type(x) is not int or not -128 <= x <= 127 for x in values):
        raise ValueError("expected exactly 60 signed INT8 values")
    result = []
    for h in range(HEIGHT):
        for w in range(WIDTH):
            intermediate = []
            for c in range(CIN):
                acc = DW_BIAS[c]
                for kh in range(3):
                    for kw in range(3):
                        ih, iw = h + kh - 1, w + kw - 1
                        raw = values[(ih * WIDTH + iw) * CIN + c] if 0 <= ih < HEIGHT and 0 <= iw < WIDTH else INPUT_ZERO
                        acc += (raw - INPUT_ZERO) * DW_WEIGHTS[c][kh][kw]
                intermediate.append(max(MID_ZERO, saturate(nearest_even(acc, 2) + MID_ZERO)))
            for o in range(COUT):
                acc = PW_BIAS[o] + sum((intermediate[c] - MID_ZERO) * PW_WEIGHTS[o][c] for c in range(CIN))
                result.append(saturate(nearest_even(acc, OUTPUT_DENOMINATORS[o]) + OUTPUT_ZEROS[o]))
    return tuple(result)


def pack_tensor(values: list[int] | tuple[int, ...], channels: int) -> tuple[int, ...]:
    """18-bit beats: [mask1,mask0,lane1[7:0],lane0[7:0]]."""
    if channels < 1 or len(values) % channels or any(type(x) is not int or not -128 <= x <= 127 for x in values):
        raise ValueError("complete signed INT8 pixels required")
    beats = []
    for base in range(0, len(values), channels):
        for c in range(0, channels, 2):
            valid = min(2, channels - c)
            beats.append(((1 << valid) - 1) << 16 | (values[base + c] & 255) |
                         ((values[base + c + 1] & 255) << 8 if valid == 2 else 0))
    return tuple(beats)


def unpack_tensor(beats: list[int] | tuple[int, ...], channels: int) -> tuple[int, ...]:
    groups = (channels + 1) // 2
    if channels < 1 or len(beats) % groups:
        raise ValueError("complete pixels required")
    result = []
    for i, beat in enumerate(beats):
        if type(beat) is not int or not 0 <= beat < (1 << 18):
            raise ValueError("18-bit beats required")
        valid = min(2, channels - 2 * (i % groups))
        if beat >> 16 != (1 << valid) - 1 or valid == 1 and beat & 0xFF00:
            raise ValueError("invalid mask or nonzero invalid lane")
        for lane in range(valid):
            raw = (beat >> (8 * lane)) & 255
            result.append(raw - 256 if raw >= 128 else raw)
    return tuple(result)
