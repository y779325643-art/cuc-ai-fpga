"""System-HIS contract checks for project-level L0 validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.rtl_introspect import (
    declared_module_parameters,
    declared_module_ports,
    declared_modules,
    normalize_width,
)
from sr2fpga_agent.system_his_v12_checker import SCHEMA_VERSION as SYSTEM_HIS_V12_SCHEMA
from sr2fpga_agent.system_his_v12_checker import check_system_his_v12_against_rtl

if TYPE_CHECKING:
    from sr2fpga_agent.parsers import ResolvedProjectManifest


@dataclass(frozen=True)
class L0CheckResult:
    """Result of one project-level L0 check."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def check_common_project_l0(project: GeneratedProject) -> L0CheckResult:
    """Validate the method-neutral package through the canonical resolver."""

    # Local import breaks the legacy parser/checker import cycle while keeping
    # one canonical+legacy manifest resolver as the source of common L0 rules.
    from sr2fpga_agent.parsers import check_project_package_l0

    return check_project_package_l0(project)


def check_project_l0(project: GeneratedProject) -> L0CheckResult:
    """Compatibility entry point for common plus System-HIS consistency checks."""

    common = check_common_project_l0(project)
    consistency = check_his_project_consistency(project)
    return L0CheckResult(
        passed=common.passed and consistency.passed,
        errors=[*common.errors, *consistency.errors],
        warnings=[*common.warnings, *consistency.warnings],
    )


def check_his_project_consistency(project: GeneratedProject) -> L0CheckResult:
    """Validate System-HIS-to-project consistency for methods that emit it."""

    errors: list[str] = []
    warnings: list[str] = []
    system_his = _read_json_file(project, "system_his.json", errors)
    if system_his is None:
        return L0CheckResult(passed=False, errors=errors, warnings=warnings)

    # Local import avoids the historical parser/checker import cycle. Both
    # canonical and legacy manifests are projected through one validated view.
    from sr2fpga_agent.parsers import resolve_project_manifest

    try:
        manifest = resolve_project_manifest(project.files)
    except ValueError as exc:
        errors.append(str(exc))
        return L0CheckResult(passed=False, errors=errors, warnings=warnings)

    if not manifest.is_legacy:
        _require_manifest_artifact_role(
            manifest,
            role="system_his",
            expected_path="system_his.json",
            context="System-HIS project",
            errors=errors,
        )
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
    manifest_top = manifest.top_module
    if not his_top:
        errors.append("system_his.architecture.top_module is required")
    if not project_top:
        errors.append("system_his.project.top is required")
    if his_top and project_top and his_top != project_top:
        errors.append(f"system_his.project.top '{project_top}' does not match architecture.top_module '{his_top}'")
    if his_top and manifest_top and his_top != manifest_top:
        errors.append(
            f"manifest top module '{manifest_top}' does not match System-HIS top_module '{his_top}'"
        )

    sources = list(manifest.sources)
    testbenches = _manifest_artifact_paths(manifest, "candidate_testbench")
    timing_constraints = _manifest_artifact_paths(manifest, "constraint")

    _validate_clocks(system_his.get("clocks"), errors)
    _validate_resets(system_his.get("resets"), errors)
    _validate_qor_intent(system_his.get("qor_intent"), errors)
    verification = system_his.get("verification")
    _validate_verification(verification, errors)
    if isinstance(verification, dict):
        testbench = str(verification.get("testbench", "")).strip()
        if testbench:
            _require_manifest_artifact_role(
                manifest,
                role="candidate_testbench",
                expected_path=testbench,
                context="system_his.verification.testbench",
                errors=errors,
            )

    rtl_modules = declared_modules(project.files, sources)
    if manifest_top and manifest_top not in rtl_modules:
        errors.append(f"top module '{manifest_top}' is not declared in manifest sources")
    for submodule in _string_list(architecture.get("submodules", []), "system_his.architecture.submodules", errors):
        if submodule not in rtl_modules:
            errors.append(f"System-HIS submodule '{submodule}' is not declared in manifest sources")

    declared_parameters = declared_module_parameters(project.files, sources)
    declared_ports = declared_module_ports(project.files, sources)
    his_modules, ports_by_module = _validate_his_modules(
        system_his.get("modules"),
        set(sources),
        rtl_modules,
        declared_parameters,
        declared_ports,
        errors,
    )
    _validate_his_connections(system_his.get("connections"), his_modules, ports_by_module, errors)
    if manifest_top:
        _validate_top_ports(system_his.get("top_ports"), manifest_top, declared_ports, errors)
        for testbench in testbenches:
            _validate_testbench_instantiates_top(project, testbench, manifest_top, errors)
        for timing_constraint in timing_constraints:
            _validate_timing_constraint_ports(
                project,
                timing_constraint,
                manifest_top,
                declared_ports,
                errors,
            )

    return L0CheckResult(passed=not errors, errors=errors, warnings=warnings)


