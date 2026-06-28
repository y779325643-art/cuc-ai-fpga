"""Contract-preserving skeleton generation from System-HIS v1.2."""

from __future__ import annotations

import json
from typing import Any

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


def build_contract_skeleton_project(
    request: ProjectRequest,
    platform: PlatformProfile,
    system_his: dict[str, Any],
) -> GeneratedProject:
    """Build deterministic project structure from a checked System-HIS contract."""

    artifacts = _mapping(system_his.get("artifacts"))
    top = _mapping(system_his.get("top"))
    top_module = str(artifacts.get("top_module") or top.get("name") or "top")
    sources = _string_list(artifacts.get("rtl_sources")) or ["rtl/top.v"]
    components = [_mapping(component) for component in _list(system_his.get("components"))]
    components_by_source = {str(component.get("source")): component for component in components}
    component_names = {str(component.get("name")) for component in components}

    files: dict[str, str] = {
        "system_his.json": _json(system_his),
        "manifest.json": _json(_manifest(request, platform, system_his, top_module, sources)),
    }
    for source in sources:
        if source == _top_source(sources):
            files[source] = _top_module(system_his, top_module, components_by_source)
        elif source in components_by_source:
            files[source] = _component_module(components_by_source[source], system_his)
        else:
            files[source] = _placeholder_module(source, component_names, system_his)
    files["constraints/timing.sdc"] = _timing_sdc(system_his)
    files["sim/tb_top.v"] = _testbench(system_his, top_module)
    files["reports/predicted_qor.json"] = _json(_predicted_qor(system_his))
    return GeneratedProject(project_name=request.project_name, files=files)


def merge_behavior_files(
    skeleton: GeneratedProject,
    behavior_files: dict[str, str],
) -> GeneratedProject:
    """Fill BEHAVIOR_HOLE markers while preserving deterministic structure."""

    files = dict(skeleton.files)
    required_paths = {path for path, content in files.items() if "BEHAVIOR_HOLE" in content}
    for path, behavior in behavior_files.items():
        if path not in files:
            raise ValueError(f"behavior file '{path}' is not part of the deterministic skeleton")
        if "BEHAVIOR_HOLE" not in files[path]:
            raise ValueError(f"behavior file '{path}' does not contain a BEHAVIOR_HOLE")
    missing = sorted(required_paths - set(behavior_files))
    if missing:
        raise ValueError(f"missing behavior for: {', '.join(missing)}")
    for path, behavior in behavior_files.items():
        files[path] = _fill_behavior_hole(files[path], behavior)
    return GeneratedProject(project_name=skeleton.project_name, files=files)


def _fill_behavior_hole(content: str, behavior: str) -> str:
    behavior_lines = behavior.strip("\n").splitlines() or ["// empty behavior body"]
    indented = "\n".join(f"  {line}" if line.strip() else "" for line in behavior_lines)
    return content.replace("  // BEHAVIOR_HOLE: model-generated RTL behavior goes here.", indented, 1)


def _manifest(
    request: ProjectRequest,
    platform: PlatformProfile,
    system_his: dict[str, Any],
    top_module: str,
    sources: list[str],
) -> dict[str, Any]:
    return {
        "project_name": request.project_name,
        "top_module": top_module,
        "language": "verilog",
        "target": {
            "vendor": platform.vendor,
            "family": platform.family,
            "part": platform.part,
            "board": platform.board,
            "toolchain": platform.toolchain,
        },
        "sources": sources,
        "constraints": {"timing": _first_string(_mapping(system_his.get("timing")).get("constraints"), "constraints/timing.sdc")},
        "simulation": {"testbench": _mapping(system_his.get("verification")).get("testbench", "sim/tb_top.v")},
        "reports": {"predicted_qor": "reports/predicted_qor.json"},
    }


def _top_module(
    system_his: dict[str, Any],
    top_module: str,
    components_by_source: dict[str, dict[str, Any]],
) -> str:
    top = _mapping(system_his.get("top"))
    ports = _list(top.get("ports"))
    instances = _list(system_his.get("instances"))
    components_by_name = {str(component.get("name")): component for component in components_by_source.values()}
    lines = [
        f"module {top_module}{_parameter_block(_list(top.get('parameters')))} (",
        _port_block(ports),
        ");",
        "",
    ]
    declared_wires: set[str] = set()
    for instance in instances:
        instance_map = _mapping(instance)
        component = components_by_name.get(str(instance_map.get("component")), {})
        for port in _list(component.get("ports")):
            port_map = _mapping(port)
            port_name = str(port_map.get("name", "")).strip()
            if not port_name or _is_top_passthrough(port_name, instance_map):
                continue
            wire_name = _instance_wire(str(instance_map.get("name")), port_name)
            if wire_name in declared_wires:
                continue
            declared_wires.add(wire_name)
            lines.append(f"  wire{_range(port_map.get('width'))} {wire_name};")
    if declared_wires:
        lines.append("")
    for instance in instances:
        instance_map = _mapping(instance)
        component = components_by_name.get(str(instance_map.get("component")), {})
        lines.extend(_instance_lines(instance_map, component))
        lines.append("")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


def _component_module(component: dict[str, Any], system_his: dict[str, Any]) -> str:
    name = str(component.get("name", "")).strip()
    states = _fsm_states_for_component(name, system_his)
    lines = [
        f"module {name}{_parameter_block(_list(component.get('parameters')))} (",
        _port_block(_list(component.get("ports"))),
        ");",
        "  // BEHAVIOR_HOLE: model-generated RTL behavior goes here.",
    ]
    for state in states:
        lines.append(f"  localparam {state} = 0;")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


