"""REQ-to-System-HIS fidelity checks for known synthetic tasks."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sr2fpga_agent.frozen_context import FrozenRequirementContext

from sr2fpga_agent.family_recipe import recipe_task_type, select_family_recipe
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.project_generator import COMPONENT_TOPOLOGIES, ProjectGenerator
from sr2fpga_agent.requirement_envelope import build_request_requirement_envelope
from sr2fpga_agent.rtl_introspect import widths_equivalent


@dataclass(frozen=True)
class SystemHisReqFidelityResult:
    """Result of validating whether System-HIS preserves the original request."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, dict[str, Any]] = field(default_factory=dict)


FIDELITY_METRIC_KEYS = (
    "interface_extraction",
    "clock_reset_fidelity",
    "parameter_fidelity",
    "behavior_intent_fidelity",
    "verification_intent_fidelity",
    "constraint_fidelity",
)

_FORBIDDEN_COMPONENT_ALIAS_PORTS: dict[str, set[str]] = {
    "accumulator_core": {
        "sample_valid_in",
        "sample_valid_out",
        "sample_ready_in",
        "sample_ready_out",
    }
}


_TASK_TOP_PORTS: dict[str, dict[str, dict[str, Any]]] = {
    "alu_control_unit": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "valid": {"direction": "input"},
        "ready": {"direction": "output"},
        "op": {"direction": "input", "width": 3},
        "lhs": {"direction": "input", "width": "request"},
        "rhs": {"direction": "input", "width": "request"},
        "result_valid": {"direction": "output"},
        "result": {"direction": "output", "width": "request"},
        "zero": {"direction": "output"},
        "carry": {"direction": "output"},
        "negative": {"direction": "output"},
    },
    "crc_stream_checker": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "in_valid": {"direction": "input"},
        "in_data": {"direction": "input", "width": "request"},
        "frame_start": {"direction": "input"},
        "frame_end": {"direction": "input"},
        "expected_crc": {"direction": "input", "width": 8},
        "out_ready": {"direction": "input"},
        "in_ready": {"direction": "output"},
        "out_valid": {"direction": "output"},
        "crc_value": {"direction": "output", "width": 8},
        "crc_match": {"direction": "output"},
    },
    "composed_event_counter": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "event_valid": {"direction": "input"},
        "count": {"direction": "output", "width": "request"},
    },
    "composed_stream_accumulator": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "in_valid": {"direction": "input"},
        "in_data": {"direction": "input", "width": "request"},
        "in_ready": {"direction": "output"},
        "sample_valid": {"direction": "output"},
        "sum": {"direction": "output"},
    },
    "composed_stream_fork": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "in_valid": {"direction": "input"},
        "in_data": {"direction": "input", "width": "request"},
        "out0_ready": {"direction": "input"},
        "out1_ready": {"direction": "input"},
        "in_ready": {"direction": "output"},
        "out0_valid": {"direction": "output"},
        "out0_data": {"direction": "output", "width": "request"},
        "out1_valid": {"direction": "output"},
        "out1_data": {"direction": "output", "width": "request"},
    },
    "composed_dual_stream_join": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "in0_valid": {"direction": "input"},
        "in0_data": {"direction": "input", "width": "request"},
        "in1_valid": {"direction": "input"},
        "in1_data": {"direction": "input", "width": "request"},
        "out_ready": {"direction": "input"},
        "in0_ready": {"direction": "output"},
        "in1_ready": {"direction": "output"},
        "out_valid": {"direction": "output"},
        "out_data": {"direction": "output"},
    },
    "composed_vector_mac_pipeline": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "feature_valid": {"direction": "input"},
        "feature_data": {"direction": "input", "width": "request"},
        "weight_valid": {"direction": "input"},
        "weight_data": {"direction": "input", "width": "request"},
        "bias": {"direction": "input"},
        "score_ready": {"direction": "input"},
        "feature_ready": {"direction": "output"},
        "weight_ready": {"direction": "output"},
        "score_valid": {"direction": "output"},
        "score_data": {"direction": "output"},
    },
    "composed_td_update_core": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "in_valid": {"direction": "input"},
        "reward": {"direction": "input", "width": "request"},
        "value": {"direction": "input", "width": "request"},
        "next_value": {"direction": "input", "width": "request"},
        "gamma": {"direction": "input", "width": "request"},
        "alpha": {"direction": "input", "width": "request"},
        "out_ready": {"direction": "input"},
        "in_ready": {"direction": "output"},
        "out_valid": {"direction": "output"},
        "td_error": {"direction": "output", "width": "request"},
        "updated_value": {"direction": "output", "width": "request"},
    },
    "composed_policy_value_shell": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "cfg_valid": {"direction": "input"},
        "cfg_addr": {"direction": "input", "width": 3},
        "cfg_data": {"direction": "input", "width": "request"},
        "cfg_ready": {"direction": "output"},
        "obs_valid": {"direction": "input"},
        "obs_ready": {"direction": "output"},
        "obs0": {"direction": "input", "width": "request"},
        "obs1": {"direction": "input", "width": "request"},
        "action_valid": {"direction": "output"},
        "action_ready": {"direction": "input"},
        "selected_action": {"direction": "output"},
        "value_estimate": {"direction": "output", "width": "request"},
    },
    "composed_replay_sample_shell": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "host_valid": {"direction": "input"},
        "host_ready": {"direction": "output"},
        "host_state": {"direction": "input", "width": "request"},
        "host_action": {"direction": "input"},
        "host_reward": {"direction": "input", "width": "request"},
        "host_next_state": {"direction": "input", "width": "request"},
        "host_done": {"direction": "input"},
        "sample_valid": {"direction": "output"},
        "sample_ready": {"direction": "input"},
        "sample_state": {"direction": "output", "width": "request"},
        "sample_action": {"direction": "output"},
        "sample_reward": {"direction": "output", "width": "request"},
        "sample_next_state": {"direction": "output", "width": "request"},
        "sample_done": {"direction": "output"},
        "occupancy": {"direction": "output", "width": 3},
    },
    "composed_host_protocol_shell": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "s_axi_awvalid": {"direction": "input"},
        "s_axi_awready": {"direction": "output"},
        "s_axi_awaddr": {"direction": "input", "width": 4},
        "s_axi_wvalid": {"direction": "input"},
        "s_axi_wready": {"direction": "output"},
        "s_axi_wdata": {"direction": "input", "width": "request"},
        "s_axi_wstrb": {"direction": "input"},
        "s_axi_bvalid": {"direction": "output"},
        "s_axi_bready": {"direction": "input"},
        "s_axi_arvalid": {"direction": "input"},
        "s_axi_arready": {"direction": "output"},
        "s_axi_araddr": {"direction": "input", "width": 4},
        "s_axi_rvalid": {"direction": "output"},
        "s_axi_rready": {"direction": "input"},
        "s_axi_rdata": {"direction": "output", "width": "request"},
        "m_axis_tvalid": {"direction": "output"},
        "m_axis_tready": {"direction": "input"},
        "m_axis_tdata": {"direction": "output"},
        "m_axis_tlast": {"direction": "output"},
        "irq": {"direction": "output"},
    },
    "composed_rl_accelerator_shell": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "cfg_valid": {"direction": "input"},
        "cfg_ready": {"direction": "output"},
        "cfg_addr": {"direction": "input", "width": 3},
        "cfg_data": {"direction": "input", "width": "request"},
        "sample_valid": {"direction": "input"},
        "sample_ready": {"direction": "output"},
        "obs0": {"direction": "input", "width": "request"},
        "obs1": {"direction": "input", "width": "request"},
        "reward": {"direction": "input", "width": "request"},
        "next_value": {"direction": "input", "width": "request"},
        "done_in": {"direction": "input"},
        "result_valid": {"direction": "output"},
        "result_ready": {"direction": "input"},
        "selected_action": {"direction": "output"},
        "value_estimate": {"direction": "output", "width": "request"},
        "updated_value": {"direction": "output", "width": "request"},
        "episode_done": {"direction": "output"},
        "irq": {"direction": "output"},
    },
    "composed_batch_rl_accelerator_shell": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "cfg_valid": {"direction": "input"},
        "cfg_ready": {"direction": "output"},
        "cfg_addr": {"direction": "input", "width": 3},
        "cfg_data": {"direction": "input", "width": "request"},
        "batch_valid": {"direction": "input"},
        "batch_ready": {"direction": "output"},
        "obs0_a": {"direction": "input", "width": "request"},
        "obs1_a": {"direction": "input", "width": "request"},
        "reward_a": {"direction": "input", "width": "request"},
        "next_value_a": {"direction": "input", "width": "request"},
        "done_a": {"direction": "input"},
        "obs0_b": {"direction": "input", "width": "request"},
        "obs1_b": {"direction": "input", "width": "request"},
        "reward_b": {"direction": "input", "width": "request"},
        "next_value_b": {"direction": "input", "width": "request"},
        "done_b": {"direction": "input"},
        "result_valid": {"direction": "output"},
        "result_ready": {"direction": "input"},
        "selected_action_a": {"direction": "output"},
        "value_estimate_a": {"direction": "output", "width": "request"},
        "updated_value_a": {"direction": "output", "width": "request"},
        "selected_action_b": {"direction": "output"},
        "value_estimate_b": {"direction": "output", "width": "request"},
        "updated_value_b": {"direction": "output", "width": "request"},
        "batch_done": {"direction": "output"},
        "irq": {"direction": "output"},
    },
    "composed_replay_arbiter_shell": {
        "clk": {"direction": "input"},
        "rst_n": {"direction": "input"},
        "host_valid": {"direction": "input"},
        "host_ready": {"direction": "output"},
        "host_state": {"direction": "input", "width": "request"},
        "host_action": {"direction": "input"},
        "host_reward": {"direction": "input", "width": "request"},
        "host_next_state": {"direction": "input", "width": "request"},
        "host_done": {"direction": "input"},
        "sample_req_valid": {"direction": "input"},
        "sample_req_ready": {"direction": "output"},
        "sample_index": {"direction": "input", "width": 2},
        "sample_valid": {"direction": "output"},
        "sample_ready": {"direction": "input"},
        "sample_state": {"direction": "output", "width": "request"},
        "sample_action": {"direction": "output"},
        "sample_reward": {"direction": "output", "width": "request"},
        "sample_next_state": {"direction": "output", "width": "request"},
        "sample_done": {"direction": "output"},
        "occupancy": {"direction": "output", "width": 3},
        "write_index": {"direction": "output", "width": 2},
        "irq": {"direction": "output"},
    },
}


