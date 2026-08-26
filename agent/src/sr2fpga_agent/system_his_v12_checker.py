"""Structural checks for the canonical System-HIS v1.2 schema."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from typing import Any

from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.rtl_introspect import declared_module_ports, declared_modules, widths_equivalent


SCHEMA_VERSION = "system-his-v1.2"
REQUIRED_TOP_LEVEL_KEYS = (
    "schema_version",
    "intent",
    "top",
    "state",
    "components",
    "instances",
    "data_flow",
    "control_flow",
    "timing",
    "resources",
    "verification",
    "artifacts",
)
STATE_GROUPS = ("registers", "counters", "fsms", "buffers", "memories")
GUARD_OPERATORS = {"==", "!=", "<", ">", "&&", "||"}
CONTROL_FLOW_KINDS = {
    "reset_rule",
    "handshake_rule",
    "enable_rule",
    "stall_rule",
    "counter_update",
    "fsm_transition",
    "buffer_occupancy",
}
VERILOG_RESERVED_KEYWORDS = {
    "always",
    "assign",
    "begin",
    "buf",
    "case",
    "default",
    "else",
    "end",
    "endcase",
    "endmodule",
    "for",
    "fork",
    "generate",
    "if",
    "initial",
    "inout",
    "input",
    "join",
    "module",
    "output",
    "parameter",
    "reg",
    "wire",
}


@dataclass(frozen=True)
class SystemHisV12CheckResult:
    """Result of validating a System-HIS v1.2 JSON object."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SystemHisWellFormednessRuleResult:
    """One machine-readable W1-W10 conformance result."""

    status: str
    diagnostics: list[str] = field(default_factory=list)


def check_system_his_v12(payload: dict[str, Any]) -> SystemHisV12CheckResult:
    """Validate v1.2 System-HIS internal structure.

    This checker intentionally stops at IR self-consistency. It does not parse
    RTL files or replace the existing v1.1 project-level L0 checker.
    """

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return SystemHisV12CheckResult(False, ["system_his must be an object"], warnings)

    _validate_required_keys(payload, errors)
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"system_his.schema_version must be {SCHEMA_VERSION}")

    intent = _mapping(payload.get("intent"), "system_his.intent", errors)
    top = _mapping(payload.get("top"), "system_his.top", errors)
    components = _list(payload.get("components"), "system_his.components", errors)
    instances = _list(payload.get("instances"), "system_his.instances", errors)
    state = _mapping(payload.get("state"), "system_his.state", errors)
    data_flow = _list(payload.get("data_flow"), "system_his.data_flow", errors)
    control_flow = _list(payload.get("control_flow"), "system_his.control_flow", errors)
    timing = _mapping(payload.get("timing"), "system_his.timing", errors)
    resources = _mapping(payload.get("resources"), "system_his.resources", errors)
    verification = _mapping(payload.get("verification"), "system_his.verification", errors)
    artifacts = _mapping(payload.get("artifacts"), "system_his.artifacts", errors)

    _validate_intent(intent, errors)
    _validate_top_clock_reset(top, errors)
    _validate_timing(timing, errors)
    _validate_resources(resources, errors)
    _validate_verification(verification, errors)
    top_ports = _top_ports(top, errors)
    top_control_signals = top_ports | _top_clock_reset_names(top)
    rtl_sources = _artifact_rtl_sources(artifacts, errors)
    component_ports = _component_ports(components, set(rtl_sources), errors)
    component_parameters = _component_parameters(components)
    instance_components = _instance_components(instances, component_ports, component_parameters, errors)
    instance_ports = {
        instance_name: component_ports.get(component_name, set())
        for instance_name, component_name in instance_components.items()
    }
    state_names = _state_names(state, errors)
    valid_fsm_owners = {"top", str(top.get("name", "")).strip()} | set(instance_components)
    valid_fsm_owners.discard("")
    fsm_defs = _validate_fsms(state, state_names, valid_fsm_owners, errors)
    data_flow_names = _data_flow_names(data_flow, top_ports, instance_ports, errors)
    _validate_instance_state_ownership(instances, state_names, errors)
    _validate_control_flow(
        control_flow,
        state_names,
        data_flow_names,
        top_control_signals,
        instance_ports,
        fsm_defs,
        errors,
    )
    _validate_artifacts(artifacts, errors)
    for rule_id, rule_result in check_system_his_well_formedness(payload).items():
        for diagnostic in rule_result.diagnostics:
            message = f"[{rule_id}] {diagnostic}"
            if message not in errors:
                errors.append(message)

    return SystemHisV12CheckResult(passed=not errors, errors=errors, warnings=warnings)


def check_system_his_well_formedness(
    payload: dict[str, Any],
) -> dict[str, SystemHisWellFormednessRuleResult]:
    """Return independently attributable W1-W10 results.

    ``not_applicable`` is used only when the governed construct is absent
    (currently CDC flows or memories). It is never treated as evidence that an
    uninspected construct passed.
    """

    rules = {
        "W1": _w1_component_references(payload),
        "W2": _w2_endpoint_references(payload),
        "W3": _w3_connection_types(payload),
        "W4": _w4_state_clock_reset_bindings(payload),
        "W5": _w5_combinational_state(payload),
        "W6": _w6_cdc_paths(payload),
        "W7": _w7_memory_intent(payload),
        "W8": _w8_verification_references(payload),
        "W9": _w9_constraint_references(payload),
        "W10": _w10_artifact_reproducibility(payload),
    }
    return {
        rule_id: SystemHisWellFormednessRuleResult(
            status="fail" if diagnostics else ("not_applicable" if diagnostics is None else "pass"),
            diagnostics=[] if diagnostics is None else diagnostics,
        )
        for rule_id, diagnostics in rules.items()
    }


def check_system_his_v12_against_rtl(
    payload: dict[str, Any],
    project: GeneratedProject,
) -> SystemHisV12CheckResult:
    """Validate v1.2 System-HIS internal structure plus selected RTL cross-checks."""

    result = check_system_his_v12(payload)
    errors = list(result.errors)
    warnings = list(result.warnings)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return SystemHisV12CheckResult(False, errors, warnings)

    sources = _v12_string_list(artifacts.get("rtl_sources"), "system_his.artifacts.rtl_sources", errors)
    for source in sources:
        if source not in project.files:
            errors.append(f"system_his.artifacts.rtl_sources entry '{source}' is missing from project files")
    top_module = str(artifacts.get("top_module", "")).strip()
    rtl_modules = declared_modules(project.files, sources)
    rtl_ports = declared_module_ports(project.files, sources)

    if top_module and top_module not in rtl_modules:
        errors.append(f"top module '{top_module}' is not declared in System-HIS v1.2 RTL sources")
    _validate_v12_artifacts_against_project(artifacts, project, sources, top_module, rtl_ports, errors)
    _validate_v12_top_against_rtl(payload.get("top"), top_module, rtl_ports, errors)
    component_ports = _validate_v12_components_against_rtl(
        payload.get("components"),
        sources,
        rtl_modules,
        rtl_ports,
        project,
        errors,
    )
    instance_components = _v12_instance_components(payload.get("instances"), component_ports, errors)
    _validate_v12_instances_in_top(instance_components, component_ports, top_module, project, errors)
    _validate_v12_data_flow_against_rtl(payload.get("data_flow"), top_module, rtl_ports, instance_components, errors)
    _validate_v12_fsm_states_against_rtl(payload.get("state"), instance_components, top_module, rtl_ports, project, errors)

    return SystemHisV12CheckResult(passed=not errors, errors=errors, warnings=warnings)


