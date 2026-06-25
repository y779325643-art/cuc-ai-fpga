import unittest

from LLM.src.sr2fpga_agent.semantic_trace import (
    diagnose_semantic_trace,
    parse_semantic_trace,
    summarize_semantic_trace,
)


class SemanticTraceTest(unittest.TestCase):
    def test_parses_trace_events_and_reports_first_output_mismatch(self) -> None:
        log = """
        Starting testbench...
        TRACE input_accept cycle=4 lane=0 idx=0 data=1
        TRACE input_accept cycle=4 lane=1 idx=0 data=4
        TRACE join_output cycle=6 idx=0 data=5
        TRACE output cycle=8 idx=0 expected=5 actual=5
        TRACE input_accept cycle=14 lane=0 idx=1 data=2
        TRACE input_accept cycle=14 lane=1 idx=1 data=5
        TRACE join_output cycle=16 idx=1 data=7
        TRACE output cycle=18 idx=1 expected=12 actual=10
        TEST_FAIL
        """

        trace = parse_semantic_trace(log)
        summary = summarize_semantic_trace(trace)

        self.assertEqual(trace["input_accepts"][0]["data"], 1)
        self.assertEqual(trace["join_outputs"][1]["data"], 7)
        self.assertEqual(summary["input_accept_count"], 4)
        self.assertEqual(summary["join_output_count"], 2)
        self.assertEqual(summary["output_count"], 2)
        self.assertEqual(
            summary["first_output_mismatch"],
            {"idx": 1, "expected": 12, "actual": 10, "delta": -2},
        )

    def test_diagnoses_reaccepted_stimulus_before_output_mismatch(self) -> None:
        log = """
        TRACE input_accept cycle=5 lane=0 idx=0 data=1
        TRACE input_accept cycle=5 lane=1 idx=0 data=4
        TRACE input_accept cycle=6 lane=0 idx=1 data=1
        TRACE input_accept cycle=6 lane=1 idx=1 data=4
        TRACE join_output cycle=7 idx=0 data=5
        TRACE acc_output cycle=8 idx=0 data=5
        TRACE output cycle=9 idx=0 expected=5 actual=5
        TRACE acc_output cycle=9 idx=1 data=10
        TRACE output cycle=10 idx=1 expected=12 actual=10
        """

        diagnosis = diagnose_semantic_trace(parse_semantic_trace(log))

        self.assertEqual(diagnosis["primary_issue"], "stimulus_reaccepted_while_valid_held")
        self.assertEqual(diagnosis["duplicate_input_accepts"][0], {"lane": 0, "data": 1, "first_cycle": 5, "repeat_cycle": 6})
        self.assertEqual(diagnosis["first_output_mismatch"]["actual"], 10)


if __name__ == "__main__":
    unittest.main()
