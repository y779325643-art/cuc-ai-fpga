"""Response parsers and project validation helpers."""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from sr2fpga_agent.models import GeneratedProject, compact_json_text as _canonical_json
from sr2fpga_agent.path_safety import validate_project_relative_path
from sr2fpga_agent.project_contract import validate_project_package_manifest
from sr2fpga_agent.rtl_introspect import (
    declared_module_ports,
    declared_modules,
    module_port_body,
    widths_equivalent,
)
from sr2fpga_agent.system_his_checker import L0CheckResult, check_project_l0
from sr2fpga_agent.system_his_v12_checker import check_system_his_v12

REQUIRED_PROJECT_FILES = {"manifest.json"}
PROJECT_PACKAGE_VERSION = "project-package-v1"
ManifestPolicy = Literal["compatible", "canonical", "legacy"]


@dataclass(frozen=True)
class ResolvedTopPort:
    """Canonical top-interface port used by common L0."""

    name: str
    direction: str
    width: int | str


@dataclass(frozen=True)
class ResolvedProjectManifest:
    """Method-neutral build intent resolved from canonical or legacy manifests."""

    contract_version: str
    project_name: str
    top_module: str
    top_source: str | None
    sources: tuple[str, ...]
    source_languages: dict[str, str]
    top_ports: tuple[ResolvedTopPort, ...] | None
    artifact_paths_by_role: dict[str, tuple[str, ...]]
    is_legacy: bool


