"""H0-H3 System-HIS validation stages."""

from __future__ import annotations

import json
from typing import Any

from sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
from sr2fpga_agent.frozen_context import (
    FrozenRequirementContext,
    frozen_project_name,
    frozen_public_project_request,
    platform_profile_sha256,
)
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.parsers import parse_system_his_payload
from sr2fpga_agent.system_his_capabilities import load_system_his_backend_capabilities
from sr2fpga_agent.system_his_fidelity import (
    check_frozen_context_system_his_fidelity,
    check_system_his_req_fidelity,
)
from sr2fpga_agent.system_his_schema import validate_registered_system_his_schema
from sr2fpga_agent.system_his_v12_checker import check_system_his_v12, check_system_his_well_formedness


_BACKEND_CAPABILITIES = load_system_his_backend_capabilities()
SUPPORTED_DATA_FLOW_PROTOCOLS = _BACKEND_CAPABILITIES.supported_data_flow_protocols
SUPPORTED_VERIFICATION_SCENARIOS = _BACKEND_CAPABILITIES.supported_verification_scenarios
SUPPORTED_COMPONENT_SEMANTIC_KINDS = _BACKEND_CAPABILITIES.supported_component_semantic_kinds
COMPONENT_SEMANTIC_KIND_ALIASES = _BACKEND_CAPABILITIES.component_semantic_kind_aliases
DATA_FLOW_PROTOCOL_ALIASES = _BACKEND_CAPABILITIES.data_flow_protocol_aliases


class SystemHisValidationError(ValueError):
    """A model-produced System-HIS candidate failed one of H0-H3."""

    def __init__(
        self,
        candidate_output: str,
        report: dict[str, Any],
        *,
        candidate_artifact_sha256: str | None = None,
    ) -> None:
        self.candidate_output = candidate_output
        self.report = report
        self.candidate_artifact_sha256 = candidate_artifact_sha256
        self.failed_h_stage = first_failed_h_stage(report) or "h0"
        stage_report = report.get(self.failed_h_stage, {})
        self.diagnostics = list(stage_report.get("diagnostics", [])) if isinstance(stage_report, dict) else []
        detail = "; ".join(self.diagnostics) or "unknown validation error"
        super().__init__(f"System-HIS {self.failed_h_stage.upper()} validation failed: {detail}")


def validate_system_his_h_stages(
    request: ProjectRequest,
    project: GeneratedProject,
    his_source_used_for_generation: str = "generated",
    platform: PlatformProfile | None = None,
) -> dict[str, Any]:
    """Validate the generated System-HIS as H0/H1/H2/H3 gates."""

    payload, h0_errors = _load_his_payload(project)
    if payload is None:
        return _initial_report(his_source_used_for_generation, h0_errors)
    return validate_system_his_payload_h_stages(
        request,
        payload,
        his_source_used_for_generation=his_source_used_for_generation,
        platform=platform,
    )


def validate_system_his_payload_h_stages(
    request: ProjectRequest,
    payload: dict[str, Any],
    his_source_used_for_generation: str = "generated",
    platform: PlatformProfile | None = None,
) -> dict[str, Any]:
    """Validate one parsed System-HIS payload through the H0-H3 gates."""

    h0_errors = _h0_payload_errors(payload)
    report = _initial_report(his_source_used_for_generation, h0_errors)
    if h0_errors:
        return report

    h1_result = check_system_his_v12(payload)
    w_rules = check_system_his_well_formedness(payload)
    report["h1"] = {
        **_stage("pass" if h1_result.passed else "fail", h1_result.errors),
        "well_formedness_rules": {
            rule_id: {"status": result.status, "diagnostics": list(result.diagnostics)}
            for rule_id, result in w_rules.items()
        },
    }
    if not h1_result.passed:
        return report

    h2_errors = _lowerability_errors(payload)
    if not h2_errors and platform is not None:
        h2_errors.extend(_dry_lowerability_errors(request, platform, payload))
    report["h2"] = _stage("pass" if not h2_errors else "fail", h2_errors)
    if h2_errors:
        return report

    h3_result = check_system_his_req_fidelity(request, payload, platform)
    h3_status = _h3_status(h3_result)
    report["h3"] = {
        "status": h3_status,
        "scores": _h3_scores(h3_result.metrics),
        "diagnostics": list(h3_result.errors),
        "metrics": h3_result.metrics,
    }
    report["passed"] = h3_status in {"pass", "not_applicable"}
    return report


