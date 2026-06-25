"""Semantic trace helpers for valid-ready simulation logs."""

from __future__ import annotations

import re
from typing import Any


TRACE_GROUPS = {
    "input_accept": "input_accepts",
    "join_output": "join_outputs",
    "acc_output": "acc_outputs",
    "output": "outputs",
}


def parse_semantic_trace(log_text: str) -> dict[str, list[dict[str, int]]]:
    """Parse structured TRACE lines emitted by diagnostic testbenches."""
    trace: dict[str, list[dict[str, int]]] = {
        "input_accepts": [],
        "join_outputs": [],
        "acc_outputs": [],
        "outputs": [],
    }
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        match = re.match(r"^TRACE\s+([A-Za-z0-9_]+)\s+(.*)$", line)
        if not match:
            continue
        group = TRACE_GROUPS.get(match.group(1))
        if group is None:
            continue
        trace[group].append(_parse_trace_fields(match.group(2)))
    return trace


def summarize_semantic_trace(trace: dict[str, list[dict[str, int]]]) -> dict[str, Any]:
    """Return compact counts and the first observed output mismatch."""
    first_mismatch = None
    for output in trace.get("outputs", []):
        if "expected" not in output or "actual" not in output:
            continue
        if output["expected"] == output["actual"]:
            continue
        first_mismatch = {
            "idx": output.get("idx", -1),
            "expected": output["expected"],
            "actual": output["actual"],
            "delta": output["actual"] - output["expected"],
        }
        break
    return {
        "input_accept_count": len(trace.get("input_accepts", [])),
        "join_output_count": len(trace.get("join_outputs", [])),
        "acc_output_count": len(trace.get("acc_outputs", [])),
        "output_count": len(trace.get("outputs", [])),
        "first_output_mismatch": first_mismatch,
    }


def diagnose_semantic_trace(trace: dict[str, list[dict[str, int]]]) -> dict[str, Any]:
    """Identify common semantic trace failure patterns."""
    summary = summarize_semantic_trace(trace)
    duplicates = _duplicate_input_accepts(trace.get("input_accepts", []))
    primary_issue = "none"
    if duplicates:
        primary_issue = "stimulus_reaccepted_while_valid_held"
    elif summary["first_output_mismatch"] is not None:
        primary_issue = "output_mismatch"
    return {
        **summary,
        "primary_issue": primary_issue,
        "duplicate_input_accepts": duplicates,
    }


def _duplicate_input_accepts(input_accepts: list[dict[str, int]]) -> list[dict[str, int]]:
    duplicates: list[dict[str, int]] = []
    previous_by_lane: dict[int, dict[str, int]] = {}
    for event in input_accepts:
        lane = event.get("lane")
        data = event.get("data")
        cycle = event.get("cycle")
        if lane is None or data is None or cycle is None:
            continue
        previous = previous_by_lane.get(lane)
        if previous is not None and previous.get("data") == data:
            duplicates.append(
                {
                    "lane": lane,
                    "data": data,
                    "first_cycle": previous.get("cycle", -1),
                    "repeat_cycle": cycle,
                }
            )
        previous_by_lane[lane] = event
    return duplicates


def _parse_trace_fields(field_text: str) -> dict[str, int]:
    fields: dict[str, int] = {}
    for key, value in re.findall(r"([A-Za-z0-9_]+)=(-?\d+)", field_text):
        fields[key] = int(value)
    return fields
