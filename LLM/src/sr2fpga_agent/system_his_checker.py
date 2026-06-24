"""System-HIS contract checks for project-level L0 validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from LLM.src.sr2fpga_agent.models import GeneratedProject
from LLM.src.sr2fpga_agent.system_his_v12_checker import SCHEMA_VERSION as SYSTEM_HIS_V12_SCHEMA
from LLM.src.sr2fpga_agent.system_his_v12_checker import check_system_his_v12


@dataclass(frozen=True)
class L0CheckResult:
    """Result of validating generated project structure against System-HIS."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def check_project_l0(project: GeneratedProject) -> L0CheckResult:
    """Validate the file/package contract before running HDL tools."""

    errors: list[str] = []
    warnings: list[str] = []
    system_his = _read_json_file(project, "system_his.json", errors)
    manifest = _read_json_file(project, "manifest.json", errors)
    if system_his is None or manifest is None:
        return L0CheckResult(passed=False, errors=errors, warnings=warnings)

    _require_mapping(system_his, "system_his", errors)
    _require_mapping(manifest, "manifest", errors)
    if errors:
        return L0CheckResult(passed=False, errors=errors, warnings=warnings)

    schema_version = system_his.get("schema_version")
    if schema_version == SYSTEM_HIS_V12_SCHEMA:
        return _check_project_l0_v12(system_his, manifest, project)
    if schema_version != "system-his-v1.1":
        warnings.append("system_his.schema_version is not system-his-v1.1")

    for key in (
        "project",
        "clocks",
        "resets",
        "project_name",
        "system",
        "interface",
        "architecture",
        "modules",
        "connections",
        "top_ports",
        "platform",
        "verification",
        "qor_intent",
    ):
        if key not in system_his:
            errors.append(f"system_his.{key} is required")

    project_record = system_his.get("project", {})
    if not isinstance(project_record, dict):
        errors.append("system_his.project must be an object")
        project_record = {}
    architecture = system_his.get("architecture", {})
    if not isinstance(architecture, dict):
        errors.append("system_his.architecture must be an object")
        architecture = {}
    his_top = str(architecture.get("top_module", "")).strip()
    project_top = str(project_record.get("top", "")).strip()
    manifest_top = str(manifest.get("top_module", "")).strip()
    if not his_top:
        errors.append("system_his.architecture.top_module is required")
    if not project_top:
        errors.append("system_his.project.top is required")
    if his_top and project_top and his_top != project_top:
        errors.append(f"system_his.project.top '{project_top}' does not match architecture.top_module '{his_top}'")
    if not manifest_top:
        errors.append("manifest.top_module is required")
    if his_top and manifest_top and his_top != manifest_top:
        errors.append(
            f"manifest.top_module '{manifest_top}' does not match System-HIS top_module '{his_top}'"
        )

    sources = _string_list(manifest.get("sources"), "manifest.sources", errors)
    for source in sources:
        if source not in project.files:
            errors.append(f"manifest source '{source}' is missing from project files")

    testbench = _manifest_testbench(manifest)
    if not testbench:
        errors.append("manifest.simulation.testbench is required")
    elif testbench not in project.files:
        errors.append(f"manifest testbench '{testbench}' is missing from project files")

    timing_constraint = _manifest_timing_constraint(manifest)
    if not timing_constraint:
        errors.append("manifest.constraints.timing is required")
    elif timing_constraint not in project.files:
        errors.append(f"manifest timing constraint '{timing_constraint}' is missing from project files")

    _validate_clocks(system_his.get("clocks"), errors)
    _validate_resets(system_his.get("resets"), errors)
    _validate_qor_intent(system_his.get("qor_intent"), errors)
    _validate_verification(system_his.get("verification"), errors)

    declared_modules = _declared_modules(project, sources)
    if manifest_top and manifest_top not in declared_modules:
        errors.append(f"top module '{manifest_top}' is not declared in manifest sources")
    for submodule in _string_list(architecture.get("submodules", []), "system_his.architecture.submodules", errors):
        if submodule not in declared_modules:
            errors.append(f"System-HIS submodule '{submodule}' is not declared in manifest sources")

    declared_parameters = _declared_module_parameters(project, sources)
    declared_ports = _declared_module_ports(project, sources)
    his_modules, ports_by_module = _validate_his_modules(
        system_his.get("modules"),
        set(sources),
        declared_modules,
        declared_parameters,
        declared_ports,
        errors,
    )
    _validate_his_connections(system_his.get("connections"), his_modules, ports_by_module, errors)
    if manifest_top:
        _validate_top_ports(system_his.get("top_ports"), manifest_top, declared_ports, errors)
        _validate_testbench_instantiates_top(project, testbench, manifest_top, errors)
        _validate_timing_constraint_ports(project, timing_constraint, manifest_top, declared_ports, errors)

    return L0CheckResult(passed=not errors, errors=errors, warnings=warnings)