def _placeholder_module(source: str, component_names: set[str], system_his: dict[str, Any]) -> str:
    stem = source.rsplit("/", 1)[-1].removesuffix(".v")
    name = stem if stem not in component_names else f"{stem}_skeleton"
    return _component_module({"name": name, "ports": []}, system_his)


def _instance_lines(instance: dict[str, Any], component: dict[str, Any]) -> list[str]:
    component_name = str(instance.get("component", "")).strip()
    instance_name = str(instance.get("name", "")).strip()
    ports = _list(component.get("ports"))
    lines = [f"  {component_name}{_parameter_override_block(_mapping(instance.get('parameter_values')))} {instance_name} ("]
    connections = []
    for port in ports:
        port_name = str(_mapping(port).get("name", "")).strip()
        if not port_name:
            continue
        signal = port_name if _is_top_passthrough(port_name, instance) else _instance_wire(instance_name, port_name)
        connections.append(f"    .{port_name}({signal})")
    lines.append(",\n".join(connections))
    lines.append("  );")
    return lines


def _testbench(system_his: dict[str, Any], top_module: str) -> str:
    ports = _list(_mapping(system_his.get("top")).get("ports"))
    declarations = []
    connections = []
    for port in ports:
        port_map = _mapping(port)
        name = str(port_map.get("name", "")).strip()
        if not name:
            continue
        kind = "reg" if str(port_map.get("dir", port_map.get("direction"))) == "input" else "wire"
        declarations.append(f"  {kind}{_range(port_map.get('width'))} {name};")
        connections.append(f"    .{name}({name})")
    return (
        "module tb_top;\n"
        + "\n".join(declarations)
        + f"\n  {top_module} dut (\n"
        + ",\n".join(connections)
        + "\n  );\n"
        + "  initial begin\n"
        + "    $display(\"TEST_PASS\");\n"
        + "  end\n"
        + "endmodule\n"
    )


def _timing_sdc(system_his: dict[str, Any]) -> str:
    timing = _mapping(system_his.get("timing"))
    clock = str(timing.get("primary_clock") or "clk")
    fmax = timing.get("target_fmax_mhz") or 100
    try:
        period = 1000 / float(fmax)
    except (TypeError, ValueError, ZeroDivisionError):
        period = 10.0
    return f"create_clock -name {clock} -period {period:g} [get_ports {clock}]\n"


def _predicted_qor(system_his: dict[str, Any]) -> dict[str, Any]:
    resources = _mapping(system_his.get("resources"))
    return {"resources": _mapping(resources.get("expected"))}


def _port_block(ports: list[Any]) -> str:
    declarations = []
    for port in ports:
        port_map = _mapping(port)
        name = str(port_map.get("name", "")).strip()
        direction = str(port_map.get("dir", port_map.get("direction", ""))).strip()
        if name and direction:
            declarations.append(f"    {direction} wire{_range(port_map.get('width'))} {name}")
    return ",\n".join(declarations)


def _parameter_block(parameters: list[Any]) -> str:
    declarations = []
    for parameter in parameters:
        parameter_map = _mapping(parameter)
        name = str(parameter_map.get("name", "")).strip()
        value = parameter_map.get("value", parameter_map.get("default", 0))
        if name:
            declarations.append(f"parameter {name} = {value}")
    return "" if not declarations else " #(" + ", ".join(declarations) + ")"


def _parameter_override_block(values: dict[str, Any]) -> str:
    overrides = [f".{name}({value})" for name, value in values.items()]
    return "" if not overrides else " #(" + ", ".join(overrides) + ")"


def _range(width: Any) -> str:
    if isinstance(width, dict):
        if width.get("expr"):
            return f" [{width['expr']}-1:0]"
        width = width.get("resolved", 1)
    if isinstance(width, int):
        return "" if width <= 1 else f" [{width - 1}:0]"
    text = str(width).strip()
    if not text or text == "1":
        return ""
    if text.startswith("["):
        return f" {text}"
    return f" [{text}-1:0]"


def _fsm_states_for_component(component_name: str, system_his: dict[str, Any]) -> list[str]:
    instances_by_name = {
        str(_mapping(instance).get("name")): str(_mapping(instance).get("component"))
        for instance in _list(system_his.get("instances"))
    }
    states: list[str] = []
    for fsm in _list(_mapping(system_his.get("state")).get("fsms")):
        fsm_map = _mapping(fsm)
        owner = str(fsm_map.get("owner", "")).strip()
        if instances_by_name.get(owner, owner) != component_name:
            continue
        for state in _list(fsm_map.get("states")):
            state_name = str(state).strip()
            if state_name:
                states.append(state_name)
    return states


def _is_top_passthrough(port_name: str, instance: dict[str, Any]) -> bool:
    return port_name in {str(instance.get("clock", "")), str(instance.get("reset", ""))}


def _instance_wire(instance_name: str, port_name: str) -> str:
    return f"{instance_name}__{port_name}"


def _top_source(sources: list[str]) -> str:
    return "rtl/top.v" if "rtl/top.v" in sources else sources[0]


def _json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [item for item in _list(value) if isinstance(item, str) and item.strip()]


def _first_string(value: Any, default: str) -> str:
    strings = _string_list(value)
    return strings[0] if strings else default