def validate_frozen_system_his_payload_h_stages(
    context: FrozenRequirementContext,
    payload: dict[str, Any],
    *,
    platform: PlatformProfile,
    his_source_used_for_generation: str = "generated",
) -> dict[str, Any]:
    """Validate H0-H3 without reconstructing request or family metadata."""

    if platform_profile_sha256(platform) != context.platform_profile_sha256:
        raise ValueError("PlatformProfile does not match frozen requirement context")

    h0_errors = _h0_payload_errors(payload)
    report = _initial_report(his_source_used_for_generation, h0_errors)
    if h0_errors:
        return report

    h1_result = check_system_his_v12(payload)
    h1_errors = [*h1_result.errors, *_frozen_identity_errors(context, payload)]
    w_rules = check_system_his_well_formedness(payload)
    report["h1"] = {
        **_stage("pass" if not h1_errors else "fail", h1_errors),
        "well_formedness_rules": {
            rule_id: {"status": result.status, "diagnostics": list(result.diagnostics)}
            for rule_id, result in w_rules.items()
        },
    }
    if h1_errors:
        return report

    h2_errors = _lowerability_errors(payload)
    if not h2_errors:
        h2_errors.extend(
            _dry_lowerability_errors(frozen_public_project_request(context), platform, payload)
        )
    report["h2"] = _stage("pass" if not h2_errors else "fail", h2_errors)
    if h2_errors:
        return report

    h3_result = check_frozen_context_system_his_fidelity(context, payload)
    h3_status = _h3_status(h3_result)
    report["h3"] = {
        "status": h3_status,
        "scores": _h3_scores(h3_result.metrics),
        "diagnostics": list(h3_result.errors),
        "metrics": h3_result.metrics,
    }
    report["passed"] = h3_status == "pass"
    return report


def validate_system_his_candidate(
    request: ProjectRequest,
    candidate_output: str,
    his_source_used_for_generation: str = "generated",
    platform: PlatformProfile | None = None,
) -> dict[str, Any]:
    """Parse and validate one raw model candidate, raising with its H-stage report."""

    try:
        payload = parse_system_his_payload(candidate_output)
    except ValueError as exc:
        report = _initial_report(his_source_used_for_generation, [str(exc)])
        raise SystemHisValidationError(candidate_output, report) from exc
    report = validate_system_his_payload_h_stages(
        request,
        payload,
        his_source_used_for_generation=his_source_used_for_generation,
        platform=platform,
    )
    if not report["passed"]:
        raise SystemHisValidationError(candidate_output, report)
    return payload


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
    if not isinstance(payload, dict):
        return None, ["system_his must be an object"]
    return payload, _h0_payload_errors(payload)


def _h0_payload_errors(payload: Any) -> list[str]:
    return validate_registered_system_his_schema(payload)


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
        if testbench and testbench != _BACKEND_CAPABILITIES.canonical_testbench:
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


def _dry_lowerability_errors(
    request: ProjectRequest,
    platform: PlatformProfile,
    payload: dict[str, Any],
) -> list[str]:
    try:
        build_contract_skeleton_project(request, platform, payload)
    except (KeyError, TypeError, ValueError) as exc:
        return [f"H2 deterministic dry-lowering failed: {exc}"]
    return []


def _frozen_identity_errors(
    context: FrozenRequirementContext,
    payload: dict[str, Any],
) -> list[str]:
    expected = frozen_project_name(context)
    values: list[tuple[str, Any]] = [("project_name", payload.get("project_name"))]
    project = payload.get("project")
    if isinstance(project, dict):
        values.extend(
            [
                ("project.name", project.get("name")),
                ("project.project_name", project.get("project_name")),
            ]
        )
    return [
        f"H1 frozen identity: {path} must equal '{expected}'"
        for path, value in values
        if value is not None and value != expected
    ]


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


def _initial_report(his_source_used_for_generation: str, h0_errors: list[str]) -> dict[str, Any]:
    return {
        "his_source_used_for_generation": his_source_used_for_generation,
        "h0": _stage("pass" if not h0_errors else "fail", h0_errors),
        "h1": _stage("not_run", []),
        "h2": _stage("not_run", []),
        "h3": _stage("not_run", []),
        "passed": False,
    }


def _stage(status: str, diagnostics: list[str]) -> dict[str, Any]:
    return {"status": status, "diagnostics": diagnostics}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