def _validate_required_keys(payload: dict[str, Any], errors: list[str]) -> None:
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            errors.append(f"system_his.{key} is required")


def _validate_intent(intent: dict[str, Any], errors: list[str]) -> None:
    for key in ("user_prompt", "design_goal"):
        if not str(intent.get(key, "")).strip():
            errors.append(f"system_his.intent.{key} is required")
    _list(intent.get("assumptions"), "system_his.intent.assumptions", errors)


def _validate_top_clock_reset(top: dict[str, Any], errors: list[str]) -> None:
    clocks = _list(top.get("clocks"), "system_his.top.clocks", errors)
    for index, clock in enumerate(clocks):
        if not isinstance(clock, dict):
            errors.append(f"system_his.top.clocks[{index}] must be an object")
            continue
        if not str(clock.get("name", "")).strip():
            errors.append(f"system_his.top.clocks[{index}].name is required")
        if not _is_positive_number(clock.get("target_fmax_mhz")):
            errors.append(f"system_his.top.clocks[{index}].target_fmax_mhz must be positive")

    resets = _list(top.get("resets"), "system_his.top.resets", errors)
    for index, reset in enumerate(resets):
        if not isinstance(reset, dict):
            errors.append(f"system_his.top.resets[{index}] must be an object")
            continue
        if not str(reset.get("name", "")).strip():
            errors.append(f"system_his.top.resets[{index}].name is required")
        polarity = str(reset.get("polarity", "")).strip()
        if polarity not in {"active_low", "active_high", "low", "high"}:
            errors.append(f"system_his.top.resets[{index}].polarity is invalid")
        kind = str(reset.get("kind", "")).strip()
        if kind not in {"sync", "async", "synchronous", "asynchronous"}:
            errors.append(f"system_his.top.resets[{index}].kind is invalid")


def _validate_timing(timing: dict[str, Any], errors: list[str]) -> None:
    if not str(timing.get("primary_clock", "")).strip():
        errors.append("system_his.timing.primary_clock is required")
    if not _is_positive_number(timing.get("target_fmax_mhz")):
        errors.append("system_his.timing.target_fmax_mhz must be positive")
    _list(timing.get("constraints"), "system_his.timing.constraints", errors)


def _validate_resources(resources: dict[str, Any], errors: list[str]) -> None:
    if not str(resources.get("optimization_goal", "")).strip():
        errors.append("system_his.resources.optimization_goal is required")
    _mapping(resources.get("expected"), "system_his.resources.expected", errors)


def _validate_verification(verification: dict[str, Any], errors: list[str]) -> None:
    if not str(verification.get("testbench", "")).strip():
        errors.append("system_his.verification.testbench is required")
    _list(verification.get("scenarios"), "system_his.verification.scenarios", errors)
    if not str(verification.get("pass_condition", "")).strip():
        errors.append("system_his.verification.pass_condition is required")


