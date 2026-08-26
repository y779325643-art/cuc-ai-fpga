import json
import tempfile
import unittest
from pathlib import Path

from sr2fpga_agent.model_budget import ModelCallBudget, ModelCallBudgetExceeded
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.requirement_audit import (
    ClarificationAnswerBranch,
    RequirementAuditGold,
    build_requirement_audit_artifact,
    build_requirement_audit_case,
)
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary
from sr2fpga_agent.requirement_envelope import build_requirement_envelope
from sr2fpga_agent.runner import RunnerConfig, TaskConfig, run_batch, runner_preflight


def _platform() -> PlatformProfile:
    return PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")


class _Client:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error

    def chat(self, _messages):
        if self.error is not None:
            raise self.error
        return "ok"

    def stream_chat(self, _messages):
        return self.chat(_messages)


class Paper1ProtocolTest(unittest.TestCase):
    def test_requirement_provenance_separates_defaults_assumptions_and_unknowns(self) -> None:
        envelope = build_requirement_envelope(
            "Build an 8-bit counter.",
            defaults={"reset_polarity": "active_low"},
            assumptions={"latency_cycles": 1},
        )

        self.assertEqual(envelope.default_facts, {"reset_polarity": "active_low"})
        self.assertEqual(envelope.assumption_facts, {"latency_cycles": 1})
        self.assertIn("clock_frequencies_hz", envelope.unknown_facts)
        self.assertEqual(
            envelope.requirement_trace_template()["required_facts"]["latency_cycles"]["origin"],
            "assumption",
        )

    def test_requirement_fact_cannot_be_both_default_and_assumption(self) -> None:
        with self.assertRaisesRegex(ValueError, "both defaults and assumptions"):
            build_requirement_envelope(
                "Build a counter.",
                defaults={"latency_cycles": 1},
                assumptions={"latency_cycles": 2},
            )

    def test_ambiguity_precedes_capability_gap(self) -> None:
        request = ProjectRequest(
            task_type="unclassified",
            width=8,
            project_name="adc",
            description="Build an 8-bit ADC interface.",
        )

        decision = evaluate_requirement_boundary(request, _platform())

        self.assertEqual(decision.disposition, "needs_clarification")
        self.assertIn("adc_interface_contract", decision.clarification_fact_ids)
        self.assertIn("adc_interface", decision.capability_gap_ids)

    def test_ready_boundary_is_recipe_independent(self) -> None:
        request = ProjectRequest(
            task_type="counter",
            width=8,
            project_name="counter",
            description="Build an 8-bit counter with active-low reset.",
        )

        decision = evaluate_requirement_boundary(request, _platform())

        self.assertEqual(decision.disposition, "ready")
        self.assertEqual(decision.route.strategy, "exact_family")
        self.assertEqual(len(decision.to_dict()["decision_sha256"]), 64)

    def test_offline_audit_stops_before_generation_and_validates_contract(self) -> None:
        request = ProjectRequest(
            task_type="unclassified",
            width=8,
            project_name="adc",
            description="Build an 8-bit ADC interface.",
        )
        case = build_requirement_audit_case(
            request,
            _platform(),
            base_requirement_cluster_id="cluster-001",
            ambiguity_case_id="case-ambiguous",
            gold=RequirementAuditGold(
                disposition="needs_clarification",
                reason_ids=("missing-adc-contract",),
                fact_ids=("adc_interface_contract",),
                clarification_answer_branches=(
                    ClarificationAnswerBranch(
                        branch_id="answer-1",
                        answer_facts={"adc_interface_contract": "sample-rate-and-timing"},
                        expected_replay_disposition="capability_gap",
                    ),
                ),
            ),
        )

        artifact = build_requirement_audit_artifact("audit-run-001", [case])

        self.assertFalse(case["boundary_result"]["generation_boundary_crossed"])
        self.assertEqual(case["boundary_result"]["counters"]["model_calls"], 0)
        self.assertEqual(artifact["summary"]["false_proceed_count"], 0)
        self.assertEqual(
            artifact["summary"]["confusion_matrix"]["needs_clarification"]
            ["needs_clarification"],
            1,
        )

        escaped_case = dict(case)
        escaped_case["boundary_result"] = {
            **case["boundary_result"],
            "generation_boundary_crossed": True,
        }
        escaped = build_requirement_audit_artifact("audit-run-escaped", [escaped_case])
        self.assertEqual(escaped["summary"]["false_proceed_count"], 1)
        self.assertEqual(escaped["summary"]["generation_boundary_crossed_count"], 1)
        self.assertEqual(len(artifact["audit_sha256"]), 64)

    def test_offline_audit_cannot_use_evaluator_task_type_to_resolve_ambiguity(self) -> None:
        request = ProjectRequest(
            task_type="counter",
            width=8,
            project_name="hidden_family_label",
            description="Build an 8-bit synchronous hardware block.",
        )

        case = build_requirement_audit_case(
            request,
            _platform(),
            base_requirement_cluster_id="cluster-hidden-label",
            ambiguity_case_id="case-hidden-label",
            gold=RequirementAuditGold(
                disposition="needs_clarification",
                fact_ids=("functional_decomposition",),
                clarification_answer_branches=(
                    ClarificationAnswerBranch(
                        branch_id="answer-hidden-label",
                        answer_facts={"functional_decomposition": "counter"},
                        expected_replay_disposition="ready",
                    ),
                ),
            ),
        )

        self.assertEqual(
            case["boundary_result"]["predicted_disposition"],
            "needs_clarification",
        )
        projection = case["generation_visible_projection"]
        self.assertEqual(projection["width_bits"], 8)
        self.assertNotIn("task_type", projection)
        facts = case["preflight_projection"]["envelope"]["facts"]
        declared = next(item for item in facts if item["fact_id"] == "declared_task_type")
        self.assertEqual(declared["origin"], "unresolved")
        self.assertIsNone(declared["value"])

    def test_offline_audit_keeps_not_run_out_of_disposition_error_counts(self) -> None:
        request = ProjectRequest(
            task_type="unclassified",
            width=8,
            project_name="counter_not_run",
            description="Build an 8-bit synchronous counter.",
        )
        case = build_requirement_audit_case(
            request,
            _platform(),
            base_requirement_cluster_id="cluster-not-run",
            ambiguity_case_id="case-not-run",
            gold=RequirementAuditGold(disposition="ready"),
        )
        case["boundary_result"] = {
            **case["boundary_result"],
            "execution_status": "not_run",
            "not_run_reason_id": "audit_infrastructure_unavailable",
        }
        case["boundary_result"].pop("predicted_disposition")

        artifact = build_requirement_audit_artifact("audit-run-not-run", [case])
        summary = artifact["summary"]

        self.assertEqual(summary["execution_status_counts"], {"completed": 0, "not_run": 1})
        self.assertEqual(
            summary["predicted_disposition_counts"],
            {"ready": 0, "needs_clarification": 0, "capability_gap": 0},
        )
        self.assertEqual(
            summary["confusion_matrix"]["ready"],
            {"ready": 0, "needs_clarification": 0, "capability_gap": 0},
        )
        self.assertEqual(summary["false_proceed_count"], 0)
        self.assertEqual(summary["false_block_count"], 0)

    def test_offline_audit_rejects_synthetic_task_type_fallback_text(self) -> None:
        request = ProjectRequest(
            task_type="counter",
            width=8,
            project_name="missing_public_text",
        )

        with self.assertRaisesRegex(ValueError, "explicit public requirement text"):
            build_requirement_audit_case(
                request,
                _platform(),
                base_requirement_cluster_id="cluster-no-text",
                ambiguity_case_id="case-no-text",
                gold=RequirementAuditGold(disposition="ready"),
            )

    def test_model_call_budget_counts_failed_calls_and_fails_before_overrun(self) -> None:
        events = []
        budget = ModelCallBudget(1, event_sink=events.append)
        client = budget.client(_Client(error=RuntimeError("provider failed")), "req2his")

        with self.assertRaisesRegex(RuntimeError, "provider failed"):
            client.stream_chat([{"role": "user", "content": "hello"}])
        with self.assertRaises(ModelCallBudgetExceeded):
            client.stream_chat([{"role": "user", "content": "again"}])

        summary = budget.summary()
        self.assertEqual(summary["model_calls_used"], 1)
        self.assertEqual(summary["model_calls_failed"], 1)
        self.assertEqual(events[-1]["event"], "model_call_failed")

    def test_unsigned_official_population_fails_before_run_directory_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[
                    TaskConfig(
                        source="deterministic",
                        task_type="counter",
                        widths=[8],
                        count=1,
                        method_condition="reference_deterministic",
                        analysis_population="official_vpp",
                    )
                ],
            )

            report = runner_preflight(config, run_id="unsigned-official")
            self.assertFalse(report["ok"])
            self.assertTrue(any("signed G4b" in item for item in report["errors"]))
            with self.assertRaisesRegex(SystemExit, "signed G4b"):
                run_batch(config, run_id="unsigned-official")
            self.assertFalse((root / "runs" / "unsigned-official").exists())

    def test_ambiguity_population_cannot_enter_project_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deterministic",
                repair_provider="none",
                max_attempts=1,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[
                    TaskConfig(
                        source="deterministic",
                        task_type="counter",
                        widths=[8],
                        count=1,
                        analysis_population="ambiguity_audit",
                    )
                ],
            )

            with self.assertRaisesRegex(SystemExit, "sealed evaluator-owned"):
                run_batch(config, run_id="wrong-audit-path")
            self.assertFalse((root / "runs" / "wrong-audit-path").exists())

    def test_non_ready_runner_sample_does_not_resolve_model_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = RunnerConfig(
                dataset_root=root / "datasets",
                export_root=root / "exports",
                run_root=root / "runs",
                provider="deepseek-his-v12",
                repair_provider="same_as_source",
                max_attempts=2,
                refresh_exports=False,
                line_b_targets={"max_samples": 1},
                tasks=[
                    TaskConfig(
                        source="deepseek-his-v12",
                        task_type="unclassified",
                        widths=[8],
                        count=1,
                        requirement="Build an 8-bit hardware block.",
                    )
                ],
            )

            summary = run_batch(config, run_id="clarification-stop")

            self.assertEqual(summary["pass_level_breakdown"], {"GEN_FAIL": 1})
            sample_dir = root / "datasets" / "sample_runner_unclassified_8_000001"
            metadata = json.loads(
                (sample_dir / "metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                metadata["requirement_boundary"]["disposition"],
                "needs_clarification",
            )
            self.assertEqual(metadata["model_call_budget"]["model_calls_used"], 0)


if __name__ == "__main__":
    unittest.main()
