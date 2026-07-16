import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from LLM.src.sr2fpga_agent import GeneratedProject, PlatformProfile, ProjectGenerator, ProjectRequest
from LLM.src.sr2fpga_agent.agent import DataGenerationAgent, RepairResult
from LLM.src.sr2fpga_agent.failure_injector import FailureInjectingProjectGenerator
from LLM.src.sr2fpga_agent.models import RepairResult as ModelRepairResult
from LLM.src.sr2fpga_agent.models import ToolResult
from LLM.src.sr2fpga_agent.oracles import OracleField, OracleScenarioSpec, write_oracle_bundle
from LLM.src.sr2fpga_agent.recorder import (
    AttemptRecord,
    DatasetRecorder,
    _sanitize_oracle_profile,
    _sanitize_training_payload,
    _write_jsonl,
)
from LLM.src.sr2fpga_agent.system_his_checker import check_project_l0


def _write_four_class_oracle_bundle(width: int, output_root: Path):
    field = OracleField("sample", width - 1, 0, False)
    scenarios = tuple(
        OracleScenarioSpec(
            scenario_id=f"{scenario_class}_001",
            scenario_class=scenario_class,
            seed=index + 11,
            input_record_width_bits=width,
            expected_record_width_bits=width,
            input_fields=(field,),
            expected_fields=(field,),
            input_records=(index + 1,),
            expected_records=(index + 1,),
        )
        for index, scenario_class in enumerate(
            ("public_smoke", "hidden_deterministic", "randomized_fixed_seed", "stress")
        )
    )
    return write_oracle_bundle(
        root=output_root,
        family_id="fir_filter",
        reference_model="numeric.fir_filter",
        reference_version="1",
        task_parameters={"width": width},
        scenarios=scenarios,
    )


