"""Lightweight Verilog identifier checks before external lint tools run."""

from __future__ import annotations

from dataclasses import dataclass
import re

from LLM.src.sr2fpga_agent.models import GeneratedProject, ToolResult
from LLM.src.sr2fpga_agent.system_his_v12_checker import VERILOG_RESERVED_KEYWORDS


DECLARATION_KEYWORDS = {"input", "output", "inout", "wire", "reg", "logic", "integer"}
STATEMENT_KEYWORDS = {
    "always",
    "assign",
    "begin",
    "case",
    "else",
    "end",
    "endcase",
    "endmodule",
    "for",
    "if",
    "initial",
    "module",
}


@dataclass(frozen=True)
class RtlIdentifierIssue:
    """One reserved-keyword identifier occurrence in generated RTL."""

    path: str
    line: int
    identifier: str
    context: str


def check_rtl_identifiers(project: GeneratedProject, sources: list[str]) -> list[RtlIdentifierIssue]:
    """Find generated RTL identifiers that collide with Verilog keywords."""

    issues: list[RtlIdentifierIssue] = []
    for source in sources:
        content = project.files.get(source, "")
        if not source.endswith(".v") or not content:
            continue
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            line = _strip_line_comment(raw_line)
            if not line.strip():
                continue
            issues.extend(_module_name_issues(source, line_number, line))
            issues.extend(_declaration_issues(source, line_number, line))
            issues.extend(_instance_issues(source, line_number, line))
    return issues


def rtl_identifier_tool_result(issues: list[RtlIdentifierIssue]) -> ToolResult:
    """Represent lexical identifier issues as a pipeline ToolResult."""

    status = "passed" if not issues else "failed"
    stderr = ""
    if issues:
        stderr = "\n".join(
            (
                f"{issue.path}:{issue.line}: Verilog reserved keyword '{issue.identifier}' "
                f"used as {issue.context}"
            )
            for issue in issues
        )
        stderr += "\n"
    return ToolResult(
        stage="rtl_identifier_check",
        command=["rtl_identifier_checker"],
        status=status,
        exit_code=0 if not issues else 1,
        stdout="",
        stderr=stderr,
        duration_seconds=0.0,
    )


def _strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0]


def _module_name_issues(path: str, line_number: int, line: str) -> list[RtlIdentifierIssue]:
    match = re.match(r"\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", line)
    if match and match.group(1) in VERILOG_RESERVED_KEYWORDS:
        return [RtlIdentifierIssue(path, line_number, match.group(1), "module name")]
    return []


def _declaration_issues(path: str, line_number: int, line: str) -> list[RtlIdentifierIssue]:
    stripped = line.strip()
    first = stripped.split(None, 1)[0] if stripped.split(None, 1) else ""
    if first not in DECLARATION_KEYWORDS:
        return []
    declaration = re.sub(r"\[[^\]]+\]", " ", stripped)
    declaration = declaration.rstrip(";")
    issues: list[RtlIdentifierIssue] = []
    for name in re.findall(r"\b([A-Za-z_][A-Za-z0-9_$]*)\b\s*(?:\[[^\]]+\])?\s*(?:,|$)", declaration):
        if name in DECLARATION_KEYWORDS:
            continue
        if name in VERILOG_RESERVED_KEYWORDS:
            issues.append(RtlIdentifierIssue(path, line_number, name, "declared signal"))
    return issues


def _instance_issues(path: str, line_number: int, line: str) -> list[RtlIdentifierIssue]:
    match = re.match(
        r"\s*([A-Za-z_][A-Za-z0-9_$]*)\s*(?:#\s*\([^;]*\)\s*)?([A-Za-z_][A-Za-z0-9_$]*)\s*\(",
        line,
    )
    if not match:
        return []
    module_type, instance_name = match.groups()
    if module_type in STATEMENT_KEYWORDS or module_type in DECLARATION_KEYWORDS:
        return []
    if instance_name in VERILOG_RESERVED_KEYWORDS:
        return [RtlIdentifierIssue(path, line_number, instance_name, "instance name")]
    return []
