"""Structural checks for the System-HIS v1.2 top-down prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SCHEMA_VERSION = "system-his-v1.2-topdown"
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


def check_system_his_v12(payload: dict[str, Any]) -> SystemHisV12CheckResult:
    """Validate v1.2 top-down System-HIS internal structure.

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

    top = _mapping(payload.get("top"), "system_his.top", errors)
    components = _list(payload.get("components"), "system_his.components", errors)
    instances = _list(payload.get("instances"), "system_his.instances", errors)
    state = _mapping(payload.get("state"), "system_his.state", errors)
    data_flow = _list(payload.get("data_flow"), "system_his.data_flow", errors)
    control_flow = _list(payload.get("control_flow"), "system_his.control_flow", errors)
    artifacts = _mapping(payload.get("artifacts"), "system_his.artifacts", errors)

    top_ports = _top_ports(top, errors)
    component_ports = _component_ports(components, errors)
    instance_components = _instance_components(instances, component_ports, errors)
    instance_ports = {
        instance_name: component_ports.get(component_name, set())
        for instance_name, component_name in instance_components.items()
    }
    state_names = _state_names(state, errors)
    data_flow_names = _data_flow_names(data_flow, top_ports, instance_ports, errors)
    _validate_instance_state_ownership(instances, state_names, errors)
    _validate_control_flow(control_flow, state_names, data_flow_names, errors)
    _validate_artifacts(artifacts, errors)

    return SystemHisV12CheckResult(passed=not errors, errors=errors, warnings=warnings)


def _validate_required_keys(payload: dict[str, Any], errors: list[str]) -> None:
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            errors.append(f"system_his.{key} is required")


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


def _component_ports(components: list[Any], errors: list[str]) -> dict[str, set[str]]:
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


def _instance_components(
    instances: list[Any],
    component_ports: dict[str, set[str]],
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
        path = _list(flow.get("path"), f"data_flow '{name}'.path", errors)
        for endpoint in path:
            endpoint_text = str(endpoint).strip() if isinstance(endpoint, str) else ""
            if not _is_valid_endpoint(endpoint_text, top_ports, instance_ports):
                errors.append(f"data_flow '{name}' endpoint '{endpoint_text}' is not a valid top or instance port")
    return names


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
    errors: list[str],
) -> None:
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


def _validate_artifacts(artifacts: dict[str, Any], errors: list[str]) -> None:
    for key in ("top_module", "testbench", "manifest", "predicted_qor"):
        if not str(artifacts.get(key, "")).strip():
            errors.append(f"system_his.artifacts.{key} is required")
    for key in ("rtl_sources", "constraints"):
        values = _list(artifacts.get(key), f"system_his.artifacts.{key}", errors)
        if not values:
            errors.append(f"system_his.artifacts.{key} must be non-empty")
