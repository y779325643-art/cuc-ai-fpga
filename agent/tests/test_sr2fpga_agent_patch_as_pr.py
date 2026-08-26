import json
import tempfile
import unittest
from pathlib import Path

from sr2fpga_agent.models import GeneratedProject, PatchMetadata, PlatformProfile
from sr2fpga_agent.path_safety import build_patch_metadata, finalize_patch_metadata
from sr2fpga_agent.recorder import AttemptRecord, DatasetRecorder


class PatchAsPrTest(unittest.TestCase):
    def test_explicit_checker_scoreboard_and_uvm_directories_are_trusted(self) -> None:
        for path in (
            "sim/checkers/protocol.sv",
            "sim/scoreboards/stream.sv",
            "sim/uvm/stream_agent.sv",
            "tests/checkers/protocol.py",
            "verification/checkers/protocol.sv",
            "uvm/stream_agent.sv",
        ):
            metadata = build_patch_metadata(
                GeneratedProject("demo", {path: "before\n"}),
                GeneratedProject("demo", {path: "after\n"}),
                diagnosis={},
            )

            self.assertTrue(metadata.touched_trusted_artifacts, path)

    def test_rtl_names_containing_checker_scoreboard_or_uvm_remain_editable(self) -> None:
        for path in (
            "rtl/packet_checker.v",
            "rtl/scoreboard_counter.v",
            "rtl/uvm_adapter.v",
            "rtl/checkers/protocol.v",
            "rtl/scoreboards/counter.v",
            "rtl/uvm/adapter.v",
        ):
            old = "module core(input wire a, output wire y); assign y = a; endmodule\n"
            new = "module core(input wire a, output wire y); assign y = ~a; endmodule\n"
            metadata = build_patch_metadata(
                GeneratedProject("demo", {path: old}),
                GeneratedProject("demo", {path: new}),
                diagnosis={},
            )

            self.assertEqual(metadata.status, "valid", path)
            self.assertFalse(metadata.touched_trusted_artifacts, path)

    def test_oracle_bundle_and_runtime_source_patches_are_trusted(self) -> None:
        for path in (
            "oracle/manifest.json",
            "attempts/attempt_000/eval/oracle/hidden/case/input.memh",
            "agent/src/sr2fpga_agent/oracles/types.py",
        ):
            metadata = build_patch_metadata(
                GeneratedProject("demo", {path: "before\n"}),
                GeneratedProject("demo", {path: "after\n"}),
                diagnosis={},
            )

            self.assertEqual(metadata.status, "invalid_edit_surface", path)
            self.assertTrue(metadata.touched_trusted_artifacts, path)
            self.assertFalse(metadata.automatic_pass_credit, path)

    def test_oracle_trusted_path_matching_normalizes_windows_separators(self) -> None:
        path = "attempts\\attempt_000\\eval\\oracle\\manifest.json"
        metadata = build_patch_metadata(
            GeneratedProject("demo", {path: "before\n"}),
            GeneratedProject("demo", {path: "after\n"}),
            diagnosis={},
        )

        self.assertTrue(metadata.touched_trusted_artifacts)

    def test_legacy_rtl_patch_cannot_change_module_interface(self) -> None:
        old = GeneratedProject(
            "demo",
            {"rtl/top.v": "module top(input wire a, output wire y);\nassign y = a;\nendmodule\n"},
        )
        new = GeneratedProject(
            "demo",
            {
                "rtl/top.v": (
                    "module top(input wire a, input wire b, output wire y);\n"
                    "assign y = a & b;\n"
                    "endmodule\n"
                )
            },
        )

        metadata = build_patch_metadata(old, new, diagnosis={})

        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertFalse(metadata.allowed_edit_regions_respected)
        self.assertFalse(metadata.touched_trusted_artifacts)

    def test_legacy_rtl_l0_repair_may_change_module_interface(self) -> None:
        old = GeneratedProject(
            "demo",
            {"rtl/top.v": "module top(input wire [6:0] a, output wire y); assign y = a[0]; endmodule\n"},
        )
        new = GeneratedProject(
            "demo",
            {"rtl/top.v": "module top(input wire [7:0] a, output wire y); assign y = a[0]; endmodule\n"},
        )

        metadata = build_patch_metadata(old, new, diagnosis={"stage": "l0_consistency"})

        self.assertEqual(metadata.status, "valid")
        self.assertTrue(metadata.allowed_edit_regions_respected)
        self.assertFalse(metadata.automatic_pass_credit)

    def test_legacy_rtl_patch_cannot_add_a_new_source_file(self) -> None:
        old = GeneratedProject("demo", {"rtl/top.v": "module top; endmodule\n"})
        new = GeneratedProject(
            "demo",
            {
                "rtl/top.v": "module top; endmodule\n",
                "rtl/helper.v": "module helper; endmodule\n",
            },
        )

        metadata = build_patch_metadata(old, new, diagnosis={})

        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertFalse(metadata.allowed_edit_regions_respected)

    def test_legacy_rtl_patch_requires_a_parseable_module_interface(self) -> None:
        metadata = build_patch_metadata(
            GeneratedProject("demo", {"rtl/top.v": "// malformed generated RTL\n"}),
            GeneratedProject("demo", {"rtl/top.v": "// arbitrary replacement\n"}),
            diagnosis={},
        )

        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertFalse(metadata.allowed_edit_regions_respected)

    def test_contract_skeleton_patch_may_change_only_behavior_region(self) -> None:
        old_body = (
            "module core(input wire a, output wire y);\n"
            "  // SR2FPGA_BEHAVIOR_BEGIN\n"
            "  assign y = a;\n"
            "  // SR2FPGA_BEHAVIOR_END\n"
            "endmodule\n"
        )
        new_body = old_body.replace("assign y = a;", "assign y = ~a;")

        metadata = build_patch_metadata(
            GeneratedProject("demo", {"rtl/core.v": old_body}),
            GeneratedProject("demo", {"rtl/core.v": new_body}),
            diagnosis={},
        )

        self.assertEqual(metadata.status, "valid")
        self.assertTrue(metadata.allowed_edit_regions_respected)

    def test_contract_skeleton_patch_cannot_change_content_outside_behavior_region(self) -> None:
        old_body = (
            "module core(input wire a, output wire y);\n"
            "  wire deterministic_wire = a;\n"
            "  // SR2FPGA_BEHAVIOR_BEGIN\n"
            "  assign y = deterministic_wire;\n"
            "  // SR2FPGA_BEHAVIOR_END\n"
            "endmodule\n"
        )
        new_body = old_body.replace("wire deterministic_wire = a;", "wire deterministic_wire = ~a;")

        metadata = build_patch_metadata(
            GeneratedProject("demo", {"rtl/core.v": old_body}),
            GeneratedProject("demo", {"rtl/core.v": new_body}),
            diagnosis={},
        )

        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertFalse(metadata.allowed_edit_regions_respected)

    def test_contract_skeleton_patch_cannot_change_unmarked_top_shell(self) -> None:
        marked_core = (
            "module core(input wire a, output wire y);\n"
            "  // SR2FPGA_BEHAVIOR_BEGIN\n"
            "  assign y = a;\n"
            "  // SR2FPGA_BEHAVIOR_END\n"
            "endmodule\n"
        )
        old = GeneratedProject(
            "demo",
            {
                "rtl/core.v": marked_core,
                "rtl/top.v": "module top(input wire a, output wire y); core u_core(a, y); endmodule\n",
            },
        )
        new = GeneratedProject(
            "demo",
            {
                "rtl/core.v": marked_core,
                "rtl/top.v": "module top(input wire a, output wire y); assign y = a; endmodule\n",
            },
        )

        metadata = build_patch_metadata(old, new, diagnosis={})

        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertFalse(metadata.allowed_edit_regions_respected)

    def test_trusted_testbench_patch_is_invalid_without_automatic_credit(self) -> None:
        metadata = build_patch_metadata(
            GeneratedProject("demo", {"sim/tb_top.v": "module tb; endmodule\n"}),
            GeneratedProject("demo", {"sim/tb_top.v": "module tb; initial $finish; endmodule\n"}),
            diagnosis={"diagnosis_id": "d002"},
            patch_id="p003",
        )

        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertTrue(metadata.touched_trusted_artifacts)
        self.assertFalse(metadata.allowed_edit_regions_respected)
        self.assertFalse(metadata.automatic_pass_credit)

    def test_golden_model_and_hidden_test_patches_are_invalid(self) -> None:
        metadata = build_patch_metadata(
            GeneratedProject("demo", {"models/golden.py": "return 0\n", "tests/hidden/case.py": "assert 0\n"}),
            GeneratedProject("demo", {"models/golden.py": "return 1\n", "tests/hidden/case.py": "assert 1\n"}),
            diagnosis={},
        )

        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertTrue(metadata.touched_trusted_artifacts)
        self.assertEqual(metadata.files_touched, ["models/golden.py", "tests/hidden/case.py"])

    def test_rtl_only_patch_is_pending_without_automatic_credit(self) -> None:
        metadata = build_patch_metadata(
            GeneratedProject("demo", {"rtl/top.v": "module top; endmodule\n"}),
            GeneratedProject("demo", {"rtl/top.v": "module top; assign out = 1'b0; endmodule\n"}),
            diagnosis={
                "diagnosis_id": "d002",
                "expected_effect": "hold payload stable",
                "tool_result_before": {"lint": "passed", "sim_run": "failed"},
            },
            patch_id="p003",
        )

        self.assertEqual(metadata.patch_id, "p003")
        self.assertEqual(metadata.diagnosis_id, "d002")
        self.assertEqual(metadata.files_touched, ["rtl/top.v"])
        self.assertTrue(metadata.allowed_edit_regions_respected)
        self.assertFalse(metadata.touched_trusted_artifacts)
        self.assertFalse(metadata.automatic_pass_credit)
        self.assertEqual(metadata.expected_effect, "hold payload stable")
        self.assertEqual(metadata.tool_result_before["sim_run"], "failed")
        self.assertEqual(metadata.tool_result_after, {})
        self.assertFalse(metadata.repair_regression["hidden_tests_preserved"])

    def test_constraints_patch_is_invalid_without_automatic_credit(self) -> None:
        metadata = build_patch_metadata(
            GeneratedProject("demo", {"constraints/timing.sdc": "create_clock -period 10 [get_ports clk]\n"}),
            GeneratedProject("demo", {"constraints/timing.sdc": "create_clock -period 20 [get_ports clk]\n"}),
            diagnosis={},
        )

        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertTrue(metadata.touched_trusted_artifacts)
        self.assertFalse(metadata.automatic_pass_credit)

    def test_noop_patch_is_invalid_without_automatic_credit(self) -> None:
        project = GeneratedProject("demo", {"rtl/top.v": "module top; endmodule\n"})
        metadata = build_patch_metadata(
            project,
            project,
            diagnosis={"stage": "sim_run", "tool_result_before": {"sim_run": "failed"}},
        )

        self.assertEqual(metadata.files_touched, [])
        self.assertEqual(metadata.status, "invalid_edit_surface")
        self.assertFalse(metadata.allowed_edit_regions_respected)
        self.assertFalse(metadata.automatic_pass_credit)

    def test_finalize_patch_with_failed_target_or_regression_loses_credit(self) -> None:
        pending = build_patch_metadata(
            GeneratedProject("demo", {"rtl/top.v": "module top; endmodule\n"}),
            GeneratedProject("demo", {"rtl/top.v": "module top; wire x; endmodule\n"}),
            diagnosis={"stage": "sim_run", "tool_result_before": {"lint": "passed", "sim_run": "failed"}},
        )

        finalized = finalize_patch_metadata(pending, {"lint": "failed", "sim_run": "failed"})

        self.assertFalse(finalized.automatic_pass_credit)
        self.assertEqual(finalized.regressions, ["lint"])
        self.assertFalse(finalized.repair_regression["fixed_target"])
        self.assertFalse(finalized.repair_regression["hidden_tests_preserved"])

    def test_recorder_persists_structured_patch_metadata_and_exports_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
            recorder.start_sample("sample_patch", "repair this", platform)
            patch = PatchMetadata(
                patch_id="p001",
                format="unified_diff",
                diagnosis_id="d001",
                files_touched=["rtl/top.v"],
                allowed_edit_regions_respected=True,
                expected_effect="fix reset",
                tool_result_before={"lint": "passed", "sim_run": "failed"},
                tool_result_after={"lint": "passed", "sim_run": "passed"},
                regressions=[],
                touched_trusted_artifacts=False,
                status="valid",
                automatic_pass_credit=True,
                repair_regression={
                    "target_failure": "sim_run",
                    "fixed_target": True,
                    "regressed_levels": [],
                    "regressed_scenarios": [],
                    "hidden_tests_preserved": True,
                },
            )
            project = GeneratedProject("demo", {"rtl/top.v": "module top; endmodule\n"})
            recorder.write_attempt(
                "sample_patch",
                AttemptRecord(
                    attempt_id=0,
                    generated_project=project,
                    tool_results={},
                    diagnosis={"diagnosis_id": "d001"},
                    patch_diff="--- a/rtl/top.v\n+++ b/rtl/top.v\n",
                    patch_metadata=patch,
                ),
            )
            recorder.write_final(
                "sample_patch",
                project,
                labels={"pass_level": "L2", "checks": {}},
                measured_qor={},
                tool_versions={},
                trajectory={"sample_id": "sample_patch", "attempts": [], "patches": [patch.to_dict()]},
            )
            exports = Path(tmp) / "exports"
            recorder.export_training_views(exports)

            saved = json.loads((root / "sample_patch/attempts/attempt_000/patch.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["tool_result_after"]["sim_run"], "passed")
            row = json.loads((exports / "failure_to_patch.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["patch_metadata"]["repair_regression"]["fixed_target"], True)
