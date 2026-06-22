import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent import PlatformProfile, ProjectGenerator, ProjectRequest


class ProjectGeneratorTest(unittest.TestCase):
    def test_generates_minimal_counter_project_package(self) -> None:
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(
            name="generic_verilog",
            vendor="generic",
            toolchain="open_source",
            clock_hz=100_000_000,
        )

        project = ProjectGenerator().generate(request, platform)

        expected_paths = {
            "system_his.json",
            "manifest.json",
            "rtl/top.v",
            "constraints/timing.sdc",
            "sim/tb_top.v",
            "reports/predicted_qor.json",
        }
        self.assertEqual(set(project.files), expected_paths)

        manifest = json.loads(project.files["manifest.json"])
        self.assertEqual(manifest["project_name"], "counter_8bit")
        self.assertEqual(manifest["top_module"], "top")
        self.assertEqual(manifest["sources"], ["rtl/top.v"])
        self.assertEqual(manifest["simulation"]["testbench"], "sim/tb_top.v")

        rtl = project.files["rtl/top.v"]
        self.assertRegex(rtl, r"module\s+top\s*\(")
        self.assertIn("input wire clk", rtl)
        self.assertIn("input wire rst_n", rtl)
        self.assertIn("input wire en", rtl)
        self.assertIn("output reg [7:0] count", rtl)

        testbench = project.files["sim/tb_top.v"]
        self.assertRegex(testbench, r"top\s+dut\s*\(")
        self.assertIn(".count(count)", testbench)
        self.assertIn("TEST_PASS", testbench)

        predicted_qor = json.loads(project.files["reports/predicted_qor.json"])
        self.assertEqual(predicted_qor["project_name"], "counter_8bit")
        self.assertEqual(predicted_qor["assumptions"]["counter_width"], 8)
        for key in ("lut", "ff", "bram", "dsp", "fmax_mhz", "confidence"):
            self.assertIn(key, predicted_qor["predicted"])

    def test_manifest_top_module_matches_rtl_module_name(self) -> None:
        request = ProjectRequest(task_type="counter", width=4, project_name="counter_4bit")
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        project = ProjectGenerator().generate(request, platform)

        manifest = json.loads(project.files["manifest.json"])
        rtl = project.files["rtl/top.v"]
        module_name = re.search(r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_$]*)\s*\(", rtl)
        self.assertIsNotNone(module_name)
        self.assertEqual(manifest["top_module"], module_name.group(1))

    def test_generates_fifo_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="fifo", width=8, project_name="fifo_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        self.assertEqual(_task_type(project), "fifo")
        self.assertIn("module top", project.files["rtl/top.v"])
        self.assertIn("wr_en", project.files["rtl/top.v"])
        self.assertIn("rd_en", project.files["rtl/top.v"])
        self.assertIn("full", project.files["rtl/top.v"])
        self.assertIn("empty", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_simple_fsm_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="simple_fsm", width=4, project_name="fsm_sequence_4bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        self.assertEqual(_task_type(project), "simple_fsm")
        self.assertIn("state", project.files["rtl/top.v"])
        self.assertIn("start", project.files["rtl/top.v"])
        self.assertIn("done", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_ram_read_write_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="ram_read_write", width=16, project_name="ram_rw_16bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        self.assertEqual(_task_type(project), "ram_read_write")
        self.assertIn("addr", project.files["rtl/top.v"])
        self.assertIn("wdata", project.files["rtl/top.v"])
        self.assertIn("rdata", project.files["rtl/top.v"])
        self.assertIn("mem", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_uart_tx_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "uart_tx",
            {"rtl/top.v", "rtl/uart_tx_core.v", "rtl/baud_tick_gen.v"},
            ["uart_tx_core", "baud_tick_gen", ".tx(tx)", ".busy(busy)"],
        )
        self.assertIn("output wire tx", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_pwm_controller_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="pwm_controller", width=8, project_name="pwm_controller_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "pwm_controller",
            {"rtl/top.v", "rtl/pwm_timer.v", "rtl/pwm_channel.v"},
            ["pwm_timer", "pwm_channel", ".pwm_out(pwm_out)"],
        )
        self.assertIn("input wire [7:0] duty", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_generates_streaming_valid_ready_multimodule_project_package(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(
                task_type="streaming_valid_ready",
                width=8,
                project_name="streaming_valid_ready_8bit",
            ),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )

        _assert_multimodule_task(
            self,
            project,
            "streaming_valid_ready",
            {"rtl/top.v", "rtl/stream_stage.v", "rtl/skid_buffer.v"},
            ["stream_stage", "skid_buffer", ".in_valid(in_valid)", ".out_ready(out_ready)"],
        )
        self.assertIn("out_valid", project.files["rtl/top.v"])
        self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_manifest_sources_exist_for_all_supported_task_types(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        for task_type, width, project_name in _supported_task_cases():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                _assert_manifest_sources_exist(self, project)
                self.assertEqual(_manifest(project)["simulation"]["testbench"], "sim/tb_top.v")
                self.assertIn("TEST_PASS", project.files["sim/tb_top.v"])

    def test_system_his_architecture_submodules_match_emitted_rtl_modules(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        for task_type, width, project_name in _supported_task_cases():
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                architecture = _system_his(project)["architecture"]
                actual_submodules = sorted(_non_top_rtl_module_names(project))

                self.assertEqual(architecture["top_module"], "top")
                self.assertEqual(sorted(architecture["submodules"]), actual_submodules)
                expected_style = "multi_module" if actual_submodules else "single_module"
                self.assertEqual(architecture["style"], expected_style)

    @unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "iverilog/vvp are not installed")
    def test_task2_generated_testbenches_pass_under_icarus(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = [
            ("uart_tx", 8, "uart_tx_8bit"),
            ("pwm_controller", 8, "pwm_controller_8bit"),
            ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
        ]

        for task_type, width, project_name in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                with tempfile.TemporaryDirectory() as tmp:
                    project_dir = Path(tmp)
                    _write_project(project_dir, project)
                    manifest = _manifest(project)
                    compile_result = subprocess.run(
                        [
                            "iverilog",
                            "-g2012",
                            "-o",
                            "sim.out",
                            *manifest["sources"],
                            manifest["simulation"]["testbench"],
                        ],
                        cwd=project_dir,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(
                        compile_result.returncode,
                        0,
                        f"{task_type} sim compile failed\n"
                        f"STDOUT:\n{compile_result.stdout}\n"
                        f"STDERR:\n{compile_result.stderr}",
                    )
                    run_result = subprocess.run(
                        ["vvp", "sim.out"],
                        cwd=project_dir,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(
                    run_result.returncode,
                    0,
                    f"{task_type} sim run failed\nSTDOUT:\n{run_result.stdout}\nSTDERR:\n{run_result.stderr}",
                )
                self.assertIn("TEST_PASS", run_result.stdout)

    @unittest.skipUnless(shutil.which("verilator"), "verilator is not installed")
    def test_multimodule_task_sources_are_verilator_wall_clean(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        cases = [
            ("uart_tx", 8, "uart_tx_8bit"),
            ("spi_master", 8, "spi_master_8bit"),
            ("pwm_controller", 8, "pwm_controller_8bit"),
            ("fir_filter", 8, "fir_filter_8bit"),
            ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
            ("matrix_vector_mac", 8, "matrix_vector_mac_8bit"),
        ]

        for task_type, width, project_name in cases:
            with self.subTest(task_type=task_type):
                project = ProjectGenerator().generate(
                    ProjectRequest(task_type=task_type, width=width, project_name=project_name),
                    platform,
                )
                with tempfile.TemporaryDirectory() as tmp:
                    project_dir = Path(tmp)
                    _write_project(project_dir, project)
                    manifest = _manifest(project)
                    result = subprocess.run(
                        ["verilator", "--lint-only", "-Wall", *manifest["sources"]],
                        cwd=project_dir,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{task_type} lint failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                )


def _task_type(project) -> str:
    return json.loads(project.files["system_his.json"])["task_type"]


def _manifest(project) -> dict:
    return json.loads(project.files["manifest.json"])


def _system_his(project) -> dict:
    return json.loads(project.files["system_his.json"])


def _supported_task_cases() -> list[tuple[str, int, str]]:
    return [
        ("counter", 8, "counter_8bit"),
        ("fifo", 8, "fifo_8bit"),
        ("simple_fsm", 4, "fsm_sequence_4bit"),
        ("ram_read_write", 16, "ram_rw_16bit"),
        ("uart_tx", 8, "uart_tx_8bit"),
        ("spi_master", 8, "spi_master_8bit"),
        ("pwm_controller", 8, "pwm_controller_8bit"),
        ("fir_filter", 8, "fir_filter_8bit"),
        ("streaming_valid_ready", 8, "streaming_valid_ready_8bit"),
        ("matrix_vector_mac", 8, "matrix_vector_mac_8bit"),
    ]


def _non_top_rtl_module_names(project) -> list[str]:
    names = []
    for source in _manifest(project)["sources"]:
        for match in re.finditer(r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_$]*)\b", project.files[source]):
            if match.group(1) != "top":
                names.append(match.group(1))
    return names


def _assert_manifest_sources_exist(testcase: unittest.TestCase, project) -> None:
    manifest = _manifest(project)
    rtl_sources = sorted(path for path in project.files if path.startswith("rtl/"))
    testcase.assertEqual(sorted(manifest["sources"]), rtl_sources)
    testcase.assertIn("rtl/top.v", manifest["sources"])
    for source in manifest["sources"]:
        testcase.assertIn(source, project.files)
        testcase.assertTrue(source.startswith("rtl/"), source)
        testcase.assertIn("module ", project.files[source])


def _assert_multimodule_task(
    testcase: unittest.TestCase,
    project,
    task_type: str,
    expected_sources: set[str],
    top_markers: list[str],
) -> None:
    manifest = _manifest(project)
    system_his = _system_his(project)
    testcase.assertEqual(system_his["task_type"], task_type)
    testcase.assertTrue(expected_sources.issubset(set(manifest["sources"])))
    testcase.assertTrue(expected_sources.issubset(set(project.files)))
    testcase.assertGreater(len(manifest["sources"]), 1)
    testcase.assertIn("architecture", system_his)
    testcase.assertIn("submodules", system_his["architecture"])
    for marker in top_markers:
        testcase.assertIn(marker, project.files["rtl/top.v"])
    testcase.assertIn("TEST_PASS", project.files["sim/tb_top.v"])


def _write_project(project_dir: Path, project) -> None:
    for relative_path, content in project.files.items():
        target = project_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