def _mapping(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def _list(value: Any, name: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    return value


def _top_ports(top: dict[str, Any], errors: list[str]) -> set[str]:
    name = str(top.get("name", "")).strip()
    if not name:
        errors.append("system_his.top.name is required")
    ports = _list(top.get("ports"), "system_his.top.ports", errors)
    port_names: set[str] = set()
    for index, port in enumerate(ports):
        if not isinstance(port, dict):
            errors.append(f"system_his.top.ports[{index}] must be an object")
            continue
        port_name = str(port.get("name", "")).strip()
        if not port_name:
            errors.append(f"system_his.top.ports[{index}].name is required")
        elif port_name in port_names:
            errors.append(f"system_his.top.ports duplicate port '{port_name}'")
        else:
            port_names.add(port_name)
    return port_names


def _top_clock_reset_names(top: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for section in ("clocks", "resets"):
        items = top.get(section, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if name:
                names.add(name)
    return names


def _component_ports(components: list[Any], rtl_sources: set[str], errors: list[str]) -> dict[str, set[str]]:
    component_ports: dict[str, set[str]] = {}
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            errors.append(f"components[{index}] must be an object")
            continue
        name = str(component.get("name", "")).strip()
        if not name:
            errors.append(f"components[{index}].name is required")
            continue
        if name in component_ports:
            errors.append(f"components duplicate component '{name}'")
            continue
        if not str(component.get("semantic_kind", "")).strip():
            errors.append(f"components[{index}].semantic_kind is required")
        source = str(component.get("source", "")).strip()
        if not source:
            errors.append(f"components[{index}].source is required")
        elif rtl_sources and source not in rtl_sources:
            errors.append(f"components[{index}].source '{source}' is not in artifacts.rtl_sources")
        if not str(component.get("intent", "")).strip():
            errors.append(f"components[{index}].intent is required")
        ports = _list(component.get("ports"), f"components[{index}].ports", errors)
        port_names: set[str] = set()
        for port_index, port in enumerate(ports):
            if not isinstance(port, dict):
                errors.append(f"components[{index}].ports[{port_index}] must be an object")
                continue
            port_name = str(port.get("name", "")).strip()
            if not port_name:
                errors.append(f"components[{index}].ports[{port_index}].name is required")
            else:
                port_names.add(port_name)
        component_ports[name] = port_names
    return component_ports


def _component_parameters(components: list[Any]) -> dict[str, set[str]]:
    component_parameters: dict[str, set[str]] = {}
    for component in components:
        if not isinstance(component, dict):
            continue
        name = str(component.get("name", "")).strip()
        parameters = component.get("parameters", [])
        if not name or not isinstance(parameters, list):
            continue
        component_parameters[name] = {
            str(parameter.get("name", "")).strip()
            for parameter in parameters
            if isinstance(parameter, dict) and str(parameter.get("name", "")).strip()
        }
    return component_parameters


def _instance_components(
    instances: list[Any],
    component_ports: dict[str, set[str]],
    component_parameters: dict[str, set[str]],
    errors: list[str],
) -> dict[str, str]:
    instance_components: dict[str, str] = {}
    for index, instance in enumerate(instances):
        if not isinstance(instance, dict):
            errors.append(f"instances[{index}] must be an object")
            continue
        name = str(instance.get("name", "")).strip()
        component = str(instance.get("component", "")).strip()
        if not name:
            errors.append(f"instances[{index}].name is required")
            continue
        if name in VERILOG_RESERVED_KEYWORDS:
            errors.append(f"instances[{index}].name '{name}' is a Verilog reserved keyword")
        if name in instance_components:
            errors.append(f"instances duplicate instance '{name}'")
        if not component:
            errors.append(f"instances[{index}].component is required")
        elif component not in component_ports:
            errors.append(f"instances[{index}] references missing component '{component}'")
        if not str(instance.get("clock", "")).strip():
            errors.append(f"instances[{index}].clock is required")
        if not str(instance.get("reset", "")).strip():
            errors.append(f"instances[{index}].reset is required")
        parameter_values = _mapping(instance.get("parameter_values"), f"instances[{index}].parameter_values", errors)
        declared_parameters = component_parameters.get(component, set())
        for parameter_name in parameter_values:
            if parameter_name not in declared_parameters:
                errors.append(
                    f"instances[{index}].parameter_values.{parameter_name} "
                    f"is not declared by component '{component}'"
                )
        instance_components[name] = component
    return instance_components


def _state_names(state: dict[str, Any], errors: list[str]) -> set[str]:
    names: set[str] = set()
    for group in STATE_GROUPS:
        items = _list(state.get(group), f"system_his.state.{group}", errors)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"system_his.state.{group}[{index}] must be an object")
                continue
            name = str(item.get("name", "")).strip()
            if not name:
                errors.append(f"system_his.state.{group}[{index}].name is required")
            elif name in names:
                errors.append(f"system_his.state duplicate state '{name}'")
            else:
                names.add(name)
                owner = str(item.get("owner", "")).strip()
                if owner:
                    names.add(f"{owner}.{name}")
    return names


def _validate_fsms(
    state: dict[str, Any],
    state_names: set[str],
    valid_owners: set[str],
    errors: list[str],
) -> dict[str, set[str]]:
    fsm_defs: dict[str, set[str]] = {}
    fsms = state.get("fsms")
    if not isinstance(fsms, list):
        return fsm_defs
    for index, fsm in enumerate(fsms):
        if not isinstance(fsm, dict):
            continue
        name = str(fsm.get("name", "")).strip()
        if not name:
            continue
        if name in fsm_defs:
            errors.append(f"state.fsms duplicate FSM '{name}'")
        owner = str(fsm.get("owner", "")).strip()
        if not owner and "." in name:
            owner = name.split(".", 1)[0]
        if not owner:
            errors.append(f"state.fsms '{name}' must declare owner or use <instance>.<fsm> name")
        elif owner not in valid_owners:
            errors.append(f"state.fsms '{name}'.owner '{owner}' is not top or an instance")
        states_value = fsm.get("states")
        states: set[str] = set()
        if not isinstance(states_value, list):
            errors.append(f"state.fsms '{name}'.states must be a list")
        else:
            for state_index, state_value in enumerate(states_value):
                state_text = str(state_value).strip() if isinstance(state_value, str) else ""
                if not state_text:
                    errors.append(f"state.fsms '{name}'.states[{state_index}] must be a non-empty string")
                elif state_text in states:
                    errors.append(f"state.fsms '{name}' duplicate state '{state_text}'")
                else:
                    states.add(state_text)
        if not states:
            errors.append(f"state.fsms '{name}'.states must be non-empty")
        for field_name in ("initial", "reset_state"):
            value = str(fsm.get(field_name, "")).strip()
            if value not in states:
                errors.append(f"state.fsms '{name}'.{field_name} '{value}' is not declared in states")
        fsm_defs[name] = states
        state_names.add(f"{name}.state")
    return fsm_defs


def _data_flow_names(
    data_flow: list[Any],
    top_ports: set[str],
    instance_ports: dict[str, set[str]],
    errors: list[str],
) -> set[str]:
    names: set[str] = set()
    for index, flow in enumerate(data_flow):
        if not isinstance(flow, dict):
            errors.append(f"data_flow[{index}] must be an object")
            continue
        name = str(flow.get("name", "")).strip()
        if not name:
            errors.append(f"data_flow[{index}].name is required")
            continue
        if name in names:
            errors.append(f"data_flow duplicate flow '{name}'")
        names.add(name)
        if not str(flow.get("protocol", "")).strip():
            errors.append(f"data_flow '{name}'.protocol is required")
        payload = flow.get("payload")
        if "payload" in flow:
            _mapping(payload, f"data_flow '{name}'.payload", errors)
        path = _list(flow.get("path"), f"data_flow '{name}'.path", errors)
        for endpoint in path:
            endpoint_text = str(endpoint).strip() if isinstance(endpoint, str) else ""
            if not _is_valid_endpoint(endpoint_text, top_ports, instance_ports):
                errors.append(f"data_flow '{name}' endpoint '{endpoint_text}' is not a valid top or instance port")
        if "timing" in flow:
            _validate_data_flow_timing(name, flow.get("timing"), errors)
    return names


def _validate_data_flow_timing(flow_name: str, timing: Any, errors: list[str]) -> None:
    if not isinstance(timing, dict):
        errors.append(f"data_flow '{flow_name}'.timing must be an object")
        return
    latency_cycles = timing.get("latency_cycles")
    if not _is_non_bool_int(latency_cycles) or latency_cycles < 0:
        errors.append(f"data_flow '{flow_name}'.timing.latency_cycles must be a non-negative integer")
    initiation_interval = timing.get("initiation_interval")
    if not _is_non_bool_int(initiation_interval) or initiation_interval <= 0:
        errors.append(f"data_flow '{flow_name}'.timing.initiation_interval must be a positive integer")
    if "throughput" in timing and not str(timing.get("throughput", "")).strip():
        errors.append(f"data_flow '{flow_name}'.timing.throughput must be a non-empty string")


def _is_non_bool_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _is_valid_endpoint(endpoint: str, top_ports: set[str], instance_ports: dict[str, set[str]]) -> bool:
    if "." not in endpoint:
        return False
    owner, port = endpoint.split(".", 1)
    if owner == "top":
        return port in top_ports
    return port in instance_ports.get(owner, set())


def _validate_instance_state_ownership(instances: list[Any], state_names: set[str], errors: list[str]) -> None:
    for index, instance in enumerate(instances):
        if not isinstance(instance, dict):
            continue
        name = str(instance.get("name", "")).strip() or f"instances[{index}]"
        owns_state = _list(instance.get("owns_state"), f"instance '{name}'.owns_state", errors)
        for state_name in owns_state:
            state_text = str(state_name).strip() if isinstance(state_name, str) else ""
            if state_text not in state_names:
                errors.append(f"instance '{name}' owns missing state '{state_text}'")


def _validate_control_flow(
    control_flow: list[Any],
    state_names: set[str],
    data_flow_names: set[str],
    top_ports: set[str],
    instance_ports: dict[str, set[str]],
    fsm_defs: dict[str, set[str]],
    errors: list[str],
) -> None:
    guard_signals = _guard_signals(top_ports, instance_ports, state_names, data_flow_names)
    effect_targets = _effect_targets(instance_ports, state_names, data_flow_names)
    for index, rule in enumerate(control_flow):
        if not isinstance(rule, dict):
            errors.append(f"control_flow[{index}] must be an object")
            continue
        name = str(rule.get("name", "")).strip()
        if not name:
            errors.append(f"control_flow[{index}].name is required")
            name = f"control_flow[{index}]"
        related_state = _list(rule.get("related_state"), f"control_flow '{name}'.related_state", errors)
        for state_name in related_state:
            state_text = str(state_name).strip() if isinstance(state_name, str) else ""
            if state_text not in state_names:
                errors.append(f"control_flow '{name}' references missing state '{state_text}'")
        related_flows = _list(rule.get("related_flows"), f"control_flow '{name}'.related_flows", errors)
        for flow_name in related_flows:
            flow_text = str(flow_name).strip() if isinstance(flow_name, str) else ""
            if flow_text not in data_flow_names:
                errors.append(f"control_flow '{name}' references missing data_flow '{flow_text}'")
        kind = str(rule.get("kind", "")).strip()
        if not kind:
            errors.append(f"control_flow '{name}'.kind is required")
        elif kind not in CONTROL_FLOW_KINDS:
            errors.append(f"control_flow '{name}'.kind '{kind}' is invalid")
        if kind == "fsm_transition":
            _validate_fsm_transition(rule, name, fsm_defs, guard_signals, effect_targets, errors)
        elif "when" in rule or "effect" in rule:
            _validate_structured_enable_rule(rule, name, guard_signals, effect_targets, errors)


def _guard_signals(
    top_ports: set[str],
    instance_ports: dict[str, set[str]],
    state_names: set[str],
    data_flow_names: set[str],
) -> set[str]:
    signals = set(state_names) | set(data_flow_names)
    for port in top_ports:
        signals.add(port)
        signals.add(f"top.{port}")
    for instance_name, ports in instance_ports.items():
        for port in ports:
            signals.add(f"{instance_name}.{port}")
    return signals


def _effect_targets(
    instance_ports: dict[str, set[str]],
    state_names: set[str],
    data_flow_names: set[str],
) -> set[str]:
    return set(instance_ports) | set(state_names) | set(data_flow_names)


def _validate_fsm_transition(
    rule: dict[str, Any],
    name: str,
    fsm_defs: dict[str, set[str]],
    guard_signals: set[str],
    effect_targets: set[str],
    errors: list[str],
) -> None:
    fsm = str(rule.get("fsm", "")).strip()
    states = fsm_defs.get(fsm)
    if states is None:
        errors.append(f"control_flow '{name}'.fsm '{fsm}' is not declared")
        states = set()
    for endpoint in ("from", "to"):
        value = str(rule.get(endpoint, "")).strip()
        if value not in states:
            errors.append(f"control_flow '{name}'.{endpoint} '{value}' is not a state of FSM '{fsm}'")
    _validate_guard(rule.get("when"), guard_signals, f"control_flow '{name}'.when", errors)
    if "effect" in rule:
        _validate_effect(rule.get("effect"), effect_targets, f"control_flow '{name}'.effect", errors)


def _validate_structured_enable_rule(
    rule: dict[str, Any],
    name: str,
    guard_signals: set[str],
    effect_targets: set[str],
    errors: list[str],
) -> None:
    _validate_guard(rule.get("when"), guard_signals, f"control_flow '{name}'.when", errors)
    _validate_effect(rule.get("effect"), effect_targets, f"control_flow '{name}'.effect", errors)


def _validate_guard(
    guard: Any,
    valid_signals: set[str],
    context: str,
    errors: list[str],
    depth: int = 0,
) -> None:
    if not isinstance(guard, dict):
        errors.append(f"{context} must be an object")
        return
    combinators = [key for key in ("all_of", "any_of") if key in guard]
    if combinators:
        for combinator in combinators:
            next_depth = depth + 1
            if next_depth > 2:
                errors.append(f"{context} guard nesting depth exceeds 2")
            children = guard.get(combinator)
            if not isinstance(children, list):
                errors.append(f"{context}.{combinator} must be a list")
                continue
            for child in children:
                _validate_guard(child, valid_signals, f"{context}.{combinator}", errors, next_depth)
        return
    signal = str(guard.get("signal", "")).strip()
    if signal not in valid_signals:
        errors.append(f"{context} signal '{signal}' is not declared")
    op = str(guard.get("op", "")).strip()
    if op not in GUARD_OPERATORS:
        errors.append(f"{context} operator '{op}' is not allowed")
    if "value" not in guard:
        errors.append(f"{context}.value is required")


def _validate_effect(effect: Any, valid_targets: set[str], context: str, errors: list[str]) -> None:
    if not isinstance(effect, dict):
        errors.append(f"{context} must be an object")
        return
    target = str(effect.get("target", "")).strip()
    if target not in valid_targets:
        errors.append(f"{context}.target '{target}' is not declared")


def _validate_v12_artifacts_against_project(
    artifacts: dict[str, Any],
    project: GeneratedProject,
    sources: list[str],
    top_module: str,
    rtl_ports: dict[str, dict[str, dict[str, Any]]],
    errors: list[str],
) -> None:
    manifest_path = str(artifacts.get("manifest", "")).strip()
    manifest = _read_v12_project_json(project, manifest_path, errors)
    if manifest is not None:
        manifest_top = str(manifest.get("top_module", "")).strip()
        if top_module and manifest_top and top_module != manifest_top:
            errors.append(f"manifest.top_module '{manifest_top}' does not match System-HIS v1.2 artifacts.top_module '{top_module}'")
        manifest_sources = _v12_string_list(manifest.get("sources"), "manifest.sources", errors)
        if manifest_sources and manifest_sources != sources:
            errors.append("manifest.sources does not match System-HIS v1.2 artifacts.rtl_sources")
        testbench = _manifest_testbench_v12(manifest)
        if testbench:
            _validate_v12_testbench_instantiates_top(project, testbench, top_module, errors)
        else:
            errors.append("manifest.simulation.testbench is required")
        timing_constraint = _manifest_timing_constraint_v12(manifest)
        if timing_constraint:
            _validate_v12_timing_constraint_ports(project, timing_constraint, top_module, rtl_ports, errors)
        else:
            errors.append("manifest.constraints.timing is required")
    testbench_path = str(artifacts.get("testbench", "")).strip()
    if testbench_path and testbench_path not in project.files:
        errors.append(f"system_his.artifacts.testbench '{testbench_path}' is missing from project files")
    constraints = _v12_string_list(artifacts.get("constraints"), "system_his.artifacts.constraints", errors)
    for constraint in constraints:
        if constraint not in project.files:
            errors.append(f"system_his.artifacts.constraints entry '{constraint}' is missing from project files")


def _validate_v12_top_against_rtl(
    top: Any,
    top_module: str,
    rtl_ports: dict[str, dict[str, dict[str, Any]]],
    errors: list[str],
) -> None:
    if not isinstance(top, dict) or not top_module:
        return
    top_name = str(top.get("name", "")).strip()
    if top_name and top_name != top_module:
        errors.append(f"system_his.top.name '{top_name}' does not match artifacts.top_module '{top_module}'")
    _validate_v12_port_records("top", _his_port_records(top.get("ports")), rtl_ports.get(top_module, {}), errors)


def _validate_v12_components_against_rtl(
    components: Any,
    sources: list[str],
    rtl_modules: set[str],
    rtl_ports: dict[str, dict[str, dict[str, Any]]],
    project: GeneratedProject,
    errors: list[str],
) -> dict[str, set[str]]:
    component_ports: dict[str, set[str]] = {}
    if not isinstance(components, list):
        return component_ports
    source_set = set(sources)
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            continue
        name = str(component.get("name", "")).strip()
        source = str(component.get("source", "")).strip()
        if not name:
            continue
        if source and source not in source_set:
            errors.append(f"component '{name}' source '{source}' is not in artifacts.rtl_sources")
        if source and source not in project.files:
            errors.append(f"component '{name}' source '{source}' is missing from project files")
        if name not in rtl_modules:
            errors.append(f"component '{name}' is not declared in System-HIS v1.2 RTL sources")
        elif source and name not in declared_modules(project.files, [source]):
            errors.append(f"component '{name}' is not declared in source '{source}'")
        ports = _his_port_records(component.get("ports"))
        component_ports[name] = {port_name for port_name, _ in ports}
        _validate_v12_port_records(f"component '{name}'", ports, rtl_ports.get(name, {}), errors)
    return component_ports


def _validate_v12_port_records(
    owner: str,
    his_ports: list[tuple[str, dict[str, Any]]],
    rtl_ports: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for port_name, port in his_ports:
        if port_name not in rtl_ports:
            errors.append(f"{owner} port '{port_name}' is not declared in RTL")
            continue
        direction = _his_direction(port)
        rtl_direction = str(rtl_ports[port_name].get("direction", "")).strip()
        if direction and direction != rtl_direction:
            errors.append(f"{owner} port '{port_name}' direction '{direction}' does not match RTL '{rtl_direction}'")
        width = _his_width(port.get("width"))
        if "width" in port and not widths_equivalent(width, rtl_ports[port_name].get("width")):
            errors.append(f"{owner} port '{port_name}' width {width} does not match RTL {rtl_ports[port_name].get('width')}")


def _his_port_records(value: Any) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(value, list):
        return []
    records: list[tuple[str, dict[str, Any]]] = []
    for port in value:
        if isinstance(port, dict):
            name = str(port.get("name", "")).strip()
            if name:
                records.append((name, port))
    return records


def _his_direction(port: dict[str, Any]) -> str:
    direction = str(port.get("direction", port.get("dir", ""))).strip()
    if direction == "in":
        return "input"
    if direction == "out":
        return "output"
    return direction


def _his_width(value: Any) -> Any:
    return value


def _v12_instance_components(
    instances: Any,
    component_ports: dict[str, set[str]],
    errors: list[str],
) -> dict[str, str]:
    instance_components: dict[str, str] = {}
    if not isinstance(instances, list):
        return instance_components
    for instance in instances:
        if not isinstance(instance, dict):
            continue
        name = str(instance.get("name", "")).strip()
        component = str(instance.get("component", "")).strip()
        if not name:
            continue
        if component not in component_ports:
            errors.append(f"instance '{name}' references component '{component}' without RTL ports")
        instance_components[name] = component
    return instance_components


def _validate_v12_instances_in_top(
    instance_components: dict[str, str],
    component_ports: dict[str, set[str]],
    top_module: str,
    project: GeneratedProject,
    errors: list[str],
) -> None:
    top_content = _module_source_content(project, top_module)
    if not top_content:
        return
    for instance_name, component_name in instance_components.items():
        if component_name not in component_ports:
            continue
        pattern = re.compile(
            rf"\b{re.escape(component_name)}\b\s*(?:#\s*\(.*?\)\s*)?{re.escape(instance_name)}\s*\(",
            re.DOTALL,
        )
        if pattern.search(top_content) is None:
            errors.append(f"instance '{instance_name}' of component '{component_name}' is not instantiated in top RTL")


def _validate_v12_data_flow_against_rtl(
    data_flow: Any,
    top_module: str,
    rtl_ports: dict[str, dict[str, dict[str, Any]]],
    instance_components: dict[str, str],
    errors: list[str],
) -> None:
    if not isinstance(data_flow, list):
        return
    for flow in data_flow:
        if not isinstance(flow, dict):
            continue
        flow_name = str(flow.get("name", "")).strip() or "<unnamed>"
        path = flow.get("path")
        if not isinstance(path, list):
            continue
        for endpoint in path:
            endpoint_text = str(endpoint).strip() if isinstance(endpoint, str) else ""
            if "." not in endpoint_text:
                continue
            owner, port = endpoint_text.split(".", 1)
            if owner == "top":
                if port not in rtl_ports.get(top_module, {}):
                    errors.append(f"data_flow '{flow_name}' endpoint '{endpoint_text}' is not declared in RTL")
                continue
            component = instance_components.get(owner, "")
            if port not in rtl_ports.get(component, {}):
                errors.append(f"data_flow '{flow_name}' endpoint '{endpoint_text}' is not declared in RTL")


def _validate_v12_fsm_states_against_rtl(
    state: Any,
    instance_components: dict[str, str],
    top_module: str,
    rtl_ports: dict[str, dict[str, dict[str, Any]]],
    project: GeneratedProject,
    errors: list[str],
) -> None:
    if not isinstance(state, dict):
        return
    fsms = state.get("fsms")
    if not isinstance(fsms, list):
        return
    for fsm in fsms:
        if not isinstance(fsm, dict):
            continue
        owner = _v12_state_owner(fsm)
        module = instance_components.get(owner, owner or top_module)
        if module not in rtl_ports:
            continue
        content = _module_source_content(project, module)
        states = fsm.get("states")
        if not isinstance(states, list):
            continue
        for state_name in states:
            state_text = str(state_name).strip() if isinstance(state_name, str) else ""
            if state_text and not re.search(rf"\b{re.escape(state_text)}\b", content):
                errors.append(f"state.fsms '{fsm.get('name', '')}' state '{state_text}' is not found in RTL module '{module}'")


def _v12_state_owner(state_item: dict[str, Any]) -> str:
    owner = str(state_item.get("owner", "")).strip()
    if owner:
        return owner
    name = str(state_item.get("name", "")).strip()
    if "." in name:
        return name.split(".", 1)[0]
    return ""


def _read_v12_project_json(project: GeneratedProject, path: str, errors: list[str]) -> dict[str, Any] | None:
    if not path:
        return None
    content = project.files.get(path)
    if content is None:
        errors.append(f"system_his.artifacts.manifest '{path}' is missing from project files")
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        errors.append(f"{path} is not valid JSON: {exc.msg}")
        return None
    if not isinstance(parsed, dict):
        errors.append(f"{path} must contain a JSON object")
        return None
    return parsed


def _v12_string_list(value: Any, name: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    strings: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            strings.append(item)
        else:
            errors.append(f"{name} entries must be non-empty strings")
    return strings


def _manifest_testbench_v12(manifest: dict[str, Any]) -> str:
    simulation = manifest.get("simulation")
    if isinstance(simulation, dict):
        return str(simulation.get("testbench", "")).strip()
    return ""


def _manifest_timing_constraint_v12(manifest: dict[str, Any]) -> str:
    constraints = manifest.get("constraints")
    if isinstance(constraints, dict):
        return str(constraints.get("timing", "")).strip()
    return ""


def _validate_v12_testbench_instantiates_top(
    project: GeneratedProject,
    testbench: str,
    top_module: str,
    errors: list[str],
) -> None:
    if testbench not in project.files:
        errors.append(f"manifest testbench '{testbench}' is missing from project files")
        return
    pattern = re.compile(
        rf"\b{re.escape(top_module)}\b\s*(?:#\s*\(.*?\)\s*)?[A-Za-z_][A-Za-z0-9_$]*\s*\(",
        re.DOTALL,
    )
    if pattern.search(project.files[testbench]) is None:
        errors.append(f"manifest testbench '{testbench}' does not instantiate top module '{top_module}'")


def _validate_v12_timing_constraint_ports(
    project: GeneratedProject,
    timing_constraint: str,
    top_module: str,
    rtl_ports: dict[str, dict[str, dict[str, Any]]],
    errors: list[str],
) -> None:
    if timing_constraint not in project.files:
        errors.append(f"manifest timing constraint '{timing_constraint}' is missing from project files")
        return
    top_ports = set(rtl_ports.get(top_module, {}))
    for port in re.findall(r"\[get_ports\s+\{?([A-Za-z_][A-Za-z0-9_$]*)\}?\]", project.files[timing_constraint]):
        if port not in top_ports:
            errors.append(f"manifest timing constraint '{timing_constraint}' references unknown top port '{port}'")


def _module_source_content(project: GeneratedProject, module_name: str) -> str:
    if not module_name:
        return ""
    pattern = re.compile(rf"\bmodule\s+{re.escape(module_name)}\b")
    for content in project.files.values():
        if pattern.search(content):
            return content
    return ""


def _validate_artifacts(artifacts: dict[str, Any], errors: list[str]) -> None:
    for key in ("top_module", "testbench", "manifest", "predicted_qor"):
        if not str(artifacts.get(key, "")).strip():
            errors.append(f"system_his.artifacts.{key} is required")
    for key in ("rtl_sources", "constraints"):
        values = _list(artifacts.get(key), f"system_his.artifacts.{key}", errors)
        if not values:
            errors.append(f"system_his.artifacts.{key} must be non-empty")


def _artifact_rtl_sources(artifacts: dict[str, Any], errors: list[str]) -> list[str]:
    values = artifacts.get("rtl_sources")
    if not isinstance(values, list):
        return []
    sources: list[str] = []
    for index, value in enumerate(values):
        if isinstance(value, str) and value.strip():
            sources.append(value)
        else:
            errors.append(f"system_his.artifacts.rtl_sources[{index}] must be a non-empty string")
    return sources


def _w1_component_references(payload: dict[str, Any]) -> list[str]:
    components = _named_objects(payload.get("components"))
    diagnostics: list[str] = []
    for index, instance in enumerate(_object_list(payload.get("instances"))):
        component = str(instance.get("component", "")).strip()
        if len(components.get(component, [])) != 1:
            diagnostics.append(f"instances[{index}].component '{component}' does not resolve exactly once")
    return diagnostics


def _w2_endpoint_references(payload: dict[str, Any]) -> list[str]:
    contracts = _endpoint_contracts(payload)
    diagnostics: list[str] = []
    for flow_index, flow in enumerate(_object_list(payload.get("data_flow"))):
        for endpoint_index, endpoint in enumerate(_string_list(flow.get("path"))):
            if endpoint not in contracts:
                diagnostics.append(
                    f"data_flow[{flow_index}].path[{endpoint_index}] endpoint '{endpoint}' does not resolve"
                )
    return diagnostics


def _w3_connection_types(payload: dict[str, Any]) -> list[str] | None:
    typed_connections = _object_list(payload.get("connections")) + [
        connection
        for flow in _object_list(payload.get("data_flow"))
        for connection in _object_list(flow.get("connections"))
    ]
    if not typed_connections:
        return None
    contracts = _endpoint_contracts(payload)
    diagnostics: list[str] = []
    for connection_index, connection in enumerate(typed_connections):
        source_name = _typed_endpoint_name(connection.get("from"), payload)
        target_name = _typed_endpoint_name(connection.get("to"), payload)
        source = contracts.get(source_name)
        target = contracts.get(target_name)
        if source is None:
            diagnostics.append(f"typed connection[{connection_index}] source '{source_name}' does not resolve")
        if target is None:
            diagnostics.append(f"typed connection[{connection_index}] target '{target_name}' does not resolve")
        if source is None or target is None:
            continue
        if source["width"] is not None and target["width"] is not None and not widths_equivalent(
            source["width"], target["width"]
        ):
            diagnostics.append(
                f"typed connection[{connection_index}] '{source_name}' -> '{target_name}' has incompatible widths"
            )
        declared_width = _resolved_width(connection.get("width"))
        if isinstance(declared_width, int) and not isinstance(declared_width, bool):
            for endpoint_name, endpoint in ((source_name, source), (target_name, target)):
                if endpoint["width"] is not None and not widths_equivalent(declared_width, endpoint["width"]):
                    diagnostics.append(
                        f"typed connection[{connection_index}] width {declared_width} is incompatible with endpoint '{endpoint_name}'"
                    )
        if source["owner"] == target["owner"]:
            compatible = source["role"] in {"sink", "bidirectional"} and target["role"] in {
                "source",
                "bidirectional",
            }
        else:
            compatible = source["role"] in {"source", "bidirectional"} and target["role"] in {
                "sink",
                "bidirectional",
            }
        if not compatible:
            diagnostics.append(
                f"typed connection[{connection_index}] '{source_name}' -> '{target_name}' has incompatible directions"
            )
    return diagnostics


def _typed_endpoint_name(value: Any, payload: dict[str, Any]) -> str:
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, dict):
        return ""
    port = str(value.get("port", "")).strip()
    instance = str(value.get("instance", "")).strip()
    module = str(value.get("module", "")).strip()
    top = payload.get("top") if isinstance(payload.get("top"), dict) else {}
    top_name = str(top.get("name", "")).strip()
    owner = instance or ("top" if module in {"top", top_name} else module)
    return f"{owner}.{port}" if owner and port else ""


def _w4_state_clock_reset_bindings(payload: dict[str, Any]) -> list[str]:
    top = payload.get("top") if isinstance(payload.get("top"), dict) else {}
    clocks = set(_object_names(top.get("clocks")))
    resets = set(_object_names(top.get("resets")))
    state_owners: set[str] = set()
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
    for group in STATE_GROUPS:
        for item in _object_list(state.get(group)):
            owner = str(item.get("owner", "")).strip()
            if owner and owner != "top":
                state_owners.add(owner)
    diagnostics: list[str] = []
    instances = _object_list(payload.get("instances"))
    instance_names = {str(instance.get("name", "")).strip() for instance in instances}
    for owner in sorted(state_owners - instance_names):
        diagnostics.append(f"state owner '{owner}' is not a declared instance")
    for index, instance in enumerate(instances):
        name = str(instance.get("name", "")).strip()
        owns_state = bool(instance.get("owns_state")) or name in state_owners
        if not owns_state:
            continue
        clock = str(instance.get("clock", "")).strip()
        reset = str(instance.get("reset", "")).strip()
        if clock not in clocks:
            diagnostics.append(f"state-owning instance '{name}' clock '{clock}' is not declared")
        if reset not in resets:
            diagnostics.append(f"state-owning instance '{name}' reset '{reset}' is not declared")
    primary_clock = str(payload.get("timing", {}).get("primary_clock", "")).strip() if isinstance(payload.get("timing"), dict) else ""
    if primary_clock and primary_clock not in clocks:
        diagnostics.append(f"timing.primary_clock '{primary_clock}' is not declared")
    return diagnostics


def _w5_combinational_state(payload: dict[str, Any]) -> list[str] | None:
    declarations = [
        component
        for component in _object_list(payload.get("components"))
        if "combinational" in component
    ]
    if not declarations:
        return None
    combinational = {
        str(component.get("name", "")).strip()
        for component in declarations
        if component.get("combinational") is True
    }
    diagnostics: list[str] = []
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
    state_owners = {
        str(item.get("owner", "")).strip()
        for group in STATE_GROUPS
        for item in _object_list(state.get(group))
    }
    for instance in _object_list(payload.get("instances")):
        component = str(instance.get("component", "")).strip()
        if component not in combinational:
            continue
        name = str(instance.get("name", "")).strip()
        if instance.get("owns_state") or name in state_owners:
            diagnostics.append(f"combinational component instance '{name}' owns state")
    top = payload.get("top") if isinstance(payload.get("top"), dict) else {}
    top_name = str(top.get("name", "")).strip()
    clock_reset_names = set(_object_names(top.get("clocks"))) | set(_object_names(top.get("resets")))
    for component in _object_list(payload.get("components")):
        component_name = str(component.get("name", "")).strip()
        if component_name == top_name or component_name not in combinational:
            continue
        owned_clock_reset_ports = clock_reset_names & set(_object_names(component.get("ports")))
        for port_name in sorted(owned_clock_reset_ports):
            diagnostics.append(
                f"combinational component '{component.get('name')}' declares clock/reset port '{port_name}'"
            )
    return diagnostics


def _w6_cdc_paths(payload: dict[str, Any]) -> list[str] | None:
    flows = [flow for flow in _object_list(payload.get("data_flow")) if flow.get("cdc") is True]
    if not flows:
        return None
    contracts = _endpoint_contracts(payload)
    component_kinds = {
        str(component.get("name", "")).strip(): str(component.get("semantic_kind", "")).strip().lower()
        for component in _object_list(payload.get("components"))
    }
    instance_components = {
        str(instance.get("name", "")).strip(): str(instance.get("component", "")).strip()
        for instance in _object_list(payload.get("instances"))
    }
    diagnostics: list[str] = []
    for flow in flows:
        name = str(flow.get("name", "")).strip()
        endpoints = _string_list(flow.get("path"))
        endpoint_clocks = [contracts[endpoint]["clock"] for endpoint in endpoints if endpoint in contracts and contracts[endpoint]["clock"]]
        if len(set(endpoint_clocks)) < 2:
            diagnostics.append(f"cdc data_flow '{name}' does not cross two declared clock domains")
        owners = {contracts[endpoint]["owner"] for endpoint in endpoints if endpoint in contracts}
        has_cdc_primitive = any(
            component_kinds.get(instance_components.get(owner, ""), "")
            in {"synchronizer", "cdc", "cdc_primitive", "async_fifo"}
            for owner in owners
        )
        if not has_cdc_primitive:
            diagnostics.append(f"cdc data_flow '{name}' has no synchronizer or declared CDC primitive")
    return diagnostics


def _w7_memory_intent(payload: dict[str, Any]) -> list[str] | None:
    state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
    memories = _object_list(state.get("memories"))
    if not memories:
        return None
    diagnostics: list[str] = []
    for index, memory in enumerate(memories):
        for field_name in ("depth", "width", "read_latency", "read_type", "memory_style"):
            value = memory.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                diagnostics.append(f"state.memories[{index}].{field_name} is required")
        for field_name in ("depth", "read_latency"):
            value = memory.get(field_name)
            if value is not None and (not _is_non_bool_int(value) or value < (0 if field_name == "read_latency" else 1)):
                diagnostics.append(f"state.memories[{index}].{field_name} is invalid")
        width = _resolved_width(memory.get("width"))
        if width is not None and (not _is_non_bool_int(width) or width <= 0):
            diagnostics.append(f"state.memories[{index}].width is invalid")
    return diagnostics


def _w8_verification_references(payload: dict[str, Any]) -> list[str]:
    verification = payload.get("verification") if isinstance(payload.get("verification"), dict) else {}
    flow_names = set(_object_names(payload.get("data_flow")))
    control_names = set(_object_names(payload.get("control_flow")))
    signal_names = set(_endpoint_contracts(payload))
    diagnostics: list[str] = []
    for index, scenario in enumerate(_object_list(verification.get("scenarios"))):
        for field_name, valid_names in (
            ("related_flows", flow_names),
            ("related_control", control_names),
            ("signals", signal_names),
        ):
            for reference in _string_list(scenario.get(field_name)):
                if reference not in valid_names:
                    diagnostics.append(
                        f"verification.scenarios[{index}].{field_name} reference '{reference}' is not declared"
                    )
    return diagnostics


def _w9_constraint_references(payload: dict[str, Any]) -> list[str]:
    top = payload.get("top") if isinstance(payload.get("top"), dict) else {}
    timing = payload.get("timing") if isinstance(payload.get("timing"), dict) else {}
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), dict) else {}
    diagnostics: list[str] = []
    primary_clock = str(timing.get("primary_clock", "")).strip()
    if primary_clock not in set(_object_names(top.get("clocks"))):
        diagnostics.append(f"timing.primary_clock '{primary_clock}' is not declared")
    timing_constraints = set(_string_list(timing.get("constraints")))
    artifact_constraints = set(_string_list(artifacts.get("constraints")))
    for path in sorted(timing_constraints - artifact_constraints):
        diagnostics.append(f"timing constraint '{path}' is not declared in artifacts.constraints")
    return diagnostics


def _w10_artifact_reproducibility(payload: dict[str, Any]) -> list[str]:
    top = payload.get("top") if isinstance(payload.get("top"), dict) else {}
    timing = payload.get("timing") if isinstance(payload.get("timing"), dict) else {}
    verification = payload.get("verification") if isinstance(payload.get("verification"), dict) else {}
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), dict) else {}
    diagnostics: list[str] = []
    if str(artifacts.get("top_module", "")).strip() != str(top.get("name", "")).strip():
        diagnostics.append("artifacts.top_module does not match top.name")
    if str(artifacts.get("manifest", "")).strip() != "manifest.json":
        diagnostics.append("artifacts.manifest must be manifest.json")
    if str(artifacts.get("testbench", "")).strip() != str(verification.get("testbench", "")).strip():
        diagnostics.append("artifacts.testbench does not match verification.testbench")
    if set(_string_list(artifacts.get("constraints"))) != set(_string_list(timing.get("constraints"))):
        diagnostics.append("artifacts.constraints does not match timing.constraints")
    sources = set(_string_list(artifacts.get("rtl_sources")))
    for component in _object_list(payload.get("components")):
        source = str(component.get("source", "")).strip()
        if source and source not in sources:
            diagnostics.append(f"component source '{source}' is not reproducible from artifacts.rtl_sources")
    return diagnostics