class DatasetRecorderTest(unittest.TestCase):
    def test_oracle_profile_export_uses_strict_fail_closed_schema(self) -> None:
        valid_sha256 = "a" * 64
        profile = _sanitize_oracle_profile(
            {
                "kind": "python_reference/../../private",
                "status": "pass\nD:/private/oracle",
                "family_id": "fir/filter",
                "reference_model": "numeric.fir_filter",
                "reference_version": "1.0",
                "bundle_sha256": f"D:/private/{valid_sha256}",
                "skip_reason": "blocked_before_oracle",
                "failure_origin": "oracle_environment_failure",
                "failure_type": "oracle_bundle_invalid",
                "scenario_counts": {
                    "public_smoke": 1,
                    "stress": -1,
                    "hidden_deterministic": True,
                    "../../private": 4,
                },
                "class_status": {
                    "public_smoke": "pass",
                    "stress": "D:/private/status",
                    "../../private": "pass",
                },
                "scenarios": [
                    {
                        "scenario_id": "public_001",
                        "scenario_class": "public_smoke",
                        "transaction_count": 1,
                        "input_record_width_bits": 8,
                        "expected_record_width_bits": 8,
                        "input_sha256": valid_sha256,
                        "expected_sha256": valid_sha256,
                    },
                    {
                        "scenario_id": "D:/private/scenario",
                        "scenario_class": "public_smoke/../../hidden",
                    },
                ],
            }
        )

        self.assertEqual(profile["kind"], "python_reference")
        self.assertEqual(profile["status"], "not_run")
        self.assertNotIn("family_id", profile)
        self.assertNotIn("bundle_sha256", profile)
        self.assertEqual(profile["reference_model"], "numeric.fir_filter")
        self.assertEqual(profile["scenario_counts"], {"public_smoke": 1})
        self.assertEqual(profile["class_status"], {"public_smoke": "pass"})
        self.assertEqual(len(profile["scenarios"]), 1)
        self.assertEqual(profile["scenarios"][0]["input_sha256"], valid_sha256)
        self.assertNotIn("D:/private", json.dumps(profile))

    def test_independent_oracle_episode_does_not_reuse_label_mismatch_detail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter"),
                platform,
            )
            sample_id = "sample_oracle_label_bypass"
            recorder.start_sample(sample_id, "Design a counter.", platform)
            recorder.write_final(
                sample_id,
                project,
                labels={
                    "pass_level": "L2",
                    "checks": {"l2_sim_pass": True},
                    "l2_mismatch_detail": [
                        {
                            "scenario_class": "public_smoke",
                            "expected": "HIDDEN_LABEL_EXPECTED",
                            "actual": "HIDDEN_LABEL_ACTUAL",
                            "raw_path": "D:/private/hidden-label.memh",
                        }
                    ],
                },
                measured_qor={},
                tool_versions={},
                trajectory={
                    "oracle_profile": {
                        "kind": "python_reference",
                        "status": "pass",
                        "bundle_sha256": "b" * 64,
                    }
                },
            )

            trajectory = json.loads(
                (root / sample_id / "eval/trajectory.json").read_text(encoding="utf-8")
            )
            self.assertEqual(trajectory["verification"]["l2_core"]["public"]["mismatch_detail"], [])
            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)
            exported = "\n".join(path.read_text(encoding="utf-8") for path in export_dir.glob("*.jsonl"))
            self.assertNotIn("HIDDEN_LABEL_EXPECTED", exported)
            self.assertNotIn("HIDDEN_LABEL_ACTUAL", exported)
            self.assertNotIn("hidden-label.memh", exported)

    def test_independent_oracle_diagnosis_is_public_only_and_fail_closed(self) -> None:
        nested = {
            "stage": "sim_run",
            "failure_type": "functional_mismatch",
            "root_cause": "D:/private/hidden.memh expected=HIDDEN_ROOT_VALUE",
            "public": {
                "scenario_class": "public_smoke",
                "structured_diagnosis": {
                    "signal": "public_out",
                    "expected": "PUBLIC_EXPECTED",
                    "actual": "PUBLIC_ACTUAL",
                    "root_cause": "PUBLIC_RAW_LOG_SHOULD_DROP",
                },
            },
            "hidden": {
                "scenario_class": "hidden_deterministic",
                "expected": "HIDDEN_EXPECTED",
                "actual": "HIDDEN_ACTUAL",
                "payload": [1, 2],
                "raw_path": "D:/private/hidden-input.memh",
            },
            "invalid": {
                "scenario_class": "public_smoke/../../hidden",
                "root_cause": "INVALID_CLASS_SECRET",
            },
            "tuple_wrapper": (
                {
                    "scenario_class": "stress",
                    "seed": 998877,
                    "stdout": "TUPLE_HIDDEN_STDOUT",
                },
            ),
        }
        directly_sanitized = _sanitize_training_payload(nested, independent_oracle=True)
        direct_text = json.dumps(directly_sanitized)
        self.assertIn("PUBLIC_EXPECTED", direct_text)
        self.assertNotIn("HIDDEN_ROOT_VALUE", direct_text)
        self.assertNotIn("TUPLE_HIDDEN_STDOUT", direct_text)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter"),
                platform,
            )
            sample_id = "sample_oracle_diagnosis_bypass"
            recorder.start_sample(sample_id, "Design a counter.", platform)
            recorder.write_final(
                sample_id,
                project,
                labels={"pass_level": "L2", "checks": {"l2_sim_pass": False}},
                measured_qor={},
                tool_versions={},
                trajectory={
                    "oracle_profile": {
                        "kind": "python_reference",
                        "status": "fail",
                        "bundle_sha256": "c" * 64,
                    }
                },
            )
            attempt_dir = root / sample_id / "attempts/attempt_000"
            attempt_dir.mkdir(parents=True)
            (attempt_dir / "diagnosis.json").write_text(json.dumps(nested) + "\n", encoding="utf-8")
            (attempt_dir / "patch.diff").write_text("--- a/rtl/top.v\n+++ b/rtl/top.v\n", encoding="utf-8")
            (attempt_dir / "patch.json").write_text(
                json.dumps({"diagnosis": nested, "status": "valid"}) + "\n",
                encoding="utf-8",
            )

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)
            diagnosis_text = (export_dir / "failure_to_diagnosis.jsonl").read_text(encoding="utf-8")
            patch_text = (export_dir / "failure_to_patch.jsonl").read_text(encoding="utf-8")
            combined = diagnosis_text + patch_text
            self.assertIn("PUBLIC_EXPECTED", combined)
            self.assertIn("PUBLIC_ACTUAL", combined)
            self.assertIn("functional_mismatch", combined)
            for secret in (
                "HIDDEN_ROOT_VALUE",
                "HIDDEN_EXPECTED",
                "HIDDEN_ACTUAL",
                "hidden-input.memh",
                "INVALID_CLASS_SECRET",
                "PUBLIC_RAW_LOG_SHOULD_DROP",
                "998877",
                "TUPLE_HIDDEN_STDOUT",
            ):
                self.assertNotIn(secret, combined)

    def test_oracle_diagnosis_trust_scope_cannot_upgrade_below_untrusted_parent(self) -> None:
        sanitized = _sanitize_training_payload(
            {
                "legal_public_sibling": {
                    "scenario_class": "public_smoke",
                    "expected": "PUBLIC_EXPECTED_SURVIVES",
                    "actual": "PUBLIC_ACTUAL_SURVIVES",
                },
                "unknown_parent": {
                    "nested_public_claim": {
                        "scenario_class": "public_smoke",
                        "expected": "HIDDEN_EXPECTED_MUST_DROP",
                        "actual": "HIDDEN_ACTUAL_MUST_DROP",
                    }
                },
            },
            independent_oracle=True,
        )
        exported = json.dumps(sanitized)

        self.assertIn("PUBLIC_EXPECTED_SURVIVES", exported)
        self.assertIn("PUBLIC_ACTUAL_SURVIVES", exported)
        self.assertNotIn("HIDDEN_EXPECTED_MUST_DROP", exported)
        self.assertNotIn("HIDDEN_ACTUAL_MUST_DROP", exported)

    def test_write_final_and_exports_remove_withheld_oracle_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter"),
                platform,
            )
            recorder.start_sample("sample_oracle_sanitize", "Design a counter.", platform)
            malformed_profile = {
                "kind": "python_reference",
                "bundle_sha256": "bundle-digest",
                "raw_evaluator_path": "D:/private/oracle/hidden/input.memh",
                "scenarios": [
                    {
                        "scenario_id": "hidden_001",
                        "scenario_class": "hidden_deterministic",
                        "seed": 424242,
                        "seed_sha256": "a" * 64,
                        "input_path": "hidden/input.memh",
                        "expected_path": "hidden/expected.memh",
                        "input_sha256": "input-digest",
                        "expected_sha256": "expected-digest",
                        "input_records": [1, 2],
                        "expected_records": [3, 4],
                    }
                ],
            }
            recorder.write_final(
                "sample_oracle_sanitize",
                project,
                labels={"pass_level": "L2", "checks": {"l2_sim_pass": True}},
                measured_qor={},
                tool_versions={},
                trajectory={"oracle_profile": malformed_profile},
            )

            trajectory_text = (root / "sample_oracle_sanitize/eval/trajectory.json").read_text(encoding="utf-8")
            trajectory = json.loads(trajectory_text)
            hidden = trajectory["oracle_profile"]["scenarios"][0]
            for key in (
                "seed",
                "input_path",
                "expected_path",
                "input_sha256",
                "expected_sha256",
                "input_records",
                "expected_records",
            ):
                self.assertNotIn(key, hidden)
            self.assertEqual(hidden["seed_sha256"], "a" * 64)
            self.assertNotIn("raw_evaluator_path", trajectory["oracle_profile"])

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)
            exported = "\n".join(path.read_text(encoding="utf-8") for path in export_dir.glob("*.jsonl"))
            self.assertNotIn("424242", exported)
            self.assertIn("a" * 64, exported)
            self.assertNotIn("D:/private/oracle", exported)
            self.assertNotIn("hidden/input.memh", exported)

    def test_training_exports_deeply_redact_withheld_diagnostics_but_keep_public_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter"),
                platform,
            )
            sample_id = "sample_nested_oracle_secrets"
            recorder.start_sample(sample_id, "Design a counter.", platform)
            recorder.write_final(
                sample_id,
                project,
                labels={"pass_level": "L1", "checks": {"l1_lint_pass": True}},
                measured_qor={},
                tool_versions={},
                trajectory={},
            )
            attempt_dir = root / sample_id / "attempts/attempt_000"
            attempt_dir.mkdir(parents=True)
            malicious = {
                "public": {
                    "scenario_class": "public_smoke",
                    "structured_diagnosis": {"signal": "public_out", "cycle": 3, "failure_type": "mismatch"},
                },
                "hidden": {
                    "scenario_class": "hidden_deterministic",
                    "nested": [
                        {
                            "seed": 987654,
                            "raw_path": "D:/private/hidden/input.memh",
                            "payload": [1, 2],
                            "expected": 7,
                            "actual": 6,
                            "stdout": "HIDDEN_STDOUT_TOKEN",
                            "command": ["vvp", "+ORACLE_INPUT=secret.memh"],
                            "deeper": ({"input_sha256": "HIDDEN_HASH_TOKEN"},),
                        }
                    ],
                    "failure_type": "functional_mismatch",
                    "signal": "hidden_out",
                },
            }
            (attempt_dir / "diagnosis.json").write_text(json.dumps(malicious) + "\n", encoding="utf-8")
            (attempt_dir / "patch.diff").write_text("--- a/rtl/top.v\n+++ b/rtl/top.v\n", encoding="utf-8")
            (attempt_dir / "patch.json").write_text(
                json.dumps({"diagnosis": malicious, "status": "valid"}) + "\n",
                encoding="utf-8",
            )

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)
            diagnosis_text = (export_dir / "failure_to_diagnosis.jsonl").read_text(encoding="utf-8")
            patch_text = (export_dir / "failure_to_patch.jsonl").read_text(encoding="utf-8")
            combined = diagnosis_text + patch_text

            self.assertIn("public_out", combined)
            self.assertIn("functional_mismatch", combined)
            for secret in (
                "987654",
                "D:/private/hidden/input.memh",
                "HIDDEN_STDOUT_TOKEN",
                "HIDDEN_HASH_TOKEN",
                "+ORACLE_INPUT=secret.memh",
                '"expected": 7',
                '"actual": 6',
            ):
                self.assertNotIn(secret, combined)

    def test_write_jsonl_replaces_existing_file_without_opening_target_for_truncate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "exports" / "his_to_project.jsonl"
            output_path.parent.mkdir(parents=True)
            output_path.write_text('{"old": true}\n', encoding="utf-8")
            original_open = Path.open

            def guarded_open(path: Path, mode: str = "r", *args, **kwargs):
                if path == output_path and "w" in mode:
                    raise OSError(22, "Invalid argument", str(path))
                return original_open(path, mode, *args, **kwargs)

            with mock.patch.object(Path, "open", guarded_open):
                _write_jsonl(output_path, [{"new": True}])

            self.assertEqual(output_path.read_text(encoding="utf-8"), '{"new": true}\n')

    def test_write_final_replaces_previous_generated_project_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                platform,
            )
            sample_dir = recorder.start_sample("sample_replace_snapshot", "Design a counter.", platform)
            stale_file = sample_dir / "final/generated_project/rtl/stale.v"
            stale_file.parent.mkdir(parents=True, exist_ok=True)
            stale_file.write_text("module stale; endmodule\n", encoding="utf-8")

            recorder.write_final(
                "sample_replace_snapshot",
                project,
                labels={"pass_level": "L3", "checks": {"l3_synth_pass": True}},
                measured_qor={"lut": 1, "ff": 8},
                tool_versions={},
                trajectory={"attempts": []},
            )

            self.assertFalse(stale_file.exists())
            self.assertTrue((sample_dir / "final/generated_project/reports/predicted_qor.json").exists())
            self.assertTrue((sample_dir / "final/generated_project/sim/tb_top.v").exists())

    def test_write_attempt_preserves_tool_outputs_created_in_project_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                platform,
            )
            sample_dir = recorder.start_sample("sample_attempt_outputs", "Design a counter.", platform)
            routed_design = sample_dir / "attempts/attempt_000/generated_project/eval/openxc7_routed.json"
            routed_design.parent.mkdir(parents=True, exist_ok=True)
            routed_design.write_text('{"routed": true}\n', encoding="utf-8")

            recorder.write_attempt(
                "sample_attempt_outputs",
                AttemptRecord(attempt_id=0, generated_project=project, tool_results={}),
            )

            self.assertEqual(routed_design.read_text(encoding="utf-8"), '{"routed": true}\n')
            self.assertTrue((sample_dir / "attempts/attempt_000/generated_project/rtl/top.v").exists())

    def test_start_sample_rejects_unsafe_sample_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            with self.assertRaisesRegex(ValueError, "unsafe sample_id"):
                recorder.start_sample("../escape", "Design a counter.", platform)

            self.assertFalse((Path(tmp) / "datasets" / "escape").exists())

    def test_write_attempt_rejects_unsafe_project_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            recorder.start_sample("sample_safe", "Design a counter.", platform)
            project = GeneratedProject(
                project_name="unsafe",
                files={"../escape.v": "module escape; endmodule\n"},
            )

            with self.assertRaisesRegex(ValueError, "unsafe project file path"):
                recorder.write_attempt(
                    "sample_safe",
                    AttemptRecord(attempt_id=0, generated_project=project, tool_results={}),
                )

            self.assertFalse((root / "sample_safe" / "attempts" / "escape.v").exists())

    def test_records_attempt_final_outputs_and_training_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            requirement = "Design an 8-bit counter with enable and active-low reset."
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                platform,
            )

            metadata = {
                "source": "deepseek",
                "generator_provider": "deepseek",
                "failure_origin": "natural_llm",
                "difficulty_tier": "T2",
                "measurement_point": "a_first_attempt_no_tools",
                "repair_provider": "none",
                "failure_injectors": [],
                "system_his_schema_version": "system-his-v1.1",
            }
            sample_dir = recorder.start_sample("sample_000001", requirement, platform, metadata=metadata)
            attempt = AttemptRecord(
                attempt_id=0,
                generated_project=project,
                tool_results={
                    "lint": ToolResult(
                        stage="lint",
                        command=["verilator", "--lint-only", "rtl/top.v"],
                        status="failed",
                        exit_code=1,
                        stdout="",
                        stderr="Port rst_n of module top is not declared",
                        duration_seconds=0.1,
                    )
                },
                diagnosis={
                    "failure_type": "port_mismatch",
                    "root_cause": "The testbench and RTL disagree on the reset port.",
                    "affected_files": ["rtl/top.v", "sim/tb_top.v"],
                },
                patch_diff="diff --git a/sim/tb_top.v b/sim/tb_top.v\n",
            )
            recorder.write_attempt("sample_000001", attempt)
            labels = {
                "pass_level": "L3",
                "checks": {
                    "l0_complete": True,
                    "l1_lint_pass": True,
                    "l2_sim_pass": True,
                    "l3_synth_pass": True,
                    "l4_lite_timing_pass": False,
                },
                "final_attempt_id": 1,
                "failure_count": 1,
            }
            measured_qor = {"lut": 4, "ff": 8, "bram": 0, "dsp": 0}
            trajectory = {
                "sample_id": "sample_000001",
                "attempts": [
                    {
                        "attempt_id": 0,
                        "stage": "lint",
                        "status": "failed",
                        "failure_type": "port_mismatch",
                        "patch_path": "attempts/attempt_000/patch.diff",
                    }
                ],
            }
            recorder.write_final(
                "sample_000001",
                project,
                labels=labels,
                measured_qor=measured_qor,
                tool_versions={"verilator": "not-installed"},
                trajectory=trajectory,
            )
            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            self.assertEqual(sample_dir, root / "sample_000001")
            self.assertEqual((sample_dir / "requirement.txt").read_text(encoding="utf-8"), requirement + "\n")
            self.assertTrue((sample_dir / "platform_profile.json").exists())
            self.assertTrue((sample_dir / "attempts/attempt_000/generated_project/rtl/top.v").exists())
            self.assertIn(
                "rst_n",
                (sample_dir / "attempts/attempt_000/eval/lint.log").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))[
                    "failure_type"
                ],
                "port_mismatch",
            )
            self.assertTrue((sample_dir / "attempts/attempt_000/patch.diff").exists())
            self.assertTrue((sample_dir / "final/generated_project/manifest.json").exists())
            self.assertEqual(json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8")), labels)
            self.assertEqual(
                json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))["ff"],
                8,
            )
            self.assertTrue((sample_dir / "eval/trajectory.json").exists())
            saved_trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(saved_trajectory["verification"]["l4_open"]["status"], "not_run")
            self.assertEqual(
                saved_trajectory["derived_training_views"]["req2file"],
                {
                    "available": True,
                    "official_eval_unit": False,
                    "standalone_pass_credit": False,
                    "source_episode_id": "sample_000001",
                },
            )
            self.assertEqual(json.loads((sample_dir / "metadata.json").read_text(encoding="utf-8")), metadata)

            requirement_rows = (export_dir / "requirement_to_his.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(requirement_rows), 1)
            requirement_row = json.loads(requirement_rows[0])
            self.assertEqual(requirement_row["sample_id"], "sample_000001")
            self.assertIn("system_his", requirement_row)
            self.assertEqual(requirement_row["metadata"]["failure_origin"], "natural_llm")
            self.assertEqual(requirement_row["metadata"]["training_split"], "quarantine")

            file_rows = (export_dir / "requirement_to_file.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertGreaterEqual(len(file_rows), 6)
            file_row = json.loads(file_rows[0])
            self.assertEqual(file_row["sample_id"], "sample_000001")
            self.assertEqual(file_row["requirement"], requirement)
            self.assertIn("file_path", file_row)
            self.assertIn("file_content", file_row)
            self.assertEqual(file_row["source_episode_id"], "sample_000001")
            self.assertEqual(file_row["view"], "req2file")
            self.assertFalse(file_row["official_eval_unit"])
            self.assertFalse(file_row["standalone_pass_credit"])
            self.assertEqual(file_row["metadata"]["difficulty_tier"], "T2")

            patch_rows = (export_dir / "failure_to_patch.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(patch_rows), 1)
            patch_row = json.loads(patch_rows[0])
            self.assertEqual(patch_row["diagnosis"]["failure_type"], "port_mismatch")
            self.assertIn("diff --git", patch_row["patch"])

            for export_name in (
                "his_to_project.jsonl",
                "requirement_to_project.jsonl",
                "failure_to_diagnosis.jsonl",
                "project_to_predicted_qor.jsonl",
                "project_to_measured_qor.jsonl",
            ):
                rows = (export_dir / export_name).read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(rows), 1, export_name)
                self.assertEqual(json.loads(rows[0])["sample_id"], "sample_000001")
                self.assertEqual(json.loads(rows[0])["metadata"]["difficulty_tier"], "T2")

    def test_predicted_qor_rows_exclude_verification_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                platform,
            )
            recorder.start_sample(
                "sample_qor_leak",
                "Design an 8-bit counter.",
                platform,
                metadata={"system_his_schema_version": "system-his-v1.2"},
            )
            recorder.write_final(
                "sample_qor_leak",
                project,
                labels={"pass_level": "L3", "checks": {"l3_synth_pass": True}},
                measured_qor={"lut": 99, "ff": 12},
                tool_versions={},
                trajectory={"attempts": []},
            )

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            row = json.loads((export_dir / "project_to_predicted_qor.jsonl").read_text(encoding="utf-8"))
            self.assertNotIn("verification", row["episode"])
            self.assertNotIn("measured_qor", row["episode"])

    def test_behavior_hole_count_no_double_count(self) -> None:
        from LLM.src.sr2fpga_agent.recorder import _behavior_hole_count

        self.assertEqual(_behavior_hole_count("  // BEHAVIOR_HOLE: model-generated RTL behavior goes here."), 1)
        self.assertEqual(_behavior_hole_count("  // __BEHAVIOR_HOLE__"), 1)
        self.assertEqual(_behavior_hole_count("  // __BEHAVIOR_HOLE__\n  // __BEHAVIOR_HOLE__"), 2)

    def test_project_metadata_marks_predicted_qor_as_model_generated_for_llm_source(self) -> None:
        from LLM.src.sr2fpga_agent.recorder import _project_episode_metadata

        project = GeneratedProject(
            project_name="llm_project",
            files={
                "system_his.json": "{}\n",
                "manifest.json": "{}\n",
                "rtl/top.v": "module top; endmodule\n",
                "reports/predicted_qor.json": "{\"lut\": 10}\n",
            },
        )

        metadata = _project_episode_metadata(project)

        self.assertEqual(metadata["files"]["reports/predicted_qor.json"]["origin"], "model_generated")
        self.assertIn("reports/predicted_qor.json", metadata["model_generated_artifacts"])

    def test_l0_checker_rejects_manifest_that_violates_system_his_contract(self) -> None:
        platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            platform,
        )
        broken_files = dict(project.files)
        manifest = json.loads(broken_files["manifest.json"])
        manifest["top_module"] = "missing_top"
        broken_files["manifest.json"] = json.dumps(manifest) + "\n"
        broken_project = GeneratedProject(project_name=project.project_name, files=broken_files)

        result = check_project_l0(broken_project)

        self.assertFalse(result.passed)
        self.assertIn(
            "manifest.top_module 'missing_top' does not match System-HIS v1.2 artifacts.top_module 'top'",
            result.errors,
        )

    def test_l0_checker_accepts_system_his_v12_cross_checked_project(self) -> None:
        project = _minimal_v12_l0_project()

        result = check_project_l0(project)

        self.assertTrue(result.passed, result.errors)

    def test_l0_checker_rejects_system_his_module_source_outside_manifest(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["modules"][0]["source"] = "rtl/not_in_manifest.v"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'top' source 'rtl/not_in_manifest.v' is not in manifest.sources", result.errors)

    def test_l0_checker_rejects_connection_to_unknown_module(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["connections"][0]["to"]["module"] = "missing_core"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS connection[0].to.module 'missing_core' is not declared", result.errors)

    def test_l0_checker_rejects_connection_to_unknown_port(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["connections"][0]["to"]["port"] = "missing_port"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn(
            "System-HIS connection[0].to.port 'missing_port' is not declared on module 'baud_tick_gen'",
            result.errors,
        )

    def test_l0_checker_rejects_unknown_module_parameter(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="composed_stream_accumulator", width=8, project_name="stream_accum_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        for module in system_his["modules"]:
            if module["name"] == "accumulator_core":
                module["parameters"]["BAD_PARAM"] = 1
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'accumulator_core' parameter 'BAD_PARAM' is not declared in RTL", result.errors)

    def test_l0_checker_rejects_system_his_port_direction_mismatch(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        for port in system_his["modules"][0]["ports"]:
            if port["name"] == "count":
                port["direction"] = "input"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'top' port 'count' direction 'input' does not match RTL 'output'", result.errors)

    def test_l0_checker_rejects_system_his_port_width_mismatch(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        for port in system_his["modules"][0]["ports"]:
            if port["name"] == "count":
                port["width"] = 7
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'top' port 'count' width 7 does not match RTL 8", result.errors)

    def test_l0_checker_accepts_numeric_range_width_equivalent_to_integer_width(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        files = dict(project.files)
        system_his = json.loads(files["system_his.json"])
        for collection in (system_his["top_ports"], system_his["modules"][0]["ports"]):
            for port in collection:
                if port["name"] == "count":
                    port["width"] = "[7:0]"
        files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=files))

        self.assertTrue(result.passed, result.errors)

    def test_l0_checker_rejects_testbench_that_instantiates_wrong_top(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        broken_files["sim/tb_top.v"] = broken_files["sim/tb_top.v"].replace("top dut", "missing_top dut")

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("manifest testbench 'sim/tb_top.v' does not instantiate top module 'top'", result.errors)

    def test_l0_checker_rejects_timing_constraint_that_references_unknown_port(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        broken_files["constraints/timing.sdc"] = "create_clock -name clk -period 10.000 [get_ports missing_clk]\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("manifest timing constraint 'constraints/timing.sdc' references unknown top port 'missing_clk'", result.errors)

    def test_l0_checker_rejects_system_his_top_ports_that_do_not_match_rtl(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["top_ports"] = [{"name": "missing", "direction": "input", "width": 1}]
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.top_ports does not match top module RTL ports", result.errors)

    def test_l0_checker_rejects_module_missing_intent(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        del system_his["modules"][0]["intent"]
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS module 'top' intent is required", result.errors)

    def test_l0_checker_rejects_verification_missing_test_pass_means(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        del system_his["verification"]["test_pass_means"]
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.verification.test_pass_means is required", result.errors)

    def test_l0_checker_rejects_clock_without_positive_target_fmax(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["clocks"][0]["target_fmax_mhz"] = 0
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.clocks[0].target_fmax_mhz must be positive", result.errors)

    def test_l0_checker_rejects_reset_with_invalid_polarity(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["resets"][0]["polarity"] = "lowish"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.resets[0].polarity is invalid", result.errors)

    def test_l0_checker_rejects_qor_intent_missing_resource_field(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        del system_his["qor_intent"]["resources"]["lut"]
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("system_his.qor_intent.resources.lut is required", result.errors)

    def test_l0_checker_rejects_connection_with_invalid_protocol(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["connections"][0]["protocol"] = "mystery_bus"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS connection[0].protocol is invalid", result.errors)

    def test_l0_checker_rejects_connection_with_invalid_width_or_cdc(self) -> None:
        project = ProjectGenerator().generate(
            ProjectRequest(task_type="uart_tx", width=8, project_name="uart_tx_8bit"),
            PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source"),
        )
        broken_files = dict(project.files)
        system_his = json.loads(broken_files["system_his.json"])
        system_his["connections"][0]["width"] = 0
        system_his["connections"][0]["cdc"] = "false"
        broken_files["system_his.json"] = json.dumps(system_his) + "\n"

        result = check_project_l0(GeneratedProject(project_name=project.project_name, files=broken_files))

        self.assertFalse(result.passed)
        self.assertIn("System-HIS connection[0].width must be positive", result.errors)
        self.assertIn("System-HIS connection[0].cdc must be boolean", result.errors)

    def test_agent_stops_before_tools_when_l0_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=BrokenManifestGenerator(),
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="broken_counter")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_l0_fail",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_l0_fail"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L0_FAIL")
            self.assertFalse(labels["checks"]["l0_complete"])
            self.assertEqual(labels["failure_count"], 1)
            self.assertEqual(diagnosis["stage"], "l0_consistency")
            self.assertEqual(runner.calls, [])

    def test_agent_stops_before_l0_when_h3_fidelity_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=MutatingSystemHisGenerator(_break_stream_width_for_h3),
            )
            request = ProjectRequest(
                task_type="composed_stream_accumulator",
                width=8,
                project_name="stream_accum_8bit",
            )
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_h3_fail",
                requirement="Build an 8-bit stream accumulator with valid-ready input and output.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_h3_fail"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "H3_FAIL")
            self.assertTrue(labels["h0_pass"])
            self.assertTrue(labels["h1_pass"])
            self.assertTrue(labels["h2_pass"])
            self.assertFalse(labels["h3_pass"])
            self.assertEqual(trajectory["his_validation"]["h3"]["status"], "fail")
            self.assertEqual(runner.calls, [])

    def test_agent_stops_before_l0_when_h3_reset_fidelity_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=MutatingSystemHisGenerator(_break_reset_polarity_for_h3),
            )
            request = ProjectRequest(
                task_type="composed_stream_accumulator",
                width=8,
                project_name="stream_accum_8bit",
            )
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_h3_reset_fail",
                requirement="Build an 8-bit stream accumulator with valid-ready input and output.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_h3_reset_fail"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "H3_FAIL")
            self.assertFalse(labels["h3_pass"])
            self.assertEqual(trajectory["his_validation"]["h3"]["scores"]["clock_reset_fidelity"], 0.0)
            self.assertEqual(runner.calls, [])

    def test_agent_marks_oracle_fallback_as_not_generated_his_pass_credit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=FailureInjectingProjectGenerator(OracleFallbackGenerator(), []),
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one(
                sample_id="sample_oracle_fallback",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_oracle_fallback"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertFalse(labels["generated_his_pass_credit"])
            self.assertEqual(labels["pass_level"], "L3")
            self.assertEqual(labels["highest_official_level"], "L3")
            self.assertEqual(labels["generated_his_pass_level"], "NO_CREDIT_ORACLE_FALLBACK")
            self.assertEqual(labels["generated_his_no_credit_reason"], "oracle_fallback")
            self.assertEqual(trajectory["his_validation"]["his_source_used_for_generation"], "oracle_fallback")

    def test_agent_records_repair_failure_without_crashing_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=BrokenManifestGenerator(),
                repairer=FailingRepairer(),
                max_attempts=2,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="broken_counter")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_repair_fail",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_repair_fail"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L0_FAIL")
            self.assertEqual(labels["failure_count"], 1)
            self.assertEqual(diagnosis["stage"], "repair")
            self.assertEqual(diagnosis["failure_type"], "repair_failed")
            self.assertIn("DeepSeek repair system_his.json failed validation", diagnosis["root_cause"])
            self.assertEqual(diagnosis["upstream_diagnosis"]["stage"], "l0_consistency")
            self.assertEqual([item["stage"] for item in trajectory["attempts"]], ["l0_consistency", "repair"])
            self.assertFalse((sample_dir / "attempts/attempt_001").exists())
            self.assertEqual(runner.calls, [])

    def test_agent_records_repair_contract_regression_as_specific_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FailThenPassRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                repairer=ContractRegressionRepairer(),
                max_attempts=2,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_repair_contract_regression",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_repair_contract_regression"
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L0")
            self.assertEqual(diagnosis["stage"], "repair")
            self.assertEqual(diagnosis["failure_type"], "repair_contract_regression")
            self.assertIn("introduced L0 contract violations", diagnosis["root_cause"])
            self.assertEqual(diagnosis["upstream_diagnosis"]["stage"], "lint")
            self.assertEqual([item["stage"] for item in trajectory["attempts"]], ["rtl_identifier_check", "lint", "repair"])
            self.assertFalse((sample_dir / "attempts/attempt_001").exists())

    def test_agent_records_generation_failure_before_project_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=FailingProjectGenerator(),
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="broken_generation")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_generation_fail",
                requirement="Generate an 8-bit FPGA RTL project.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_generation_fail"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "GEN_FAIL")
            self.assertEqual(labels["pass_level"], "GEN_FAIL")
            self.assertFalse(labels["checks"]["generation_complete"])
            self.assertEqual(labels["failure_count"], 1)
            self.assertEqual(diagnosis["stage"], "generation")
            self.assertEqual(diagnosis["failure_type"], "generation_failed")
            self.assertIn("DeepSeek System-HIS v1.2 failed validation", diagnosis["root_cause"])
            self.assertEqual([item["stage"] for item in trajectory["attempts"]], ["generation"])
            self.assertEqual(runner.calls, [])

    def test_agent_stops_before_verilator_when_rtl_identifier_is_reserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=ReservedIdentifierGenerator(),
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="reserved_identifier_counter")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_reserved_identifier",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_reserved_identifier"
            self.assertEqual(result["pass_level"], "L0")
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertTrue(labels["checks"]["l0_complete"])
            self.assertFalse(labels["checks"]["l1_lint_pass"])
            self.assertEqual(diagnosis["stage"], "rtl_identifier_check")
            self.assertEqual(diagnosis["failure_type"], "rtl_reserved_identifier")
            self.assertIn("rtl/top.v", diagnosis["root_cause"])
            self.assertIn("'buf'", diagnosis["root_cause"])
            self.assertEqual([item["stage"] for item in trajectory["attempts"]], ["rtl_identifier_check"])
            self.assertEqual(runner.calls, [])

    def test_agent_stops_before_sim_compile_when_testbench_can_skip_output_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=ObservationRaceTestbenchGenerator(),
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="bad_observation_counter")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_testbench_observation_race",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_testbench_observation_race"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L1")
            self.assertTrue(labels["checks"]["l1_lint_pass"])
            self.assertFalse(labels["checks"]["l2_sim_pass"])
            self.assertEqual(diagnosis["stage"], "testbench_static_check")
            self.assertEqual(diagnosis["failure_type"], "testbench_observation_race")
            self.assertIn("wait(out_valid)", diagnosis["root_cause"])
            self.assertEqual(
                [item["stage"] for item in trajectory["attempts"]],
                ["rtl_identifier_check", "lint", "testbench_static_check"],
            )
            self.assertEqual([call["stage"] for call in runner.calls], ["lint"])

    def test_agent_stops_before_sim_compile_when_testbench_can_reaccept_stimulus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=StimulusReacceptTestbenchGenerator(),
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="bad_stimulus_counter")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_testbench_stimulus_reaccept",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_testbench_stimulus_reaccept"
            diagnosis = json.loads((sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L1")
            self.assertEqual(diagnosis["stage"], "testbench_static_check")
            self.assertEqual(diagnosis["failure_type"], "testbench_stimulus_reaccept_risk")
            self.assertIn("same packet can be accepted repeatedly", diagnosis["root_cause"])
            self.assertEqual(
                [item["stage"] for item in trajectory["attempts"]],
                ["rtl_identifier_check", "lint", "testbench_static_check"],
            )
            self.assertEqual([call["stage"] for call in runner.calls], ["lint"])

    def test_agent_run_one_records_l3_sample_with_fake_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            agent = DataGenerationAgent(dataset_root=root, command_runner=runner)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_000001",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_000001"
            self.assertEqual(result["pass_level"], "L3")
            self.assertTrue((sample_dir / "final/generated_project/rtl/top.v").exists())
            self.assertEqual(
                json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))["pass_level"],
                "L3",
            )
            measured_qor = json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))
            self.assertEqual(measured_qor["lut"], 5)
            self.assertEqual(measured_qor["ff"], 8)
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [item["stage"] for item in trajectory["attempts"]],
                ["rtl_identifier_check", "lint", "testbench_static_check", "sim_compile", "sim_run", "synth"],
            )
            self.assertEqual([call["stage"] for call in runner.calls], ["lint", "sim_compile", "sim_run", "synth"])

    def test_agent_independent_oracle_builds_once_and_reuses_bundle_for_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets"
            runner = FakeRunner()
            build_roots: list[Path] = []

            def builder(family_id, request, output_root):
                build_roots.append(Path(output_root))
                return _write_four_class_oracle_bundle(request.width, Path(output_root))

            agent = DataGenerationAgent(root, command_runner=runner, enable_independent_oracle=True)
            with mock.patch("LLM.src.sr2fpga_agent.agent.build_oracle_bundle_for_request", builder):
                result = agent.run_one(
                    "sample_fir_independent_oracle",
                    "Implement the declared FIR stream contract.",
                    ProjectRequest(task_type="fir_filter", width=8, project_name="fir"),
                    PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
                    metadata={"family_id": "fir_filter", "evaluation_line": "line_a"},
                )

            sample_dir = Path(result["sample_dir"])
            oracle_root = sample_dir / "attempts/attempt_000/eval/oracle"
            self.assertEqual(build_roots, [oracle_root])
            self.assertTrue((oracle_root / "manifest.json").is_file())
            self.assertTrue((oracle_root / "evidence.json").is_file())
            self.assertFalse((sample_dir / "final/generated_project/oracle").exists())
            vvp_calls = [call["command"] for call in runner.calls if call["stage"] == "sim_run"]
            self.assertGreaterEqual(len(vvp_calls), 4)
            self.assertTrue(
                all(
                    any(
                        Path(arg.split("=", 1)[1]).resolve().is_relative_to(oracle_root.resolve())
                        for arg in call
                        if arg.startswith("+ORACLE_INPUT=")
                    )
                    for call in vvp_calls
                )
            )
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(set(trajectory["oracle_profile"]["class_status"].values()), {"pass"})
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            self.assertTrue(labels["checks"]["l2_hidden_pass"])
            self.assertTrue(labels["checks"]["l2_randomized_pass"])
            self.assertTrue(labels["checks"]["l2_stress_pass"])

    def test_agent_independent_oracle_unsupported_family_keeps_legacy_simulation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets"
            runner = FakeRunner()
            agent = DataGenerationAgent(root, command_runner=runner, enable_independent_oracle=True)
            with mock.patch(
                "LLM.src.sr2fpga_agent.agent.build_oracle_bundle_for_request",
                return_value=None,
            ):
                result = agent.run_one(
                    "sample_counter_no_independent_oracle",
                    "Design a counter.",
                    ProjectRequest(task_type="counter", width=8, project_name="counter"),
                    PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
                    metadata={"family_id": "counter", "evaluation_line": "line_b"},
                )

            sample_dir = Path(result["sample_dir"])
            vvp_calls = [call["command"] for call in runner.calls if call["stage"] == "sim_run"]
            self.assertEqual(vvp_calls, [["vvp", "sim.out"]])
            profile = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))["oracle_profile"]
            self.assertEqual(profile["status"], "not_run")
            self.assertEqual(profile["skip_reason"], "unsupported_family")

    def test_agent_independent_oracle_build_failure_revokes_credit_without_model_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets"
            agent = DataGenerationAgent(root, command_runner=FakeRunner(), enable_independent_oracle=True)
            with mock.patch(
                "LLM.src.sr2fpga_agent.agent.build_oracle_bundle_for_request",
                side_effect=ValueError("reference model could not build vectors"),
            ):
                result = agent.run_one(
                    "sample_fir_oracle_build_failure",
                    "Implement the declared FIR stream contract.",
                    ProjectRequest(task_type="fir_filter", width=8, project_name="fir"),
                    PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
                    metadata={"family_id": "fir_filter", "evaluation_line": "line_a"},
                )

            labels = json.loads(
                (Path(result["sample_dir"]) / "eval/labels.json").read_text(encoding="utf-8")
            )
            self.assertEqual(labels["pass_level"], "ORACLE_ERROR")
            self.assertFalse(labels["automatic_pass_credit"])
            self.assertEqual(labels["independent_oracle_status"], "infrastructure_error")
            self.assertEqual(labels["failure_origin"], "oracle_environment_failure")
            self.assertFalse(labels["checks"]["l2_sim_pass"])

    def test_agent_pre_oracle_lint_failure_is_blocked_not_infrastructure_error(self) -> None:
        class LintFailRunner(FakeRunner):
            def run(self, command, cwd, stage, timeout_seconds=30):
                result = super().run(command, cwd, stage, timeout_seconds)
                if stage == "lint":
                    return ToolResult(
                        stage="lint",
                        command=list(command),
                        status="failed",
                        exit_code=1,
                        stdout="",
                        stderr="%Error: model RTL lint failure",
                        duration_seconds=0.01,
                    )
                return result

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets"
            agent = DataGenerationAgent(root, command_runner=LintFailRunner(), enable_independent_oracle=True)
            with mock.patch(
                "LLM.src.sr2fpga_agent.agent.build_oracle_bundle_for_request",
                side_effect=lambda family_id, request, output_root: _write_four_class_oracle_bundle(
                    request.width,
                    Path(output_root),
                ),
            ):
                result = agent.run_one(
                    "sample_fir_blocked_before_oracle",
                    "Implement the declared FIR stream contract.",
                    ProjectRequest(task_type="fir_filter", width=8, project_name="fir"),
                    PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
                    metadata={"family_id": "fir_filter", "evaluation_line": "line_a"},
                )

            sample_dir = Path(result["sample_dir"])
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            diagnosis = json.loads(
                (sample_dir / "attempts/attempt_000/diagnosis.json").read_text(encoding="utf-8")
            )
            self.assertEqual(labels["pass_level"], "L0")
            self.assertTrue(labels["automatic_pass_credit"])
            self.assertEqual(labels["independent_oracle_status"], "not_run")
            self.assertEqual(trajectory["oracle_profile"]["skip_reason"], "blocked_before_oracle")
            self.assertEqual(diagnosis["stage"], "lint")
            self.assertIn("model RTL lint failure", diagnosis["root_cause"])

    def test_agent_oracle_runner_and_evidence_writer_exceptions_become_stable_oracle_error(self) -> None:
        cases = (
            ("run_oracle_scenarios", RuntimeError("scenario runner crashed")),
            ("write_oracle_run_evidence", OSError("evidence disk unavailable")),
            ("sanitize_oracle_profile", ValueError("oracle profile is invalid")),
        )
        for index, (target, error) in enumerate(cases):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "datasets"
                agent = DataGenerationAgent(root, command_runner=FakeRunner(), enable_independent_oracle=True)
                sample_id = f"sample_fir_oracle_boundary_{index}"
                with mock.patch(
                    "LLM.src.sr2fpga_agent.agent.build_oracle_bundle_for_request",
                    side_effect=lambda family_id, request, output_root: _write_four_class_oracle_bundle(
                        request.width,
                        Path(output_root),
                    ),
                ), mock.patch(f"LLM.src.sr2fpga_agent.agent.{target}", side_effect=error):
                    result = agent.run_one(
                        sample_id,
                        "Implement the declared FIR stream contract.",
                        ProjectRequest(task_type="fir_filter", width=8, project_name="fir"),
                        PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
                        metadata={"family_id": "fir_filter", "evaluation_line": "line_a"},
                    )

                sample_dir = Path(result["sample_dir"])
                labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
                trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
                self.assertEqual(labels["pass_level"], "ORACLE_ERROR")
                self.assertFalse(labels["automatic_pass_credit"])
                self.assertEqual(labels["independent_oracle_status"], "infrastructure_error")
                self.assertEqual(labels["failure_origin"], "oracle_environment_failure")
                self.assertEqual(trajectory["oracle_profile"]["status"], "infrastructure_error")

    def test_agent_l4_open_disabled_records_auditable_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(dataset_root=root, command_runner=FakeRunner(), enable_openxc7_l4=False)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one("sample_l4_open_disabled", "Design a counter.", request, platform)

            sample_dir = root / "sample_l4_open_disabled"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertTrue(labels["checks"]["l3_synth_pass"])
            self.assertEqual(labels["l4_open_status"], "not_run")
            self.assertFalse(labels["l4_open_pass"])
            self.assertEqual(trajectory["verification"]["l4_open"]["skip_reason"], "disabled_by_config")

    def test_agent_l4_commercial_disabled_records_auditable_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(dataset_root=root, command_runner=FakeRunner())
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one("sample_l4_commercial_disabled", "Design a counter.", request, platform)

            sample_dir = root / "sample_l4_commercial_disabled"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            measured_qor = json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(result["pass_level"], "L3")
            self.assertEqual(labels["l4_commercial_status"], "not_run")
            self.assertFalse(labels["l4_commercial_pass"])
            self.assertEqual(labels["l4_commercial_skip_reason"], "disabled_by_config")
            self.assertEqual(measured_qor["l4_commercial"]["status"], "not_run")
            self.assertEqual(
                trajectory["verification"]["l4_commercial"]["skip_reason"],
                "disabled_by_config",
            )

    def test_agent_l4_commercial_success_records_reference_without_upgrading_pass_level(self) -> None:
        vivado_report = {
            "tool": "vivado",
            "status": "pass",
            "constraint_scope": "logical_only",
            "board_constraints_applied": False,
            "official_board_ready": False,
            "wns_ns": 5.79,
            "fmax_mhz": 237.53,
            "lut": 34,
            "ff": 28,
            "bram": 0,
            "dsp": 0,
            "drc_warnings": ["NSTD-1", "UCIO-1", "ZPS7-1"],
            "expected_board_drc_exceptions": ["NSTD-1", "UCIO-1"],
            "invalidating_critical_warnings": [],
            "methodology_warnings": ["TIMING-18"],
            "runtime_sec": 12.5,
            "report_paths": ["eval/vivado/vivado_report.json", "eval/vivado/vivado_timing_summary.rpt"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=FakeRunner(),
                enable_vivado_l4=True,
                vivado_command="vivado",
                vivado_part="XC7Z020CLG484-2",
                vivado_timeout_seconds=90,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            with mock.patch.dict("os.environ", {"SR2FPGA_VIVADO_COMMAND": "C:/tools/vivado.bat"}):
                with mock.patch(
                    "LLM.src.sr2fpga_agent.agent.run_vivado_reference",
                    return_value=vivado_report,
                ) as run_vivado:
                    result = agent.run_one("sample_l4_commercial_pass", "Design a counter.", request, platform)

            sample_dir = root / "sample_l4_commercial_pass"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            measured_qor = json.loads((sample_dir / "eval/measured_qor.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(result["pass_level"], "L3")
            self.assertEqual(labels["l4_commercial_status"], "pass")
            self.assertTrue(labels["l4_commercial_pass"])
            self.assertEqual(measured_qor["l4_commercial"]["wns_ns"], 5.79)
            self.assertFalse(trajectory["verification"]["l4_commercial"]["official_board_ready"])
            self.assertEqual(
                trajectory["verification"]["l4_commercial"]["report_paths"],
                [
                    "attempts/attempt_000/generated_project/eval/vivado/vivado_report.json",
                    "attempts/attempt_000/generated_project/eval/vivado/vivado_timing_summary.rpt",
                ],
            )
            run_vivado.assert_called_once()
            self.assertEqual(run_vivado.call_args.kwargs["vivado_command"], "C:/tools/vivado.bat")

    def test_agent_l4_open_l3_failed_records_auditable_not_run(self) -> None:
        class SynthFailingRunner(FakeRunner):
            def run(self, command, cwd, stage, timeout_seconds=30):
                result = super().run(command, cwd, stage, timeout_seconds)
                if stage == "synth":
                    return ToolResult(
                        stage=stage,
                        command=list(command),
                        status="failed",
                        exit_code=1,
                        stdout="",
                        stderr="synthesis failed",
                        duration_seconds=0.01,
                    )
                return result

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(dataset_root=root, command_runner=SynthFailingRunner(), enable_openxc7_l4=True)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one("sample_l4_open_l3_failed", "Design a counter.", request, platform)

            sample_dir = root / "sample_l4_open_l3_failed"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertFalse(labels["checks"]["l3_synth_pass"])
            self.assertEqual(labels["l4_open_status"], "not_run")
            self.assertEqual(trajectory["verification"]["l4_open"]["skip_reason"], "l3_failed")

    def test_agent_l4_open_disabled_reason_takes_precedence_over_l3_failure(self) -> None:
        class SynthFailingRunner(FakeRunner):
            def run(self, command, cwd, stage, timeout_seconds=30):
                result = super().run(command, cwd, stage, timeout_seconds)
                if stage == "synth":
                    return ToolResult(
                        stage=stage,
                        command=list(command),
                        status="failed",
                        exit_code=1,
                        stdout="",
                        stderr="synthesis failed",
                        duration_seconds=0.01,
                    )
                return result

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(dataset_root=root, command_runner=SynthFailingRunner(), enable_openxc7_l4=False)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one("sample_l4_disabled_l3_failed", "Design a counter.", request, platform)

            trajectory = json.loads((root / "sample_l4_disabled_l3_failed/eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(trajectory["verification"]["l4_open"]["status"], "not_run")
            self.assertEqual(trajectory["verification"]["l4_open"]["skip_reason"], "disabled_by_config")

    def test_agent_records_project_from_injected_llm_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FakeRunner()
            llm_generator = FakeLLMProjectGenerator()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                project_generator=llm_generator,
            )
            request = ProjectRequest(
                task_type="counter",
                width=8,
                project_name="llm_counter_8bit",
                description="Design a counter using an LLM-generated package.",
            )
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one(
                sample_id="sample_llm_000001",
                requirement=request.description,
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_llm_000001"
            top_rtl = (sample_dir / "final/generated_project/rtl/top.v").read_text(encoding="utf-8")
            system_his = json.loads(
                (sample_dir / "final/generated_project/system_his.json").read_text(encoding="utf-8")
            )
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(llm_generator.call_count, 1)
            self.assertIn("LLM_GENERATED_MARKER", top_rtl)
            self.assertNotIn("count <= count +", top_rtl)
            self.assertEqual(system_his["schema_version"], "system-his-v1.2")
            self.assertEqual(system_his["intent"]["user_prompt"], request.description)
            self.assertEqual(system_his["system"]["description"], request.description)
            self.assertEqual(trajectory["his_validation"]["his_source_used_for_generation"], "generated")

    def test_agent_records_failed_attempt_patch_and_repaired_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = FailThenPassRunner()
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=runner,
                repairer=FakeRepairer(),
                max_attempts=2,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_000002",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_000002"
            self.assertEqual(result["pass_level"], "L3")
            self.assertTrue((sample_dir / "attempts/attempt_000/diagnosis.json").exists())
            self.assertIn(
                "fix reset port",
                (sample_dir / "attempts/attempt_000/patch.diff").read_text(encoding="utf-8"),
            )
            self.assertTrue((sample_dir / "attempts/attempt_001/generated_project/rtl/top.v").exists())
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            self.assertEqual(labels["final_attempt_id"], 1)
            self.assertEqual(labels["failure_count"], 1)
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
            patch_metadata = json.loads((sample_dir / "attempts/attempt_000/patch.json").read_text(encoding="utf-8"))
            first_failed = next(item for item in trajectory["attempts"] if item["status"] == "failed")
            self.assertEqual(first_failed["attempt_id"], 0)
            self.assertEqual(first_failed["stage"], "lint")
            self.assertEqual(trajectory["attempts"][-1]["attempt_id"], 1)
            self.assertEqual(trajectory["attempts"][-1]["stage"], "synth")
            self.assertEqual(patch_metadata["tool_result_before"]["lint"], "failed")
            self.assertEqual(patch_metadata["tool_result_after"]["synth"], "passed")
            self.assertTrue(patch_metadata["repair_regression"]["fixed_target"])
            self.assertEqual(trajectory["patches"][0]["patch_id"], "p001")

            export_dir = Path(tmp) / "exports"
            DatasetRecorder(root).export_training_views(export_dir)
            patch_rows = (export_dir / "failure_to_patch.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(patch_rows), 1)
            patch_row = json.loads(patch_rows[0])
            self.assertEqual(patch_row["sample_id"], "sample_000002")
            self.assertEqual(patch_row["diagnosis"]["failure_type"], "port_mismatch")
            self.assertIn("fix reset port", patch_row["patch"])
            self.assertEqual(patch_row["patch_metadata"]["repair_regression"]["regressed_levels"], [])

    def test_agent_credits_successful_l0_repair_target(self) -> None:
        class BrokenWidthGenerator:
            def generate(self, request, platform):
                project = ProjectGenerator().generate(request, platform)
                files = dict(project.files)
                files["rtl/top.v"] = files["rtl/top.v"].replace(
                    "output reg [7:0] count",
                    "output reg [6:0] count",
                )
                return GeneratedProject(project_name=project.project_name, files=files)

        class WidthRepairer:
            def repair(self, project, diagnosis):
                files = dict(project.files)
                files["rtl/top.v"] = files["rtl/top.v"].replace(
                    "output reg [6:0] count",
                    "output reg [7:0] count",
                )
                return RepairResult(
                    generated_project=GeneratedProject(project_name=project.project_name, files=files),
                    patch_diff="diff --git a/rtl/top.v b/rtl/top.v\n# restore count width\n",
                )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=FakeRunner(),
                project_generator=BrokenWidthGenerator(),
                repairer=WidthRepairer(),
                max_attempts=2,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one("sample_l0_repair", "Design an 8-bit counter.", request, platform)

            patch_metadata = json.loads(
                (root / "sample_l0_repair/attempts/attempt_000/patch.json").read_text(encoding="utf-8")
            )
            self.assertEqual(patch_metadata["repair_regression"]["target_failure"], "l0_consistency")
            self.assertEqual(patch_metadata["tool_result_after"]["l0_consistency"], "passed")
            self.assertTrue(patch_metadata["repair_regression"]["fixed_target"])
            self.assertTrue(patch_metadata["automatic_pass_credit"])

    def test_agent_rejects_invalid_repair_and_preserves_original_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=FailThenPassRunner(),
                repairer=InvalidSurfaceRepairer(),
                max_attempts=2,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one("sample_invalid_repair", "Design an 8-bit counter.", request, platform)

            sample_dir = root / "sample_invalid_repair"
            original = (sample_dir / "attempts/attempt_000/generated_project/sim/tb_top.v").read_text(encoding="utf-8")
            final = (sample_dir / "final/generated_project/sim/tb_top.v").read_text(encoding="utf-8")
            patch = json.loads((sample_dir / "attempts/attempt_000/patch.json").read_text(encoding="utf-8"))
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))

            self.assertEqual(final, original)
            self.assertEqual(patch["status"], "invalid_edit_surface")
            self.assertFalse(patch["automatic_pass_credit"])
            self.assertFalse(labels["automatic_pass_credit"])

    def test_agent_revokes_credit_for_failed_and_regressing_rtl_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(
                dataset_root=root,
                command_runner=SimFailThenLintFailRunner(),
                repairer=RtlChangingRepairer(),
                max_attempts=2,
            )
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one("sample_regressing_repair", "Design an 8-bit counter.", request, platform)

            sample_dir = root / "sample_regressing_repair"
            patch = json.loads((sample_dir / "attempts/attempt_000/patch.json").read_text(encoding="utf-8"))
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))

            self.assertFalse(patch["automatic_pass_credit"])
            self.assertFalse(patch["repair_regression"]["fixed_target"])
            self.assertEqual(patch["repair_regression"]["regressed_levels"], ["lint"])
            self.assertFalse(labels["automatic_pass_credit"])

    def test_agent_treats_test_fail_output_as_failed_simulation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            runner = SemanticFailRunner()
            agent = DataGenerationAgent(dataset_root=root, command_runner=runner)
            request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            result = agent.run_one(
                sample_id="sample_000003",
                requirement="Design an 8-bit counter with enable.",
                request=request,
                platform=platform,
            )

            sample_dir = root / "sample_000003"
            labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
            diagnosis_path = sample_dir / "attempts/attempt_000/diagnosis.json"
            self.assertTrue(diagnosis_path.exists())
            diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
            trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))

            self.assertEqual(result["pass_level"], "L1")
            self.assertFalse(labels["checks"]["l2_sim_pass"])
            self.assertEqual(labels["failure_count"], 1)
            self.assertEqual(diagnosis["stage"], "sim_run")
            self.assertIn("TEST_FAIL", diagnosis["root_cause"])
            self.assertEqual(
                [item["stage"] for item in trajectory["attempts"]],
                ["rtl_identifier_check", "lint", "testbench_static_check", "sim_compile", "sim_run"],
            )

    def test_agent_records_req_his_fidelity_metrics_for_supported_topology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            agent = DataGenerationAgent(dataset_root=root, command_runner=FakeRunner())
            request = ProjectRequest(
                task_type="composed_stream_accumulator",
                width=8,
                project_name="stream_accum_8bit",
            )
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")

            agent.run_one(
                sample_id="sample_000004",
                requirement="Build a stream accumulator.",
                request=request,
                platform=platform,
            )

            trajectory = json.loads((root / "sample_000004/eval/trajectory.json").read_text(encoding="utf-8"))
            fidelity = trajectory["req_his_fidelity"]
            self.assertEqual(fidelity["interface_extraction"]["status"], "pass")
            self.assertEqual(fidelity["parameter_fidelity"]["status"], "pass")
            self.assertEqual(fidelity["behavior_intent_fidelity"]["status"], "pass")

    def test_repair_result_is_shared_model_and_agent_compatible(self) -> None:
        self.assertIs(RepairResult, ModelRepairResult)

    def test_export_training_views_ignores_hidden_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            requirement = "Design an 8-bit counter with enable and active-low reset."
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                platform,
            )
            recorder.start_sample("sample_000001", requirement, platform)
            recorder.write_final(
                "sample_000001",
                project,
                labels={"pass_level": "L3"},
                measured_qor={"lut": 1, "ff": 8, "bram": 0, "dsp": 0},
                tool_versions={"yosys": "unknown"},
                trajectory={"sample_id": "sample_000001", "attempts": []},
            )
            hidden_file = root / "sample_000001" / "final" / "generated_project" / ".DS_Store"
            hidden_file.write_bytes(b"\x00\x80binary finder metadata")

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            rows = (export_dir / "requirement_to_project.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 1)
            exported_paths = [item["path"] for item in json.loads(rows[0])["files"]]
            self.assertNotIn(".DS_Store", exported_paths)

    def test_write_final_adds_system_his_episode_metadata_and_exports_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "datasets" / "sr2fpga_rtl_v1"
            recorder = DatasetRecorder(root)
            requirement = "Design an 8-bit counter with enable and active-low reset."
            platform = PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")
            project = ProjectGenerator().generate(
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                platform,
            )
            recorder.start_sample(
                "sample_000001",
                requirement,
                platform,
                metadata={"system_his_schema_version": "system-his-v1.2"},
            )

            recorder.write_final(
                "sample_000001",
                project,
                labels={
                    "pass_level": "L3",
                    "checks": {
                        "l0_complete": True,
                        "l1_lint_pass": True,
                        "l2_sim_pass": True,
                        "l2_hidden_pass": False,
                        "l2_stress_pass": True,
                        "l2_coverage_profile": "counter_reset_enable_stress",
                        "l2_coverage_seeds": [3, 17],
                        "l2s_pass": False,
                        "l2s_divergences": ["post-synth count output diverged at cycle 4"],
                        "l3_synth_pass": True,
                    },
                },
                measured_qor={"lut": 1, "ff": 8, "bram": 0, "dsp": 0},
                tool_versions={"yosys": "unknown"},
                trajectory={"sample_id": "sample_000001", "attempts": []},
            )

            trajectory = json.loads((root / "sample_000001/eval/trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(trajectory["generated_his"]["schema_version"], "system-his-v1.2")
            self.assertEqual(trajectory["req_his_fidelity"]["interface_extraction"], None)
            self.assertIn("deterministic_artifacts", trajectory["project"])
            self.assertIn("model_generated_artifacts", trajectory["project"])
            self.assertEqual(trajectory["project"]["files"]["system_his.json"]["origin"], "deterministic")
            self.assertEqual(trajectory["project"]["files"]["rtl/top.v"]["origin"], "model_generated")
            self.assertEqual(trajectory["project"]["behavior_hole_count"], 0)
            self.assertEqual(trajectory["verification"]["l2_core"]["public"]["status"], "pass")
            self.assertEqual(trajectory["verification"]["l2_core"]["hidden"]["status"], "fail")
            self.assertEqual(trajectory["verification"]["l2_core"]["stress"]["status"], "pass")
            self.assertEqual(
                trajectory["verification"]["l2_core"]["coverage"]["scenario_profile"],
                "counter_reset_enable_stress",
            )
            self.assertEqual(trajectory["verification"]["l2_core"]["coverage"]["seeds"], [3, 17])
            self.assertEqual(trajectory["verification"]["l2s"]["status"], "fail")
            self.assertEqual(
                trajectory["verification"]["l2s"]["divergences"],
                ["post-synth count output diverged at cycle 4"],
            )
            self.assertEqual(trajectory["verification"]["l4_open"]["status"], "not_run")
            self.assertEqual(trajectory["data_release"]["requirement"], "open_public")
            self.assertEqual(trajectory["data_release"]["l4_commercial"], "restricted_reference")

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)
            requirement_row = json.loads((export_dir / "requirement_to_his.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(requirement_row["episode"]["verification"]["l2_core"]["public"]["status"], "pass")
            self.assertEqual(requirement_row["episode"]["data_release"]["vivado_raw_artifacts"], "internal_only")


class FakeRunner:
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
        }
        return ToolResult(
            stage=stage,
            command=list(command),
            status="passed",
            exit_code=0,
            stdout=stdout_by_stage[stage],
            stderr="",
            duration_seconds=0.01,
        )


class FakeLLMProjectGenerator:
    def __init__(self) -> None:
        self.call_count = 0

    def generate(self, request, platform):
        self.call_count += 1
        project = ProjectGenerator().generate(request, platform)
        files = dict(project.files)
        system_his = json.loads(files["system_his.json"])
        system_his["intent"]["user_prompt"] = request.description
        system_his["system"] = {"description": request.description}
        files["system_his.json"] = json.dumps(system_his) + "\n"
        files["rtl/top.v"] = """module top (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg [7:0] count
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 8'd0;
    end else begin
      count <= {7'd0, en};
    end
  end

endmodule

// LLM_GENERATED_MARKER
"""
        files["sim/tb_top.v"] = """module tb_top;
  reg clk;
  reg rst_n;
  reg en;
  wire [7:0] count;
  top dut(.clk(clk), .rst_n(rst_n), .en(en), .count(count));
  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end
  initial begin
    rst_n = 1'b0;
    en = 1'b0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;
    en = 1'b1;
    @(posedge clk);
    if (count !== 8'd1) begin $display("TEST_FAIL expected count=1"); $finish; end
    en = 1'b0;
    @(posedge clk);
    if (count !== 8'd0) begin $display("TEST_FAIL expected count=0"); $finish; end
    $display("TEST_PASS");
    $finish;
  end
endmodule
"""
        return GeneratedProject(project_name=request.project_name, files=files)


class FailThenPassRunner(FakeRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == "lint" and not self.calls:
            self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
            return ToolResult(
                stage=stage,
                command=list(command),
                status="failed",
                exit_code=1,
                stdout="",
                stderr="Port rst_n of module top is not declared",
                duration_seconds=0.01,
            )
        return super().run(command, cwd, stage, timeout_seconds)


class SemanticFailRunner(FakeRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == "sim_run":
            self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
            return ToolResult(
                stage=stage,
                command=list(command),
                status="passed",
                exit_code=0,
                stdout="TEST_FAIL semantic mismatch\n",
                stderr="",
                duration_seconds=0.01,
            )
        return super().run(command, cwd, stage, timeout_seconds)


class FakeRepairer:
    def repair(self, project, diagnosis):
        files = dict(project.files)
        files["rtl/top.v"] += "\n// fix reset port\n"
        return RepairResult(
            generated_project=GeneratedProject(project_name=project.project_name, files=files),
            patch_diff="diff --git a/rtl/top.v b/rtl/top.v\n# fix reset port\n",
        )


class InvalidSurfaceRepairer:
    def repair(self, project, diagnosis):
        files = dict(project.files)
        files["sim/tb_top.v"] = "module tb_top; initial $display(\"TEST_PASS\"); endmodule\n"
        return RepairResult(
            generated_project=GeneratedProject(project_name=project.project_name, files=files),
            patch_diff="diff --git a/sim/tb_top.v b/sim/tb_top.v\n# weaken testbench\n",
        )


class RtlChangingRepairer:
    def repair(self, project, diagnosis):
        files = dict(project.files)
        files["rtl/top.v"] += "\n// attempted repair\n"
        return RepairResult(
            generated_project=GeneratedProject(project_name=project.project_name, files=files),
            patch_diff="diff --git a/rtl/top.v b/rtl/top.v\n# attempted repair\n",
        )


class SimFailThenLintFailRunner(FakeRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        self.calls.append({"command": command, "cwd": cwd, "stage": stage, "timeout_seconds": timeout_seconds})
        if len(self.calls) == 1 and stage == "lint":
            return ToolResult(stage, list(command), "passed", 0, "", "", 0.01)
        if len(self.calls) == 2 and stage == "sim_compile":
            return ToolResult(stage, list(command), "passed", 0, "", "", 0.01)
        if len(self.calls) == 3 and stage == "sim_run":
            return ToolResult(stage, list(command), "failed", 1, "", "target still failing", 0.01)
        return ToolResult(stage, list(command), "failed", 1, "", "new lint regression", 0.01)


class FailingRepairer:
    def repair(self, project, diagnosis):
        raise ValueError(
            "DeepSeek repair system_his.json failed validation: "
            "control_flow 'join_wait_both'.fsm 'join_fsm' is not declared"
        )


class ContractRegressionRepairer:
    def repair(self, project, diagnosis):
        raise ValueError("DeepSeek repair introduced L0 contract violations: stream_join.in1_data is not declared")


class BrokenManifestGenerator:
    def generate(self, request, platform):
        project = ProjectGenerator().generate(request, platform)
        files = dict(project.files)
        manifest = json.loads(files["manifest.json"])
        manifest["top_module"] = "missing_top"
        files["manifest.json"] = json.dumps(manifest) + "\n"
        return GeneratedProject(project_name=project.project_name, files=files)


class MutatingSystemHisGenerator:
    def __init__(self, mutate) -> None:
        self.mutate = mutate

    def generate(self, request, platform):
        project = ProjectGenerator().generate(request, platform)
        files = dict(project.files)
        system_his = json.loads(files["system_his.json"])
        self.mutate(system_his)
        files["system_his.json"] = json.dumps(system_his) + "\n"
        return GeneratedProject(project_name=project.project_name, files=files)


class OracleFallbackGenerator:
    his_source_used_for_generation = "oracle_fallback"

    def generate(self, request, platform):
        return ProjectGenerator().generate(request, platform)


def _break_stream_width_for_h3(system_his: dict) -> None:
    next(port for port in system_his["top"]["ports"] if port["name"] == "in_data")["width"] = 7


def _break_reset_polarity_for_h3(system_his: dict) -> None:
    system_his["top"]["resets"][0]["polarity"] = "active_high"


class FailingProjectGenerator:
    def generate(self, request, platform):
        raise ValueError("DeepSeek System-HIS v1.2 failed validation: instances[0].name is required")


class ReservedIdentifierGenerator:
    def generate(self, request, platform):
        project = ProjectGenerator().generate(request, platform)
        files = dict(project.files)
        files["rtl/top.v"] = files["rtl/top.v"].replace(");\n\n  always", ");\n\n  reg [7:0] buf;\n\n  always")
        return GeneratedProject(project_name=project.project_name, files=files)


class ObservationRaceTestbenchGenerator:
    def generate(self, request, platform):
        project = ProjectGenerator().generate(request, platform)
        files = dict(project.files)
        files["sim/tb_top.v"] = """
module tb_top;
  reg clk;
  wire out_valid;
  wire [7:0] out_data;
  reg [7:0] expected;
  top dut();
  initial begin
    wait(out_valid);
    @(posedge clk) #1;
    if (out_data !== expected) $display("TEST_FAIL");
    $display("TEST_PASS");
  end
endmodule
"""
        return GeneratedProject(project_name=project.project_name, files=files)


class StimulusReacceptTestbenchGenerator:
    def generate(self, request, platform):
        project = ProjectGenerator().generate(request, platform)
        files = dict(project.files)
        files["sim/tb_top.v"] = """
module tb_top;
  reg clk;
  reg in0_valid;
  reg in1_valid;
  wire out_valid;
  wire [7:0] out_data;
  reg [7:0] expected;
  top dut();
  initial begin
    in0_valid = 1;
    in1_valid = 1;
    @(posedge clk);
    wait(out_valid);
    #1;
    if (out_data !== expected) $display("TEST_FAIL");
    @(negedge clk);
    in0_valid = 0;
    in1_valid = 0;
  end
endmodule
"""
        return GeneratedProject(project_name=project.project_name, files=files)


def _minimal_v12_l0_project() -> GeneratedProject:
    system_his = {
        "schema_version": "system-his-v1.2",
        "intent": {"user_prompt": "Build an 8-bit counter.", "design_goal": "Counter project.", "assumptions": []},
        "top": {
            "name": "top",
            "parameters": [],
            "clocks": [{"name": "clk", "target_fmax_mhz": 100}],
            "resets": [{"name": "rst_n", "polarity": "active_low", "kind": "sync"}],
            "ports": [
                {"name": "clk", "dir": "input", "width": 1},
                {"name": "rst_n", "dir": "input", "width": 1},
                {"name": "en", "dir": "input", "width": 1},
                {"name": "count", "dir": "output", "width": 8},
            ],
            "interfaces": [],
        },
        "state": {
            "registers": [{"name": "count_q", "owner": "u_counter", "width": 8}],
            "counters": [],
            "fsms": [],
            "buffers": [],
            "memories": [],
        },
        "components": [
            {
                "name": "counter_core",
                "semantic_kind": "counter",
                "source": "rtl/counter_core.v",
                "parameters": [],
                "ports": [
                    {"name": "clk", "dir": "input", "width": 1},
                    {"name": "rst_n", "dir": "input", "width": 1},
                    {"name": "en", "dir": "input", "width": 1},
                    {"name": "count", "dir": "output", "width": 8},
                ],
                "intent": "8-bit counter datapath and state update logic",
            }
        ],
        "instances": [
            {
                "name": "u_counter",
                "component": "counter_core",
                "parameter_values": {},
                "clock": "clk",
                "reset": "rst_n",
                "owns_state": ["u_counter.count_q"],
            }
        ],
        "data_flow": [
            {
                "name": "count_path",
                "path": ["top.en", "u_counter.en", "u_counter.count", "top.count"],
                "payload": {"name": "count_value", "width": 8},
                "protocol": "register",
            }
        ],
        "control_flow": [
            {
                "name": "increment_when_enabled",
                "kind": "enable_rule",
                "condition": "en",
                "effects": ["count_q := count_q + 1"],
                "related_state": ["u_counter.count_q"],
                "related_flows": ["count_path"],
            }
        ],
        "timing": {"primary_clock": "clk", "target_fmax_mhz": 100, "constraints": ["constraints/timing.sdc"]},
        "resources": {"optimization_goal": "area_first", "expected": {"lut": "low", "ff": "low", "bram": 0, "dsp": 0}},
        "verification": {"testbench": "sim/tb_top.v", "scenarios": [], "pass_condition": "TEST_PASS"},
        "artifacts": {
            "top_module": "top",
            "rtl_sources": ["rtl/top.v", "rtl/counter_core.v"],
            "testbench": "sim/tb_top.v",
            "constraints": ["constraints/timing.sdc"],
            "manifest": "manifest.json",
            "predicted_qor": "reports/predicted_qor.json",
        },
    }
    files = {
        "system_his.json": json.dumps(system_his) + "\n",
        "manifest.json": json.dumps(
            {
                "project_name": "counter8",
                "top_module": "top",
                "sources": ["rtl/top.v", "rtl/counter_core.v"],
                "constraints": {"timing": "constraints/timing.sdc"},
                "simulation": {"testbench": "sim/tb_top.v"},
                "reports": ["reports/predicted_qor.json"],
            }
        )
        + "\n",
        "rtl/top.v": (
            "module top(input clk, input rst_n, input en, output [7:0] count);\n"
            "  counter_core u_counter(.clk(clk), .rst_n(rst_n), .en(en), .count(count));\n"
            "endmodule\n"
        ),
        "rtl/counter_core.v": (
            "module counter_core(input clk, input rst_n, input en, output reg [7:0] count);\n"
            "  always @(posedge clk) begin\n"
            "    if (!rst_n) count <= 8'd0;\n"
            "    else if (en) count <= count + 8'd1;\n"
            "  end\n"
            "endmodule\n"
        ),
        "constraints/timing.sdc": "create_clock -period 10 [get_ports clk]\n",
        "sim/tb_top.v": "module tb; reg clk, rst_n, en; wire [7:0] count; top dut(clk, rst_n, en, count); endmodule\n",
        "reports/predicted_qor.json": "{}\n",
    }
    return GeneratedProject(project_name="counter8", files=files)


if __name__ == "__main__":
    unittest.main()
