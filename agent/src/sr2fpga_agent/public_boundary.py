"""Scoped checks of the development public boundary, shared by all methods.

Accepts a parsed development-public-boundary-v1 document. This is not a file
reader, task-ready adjudicator, complete boundary validator or PC checker.
"""

from __future__ import annotations

from typing import Any

from sr2fpga_agent.contract_registry import ContractRegistry


def check_public_boundary_ports(
    payload: Any, *, registry: ContractRegistry | None = None
) -> tuple[str, ...]:
    """Check schema, exact port-map coverage and stream/value mapping forms.

    Return diagnostics without mutating the input. An empty tuple covers only
    these checks: domain binding, physical-name collisions, parameter semantics,
    task behavior and source-byte identity remain separate responsibilities.
    """

    registry = registry if registry is not None else ContractRegistry()
    schema_errors = registry.load_schema("development_public_boundary").validate(payload)
    if schema_errors:
        return schema_errors

    boundary = payload["boundary"]
    ports = boundary["signature"]["ports"]
    mappings = boundary["abi"]["ports"]
    declared_names = set(ports)
    mapped_names = set(mappings)
    errors: list[str] = []

    missing = sorted(declared_names - mapped_names)
    extra = sorted(mapped_names - declared_names)
    if missing:
        errors.append("$.boundary.abi.ports: missing port mappings: " + ", ".join(missing))
    if extra:
        errors.append("$.boundary.abi.ports: mappings for undeclared ports: " + ", ".join(extra))

    for name in sorted(declared_names & mapped_names):
        kind = ports[name]["kind"]
        expected_keys = {"signal"} if kind == "value" else {"payload", "valid", "ready"}
        if set(mappings[name]) != expected_keys:
            expected_form = "signal" if kind == "value" else "payload/valid/ready"
            errors.append(
                f"$.boundary.abi.ports.{name}: {kind} port requires {expected_form} mapping"
            )

    return tuple(errors)


def check_public_boundary_domains(
    payload: Any, *, registry: ContractRegistry | None = None
) -> tuple[str, ...]:
    """Check domain-map coverage and declared clock/reset pin presence.

    Schema validation precedes all field access. This checks neither port-domain
    references nor clock timing, reset implementation, CDC or target capability.
    """

    registry = registry if registry is not None else ContractRegistry()
    schema_errors = registry.load_schema("development_public_boundary").validate(payload)
    if schema_errors:
        return schema_errors

    boundary = payload["boundary"]
    domains = boundary["signature"]["domains"]
    mappings = boundary["abi"]["domains"]
    declared_names = set(domains)
    mapped_names = set(mappings)
    errors: list[str] = []

    missing = sorted(declared_names - mapped_names)
    extra = sorted(mapped_names - declared_names)
    if missing:
        errors.append("$.boundary.abi.domains: missing domain mappings: " + ", ".join(missing))
    if extra:
        errors.append("$.boundary.abi.domains: mappings for undeclared domains: " + ", ".join(extra))

    for name in sorted(declared_names):
        clock_kind = domains[name]["clock"]
        reset_kind = domains[name]["reset"]["kind"]
        if clock_kind == "none" and reset_kind != "none":
            errors.append(
                f"$.boundary.signature.domains.{name}: clock=none requires reset=none"
            )
        if name not in mappings:
            continue
        for signal, kind in (("clock", clock_kind), ("reset", reset_kind)):
            requires_pin = kind != "none"
            has_pin = mappings[name][signal] is not None
            if has_pin != requires_pin:
                expected = "a pin name" if requires_pin else "null"
                errors.append(
                    f"$.boundary.abi.domains.{name}.{signal}: "
                    f"expected {expected} for {signal}={kind}"
                )

    return tuple(errors)
