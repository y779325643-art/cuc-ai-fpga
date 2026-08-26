"""Contract-preserving skeleton generation from System-HIS v1.2."""

from __future__ import annotations

import json
import re
from typing import Any

from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest


BEHAVIOR_REGION_BEGIN = "// SR2FPGA_BEHAVIOR_BEGIN"
BEHAVIOR_REGION_END = "// SR2FPGA_BEHAVIOR_END"


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
    components_by_source: dict[str, dict[str, Any]] = {}
    for component in components:
        source = str(component.get("source"))
        if source in components_by_source:
            raise ValueError(
                f"System-HIS has two components with the same source path '{source}': "
                f"'{components_by_source[source].get('name')}' and '{component.get('name')}'. "
                "Each source file must belong to exactly one component."
            )
        components_by_source[source] = component
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
    files["sim/tb_top.v"] = _testbench(request, platform, system_his, top_module)
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
        _validate_behavior_body(path, behavior)
        files[path] = _fill_behavior_hole(files[path], behavior)
    return GeneratedProject(project_name=skeleton.project_name, files=files)


def _validate_behavior_body(path: str, behavior: str) -> None:
    if re.search(r"(?m)^\s*module\b|\bendmodule\b", behavior):
        raise ValueError(f"behavior file '{path}' must contain behavior body only, not module declarations or endmodule")


def _fill_behavior_hole(content: str, behavior: str) -> str:
    behavior_lines = _drop_duplicate_unused_clock_reset_lines(content, behavior).strip("\n").splitlines() or ["// empty behavior body"]
    indented = "\n".join(f"  {line}" if line.strip() else "" for line in behavior_lines)
    editable_region = (
        f"  {BEHAVIOR_REGION_BEGIN}\n"
        f"{indented}\n"
        f"  {BEHAVIOR_REGION_END}"
    )
    merged = content.replace("  // BEHAVIOR_HOLE: model-generated RTL behavior goes here.", editable_region, 1)
    return _drop_duplicate_skeleton_localparams(merged, _declared_localparams(behavior))


def _declared_localparams(verilog: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(r"\blocalparam\b(?:\s+\[[^\]]+\])?\s+([A-Za-z_][A-Za-z0-9_$]*)\s*=", verilog)
    }


def _drop_duplicate_skeleton_localparams(content: str, declared: set[str]) -> str:
    if not declared:
        return content
    lines = []
    for line in content.splitlines():
        match = re.fullmatch(r"\s*localparam\s+([A-Za-z_][A-Za-z0-9_$]*)\s*=\s*0\s*;", line)
        if match and match.group(1) in declared:
            continue
        lines.append(line)
    return "\n".join(lines) + ("\n" if content.endswith("\n") else "")


def _drop_duplicate_unused_clock_reset_lines(content: str, behavior: str) -> str:
    if "_unused_clock_reset" not in content:
        return behavior
    lines = [
        line
        for line in behavior.splitlines()
        if not re.fullmatch(r"\s*wire\s+_unused_clock_reset\s*=\s*&\{[^}]+\}\s*;", line)
    ]
    return "\n".join(lines) + ("\n" if behavior.endswith("\n") else "")


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
    parameters = _merged_parameters(_list(top.get("parameters")), components_by_name.values())
    top_parameter_names = {str(parameter.get("name", "")).strip() for parameter in parameters}
    lines = [
        f"module {top_module}{_parameter_block(parameters)} (",
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
    data_flow_assignments = _data_flow_assignment_lines(system_his)
    if data_flow_assignments:
        lines.extend(data_flow_assignments)
        lines.append("")
    for instance in instances:
        instance_map = _mapping(instance)
        component = components_by_name.get(str(instance_map.get("component")), {})
        lines.extend(_instance_lines(instance_map, component, top_parameter_names))
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
    ]
    unused_clock_reset = _unused_clock_reset_line(_list(component.get("ports")))
    if unused_clock_reset:
        lines.append(unused_clock_reset)
    lines.append("  // BEHAVIOR_HOLE: model-generated RTL behavior goes here.")
    for state in states:
        lines.append(f"  localparam {state} = 0;")
    if states:
        state_terms = ", ".join(f"({state} == {state})" for state in states)
        lines.append(f"  wire _unused_fsm_states = &{{1'b0, {state_terms}}};")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


def _placeholder_module(source: str, component_names: set[str], system_his: dict[str, Any]) -> str:
    stem = source.rsplit("/", 1)[-1].removesuffix(".v")
    name = stem if stem not in component_names else f"{stem}_skeleton"
    return _component_module({"name": name, "ports": []}, system_his)


