from copy import deepcopy
import json

import pytest

from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.requirement_envelope import build_request_requirement_envelope
from sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity


def test_unknown_requirement_trace_passes_generic_h3() -> None:
    request, platform, payload = _requirement_fixture()

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is True
    assert result.errors == []
    assert {metric["status"] for metric in result.metrics.values()} == {"pass"}


def test_requirement_trace_missing_functional_capabilities_fails() -> None:
    request, platform, payload = _requirement_fixture()
    trace = payload["intent"]["requirement_trace"]
    trace["required_facts"].pop("functional_capabilities")

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any(
        "missing required fact 'functional_capabilities'" in error
        for error in result.errors
    )


def test_requirement_trace_bad_json_pointer_fails() -> None:
    request, platform, payload = _requirement_fixture()
    trace = payload["intent"]["requirement_trace"]
    trace["fact_to_his"]["data_width_bits"] = ["/top/ports/99/width"]

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any("does not resolve" in error for error in result.errors)


def test_requirement_trace_unresolved_fact_fails() -> None:
    request, platform, payload = _requirement_fixture()
    trace = payload["intent"]["requirement_trace"]
    trace["unresolved_facts"] = ["data_width_bits"]

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any("unresolved_facts must be an empty list" in error for error in result.errors)


def test_trace_cannot_self_assert_every_fact_from_user_prompt() -> None:
    request, platform, payload = _requirement_fixture()
    trace = payload["intent"]["requirement_trace"]
    trace["fact_to_his"] = {
        key: ["/intent/user_prompt"]
        for key in trace["required_facts"]
    }

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any("does not structurally represent fact" in error for error in result.errors)


def test_functional_capabilities_cannot_map_to_user_prompt() -> None:
    request, platform, payload = _requirement_fixture()
    trace = payload["intent"]["requirement_trace"]
    trace["fact_to_his"]["functional_capabilities"] = ["/intent/user_prompt"]

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any(
        "does not structurally represent fact 'functional_capabilities'" in error
        for error in result.errors
    )


def test_declared_task_type_cannot_map_to_user_prompt() -> None:
    request, platform, payload = _requirement_fixture()
    trace = payload["intent"]["requirement_trace"]
    trace["fact_to_his"]["declared_task_type"] = ["/intent/user_prompt"]

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any(
        "does not structurally represent fact 'declared_task_type'" in error
        for error in result.errors
    )


@pytest.mark.parametrize(
    ("fact_key", "section", "field", "bad_value"),
    [
        ("data_width_bits", "top_port", "width", 999),
        ("clock_frequencies_hz", "clock", "target_fmax_mhz", 1),
        ("reset_polarity", "reset", "polarity", "active_high"),
        ("interface_protocols", "data_flow", "protocol", "wire"),
        ("functional_capabilities", "component", "semantic_kind", "counter"),
        ("declared_task_type", "intent", "design_goal", "implement a counter"),
        ("target_platform", "intent", "target_platform", "wrong_platform"),
    ],
)
def test_requirement_trace_rejects_wrong_mapped_value(
    fact_key: str,
    section: str,
    field: str,
    bad_value: object,
) -> None:
    request, platform, payload = _requirement_fixture()
    targets = {
        "top_port": payload["top"]["ports"][0],
        "clock": payload["top"]["clocks"][0],
        "reset": payload["top"]["resets"][0],
        "data_flow": payload["data_flow"][0],
        "component": payload["components"][0],
        "intent": payload["intent"],
    }
    targets[section][field] = bad_value

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any(
        f"mapped values do not preserve required fact '{fact_key}'" in error
        for error in result.errors
    )


def test_interface_protocol_can_map_to_top_interfaces() -> None:
    request, platform, payload = _requirement_fixture()
    payload["top"]["interfaces"] = [
        {"name": "input_stream", "protocol": "valid_ready"}
    ]
    payload["intent"]["requirement_trace"]["fact_to_his"]["interface_protocols"] = [
        "/top/interfaces/0/protocol"
    ]

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is True
    assert result.errors == []


def test_target_platform_cannot_map_to_user_prompt() -> None:
    request, platform, payload = _requirement_fixture()
    payload["intent"]["requirement_trace"]["fact_to_his"]["target_platform"] = [
        "/intent/user_prompt"
    ]

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any(
        "does not structurally represent fact 'target_platform'" in error
        for error in result.errors
    )


