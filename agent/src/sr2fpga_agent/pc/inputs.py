"""Strict input and trusted byte binding (plan v2.2 §4.1; architecture §6).

This module deliberately does not implement H1–H3, tensor semantics, boundary
projection or RTL construction. Trusted inputs must be selected by the caller
from the public controller context, never supplied by the candidate. Hashes
establish byte identity, not source authorization or task qualification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sr2fpga_agent.contract_registry import ContractRegistry

from .semantics import (
    validate_acyclic_modules,
    validate_entry_module,
    validate_instance_parameter_names,
    validate_instance_modules,
    validate_reachable_modules,
    validate_signature_sources,
)


class PcInputError(ValueError):
    """A PC input was rejected before semantic validation."""


class PcParseError(PcInputError):
    """Invalid or resource-limited PC JSON."""


class PcSchemaError(PcInputError):
    """Input does not conform to the registered PC 2.1 schema."""


class BindingError(PcInputError):
    """A full PC does not bind to the controller's original public bytes."""


@dataclass(frozen=True)
class ParseLimits:
    """Explicit local resource policy, not an implicit research budget.

    Depth counts nested containers, with the root object at depth one.
    """

    max_bytes: int
    max_depth: int

    def __post_init__(self) -> None:
        for value in (self.max_bytes, self.max_depth):
            if type(value) is not int or value < 1:
                raise ValueError("parse limits must be positive integers")


@dataclass(frozen=True)
class TrustedSource:
    """Controller-owned identity and exact source bytes (no reserialization)."""

    id: str
    content: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not 1 <= len(self.id) <= 8192:
            raise ValueError("source id must contain 1–8192 characters")
        if type(self.content) is not bytes:
            raise TypeError("trusted source content must be immutable bytes")

    def reference(self) -> dict[str, str]:
        return {"id": self.id, "sha256": hashlib.sha256(self.content).hexdigest()}


@dataclass(frozen=True)
class TrustedContext:
    requirements: TrustedSource
    target_profile: TrustedSource
    capability_profile: TrustedSource

    def __post_init__(self) -> None:
        if not all(isinstance(source, TrustedSource) for source in (
            self.requirements, self.target_profile, self.capability_profile
        )):
            raise TypeError("trusted context requires three TrustedSource objects")

    def bindings(self) -> dict[str, dict[str, str]]:
        return {name: getattr(self, name).reference() for name in (
            "requirements", "target_profile", "capability_profile"
        )}


def _reject_number(value: str) -> Any:
    raise PcParseError("PC JSON requires integer number literals")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PcParseError("duplicate JSON object key")
        result[key] = value
    return result


def _parse(raw: bytes, limits: ParseLimits) -> dict[str, Any]:
    if type(raw) is not bytes:
        raise TypeError("PC input must be UTF-8 bytes")
    if len(raw) > limits.max_bytes:
        raise PcParseError("PC JSON exceeds max_bytes")
    try:
        source = raw.decode("utf-8")
        # Bound nesting before invoking the recursive JSON decoder. Brackets
        # inside strings (including escaped quotes) do not contribute depth.
        depth = 0
        quoted = escaped = False
        for char in source:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > limits.max_depth:
                    raise PcParseError("PC JSON exceeds max_depth")
            elif char in "]}":
                depth -= 1
        payload = json.loads(source, object_pairs_hook=_object,
                             parse_float=_reject_number,
                             parse_constant=_reject_number)
    except PcParseError:
        raise
    except (UnicodeError, ValueError, RecursionError) as error:
        raise PcParseError("invalid PC JSON") from error
    if not isinstance(payload, dict):
        raise PcParseError("PC JSON root must be an object")
    # Python's decoder accepts isolated escaped UTF-16 surrogates, which cannot
    # be written back as valid UTF-8. Valid escaped pairs decode to one scalar.
    pending: list[Any] = [payload]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            pending.extend(value.keys())
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, str) and any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise PcParseError("PC JSON contains an unpaired Unicode surrogate")
    return payload


def _validate(payload: dict[str, Any], key: str, registry: ContractRegistry) -> None:
    errors = registry.load_schema(key).validate(payload)
    if errors:
        raise PcSchemaError("; ".join(errors))


def _validate_semantics(design: dict[str, Any]) -> None:
    """Run the semantic rules implemented by this incremental checker."""

    validate_entry_module(design)
    validate_instance_modules(design)
    validate_acyclic_modules(design)
    validate_reachable_modules(design)
    validate_signature_sources(design)
    validate_instance_parameter_names(design)


def parse_design_proposal(raw: bytes, *, limits: ParseLimits,
                          registry: ContractRegistry | None = None) -> dict[str, Any]:
    """Accept only the model's direct design root; no repair or fallback."""
    proposal = _parse(raw, limits)
    _validate(proposal, "design_proposal_2_1", registry or ContractRegistry())
    return proposal


def _validate_bound(pc: dict[str, Any], context: TrustedContext,
                    registry: ContractRegistry) -> None:
    _validate(pc, "project_contract_2_1", registry)
    expected = context.bindings()
    for name, reference in expected.items():
        if pc["bindings"][name] != reference:
            raise BindingError(f"trusted byte binding mismatch: {name}")


def assemble_project_contract(raw_design: bytes, context: TrustedContext, *,
                              limits: ParseLimits,
                              registry: ContractRegistry | None = None) -> dict[str, Any]:
    """Bind a validated model proposal to public controller inputs."""
    registry = registry or ContractRegistry()
    design = parse_design_proposal(raw_design, limits=limits, registry=registry)
    _validate_semantics(design)
    pc = {
        "schema_version": "sr2fpga-pc-2.1",
        "bindings": context.bindings(),
        "design": design,
    }
    _validate_bound(pc, context, registry)
    return pc


def parse_project_contract(raw: bytes, context: TrustedContext, *,
                           limits: ParseLimits,
                           registry: ContractRegistry | None = None) -> dict[str, Any]:
    """Recheck a saved full PC against current controller-owned source bytes."""
    pc = _parse(raw, limits)
    _validate_bound(pc, context, registry or ContractRegistry())
    _validate_semantics(pc["design"])
    return pc
