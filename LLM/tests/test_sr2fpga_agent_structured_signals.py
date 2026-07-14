import json
import tempfile
import unittest
from pathlib import Path

from LLM.src.sr2fpga_agent.agent import (
    _diagnose_first_failure,
    _expected_bram,
    _l4_open_record,
    _labels,
)
from LLM.src.sr2fpga_agent.log_parser import parse_test_fail_mismatches, parse_tool_warnings
from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ToolResult
from LLM.src.sr2fpga_agent.recorder import DatasetRecorder


class StructuredToolSignalTests(unittest.TestCase):
    def test_structured_mismatch_marker_takes_priority_over_legacy_test_fail(self) -> None:
        details = parse_test_fail_mismatches(
            'SR2FPGA_MISMATCH {"scenario_id":"stress_001","class":"stress",'
            '"item_index":3,"expected":"2a","actual":"29","ignored":"value"}\n'
            "TEST_FAIL signal=out_data cycle=17 expected=0x2a actual=0x29\n"
        )

        self.assertEqual(
            details,
            [
                {
                    "scenario_id": "stress_001",
                    "class": "stress",
                    "item_index": 3,
                    "expected": "2a",
                    "actual": "29",
                }
            ],
        )

    def test_malformed_structured_marker_falls_back_to_legacy_test_fail(self) -> None:
        details = parse_test_fail_mismatches(
            "SR2FPGA_MISMATCH {not-json}\n"
            "TEST_FAIL signal=out_data cycle=17 expected=42 actual=41\n"
        )

        self.assertEqual(
            details,
            [{"signal": "out_data", "cycle": 17, "expected": "42", "actual": "41"}],
        )

    def test_parser_extracts_test_fail_fields_without_inventing_missing_values(self) -> None:
        details = parse_test_fail_mismatches(
            "TEST_FAIL cycle=17 signal=out_data expected=0x2a actual=0x29\n"
            "TEST_FAIL expected count=1 actual=0\n"
            "TEST_FAIL expected count=4 got 252\n"
        )

        self.assertEqual(
            details,
            [
                {"signal": "out_data", "cycle": 17, "expected": "0x2a", "actual": "0x29"},
                {"expected": "count=1", "actual": "0"},
                {"expected": "count=4", "actual": "252"},
            ],
        )

    def test_parser_maps_verilator_warning_classes_to_failure_taxonomy(self) -> None:
        warnings = parse_tool_warnings(
            "%Warning-WIDTHTRUNC: rtl/top.v:8: truncated value\n"
            "%Warning-UNDRIVEN: rtl/top.v:9: Signal is not driven\n"
            "%Warning-LATCH: rtl/top.v:10: Latch inferred\n"
        )

        self.assertEqual(
            warnings,
            [
                {"warning_class": "WIDTHTRUNC", "failure_type": "width_mismatch"},
                {"warning_class": "UNDRIVEN", "failure_type": "undriven_signal"},
                {"warning_class": "LATCH", "failure_type": "latch_inferred"},
            ],
        )

    def test_yosys_warning_is_labeled_and_persisted_for_l3(self) -> None:
        synth = ToolResult(
            "synth",
            ["yosys"],
            "passed",
            0,
            "Warning: Wire top.unused is assigned but never used.\n",
            "",
            0.01,
        )
        labels = _labels(
            {"synth": synth},
            {"status": "not_run", "skip_reason": "disabled_by_config", "tool": "openxc7_nextpnr"},
            final_attempt_id=0,
            failure_count=0,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
            project = GeneratedProject(project_name="counter", files={"manifest.json": "{}\n"})
            recorder.start_sample("sample_l3_warnings", "Design a counter.", platform)
            recorder.write_final(
                "sample_l3_warnings",
                project,
                labels=labels,
                measured_qor={"lut": 1, "ff": 2, "bram": 0, "dsp": 0},
                tool_versions={},
                trajectory={"attempts": []},
            )
            trajectory = json.loads((root / "sample_l3_warnings/eval/trajectory.json").read_text(encoding="utf-8"))

        self.assertEqual(labels["l3_warnings"], [{"warning_class": "YOSYS", "failure_type": "unused_signal"}])
        self.assertEqual(trajectory["verification"]["l3"]["warnings"], labels["l3_warnings"])

    def test_failed_simulation_diagnosis_contains_structured_mismatch(self) -> None:
        diagnosis = _diagnose_first_failure(
            {
                "sim_run": ToolResult(
                    stage="sim_run",
                    command=["vvp", "sim.out"],
                    status="failed",
                    exit_code=1,
                    stdout="TEST_FAIL signal=out_data cycle=17 expected=42 actual=41\n",
                    stderr="",
                    duration_seconds=0.01,
                )
            }
        )

        self.assertEqual(diagnosis["failure_type"], "functional_mismatch")
        self.assertEqual(
            diagnosis["structured_diagnosis"]["mismatch_detail"],
            [{"signal": "out_data", "cycle": 17, "expected": "42", "actual": "41"}],
        )

    def test_l0_and_his_validation_diagnoses_include_structured_diagnosis(self) -> None:
        for stage, command, failure_type in (
            ("l0_consistency", "system_his_checker", "l0_contract_violation"),
            ("his_validation", "system_his_h_stage_validator", "his_validation_failed"),
        ):
            diagnosis = _diagnose_first_failure(
                {
                    stage: ToolResult(stage, [command], "failed", 1, "", "validation failed", 0.0),
                }
            )

            self.assertEqual(diagnosis["failure_type"], failure_type)
            self.assertEqual(diagnosis["structured_diagnosis"]["failure_type"], failure_type)
            self.assertEqual(diagnosis["structured_diagnosis"]["warnings"], [])

    def test_bram_miss_is_derived_from_prediction_and_zero_bram_synth_result(self) -> None:
        project = GeneratedProject(
            project_name="ram",
            files={
                "manifest.json": "{}\n",
                "reports/predicted_qor.json": '{"bram": 1}\n',
            },
        )
        labels = _labels(
            {"synth": ToolResult("synth", ["yosys"], "passed", 0, "Number of cells: 1\n  $lut 1\n", "", 0.01)},
            {"status": "not_run", "skip_reason": "disabled_by_config", "tool": "openxc7_nextpnr"},
            final_attempt_id=0,
            failure_count=0,
            expected_bram=_expected_bram(project),
        )

        self.assertEqual(_expected_bram(project), 1)
        self.assertTrue(labels["l3_bram_miss"])

    def test_labels_classify_open_and_commercial_l4_agreement(self) -> None:
        labels = _labels(
            {"synth": ToolResult("synth", ["yosys"], "passed", 0, "", "", 0.01)},
            {"status": "pass", "skip_reason": None, "tool": "openxc7_nextpnr"},
            final_attempt_id=0,
            failure_count=0,
            l4_commercial={"status": "pass", "skip_reason": None, "tool": "vivado"},
        )

        self.assertEqual(labels["l4_agreement_class"], "both_pass")
        self.assertEqual(labels["checks"]["l4_agreement_class"], "both_pass")

    def test_recorder_surfaces_structured_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
            project = GeneratedProject(project_name="counter", files={"manifest.json": "{}\n"})
            recorder.start_sample("sample_structured_signals", "Design a counter.", platform)
            recorder.write_final(
                "sample_structured_signals",
                project,
                labels={
                    "checks": {"l1_lint_pass": True, "l2_sim_pass": False, "l3_synth_pass": True},
                    "l1_warnings": [{"warning_class": "WIDTH", "failure_type": "width_mismatch"}],
                    "l2_mismatch_detail": [{"signal": "out_data", "expected": "42", "actual": "41"}],
                },
                measured_qor={"lut": 1, "ff": 2, "bram": 0, "dsp": 0},
                tool_versions={},
                trajectory={"attempts": []},
            )

            trajectory = json.loads((root / "sample_structured_signals/eval/trajectory.json").read_text(encoding="utf-8"))

        verification = trajectory["verification"]
        self.assertEqual(verification["l1"]["warnings"][0]["failure_type"], "width_mismatch")
        self.assertEqual(verification["l2_core"]["public"]["mismatch_detail"][0]["actual"], "41")

    def test_failed_l4_record_includes_failure_family(self) -> None:
        record = _l4_open_record(
            {
                "synth": ToolResult("synth", ["yosys"], "passed", 0, "", "", 0.01),
                "pnr": ToolResult(
                    "pnr",
                    ["openxc7_nextpnr"],
                    "failed",
                    1,
                    "",
                    "ERROR: constraint failed: no ports matched",
                    0.01,
                ),
            },
            enabled=True,
            attempt_id=0,
            tool="openxc7_nextpnr",
            board_profile="",
        )

        self.assertEqual(record["status"], "fail")
        self.assertEqual(record["failure_family"], "constraint_port_missing")


if __name__ == "__main__":
    unittest.main()