def _instance_lines(instance: dict[str, Any], component: dict[str, Any], top_parameter_names: set[str] | None = None) -> list[str]:
    component_name = str(instance.get("component", "")).strip()
    instance_name = str(instance.get("name", "")).strip()
    ports = _list(component.get("ports"))
    parameter_overrides = _parameter_override_block(_mapping(instance.get("parameter_values")), top_parameter_names or set())
    lines = [f"  {component_name}{parameter_overrides} {instance_name} ("]
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


def _data_flow_assignment_lines(system_his: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    assigned_sinks: dict[str, tuple[str, int]] = {}
    unused_signals: set[str] = set()
    ports_by_owner = _ports_by_endpoint_owner(system_his)
    for flow in _list(system_his.get("data_flow")):
        path = _list(_mapping(flow).get("path"))
        endpoints = [_parse_endpoint(endpoint) for endpoint in path]
        endpoints = [endpoint for endpoint in endpoints if endpoint]
        for source, sink in zip(endpoints, endpoints[1:]):
            source_owner, source_port = source
            sink_owner, sink_port = sink
            if source_owner == sink_owner:
                continue
            _append_assignment(
                lines,
                seen,
                assigned_sinks,
                _endpoint_signal(source_owner, source_port),
                _endpoint_signal(sink_owner, sink_port),
            )
            source_valid = _companion_signal(source_owner, source_port, "valid", ports_by_owner)
            sink_valid = _companion_signal(sink_owner, sink_port, "valid", ports_by_owner)
            if source_valid and sink_valid:
                _append_assignment(lines, seen, assigned_sinks, source_valid, sink_valid)
            elif sink_valid:
                _append_assignment(lines, seen, assigned_sinks, "1'b1", sink_valid)
            elif source_valid:
                unused_signals.add(source_valid)
            source_ready = _companion_signal(source_owner, source_port, "ready", ports_by_owner)
            sink_ready = _companion_signal(sink_owner, sink_port, "ready", ports_by_owner)
            if source_ready and sink_ready:
                _append_assignment(lines, seen, assigned_sinks, sink_ready, source_ready)
            elif source_ready:
                _append_assignment(lines, seen, assigned_sinks, "1'b1", source_ready)
            elif sink_ready:
                unused_signals.add(sink_ready)
    if unused_signals:
        lines.append(f"  wire _unused_data_flow_signals = &{{1'b0, {', '.join(sorted(unused_signals))}}};")
    return lines


def _append_assignment(
    lines: list[str],
    seen: set[tuple[str, str]],
    assigned_sinks: dict[str, tuple[str, int]],
    source: str,
    sink: str,
) -> None:
    if source == sink or (source, sink) in seen:
        return
    existing = assigned_sinks.get(sink)
    if existing:
        existing_source, line_index = existing
        if existing_source == "1'b1" and source != "1'b1":
            lines[line_index] = f"  assign {sink} = {source};"
            assigned_sinks[sink] = (source, line_index)
            seen.add((source, sink))
        return
    seen.add((source, sink))
    assigned_sinks[sink] = (source, len(lines))
    lines.append(f"  assign {sink} = {source};")


def _ports_by_endpoint_owner(system_his: dict[str, Any]) -> dict[str, set[str]]:
    ports_by_owner = {
        "top": {
            str(_mapping(port).get("name", "")).strip()
            for port in _list(_mapping(system_his.get("top")).get("ports"))
            if str(_mapping(port).get("name", "")).strip()
        }
    }
    components_by_name = {
        str(_mapping(component).get("name", "")).strip(): _mapping(component)
        for component in _list(system_his.get("components"))
    }
    for instance in _list(system_his.get("instances")):
        instance_map = _mapping(instance)
        owner = str(instance_map.get("name", "")).strip()
        component = components_by_name.get(str(instance_map.get("component", "")).strip(), {})
        if owner:
            ports_by_owner[owner] = {
                str(_mapping(port).get("name", "")).strip()
                for port in _list(component.get("ports"))
                if str(_mapping(port).get("name", "")).strip()
            }
    return ports_by_owner


def _parse_endpoint(endpoint: Any) -> tuple[str, str] | None:
    text = str(endpoint).strip() if isinstance(endpoint, str) else ""
    if "." not in text:
        return None
    owner, port = text.split(".", 1)
    if not owner or not port:
        return None
    return owner, port


def _endpoint_signal(owner: str, port: str) -> str:
    if owner == "top":
        return port
    return _instance_wire(owner, port)


def _companion_signal(owner: str, port: str, suffix: str, ports_by_owner: dict[str, set[str]]) -> str:
    port_names = ports_by_owner.get(owner, set())
    candidates = [f"{port.removesuffix('_data')}_{suffix}"]
    if suffix == "ready" and port.endswith("_valid"):
        candidates.append(f"{port.removesuffix('_valid')}_ready")
    if suffix == "ready" and port == "valid":
        candidates.append("ready")
    for companion in candidates:
        if companion in port_names:
            return _endpoint_signal(owner, companion)
    return ""


def _unused_clock_reset_line(ports: list[Any]) -> str:
    names = []
    for port in ports:
        port_map = _mapping(port)
        name = str(port_map.get("name", "")).strip()
        direction = str(port_map.get("dir", port_map.get("direction", ""))).strip()
        if direction == "input" and name in {"clk", "clock", "rst", "rst_n", "reset", "reset_n"}:
            names.append(name)
    if not names:
        return ""
    return f"  wire _unused_clock_reset = &{{1'b0, {', '.join(names)}}};"


def _testbench(
    request: ProjectRequest,
    platform: PlatformProfile,
    system_his: dict[str, Any],
    top_module: str,
) -> str:
    deterministic_testbench = _deterministic_functional_testbench(request, platform, top_module)
    if deterministic_testbench:
        return deterministic_testbench
    return _fail_safe_testbench(request.task_type)


def _deterministic_functional_testbench(
    request: ProjectRequest,
    platform: PlatformProfile,
    top_module: str,
) -> str:
    if top_module != "top":
        return ""
    try:
        from sr2fpga_agent.project_generator import ProjectGenerator

        return ProjectGenerator().generate(request, platform).files.get("sim/tb_top.v", "")
    except ValueError:
        return ""


def _fail_safe_testbench(task_type: str) -> str:
    safe_task_type = task_type.replace("\\", "\\\\").replace('"', '\\"')
    return (
        "// SR2FPGA_ORACLE_STATUS: needs_oracle\n"
        "module tb_top;\n"
        "  initial begin\n"
        f"    $display(\"TEST_FAIL missing independent functional oracle for {safe_task_type}\");\n"
        "    $finish;\n"
        "  end\n"
        "endmodule\n"
    )


def _merged_parameters(top_parameters: list[Any], components: Any) -> list[Any]:
    merged = [_mapping(parameter) for parameter in top_parameters]
    seen = {str(parameter.get("name", "")).strip() for parameter in merged}
    for component in components:
        for parameter in _list(_mapping(component).get("parameters")):
            parameter_map = _mapping(parameter)
            name = str(parameter_map.get("name", "")).strip()
            if name and name not in seen:
                merged.append(parameter_map)
                seen.add(name)
    return merged


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
        direction = str(port_map.get("dir", port_map.get("direction", "input"))).strip()
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


def _parameter_override_block(values: dict[str, Any], top_parameter_names: set[str] | None = None) -> str:
    exposed_parameters = top_parameter_names or set()
    overrides = [
        f".{name}({name if name in exposed_parameters else value})"
        for name, value in values.items()
    ]
    return "" if not overrides else " #(" + ", ".join(overrides) + ")"


def _range(width: Any) -> str:
    if width is None:
        return ""
    if isinstance(width, dict):
        if width.get("expr"):
            width = width["expr"]
        else:
            width = width.get("resolved", 1)
        if width is None:
            return ""
    if isinstance(width, int):
        return "" if width <= 1 else f" [{width - 1}:0]"
    text = str(width).strip()
    if not text or text == "1":
        return ""
    if text.startswith("["):
        return f" {text}"
    if ":" in text:
        return f" [{text}]"
    return f" [{text}-1:0]"


def _fsm_states_for_component(component_name: str, system_his: dict[str, Any]) -> list[str]:
    instances_by_name = {
        str(_mapping(instance).get("name")): str(_mapping(instance).get("component"))
        for instance in _list(system_his.get("instances"))
    }
    states: list[str] = []
    seen: set[str] = set()
    for fsm in _list(_mapping(system_his.get("state")).get("fsms")):
        fsm_map = _mapping(fsm)
        owner = _fsm_owner(fsm_map)
        if instances_by_name.get(owner, owner) != component_name:
            continue
        for state in _list(fsm_map.get("states")):
            state_name = str(state).strip()
            if state_name and state_name not in seen:
                seen.add(state_name)
                states.append(state_name)
    return states


def _fsm_owner(fsm: dict[str, Any]) -> str:
    owner = str(fsm.get("owner", "")).strip()
    if owner:
        return owner
    name = str(fsm.get("name", "")).strip()
    if "." in name:
        return name.split(".", 1)[0]
    return ""


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