def resolve_project_manifest(files: dict[str, str]) -> ResolvedProjectManifest:
    """Resolve and validate canonical project-package-v1 or a legacy manifest."""

    for path in files:
        validate_project_relative_path(path)
    try:
        manifest_content = files["manifest.json"]
    except KeyError as exc:
        raise ValueError("project is missing required files: manifest.json") from exc
    try:
        manifest = json.loads(manifest_content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest.json is not valid JSON: {exc.msg}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must contain a JSON object")

    contract_version = manifest.get("contract_version")
    if contract_version is None:
        return _resolve_legacy_manifest(manifest, files)
    if contract_version != PROJECT_PACKAGE_VERSION:
        raise ValueError(f"unsupported manifest.json contract_version: {contract_version}")
    return _resolve_project_package_v1(manifest, files)


def check_project_package_l0(project: GeneratedProject) -> L0CheckResult:
    """Validate the method-neutral project package without requiring System-HIS."""

    errors: list[str] = []
    missing = sorted(REQUIRED_PROJECT_FILES - set(project.files))
    if missing:
        errors.append(f"project is missing required files: {', '.join(missing)}")
    if "manifest.json" not in project.files:
        return L0CheckResult(passed=False, errors=errors)

    try:
        manifest = resolve_project_manifest(project.files)
    except ValueError as exc:
        errors.append(str(exc))
        return L0CheckResult(passed=False, errors=errors)

    sources = list(manifest.sources)
    top_language = (
        manifest.source_languages.get(manifest.top_source)
        if manifest.top_source is not None
        else None
    )
    if manifest.is_legacy or top_language in {"verilog", "systemverilog"}:
        if manifest.top_module not in declared_modules(project.files, sources):
            errors.append(f"top module '{manifest.top_module}' is not declared in manifest sources")
        if (
            manifest.top_source is not None
            and manifest.top_module not in declared_modules(project.files, [manifest.top_source])
        ):
            errors.append(
                f"top source '{manifest.top_source}' does not declare top module "
                f"'{manifest.top_module}'"
            )
    if not manifest.is_legacy:
        _validate_canonical_top_interface(project.files, manifest, errors)

    return L0CheckResult(passed=not errors, errors=errors)


MULTIMODULE_RTL_EXAMPLES = {
    "uart_tx": ["rtl/top.v", "rtl/baud_tick_gen.v", "rtl/uart_tx_core.v"],
    "spi_master": ["rtl/top.v", "rtl/clock_divider.v", "rtl/spi_master_core.v"],
    "pwm_controller": ["rtl/top.v", "rtl/pwm_timer.v", "rtl/pwm_channel.v"],
    "fir_filter": ["rtl/top.v", "rtl/mac_unit.v", "rtl/fir_filter_core.v"],
    "streaming_valid_ready": ["rtl/top.v", "rtl/skid_buffer.v", "rtl/stream_stage.v"],
    "matrix_vector_mac": [
        "rtl/top.v",
        "rtl/vector_rom.v",
        "rtl/mac_unit.v",
        "rtl/dot_product_engine.v",
    ],
    "alu_control_unit": [
        "rtl/top.v",
        "rtl/control_decode.v",
        "rtl/alu_core.v",
        "rtl/status_flags.v",
    ],
    "crc_stream_checker": [
        "rtl/top.v",
        "rtl/stream_frame_accumulator.v",
        "rtl/crc8_update.v",
        "rtl/crc_status.v",
    ],
    "composed_event_counter": ["rtl/top.v", "rtl/event_gate.v", "rtl/counter_core.v"],
    "composed_stream_accumulator": ["rtl/top.v", "rtl/skid_buffer.v", "rtl/accumulator_core.v"],
    "composed_stream_fork": [
        "rtl/top.v",
        "rtl/skid_buffer.v",
        "rtl/stream_fork.v",
        "rtl/stream_stage.v",
    ],
    "composed_dual_stream_join": [
        "rtl/top.v",
        "rtl/skid_buffer.v",
        "rtl/stream_join.v",
        "rtl/accumulator_core.v",
        "rtl/stream_stage.v",
    ],
    "composed_vector_mac_pipeline": [
        "rtl/top.v",
        "rtl/skid_buffer.v",
        "rtl/vector_mac_core.v",
        "rtl/stream_stage.v",
    ],
    "composed_td_update_core": [
        "rtl/top.v",
        "rtl/td_input_stage.v",
        "rtl/discount_core.v",
        "rtl/td_update_core.v",
        "rtl/stream_stage.v",
    ],
    "composed_policy_value_shell": [
        "rtl/top.v",
        "rtl/config_reg_bank.v",
        "rtl/observation_stage.v",
        "rtl/policy_score_core.v",
        "rtl/action_select_core.v",
        "rtl/stream_stage.v",
    ],
    "composed_replay_sample_shell": [
        "rtl/top.v",
        "rtl/host_sample_stage.v",
        "rtl/replay_store.v",
        "rtl/sample_pack_core.v",
        "rtl/sample_read_stage.v",
        "rtl/occupancy_counter.v",
    ],
    "composed_host_protocol_shell": [
        "rtl/top.v",
        "rtl/axi_lite_write_ctrl.v",
        "rtl/axi_lite_read_ctrl.v",
        "rtl/control_reg_bank.v",
        "rtl/sample_stream_adapter.v",
        "rtl/irq_status.v",
    ],
    "composed_rl_accelerator_shell": [
        "rtl/top.v",
        "rtl/host_config_bank.v",
        "rtl/sample_capture_stage.v",
        "rtl/policy_value_core.v",
        "rtl/td_update_core.v",
        "rtl/result_stream_stage.v",
    ],
    "composed_batch_rl_accelerator_shell": [
        "rtl/top.v",
        "rtl/batch_config_bank.v",
        "rtl/batch_sample_buffer.v",
        "rtl/dual_policy_value_core.v",
        "rtl/dual_td_update_core.v",
        "rtl/batch_result_stage.v",
    ],
    "composed_replay_arbiter_shell": [
        "rtl/top.v",
        "rtl/host_transition_packetizer.v",
        "rtl/replay_index_allocator.v",
        "rtl/replay_request_arbiter.v",
        "rtl/replay_memory_bank.v",
        "rtl/sample_packet_stage.v",
    ],
}


def parse_project_files(
    content: str,
    expected_task_type: str | None = None,
    *,
    manifest_policy: ManifestPolicy = "compatible",
) -> dict[str, str]:
    """Parse model JSON output into project files."""
    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model output is not valid JSON: {exc.msg}") from exc

    raw_files = payload.get("files")
    if isinstance(raw_files, dict):
        files = {str(path): str(file_content) for path, file_content in raw_files.items()}
    elif isinstance(raw_files, list):
        files = _files_from_list(raw_files)
    else:
        raise ValueError("Model output must contain files as an object or list")

    files = {
        validate_project_relative_path(path): _ensure_trailing_newline(content)
        for path, content in files.items()
    }
    missing = sorted(REQUIRED_PROJECT_FILES - set(files))
    if missing:
        raise ValueError(f"Model output is missing required files: {', '.join(missing)}")
    resolved_manifest = resolve_project_manifest(files)
    _enforce_manifest_policy(resolved_manifest, manifest_policy)
    _validate_expected_rtl_structure(files, expected_task_type)
    return files


def parse_behavior_files(content: str) -> dict[str, str]:
    """Parse HIS2PROJECT JSON output into behavior-only file bodies."""

    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"HIS2PROJECT behavior output is not valid JSON: {exc.msg}") from exc
    if "files" in payload:
        raise ValueError("HIS2PROJECT response must contain behavior_files, not files")
    raw_behavior = payload.get("behavior_files")
    if not isinstance(raw_behavior, dict):
        raise ValueError("HIS2PROJECT response must contain behavior_files as an object")
    return {str(path): str(body) for path, body in raw_behavior.items()}


