"""Evaluator-owned integer/Fraction model; no RTL implementation is imported."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .task import (EXP_LUT, HEAD_DIM, KV_HEADS, MAX_CONTEXT, QUERY_HEADS,
                   SCORE_DENOMINATOR, SCORE_LIMIT, SCORE_NUMERATOR)


def nearest_even(numerator: int, denominator: int) -> int:
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise ValueError("rounding requires an integer numerator and positive integer denominator")
    return round(Fraction(numerator, denominator))


def _raw(values, size: int) -> tuple[int, ...]:
    result = tuple(values)
    if len(result) != size or any(type(value) is not int or not -128 <= value <= 127 for value in result):
        raise ValueError("invalid signed INT8 frame")
    return result


@dataclass(frozen=True)
class DecodeInput:
    query: tuple[int, ...]
    key: tuple[int, ...]
    value: tuple[int, ...]

    def __post_init__(self):
        _raw(self.query, QUERY_HEADS * HEAD_DIM)
        _raw(self.key, KV_HEADS * HEAD_DIM)
        _raw(self.value, KV_HEADS * HEAD_DIM)


class DecodeOracle:
    """Past K/V remain live; an invocation appends exactly one current token."""

    def __init__(self):
        self.keys: list[tuple[int, ...]] = []
        self.values: list[tuple[int, ...]] = []

    def reset(self) -> None:
        self.keys.clear()
        self.values.clear()

    @property
    def valid_length(self) -> int:
        return len(self.keys)

    def decode(self, command: DecodeInput) -> tuple[int, ...]:
        if self.valid_length >= MAX_CONTEXT:
            raise ValueError("KV cache full: reset is required before another append")
        query = _raw(command.query, QUERY_HEADS * HEAD_DIM)
        key = _raw(command.key, KV_HEADS * HEAD_DIM)
        value = _raw(command.value, KV_HEADS * HEAD_DIM)
        self.keys.append(key)
        self.values.append(value)
        result = []
        for head in range(QUERY_HEADS):
            group = head // (QUERY_HEADS // KV_HEADS)
            q = query[head * HEAD_DIM:(head + 1) * HEAD_DIM]
            scores = [max(-SCORE_LIMIT, min(SCORE_LIMIT, nearest_even(
                sum(a * b for a, b in zip(q, key[group * HEAD_DIM:(group + 1) * HEAD_DIM])) *
                SCORE_NUMERATOR, SCORE_DENOMINATOR)))
                for key in self.keys]
            maximum = max(scores)
            weights = [EXP_LUT[maximum - score] for score in scores]
            denominator = sum(weights)
            for channel in range(HEAD_DIM):
                numerator = sum(weight * value[group * HEAD_DIM + channel]
                                for weight, value in zip(weights, self.values))
                result.append(max(-128, min(127, nearest_even(numerator, denominator))))
        return tuple(result)


def pack_vectors(values, heads: int) -> tuple[int, ...]:
    """Two lanes, head-local tail: low lane first; mask is bits 17:16."""
    raw = _raw(values, heads * HEAD_DIM)
    result = []
    for head in range(heads):
        row = raw[head * HEAD_DIM:(head + 1) * HEAD_DIM]
        result.extend((0x30000 | (row[0] & 255) | ((row[1] & 255) << 8), 0x10000 | (row[2] & 255)))
    return tuple(result)


def unpack_vectors(beats, heads: int) -> tuple[int, ...]:
    packed = tuple(beats)
    if len(packed) != heads * 2:
        raise ValueError("wrong head-local beat count")
    result = []
    for index, beat in enumerate(packed):
        if type(beat) is not int or not 0 <= beat < (1 << 18):
            raise ValueError("packed payload outside eighteen bits")
        if beat >> 16 != (3 if index % 2 == 0 else 1) or (index % 2 and beat & 0xFF00):
            raise ValueError("invalid tail mask or nonzero invalid lane")
        result.extend((value - 256 if value >= 128 else value)
                      for value in ((beat & 255, (beat >> 8) & 255) if index % 2 == 0 else (beat & 255,)))
    return tuple(result)
