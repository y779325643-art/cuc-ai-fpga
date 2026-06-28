"""Shared lightweight RTL introspection helpers for System-HIS checkers."""

from __future__ import annotations

import re
from typing import Any


def declared_modules(files: dict[str, str], sources: list[str]) -> set[str]:
    """Return Verilog module names declared in the selected source files."""

    modules: set[str] = set()
    pattern = re.compile(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", re.MULTILINE)
    for source in sources:
        modules.update(pattern.findall(files.get(source, "")))
    return modules


def declared_module_parameters(files: dict[str, str], sources: list[str]) -> dict[str, set[str]]:
    """Return declared parameter names for each module in selected sources."""

    parameters: dict[str, set[str]] = {}
    for source in sources:
        content = files.get(source, "")
        for module_name in re.findall(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", content, re.MULTILINE):
            parameters[module_name] = module_parameter_names(content, module_name)
    return parameters


def declared_module_ports(files: dict[str, str], sources: list[str]) -> dict[str, dict[str, dict[str, Any]]]:
    """Return parsed RTL ports for each module in selected sources."""

    ports: dict[str, dict[str, dict[str, Any]]] = {}
    for source in sources:
        content = files.get(source, "")
        for module_name in re.findall(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", content, re.MULTILINE):
            ports[module_name] = parse_module_ports(content, module_name)
    return ports


def parse_module_ports(content: str, module_name: str) -> dict[str, dict[str, Any]]:
    """Parse ANSI-style Verilog module ports into direction and width records."""

    body = module_port_body(content, module_name)
    if body is None:
        return {}
    body = strip_line_comments(body)
    ports: dict[str, dict[str, Any]] = {}
    current_direction = ""
    current_width: int | str = 1
    for declaration in split_port_declarations(body):
        match = re.search(
            r"^\s*\b(input|output|inout)\b\s+(?:(?:wire|reg|logic)\s+)?(\[[^\]]+\])?\s*"
            r"(.+?)\s*$",
            declaration,
        )
        if match is not None:
            current_direction = match.group(1)
            current_width = port_width(match.group(2))
            name_text = match.group(3)
        elif current_direction:
            name_text = declaration
        else:
            continue
        name_match = re.search(r"\b([A-Za-z_][A-Za-z0-9_$]*)\b", name_text)
        if name_match is None:
            continue
        ports[name_match.group(1)] = {
            "direction": current_direction,
            "width": current_width,
        }
    return ports


def module_port_body(content: str, module_name: str) -> str | None:
    """Return the text inside a module's ANSI port list."""

    match = re.search(rf"\bmodule\s+{re.escape(module_name)}\b", content)
    if match is None:
        return None
    index = match.end()
    while index < len(content) and content[index].isspace():
        index += 1
    if index < len(content) and content[index] == "#":
        index += 1
        while index < len(content) and content[index].isspace():
            index += 1
        if index < len(content) and content[index] == "(":
            index = matching_paren(content, index) + 1
    while index < len(content) and content[index].isspace():
        index += 1
    if index >= len(content) or content[index] != "(":
        return None
    end = matching_paren(content, index)
    return content[index + 1 : end]


def split_port_declarations(body: str) -> list[str]:
    """Split a simple ANSI port-list body into comma-separated declarations."""

    declarations: list[str] = []
    for part in body.split(","):
        stripped = " ".join(part.strip().split())
        if stripped:
            declarations.append(stripped)
    return declarations


def strip_line_comments(text: str) -> str:
    return re.sub(r"//.*", "", text)


def port_width(range_text: str | None) -> int | str:
    """Convert a Verilog range into a normalized width value where possible."""

    if range_text is None:
        return 1
    normalized = range_text.strip()
    numeric = re.fullmatch(r"\[(\d+):0\]", normalized)
    if numeric is not None:
        return int(numeric.group(1)) + 1
    concrete_minus_one = re.fullmatch(r"\[(\d+)\s*-\s*1\s*:\s*0\]", normalized)
    if concrete_minus_one is not None:
        return int(concrete_minus_one.group(1))
    return normalized


def module_parameter_names(content: str, module_name: str) -> set[str]:
    """Return parameter names declared in a module parameter list."""

    match = re.search(rf"\bmodule\s+{re.escape(module_name)}\b", content)
    if match is None:
        return set()
    index = match.end()
    while index < len(content) and content[index].isspace():
        index += 1
    if index >= len(content) or content[index] != "#":
        return set()
    index += 1
    while index < len(content) and content[index].isspace():
        index += 1
    if index >= len(content) or content[index] != "(":
        return set()
    end = matching_paren(content, index)
    parameter_body = content[index + 1 : end]
    return set(re.findall(r"\bparameter\s+([A-Za-z_][A-Za-z0-9_$]*)\b", parameter_body))


def matching_paren(text: str, open_index: int) -> int:
    """Return the matching close-paren index, or len(text) if unmatched."""

    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return len(text)


def normalize_width(value: Any) -> str:
    """Normalize width spelling so numeric ranges and integers compare equally."""

    if isinstance(value, dict):
        if "expr" in value:
            return normalize_width(value["expr"])
        if "resolved" in value:
            return normalize_width(value["resolved"])
    text = str(value).strip()
    numeric_range = re.fullmatch(r"\[(\d+):0\]", text)
    if numeric_range is not None:
        return str(int(numeric_range.group(1)) + 1)
    concrete_minus_one_range = re.fullmatch(r"\[(\d+)\s*-\s*1\s*:\s*0\]", text)
    if concrete_minus_one_range is not None:
        return concrete_minus_one_range.group(1)
    symbolic_range = re.fullmatch(r"\[([A-Za-z_][A-Za-z0-9_$]*)\s*-\s*1\s*:\s*0\]", text)
    if symbolic_range is not None:
        return symbolic_range.group(1)
    unbracketed_numeric_range = re.fullmatch(r"(\d+)\s*:\s*0", text)
    if unbracketed_numeric_range is not None:
        return str(int(unbracketed_numeric_range.group(1)) + 1)
    unbracketed_concrete_minus_one_range = re.fullmatch(r"(\d+)\s*-\s*1\s*:\s*0", text)
    if unbracketed_concrete_minus_one_range is not None:
        return unbracketed_concrete_minus_one_range.group(1)
    unbracketed_symbolic_range = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_$]*)\s*-\s*1\s*:\s*0", text)
    if unbracketed_symbolic_range is not None:
        return unbracketed_symbolic_range.group(1)
    bracketed_range = re.fullmatch(r"\[(.+:.+)\]", text)
    if bracketed_range is not None:
        return bracketed_range.group(1).strip()
    return text


def width_candidates(value: Any) -> set[str]:
    """Return all normalized width spellings that can represent a value."""

    if isinstance(value, dict):
        candidates: set[str] = set()
        if "expr" in value:
            candidates.update(width_candidates(value["expr"]))
        if "resolved" in value:
            candidates.update(width_candidates(value["resolved"]))
        return candidates
    return {normalize_width(value)}


def widths_equivalent(left: Any, right: Any) -> bool:
    """Compare widths allowing symbolic and resolved forms to match."""

    return bool(width_candidates(left) & width_candidates(right))
