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
        self.assertEqual(
            classify_failure(
                "%Error: rtl/top.v:50:19: Signal definition not found, and implicit disabled "
                "with `default_nettype: 'join_core_ready0'"
            ),
            "undeclared_signal",
        )
        self.assertEqual(
            classify_failure(
                "%Warning-IMPLICIT: rtl/top.v:60:15: Signal definition not found, creating implicitly: "
                "'buffer1_out_data'\n%Error: Exiting due to 14 warning(s)"
            ),
            "undeclared_signal",
        )
        self.assertEqual(
            classify_failure("TEST_FAIL: Timeout waiting for outputs\nSimulation reported TEST_FAIL"),
            "testbench_timeout",
        )
        self.assertEqual(
            classify_failure("TEST_FAIL: timeout waiting for output at iteration 0"),
            "testbench_handshake_timeout",
        )
        self.assertEqual(
            classify_failure("TEST_FAIL: Timeout waiting for input handshake at i=2"),
            "testbench_handshake_timeout",
        )
        self.assertEqual(
            classify_failure("testbench_missing_functional_oracle: TEST_PASS appears without a prior conditional TEST_FAIL oracle"),
            "testbench_missing_functional_oracle",
        )
        self.assertEqual(
            classify_failure(
                "testbench_internal_signal_access: line 12: dut.u_core.state reads below the DUT top-level interface"
            ),
            "testbench_internal_signal_access",
        )
        self.assertEqual(
            classify_failure("%Warning-UNUSEDSIGNAL: Signal is not used\n%Error: Exiting due to 1 warning(s)"),
            "lint_warning_as_error",
        )
        self.assertEqual(
            classify_failure(
                "%Error-PINNOTFOUND: rtl/top.v:15:41: Parameter not found: 'DEPTH'\n"
                "   15 | skid_buffer #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(2)) in0_buffer (\n"
                "      |                                         ^~~~~\n"
                "                                   : ... Location of instance's module declaration\n"
                "    1 | module skid_buffer #(parameter DATA_WIDTH=8) (\n"
                "      |        ^~~~~~~~~~~\n"
                "%Error: Exiting due to 2 error(s)"
            ),
            "parameter_mismatch",
        )
        self.assertEqual(
            classify_failure(
                "sim/tb_top.v:14: internal error: I don't know how to elaborate(ivl_type_t) "
                "this expression: {8'd1, 8'd2, 8'd3}\nElaboration failed"
            ),
            "testbench_simulator_compatibility",
        )
        self.assertEqual(
            classify_failure(
                "testbench_observation_race: line 12: wait(out_valid) is followed by @(posedge clk)"
            ),
            "testbench_observation_race",
        )
        self.assertEqual(
            classify_failure(
                "testbench_stimulus_reaccept_risk: line 42: in0_valid is asserted before wait(out_valid)"
            ),
            "testbench_stimulus_reaccept_risk",
        )
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

    def test_parse_yosys_stats_extracts_current_yosys_stat_format(self) -> None:
        log = """
        === top ===

           12 wires
           33 wire bits
            4 ports
           11 port bits
           22 cells
            5   $_AND_
            8   $_DFFE_PN0P_
            1   $_NAND_
            1   $_NOT_
            1   $_XNOR_
            6   $_XOR_
        """

        stats = parse_yosys_stats(log)

        self.assertEqual(stats["cell_count"], 22)
        self.assertEqual(stats["cell_breakdown"]["$_DFFE_PN0P_"], 8)
        self.assertNotIn("wires", stats["cell_breakdown"])
        self.assertNotIn("ports", stats["cell_breakdown"])
        self.assertEqual(stats["ff"], 8)

    def test_parse_yosys_stats_resets_at_repeated_module_headers(self) -> None:
        log = """
        === top ===
           22 cells
            8   $_DFFE_PN0P_

        === top ===
           12 wires
            4 ports
           22 cells
            8   $_DFFE_PN0P_
        """

        stats = parse_yosys_stats(log)

        self.assertEqual(stats["cell_breakdown"], {"$_DFFE_PN0P_": 8})
        self.assertEqual(stats["cell_count"], 22)


if __name__ == "__main__":
    unittest.main()
