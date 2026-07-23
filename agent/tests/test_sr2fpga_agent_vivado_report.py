import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from sr2fpga_agent.vivado_report import (
    build_vivado_tcl,
    normalize_existing_vivado_reports,
    parse_vivado_reports,
    run_vivado_reference,
)


TIMING_REPORT = """
Design Timing Summary
---------------------
WNS(ns)      TNS(ns)  TNS Failing Endpoints  TNS Total Endpoints
-------      -------  ---------------------  -------------------
  7.500        0.000                      0                   28
"""

UTILIZATION_REPORT = """
1. Slice Logic
--------------
| Site Type            | Used | Fixed | Available | Util% |
| Slice LUTs*           |   32 |     0 |     53200 |  0.06 |
| Slice Registers      |   29 |     0 |    106400 |  0.03 |
| Block RAM Tile       |  1.0 |     0 |       140 |  0.71 |
| DSPs                 |    3 |     0 |       220 |  1.36 |
"""

DRC_REPORT = """
| Rule   | Severity         | Description                | Checks |
| NSTD-1 | Critical Warning | Unspecified I/O Standard   | 1      |
| UCIO-1 | Critical Warning | Unconstrained Logical Port | 1      |
| ZPS7-1 | Warning          | PS7 block required         | 1      |
"""

METHODOLOGY_REPORT = """
| Rule      | Severity | Description                   | Checks |
| TIMING-18 | Warning  | Missing input or output delay | 24     |
"""


class VivadoReportTest(unittest.TestCase):
    def test_parse_vivado_reports_extracts_qor_and_derives_fmax(self) -> None:
        report = parse_vivado_reports(TIMING_REPORT, UTILIZATION_REPORT, target_period_ns=10.0)

        self.assertEqual(report["status"], "pass")
        self.assertAlmostEqual(report["wns_ns"], 7.5)
        self.assertAlmostEqual(report["fmax_mhz"], 400.0)
        self.assertEqual(report["lut"], 32)
        self.assertEqual(report["ff"], 29)
        self.assertEqual(report["bram"], 1)
        self.assertEqual(report["dsp"], 3)

    def test_parse_vivado_reports_marks_negative_slack_as_fail(self) -> None:
        timing = TIMING_REPORT.replace("7.500", "-0.250")

        report = parse_vivado_reports(timing, UTILIZATION_REPORT, target_period_ns=10.0)

        self.assertEqual(report["status"], "fail")
        self.assertAlmostEqual(report["wns_ns"], -0.25)

    def test_parse_vivado_reports_classifies_expected_board_only_drc(self) -> None:
        report = parse_vivado_reports(
            TIMING_REPORT,
            UTILIZATION_REPORT,
            target_period_ns=10.0,
            drc_report=DRC_REPORT,
            methodology_report=METHODOLOGY_REPORT,
        )

        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["official_board_ready"])
        self.assertEqual(report["expected_board_drc_exceptions"], ["NSTD-1", "UCIO-1"])
        self.assertEqual(report["invalidating_critical_warnings"], [])
        self.assertEqual(report["methodology_warnings"], ["TIMING-18"])

    def test_build_vivado_tcl_uses_manifest_sources_top_and_required_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "generated_project"
            (project_dir / "rtl").mkdir(parents=True)
            (project_dir / "rtl/top.v").write_text("module top(input clk); endmodule\n", encoding="utf-8")
            (project_dir / "manifest.json").write_text(
                json.dumps({"top_module": "top", "sources": ["rtl/top.v"]}),
                encoding="utf-8",
            )
            (project_dir / "system_his.json").write_text(
                json.dumps({"clocks": [{"name": "clk"}]}),
                encoding="utf-8",
            )

            tcl = build_vivado_tcl(project_dir, part="XC7Z020CLG484-2", target_period_ns=10.0)

            self.assertIn("read_verilog -sv", tcl)
            self.assertIn((project_dir / "rtl/top.v").resolve().as_posix(), tcl)
            self.assertIn("synth_design -top {top} -part {XC7Z020CLG484-2}", tcl)
            self.assertIn("create_clock -period 10.000000 [get_ports {clk}]", tcl)
            self.assertIn("report_timing_summary", tcl)
            self.assertIn("report_utilization", tcl)
            self.assertIn("report_drc", tcl)
            self.assertIn("report_methodology", tcl)

    def test_run_vivado_reference_writes_normalized_report_and_command_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "generated_project"
            (project_dir / "rtl").mkdir(parents=True)
            (project_dir / "rtl/top.v").write_text("module top(input clk); endmodule\n", encoding="utf-8")
            (project_dir / "manifest.json").write_text(
                json.dumps({"top_module": "top", "sources": ["rtl/top.v"]}),
                encoding="utf-8",
            )
            report_dir = project_dir / "eval/vivado"
            report_dir.mkdir(parents=True)
            (report_dir / "vivado_timing_summary.rpt").write_text(TIMING_REPORT, encoding="utf-8")
            (report_dir / "vivado_utilization.rpt").write_text(UTILIZATION_REPORT, encoding="utf-8")
            (report_dir / "vivado_drc.rpt").write_text(DRC_REPORT, encoding="utf-8")
            (report_dir / "vivado_methodology.rpt").write_text(METHODOLOGY_REPORT, encoding="utf-8")

            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="Vivado completed\n", stderr="")
            with mock.patch(
                "sr2fpga_agent.vivado_report.subprocess.run",
                return_value=completed,
            ) as run:
                report = run_vivado_reference(
                    project_dir,
                    vivado_command="vivado",
                    part="XC7Z020CLG484-2",
                    target_period_ns=10.0,
                    timeout_seconds=60,
                )

            command = run.call_args.args[0]
            self.assertEqual(command[:3], ["vivado", "-mode", "batch"])
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["exit_code"], 0)
            self.assertFalse(report["official_board_ready"])
            self.assertTrue((report_dir / "vivado_run.tcl").is_file())
            self.assertTrue((report_dir / "vivado.log").is_file())
            self.assertEqual(
                json.loads((report_dir / "vivado_report.json").read_text(encoding="utf-8"))["lut"],
                32,
            )

    def test_normalize_existing_vivado_reports_backfills_drc_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "generated_project"
            report_dir = project_dir / "eval/vivado"
            report_dir.mkdir(parents=True)
            (report_dir / "vivado_timing_summary.rpt").write_text(TIMING_REPORT, encoding="utf-8")
            (report_dir / "vivado_utilization.rpt").write_text(UTILIZATION_REPORT, encoding="utf-8")
            (report_dir / "vivado_drc.rpt").write_text(DRC_REPORT, encoding="utf-8")
            (report_dir / "vivado_methodology.rpt").write_text(METHODOLOGY_REPORT, encoding="utf-8")

            report = normalize_existing_vivado_reports(project_dir, target_period_ns=10.0)

            self.assertEqual(report["expected_board_drc_exceptions"], ["NSTD-1", "UCIO-1"])
            self.assertTrue((report_dir / "vivado_report.json").is_file())


if __name__ == "__main__":
    unittest.main()