def parse_system_his_payload(content: str) -> dict[str, Any]:
    """Parse model output as a System-HIS object without semantic validation."""

    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model System-HIS output is not valid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Model System-HIS output must be a JSON object")
    system_his = payload.get("system_his", payload)
    if not isinstance(system_his, dict):
        raise ValueError("Model System-HIS output field system_his must be an object")
    return system_his


def parse_system_his_v12(content: str) -> dict[str, Any]:
    """Parse and validate model output as System-HIS v1.2 JSON."""

    system_his = parse_system_his_payload(content)

    result = check_system_his_v12(system_his)
    if not result.passed:
        raise ValueError("Model System-HIS v1.2 failed validation: " + "; ".join(result.errors))
    return system_his


def _validate_system_his_contract_unchanged(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    frozen_keys = ("schema_version", "top", "state", "components", "instances", "data_flow", "control_flow", "artifacts")
    for key in frozen_keys:
        if _canonical_json(expected.get(key)) != _canonical_json(actual.get(key)):
            raise ValueError(f"HIS2PROJECT changed frozen System-HIS contract section '{key}'")


def diff_projects(old: GeneratedProject, new: GeneratedProject) -> str:
    """Return a unified diff between two generated project file maps."""
    chunks: list[str] = []
    for path in sorted(set(old.files) | set(new.files)):
        old_content = old.files.get(path, "")
        new_content = new.files.get(path, "")
        if old_content == new_content:
            continue
        chunks.extend(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
    return "".join(chunks)


def _minimize_repaired_project(
    original: GeneratedProject,
    repaired: GeneratedProject,
    diagnosis: dict[str, object],
) -> GeneratedProject:
    files = dict(repaired.files)
    if (
        original.files.get("manifest.json") != repaired.files.get("manifest.json")
        and _manifest_is_valid_for_project(original.files)
        and not _diagnosis_mentions_path(diagnosis, "manifest.json")
    ):
        files["manifest.json"] = original.files["manifest.json"]
    return GeneratedProject(project_name=repaired.project_name, files=files)


def _manifest_is_valid_for_project(files: dict[str, str]) -> bool:
    try:
        _validate_manifest(files)
    except ValueError:
        return False
    return True


def _validate_repair_preserves_l0_when_not_repairing_l0(
    repaired_project: GeneratedProject,
    diagnosis: dict[str, object],
) -> None:
    if str(diagnosis.get("stage", "")) == "l0_consistency":
        return
    l0_result = check_project_l0(repaired_project)
    if l0_result.passed:
        return
    raise ValueError("Project repair introduced L0 contract violations: " + "; ".join(l0_result.errors))


def _diagnosis_mentions_path(diagnosis: dict[str, object], path: str) -> bool:
    affected_files = diagnosis.get("affected_files")
    if isinstance(affected_files, list) and path in {str(item) for item in affected_files}:
        return True
    return path.lower() in json.dumps(diagnosis, ensure_ascii=False).lower()


def _ensure_trailing_newline(content: str) -> str:
    return content if content.endswith("\n") else content + "\n"


def _manifest_policy_for_project(files: dict[str, str]) -> ManifestPolicy:
    """Return the manifest generation a repair response must preserve."""

    try:
        manifest = json.loads(files.get("manifest.json", ""))
    except json.JSONDecodeError:
        return "compatible"
    if not isinstance(manifest, dict):
        return "compatible"
    return "canonical" if "contract_version" in manifest else "legacy"


def _enforce_manifest_policy(
    manifest: ResolvedProjectManifest,
    policy: ManifestPolicy,
) -> None:
    if policy not in {"compatible", "canonical", "legacy"}:
        raise ValueError(f"unsupported manifest policy: {policy}")
    if policy == "canonical" and manifest.is_legacy:
        raise ValueError(
            "Model output must use canonical project-package-v1 manifest.json"
        )
    if policy == "legacy" and not manifest.is_legacy:
        raise ValueError("Project repair must preserve the legacy manifest generation")


def _validate_canonical_top_interface(
    files: dict[str, str],
    manifest: ResolvedProjectManifest,
    errors: list[str],
) -> None:
    if manifest.top_source is None or manifest.top_ports is None:
        return
    language = manifest.source_languages.get(manifest.top_source)
    if language == "vhdl":
        # The package contract is valid; backend capability routing reports the
        # unsupported language before tools run rather than mislabeling L0.
        return
    if language not in {"verilog", "systemverilog"}:
        errors.append(
            f"top interface introspection does not support source language '{language}'"
        )
        return

    expected_names = [port.name for port in manifest.top_ports]
    duplicate_names = sorted(
        {name for name in expected_names if expected_names.count(name) > 1}
    )
    if duplicate_names:
        errors.append(
            "manifest.top.interface.ports contains duplicate names: "
            + ", ".join(duplicate_names)
        )
        return

    top_source_content = files.get(manifest.top_source, "")
    port_body = module_port_body(top_source_content, manifest.top_module)
    if port_body is not None:
        port_body_without_comments = re.sub(
            r"/\*.*?\*/|//[^\n]*",
            "",
            port_body,
            flags=re.DOTALL,
        ).strip()
        if port_body_without_comments and re.search(
            r"\b(?:input|output|inout)\b",
            port_body_without_comments,
        ) is None:
            errors.append(
                "top interface validation does not support non-ANSI port declarations"
            )
            return

    actual_ports = declared_module_ports(files, [manifest.top_source]).get(
        manifest.top_module,
        {},
    )
    expected_by_name = {port.name: port for port in manifest.top_ports}
    missing_in_manifest = sorted(set(actual_ports) - set(expected_by_name))
    missing_in_rtl = sorted(set(expected_by_name) - set(actual_ports))
    if missing_in_manifest:
        errors.append(
            "manifest.top.interface.ports omits RTL ports: "
            + ", ".join(missing_in_manifest)
        )
    if missing_in_rtl:
        errors.append(
            "manifest.top.interface.ports references missing RTL ports: "
            + ", ".join(missing_in_rtl)
        )
    for name in sorted(set(expected_by_name) & set(actual_ports)):
        expected = expected_by_name[name]
        actual = actual_ports[name]
        if expected.direction != actual["direction"]:
            errors.append(
                f"top port '{name}' direction '{actual['direction']}' does not match "
                f"manifest direction '{expected.direction}'"
            )
        if not widths_equivalent(expected.width, actual["width"]):
            errors.append(
                f"top port '{name}' width '{actual['width']}' does not match "
                f"manifest width '{expected.width}'"
            )


def _validate_manifest(files: dict[str, str]) -> None:
    resolve_project_manifest(files)


def _resolve_project_package_v1(
    manifest: dict[str, Any],
    files: dict[str, str],
) -> ResolvedProjectManifest:
    contract_errors = validate_project_package_manifest(manifest)
    if contract_errors:
        raise ValueError(
            "manifest.json does not satisfy project-package-v1: "
            + "; ".join(contract_errors)
        )

    project_name = manifest["project_name"]
    top = manifest["top"]
    top_module = top["module"]
    top_source_value = top["source"]
    raw_sources = manifest["sources"]
    raw_artifacts = manifest["artifacts"]

    sources: list[str] = []
    source_languages: dict[str, str] = {}
    for index, record in enumerate(raw_sources):
        path = _manifest_path(record.get("path"), f"manifest.sources[{index}].path")
        sources.append(path)
        source_languages[path] = record["language"]
    _reject_duplicate_paths(sources, "manifest.sources")

    top_source = _manifest_path(top_source_value, "manifest.top.source")
    if top_source not in sources:
        raise ValueError("manifest.top.source must reference a manifest.sources path")

    artifact_paths_by_role: dict[str, list[str]] = {}
    artifact_paths: list[str] = []
    for index, record in enumerate(raw_artifacts):
        path = _manifest_path(record.get("path"), f"manifest.artifacts[{index}].path")
        role = record["role"]
        artifact_paths.append(path)
        artifact_paths_by_role.setdefault(role, []).append(path)
    _reject_duplicate_paths(artifact_paths, "manifest.artifacts")

    overlap = sorted(set(sources) & set(artifact_paths))
    if overlap:
        raise ValueError(
            "manifest paths cannot be both sources and artifacts: " + ", ".join(overlap)
        )
    _require_referenced_files(files, sources, "source")
    _require_referenced_files(files, artifact_paths, "artifact")

    declared_paths = {"manifest.json", *sources, *artifact_paths}
    undeclared = sorted(set(files) - declared_paths)
    if undeclared:
        raise ValueError(
            "canonical manifest.json does not declare project files: " + ", ".join(undeclared)
        )
    _require_complete_rtl_source_set(files, sources, artifact_paths_by_role)

    return ResolvedProjectManifest(
        contract_version=PROJECT_PACKAGE_VERSION,
        project_name=project_name.strip(),
        top_module=top_module.strip(),
        top_source=top_source,
        sources=tuple(sources),
        source_languages=source_languages,
        top_ports=tuple(
            ResolvedTopPort(
                name=port["name"],
                direction=port["direction"],
                width=port["width"],
            )
            for port in top["interface"]["ports"]
        ),
        artifact_paths_by_role={
            role: tuple(paths) for role, paths in artifact_paths_by_role.items()
        },
        is_legacy=False,
    )


def _resolve_legacy_manifest(
    manifest: dict[str, Any],
    files: dict[str, str],
) -> ResolvedProjectManifest:
    missing_fields: list[str] = []
    top_module = manifest.get("top_module")
    if not isinstance(top_module, str) or not top_module.strip():
        missing_fields.append("top_module")
    raw_sources = manifest.get("sources")
    if (
        not isinstance(raw_sources, list)
        or not raw_sources
        or not all(isinstance(item, str) and item for item in raw_sources)
    ):
        missing_fields.append("sources")
        raw_sources = []
    if missing_fields:
        raise ValueError(f"manifest.json missing required fields: {', '.join(missing_fields)}")

    sources = [_manifest_path(path, "manifest.sources") for path in raw_sources]
    _reject_duplicate_paths(sources, "manifest.sources")
    _require_referenced_files(files, sources, "source")
    artifact_paths_by_role = _legacy_artifact_paths(manifest, files)
    declared_artifacts = [path for paths in artifact_paths_by_role.values() for path in paths]
    _require_referenced_files(files, declared_artifacts, "artifact")
    _require_complete_rtl_source_set(files, sources, artifact_paths_by_role)

    normalized_top = top_module.strip()
    top_candidates = [
        source
        for source in sources
        if normalized_top in declared_modules(files, [source])
    ]
    return ResolvedProjectManifest(
        contract_version="legacy-unversioned",
        project_name=str(manifest.get("project_name", "")).strip(),
        top_module=normalized_top,
        top_source=top_candidates[0] if len(top_candidates) == 1 else None,
        sources=tuple(sources),
        source_languages={},
        top_ports=None,
        artifact_paths_by_role={
            role: tuple(paths) for role, paths in artifact_paths_by_role.items()
        },
        is_legacy=True,
    )


def _legacy_artifact_paths(
    manifest: dict[str, Any],
    files: dict[str, str],
) -> dict[str, list[str]]:
    artifacts: dict[str, list[str]] = {}
    simulation = manifest.get("simulation")
    if simulation is not None:
        if not isinstance(simulation, dict):
            raise ValueError("manifest.simulation must be an object when present")
        testbench = simulation.get("testbench")
        if testbench is not None:
            artifacts["candidate_testbench"] = [
                _manifest_path(testbench, "manifest.simulation.testbench")
            ]

    constraints = _legacy_named_paths(manifest.get("constraints"), "manifest.constraints")
    if constraints:
        artifacts["constraint"] = [path for paths in constraints.values() for path in paths]
    reports = _legacy_named_paths(manifest.get("reports"), "manifest.reports")
    if reports:
        for key, paths in reports.items():
            for path in paths:
                filename = path.rsplit("/", 1)[-1]
                role = (
                    "predicted_qor"
                    if key == "predicted_qor" or filename == "predicted_qor.json"
                    else "report"
                )
                artifacts.setdefault(role, []).append(path)
    if "system_his.json" in files:
        artifacts["system_his"] = ["system_his.json"]
    return artifacts


def _legacy_named_paths(value: Any, field: str) -> dict[str, list[str]]:
    if value is None:
        return {}
    if isinstance(value, list):
        paths = [_manifest_path(item, field) for item in value]
        return {"items": paths}
    if isinstance(value, dict):
        paths_by_key: dict[str, list[str]] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"{field} keys must be non-empty strings")
            paths_by_key[key] = [_manifest_path(item, f"{field}.{key}")]
        return paths_by_key
    raise ValueError(f"{field} must be an object or list when present")


def _manifest_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return validate_project_relative_path(value)


def _reject_duplicate_paths(paths: list[str], field: str) -> None:
    duplicates = sorted({path for path in paths if paths.count(path) > 1})
    if duplicates:
        raise ValueError(f"{field} contains duplicate paths: {', '.join(duplicates)}")


def _require_referenced_files(
    files: dict[str, str],
    paths: list[str],
    role: str,
) -> None:
    missing = sorted(path for path in paths if path not in files)
    if missing:
        raise ValueError(
            f"manifest.json references missing {role} files: {', '.join(missing)}"
        )


def _require_complete_rtl_source_set(
    files: dict[str, str],
    sources: list[str],
    artifact_paths_by_role: dict[str, list[str]],
) -> None:
    artifact_rtl_exemptions = {
        path
        for role in ("candidate_testbench", "board_wrapper")
        for path in artifact_paths_by_role.get(role, [])
    }
    undeclared_rtl = sorted(
        path
        for path in files
        if path.lower().endswith((".v", ".sv"))
        and path not in sources
        and path not in artifact_rtl_exemptions
    )
    if undeclared_rtl:
        raise ValueError(
            "manifest.sources does not declare all RTL files: " + ", ".join(undeclared_rtl)
        )


def _validate_expected_rtl_structure(files: dict[str, str], expected_task_type: str | None) -> None:
    # Family-specific topology is not part of the method-neutral package contract.
    # Keep the argument for caller compatibility while the checks move to their
    # method/family-specific validation layer.
    del files
    del expected_task_type


def _project_task_type(files: dict[str, str]) -> str | None:
    try:
        system_his = json.loads(files.get("system_his.json", "{}"))
    except json.JSONDecodeError:
        return None
    task_type = system_his.get("task_type")
    return task_type if isinstance(task_type, str) else None


def _project_system_his_schema(files: dict[str, str]) -> str:
    try:
        system_his = json.loads(files.get("system_his.json", "{}"))
    except json.JSONDecodeError:
        return ""
    schema_version = system_his.get("schema_version") if isinstance(system_his, dict) else ""
    return schema_version if isinstance(schema_version, str) else ""


def _files_from_list(raw_files: list[Any]) -> dict[str, str]:
    files: dict[str, str] = {}
    for item in raw_files:
        if not isinstance(item, dict) or "path" not in item or "content" not in item:
            raise ValueError("Each file entry must contain path and content")
        files[str(item["path"])] = str(item["content"])
    return files


def _strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped
