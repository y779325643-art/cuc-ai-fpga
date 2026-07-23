"""Log parsing and failure classification for lightweight RTL tools."""

from __future__ import annotations

import json
import re
from collections import defaultdict


_VERILATOR_WARNING_TAXONOMY = {
    "WIDTH": "width_mismatch",
    "WIDTHTRUNC": "width_mismatch",
    "UNDRIVEN": "undriven_signal",
    "UNUSEDSIGNAL": "unused_signal",
    "IMPLICIT": "undeclared_signal",
    "LATCH": "latch_inferred",
}


def parse_test_fail_mismatches(log_text: str) -> list[dict[str, object]]:
    """Extract available key/value fields from diagnostic TEST_FAIL lines."""
    structured: list[dict[str, object]] = []
    legacy: list[dict[str, object]] = []
    for raw_line in log_text.splitlines():
        if raw_line.startswith("SR2FPGA_MISMATCH "):
            try:
                payload = json.loads(raw_line.removeprefix("SR2FPGA_MISMATCH "))
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(payload, dict):
                detail = {
                    key: payload[key]
                    for key in ("scenario_id", "class", "item_index", "expected", "actual")
                    if key in payload
                }
                if detail:
                    structured.append(detail)
            continue
        if "TEST_FAIL" not in raw_line:
            continue
        detail: dict[str, object] = {}
        signal = re.search(r"\bsignal=([^\s]+)", raw_line)
        cycle = re.search(r"\bcycle=(\d+)", raw_line)
        expected = re.search(
            r"\bexpected(?:=|\s+)(.+?)(?=\s+(?:actual|got)(?:=|\s+)|$)",
            raw_line,
        )
        actual = re.search(r"\b(?:actual|got)(?:=|\s+)(.+?)$", raw_line)
        if signal:
            detail["signal"] = signal.group(1)
        if cycle:
            detail["cycle"] = int(cycle.group(1))
        if expected:
            detail["expected"] = expected.group(1).strip()
        if actual:
            detail["actual"] = actual.group(1).strip()
        if detail:
            legacy.append(detail)
    return structured or legacy


def parse_tool_warnings(log_text: str) -> list[dict[str, str]]:
    """Extract recognized Verilator and Yosys warnings with failure taxonomy."""
    warnings: list[dict[str, str]] = []
    for warning_class in re.findall(r"%Warning-([A-Za-z0-9_]+):", log_text):
        normalized = warning_class.upper()
        failure_type = _VERILATOR_WARNING_TAXONOMY.get(normalized)
        if failure_type is not None:
            warnings.append({"warning_class": normalized, "failure_type": failure_type})
    for raw_line in log_text.splitlines():
        if not re.match(r"\s*Warning:", raw_line, flags=re.IGNORECASE):
            continue
        text = raw_line.lower()
        failure_type = "unknown"
        if "never used" in text or "not used" in text:
            failure_type = "unused_signal"
        elif "multiple" in text and "driver" in text:
            failure_type = "multiple_driver"
        elif "latch" in text:
            failure_type = "latch_inferred"
        elif "width" in text or "truncat" in text:
            failure_type = "width_mismatch"
        warnings.append({"warning_class": "YOSYS", "failure_type": failure_type})
    return warnings


def classify_failure(log_text: str) -> str:
    """Classify a raw tool log into the V1 failure taxonomy."""
    text = log_text.lower()
    if "verilog reserved keyword" in text:
        return "rtl_reserved_identifier"
    if "testbench_stimulus_reaccept_risk" in text or "stimulus reaccept" in text:
        return "testbench_stimulus_reaccept_risk"
    if "testbench_observation_race" in text or "testbench observation race" in text:
        return "testbench_observation_race"
    if "testbench_internal_signal_access" in text or "dut internal signal access" in text:
        return "testbench_internal_signal_access"
    if "testbench_missing_functional_oracle" in text or "missing functional oracle" in text:
        return "testbench_missing_functional_oracle"
    if "%error-pinnotfound" in text and "parameter not found" in text:
        return "parameter_mismatch"
    if "signal definition not found" in text or "implicit disabled" in text or "%warning-implicit" in text:
        return "undeclared_signal"
    if (
        ("i don't know how to elaborate" in text or "elaboration failed" in text)
        and "{" in text
        and "}" in text
    ):
        return "testbench_simulator_compatibility"
    if "%warning-" in text and "exiting due to" in text and "warning" in text:
        return "lint_warning_as_error"
    if (
        ("timeout waiting for output" in text and "iteration" in text)
        or "timeout waiting for input handshake" in text
    ):
        return "testbench_handshake_timeout"
    patterns = [
        ("syntax_error", ["syntax error", "parse error", "unexpected"]),
        ("module_not_found", ["unknown module type", "module not found", "can't resolve module"]),
        ("port_mismatch", [" port ", "not declared", "does not exist", "is not a port"]),
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