def _check_project_l0_v12(
    system_his: dict[str, Any],
    manifest: dict[str, Any],
    project: GeneratedProject,
) -> L0CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    result = check_system_his_v12(system_his)
    errors.extend(result.errors)
    warnings.extend(result.warnings)

    artifacts = system_his.get("artifacts", {})
    if not isinstance(artifacts, dict):
        errors.append("system_his.artifacts must be an object")
        artifacts = {}
    artifact_top = str(artifacts.get("top_module", "")).strip()
    manifest_top = str(manifest.get("top_module", "")).strip()
    if artifact_top and manifest_top and artifact_top != manifest_top:
        errors.append(f"manifest.top_module '{manifest_top}' does not match System-HIS v1.2 artifacts.top_module '{artifact_top}'")

    manifest_sources = _string_list(manifest.get("sources"), "manifest.sources", errors)
    artifact_sources = artifacts.get("rtl_sources")
    if isinstance(artifact_sources, list) and all(isinstance(source, str) for source in artifact_sources):
        if manifest_sources and manifest_sources != artifact_sources:
            errors.append("manifest.sources does not match System-HIS v1.2 artifacts.rtl_sources")
    for source in manifest_sources:
        if source not in project.files:
            errors.append(f"manifest source '{source}' is missing from project files")

    testbench = _manifest_testbench(manifest)
    if not testbench:
        errors.append("manifest.simulation.testbench is required")
    elif testbench not in project.files:
        errors.append(f"manifest testbench '{testbench}' is missing from project files")

    timing_constraint = _manifest_timing_constraint(manifest)
    if not timing_constraint:
        errors.append("manifest.constraints.timing is required")
    elif timing_constraint not in project.files:
        errors.append(f"manifest timing constraint '{timing_constraint}' is missing from project files")

    return L0CheckResult(passed=not errors, errors=errors, warnings=warnings)


def _read_json_file(project: GeneratedProject, path: str, errors: list[str]) -> dict[str, Any] | None:
    content = project.files.get(path)
    if content is None:
        errors.append(f"{path} is required")
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        errors.append(f"{path} is not valid JSON: {exc.msg}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path} must contain a JSON object")
        return None
    return payload