def test_extended_requirement_trace_passes_value_aware_h3() -> None:
    request, platform, payload = _extended_requirement_fixture()

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is True
    assert result.errors == []


@pytest.mark.parametrize(
    ("fact_key", "pointer", "bad_value"),
    [
        ("numeric_representation", "/components/0/numeric_representation", "signed"),
        ("latency_cycles", "/data_flow/0/timing/latency_cycles", 3),
        ("throughput_constraint", "/data_flow/0/timing/throughput", "one per four cycles"),
        ("acceptance_criteria", "/verification/pass_condition", "testbench compiles"),
        ("cdc_policy", "/components/0/cdc_policy", "async_fifo"),
        ("dma_transfer_contract", "/components/0/burst_length", 8),
        ("memory_depth", "/state/memories/0/depth", 512),
        ("memory_access_contract", "/state/memories/0/access", "single_port"),
        ("pcie_endpoint_contract", "/top/interfaces/0/generation", 3),
    ],
)
def test_requirement_trace_rejects_wrong_extended_fact_value(
    fact_key: str,
    pointer: str,
    bad_value: object,
) -> None:
    request, platform, payload = _extended_requirement_fixture()
    _set_json_pointer_value(payload, pointer, bad_value)

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any(
        f"mapped values do not preserve required fact '{fact_key}'" in error
        for error in result.errors
    )


def test_unknown_requirement_without_trace_fails_generic_h3() -> None:
    request = ProjectRequest(
        task_type="customer_packet_queue",
        width=8,
        project_name="customer_packet_queue",
        description="Build an 8-bit valid-ready FIFO.",
    )

    platform = PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )
    result = check_system_his_req_fidelity(request, {}, platform)

    assert result.passed is False
    assert any("requirement_trace must be an object" in error for error in result.errors)


def test_family_recipe_cannot_replace_the_generic_trace() -> None:
    request = ProjectRequest(
        task_type="composed_stream_accumulator",
        width=8,
        project_name="stream_accumulator",
    )
    platform = PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )
    project = ProjectGenerator().generate(request, platform)
    payload = json.loads(project.files["system_his.json"])
    payload["intent"].pop("requirement_trace")

    result = check_system_his_req_fidelity(request, payload, platform)

    assert result.passed is False
    assert any("requirement_trace must be an object" in error for error in result.errors)


def test_deterministic_trace_does_not_claim_an_unimplemented_protocol() -> None:
    request = ProjectRequest(
        task_type="counter",
        width=8,
        project_name="wishbone_counter",
        description="Build an 8-bit counter with a Wishbone bus.",
    )
    platform = PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )
    project = ProjectGenerator().generate(request, platform)
    payload = json.loads(project.files["system_his.json"])

    assert payload["top"]["interfaces"] == []
    assert "interface_protocols" in payload["intent"]["requirement_trace"][
        "unresolved_facts"
    ]
    assert check_system_his_req_fidelity(request, payload, platform).passed is False


def _requirement_fixture() -> tuple[ProjectRequest, PlatformProfile, dict]:
    request = ProjectRequest(
        task_type="customer_packet_queue",
        width=8,
        project_name="customer_packet_queue",
        description="Build an 8-bit valid-ready FIFO.",
    )
    platform = PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )
    trace = deepcopy(
        build_request_requirement_envelope(
            request,
            platform,
        ).requirement_trace_template()
    )
    pointers = {
        "data_width_bits": ["/top/ports/0/width"],
        "clock_frequencies_hz": ["/top/clocks/0/target_fmax_mhz"],
        "reset_polarity": ["/top/resets/0/polarity"],
        "interface_protocols": ["/data_flow/0/protocol"],
        "functional_capabilities": ["/components/0/semantic_kind"],
        "declared_task_type": ["/intent/design_goal"],
        "target_platform": ["/intent/target_platform"],
        "acceptance_criteria": ["/verification/pass_condition"],
    }
    assert set(trace["required_facts"]) == set(pointers)
    trace["fact_to_his"] = pointers
    trace["unresolved_facts"] = []
    payload = {
        "intent": {
            "user_prompt": request.description,
            "design_goal": "implement customer_packet_queue as a FIFO",
            "target_platform": platform.name,
            "requirement_trace": trace,
        },
        "top": {
            "ports": [{"name": "data", "width": request.width}],
            "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
            "resets": [{"name": "rst_n", "polarity": "active_low"}],
        },
        "components": [
            {
                "name": "fifo_core",
                "semantic_kind": "fifo",
            }
        ],
        "data_flow": [{"name": "input", "protocol": "valid_ready"}],
        "verification": {
            "pass_condition": (
                "independent evaluator verifies FIFO ordering and valid-ready behavior"
            )
        },
    }
    return request, platform, payload


