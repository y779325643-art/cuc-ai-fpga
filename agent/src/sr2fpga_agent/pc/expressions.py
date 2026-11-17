"""Bounded natural-number AST evaluation; never interprets HDL or Python."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .semantics import PcSemanticError

MAX_INTEGER = (1 << 53) - 1


def natural(value: Any, path: str, *, positive: bool = False) -> int:
    if type(value) is not int or not (int(positive) <= value <= MAX_INTEGER):
        qualifier = "positive" if positive else "nonnegative"
        raise PcSemanticError(f"{path}: expected bounded {qualifier} integer")
    return value


def evaluate(expression: Any, parameters: Mapping[str, int], path: str = "$",
             *, max_depth: int = 64) -> int:
    """Evaluate only the registered finite AST, checking every intermediate."""
    if max_depth < 1:
        raise PcSemanticError(f"{path}: expression depth limit exceeded")
    if type(expression) is int:
        return natural(expression, path)
    if not isinstance(expression, dict):
        raise PcSemanticError(f"{path}: invalid natural expression")
    if set(expression) == {"param"}:
        name = expression["param"]
        if not isinstance(name, str) or name not in parameters:
            raise PcSemanticError(f"{path}: unbound parameter {name!r}")
        return natural(parameters[name], path)
    op = expression.get("op")
    if op == "clog2" and set(expression) == {"op", "arg"}:
        arg = evaluate(expression["arg"], parameters, path + ".arg", max_depth=max_depth - 1)
        if arg == 0:
            raise PcSemanticError(f"{path}: clog2 requires a positive argument")
        return (arg - 1).bit_length()
    if (op not in {"add", "sub", "mul", "ceil_div", "min", "max"}
            or set(expression) != {"op", "args"}
            or not isinstance(expression["args"], list) or len(expression["args"]) != 2):
        raise PcSemanticError(f"{path}: unsupported natural expression")
    a, b = [evaluate(item, parameters, f"{path}.args[{i}]", max_depth=max_depth - 1)
            for i, item in enumerate(expression["args"])]
    if op == "ceil_div" and b == 0:
        raise PcSemanticError(f"{path}: division by zero")
    if op == "add":
        result = a + b
    elif op == "sub":
        result = a - b
    elif op == "mul":
        result = a * b
    elif op == "ceil_div":
        result = (a + b - 1) // b
    elif op == "min":
        result = min(a, b)
    else:
        result = max(a, b)
    return natural(result, path)


def bind_parameters(declarations: Mapping[str, Any], values: Mapping[str, Any],
                    parent: Mapping[str, int], path: str) -> dict[str, int]:
    if set(declarations) != set(values):
        raise PcSemanticError(f"{path}: parameter bindings must exactly cover declarations")
    bound: dict[str, int] = {}
    for name, declaration in declarations.items():
        low = natural(declaration["minimum"], f"{path}.{name}.minimum")
        high = natural(declaration["maximum"], f"{path}.{name}.maximum")
        if low > high:
            raise PcSemanticError(f"{path}.{name}: parameter minimum exceeds maximum")
        value = evaluate(values[name], parent, f"{path}.{name}")
        if not low <= value <= high:
            raise PcSemanticError(f"{path}.{name}: parameter {value} outside [{low}, {high}]")
        bound[name] = value
    return bound
