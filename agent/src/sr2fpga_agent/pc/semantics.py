"""Incremental PC 2.1 semantic checks after schema validation."""

from __future__ import annotations

from typing import Any, Mapping


class PcSemanticError(ValueError):
    """A schema-valid PC design contains an invalid semantic relationship."""


def validate_entry_module(design: Mapping[str, Any]) -> None:
    """Require ``design.entry`` to name one exactly defined module.

    The caller must run the registered design schema first. This check only
    resolves the top-level module reference; it does not inspect reachability,
    instances, ports, types, tensors, or behavior.
    """

    entry = design["entry"]
    modules = design["modules"]
    if entry not in modules:
        raise PcSemanticError(f"entry module is not defined: {entry}")


def validate_instance_modules(design: Mapping[str, Any]) -> None:
    """Require every structural child instance to name a defined module.

    This resolves only the instance's module reference. It does not check
    recursion, reachability, parameter/domain bindings, ports, nets, or types.
    """

    modules = design["modules"]
    for owner_name, module in modules.items():
        implementation = module["implementation"]
        if implementation["kind"] != "structural":
            continue
        for instance_name, instance in implementation["instances"].items():
            target_name = instance["module"]
            if target_name not in modules:
                raise PcSemanticError(
                    "instance module is not defined: "
                    f"{owner_name}.{instance_name} -> {target_name}"
                )


def _child_module_names(module: Mapping[str, Any]) -> tuple[str, ...]:
    """Return direct child-module references for one structural module."""

    implementation = module["implementation"]
    if implementation["kind"] != "structural":
        return ()
    return tuple(
        instance["module"] for instance in implementation["instances"].values()
    )


def validate_acyclic_modules(design: Mapping[str, Any]) -> None:
    """Reject direct or indirect recursion in the module-definition graph.

    Entry and instance references must be validated first. The iterative walk
    avoids making Python's own recursion limit a design-size limit.
    """

    modules = design["modules"]
    completed: set[str] = set()

    for start_name in modules:
        if start_name in completed:
            continue

        path = [start_name]
        active_positions = {start_name: 0}
        child_iterators = [iter(_child_module_names(modules[start_name]))]

        while child_iterators:
            try:
                child_name = next(child_iterators[-1])
            except StopIteration:
                finished_name = path.pop()
                active_positions.pop(finished_name)
                completed.add(finished_name)
                child_iterators.pop()
                continue

            cycle_start = active_positions.get(child_name)
            if cycle_start is not None:
                cycle = [*path[cycle_start:], child_name]
                raise PcSemanticError(
                    "recursive module hierarchy: " + " -> ".join(cycle)
                )
            if child_name in completed:
                continue

            active_positions[child_name] = len(path)
            path.append(child_name)
            child_iterators.append(iter(_child_module_names(modules[child_name])))


def validate_reachable_modules(design: Mapping[str, Any]) -> None:
    """Require every module definition to be reachable from ``design.entry``.

    Entry and instance references must be validated first. Multiple instances
    may reuse one module definition; reachability records definitions, not the
    number of instantiated hardware copies.
    """

    entry = design["entry"]
    modules = design["modules"]
    reachable: set[str] = set()
    pending = [entry]

    while pending:
        module_name = pending.pop()
        if module_name in reachable:
            continue
        reachable.add(module_name)
        pending.extend(_child_module_names(modules[module_name]))

    unreachable = sorted(set(modules) - reachable)
    if unreachable:
        raise PcSemanticError(
            f"module definitions are unreachable from entry {entry}: "
            + ", ".join(unreachable)
        )


def validate_signature_sources(design: Mapping[str, Any]) -> None:
    """Separate the requirement-owned entry ABI from internal declarations."""

    entry = design["entry"]
    for module_name, module in design["modules"].items():
        expected_source = (
            "requirement_boundary" if module_name == entry else "declared"
        )
        actual_source = module["signature"]["source"]
        if actual_source != expected_source:
            raise PcSemanticError(
                "module signature source mismatch: "
                f"{module_name} expected {expected_source}, got {actual_source}"
            )


def validate_instance_parameter_names(design: Mapping[str, Any]) -> None:
    """Require supplied parameter names to exactly match target declarations.

    Each instance binds its own parameters; no implicit defaults are supplied.
    Values and expressions are checked by later, not-yet-implemented rules.
    """

    modules = design["modules"]
    for owner_name, owner in modules.items():
        implementation = owner["implementation"]
        if implementation["kind"] != "structural":
            continue
        for instance_name, instance in implementation["instances"].items():
            target_name = instance["module"]
            declared_names = set(modules[target_name]["signature"]["parameters"])
            supplied_names = set(instance["parameters"])
            unknown_names = sorted(supplied_names - declared_names)
            if unknown_names:
                raise PcSemanticError(
                    "instance parameters are not declared by target module: "
                    f"{owner_name}.{instance_name} -> {target_name}: "
                    + ", ".join(unknown_names)
                )
            missing_names = sorted(declared_names - supplied_names)
            if missing_names:
                raise PcSemanticError(
                    "instance parameter bindings are missing: "
                    f"{owner_name}.{instance_name} -> {target_name}: "
                    + ", ".join(missing_names)
                )
