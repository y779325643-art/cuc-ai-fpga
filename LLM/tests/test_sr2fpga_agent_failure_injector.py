import json
import unittest

from LLM.src.sr2fpga_agent.failure_injector import (
    FailureInjectingProjectGenerator,
    apply_failure_injectors,
)
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator


class FailureInjectorTest(unittest.TestCase):
    def test_rename_reset_port_injector_breaks_rtl_without_rewriting_testbench(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["rename_reset_port"])

        self.assertIn("reset_n", injected.files["rtl/top.v"])
        self.assertNotIn("input wire rst_n", injected.files["rtl/top.v"])
        self.assertIn(".rst_n(rst_n)", injected.files["sim/tb_top.v"])
        self.assertEqual(json.loads(injected.files["manifest.json"])["sources"], ["rtl/top.v"])

    def test_missing_manifest_source_injector_adds_absent_source_reference(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["missing_manifest_source"])

        manifest = json.loads(injected.files["manifest.json"])
        self.assertIn("rtl/missing_dependency.v", manifest["sources"])
        self.assertNotIn("rtl/missing_dependency.v", injected.files)

    def test_width_mismatch_injector_changes_top_port_width_only(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["width_mismatch"])

        self.assertIn("output reg [4:0] count", injected.files["rtl/top.v"])
        self.assertIn("wire [3:0] count", injected.files["sim/tb_top.v"])

    def test_width_mismatch_injector_handles_wider_counter(self) -> None:
        project = _counter_project(width=8)

        injected = apply_failure_injectors(project, ["width_mismatch"])

        self.assertIn("output reg [8:0] count", injected.files["rtl/top.v"])
        self.assertIn("wire [7:0] count", injected.files["sim/tb_top.v"])

    def test_testbench_expected_value_mismatch_changes_self_check(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["testbench_expected_value_mismatch"])

        self.assertIn("count !== 4'd5", injected.files["sim/tb_top.v"])
        self.assertIn("TEST_FAIL expected count=4", injected.files["sim/tb_top.v"])

    def test_constraint_missing_clock_injector_references_absent_clock(self) -> None:
        project = _counter_project()

        injected = apply_failure_injectors(project, ["constraint_missing_clock"])

        self.assertEqual(injected.files["constraints/timing.sdc"], "create_clock -name missing_clk -period 10.000 [get_ports missing_clk]\n")

    def test_multimodule_connection_mismatch_changes_top_instantiation_only(self) -> None:
        project = _uart_tx_project()

        injected = apply_failure_injectors(project, ["multimodule_connection_mismatch"])

        self.assertIn("uart_tx_core_missing u_uart_tx_core", injected.files["rtl/top.v"])
        self.assertIn("module uart_tx_core", injected.files["rtl/uart_tx_core.v"])

    def test_failure_injecting_project_generator_wraps_base_generator(self) -> None:
        base = CountingGenerator()
        request = ProjectRequest(task_type="counter", width=4, project_name="counter_4bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = FailureInjectingProjectGenerator(base, ["wrong_top_module"]).generate(request, platform)

        self.assertEqual(base.call_count, 1)
        self.assertEqual(json.loads(project.files["manifest.json"])["top_module"], "missing_top")


def _counter_project(width: int = 4) -> GeneratedProject:
    request = ProjectRequest(task_type="counter", width=width, project_name=f"counter_{width}bit")
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    return ProjectGenerator().generate(request, platform)


def _uart_tx_project() -> GeneratedProject:
    request = ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit")
    platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
    return ProjectGenerator().generate(request, platform)


class CountingGenerator:
    def __init__(self) -> None:
        self.call_count = 0
        self.base = ProjectGenerator()

    def generate(self, request, platform):
        self.call_count += 1
        return self.base.generate(request, platform)


if __name__ == "__main__":
    unittest.main()
