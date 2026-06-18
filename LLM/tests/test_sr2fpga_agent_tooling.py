import sys
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.log_parser import classify_failure, parse_yosys_stats
from LLM.src.sr2fpga_agent.tool_runner import CommandRunner


class ToolingTest(unittest.TestCase):
    def test_command_runner_captures_successful_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = CommandRunner().run(
                [sys.executable, "-c", "print('ok')"],
                cwd=Path(tmp),
                stage="smoke",
            )

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("ok", result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertGreaterEqual(result.duration_seconds, 0.0)

    def test_command_runner_reports_missing_tool_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = CommandRunner().run(
                ["definitely_missing_sr2fpga_tool_12345"],
                cwd=Path(tmp),
                stage="lint",
            )

        self.assertEqual(result.status, "missing_tool")
        self.assertIsNone(result.exit_code)
        self.assertIn("definitely_missing_sr2fpga_tool_12345", result.stderr)

    def test_classifies_common_failure_types(self) -> None:
        self.assertEqual(classify_failure("Unknown module type: fifo_core"), "module_not_found")
        self.assertEqual(classify_failure("Port rst_n of module top is not declared"), "port_mismatch")
        self.assertEqual(classify_failure("Width mismatch in assignment"), "width_mismatch")
        self.assertEqual(classify_failure("syntax error, unexpected endmodule"), "syntax_error")
        self.assertEqual(classify_failure("no obvious pattern here"), "unknown")

    def test_parse_yosys_stats_extracts_resource_like_counts(self) -> None:
        log = """
        === top ===

           Number of cells:                 12
             $add                            1
             $dff                            8
             $logic_and                      2
             SB_LUT4                         5
             SB_DFF                          8
             SB_RAM40_4K                     1
             SB_MAC16                        2
        """

        stats = parse_yosys_stats(log)

        self.assertEqual(stats["cell_count"], 12)
        self.assertEqual(stats["cell_breakdown"]["SB_LUT4"], 5)
        self.assertEqual(stats["lut"], 5)
        self.assertEqual(stats["ff"], 16)
        self.assertEqual(stats["bram"], 1)
        self.assertEqual(stats["dsp"], 2)


if __name__ == "__main__":
    unittest.main()