def _extended_requirement_fixture() -> tuple[ProjectRequest, PlatformProfile, dict]:
    request = ProjectRequest(
        task_type="customer_dma_capture",
        width=16,
        project_name="customer_dma_capture",
        description=(
            "Build a 16-bit unsigned dual-clock streaming DMA to dual-port DDR depth 1024 "
            "with a two-flop synchronizer, burst length 16, PCIe Gen4 x8, latency 2 cycles, "
            "and one sample per cycle. Acceptance: every DMA burst reaches PCIe in order "
            "without loss"
        ),
    )
    platform = PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )
    trace = deepcopy(
        build_request_requirement_envelope(
            request,
            platform,
        ).requirement_trace_template()
    )
    pointers = {
        "declared_task_type": ["/intent/design_goal"],
        "functional_capabilities": ["/components/0/intent"],
        "data_width_bits": ["/top/ports/0/width"],
        "clock_frequencies_hz": ["/top/clocks/0/target_fmax_mhz"],
        "clock_domain_count": ["/top/clocks"],
        "reset_polarity": ["/top/resets/0/polarity"],
        "numeric_representation": ["/components/0/numeric_representation"],
        "interface_protocols": ["/top/interfaces/0/protocol"],
        "latency_cycles": ["/data_flow/0/timing/latency_cycles"],
        "throughput_constraint": ["/data_flow/0/timing/throughput"],
        "target_platform": ["/intent/target_platform"],
        "acceptance_criteria": ["/verification/pass_condition"],
        "cdc_policy": ["/components/0/cdc_policy"],
        "dma_transfer_contract": ["/components/0/burst_length"],
        "memory_depth": ["/state/memories/0/depth"],
        "memory_access_contract": ["/state/memories/0/access"],
        "pcie_endpoint_contract": [
            "/top/interfaces/0/generation",
            "/top/interfaces/0/lanes",
        ],
    }
    assert set(trace["required_facts"]) == set(pointers)
    trace["fact_to_his"] = pointers
    payload = {
        "intent": {
            "user_prompt": request.description,
            "design_goal": "implement customer_dma_capture",
            "target_platform": platform.name,
            "requirement_trace": trace,
        },
        "top": {
            "ports": [{"name": "data", "width": request.width}],
            "clocks": [
                {"name": "source_clk", "target_fmax_mhz": 100},
                {"name": "destination_clk", "target_fmax_mhz": 100},
            ],
            "resets": [{"name": "rst_n", "polarity": "active_low"}],
            "interfaces": [
                {"name": "host", "protocol": "pcie", "generation": 4, "lanes": 8}
            ],
        },
        "state": {
            "memories": [{"name": "capture", "depth": 1024, "access": "dual_port"}]
        },
        "components": [
            {
                "name": "capture_core",
                "semantic_kind": "rtl_component",
                "intent": (
                    "dual-clock streaming DMA to external DDR memory over PCIe"
                ),
                "numeric_representation": "unsigned",
                "cdc_policy": "two_flop_synchronizer",
                "burst_length": 16,
            }
        ],
        "data_flow": [
            {
                "name": "capture_stream",
                "protocol": "valid_ready",
                "timing": {
                    "latency_cycles": 2,
                    "initiation_interval": 1,
                    "throughput": "one sample per cycle",
                },
            }
        ],
        "verification": {
            "pass_condition": "every DMA burst reaches PCIe in order without loss"
        },
    }
    return request, platform, payload


def _set_json_pointer_value(payload: dict, pointer: str, value: object) -> None:
    tokens = pointer.lstrip("/").split("/")
    current: object = payload
    for token in tokens[:-1]:
        if isinstance(current, list):
            current = current[int(token)]
        else:
            assert isinstance(current, dict)
            current = current[token]
    if isinstance(current, list):
        current[int(tokens[-1])] = value
    else:
        assert isinstance(current, dict)
        current[tokens[-1]] = value
