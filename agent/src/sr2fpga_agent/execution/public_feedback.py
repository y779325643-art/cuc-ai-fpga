"""Bounded public diagnostics; raw tool and checker text stays evaluator-owned."""
from __future__ import annotations

import copy
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence

from sr2fpga_agent.models import ToolResult


FEEDBACK_REVISION = "pc21-public-feedback-v2"
MAX_DIAGNOSTICS = 8
MAX_LINE = 1_000_000
_MAX_LOG_CHARACTERS = 65_536
_SOURCE_PATH = re.compile(r"rtl/[A-Za-z0-9_-][A-Za-z0-9_./-]*\.(?:v|sv)\Z")
_LOCATION = re.compile(r"(?P<file>.+?):(?P<line>[1-9][0-9]{0,6}):(?P<message>[^\r\n]*)\Z")

# Hints are complete literals, never interpolated from logs, identifiers or vectors.
HINTS = {
    "syntax_error": "Check HDL syntax at the candidate source location.",
    "unsupported_parameter_array": "Replace unpacked parameter/localparam arrays with supported constant expressions or case selections.",
    "undeclared_signal": "Declare candidate signals explicitly and check their scope.",
    "port_connection": "Check candidate module port names, directions and connection widths.",
    "parser_failure": "Check the candidate RTL against the declared HDL tool subset.",
    "compile_failure": "Check candidate RTL syntax and compatibility with the declared simulator.",
    "output_mismatch": "Check public arithmetic, tensor order, output masks and transaction ordering.",
    "stalled_output_changed": "Hold output valid and payload stable until the ready/valid transfer completes.",
    "stalled_input_changed": "Check input ready/valid handling and stalled-token stability.",
    "reset_output_valid": "Clear output-valid state at the reset behavior required by the public task.",
    "transaction_overlap": "Keep invocation boundaries and pending outputs consistent with the public task.",
    "completion_bound": "Ensure the public operation completes within its declared cycle bound.",
    "cache_backpressure": "Apply the public cache-capacity backpressure rule to every input stream.",
    "input_beat_count": "Check the public number and ordering of input tensor beats.",
    "unexpected_output": "Emit outputs only when the corresponding public transaction is available.",
    "trace_invalid": "Check that candidate outputs remain defined and satisfy the public signal widths.",
    "completion_incomplete": "Check completion, final handshakes and reset cancellation against the public task.",
    "functional_mismatch": "Check candidate behavior against the public arithmetic and ready/valid requirements.",
}
_SOURCE_CATEGORIES = {"syntax_error", "unsupported_parameter_array", "undeclared_signal", "port_connection",
                      "parser_failure", "compile_failure"}


def _diagnostic(stage: str, category: str, **location: Any) -> dict[str, Any]:
    return {"stage": stage, "category": category, "hint": HINTS[category], **location}


def _safe_source_path(value: Any) -> bool:
    return (isinstance(value, str) and len(value) <= 240 and _SOURCE_PATH.fullmatch(value) is not None
            and all(part not in {".", ".."} for part in value.split("/")))