def _check_project_l0_v12(
    system_his: dict[str, Any],
    manifest: ResolvedProjectManifest,
    project: GeneratedProject,
) -> L0CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    rtl_check_project = _v12_rtl_check_project(project, manifest)
    result = check_system_his_v12_against_rtl(system_his, rtl_check_project)
    ignored_legacy_projection_errors = (
        {
            "manifest.simulation.testbench is required",
            "manifest.constraints.timing is required",
        }
        if not manifest.is_legacy
        else set()
    )
    errors.extend(
        error for error in result.errors if error not in ignored_legacy_projection_errors
    )
    warnings.extend(result.warnings)

    artifacts = system_his.get("artifacts", {})
    if not isinstance(artifacts, dict):
        errors.append("system_his.artifacts must be an object")
        artifacts = {}
    artifact_top = str(artifacts.get("top_module", "")).strip()
    manifest_top = manifest.top_module
    if artifact_top and manifest_top and artifact_top != manifest_top:
        errors.append(
            f"manifest top module '{manifest_top}' does not match System-HIS v1.2 "
            f"artifacts.top_module '{artifact_top}'"
        )

    manifest_sources = list(manifest.sources)
    artifact_sources = artifacts.get("rtl_sources")
    if isinstance(artifact_sources, list) and all(isinstance(source, str) for source in artifact_sources):
        if manifest_sources and manifest_sources != artifact_sources:
            errors.append("manifest.sources does not match System-HIS v1.2 artifacts.rtl_sources")

    artifact_manifest = str(artifacts.get("manifest", "")).strip()
    if artifact_manifest and artifact_manifest != "manifest.json":
        errors.append(
            f"system_his.artifacts.manifest '{artifact_manifest}' does not reference manifest.json"
        )
    testbench = str(artifacts.get("testbench", "")).strip()
    if testbench:
        _require_manifest_artifact_role(
            manifest,
            role="candidate_testbench",
            expected_path=testbench,
            context="system_his.artifacts.testbench",
            errors=errors,
        )
    artifact_constraints = artifacts.get("constraints")
    if isinstance(artifact_constraints, list):
        for constraint in artifact_constraints:
            if isinstance(constraint, str) and constraint.strip():
                _require_manifest_artifact_role(
                    manifest,
                    role="constraint",
                    expected_path=constraint,
                    context="system_his.artifacts.constraints",
                    errors=errors,
                )
    predicted_qor = str(artifacts.get("predicted_qor", "")).strip()
    if predicted_qor:
        _require_manifest_artifact_role(
            manifest,
            role="predicted_qor",
            expected_path=predicted_qor,
            context="system_his.artifacts.predicted_qor",
            errors=errors,
        )

    declared_ports = declared_module_ports(project.files, manifest_sources)
    # A candidate testbench is an advisory public-smoke artifact. Its ability
    # to instantiate the top module is not part of formal HIS/project
    # consistency and cannot confer semantic pass credit.
    for constraint_path in _manifest_artifact_paths(manifest, "constraint"):
        _validate_timing_constraint_ports(
            project,
            constraint_path,
            manifest_top,
            declared_ports,
            errors,
        )

    _validate_v12_transitional_fields(system_his, manifest_sources, project, manifest_top, errors)

    return L0CheckResult(passed=not errors, errors=errors, warnings=warnings)


def _manifest_artifact_paths(
    manifest: ResolvedProjectManifest,
    role: str,
) -> tuple[str, ...]:
    return manifest.artifact_paths_by_role.get(role, ())


def _require_manifest_artifact_role(
    manifest: ResolvedProjectManifest,
    *,
    role: str,
    expected_path: str,
    context: str,
    errors: list[str],
) -> None:
    if expected_path not in _manifest_artifact_paths(manifest, role):
        errors.append(
            f"{context} '{expected_path}' is not declared with manifest artifact role '{role}'"
        )


def _v12_rtl_check_project(
    project: GeneratedProject,
    manifest: ResolvedProjectManifest,
) -> GeneratedProject:
    """Give the legacy v1.2 RTL checker a resolver-backed compatibility view."""

    if manifest.is_legacy:
        return project
    compatibility_manifest: dict[str, Any] = {
        "top_module": manifest.top_module,
        "sources": list(manifest.sources),
    }
    constraints = _manifest_artifact_paths(manifest, "constraint")
    if constraints:
        compatibility_manifest["constraints"] = {"timing": constraints[0]}
    files = dict(project.files)
    files["manifest.json"] = json.dumps(compatibility_manifest) + "\n"
    return GeneratedProject(project_name=project.project_name, files=files)


def _validate_v12_transitional_fields(
    system_his: dict[str, Any],
    manifest_sources: list[str],
    project: GeneratedProject,
    manifest_top: str,
    errors: list[str],
) -> None:
    """Validate deterministic v1.1-compat fields when a v1.2 payload still carries them."""

    sources = set(manifest_sources)
    declared = declared_modules(project.files, manifest_sources)
    declared_parameters = declared_module_parameters(project.files, manifest_sources)
    declared_ports = declared_module_ports(project.files, manifest_sources)
    his_modules: set[str] = set()
    ports_by_module: dict[str, set[str]] = {}
    if "modules" in system_his:
        his_modules, ports_by_module = _validate_his_modules(
            system_his.get("modules"),
            sources,
            declared,
            declared_parameters,
            declared_ports,
            errors,
        )
    if "connections" in system_his:
        _validate_his_connections(system_his.get("connections"), his_modules, ports_by_module, errors)
    if "top_ports" in system_his and manifest_top:
        _validate_top_ports(system_his.get("top_ports"), manifest_top, declared_ports, errors)
    if "clocks" in system_his:
        _validate_clocks(system_his.get("clocks"), errors)
    if "resets" in system_his:
        _validate_resets(system_his.get("resets"), errors)
    if "qor_intent" in system_his:
        _validate_qor_intent(system_his.get("qor_intent"), errors)
    verification = system_his.get("verification")
    if isinstance(verification, dict) and any(key in verification for key in ("checks", "test_pass_means", "expected_behavior")):
        _validate_verification(verification, errors)


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
            if "width" in item and normalize_width(item["width"]) != normalize_width(rtl_port["width"]):
                errors.append(
                    f"System-HIS module '{module_name}' port '{name}' width {item['width']} "
                    f"does not match RTL {rtl_port['width']}"
                )
    return names


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
        normalized.append((str(name), direction, normalize_width(port.get("width", ""))))
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
