import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from LLM.src.sr2fpga_agent.agent import DataGenerationAgent, _openxc7_pnr_command, _openxc7_project_dir_arg
from LLM.src.sr2fpga_agent.models import PlatformProfile, ProjectRequest, ToolResult
from LLM.src.sr2fpga_agent.openxc7_report import parse_openxc7_report


SAMPLE_LOG = """
Info: Device utilisation:
Info:            SLICE_LUTX:    42/53200    0%
Info:            SLICE_FFX:     31/106400   0%
Info:             RAMB36E1:      1/140      0%
Info:             DSP48E1:       2/220      0%
Info: Max frequency for clock 'clk': 142.31 MHz (PASS at 100.00 MHz)
Info: Critical path report for clock 'clk': WNS 1.25 ns
"""


class OpenXC7ReportTest(unittest.TestCase):
    def test_openxc7_default_command_uses_repository_wrapper(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SR2FPGA_OPENXC7_PNR_COMMAND", None)
            command = _openxc7_pnr_command(Path("tmp/generated_project"), platform)

        if os.name == "nt":
            self.assertEqual(command[:2], ["wsl", "bash"])
            self.assertRegex(command[2], r"^/mnt/[a-z]/.*/scripts/openxc7_pnr\.sh$")
        else:
            self.assertEqual(command[0], "bash")
            self.assertTrue(command[1].endswith("/scripts/openxc7_pnr.sh"))

    def test_openxc7_project_argument_is_absolute(self) -> None:
        argument = _openxc7_project_dir_arg(Path("tmp/generated_project"))

        self.assertTrue(Path(argument).is_absolute())

    def test_openxc7_wrapper_normalizes_part_name_for_chipdb_lookup(self) -> None:
        wrapper = Path("scripts/openxc7_pnr.sh").read_text(encoding="utf-8")

        self.assertIn('part_base="${part_base,,}"', wrapper)

    def test_parse_openxc7_report_extracts_utilization_fmax_and_wns(self) -> None:
        report = parse_openxc7_report(SAMPLE_LOG)

        self.assertEqual(report["lut"], 42)
        self.assertEqual(report["ff"], 31)
        self.assertEqual(report["bram"], 1)
        self.assertEqual(report["dsp"], 2)
        self.assertAlmostEqual(report["fmax_mhz"], 142.31)
        self.assertAlmostEqual(report["wns_ns"], 1.25)

    def test_parse_openxc7_report_missing_timing_is_none(self) -> None:
        report = parse_openxc7_report("Info: Device utilisation:\nInfo: SLICE_LUTX: 5/53200 0%\n")

        self.assertEqual(report["lut"], 5)
        self.assertEqual(report["ff"], 0)
        self.assertIsNone(report["fmax_mhz"])
        self.assertIsNone(report["wns_ns"])

    def test_parse_openxc7_report_derives_slack_from_fmax_and_target(self) -> None:
        report = parse_openxc7_report(
            "Info: Max frequency for clock 'clk': 434.03 MHz (PASS at 100.00 MHz)\n"
        )

        self.assertAlmostEqual(report["fmax_mhz"], 434.03)
        self.assertAlmostEqual(report["wns_ns"], 10.0 - (1000.0 / 434.03), places=3)

    def test_parse_openxc7_report_uses_worst_reported_clock_frequency(self) -> None:
        report = parse_openxc7_report(
            "Info: Max frequency for clock 'clk': 434.03 MHz (PASS at 100.00 MHz)\n"
            "Info: Max frequency for clock 'clk': 423.37 MHz (PASS at 100.00 MHz)\n"
        )

        self.assertAlmostEqual(report["fmax_mhz"], 423.37)
        self.assertAlmostEqual(report["wns_ns"], 10.0 - (1000.0 / 423.37), places=3)

    def test_parse_openxc7_report_extracts_metrics_from_wrapper_json_log(self) -> None:
        report = parse_openxc7_report(json.dumps({"tool": "nextpnr-xilinx", "log": SAMPLE_LOG}))

        self.assertEqual(report["lut"], 42)
        self.assertEqual(report["ff"], 31)
        self.assertEqual(report["bram"], 1)
        self.assertAlmostEqual(report["fmax_mhz"], 142.31)

    def test_parse_openxc7_report_does_not_double_count_combined_wrapper_output(self) -> None:
        wrapper_output = SAMPLE_LOG + json.dumps(
            {"tool": "nextpnr-xilinx", "log": SAMPLE_LOG},
            indent=2,
        )

        report = parse_openxc7_report(wrapper_output)

        self.assertEqual(report["lut"], 42)
        self.assertEqual(report["ff"], 31)
        self.assertEqual(report["bram"], 1)
        self.assertEqual(report["dsp"], 2)


class OpenXC7PipelineTest(unittest.TestCase):
    def test_agent_records_l4_and_openxc7_qor_when_enabled_and_pnr_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = PnrPassingRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                enable_openxc7_l4=True,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_openxc7_l4",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_openxc7_l4"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            measured_qor = json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L4")
            self.assertEqual(labels["pass_level"], "L4")
            self.assertTrue(labels["checks"]["l4_lite_timing_pass"])
            self.assertEqual(measured_qor["lut"], 42)
            self.assertEqual(measured_qor["ff"], 31)
            self.assertEqual(measured_qor["bram"], 1)
            self.assertEqual(measured_qor["dsp"], 2)
            self.assertAlmostEqual(measured_qor["fmax_mhz"], 142.31)
            self.assertAlmostEqual(measured_qor["wns_ns"], 1.25)
            self.assertEqual(measured_qor["l4_openxc7"]["status"], "pass")
            self.assertEqual(measured_qor["l4_openxc7"]["lut"], 42)
            self.assertEqual(measured_qor["l4_openxc7"]["ff"], 31)
            self.assertEqual(measured_qor["l4_openxc7"]["bram"], 1)
            self.assertEqual(measured_qor["l4_openxc7"]["dsp"], 2)
            self.assertAlmostEqual(measured_qor["l4_openxc7"]["fmax_mhz"], 142.31)
            self.assertAlmostEqual(measured_qor["l4_openxc7"]["wns_ns"], 1.25)
            expected_report_paths = [
                "attempts/attempt_000/generated_project/eval/openxc7_nextpnr.log",
                "attempts/attempt_000/generated_project/eval/openxc7_report.json",
            ]
            self.assertEqual(measured_qor["l4_openxc7"]["report_paths"], expected_report_paths)
            self.assertEqual(trajectory["verification"]["l4_open"]["report_paths"], expected_report_paths)
            self.assertEqual(
                [item["stage"] for item in trajectory["attempts"]],
                ["rtl_identifier_check", "lint", "testbench_static_check", "sim_compile", "sim_run", "synth", "pnr"],
            )
            self.assertEqual([call["stage"] for call in runner.calls], ["lint", "sim_compile", "sim_run", "synth", "pnr"])

    def test_agent_applies_l4_command_part_and_timeout_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = PnrPassingRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                enable_openxc7_l4=True,
                openxc7_command="custom_openxc7_pnr",
                openxc7_part="XC7Z020CLG484-2",
                openxc7_board_profile="ac820_zynq",
                openxc7_timeout_seconds=7,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one(
                sample_id="sample_openxc7_l4_config",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            pnr_call = [call for call in runner.calls if call["stage"] == "pnr"][0]
            sample_dir = root / "sample_openxc7_l4_config"
            measured_qor = json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(pnr_call["timeout_seconds"], 7)
            self.assertEqual(pnr_call["command"][0], "custom_openxc7_pnr")
            self.assertIn("XC7Z020CLG484-2", pnr_call["command"])
            self.assertEqual(measured_qor["l4_openxc7"]["board_profile"], "ac820_zynq")
            self.assertEqual(measured_qor["l4_openxc7"]["constraint_scope"], "logical_only")
            self.assertFalse(measured_qor["l4_openxc7"]["board_constraints_applied"])
            self.assertEqual(trajectory["verification"]["l4_open"]["board_profile"], "ac820_zynq")
            self.assertEqual(trajectory["verification"]["l4_open"]["constraint_scope"], "logical_only")
            self.assertFalse(trajectory["verification"]["l4_open"]["board_constraints_applied"])

    def test_agent_treats_l4_timeout_as_not_run_without_repair_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = PnrTimeoutRunner()
            agent = DataGenerationAgent(dataset_root=root, command_runner=runner, enable_openxc7_l4=True)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_openxc7_l4_timeout",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_openxc7_l4_timeout"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L3")
            self.assertEqual(labels["pass_level"], "L3")
            self.assertEqual(labels["failure_count"], 0)
            self.assertEqual(labels["l4_open_status"], "not_run")
            self.assertEqual(labels["l4_open_skip_reason"], "tool_timeout")
            self.assertEqual(trajectory["verification"]["l4_open"]["skip_reason"], "tool_timeout")
            self.assertFalse((sample_dir / "attempts/attempt_000/diagnosis.json").exists())

    def test_agent_records_archived_openxc7_log_path_when_pnr_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = PnrFailingWithLogRunner()
            agent = DataGenerationAgent(dataset_root=root, command_runner=runner, enable_openxc7_l4=True)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_openxc7_l4_fail_with_log",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_openxc7_l4_fail_with_log"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            measured_qor = json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            expected_report_paths = ["attempts/attempt_000/generated_project/eval/openxc7_nextpnr.log"]

            self.assertEqual(result["pass_level"], "L3")
            self.assertEqual(labels["l4_open_status"], "fail")
            self.assertEqual(measured_qor["l4_openxc7"]["status"], "fail")
            self.assertEqual(measured_qor["l4_openxc7"]["report_paths"], expected_report_paths)
            self.assertEqual(trajectory["verification"]["l4_open"]["report_paths"], expected_report_paths)
            self.assertTrue((sample_dir / expected_report_paths[0]).is_file())

    def test_agent_treats_l4_toolchain_environment_failure_as_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = PnrEnvironmentFailureRunner()
            agent = DataGenerationAgent(dataset_root=root, command_runner=runner, enable_openxc7_l4=True)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_openxc7_l4_env_failure",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_openxc7_l4_env_failure"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L3")
            self.assertEqual(labels["failure_count"], 0)
            self.assertEqual(labels["l4_open_status"], "not_run")
            self.assertEqual(labels["l4_open_skip_reason"], "toolchain_environment_failure")
            self.assertEqual(trajectory["verification"]["l4_open"]["skip_reason"], "toolchain_environment_failure")
            self.assertFalse((sample_dir / "attempts/attempt_000/diagnosis.json").exists())

    def test_agent_treats_openxc7_setup_errors_as_toolchain_environment_failure(self) -> None:
        for stderr in (
            "Missing executable: nextpnr-xilinx",
            "OpenXC7 chipdb not found for part base: xc7z020clg484",
        ):
            with self.subTest(stderr=stderr), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
                runner = PnrEnvironmentFailureRunner(stderr=stderr)
                agent = DataGenerationAgent(dataset_root=root, command_runner=runner, enable_openxc7_l4=True)
                request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
                platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

                agent.run_one(
                    sample_id="sample_openxc7_l4_setup_failure",
                    requirement="Design an 8-bit counter with enable.",
                    request=request,
                    platform=platform,
                )

                sample_dir = root / "sample_openxc7_l4_setup_failure"
                labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
                self.assertEqual(labels["pass_level"], "L3")
                self.assertEqual(labels["failure_count"], 0)
                self.assertEqual(labels["l4_open_status"], "not_run")
                self.assertEqual(labels["l4_open_skip_reason"], "toolchain_environment_failure")
                self.assertFalse((sample_dir / "attempts/attempt_000/diagnosis.json").exists())


class PnrPassingRunner:
    def __init__(self) -> None:
        self.calls = []

    def run(self, command, cwd, stage, timeout_seconds=30):
        self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
        stdout_by_stage = {
            "lint": "",
            "sim_compile": "",
            "sim_run": "TEST_PASS\n",
            "synth": """
                Number of cells: 13
                  SB_LUT4 5
                  SB_DFF 8
            """,
            "pnr": SAMPLE_LOG + json.dumps({"tool": "nextpnr-xilinx", "log": SAMPLE_LOG}, indent=2),
        }
        if stage == "pnr":
            eval_dir = Path(cwd) / "eval"
            eval_dir.mkdir(parents=True, exist_ok=True)
            (eval_dir / "openxc7_nextpnr.log").write_text(SAMPLE_LOG, encoding="utf-8")
            (eval_dir / "openxc7_report.json").write_text(
                json.dumps({"tool": "nextpnr-xilinx", "log": SAMPLE_LOG}, indent=2),
                encoding="utf-8",
            )
        return ToolResult(
            stage=stage,
            command=list(command),
            status="passed",
            exit_code=0,
            stdout=stdout_by_stage[stage],
            stderr="",
            duration_seconds=0.01,
        )


class PnrTimeoutRunner(PnrPassingRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == "pnr":
            self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
            return ToolResult(
                stage=stage,
                command=list(command),
                status="timeout",
                exit_code=124,
                stdout="",
                stderr="nextpnr timed out",
                duration_seconds=timeout_seconds,
            )
        return super().run(command, cwd, stage, timeout_seconds)


class PnrFailingWithLogRunner(PnrPassingRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == "pnr":
            self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
            eval_dir = Path(cwd) / "eval"
            eval_dir.mkdir(parents=True, exist_ok=True)
            (eval_dir / "openxc7_nextpnr.log").write_text("ERROR: timing violation\n", encoding="utf-8")
            return ToolResult(
                stage=stage,
                command=list(command),
                status="failed",
                exit_code=1,
                stdout="",
                stderr="ERROR: timing violation",
                duration_seconds=0.01,
            )
        return super().run(command, cwd, stage, timeout_seconds)


class PnrEnvironmentFailureRunner(PnrPassingRunner):
    def __init__(self, stderr: str = "toolchain_environment_failure: chipdb is unavailable") -> None:
        super().__init__()
        self.stderr = stderr

    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == "pnr":
            self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
            return ToolResult(
                stage=stage,
                command=list(command),
                status="failed",
                exit_code=1,
                stdout="",
                stderr=self.stderr,
                duration_seconds=0.01,
            )
        return super().run(command, cwd, stage, timeout_seconds)


if __name__ == "__main__":
    unittest.main()