_SUPPLEMENTAL_TASK_COMPONENTS = {
    "alu_control_unit": ["control_decode", "alu_core", "status_flags"],
    "crc_stream_checker": ["stream_frame_accumulator", "crc8_update", "crc_status"],
}


def check_system_his_req_fidelity(
    request: ProjectRequest,
    payload: dict[str, Any],
    platform: PlatformProfile | None = None,
) -> SystemHisReqFidelityResult:
    """Check the generic trace, then optionally apply a family fidelity plugin."""

    trace_result = _check_requirement_trace(request, payload, platform)
    if platform is None:
        return trace_result

    try:
        envelope = build_request_requirement_envelope(request, platform)
        decision = select_family_recipe(request, envelope)
    except ValueError as exc:
        policy_result = SystemHisReqFidelityResult(
            passed=False,
            errors=[f"REQ2HIS family recipe policy: {exc}"],
            metrics=_metrics_from_errors([f"REQ2HIS family recipe policy: {exc}"]),
        )
        return _merge_fidelity_results(trace_result, policy_result)
    selected_task_type = recipe_task_type(decision)
    if selected_task_type is None:
        return trace_result

    family_request = replace(request, task_type=selected_task_type)
    family_result = check_system_his_family_recipe_fidelity(family_request, payload)
    return _merge_fidelity_results(trace_result, family_result)


def check_system_his_family_recipe_fidelity(
    request: ProjectRequest,
    payload: dict[str, Any],
) -> SystemHisReqFidelityResult:
    """Apply the optional, known-family fidelity plugin in isolation."""

    if request.task_type not in COMPONENT_TOPOLOGIES and request.task_type not in _SUPPLEMENTAL_TASK_COMPONENTS:
        return SystemHisReqFidelityResult(passed=True, metrics=_not_applicable_metrics())

    errors: list[str] = []
    _validate_components(request, payload, errors)
    _validate_component_ports(request, payload, errors)
    _validate_forbidden_component_alias_ports(payload, errors)
    _validate_instances(request, payload, errors)
    _validate_top_ports(request, payload, errors)
    _validate_clock_reset(payload, errors)
    _validate_verification(payload, errors)
    _validate_constraints(payload, errors)
    return SystemHisReqFidelityResult(
        passed=not errors,
        errors=errors,
        metrics=_metrics_from_errors(errors),
    )


def _check_requirement_trace(
    request: ProjectRequest,
    payload: dict[str, Any],
    platform: PlatformProfile | None,
) -> SystemHisReqFidelityResult:
    errors: list[str] = []
    if platform is None:
        errors.append(
            "REQ2HIS requirement fidelity: PlatformProfile is required to verify requirement_trace"
        )
        return SystemHisReqFidelityResult(
            passed=False,
            errors=errors,
            metrics=_metrics_from_errors(errors),
        )

    try:
        expected_trace = build_request_requirement_envelope(
            request,
            platform,
        ).requirement_trace_template()
    except ValueError as exc:
        errors.append(f"REQ2HIS requirement fidelity: invalid requirement: {exc}")
        return SystemHisReqFidelityResult(
            passed=False,
            errors=errors,
            metrics=_metrics_from_errors(errors),
        )

    return _check_requirement_trace_against_expected(expected_trace, payload)


def check_frozen_context_system_his_fidelity(
    context: "FrozenRequirementContext",
    payload: dict[str, Any],
) -> SystemHisReqFidelityResult:
    """Check generic H3 directly against the frozen public fact projection."""

    from sr2fpga_agent.frozen_context import frozen_requirement_trace_template

    return _check_requirement_trace_against_expected(
        frozen_requirement_trace_template(context), payload
    )


