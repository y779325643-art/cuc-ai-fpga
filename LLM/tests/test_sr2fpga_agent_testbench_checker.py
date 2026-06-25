import unittest

from LLM.src.sr2fpga_agent.testbench_checker import (
    check_testbench_observation_races,
    check_testbench_static_issues,
)


class TestbenchCheckerTest(unittest.TestCase):
    def test_flags_wait_valid_then_next_posedge_before_data_check(self) -> None:
        testbench = """
        module tb;
          initial begin
            wait(out_valid);
            @(posedge clk) #1;
            if (out_data !== expected) begin
              $display("TEST_FAIL");
            end
          end
        endmodule
        """

        issues = check_testbench_observation_races(testbench)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].failure_type, "testbench_observation_race")
        self.assertIn("wait(out_valid)", issues[0].message)
        self.assertIn("@(posedge clk)", issues[0].message)

    def test_allows_same_valid_cycle_small_delay_before_data_check(self) -> None:
        testbench = """
        module tb;
          initial begin
            wait(out_valid);
            #1;
            if (out_data !== expected) begin
              $display("TEST_FAIL");
            end
            @(posedge clk);
          end
        endmodule
        """

        self.assertEqual(check_testbench_observation_races(testbench), [])

    def test_flags_input_valid_held_until_output_valid(self) -> None:
        testbench = """
        module tb;
          initial begin
            in0_valid = 1;
            in1_valid = 1;
            in0_data = seq0[i];
            in1_data = seq1[i];
            @(posedge clk);
            wait(out_valid);
            #1;
            if (out_data !== expected[i]) begin
              $display("TEST_FAIL");
            end
            @(negedge clk);
            in0_valid = 0;
            in1_valid = 0;
          end
        endmodule
        """

        issues = check_testbench_static_issues(testbench)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].failure_type, "testbench_stimulus_reaccept_risk")
        self.assertIn("in0_valid", issues[0].message)
        self.assertIn("wait(out_valid)", issues[0].message)


if __name__ == "__main__":
    unittest.main()