def _endpoint_contracts(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    top = payload.get("top") if isinstance(payload.get("top"), dict) else {}
    primary_clock = str(payload.get("timing", {}).get("primary_clock", "")).strip() if isinstance(payload.get("timing"), dict) else ""
    top_parameters = {
        str(parameter.get("name", "")).strip(): parameter.get("value", parameter.get("default"))
        for parameter in _object_list(top.get("parameters"))
    }
    for port in _object_list(top.get("ports")):
        name = str(port.get("name", "")).strip()
        direction = _normalized_direction(port)
        role = {"input": "source", "output": "sink", "inout": "bidirectional"}.get(direction, "unknown")
        contracts[f"top.{name}"] = {
            "owner": "top",
            "role": role,
            "width": _resolved_width(port.get("width"), top_parameters),
            "clock": primary_clock,
        }
    component_ports: dict[str, list[dict[str, Any]]] = {}
    for component in _object_list(payload.get("components")):
        component_ports.setdefault(
            str(component.get("name", "")).strip(),
            _object_list(component.get("ports")),
        )
    for instance in _object_list(payload.get("instances")):
        owner = str(instance.get("name", "")).strip()
        component = str(instance.get("component", "")).strip()
        parameter_values = instance.get("parameter_values") if isinstance(instance.get("parameter_values"), dict) else {}
        for port in component_ports.get(component, []):
            name = str(port.get("name", "")).strip()
            direction = _normalized_direction(port)
            role = {"input": "sink", "output": "source", "inout": "bidirectional"}.get(direction, "unknown")
            contracts.setdefault(f"{owner}.{name}", {
                "owner": owner,
                "role": role,
                "width": _resolved_width(port.get("width"), parameter_values),
                "clock": str(instance.get("clock", "")).strip(),
            })
    return contracts


def _normalized_direction(port: dict[str, Any]) -> str:
    value = str(port.get("dir", port.get("direction", ""))).strip()
    return {"in": "input", "out": "output"}.get(value, value)


def _resolved_width(value: Any, parameters: dict[str, Any] | None = None) -> Any:
    if isinstance(value, dict):
        value = value.get("resolved", value.get("expr"))
    if not isinstance(value, str) or not parameters:
        return value
    text = value.strip()
    range_match = re.fullmatch(r"\[(.+):\s*0\]", text)
    expression = range_match.group(1) if range_match else text
    resolved = _evaluate_width_expression(expression, parameters)
    if resolved is None:
        return value
    return resolved + 1 if range_match else resolved


def _evaluate_width_expression(expression: str, parameters: dict[str, Any]) -> int | None:
    try:
        root = ast.parse(expression, mode="eval").body
    except SyntaxError:
        return None

    def evaluate(node: ast.AST) -> int:
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name):
            value = parameters.get(node.id)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
            raise ValueError
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            return left * right
        raise ValueError

    try:
        value = evaluate(root)
    except ValueError:
        return None
    return value if value > 0 else None


def _named_objects(value: Any) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for item in _object_list(value):
        result.setdefault(str(item.get("name", "")).strip(), []).append(item)
    return result


def _object_names(value: Any) -> list[str]:
    return [str(item.get("name", "")).strip() for item in _object_list(value)]


def _object_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item).strip() for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []
