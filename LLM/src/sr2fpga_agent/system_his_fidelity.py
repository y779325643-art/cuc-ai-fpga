"""REQ-to-System-HIS fidelity checks for known synthetic tasks."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import COMPONENT_TOPOLOGIES, ProjectGenerator
from LLM.src.sr2fpga_agent.rtl_introspect import widths_equivalent


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
) -> SystemHisReqFidelityResult:
    """Check that a valid System-HIS still describes the requested synthetic task.

    This is intentionally narrower than the structural v1.2 checker. It catches
    wrong-but-coherent HIS objects for the frozen topology tasks while leaving
    legacy task types unblocked.
    """

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
