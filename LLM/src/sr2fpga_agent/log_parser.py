"""Log parsing and failure classification for lightweight RTL tools."""

from __future__ import annotations

import re
from collections import defaultdict


def classify_failure(log_text: str) -> str:
    """Classify a raw tool log into the V1 failure taxonomy."""
    text = log_text.lower()
    if "verilog reserved keyword" in text:
        return "rtl_reserved_identifier"
    if "%warning-" in text and "exiting due to" in text and "warning" in text:
        return "lint_warning_as_error"
    patterns = [
        ("syntax_error", ["syntax error", "parse error", "unexpected"]),
        ("module_not_found", ["unknown module type", "module not found", "can't resolve module"]),
        ("port_mismatch", ["port", "not declared", "does not exist", "is not a port"]),
        ("width_mismatch", ["width mismatch", "different width", "size mismatch"]),
        ("multiple_driver", ["multiple driver", "multiple drivers", "conflicting drivers"]),
        ("latch_inferred", ["latch inferred", "inferred latch"]),
        ("non_synthesizable_construct", ["not synthesizable", "unsupported cell type"]),
        ("testbench_timeout", ["timeout", "timed out"]),
        ("functional_mismatch", ["test_fail", "mismatch", "expected"]),
        ("reset_behavior_error", ["reset"]),
        ("clocking_error", ["clock"]),
        ("constraint_port_missing", ["get_ports", "no ports matched"]),
        ("synthesis_error", ["synthesis failed", "yosys failed"]),
        ("resource_overuse", ["resource", "overuse", "exceeds"]),
        ("timing_risk", ["timing", "slack", "critical path"]),
    ]
    for failure_type, needles in patterns:
        if any(needle in text for needle in needles):
            return failure_type
    return "unknown"


def parse_yosys_stats(log_text: str) -> dict[str, object]:
    """Extract resource-like counts from Yosys `stat` output."""
    cell_breakdown: dict[str, int] = {}
    cell_count = 0
    in_current_cell_section = False
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        if line.startswith("===") and line.endswith("==="):
            in_current_cell_section = False
            continue
        total_match = re.match(r"Number of cells:\s+(\d+)", line)
        if total_match:
            cell_count = int(total_match.group(1))
            in_current_cell_section = True
            continue
        current_total_match = re.match(r"(\d+)\s+cells$", line)
        if current_total_match:
            cell_count = int(current_total_match.group(1))
            in_current_cell_section = True
            continue

        cell_match = re.match(r"([A-Za-z0-9_$.\-]+)\s+(\d+)$", line)
        if cell_match:
            cell_breakdown[cell_match.group(1)] = int(cell_match.group(2))
            continue
        current_cell_match = re.match(r"(\d+)\s+([A-Za-z0-9_$.\-]+)$", line)
        if in_current_cell_section and current_cell_match:
            cell_breakdown[current_cell_match.group(2)] = int(current_cell_match.group(1))

    totals = defaultdict(int)
    for cell_name, count in cell_breakdown.items():
        upper = cell_name.upper()
        if "LUT" in upper:
            totals["lut"] += count
        if "DFF" in upper:
            totals["ff"] += count
        if "RAM" in upper or "BRAM" in upper:
            totals["bram"] += count
        if "DSP" in upper or "MAC" in upper or "MULT" in upper:
            totals["dsp"] += count

    return {
        "cell_count": cell_count,
        "cell_breakdown": cell_breakdown,
        "lut": totals["lut"],
        "ff": totals["ff"],
        "bram": totals["bram"],
        "dsp": totals["dsp"],
    }