def _require_mapping(value: Any, name: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")


def _string_list(value: Any, name: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    strings: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{name} entries must be non-empty strings")
        else:
            strings.append(item)
    return strings


def _manifest_testbench(manifest: dict[str, Any]) -> str:
    simulation = manifest.get("simulation")
    if isinstance(simulation, dict):
        return str(simulation.get("testbench", "")).strip()
    return ""


def _manifest_timing_constraint(manifest: dict[str, Any]) -> str:
    constraints = manifest.get("constraints")
    if isinstance(constraints, dict):
        return str(constraints.get("timing", "")).strip()
    return ""


def _declared_modules(project: GeneratedProject, sources: list[str]) -> set[str]:
    modules: set[str] = set()
    pattern = re.compile(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", re.MULTILINE)
    for source in sources:
        modules.update(pattern.findall(project.files.get(source, "")))
    return modules


def _declared_module_parameters(project: GeneratedProject, sources: list[str]) -> dict[str, set[str]]:
    parameters: dict[str, set[str]] = {}
    for source in sources:
        content = project.files.get(source, "")
        for module_name in re.findall(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", content, re.MULTILINE):
            parameters[module_name] = _module_parameter_names(content, module_name)
    return parameters


def _declared_module_ports(project: GeneratedProject, sources: list[str]) -> dict[str, dict[str, dict[str, Any]]]:
    ports: dict[str, dict[str, dict[str, Any]]] = {}
    for source in sources:
        content = project.files.get(source, "")
        for module_name in re.findall(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)\b", content, re.MULTILINE):
            ports[module_name] = _parse_module_ports(content, module_name)
    return ports


def _parse_module_ports(content: str, module_name: str) -> dict[str, dict[str, Any]]:
    body = _module_port_body(content, module_name)
    if body is None:
        return {}
    ports: dict[str, dict[str, Any]] = {}
    for declaration in _split_port_declarations(body):
        match = re.search(
            r"\b(input|output|inout)\b\s+(?:(?:wire|reg|logic)\s+)?(\[[^\]]+\])?\s*"
            r"([A-Za-z_][A-Za-z0-9_$]*)",
            declaration,
        )
        if match is None:
            continue
        ports[match.group(3)] = {
            "direction": match.group(1),
            "width": _port_width(match.group(2)),
        }
    return ports


def _module_port_body(content: str, module_name: str) -> str | None:
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
            index = _matching_paren(content, index) + 1
    while index < len(content) and content[index].isspace():
        index += 1
    if index >= len(content) or content[index] != "(":
        return None
    end = _matching_paren(content, index)
    return content[index + 1 : end]


def _split_port_declarations(body: str) -> list[str]:
    declarations: list[str] = []
    for part in body.split(","):
        stripped = " ".join(part.strip().split())
        if stripped:
            declarations.append(stripped)
    return declarations


def _port_width(range_text: str | None) -> int | str:
    if range_text is None:
        return 1
    normalized = range_text.strip()
    numeric = re.fullmatch(r"\[(\d+):0\]", normalized)
    if numeric is not None:
        return int(numeric.group(1)) + 1
    return normalized


def _module_parameter_names(content: str, module_name: str) -> set[str]:
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
    end = _matching_paren(content, index)
    parameter_body = content[index + 1 : end]
    return set(re.findall(r"\bparameter\s+([A-Za-z_][A-Za-z0-9_$]*)\b", parameter_body))


def _matching_paren(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return len(text)


def _validate_his_modules(
    value: Any,
    manifest_sources: set[str],
    declared_modules: set[str],
    declared_parameters: dict[str, set[str]],
    declared_ports: dict[str, dict[str, dict[str, Any]]],
    errors: list[str],
) -> tuple[set[str], dict[str, set[str]]]:
    if not isinstance(value, list):
        errors.append("system_his.modules must be a list")
        return set(), {}
    his_modules: set[str] = set()
    ports_by_module: dict[str, set[str]] = {}
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"system_his.modules[{index}] must be an object")
            continue
        name = str(item.get("name", "")).strip()
        source = str(item.get("source", "")).strip()
        role = str(item.get("role", "")).strip()
        if not name:
            errors.append(f"system_his.modules[{index}].name is required")
            continue
        if not source:
            errors.append(f"System-HIS module '{name}' source is required")
        elif source not in manifest_sources:
            errors.append(f"System-HIS module '{name}' source '{source}' is not in manifest.sources")
        if name not in declared_modules:
            errors.append(f"System-HIS module '{name}' is not declared in manifest sources")
        if role not in {"top", "submodule"}:
            errors.append(f"System-HIS module '{name}' role must be top or submodule")
        if not str(item.get("clock", "")).strip():
            errors.append(f"System-HIS module '{name}' clock is required")
        if not str(item.get("reset", "")).strip():
            errors.append(f"System-HIS module '{name}' reset is required")
        if not str(item.get("intent", "")).strip():
            errors.append(f"System-HIS module '{name}' intent is required")
        if not isinstance(item.get("parameters"), dict):
            errors.append(f"System-HIS module '{name}' parameters must be an object")
        else:
            for parameter_name in item["parameters"]:
                if parameter_name not in declared_parameters.get(name, set()):
                    errors.append(
                        f"System-HIS module '{name}' parameter '{parameter_name}' is not declared in RTL"
                    )
        if not isinstance(item.get("params"), list):
            errors.append(f"System-HIS module '{name}' params must be a list")
        elif isinstance(item.get("parameters"), dict):
            if _params_to_parameters(item["params"]) != item["parameters"]:
                errors.append(f"System-HIS module '{name}' params do not match parameters")
        if not isinstance(item.get("ports"), list):
            errors.append(f"System-HIS module '{name}' ports must be a list")
        else:
            ports_by_module[name] = _port_names(item["ports"], name, declared_ports.get(name, {}), errors)
        his_modules.add(name)
    missing = declared_modules - his_modules
    for name in sorted(missing):
        errors.append(f"RTL module '{name}' is missing from system_his.modules")
    return his_modules, ports_by_module


def _params_to_parameters(params: list[Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for item in params:
        if isinstance(item, dict) and "name" in item:
            mapped[str(item["name"])] = item.get("value")
    return mapped


def _port_names(
    value: list[Any],
    module_name: str,
    rtl_ports: dict[str, dict[str, Any]],
    errors: list[str],
) -> set[str]:
    names: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"System-HIS module '{module_name}' ports[{index}] must be an object")
            continue
        name = str(item.get("name", "")).strip()
        direction = str(item.get("direction", "")).strip()
        if not name:
            errors.append(f"System-HIS module '{module_name}' ports[{index}].name is required")
        else:
            names.add(name)
        if direction not in {"input", "output", "inout"}:
            errors.append(f"System-HIS module '{module_name}' port '{name}' direction is invalid")
        if "width" not in item:
            errors.append(f"System-HIS module '{module_name}' port '{name}' width is required")
        if name and name not in rtl_ports:
            errors.append(f"System-HIS module '{module_name}' port '{name}' is not declared in RTL")
            continue
        if name:
            rtl_port = rtl_ports[name]
            if direction in {"input", "output", "inout"} and direction != rtl_port["direction"]:
                errors.append(
                    f"System-HIS module '{module_name}' port '{name}' direction '{direction}' "
                    f"does not match RTL '{rtl_port['direction']}'"
                )
            if "width" in item and _normalize_width(item["width"]) != _normalize_width(rtl_port["width"]):
                errors.append(
                    f"System-HIS module '{module_name}' port '{name}' width {item['width']} "
                    f"does not match RTL {rtl_port['width']}"
                )
    return names


def _normalize_width(value: Any) -> str:
    text = str(value).strip()
    numeric_range = re.fullmatch(r"\[(\d+):0\]", text)
    if numeric_range is not None:
        return str(int(numeric_range.group(1)) + 1)
    return text


def _validate_his_connections(
    value: Any,
    his_modules: set[str],
    ports_by_module: dict[str, set[str]],
    errors: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append("system_his.connections must be a list")
        return
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"system_his.connections[{index}] must be an object")
            continue
        for endpoint_name in ("from", "to"):
            endpoint = item.get(endpoint_name)
            if not isinstance(endpoint, dict):
                errors.append(f"System-HIS connection[{index}].{endpoint_name} must be an object")
                continue
            module = str(endpoint.get("module", "")).strip()
            if not module:
                errors.append(f"System-HIS connection[{index}].{endpoint_name}.module is required")
            elif module not in his_modules:
                errors.append(f"System-HIS connection[{index}].{endpoint_name}.module '{module}' is not declared")
            port = str(endpoint.get("port", "")).strip()
            if not port:
                errors.append(f"System-HIS connection[{index}].{endpoint_name}.port is required")
            elif module in ports_by_module and port not in ports_by_module[module]:
                errors.append(
                    f"System-HIS connection[{index}].{endpoint_name}.port '{port}' is not declared on module"
                    f" '{module}'"
                )
        if not str(item.get("signal", "")).strip():
            errors.append(f"System-HIS connection[{index}].signal is required")
        if item.get("protocol") not in {"register", "valid_ready", "axi_lite", "axi_stream"}:
            errors.append(f"System-HIS connection[{index}].protocol is invalid")
        width = item.get("width")
        if not _is_valid_width_value(width):
            errors.append(f"System-HIS connection[{index}].width must be positive")
        if not isinstance(item.get("cdc"), bool):
            errors.append(f"System-HIS connection[{index}].cdc must be boolean")


def _is_valid_width_value(value: Any) -> bool:
    if isinstance(value, int):
        return value > 0
    if isinstance(value, str):
        return bool(value.strip())
    return False


def _validate_clocks(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("system_his.clocks must be a non-empty list")
        return
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"system_his.clocks[{index}] must be an object")
            continue
        if not str(item.get("name", "")).strip():
            errors.append(f"system_his.clocks[{index}].name is required")
        target_fmax = item.get("target_fmax_mhz")
        if not isinstance(target_fmax, (int, float)) or target_fmax <= 0:
            errors.append(f"system_his.clocks[{index}].target_fmax_mhz must be positive")


def _validate_resets(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("system_his.resets must be a non-empty list")
        return
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"system_his.resets[{index}] must be an object")
            continue
        if not str(item.get("name", "")).strip():
            errors.append(f"system_his.resets[{index}].name is required")
        if item.get("polarity") not in {"active_low", "active_high"}:
            errors.append(f"system_his.resets[{index}].polarity is invalid")
        if item.get("kind") not in {"sync", "async"}:
            errors.append(f"system_his.resets[{index}].kind is invalid")


def _validate_qor_intent(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("system_his.qor_intent must be an object")
        return
    resources = value.get("resources")
    if not isinstance(resources, dict):
        errors.append("system_his.qor_intent.resources must be an object")
        return
    for key in ("lut", "ff", "bram", "dsp"):
        if key not in resources:
            errors.append(f"system_his.qor_intent.resources.{key} is required")
        elif not isinstance(resources[key], int) or resources[key] < 0:
            errors.append(f"system_his.qor_intent.resources.{key} must be a non-negative integer")


def _validate_verification(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("system_his.verification must be an object")
        return
    if not str(value.get("testbench", "")).strip():
        errors.append("system_his.verification.testbench is required")
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("system_his.verification.checks must be a non-empty list")
    elif not all(isinstance(item, str) and item.strip() for item in checks):
        errors.append("system_his.verification.checks entries must be non-empty strings")
    if not str(value.get("test_pass_means", "")).strip():
        errors.append("system_his.verification.test_pass_means is required")


def _validate_top_ports(
    value: Any,
    top_module: str,
    declared_ports: dict[str, dict[str, dict[str, Any]]],
    errors: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append("system_his.top_ports must be a list")
        return
    expected = _normalized_port_list(declared_ports.get(top_module, {}))
    actual_ports: dict[str, dict[str, Any]] = {}
    for item in value:
        if isinstance(item, dict) and "name" in item:
            actual_ports[str(item["name"])] = item
    actual = _normalized_port_list(actual_ports)
    if actual != expected:
        errors.append("system_his.top_ports does not match top module RTL ports")


def _normalized_port_list(ports: dict[str, dict[str, Any]]) -> list[tuple[str, str, str]]:
    normalized = []
    for name, port in ports.items():
        direction = str(port.get("direction", "")).strip()
        if direction == "in":
            direction = "input"
        elif direction == "out":
            direction = "output"
        normalized.append((str(name), direction, _normalize_width(port.get("width", ""))))
    return sorted(normalized)


def _validate_testbench_instantiates_top(
    project: GeneratedProject,
    testbench: str,
    top_module: str,
    errors: list[str],
) -> None:
    if not testbench or testbench not in project.files:
        return
    content = project.files[testbench]
    pattern = re.compile(
        rf"\b{re.escape(top_module)}\b\s*(?:#\s*\(.*?\)\s*)?[A-Za-z_][A-Za-z0-9_$]*\s*\(",
        re.DOTALL,
    )
    if pattern.search(content) is None:
        errors.append(f"manifest testbench '{testbench}' does not instantiate top module '{top_module}'")


def _validate_timing_constraint_ports(
    project: GeneratedProject,
    timing_constraint: str,
    top_module: str,
    declared_ports: dict[str, dict[str, dict[str, Any]]],
    errors: list[str],
) -> None:
    if not timing_constraint or timing_constraint not in project.files:
        return
    top_ports = set(declared_ports.get(top_module, {}))
    content = project.files[timing_constraint]
    for port in re.findall(r"\[get_ports\s+\{?([A-Za-z_][A-Za-z0-9_$]*)\}?\]", content):
        if port not in top_ports:
            errors.append(
                f"manifest timing constraint '{timing_constraint}' references unknown top port '{port}'"
            )
