"""Productized H0-H3 System-HIS validation stages."""

from __future__ import annotations

import json
from typing import Any

from LLM.src.sr2fpga_agent.models import GeneratedProject, ProjectRequest
from LLM.src.sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity
from LLM.src.sr2fpga_agent.system_his_v12_checker import (
    REQUIRED_TOP_LEVEL_KEYS,
    SCHEMA_VERSION,
    check_system_his_v12,
)


SUPPORTED_DATA_FLOW_PROTOCOLS = {"wire", "register", "valid_ready"}
SUPPORTED_VERIFICATION_SCENARIOS = {
    "reset",
    "nominal_operation",
    "flat_image",
    "axis_sensitive_edges",
    "back_to_back_matches",
    "threshold_boundary",
    "border_policy",
    "boundary_match_index",
    "continuous_frames",
    "defect_present_absent",
    "exact_match",
    "first_defect_coordinate",
    "stall_stability",
    "frame_boundary",
    "input_stall",
    "missing_final_in_last",
    "no_false_positive",
    "no_match",
    "overlapping_match",
    "partial_match",
    "reset_during_frame",
    "reset_during_partial_match",
}
SUPPORTED_COMPONENT_SEMANTIC_KINDS = {
    "accumulator",
    "buffer",
    "counter",
    "fifo",
    "fsm",
    "fork",
    "gate",
    "join",
    "mac",
    "pwm",
    "rtl_component",
    "spi",
    "stage",
    "top_integration",
}
COMPONENT_SEMANTIC_KIND_ALIASES = {
    "arithmetic_accumulator": "accumulator",
    "dual_stream_join": "join",
    "elastic_stream_buffer": "buffer",
    "pipeline_stage": "stage",
    "registered_stream_stage": "stage",
    "stream_accumulator": "accumulator",
    "stream_buffer": "buffer",
    "synchronous_fifo": "fifo",
}
DATA_FLOW_PROTOCOL_ALIASES = {
    "combinational": "wire",
    "combinational_operand": "wire",
    "registered_data": "register",
    "registered_enable": "register",
}
H0_OBJECT_FIELDS = {"intent", "top", "state", "timing", "resources", "verification", "artifacts"}
H0_LIST_FIELDS = {"components", "instances", "data_flow", "control_flow"}


def validate_system_his_h_stages(
    request: ProjectRequest,
    project: GeneratedProject,
    his_source_used_for_generation: str = "generated",
) -> dict[str, Any]:
    """Validate the generated System-HIS as H0/H1/H2/H3 gates."""

    payload, h0_errors = _load_his_payload(project)
    report = {
        "his_source_used_for_generation": his_source_used_for_generation,
        "h0": _stage("pass" if not h0_errors else "fail", h0_errors),
        "h1": _stage("not_run", []),
        "h2": _stage("not_run", []),
        "h3": _stage("not_run", []),
        "passed": False,
    }
    if h0_errors or payload is None:
        return report

    h1_result = check_system_his_v12(payload)
    report["h1"] = _stage("pass" if h1_result.passed else "fail", h1_result.errors)
    if not h1_result.passed:
        return report

    h2_errors = _lowerability_errors(payload)
    report["h2"] = _stage("pass" if not h2_errors else "fail", h2_errors)
    if h2_errors:
        return report

    h3_result = check_system_his_req_fidelity(request, payload)
    h3_status = _h3_status(h3_result)
    report["h3"] = {
        "status": h3_status,
        "scores": _h3_scores(h3_result.metrics),
        "diagnostics": list(h3_result.errors),
        "metrics": h3_result.metrics,
    }
    report["passed"] = h3_status in {"pass", "not_applicable"}
    return report


def first_failed_h_stage(report: dict[str, Any]) -> str | None:
    for stage in ("h0", "h1", "h2", "h3"):
        data = report.get(stage, {})
        if isinstance(data, dict) and data.get("status") == "fail":
            return stage
    return None


def h_stage_labels(report: dict[str, Any]) -> dict[str, Any]:
    labels: dict[str, Any] = {}
    for stage in ("h0", "h1", "h2", "h3"):
        data = report.get(stage, {})
        status = data.get("status") if isinstance(data, dict) else "not_run"
        labels[f"{stage}_status"] = status
        labels[f"{stage}_pass"] = status in {"pass", "not_applicable"}
    labels["generated_his_pass_credit"] = report.get("his_source_used_for_generation") != "oracle_fallback"
    return labels


def _load_his_payload(project: GeneratedProject) -> tuple[dict[str, Any] | None, list[str]]:
    content = project.files.get("system_his.json")
    if content is None:
        return None, ["system_his.json is missing"]
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return None, [f"system_his.json is not valid JSON: {exc.msg}"]
    errors: list[str] = []
    if not isinstance(payload, dict):
        return None, ["system_his must be an object"]
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"system_his.schema_version must be {SCHEMA_VERSION}")
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            errors.append(f"system_his.{key} is required")
    for key in H0_OBJECT_FIELDS:
        if key in payload and not isinstance(payload[key], dict):
            errors.append(f"system_his.{key} must be an object")
    for key in H0_LIST_FIELDS:
        if key in payload and not isinstance(payload[key], list):
            errors.append(f"system_his.{key} must be a list")
        _require_object_items(payload, key, "system_his", errors)
    _validate_h0_nested_types(payload, errors)
    return payload, errors


