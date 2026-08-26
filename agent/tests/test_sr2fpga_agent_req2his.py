import copy
import unittest
from unittest.mock import patch

from sr2fpga_agent.generation.req2his import (
    RequirementCapabilityGapError,
    RequirementClarificationRequired,
    SystemHisGenerator,
    _prepare_requirement,
    _requirement_capability_gaps,
)
from sr2fpga_agent.family_recipe import recipe_task_type
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.prompts import (
    _system_his_v12_messages,
    _with_system_his_retry_feedback,
)
from sr2fpga_agent.requirement_envelope import build_request_requirement_envelope
from sr2fpga_agent.system_his_capabilities import load_system_his_backend_capabilities


class FakeStreamingClient:
    def __init__(self, response: str = "{}") -> None:
        self.response = response
        self.calls = 0
        self.messages_history: list[list[dict[str, str]]] = []

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        self.calls += 1
        self.messages_history.append(copy.deepcopy(messages))
        return self.response


class UnifiedReq2HisTests(unittest.TestCase):
    def test_ready_requirement_calls_client_once_and_injects_trace_with_automatic_recipe(self) -> None:
        request = _alu_request()
        platform = _platform()
        client = FakeStreamingClient()

        with patch(
            "sr2fpga_agent.generation.req2his.validate_system_his_candidate",
            return_value={"schema_version": "system-his-v1.2"},
        ) as validate:
            result = SystemHisGenerator(client, max_attempts=1).generate(request, platform)

        self.assertEqual(result["schema_version"], "system-his-v1.2")
        self.assertEqual(client.calls, 1)
        validate.assert_called_once_with(request, "{}", platform=platform)
        prompt = client.messages_history[0][-1]["content"]
        self.assertIn("Requirement envelope", prompt)
        self.assertIn('"requirement_trace"', prompt)
        self.assertIn('"required_facts"', prompt)
        self.assertIn('"fact_to_his"', prompt)
        self.assertIn("RFC 6901", prompt)
        self.assertIn("width facts to top/component/instance widths", prompt)
        self.assertIn("Required architecture for alu_control_unit", prompt)

    def test_clarification_stops_before_client_with_at_most_three_questions(self) -> None:
        request = ProjectRequest(
            task_type="customer_sensor_fusion",
            width=16,
            project_name="sensor_fusion",
            description="Create a sensor fusion engine.",
        )
        client = FakeStreamingClient()

        with self.assertRaises(RequirementClarificationRequired) as caught:
            SystemHisGenerator(client).generate(request, _platform())

        self.assertEqual(client.calls, 0)
        self.assertLessEqual(len(caught.exception.questions), 3)
        self.assertIn("functional_decomposition", caught.exception.ambiguity_keys)
        self.assertIn("requirement_clarification_required", str(caught.exception))

    def test_capability_gap_stops_axi_stream_before_client(self) -> None:
        request = ProjectRequest(
            task_type="customer_axis_pipe",
            width=32,
            project_name="axis_pipe",
            description="Build a 32-bit AXI-Stream FIFO.",
        )
        client = FakeStreamingClient()

        with self.assertRaises(RequirementCapabilityGapError) as caught:
            SystemHisGenerator(client).generate(request, _platform())

        self.assertEqual(client.calls, 0)
        self.assertIn("axi_stream", caught.exception.capability_gaps)
        self.assertIn("capability_gap/needs_adapter", str(caught.exception))

    def test_unsupported_adc_requests_details_before_resolving_capability_gap(self) -> None:
        request = ProjectRequest(
            task_type="customer_adc_capture",
            width=12,
            project_name="adc_capture",
            description="Build a 12-bit ADC capture interface.",
        )
        client = FakeStreamingClient()

        with self.assertRaises(RequirementClarificationRequired) as caught:
            SystemHisGenerator(client).generate(request, _platform())

        self.assertEqual(client.calls, 0)
        self.assertIn("adc_interface_contract", caught.exception.ambiguity_keys)

    def test_capability_gap_stops_opaque_wishbone_before_client(self) -> None:
        request = ProjectRequest(
            task_type="counter",
            width=8,
            project_name="wishbone_counter",
            description="Build an 8-bit counter with a Wishbone bus.",
        )
        client = FakeStreamingClient()

        with self.assertRaises(RequirementCapabilityGapError) as caught:
            SystemHisGenerator(client).generate(request, _platform())

        self.assertEqual(client.calls, 0)
        self.assertEqual(caught.exception.capability_gaps, ("wishbone",))

    def test_vague_interface_stops_for_clarification_before_client(self) -> None:
        request = ProjectRequest(
            task_type="counter",
            width=8,
            project_name="host_counter",
            description="Build an 8-bit counter with a host interface.",
        )
        client = FakeStreamingClient()

        with self.assertRaises(RequirementClarificationRequired) as caught:
            SystemHisGenerator(client).generate(request, _platform())

        self.assertEqual(client.calls, 0)
        self.assertEqual(caught.exception.ambiguity_keys, ("interface_protocols",))

    def test_capability_preflight_matches_current_generic_lowerer_boundary(self) -> None:
        unsupported = build_request_requirement_envelope(
            ProjectRequest(
                task_type="customer_system",
                width=32,
                project_name="customer_system",
                description=(
                    "Dual-clock ADC over AXI-Stream and DMA to DDR/BRAM, then PCIe; "
                    "also expose I2C and UART."
                ),
            ),
            _platform(),
        )
        supported = build_request_requirement_envelope(
            ProjectRequest(
                task_type="customer_supported",
                width=16,
                project_name="customer_supported",
                description="SPI FIFO streaming state machine with FIR image processing.",
            ),
            _platform(),
        )
        backend = load_system_his_backend_capabilities()

        self.assertEqual(
            set(_requirement_capability_gaps(unsupported, backend)),
            {
                "adc_interface",
                "clock_domain_crossing",
                "dma",
                "external_memory",
                "on_chip_memory",
                "pcie",
                "axi_stream",
                "i2c",
                "uart",
            },
        )
        self.assertEqual(_requirement_capability_gaps(supported, backend), ())

    def test_exact_family_recipe_is_added_to_the_unified_prompt_automatically(self) -> None:
        request = _alu_request()
        client = FakeStreamingClient()

        with patch(
            "sr2fpga_agent.generation.req2his.validate_system_his_candidate",
            return_value={"schema_version": "system-his-v1.2"},
        ):
            SystemHisGenerator(client, max_attempts=1).generate(request, _platform())

        self.assertEqual(client.calls, 1)
        prompt = client.messages_history[0][-1]["content"]
        self.assertIn("Required architecture for alu_control_unit", prompt)
        self.assertIn("Requirement envelope", prompt)

    def test_retry_uses_trace_rules_and_the_same_automatic_recipe_decision(self) -> None:
        request = _generic_request()
        platform = _platform()
        envelope, route, decision = _prepare_requirement(request, platform)
        initial = _system_his_v12_messages(
            request,
            platform,
            requirement_envelope=envelope,
            requirement_route=route,
            family_recipe_decision=decision,
        )
        retry = _with_system_his_retry_feedback(
            initial,
            "H1 validation failed",
            "{}",
            task_type=request.task_type,
            family_recipe_task_type=recipe_task_type(decision),
            requirement_trace_template=envelope.requirement_trace_template(),
        )
        prompt = "\n".join(message["content"] for message in retry)

        self.assertNotIn("Required architecture for alu_control_unit", prompt)
        self.assertIn("Requirement-trace repair rules", prompt)
        self.assertIn("width facts to top/component/instance widths", prompt)

        recipe_request = _alu_request()
        recipe_envelope, recipe_route, recipe_decision = _prepare_requirement(
            recipe_request,
            platform,
        )
        recipe_initial = _system_his_v12_messages(
            recipe_request,
            platform,
            requirement_envelope=recipe_envelope,
            requirement_route=recipe_route,
            family_recipe_decision=recipe_decision,
        )
        recipe_retry = _with_system_his_retry_feedback(
            recipe_initial,
            "H1 validation failed",
            "{}",
            task_type=recipe_request.task_type,
            family_recipe_task_type=recipe_task_type(recipe_decision),
            requirement_trace_template=recipe_envelope.requirement_trace_template(),
        )
        recipe_prompt = "\n".join(message["content"] for message in recipe_retry)

        self.assertIn("Required architecture for alu_control_unit", recipe_prompt)


def _alu_request() -> ProjectRequest:
    return ProjectRequest(
        task_type="alu_control_unit",
        width=8,
        project_name="alu_8bit",
        description="Build an 8-bit ALU control unit.",
    )


def _generic_request() -> ProjectRequest:
    return ProjectRequest(
        task_type="customer_spi_pipeline",
        width=8,
        project_name="spi_pipeline",
        description="Build an 8-bit SPI streaming state machine.",
    )


def _platform() -> PlatformProfile:
    return PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )


if __name__ == "__main__":
    unittest.main()
