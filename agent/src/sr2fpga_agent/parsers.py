"""Response parsers and project validation helpers."""

from __future__ import annotations

import difflib
import json
from typing import Any

from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.path_safety import validate_project_relative_path
from sr2fpga_agent.system_his_checker import check_project_l0
from sr2fpga_agent.system_his_v12_checker import check_system_his_v12

REQUIRED_PROJECT_FILES = {
    "system_his.json",
    "manifest.json",
    "rtl/top.v",
    "constraints/timing.sdc",
    "sim/tb_top.v",
    "reports/predicted_qor.json",
}

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


def parse_project_files(content: str, expected_task_type: str | None = None) -> dict[str, str]:
    """Parse DeepSeek JSON output into project files."""
    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"DeepSeek output is not valid JSON: {exc.msg}") from exc

    raw_files = payload.get("files")
    if isinstance(raw_files, dict):
        files = {str(path): str(file_content) for path, file_content in raw_files.items()}
    elif isinstance(raw_files, list):
        files = _files_from_list(raw_files)
    else:
        raise ValueError("DeepSeek output must contain files as an object or list")

    files = {
        validate_project_relative_path(path): _ensure_trailing_newline(content)
        for path, content in files.items()
    }
    missing = sorted(REQUIRED_PROJECT_FILES - set(files))
    if missing:
        raise ValueError(f"DeepSeek output is missing required files: {', '.join(missing)}")
    _validate_manifest(files)
    _validate_expected_rtl_structure(files, expected_task_type)
    return files


def parse_behavior_files(content: str) -> dict[str, str]:
    """Parse HIS2PROJECT JSON output into behavior-only file bodies."""

    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"DeepSeek HIS2PROJECT behavior output is not valid JSON: {exc.msg}") from exc
    if "files" in payload:
        raise ValueError("HIS2PROJECT response must contain behavior_files, not files")
    raw_behavior = payload.get("behavior_files")
    if not isinstance(raw_behavior, dict):
        raise ValueError("HIS2PROJECT response must contain behavior_files as an object")
    return {str(path): str(body) for path, body in raw_behavior.items()}


def parse_system_his_v12(content: str) -> dict[str, Any]:
    """Parse and validate DeepSeek output as System-HIS v1.2 JSON."""
    cleaned = _strip_markdown_fence(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"DeepSeek System-HIS output is not valid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("DeepSeek System-HIS output must be a JSON object")
    system_his = payload.get("system_his", payload)
    if not isinstance(system_his, dict):
        raise ValueError("DeepSeek System-HIS output field system_his must be an object")

    result = check_system_his_v12(system_his)
    if not result.passed:
        raise ValueError("DeepSeek System-HIS v1.2 failed validation: " + "; ".join(result.errors))
    return system_his


def _validate_system_his_contract_unchanged(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    frozen_keys = ("schema_version", "top", "state", "components", "instances", "data_flow", "control_flow", "artifacts")
    for key in frozen_keys:
        if _canonical_json(expected.get(key)) != _canonical_json(actual.get(key)):
            raise ValueError(f"DeepSeek HIS2PROJECT changed frozen System-HIS contract section '{key}'")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    raise ValueError("DeepSeek repair introduced L0 contract violations: " + "; ".join(l0_result.errors))


def _diagnosis_mentions_path(diagnosis: dict[str, object], path: str) -> bool:
    affected_files = diagnosis.get("affected_files")
    if isinstance(affected_files, list) and path in {str(item) for item in affected_files}:
        return True
    return path.lower() in json.dumps(diagnosis, ensure_ascii=False).lower()


def _ensure_trailing_newline(content: str) -> str:
    return content if content.endswith("\n") else content + "\n"


def _validate_manifest(files: dict[str, str]) -> None:
    try:
        manifest = json.loads(files["manifest.json"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest.json is not valid JSON: {exc.msg}") from exc

    missing_fields: list[str] = []
    if not isinstance(manifest.get("top_module"), str) or not manifest["top_module"]:
        missing_fields.append("top_module")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        missing_fields.append("sources")

    simulation = manifest.get("simulation")
    testbench = simulation.get("testbench") if isinstance(simulation, dict) else None
    if not isinstance(testbench, str) or not testbench:
        missing_fields.append("simulation.testbench")

    if missing_fields:
        raise ValueError(f"manifest.json missing required fields: {', '.join(missing_fields)}")

    missing_sources = sorted(path for path in sources if path not in files)
    if missing_sources:
        raise ValueError(f"manifest.json references missing source files: {', '.join(missing_sources)}")
    if testbench not in files:
        raise ValueError(f"manifest.json references missing testbench file: {testbench}")


def _validate_expected_rtl_structure(files: dict[str, str], expected_task_type: str | None) -> None:
    if expected_task_type not in MULTIMODULE_RTL_EXAMPLES:
        return

    manifest = json.loads(files["manifest.json"])
    sources = manifest["sources"]
    rtl_sources = [path for path in sources if path.startswith("rtl/") and path.endswith(".v")]
    if "rtl/top.v" not in rtl_sources:
        raise ValueError("manifest.json sources must include rtl/top.v for multi-module tasks")
    if len(rtl_sources) < 3:
        raise ValueError(
            "DeepSeek output for multi-module task "
            f"{expected_task_type} must include rtl/top.v and at least two submodule .v files"
        )


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