def validate_diagnostics(values: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Validate restored public values without trusting arbitrary artifact text."""
    if not isinstance(values, (tuple, list)) or len(values) > MAX_DIAGNOSTICS:
        raise ValueError("invalid public diagnostic collection")
    result = []
    for item in values:
        if not isinstance(item, dict) or set(item) - {"stage", "category", "hint", "candidate_file", "line", "stream"}:
            raise ValueError("invalid public diagnostic fields")
        if (item.get("stage") not in {"parser", "compile", "functional"}
                or item.get("category") not in HINTS or item.get("hint") != HINTS[item["category"]]):
            raise ValueError("invalid public diagnostic classification")
        if ((item["stage"] == "functional") == (item["category"] in _SOURCE_CATEGORIES)
                or item["category"] == "parser_failure" and item["stage"] != "parser"
                or item["category"] == "compile_failure" and item["stage"] != "compile"):
            raise ValueError("public diagnostic stage and category disagree")
        if ("candidate_file" in item) != ("line" in item):
            raise ValueError("public diagnostic locations require both file and line")
        if "candidate_file" in item and (not _safe_source_path(item["candidate_file"])
                or type(item["line"]) is not int or not 1 <= item["line"] <= MAX_LINE
                or item["stage"] == "functional"):
            raise ValueError("invalid public candidate source location")
        if "stream" in item and (item["stage"] != "functional" or item["stream"] not in {"q", "k", "v"}):
            raise ValueError("invalid public diagnostic stream")
        result.append(copy.deepcopy(item))
    return tuple(result)


def _source_category(message: str, source_line: str) -> str | None:
    lower = message.lower()
    if "syntax error" in lower:
        # Confirm the construct in the candidate's own source rather than echoing
        # Yosys's unexpected token, identifier or arbitrary error text.
        line = source_line.split("//", 1)[0]
        array = re.search(r"\b(?:parameter|localparam)\b(?:\s+(?:signed|unsigned|logic|reg|bit|integer|int))*"
                          r"\s*(?:\[[^\]]+\]\s*)*(?!(?:signed|unsigned|logic|reg|bit|integer|int)\b)"
                          r"[A-Za-z_][A-Za-z0-9_]*\s*\[", line)
        return "unsupported_parameter_array" if array else "syntax_error"
    if "not declared" in lower or "undeclared" in lower:
        return "undeclared_signal"
    if "port" in lower and any(word in lower for word in ("connection", "width", "not found", "not a port")):
        return "port_connection"
    return None


def source_diagnostics(result: ToolResult, *, candidate_files: Mapping[str, str],
                       declared_sources: Sequence[str], work: Path) -> tuple[dict[str, Any], ...]:
    """Project only verified candidate locations from failed parser/compile stderr."""
    if (result.stage not in {"parser", "compile"} or result.status != "failed"
            or type(result.exit_code) is not int or not 0 < result.exit_code <= 255):
        return ()
    aliases: dict[str, str] = {}
    for relative in declared_sources:
        if not _safe_source_path(relative) or relative not in candidate_files:
            continue
        for alias in (relative, str(work / PurePosixPath(relative))):
            aliases[alias.replace("\\", "/")] = relative
    diagnostics = []
    # stdout may contain source echoes and runtime data. It is never inspected.
    for text in result.stderr[:_MAX_LOG_CHARACTERS].splitlines()[:256]:
        match = _LOCATION.fullmatch(text)
        if match is None:
            continue
        relative = aliases.get(match["file"].replace("\\", "/"))
        if relative is None:
            continue
        line = int(match["line"])
        source = candidate_files[relative].splitlines()
        if not 1 <= line <= min(len(source), MAX_LINE):
            continue
        category = _source_category(match["message"], source[line - 1])
        if category is None:
            continue
        item = _diagnostic(result.stage, category, candidate_file=relative, line=line)
        if item not in diagnostics:
            diagnostics.append(item)
        if len(diagnostics) == MAX_DIAGNOSTICS:
            break
    if not diagnostics:
        diagnostics.append(_diagnostic(result.stage, result.stage + "_failure"))
    return validate_diagnostics(diagnostics)


_FUNCTIONAL_MESSAGES = {
    "output valid persisted following a reset edge": "reset_output_valid",
    "output valid persisted after reset edge": "reset_output_valid",
    "output valid persisted after reset": "reset_output_valid",
    "source changed a stalled token": "stalled_input_changed",
    "source changed a stalled input token": "stalled_input_changed",
    "DUT changed a stalled output token": "stalled_output_changed",
    "next invocation input before all outputs completed": "transaction_overlap",
    "new input before previous output completed": "transaction_overlap",
    "next invocation interleaved with pending output": "transaction_overlap",
    "bounded completion exceeded": "completion_bound",
    "bounded attention completion exceeded": "completion_bound",
    "full cache did not backpressure all inputs": "cache_backpressure",
    "too many input beats": "input_beat_count",
    "unexpected or premature output": "unexpected_output",
    "unexpected or premature attention output": "unexpected_output",
    "invalid trace completion": "trace_invalid",
    "malformed trace or trace after completion": "trace_invalid",
    "malformed trace": "trace_invalid",
    "malformed attention trace": "trace_invalid",
    "trace after completion": "trace_invalid",
    "noncontiguous cycle or invalid reset": "trace_invalid",
    "noncontiguous cycle or nonbinary control": "trace_invalid",
    "noncontiguous trace or nonbinary control": "trace_invalid",
    "nonbinary control": "trace_invalid",
    "invalid packed payload width": "trace_invalid",
    "invalid eighteen-bit payload": "trace_invalid",
    "incomplete trusted simulation schedule": "completion_incomplete",
    "incomplete trusted attention schedule": "completion_incomplete",
}


def functional_diagnostics(error: ValueError) -> tuple[dict[str, Any], ...]:
    """Classify known checker messages; no exception string is returned."""
    message = str(error)
    category = _FUNCTIONAL_MESSAGES.get(message)
    if category is None:
        for prefix in ("invalid or unknown trace signal: ", "unknown or invalid trace signal: ",
                       "unknown or invalid signal in attention trace: "):
            if message.startswith(prefix):
                category = _FUNCTIONAL_MESSAGES.get(message[len(prefix):])
                break
    if category is not None:
        return (_diagnostic("functional", category),)
    for stream in ("q", "k", "v"):
        if message == "unexpected or wrong " + stream + " output":
            return (_diagnostic("functional", "output_mismatch", stream=stream),)
        if message == "changed stalled " + stream + " token":
            return (_diagnostic("functional", "stalled_output_changed", stream=stream),)
    return (_diagnostic("functional", "functional_mismatch"),)