def _validate_h0_nested_types(payload: dict[str, Any], errors: list[str]) -> None:
    top = payload.get("top")
    if isinstance(top, dict):
        _require_list(top, "ports", "system_his.top", errors)
        _require_list(top, "clocks", "system_his.top", errors)
        _require_list(top, "resets", "system_his.top", errors)
        _require_object_items(top, "ports", "system_his.top", errors)
        _require_object_items(top, "clocks", "system_his.top", errors)
        _require_object_items(top, "resets", "system_his.top", errors)

    intent = payload.get("intent")
    if isinstance(intent, dict):
        _require_list(intent, "assumptions", "system_his.intent", errors)

    state = payload.get("state")
    if isinstance(state, dict):
        for key in ("registers", "counters", "fsms", "buffers", "memories"):
            _require_list(state, key, "system_his.state", errors)
            _require_object_items(state, key, "system_his.state", errors)

    timing = payload.get("timing")
    if isinstance(timing, dict):
        _require_list(timing, "constraints", "system_his.timing", errors)

    resources = payload.get("resources")
    if isinstance(resources, dict):
        _require_object(resources, "expected", "system_his.resources", errors)

    verification = payload.get("verification")
    if isinstance(verification, dict):
        _require_list(verification, "scenarios", "system_his.verification", errors)
        _require_list(verification, "checks", "system_his.verification", errors)

    artifacts = payload.get("artifacts")
    if isinstance(artifacts, dict):
        _require_list(artifacts, "rtl_sources", "system_his.artifacts", errors)
        _require_list(artifacts, "testbenches", "system_his.artifacts", errors)
        _require_list(artifacts, "constraints", "system_his.artifacts", errors)

    for index, component in enumerate(_list(payload.get("components"))):
        if isinstance(component, dict):
            _require_list(component, "ports", f"system_his.components[{index}]", errors)
            _require_list(component, "parameters", f"system_his.components[{index}]", errors)
            _require_object_items(component, "ports", f"system_his.components[{index}]", errors)
            _require_object_items(component, "parameters", f"system_his.components[{index}]", errors)

    for index, instance in enumerate(_list(payload.get("instances"))):
        if isinstance(instance, dict):
            _require_object(instance, "parameter_values", f"system_his.instances[{index}]", errors)

    for index, flow in enumerate(_list(payload.get("data_flow"))):
        if isinstance(flow, dict):
            _require_list(flow, "path", f"system_his.data_flow[{index}]", errors)
            _require_object(flow, "payload", f"system_his.data_flow[{index}]", errors)
            _require_object(flow, "timing", f"system_his.data_flow[{index}]", errors)


def _require_list(container: dict[str, Any], key: str, path: str, errors: list[str]) -> None:
    if key in container and not isinstance(container[key], list):
        errors.append(f"{path}.{key} must be a list")


def _require_object(container: dict[str, Any], key: str, path: str, errors: list[str]) -> None:
    if key in container and not isinstance(container[key], dict):
        errors.append(f"{path}.{key} must be an object")


def _require_object_items(container: dict[str, Any], key: str, path: str, errors: list[str]) -> None:
    value = container.get(key)
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{path}.{key}[{index}] must be an object")


def _lowerability_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for index, component in enumerate(_list(payload.get("components"))):
        if not isinstance(component, dict):
            continue
        semantic_kind = str(component.get("semantic_kind", "")).strip()
        canonical_kind = COMPONENT_SEMANTIC_KIND_ALIASES.get(semantic_kind, semantic_kind)
        if semantic_kind and canonical_kind not in SUPPORTED_COMPONENT_SEMANTIC_KINDS:
            errors.append(
                f"H2 lowerability: components[{index}] has unsupported semantic_kind '{semantic_kind}'"
            )
    for index, flow in enumerate(_list(payload.get("data_flow"))):
        if not isinstance(flow, dict):
            continue
        protocol = str(flow.get("protocol", "")).strip()
        canonical_protocol = DATA_FLOW_PROTOCOL_ALIASES.get(protocol, protocol)
        if protocol and canonical_protocol not in SUPPORTED_DATA_FLOW_PROTOCOLS:
            errors.append(f"H2 lowerability: data_flow[{index}] has unsupported protocol '{protocol}'")
    verification = payload.get("verification")
    if isinstance(verification, dict):
        testbench = str(verification.get("testbench", "")).strip()
        if testbench and testbench != "sim/tb_top.v":
            errors.append(f"H2 lowerability: unsupported testbench '{testbench}'")
        for index, scenario in enumerate(_list(verification.get("scenarios"))):
            scenario_name = _scenario_identifier(scenario)
            if not scenario_name:
                errors.append(
                    f"H2 lowerability: verification.scenarios[{index}] scenario object requires "
                    "canonical 'kind' or 'name'"
                )
            elif scenario_name not in SUPPORTED_VERIFICATION_SCENARIOS:
                errors.append(f"H2 lowerability: verification.scenarios[{index}] unsupported scenario '{scenario_name}'")
    return errors


def _scenario_identifier(scenario: Any) -> str:
    if isinstance(scenario, str):
        return scenario.strip()
    if isinstance(scenario, dict):
        kind = str(scenario.get("kind", "")).strip()
        if kind:
            return kind
        return str(scenario.get("name", "")).strip()
    return ""


def _h3_status(result: Any) -> str:
    statuses = {metric.get("status") for metric in result.metrics.values() if isinstance(metric, dict)}
    if statuses == {"not_applicable"}:
        return "not_applicable"
    return "pass" if result.passed else "fail"


def _h3_scores(metrics: dict[str, Any]) -> dict[str, float | None]:
    scores: dict[str, float | None] = {}
    for key, metric in metrics.items():
        status = metric.get("status") if isinstance(metric, dict) else None
        if status == "pass":
            scores[key] = 1.0
        elif status == "fail":
            scores[key] = 0.0
        else:
            scores[key] = None
    return scores


def _stage(status: str, diagnostics: list[str]) -> dict[str, Any]:
    return {"status": status, "diagnostics": diagnostics}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
