import json
import tempfile
import unittest
from pathlib import Path

from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ToolResult
from sr2fpga_agent.recorder import AttemptRecord, DatasetRecorder


def _project(*, include_his: bool = True) -> GeneratedProject:
    files = {
        "manifest.json": "{}\n",
        "rtl/top.v": "module top; endmodule\n",
        "sim/tb_top.v": "module tb_top; endmodule\n",
    }
    if include_his:
        files["system_his.json"] = json.dumps({"schema_version": "system-his-v1.2"}) + "\n"
    return GeneratedProject(project_name="audit_project", files=files)


def _origins(
    project: GeneratedProject,
    *,
    system_his: str = "model_generated",
    testbench: str = "deterministic",
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for path in project.files:
        if path == "system_his.json":
            origin = system_his
        elif path == "sim/tb_top.v":
            origin = testbench
        elif path == "manifest.json":
            origin = "deterministic"
        else:
            origin = "model_generated"
        result[path] = {"origin": origin}
    return result


def _his_pass() -> dict:
    return {
        "h0": {"status": "pass", "diagnostics": []},
        "h1": {"status": "pass", "diagnostics": []},
        "h2": {"status": "pass", "diagnostics": []},
        "h3": {"status": "pass", "diagnostics": []},
        "passed": True,
    }


def _verified_labels() -> dict:
    return {
        "automatic_pass_credit": True,
        "generated_his_pass_credit": True,
        "provenance_compliant": True,
        "budget_compliant": True,
        "vpp_l3": True,
        "checks": {
            "l0_complete": True,
            "l1_lint_pass": True,
            "l2_sim_pass": True,
            "l2_hidden_pass": True,
            "l3_synth_pass": True,
        },
    }


def _verified_metadata(**overrides: object) -> dict:
    metadata = {
        "source": "model",
        "generator_provider": "model",
        "requirement_boundary": {"disposition": "ready"},
        "official_hidden_outcome_reference_count": 0,
        "model_call_budget": {
            "max_model_calls": 1,
            "model_calls_used": 1,
            "model_calls_failed": 0,
            "remaining_model_calls": 0,
            "calls": [{"call_id": 0, "status": "completed"}],
        },
    }
    metadata.update(overrides)
    return metadata


def _write_final(
    recorder: DatasetRecorder,
    sample_id: str,
    project: GeneratedProject,
    *,
    labels: dict | None = None,
    origins: dict[str, dict[str, str]] | None = None,
) -> None:
    recorder.write_final(
        sample_id,
        project,
        labels=labels or _verified_labels(),
        measured_qor={},
        tool_versions={},
        trajectory={
            "sample_id": sample_id,
            "attempts": [],
            "his_validation": _his_pass(),
            "project": {"files": origins if origins is not None else _origins(project)},
        },
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class TrainingViewEligibilityTest(unittest.TestCase):
    def test_official_hidden_outcome_is_forbidden_from_positive_training_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project()
            recorder.start_sample(
                "sample-official-hidden",
                "Build a counter.",
                PlatformProfile("generic", "generic", "open_source"),
                metadata=_verified_metadata(official_hidden_outcome_reference_count=1),
            )
            _write_final(recorder, "sample-official-hidden", project)
            export_dir = Path(tmp) / "exports-count"
            recorder.export_training_views(export_dir)
            decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
            self.assertIn(
                "official_hidden_outcome_reference_count_not_zero",
                decision["views"]["requirement_to_project"]["reasons"],
            )
            self.assertEqual(_read_jsonl(export_dir / "requirement_to_project.jsonl"), [])

            metadata_path = root / "sample-official-hidden" / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["official_hidden_outcome_reference_count"] = 0
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            trajectory_path = root / "sample-official-hidden" / "eval" / "trajectory.json"
            trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
            trajectory["official_hidden_outcome"] = {
                "contract_version": "official-hidden-outcome-v1"
            }
            trajectory_path.write_text(json.dumps(trajectory), encoding="utf-8")
            export_dir = Path(tmp) / "exports-embedded"
            recorder.export_training_views(export_dir)
            decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
            self.assertIn(
                "official_hidden_outcome_reference_forbidden",
                decision["views"]["requirement_to_project"]["reasons"],
            )

    def setUp(self) -> None:
        self.platform = PlatformProfile(
            name="generic_verilog",
            vendor="generic",
            toolchain="open_source",
        )

    def test_explicit_verified_eligibility_exports_positive_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project()
            recorder.start_sample(
                "sample_verified",
                "Build the declared project.",
                self.platform,
                metadata=_verified_metadata(),
            )
            _write_final(recorder, "sample_verified", project)

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            for filename in (
                "requirement_to_his.jsonl",
                "his_to_project.jsonl",
                "requirement_to_project.jsonl",
                "requirement_to_file.jsonl",
            ):
                rows = _read_jsonl(export_dir / filename)
                self.assertGreater(len(rows), 0, filename)
                self.assertTrue(rows[0]["verified_positive"])
                self.assertTrue(rows[0]["training_view_eligibility"]["eligible"])

            his_row = _read_jsonl(export_dir / "requirement_to_his.jsonl")[0]
            self.assertEqual(his_row["system_his_origin"], "model_generated")
            file_rows = _read_jsonl(export_dir / "requirement_to_file.jsonl")
            tb_row = next(row for row in file_rows if row["file_path"] == "sim/tb_top.v")
            self.assertEqual(tb_row["file_origin"], "deterministic")

    def test_missing_ready_requirement_boundary_blocks_positive_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project()
            metadata = _verified_metadata()
            metadata.pop("requirement_boundary")
            recorder.start_sample(
                "sample_missing_boundary",
                "Build the declared project.",
                self.platform,
                metadata=metadata,
            )
            _write_final(recorder, "sample_missing_boundary", project)

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            for filename in (
                "requirement_to_his.jsonl",
                "his_to_project.jsonl",
                "requirement_to_project.jsonl",
                "requirement_to_file.jsonl",
            ):
                self.assertEqual(_read_jsonl(export_dir / filename), [], filename)
            decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
            self.assertIsNone(decision["requirement_disposition"])
            self.assertIn(
                "requirement_boundary_not_explicit_ready",
                decision["views"]["requirement_to_project"]["reasons"],
            )

    def test_budget_true_requires_present_consistent_model_call_ledger(self) -> None:
        invalid_summaries = {
            "missing": None,
            "inconsistent_counts": {
                "max_model_calls": 1,
                "model_calls_used": 1,
                "model_calls_failed": 0,
                "remaining_model_calls": 1,
                "calls": [{"call_id": 0, "status": "completed"}],
            },
            "invalid_ledger": {
                "max_model_calls": 1,
                "model_calls_used": 1,
                "model_calls_failed": 0,
                "remaining_model_calls": 0,
                "calls": [{"call_id": 0, "status": "started"}],
            },
        }
        for case, summary in invalid_summaries.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "dataset"
                recorder = DatasetRecorder(root)
                project = _project()
                metadata = _verified_metadata()
                if summary is None:
                    metadata.pop("model_call_budget")
                else:
                    metadata["model_call_budget"] = summary
                recorder.start_sample(
                    "sample_invalid_budget",
                    "Build the declared project.",
                    self.platform,
                    metadata=metadata,
                )
                _write_final(recorder, "sample_invalid_budget", project)

                export_dir = Path(tmp) / "exports"
                recorder.export_training_views(export_dir)

                for filename in (
                    "requirement_to_his.jsonl",
                    "his_to_project.jsonl",
                    "requirement_to_project.jsonl",
                    "requirement_to_file.jsonl",
                ):
                    self.assertEqual(_read_jsonl(export_dir / filename), [], filename)
                decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
                self.assertFalse(decision["budget_compliant"])
                self.assertIn(
                    "budget_compliance_not_explicit_true",
                    decision["views"]["requirement_to_project"]["reasons"],
                )

    def test_failed_project_is_not_exported_as_verified_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project()
            recorder.start_sample(
                "sample_failed",
                "Build the project.",
                self.platform,
                metadata=_verified_metadata(),
            )
            recorder.write_attempt(
                "sample_failed",
                AttemptRecord(
                    attempt_id=0,
                    generated_project=project,
                    tool_results={
                        "sim_run": ToolResult(
                            stage="sim_run",
                            command=["vvp"],
                            status="failed",
                            exit_code=1,
                            stdout="TEST_FAIL\n",
                            stderr="",
                            duration_seconds=0.1,
                        )
                    },
                    diagnosis={"failure_type": "semantic_mismatch", "stage": "sim_run"},
                ),
            )
            labels = _verified_labels()
            labels["vpp_l3"] = False
            labels["checks"] = dict(labels["checks"])
            labels["checks"]["l2_sim_pass"] = False
            _write_final(recorder, "sample_failed", project, labels=labels)

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            for filename in (
                "his_to_project.jsonl",
                "requirement_to_project.jsonl",
                "requirement_to_file.jsonl",
            ):
                self.assertEqual(_read_jsonl(export_dir / filename), [], filename)
            diagnosis = _read_jsonl(export_dir / "failure_to_diagnosis.jsonl")
            self.assertEqual(len(diagnosis), 1)
            self.assertFalse(diagnosis[0]["verified_positive"])
            self.assertEqual(diagnosis[0]["training_target_class"], "diagnostic")
            decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
            self.assertIn(
                "vpp_l3_not_explicit_true",
                decision["views"]["requirement_to_project"]["reasons"],
            )

    def test_missing_credit_provenance_and_budget_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project()
            recorder.start_sample(
                "sample_legacy",
                "Build the project.",
                self.platform,
                metadata=_verified_metadata(),
            )
            _write_final(
                recorder,
                "sample_legacy",
                project,
                labels={"checks": _verified_labels()["checks"]},
                origins={},
            )

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            for filename in (
                "requirement_to_his.jsonl",
                "his_to_project.jsonl",
                "requirement_to_project.jsonl",
                "requirement_to_file.jsonl",
            ):
                self.assertEqual(_read_jsonl(export_dir / filename), [], filename)
            decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
            reasons = decision["views"]["requirement_to_project"]["reasons"]
            self.assertIn("automatic_pass_credit_not_explicit_true", reasons)
            self.assertIn("provenance_compliance_not_explicit_true", reasons)
            self.assertIn("budget_compliance_not_explicit_true", reasons)
            self.assertIn("file_provenance_incomplete", reasons)

    def test_explicit_credit_provenance_or_budget_violation_blocks_positive_views(self) -> None:
        for field in ("automatic_pass_credit", "provenance_compliant", "budget_compliant"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "dataset"
                recorder = DatasetRecorder(root)
                project = _project()
                recorder.start_sample(
                    "sample_violation",
                    "Build the project.",
                    self.platform,
                    metadata=_verified_metadata(),
                )
                labels = _verified_labels()
                labels[field] = False
                _write_final(recorder, "sample_violation", project, labels=labels)

                export_dir = Path(tmp) / "exports"
                recorder.export_training_views(export_dir)

                for filename in (
                    "requirement_to_his.jsonl",
                    "his_to_project.jsonl",
                    "requirement_to_project.jsonl",
                    "requirement_to_file.jsonl",
                ):
                    self.assertEqual(_read_jsonl(export_dir / filename), [], filename)

    def test_model_call_ledger_alone_cannot_attest_all_budget_axes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project()
            recorder.start_sample(
                "sample_budgeted",
                "Build the project.",
                self.platform,
                metadata={
                    "source": "model",
                    "generator_provider": "model",
                    "requirement_boundary": {"disposition": "ready"},
                    "model_call_budget": {
                        "max_model_calls": 2,
                        "model_calls_used": 1,
                        "remaining_model_calls": 1,
                        "calls": [{"call_id": 0, "status": "completed"}],
                    },
                },
            )
            labels = _verified_labels()
            labels.pop("budget_compliant")
            _write_final(recorder, "sample_budgeted", project, labels=labels)

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
            self.assertIsNone(decision["budget_compliant"])
            self.assertFalse(decision["views"]["requirement_to_project"]["eligible"])
            self.assertIn(
                "budget_compliance_not_explicit_true",
                decision["views"]["requirement_to_project"]["reasons"],
            )

    def test_direct_model_his_and_two_stage_testbench_use_explicit_origins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project()
            recorder.start_sample(
                "sample_direct_sources",
                "Build the project.",
                self.platform,
                metadata={
                    **_verified_metadata(
                        source="direct_model",
                        generator_provider="direct_model",
                    ),
                    "method_condition": "M0 Direct",
                    "contract_skeleton_mode": "legacy_full_project",
                },
            )
            _write_final(
                recorder,
                "sample_direct_sources",
                project,
                origins=_origins(
                    project,
                    system_his="model_generated",
                    testbench="model_generated",
                ),
            )
            recorder.start_sample(
                "sample_two_stage_sources",
                "Build the project.",
                self.platform,
                metadata={
                    **_verified_metadata(
                        source="two_stage_model",
                        generator_provider="two_stage_model",
                    ),
                    "method_condition": "M4 HIS-Skeleton",
                },
            )
            _write_final(
                recorder,
                "sample_two_stage_sources",
                project,
                origins=_origins(
                    project,
                    system_his="model_generated",
                    testbench="deterministic",
                ),
            )

            direct_trajectory = json.loads(
                (root / "sample_direct_sources" / "eval" / "trajectory.json").read_text(encoding="utf-8")
            )
            two_stage_trajectory = json.loads(
                (root / "sample_two_stage_sources" / "eval" / "trajectory.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                direct_trajectory["project"]["files"]["system_his.json"]["origin"],
                "model_generated",
            )
            self.assertEqual(
                direct_trajectory["project"]["files"]["sim/tb_top.v"]["origin"],
                "model_generated",
            )
            self.assertEqual(
                two_stage_trajectory["project"]["files"]["sim/tb_top.v"]["origin"],
                "deterministic",
            )
            self.assertTrue(two_stage_trajectory["project"]["provenance_complete"])

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)
            self.assertEqual(
                [row["sample_id"] for row in _read_jsonl(export_dir / "requirement_to_his.jsonl")],
                ["sample_two_stage_sources"],
            )
            self.assertEqual(
                [row["sample_id"] for row in _read_jsonl(export_dir / "his_to_project.jsonl")],
                ["sample_two_stage_sources"],
            )
            self.assertEqual(
                {row["sample_id"] for row in _read_jsonl(export_dir / "requirement_to_project.jsonl")},
                {"sample_direct_sources", "sample_two_stage_sources"},
            )

    def test_direct_project_without_his_can_export_method_neutral_views_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project(include_his=False)
            recorder.start_sample(
                "sample_direct",
                "Build the project.",
                self.platform,
                metadata={
                    **_verified_metadata(
                        source="direct_model",
                        generator_provider="direct_model",
                    ),
                    "method_condition": "M0 Direct",
                },
            )
            _write_final(recorder, "sample_direct", project)

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            self.assertEqual(_read_jsonl(export_dir / "requirement_to_his.jsonl"), [])
            self.assertEqual(_read_jsonl(export_dir / "his_to_project.jsonl"), [])
            self.assertEqual(len(_read_jsonl(export_dir / "requirement_to_project.jsonl")), 1)
            self.assertGreater(len(_read_jsonl(export_dir / "requirement_to_file.jsonl")), 0)

    def test_deterministic_reference_is_audited_but_not_mixed_into_model_training(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dataset"
            recorder = DatasetRecorder(root)
            project = _project()
            recorder.start_sample(
                "sample_reference",
                "Build the project.",
                self.platform,
                metadata={
                    **_verified_metadata(
                        source="deterministic",
                        generator_provider="deterministic",
                    ),
                    "failure_origin": "deterministic_template",
                    "method_condition": "M4 HIS-Skeleton",
                },
            )
            _write_final(
                recorder,
                "sample_reference",
                project,
                origins={path: {"origin": "deterministic"} for path in project.files},
            )

            export_dir = Path(tmp) / "exports"
            recorder.export_training_views(export_dir)

            for filename in (
                "requirement_to_his.jsonl",
                "his_to_project.jsonl",
                "requirement_to_project.jsonl",
                "requirement_to_file.jsonl",
            ):
                self.assertEqual(_read_jsonl(export_dir / filename), [], filename)
            decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
            self.assertIn(
                "deterministic_reference_not_training_source",
                decision["views"]["requirement_to_project"]["reasons"],
            )

    def test_boundary_not_run_outcomes_remain_recorded_but_never_become_positive(self) -> None:
        for index, (failure_type, disposition) in enumerate(
            (
                ("requirement_clarification_required", "needs_clarification"),
                ("capability_gap", "capability_gap"),
                ("not_run", "not_run"),
            )
        ):
            with self.subTest(failure_type=failure_type), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "dataset"
                recorder = DatasetRecorder(root)
                sample_id = f"sample_boundary_{index}"
                empty_project = GeneratedProject(project_name="blocked", files={})
                recorder.start_sample(
                    sample_id,
                    "Ambiguous requirement.",
                    self.platform,
                    metadata={
                        "source": "model",
                        "generator_provider": "model",
                        "requirement_boundary": {"disposition": disposition},
                        "model_call_budget": _verified_metadata()["model_call_budget"],
                    },
                )
                recorder.write_attempt(
                    sample_id,
                    AttemptRecord(
                        attempt_id=0,
                        generated_project=empty_project,
                        tool_results={
                            "generation": ToolResult(
                                stage="generation",
                                command=["project_generator"],
                                status="not_run",
                                exit_code=None,
                                stdout="",
                                stderr="",
                                duration_seconds=0.0,
                                skip_reason=failure_type,
                            )
                        },
                        diagnosis={"failure_type": failure_type, "stage": "generation"},
                    ),
                )
                recorder.write_final(
                    sample_id,
                    empty_project,
                    labels={
                        "automatic_pass_credit": False,
                        "failure_type": failure_type,
                        "provenance_compliant": False,
                        "budget_compliant": True,
                        "vpp_l3": False,
                    },
                    measured_qor={},
                    tool_versions={},
                    trajectory={"sample_id": sample_id, "attempts": []},
                )

                export_dir = Path(tmp) / "exports"
                recorder.export_training_views(export_dir)

                for filename in (
                    "requirement_to_his.jsonl",
                    "his_to_project.jsonl",
                    "requirement_to_project.jsonl",
                    "requirement_to_file.jsonl",
                ):
                    self.assertEqual(_read_jsonl(export_dir / filename), [], filename)
                self.assertTrue((root / sample_id / "eval" / "trajectory.json").is_file())
                diagnosis = _read_jsonl(export_dir / "failure_to_diagnosis.jsonl")
                self.assertEqual(diagnosis[0]["diagnosis"]["failure_type"], failure_type)
                self.assertFalse(diagnosis[0]["verified_positive"])
                decision = _read_jsonl(export_dir / "training_view_eligibility.jsonl")[0]
                self.assertIn(
                    f"requirement_boundary_{disposition}",
                    decision["views"]["requirement_to_project"]["reasons"],
                )


if __name__ == "__main__":
    unittest.main()