def build_frozen_requirement_trace(
    context: "FrozenRequirementContext",
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build value-aware pointers for deterministic/fake frozen-context HIS."""

    from sr2fpga_agent.frozen_context import frozen_requirement_trace_template

    trace = frozen_requirement_trace_template(context)
    mappings: dict[str, list[str]] = {}
    candidates = [
        (pointer, value, tokens)
        for pointer, value, tokens in _semantic_pointer_candidates(payload)
        if tokens[:2] != ("intent", "requirement_trace")
    ]
    for key, fact in trace["required_facts"].items():
        structurally_valid = [
            (pointer, value, tokens)
            for pointer, value, tokens in candidates
            if _pointer_matches_required_fact(key, tokens)
        ]
        selected = [
            pointer
            for pointer, value, tokens in structurally_valid
            if _mapped_values_preserve_required_fact(key, fact["value"], [(value, tokens)])
        ][:1]
        if not selected and structurally_valid:
            resolved = [(value, tokens) for _pointer, value, tokens in structurally_valid]
            if _mapped_values_preserve_required_fact(key, fact["value"], resolved):
                selected = [pointer for pointer, _value, _tokens in structurally_valid]
        mappings[key] = selected
    trace["fact_to_his"] = mappings
    trace["unresolved_facts"] = [key for key, pointers in mappings.items() if not pointers]
    return trace


def _check_requirement_trace_against_expected(
    expected_trace: dict[str, Any],
    payload: dict[str, Any],
) -> SystemHisReqFidelityResult:
    errors: list[str] = []
    intent = payload.get("intent")
    trace = intent.get("requirement_trace") if isinstance(intent, dict) else None
    if not isinstance(trace, dict):
        errors.append(
            "REQ2HIS requirement fidelity: intent.requirement_trace must be an object"
        )
        return SystemHisReqFidelityResult(
            passed=False,
            errors=errors,
            metrics=_metrics_from_errors(errors),
        )

    expected_keys = {
        "requirement_id",
        "required_facts",
        "fact_to_his",
        "unresolved_facts",
    }
    missing_keys = sorted(expected_keys.difference(trace))
    unexpected_keys = sorted(set(trace).difference(expected_keys))
    if missing_keys or unexpected_keys:
        errors.append(
            "REQ2HIS requirement fidelity: requirement_trace keys do not match contract; "
            f"missing={missing_keys}, unexpected={unexpected_keys}"
        )

    if trace.get("requirement_id") != expected_trace["requirement_id"]:
        errors.append(
            "REQ2HIS requirement fidelity: requirement_trace.requirement_id does not match "
            "the shared Requirement Envelope"
        )

    expected_facts = expected_trace["required_facts"]
    required_facts = trace.get("required_facts")
    if not isinstance(required_facts, dict):
        errors.append(
            "REQ2HIS requirement fidelity: requirement_trace.required_facts must be an object"
        )
    else:
        _validate_required_facts(required_facts, expected_facts, errors)

    fact_to_his = trace.get("fact_to_his")
    if not isinstance(fact_to_his, dict):
        errors.append(
            "REQ2HIS requirement fidelity: requirement_trace.fact_to_his must be an object"
        )
    else:
        _validate_fact_to_his(fact_to_his, expected_facts, payload, errors)

    unresolved_facts = trace.get("unresolved_facts")
    if unresolved_facts != []:
        errors.append(
            "REQ2HIS requirement fidelity: requirement_trace.unresolved_facts must be an empty list"
        )

    return SystemHisReqFidelityResult(
        passed=not errors,
        errors=errors,
        metrics=_metrics_from_errors(errors),
    )


def build_deterministic_requirement_trace(
    request: ProjectRequest,
    payload: dict[str, Any],
    platform: PlatformProfile,
) -> dict[str, Any]:
    """Build trace pointers only when existing payload values preserve each fact."""

    trace = build_request_requirement_envelope(request, platform).requirement_trace_template()
    mappings: dict[str, list[str]] = {}
    candidates = [
        (pointer, value, tokens)
        for pointer, value, tokens in _semantic_pointer_candidates(payload)
        if tokens[:2] != ("intent", "requirement_trace")
    ]
    for key, fact in trace["required_facts"].items():
        structurally_valid = [
            (pointer, value, tokens)
            for pointer, value, tokens in candidates
            if _pointer_matches_required_fact(key, tokens)
        ]
        selected: list[str] = []
        for pointer, value, tokens in structurally_valid:
            if _mapped_values_preserve_required_fact(
                key,
                fact["value"],
                [(value, tokens)],
            ):
                selected = [pointer]
                break
        if not selected and structurally_valid:
            resolved = [(value, tokens) for _pointer, value, tokens in structurally_valid]
            if _mapped_values_preserve_required_fact(key, fact["value"], resolved):
                selected = [pointer for pointer, _value, _tokens in structurally_valid]
        mappings[key] = selected
    trace["fact_to_his"] = mappings
    trace["unresolved_facts"] = [key for key, pointers in mappings.items() if not pointers]
    return trace


def _semantic_pointer_candidates(
    value: Any,
    tokens: tuple[str, ...] = (),
) -> list[tuple[str, Any, tuple[str, ...]]]:
    items: list[tuple[str, Any, tuple[str, ...]]] = []
    if tokens:
        pointer = "/" + "/".join(_json_pointer_escape(token) for token in tokens)
        items.append((pointer, value, tokens))
    if isinstance(value, dict):
        for key, child in value.items():
            items.extend(_semantic_pointer_candidates(child, (*tokens, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(_semantic_pointer_candidates(child, (*tokens, str(index))))
    return items


def _json_pointer_escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _merge_fidelity_results(
    trace_result: SystemHisReqFidelityResult,
    family_result: SystemHisReqFidelityResult,
) -> SystemHisReqFidelityResult:
    metrics: dict[str, dict[str, Any]] = {}
    for key in FIDELITY_METRIC_KEYS:
        trace_metric = trace_result.metrics.get(key, {})
        family_metric = family_result.metrics.get(key, {})
        statuses = {trace_metric.get("status"), family_metric.get("status")}
        status = "fail" if "fail" in statuses else "pass" if "pass" in statuses else "not_applicable"
        metrics[key] = {
            "status": status,
            "errors": [
                *list(trace_metric.get("errors", [])),
                *list(family_metric.get("errors", [])),
            ],
        }
    return SystemHisReqFidelityResult(
        passed=trace_result.passed and family_result.passed,
        errors=[*trace_result.errors, *family_result.errors],
        warnings=[*trace_result.warnings, *family_result.warnings],
        metrics=metrics,
    )


def _validate_required_facts(
    actual: dict[str, Any],
    expected: dict[str, Any],
    errors: list[str],
) -> None:
    for key in sorted(set(expected).difference(actual)):
        errors.append(
            "REQ2HIS requirement fidelity: requirement_trace.required_facts "
            f"missing required fact '{key}'"
        )
    for key in sorted(set(actual).difference(expected)):
        errors.append(
            "REQ2HIS requirement fidelity: requirement_trace.required_facts "
            f"has unexpected fact '{key}'"
        )
    for key in sorted(set(actual).intersection(expected)):
        if actual[key] != expected[key]:
            errors.append(
                "REQ2HIS requirement fidelity: requirement_trace.required_facts "
                f"fact '{key}' does not match the shared Requirement Envelope"
            )


def _validate_fact_to_his(
    actual: dict[str, Any],
    expected_facts: dict[str, Any],
    payload: dict[str, Any],
    errors: list[str],
) -> None:
    for key in sorted(set(expected_facts).difference(actual)):
        errors.append(
            "REQ2HIS requirement fidelity: requirement_trace.fact_to_his "
            f"missing required fact '{key}'"
        )
    for key in sorted(set(actual).difference(expected_facts)):
        errors.append(
            f"REQ2HIS requirement fidelity: requirement_trace.fact_to_his has unexpected fact '{key}'"
        )
    for key in sorted(set(actual).intersection(expected_facts)):
        pointers = actual[key]
        if not isinstance(pointers, list) or not pointers:
            errors.append(
                "REQ2HIS requirement fidelity: requirement_trace.fact_to_his "
                f"fact '{key}' must have a non-empty JSON Pointer list"
            )
            continue
        resolved_values: list[tuple[Any, tuple[str, ...]]] = []
        for pointer in pointers:
            if not isinstance(pointer, str):
                errors.append(
                    "REQ2HIS requirement fidelity: requirement_trace.fact_to_his "
                    f"fact '{key}' contains a non-string JSON Pointer"
                )
                continue
            try:
                resolved_value, tokens = _resolve_json_pointer(payload, pointer)
            except ValueError as exc:
                errors.append(
                    "REQ2HIS requirement fidelity: requirement_trace.fact_to_his "
                    f"JSON Pointer '{pointer}' for fact '{key}' does not resolve: {exc}"
                )
                continue
            if tokens[:2] == ("intent", "requirement_trace"):
                errors.append(
                    "REQ2HIS requirement fidelity: requirement_trace.fact_to_his "
                    f"JSON Pointer '{pointer}' for fact '{key}' cannot point into "
                    "requirement_trace"
                )
            elif not _pointer_matches_required_fact(key, tokens):
                errors.append(
                    "REQ2HIS requirement fidelity: requirement_trace.fact_to_his "
                    f"JSON Pointer '{pointer}' does not structurally represent fact '{key}'"
                )
            else:
                resolved_values.append((resolved_value, tokens))
        expected_value = expected_facts[key].get("value")
        if resolved_values and not _mapped_values_preserve_required_fact(
            key,
            expected_value,
            resolved_values,
        ):
            errors.append(
                "REQ2HIS requirement fidelity: requirement_trace.fact_to_his "
                f"mapped values do not preserve required fact '{key}'"
            )


def _pointer_matches_required_fact(key: str, tokens: tuple[str, ...]) -> bool:
    if not tokens:
        return False
    root = tokens[0]
    if key == "data_width_bits":
        return root in {"top", "components", "instances"} and any(
            token in {"width", "parameter", "parameters", "parameter_values"}
            for token in tokens[1:]
        )
    if key in {"clock_frequencies_hz", "clock_domain_count"}:
        return tokens[:2] == ("top", "clocks") or root == "timing"
    if key == "reset_polarity":
        return tokens[:2] == ("top", "resets")
    if key == "interface_protocols":
        return tokens[:2] in {("top", "ports"), ("top", "interfaces")} or root == "data_flow"
    if key == "functional_capabilities":
        return root in {
            "components",
            "instances",
            "data_flow",
            "control_flow",
            "state",
            "verification",
        }
    if key == "declared_task_type":
        return tokens in {("task_type",), ("intent", "declared_task_type")} or tokens[:2] == ("intent", "design_goal") or root in {
            "components",
            "instances",
        }
    if key == "acceptance_criteria":
        return root == "verification"
    if key == "target_platform":
        return root in {"intent", "artifacts", "resources"} and any(
            marker in _normalize_semantic_text(token)
            for token in tokens[1:]
            for marker in (
                "target",
                "platform",
                "device",
                "part",
                "board",
                "vendor",
                "family",
                "toolchain",
            )
        )
    if key in {"numeric_representation", "latency_cycles", "throughput_constraint"}:
        return root in {"components", "data_flow", "timing", "verification"}
    if key == "cdc_policy":
        return tokens[:2] == ("top", "clocks") or root in {
            "components",
            "instances",
            "data_flow",
        }
    if key in {"memory_depth", "memory_access_contract"}:
        return root in {"state", "components", "instances", "data_flow", "resources"}
    if key in {
        "adc_interface_contract",
        "dma_transfer_contract",
        "pcie_endpoint_contract",
    }:
        return tokens[:2] in {("top", "ports"), ("top", "interfaces")} or root in {
            "components",
            "instances",
            "data_flow",
            "control_flow",
            "verification",
        }
    return False


_FUNCTIONAL_CAPABILITY_VALUE_MARKERS = {
    "adc_interface": ("adc", "adc_interface"),
    "clock_domain_crossing": (
        "cdc",
        "clock_domain_crossing",
        "dual_clock",
        "async_fifo",
    ),
    "dma": ("dma",),
    "external_memory": ("external_memory", "ddr", "hbm", "sdram"),
    "on_chip_memory": ("on_chip_memory", "bram", "sram"),
    "pcie": ("pcie", "pci_e"),
    "axi_stream": ("axi_stream", "axi4_stream", "axis"),
    "spi": ("spi",),
    "i2c": ("i2c", "iic"),
    "uart": ("uart",),
    "streaming": ("stream", "streaming", "valid_ready"),
    "fifo": ("fifo",),
    "dsp": ("dsp", "fir", "fft", "mac", "matched_filter", "multiply_accumulate"),
    "image_pipeline": ("image_pipeline", "image", "pixel", "sobel", "convolution"),
    "state_machine": ("state_machine", "fsm"),
    "counter": ("counter",),
}

_PROTOCOL_VALUE_MARKERS = {
    "axi_stream": ("axi_stream", "axi4_stream", "axis"),
    "pcie": ("pcie", "pci_e"),
    "spi": ("spi",),
    "i2c": ("i2c", "iic"),
    "uart": ("uart",),
    "valid_ready": ("valid_ready",),
}


def _mapped_values_preserve_required_fact(
    key: str,
    expected: Any,
    resolved_values: list[tuple[Any, tuple[str, ...]]],
) -> bool:
    if key == "data_width_bits":
        expected_widths = expected if isinstance(expected, list) else [expected]
        actual_widths = [
            scalar
            for value, _tokens in resolved_values
            for scalar in _scalar_values(value)
        ]
        return all(
            any(widths_equivalent(expected_width, actual_width) for actual_width in actual_widths)
            for expected_width in expected_widths
        )

    if key == "clock_frequencies_hz":
        expected_frequencies = expected if isinstance(expected, list) else [expected]
        actual_frequencies = [
            frequency
            for value, tokens in resolved_values
            for frequency in _frequency_hz_values(value, tokens[-1] if tokens else "")
        ]
        return all(
            any(_numbers_equal(expected_frequency, actual_frequency) for actual_frequency in actual_frequencies)
            for expected_frequency in expected_frequencies
        )

    if key == "clock_domain_count":
        actual_counts: list[int] = []
        for value, tokens in resolved_values:
            if tokens[:2] == ("top", "clocks") and isinstance(value, list):
                actual_counts.append(len(value))
            elif tokens and "domain_count" in _normalize_semantic_text(tokens[-1]):
                if isinstance(value, int) and not isinstance(value, bool):
                    actual_counts.append(value)
        return any(_numbers_equal(expected, count) for count in actual_counts)

    if key == "reset_polarity":
        expected_polarity = _canonical_reset_polarity(expected)
        return any(
            _canonical_reset_polarity(value) == expected_polarity
            for resolved, _tokens in resolved_values
            for value in _scalar_values(resolved)
            if isinstance(value, str)
        )

    if key == "interface_protocols":
        return _all_semantic_values_present(
            expected,
            resolved_values,
            _PROTOCOL_VALUE_MARKERS,
        )

    if key == "functional_capabilities":
        return _all_semantic_values_present(
            expected,
            resolved_values,
            _FUNCTIONAL_CAPABILITY_VALUE_MARKERS,
        )

    if key == "declared_task_type":
        return _semantic_value_present(expected, resolved_values)

    if key == "target_platform":
        return _normalized_value_present(expected, resolved_values)

    if key == "numeric_representation":
        return _semantic_value_present(expected, resolved_values)

    if key == "latency_cycles":
        return _field_number_present(expected, resolved_values, ("latency",))

    if key == "throughput_constraint":
        return _throughput_present(expected, resolved_values)

    if key == "acceptance_criteria":
        return _acceptance_criteria_present(expected, resolved_values)

    if key == "memory_depth":
        return _field_number_present(expected, resolved_values, ("depth",))

    if key in {"cdc_policy", "memory_access_contract", "adc_interface_contract"}:
        return _semantic_value_present(expected, resolved_values)

    if key == "dma_transfer_contract":
        if _semantic_value_present(expected, resolved_values):
            return True
        match = re.fullmatch(r"burst_length_(\d+)", str(expected))
        return bool(match) and _field_number_present(
            int(match.group(1)),
            resolved_values,
            ("burst_length",),
        )

    if key == "pcie_endpoint_contract":
        if _semantic_value_present(expected, resolved_values):
            return True
        match = re.fullmatch(r"gen(\d+)_x(\d+)", str(expected))
        return bool(match) and (
            _field_number_present(
                int(match.group(1)),
                resolved_values,
                ("gen", "generation"),
            )
            and _field_number_present(
                int(match.group(2)),
                resolved_values,
                ("lane", "lanes"),
            )
        )

    return False


def _all_semantic_values_present(
    expected: Any,
    resolved_values: list[tuple[Any, tuple[str, ...]]],
    marker_map: dict[str, tuple[str, ...]],
) -> bool:
    expected_values = expected if isinstance(expected, list) else [expected]
    actual_texts = [
        value
        for resolved, _tokens in resolved_values
        for value in _scalar_values(resolved)
        if isinstance(value, str)
    ]
    return all(
        any(
            _semantic_marker_matches(text, marker)
            for text in actual_texts
            for marker in marker_map.get(str(expected_value), (str(expected_value),))
        )
        for expected_value in expected_values
    )


def _semantic_value_present(
    expected: Any,
    resolved_values: list[tuple[Any, tuple[str, ...]]],
) -> bool:
    return any(
        _semantic_marker_matches(value, str(expected))
        for resolved, _tokens in resolved_values
        for value in _scalar_values(resolved)
        if isinstance(value, str)
    )


def _normalized_value_present(
    expected: Any,
    resolved_values: list[tuple[Any, tuple[str, ...]]],
) -> bool:
    normalized_expected = _normalize_semantic_text(str(expected))
    return any(
        _normalize_semantic_text(value) == normalized_expected
        for resolved, _tokens in resolved_values
        for value in _scalar_values(resolved)
        if isinstance(value, str)
    )


def _field_number_present(
    expected: Any,
    resolved_values: list[tuple[Any, tuple[str, ...]]],
    field_markers: tuple[str, ...],
) -> bool:
    actual_values = [
        number
        for value, tokens in resolved_values
        for number in _field_number_values(
            value,
            tokens[-1] if tokens else "",
            field_markers,
        )
    ]
    return any(_numbers_equal(expected, actual) for actual in actual_values)


def _field_number_values(
    value: Any,
    field_name: str,
    field_markers: tuple[str, ...],
) -> list[float]:
    if isinstance(value, dict):
        return [
            number
            for key, item in value.items()
            for number in _field_number_values(item, str(key), field_markers)
        ]
    if isinstance(value, list):
        return [
            number
            for item in value
            for number in _field_number_values(item, field_name, field_markers)
        ]
    normalized_field = _normalize_semantic_text(field_name)
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and any(marker in normalized_field for marker in field_markers)
    ):
        return [float(value)]
    return []


def _throughput_present(
    expected: Any,
    resolved_values: list[tuple[Any, tuple[str, ...]]],
) -> bool:
    if _semantic_value_present(expected, resolved_values):
        return True
    if str(expected) != "one_per_cycle":
        return False
    if any(
        _semantic_marker_matches(value, marker)
        for resolved, _tokens in resolved_values
        for value in _scalar_values(resolved)
        if isinstance(value, str)
        for marker in (
            "one_transfer_per_cycle",
            "one_sample_per_cycle",
            "one_word_per_cycle",
            "1_per_cycle",
        )
    ):
        return True
    return _field_number_present(
        1,
        resolved_values,
        ("initiation_interval",),
    )


def _acceptance_criteria_present(
    expected: Any,
    resolved_values: list[tuple[Any, tuple[str, ...]]],
) -> bool:
    actual_text = " ".join(
        value
        for resolved, _tokens in resolved_values
        for value in _scalar_values(resolved)
        if isinstance(value, str)
    )
    if _semantic_marker_matches(actual_text, str(expected)):
        return True

    actual_terms = _acceptance_terms(actual_text)
    expected_text = str(expected)
    if expected_text == (
        "independent evaluator must verify every explicit functional and protocol clause"
    ):
        required_roots = (
            any(term.startswith("independent") for term in actual_terms),
            any(term.startswith("evaluator") for term in actual_terms),
            any(term.startswith(("verif", "check", "assert")) for term in actual_terms),
        )
        boilerplate = {
            "independent",
            "evaluator",
            "verify",
            "verifies",
            "verification",
            "check",
            "checks",
            "assert",
            "asserts",
            "behavior",
            "design",
            "every",
            "explicit",
            "functional",
            "protocol",
            "clause",
        }
        return all(required_roots) and bool(actual_terms.difference(boilerplate))

    expected_terms = _acceptance_terms(expected_text)
    if not expected_terms:
        return False
    expected_numbers = {term for term in expected_terms if term.isdigit()}
    overlap = expected_terms.intersection(actual_terms)
    return (
        expected_numbers.issubset(actual_terms)
        and len(overlap) >= max(1, (len(expected_terms) + 1) // 2)
    )


def _acceptance_terms(value: str) -> set[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "must",
        "of",
        "on",
        "or",
        "the",
        "to",
        "when",
        "with",
    }
    return {
        term
        for term in _normalize_semantic_text(value).split("_")
        if term and term not in stop_words
    }


def _semantic_marker_matches(value: str, marker: str) -> bool:
    normalized_value = _normalize_semantic_text(value)
    normalized_marker = _normalize_semantic_text(marker)
    return bool(normalized_marker) and (
        normalized_value == normalized_marker
        or f"_{normalized_marker}_" in f"_{normalized_value}_"
    )


def _normalize_semantic_text(value: str) -> str:
    return re.sub(r"[^\w]+", "_", value.casefold()).strip("_")


def _scalar_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        return [scalar for item in value.values() for scalar in _scalar_values(item)]
    if isinstance(value, list):
        return [scalar for item in value for scalar in _scalar_values(item)]
    return [value]


def _frequency_hz_values(value: Any, field_name: str) -> list[float]:
    if isinstance(value, dict):
        return [
            frequency
            for key, item in value.items()
            for frequency in _frequency_hz_values(item, str(key))
        ]
    if isinstance(value, list):
        return [
            frequency
            for item in value
            for frequency in _frequency_hz_values(item, field_name)
        ]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return []
    normalized_field = _normalize_semantic_text(field_name)
    if "ghz" in normalized_field:
        return [float(value) * 1_000_000_000]
    if "mhz" in normalized_field:
        return [float(value) * 1_000_000]
    if "khz" in normalized_field:
        return [float(value) * 1_000]
    if normalized_field.endswith("hz"):
        return [float(value)]
    return []


def _numbers_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return False
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return False
    return abs(float(left) - float(right)) <= max(1e-6, abs(float(left)) * 1e-9)


def _canonical_reset_polarity(value: Any) -> str:
    normalized = _normalize_semantic_text(str(value))
    return {
        "low": "active_low",
        "active_low": "active_low",
        "high": "active_high",
        "active_high": "active_high",
    }.get(normalized, normalized)


def _resolve_json_pointer(
    document: Any,
    pointer: str,
) -> tuple[Any, tuple[str, ...]]:
    if not pointer.startswith("/"):
        raise ValueError("pointer must start with '/'")
    tokens = tuple(_decode_json_pointer_token(token) for token in pointer[1:].split("/"))
    current = document
    for token in tokens:
        if isinstance(current, dict):
            if token not in current:
                raise ValueError(f"object key '{token}' is missing")
            current = current[token]
            continue
        if isinstance(current, list):
            if token == "0":
                index = 0
            elif token.isdigit() and not token.startswith("0"):
                index = int(token)
            else:
                raise ValueError(f"array index '{token}' is invalid")
            if index >= len(current):
                raise ValueError(f"array index '{token}' is out of range")
            current = current[index]
            continue
        raise ValueError(f"cannot traverse through scalar at token '{token}'")
    return current, tokens


def _decode_json_pointer_token(token: str) -> str:
    index = 0
    while index < len(token):
        if token[index] != "~":
            index += 1
            continue
        if index + 1 >= len(token) or token[index + 1] not in {"0", "1"}:
            raise ValueError(f"JSON Pointer token '{token}' has an invalid escape")
        index += 2
    return token.replace("~1", "/").replace("~0", "~")


def _not_applicable_metrics() -> dict[str, dict[str, Any]]:
    return {key: {"status": "not_applicable", "errors": []} for key in FIDELITY_METRIC_KEYS}


def _metrics_from_errors(errors: list[str]) -> dict[str, dict[str, Any]]:
    metrics = _not_applicable_metrics()
    for key in (
        "interface_extraction",
        "clock_reset_fidelity",
        "parameter_fidelity",
        "behavior_intent_fidelity",
        "verification_intent_fidelity",
        "constraint_fidelity",
    ):
        metrics[key]["status"] = "pass"

    for error in errors:
        if "reset " in error or "clock " in error:
            metrics["clock_reset_fidelity"]["status"] = "fail"
            metrics["clock_reset_fidelity"]["errors"].append(error)
        elif "verification." in error:
            metrics["verification_intent_fidelity"]["status"] = "fail"
            metrics["verification_intent_fidelity"]["errors"].append(error)
        elif "timing." in error or "resource" in error:
            metrics["constraint_fidelity"]["status"] = "fail"
            metrics["constraint_fidelity"]["errors"].append(error)
        elif "top." in error:
            if "width must match" in error:
                metrics["parameter_fidelity"]["status"] = "fail"
                metrics["parameter_fidelity"]["errors"].append(error)
            else:
                metrics["interface_extraction"]["status"] = "fail"
                metrics["interface_extraction"]["errors"].append(error)
        elif "requires component" in error or "requires " in error and "instance(s)" in error:
            metrics["behavior_intent_fidelity"]["status"] = "fail"
            metrics["behavior_intent_fidelity"]["errors"].append(error)
        else:
            metrics["interface_extraction"]["status"] = "fail"
            metrics["interface_extraction"]["errors"].append(error)

    return metrics


def _validate_components(request: ProjectRequest, payload: dict[str, Any], errors: list[str]) -> None:
    components = payload.get("components", [])
    component_names = {
        str(component.get("name", "")).strip()
        for component in components
        if isinstance(component, dict)
    }
    for component_name in _required_components(request.task_type):
        if component_name not in component_names:
            errors.append(f"REQ2HIS fidelity: {request.task_type} requires component '{component_name}'")


def _validate_component_ports(request: ProjectRequest, payload: dict[str, Any], errors: list[str]) -> None:
    expected_components = _expected_component_ports(request)
    if not expected_components:
        return
    actual_components = {
        str(component.get("name", "")).strip(): component
        for component in payload.get("components", [])
        if isinstance(component, dict)
    }
    for component_name, expected_ports in expected_components.items():
        component = actual_components.get(component_name)
        if not isinstance(component, dict):
            continue
        actual_ports = {
            str(port.get("name", "")).strip(): port
            for port in component.get("ports", [])
            if isinstance(port, dict) and str(port.get("name", "")).strip()
        }
        for port_name, expected in expected_ports.items():
            port = actual_ports.get(port_name)
            if port is None:
                errors.append(f"REQ2HIS fidelity: component {component_name} requires port '{port_name}'")
                continue
            expected_direction = expected.get("direction")
            actual_direction = _port_direction(port)
            if expected_direction is not None and actual_direction and actual_direction != expected_direction:
                errors.append(
                    f"REQ2HIS fidelity: component {component_name}.{port_name} direction must be {expected_direction}"
                )
    _validate_data_flow_component_ports(payload, expected_components, errors)


def _validate_data_flow_component_ports(
    payload: dict[str, Any],
    expected_components: dict[str, dict[str, dict[str, Any]]],
    errors: list[str],
) -> None:
    instance_components = {
        str(instance.get("name", "")).strip(): str(instance.get("component", "")).strip()
        for instance in payload.get("instances", [])
        if isinstance(instance, dict)
    }
    for flow in payload.get("data_flow", []):
        if not isinstance(flow, dict):
            continue
        for endpoint in flow.get("path", []):
            if not isinstance(endpoint, str) or "." not in endpoint:
                continue
            owner, port_name = endpoint.split(".", 1)
            component_name = instance_components.get(owner)
            if component_name not in expected_components:
                continue
            if port_name not in expected_components[component_name]:
                errors.append(f"REQ2HIS fidelity: component {component_name} has unexpected port '{port_name}'")


def _validate_forbidden_component_alias_ports(payload: dict[str, Any], errors: list[str]) -> None:
    instance_components = {
        str(instance.get("name", "")).strip(): str(instance.get("component", "")).strip()
        for instance in payload.get("instances", [])
        if isinstance(instance, dict)
    }
    for flow in payload.get("data_flow", []):
        if not isinstance(flow, dict):
            continue
        for endpoint in flow.get("path", []):
            if not isinstance(endpoint, str) or "." not in endpoint:
                continue
            owner, port_name = endpoint.split(".", 1)
            component_name = instance_components.get(owner)
            if port_name in _FORBIDDEN_COMPONENT_ALIAS_PORTS.get(component_name, set()):
                errors.append(f"REQ2HIS fidelity: component {component_name} has unexpected port '{port_name}'")


def _expected_component_ports(request: ProjectRequest) -> dict[str, dict[str, dict[str, Any]]]:
    if request.task_type != "composed_stream_accumulator":
        return {}
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    project = ProjectGenerator().generate(request, platform)
    system_his = json.loads(project.files["system_his.json"])
    components = system_his.get("components", [])
    return {
        str(component.get("name", "")).strip(): {
            str(port.get("name", "")).strip(): {
                "direction": _port_direction(port),
            }
            for port in component.get("ports", [])
            if isinstance(port, dict) and str(port.get("name", "")).strip()
        }
        for component in components
        if isinstance(component, dict) and str(component.get("name", "")).strip()
    }


def _validate_instances(request: ProjectRequest, payload: dict[str, Any], errors: list[str]) -> None:
    instances = payload.get("instances", [])
    instance_components = Counter(
        str(instance.get("component", "")).strip()
        for instance in instances
        if isinstance(instance, dict)
    )
    required_counts = _required_instance_counts(request.task_type)
    for component_name, count in required_counts.items():
        if instance_components[component_name] < count:
            errors.append(
                f"REQ2HIS fidelity: {request.task_type} requires {count} instance(s) "
                f"of component '{component_name}'"
            )


def _required_components(task_type: str) -> list[str]:
    if task_type in COMPONENT_TOPOLOGIES:
        return list(COMPONENT_TOPOLOGIES[task_type]["submodules"])
    return list(_SUPPLEMENTAL_TASK_COMPONENTS.get(task_type, []))


def _required_instance_counts(task_type: str) -> Counter[str]:
    if task_type in COMPONENT_TOPOLOGIES:
        topology = COMPONENT_TOPOLOGIES[task_type]
        return Counter(
            str(node.get("component", "")).strip()
            for node in topology.get("nodes", [])
            if isinstance(node, dict)
        )
    return Counter(_SUPPLEMENTAL_TASK_COMPONENTS.get(task_type, []))


def _validate_top_ports(request: ProjectRequest, payload: dict[str, Any], errors: list[str]) -> None:
    top = payload.get("top", {})
    ports = top.get("ports", []) if isinstance(top, dict) else []
    ports_by_name = {
        str(port.get("name", "")).strip(): port
        for port in ports
        if isinstance(port, dict)
    }
    expected_ports = _TASK_TOP_PORTS.get(request.task_type, {})
    for port_name, expected in expected_ports.items():
        port = ports_by_name.get(port_name)
        if port is None:
            errors.append(f"REQ2HIS fidelity: {request.task_type} requires top port '{port_name}'")
            continue
        expected_direction = expected.get("direction")
        actual_direction = _port_direction(port)
        if expected_direction is not None and actual_direction and actual_direction != expected_direction:
            errors.append(
                f"REQ2HIS fidelity: top.{port_name} direction must be {expected_direction}"
            )
        if expected.get("width") == "request" and not widths_equivalent(port.get("width"), request.width):
            errors.append(
                f"REQ2HIS fidelity: top.{port_name} width must match requested width {request.width}"
            )


def _validate_clock_reset(payload: dict[str, Any], errors: list[str]) -> None:
    top = payload.get("top", {})
    if not isinstance(top, dict):
        return
    clocks = top.get("clocks", [])
    clock_names = {
        str(clock.get("name", "")).strip()
        for clock in clocks
        if isinstance(clock, dict)
    }
    if "clk" not in clock_names:
        errors.append("REQ2HIS fidelity: clock clk is required")
    resets = top.get("resets", [])
    reset_by_name = {
        str(reset.get("name", "")).strip(): reset
        for reset in resets
        if isinstance(reset, dict)
    }
    rst_n = reset_by_name.get("rst_n")
    if rst_n is None:
        errors.append("REQ2HIS fidelity: reset rst_n is required")
        return
    if str(rst_n.get("polarity", "")).strip() != "active_low":
        errors.append("REQ2HIS fidelity: reset rst_n polarity must be active_low")


def _validate_verification(payload: dict[str, Any], errors: list[str]) -> None:
    verification = payload.get("verification", {})
    if not isinstance(verification, dict):
        errors.append("REQ2HIS fidelity: verification must be an object")
        return
    if not str(verification.get("testbench", "")).strip():
        errors.append("REQ2HIS fidelity: verification.testbench is required")
    if not isinstance(verification.get("scenarios"), list):
        errors.append("REQ2HIS fidelity: verification.scenarios must be a list")
    if not str(verification.get("pass_condition", "")).strip():
        errors.append("REQ2HIS fidelity: verification.pass_condition is required")


def _validate_constraints(payload: dict[str, Any], errors: list[str]) -> None:
    timing = payload.get("timing", {})
    if not isinstance(timing, dict):
        errors.append("REQ2HIS fidelity: timing must be an object")
        return
    target_fmax = timing.get("target_fmax_mhz")
    if not isinstance(target_fmax, (int, float)) or isinstance(target_fmax, bool) or target_fmax <= 0:
        errors.append("REQ2HIS fidelity: timing.target_fmax_mhz must be positive")
    if not str(timing.get("primary_clock", "")).strip():
        errors.append("REQ2HIS fidelity: timing.primary_clock is required")


def _port_direction(port: dict[str, Any]) -> str:
    return str(port.get("direction", port.get("dir", ""))).strip()
