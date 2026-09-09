from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path

import pytest

from sr2fpga_agent.artifact_store import ArtifactConflictError, ArtifactRef, ArtifactStore
from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.cost_accounting import (
    COST_AXES,
    AccountingCommandRunner,
    AttemptCostLedger,
    AttemptCostLedgerRouter,
    CostAccountingError,
    reconcile_attempt_trajectory,
    reconcile_cost_events,
)
from sr2fpga_agent.model_budget import (
    ModelCallBudget,
    ModelCallBudgetExceeded,
    _normalized_response_provenance,
)
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest, ToolResult
from sr2fpga_agent.generation.direct_project import DirectProjectGenerator
from sr2fpga_agent.episode_outcome import (
    project_development_public_evaluation,
    reconcile_development_episode_outcome,
)
from sr2fpga_agent.evaluator_dispatch import (
    DevelopmentHiddenEvaluationAuthority,
    read_verified_development_hidden_conformance_outcome,
)
from sr2fpga_agent.public_evaluator import read_verified_development_public_outcome
from sr2fpga_agent.public_l2_harness import (
    DevelopmentTrustedPublicL2Harness,
    TrustedPublicL2HarnessFile,
)


TEST_ROOT = Path(__file__).resolve().parent / ".runner_tmp"


def _test_root() -> Path:
    path = TEST_ROOT / f"cost-accounting-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


class _FailingClient:
    def stream_chat(self, messages):
        raise RuntimeError("provider failed")


class _CountedTransportClient:
    def chat(self, messages):
        return "ok"

    def consume_transport_attempt_count(self):
        return 2

    def consume_token_usage(self):
        return {"input_tokens": 11, "output_tokens": 7, "cached_tokens": 3}

    def consume_response_provenance(self):
        return {
            "provider_adapter": "openai_compatible",
            "provider_model": "test-model",
            "gateway_base_url_sha256": "a" * 64,
            "requested_decoding_seed": 17,
            "seed_forwarding_status": "forwarded",
            "deterministic_seed_control": "requested_unverified",
            "provider_system_fingerprint": "fp_test_backend",
            "system_fingerprint_status": "reported",
        }


class _FailingCountedTransportClient:
    def stream_chat(self, messages):
        raise RuntimeError("provider failed after usage")

    def consume_transport_attempt_count(self):
        return 2

    def consume_token_usage(self):
        return {"input_tokens": 11, "output_tokens": 7, "cached_tokens": 3}


class _PassingRunner:
    def run(self, command, cwd, stage, timeout_seconds=30):
        stdout = "Number of cells: 1\n  SB_LUT4 1\n" if stage == "synth" else ""
        if stage == "sim_run":
            stdout = "TEST_PASS\n"
        if stage == "public_l2_sim":
            trusted_text = "\n".join(path.read_text(encoding="utf-8") for path in (Path(cwd) / "__sr2fpga_trusted_public_l2").rglob("*.*"))
            stdout = "\n".join(re.findall(r"SR2FPGA_TRUSTED_COMPLETE_[0-9a-f]{32}", trusted_text)) + "\n"
        return ToolResult(
            stage=stage,
            command=list(command),
            status="passed",
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_seconds=0.01,
        )


class _RecordingPassingRunner(_PassingRunner):
    def __init__(self) -> None:
        self.stages: list[str] = []

    def run(self, command, cwd, stage, timeout_seconds=30):
        self.stages.append(stage)
        return super().run(command, cwd, stage, timeout_seconds)


def _trusted_public_l2_harness() -> DevelopmentTrustedPublicL2Harness:
    content = "module trusted_tb; top dut(); initial $finish; endmodule\n"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return DevelopmentTrustedPublicL2Harness(
        harness_id="trusted-counter8-v1",
        testbench_top="trusted_tb",
        language_standard="verilog-2005",
        files=(TrustedPublicL2HarnessFile("tb.v", content, digest),),
        timeout_seconds=30,
        manifest_sha256="e" * 64,
        bundle_sha256="f" * 64,
    )


class _SequenceChatClient:
    def __init__(self, responses: list[str]) -> None:
        self._responses = iter(responses)

    def chat(self, messages):
        return next(self._responses)


class _StaticProjectGenerator:
    def generate(self, _request, _platform):
        return _canonical_project()


def _canonical_project(*, composite: bool = False) -> GeneratedProject:
    rtl = (
        "module top;\n"
        "// SR2FPGA_BEHAVIOR_BEGIN\n"
        "assign out = in;\n"
        "// SR2FPGA_BEHAVIOR_END\n"
        "endmodule\n"
        if composite
        else "module top; endmodule\n"
    )
    files = {
        "manifest.json": json.dumps(
            {
                "contract_version": "project-package-v1",
                "project_name": "counter_8bit",
                "top": {
                    "module": "top",
                    "source": "rtl/top.v",
                    "interface": {"ports": []},
                },
                "sources": [
                    {
                        "path": "rtl/top.v",
                        "role": "rtl_source",
                        "language": "verilog",
                    }
                ],
                "artifacts": [],
                "build": {
                    "toolchain_id": "open_source",
                    "language_standard": "verilog-2005",
                },
            }
        )
        + "\n",
        "rtl/top.v": rtl,
    }
    return GeneratedProject("counter_8bit", files)


def test_cost_ledger_rebuilds_complete_full_axis_summary() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        ledger = AttemptCostLedger(
            store,
            episode_id="episode-001",
            attempt_id="attempt-001",
            method_condition="M5",
            failure_origin="synthetic_injected",
        )
        ledger.reserve(
            "logical_model_calls",
            1,
            stage="req2his",
            visibility_class="accounting",
            limit=3,
            used_after=1,
            started_at=1.0,
        )
        ledger.record_cost(
            stage="req2his",
            visibility_class="accounting",
            cost_delta={
                "input_tokens": 10,
                "output_tokens": 5,
                "cached_tokens": 0,
                "provider_transport_attempts": 1,
                "planner_parser_schema_retries": 0,
                "outer_repair_attempts": 1,
                "public_tool_calls": 2,
                "hidden_evaluator_tool_calls": 1,
                "hidden_infrastructure_retries": 0,
                "wall_time": 2.5,
                "eda_time": 1.25,
                "hidden_evaluator_runtime": 0.5,
            },
            duration_seconds=2.5,
            started_at=2.0,
        )
        ledger.close(started_at=5.0)

        result = reconcile_cost_events(store, ledger.event_refs)

        assert result.payload["all_required_axes_reconciled"] is True
        assert result.payload["axes"]["logical_model_calls"]["value"] == 1
        assert result.payload["axes"]["public_tool_calls"]["value"] == 2
        assert result.payload["axes"]["wall_time"]["value"] == 2.5
        assert result.payload["event_count"] == 3
        assert store.read_verified(result.artifact_ref)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_model_budget_emits_failed_call_exhaustion_and_unavailable_tokens() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        ledger = AttemptCostLedger(
            store,
            episode_id="episode-model",
            attempt_id="attempt-001",
            method_condition="M3",
            failure_origin="natural_llm",
        )
        budget = ModelCallBudget(1, attempt_cost_ledger=ledger)
        client = budget.client(_FailingClient(), "req2his")

        with pytest.raises(RuntimeError, match="provider failed"):
            client.stream_chat([{"role": "user", "content": "hello"}])
        with pytest.raises(ModelCallBudgetExceeded):
            client.stream_chat([{"role": "user", "content": "again"}])

        observed = {
            "logical_model_calls",
            "provider_transport_attempts",
            "input_tokens",
            "output_tokens",
            "cached_tokens",
        }
        ledger.close(zero_axes=set(COST_AXES) - observed)
        result = reconcile_cost_events(store, ledger.event_refs)

        assert result.payload["failure_count"] == 1
        assert result.payload["budget_exhaustion_count"] == 1
        assert result.payload["axes"]["logical_model_calls"]["value"] == 1
        assert result.payload["axes"]["provider_transport_attempts"] == {
            "status": "unavailable",
            "value": None,
            "reason": "provider_transport_attempt_count_unavailable",
        }
        assert result.payload["axes"]["input_tokens"] == {
            "status": "unavailable",
            "value": None,
            "reason": "provider_token_usage_unavailable",
        }
        assert budget.summary()["token_accounting"] == (
            "partial_or_unavailable_provider_response"
        )
        assert result.payload["all_required_axes_reconciled"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_model_budget_records_provider_reported_transport_retry_count() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        ledger = AttemptCostLedger(
            store,
            episode_id="episode-transport-retry",
            attempt_id="attempt-001",
            method_condition="M0",
            failure_origin="natural_llm",
        )
        budget = ModelCallBudget(1, attempt_cost_ledger=ledger)

        assert budget.client(_CountedTransportClient(), "direct").chat([]) == "ok"

        ledger.close(zero_axes=set(COST_AXES) - set(ledger.observed_axes))
        result = reconcile_cost_events(store, ledger.event_refs)
        assert result.payload["axes"]["logical_model_calls"]["value"] == 1
        assert result.payload["axes"]["provider_transport_attempts"] == {
            "status": "measured",
            "value": 2,
            "reason": None,
        }
        assert result.payload["axes"]["input_tokens"]["value"] == 11
        assert result.payload["axes"]["output_tokens"]["value"] == 7
        assert result.payload["axes"]["cached_tokens"]["value"] == 3
        assert budget.summary()["token_accounting"] == "provider_reported"
        assert budget.summary()["input_tokens"] == 11
        assert budget.summary()["calls"][0]["provider_response_provenance"] == {
            "provider_adapter": "openai_compatible",
            "provider_model": "test-model",
            "gateway_base_url_sha256": "a" * 64,
            "requested_decoding_seed": 17,
            "seed_forwarding_status": "forwarded",
            "deterministic_seed_control": "requested_unverified",
            "provider_system_fingerprint": "fp_test_backend",
            "system_fingerprint_status": "reported",
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    "seed,forwarding,control",
    (
        (None, "forwarded", "not_requested"),
        (None, "not_requested", "requested_unverified"),
        (17, "not_requested", "requested_unverified"),
        (17, "forwarded", "not_requested"),
    ),
)
def test_model_budget_rejects_contradictory_seed_provenance(
    seed, forwarding, control
) -> None:
    assert _normalized_response_provenance(
        {
            "provider_adapter": "openai_compatible",
            "provider_model": "test-model",
            "gateway_base_url_sha256": "a" * 64,
            "requested_decoding_seed": seed,
            "seed_forwarding_status": forwarding,
            "deterministic_seed_control": control,
            "provider_system_fingerprint": None,
            "system_fingerprint_status": "unavailable",
        }
    ) is None


def test_model_budget_records_reported_usage_from_failed_call() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        ledger = AttemptCostLedger(
            store,
            episode_id="episode-failed-usage",
            attempt_id="attempt-001",
            method_condition="M0",
            failure_origin="natural_llm",
        )
        budget = ModelCallBudget(1, attempt_cost_ledger=ledger)
        client = budget.client(_FailingCountedTransportClient(), "direct")

        with pytest.raises(RuntimeError, match="provider failed after usage"):
            client.stream_chat([])

        ledger.close(zero_axes=set(COST_AXES) - set(ledger.observed_axes))
        result = reconcile_cost_events(store, ledger.event_refs)
        assert result.payload["failure_count"] == 1
        assert result.payload["axes"]["provider_transport_attempts"]["value"] == 2
        assert result.payload["axes"]["input_tokens"]["value"] == 11
        assert result.payload["axes"]["output_tokens"]["value"] == 7
        assert result.payload["axes"]["cached_tokens"]["value"] == 3
        assert budget.summary()["token_accounting"] == "provider_reported"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_attempt_ledger_rejects_unknown_failure_origin_before_writing() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        with pytest.raises(CostAccountingError, match="unknown accounting failure origin"):
            AttemptCostLedger(
                store,
                episode_id="episode-invalid-origin",
                attempt_id="attempt-001",
                method_condition="M0",
                failure_origin="provider_specific_free_text",
            )
        assert store.reference(
            "attempt-events/episode-invalid-origin/attempt-001/000000"
        ) is None
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cost_reducer_rejects_open_or_reordered_streams() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        ledger = AttemptCostLedger(
            store,
            episode_id="episode-order",
            attempt_id="attempt-001",
            method_condition="M0",
            failure_origin=None,
        )
        ledger.record_cost(
            stage="public_lint",
            visibility_class="public",
            cost_delta={"public_tool_calls": 1},
        )
        with pytest.raises(CostAccountingError, match="not closed"):
            reconcile_cost_events(store, ledger.event_refs)

        ledger.close(zero_axes=set(COST_AXES) - {"public_tool_calls"})
        with pytest.raises(CostAccountingError, match="sequence or parent"):
            reconcile_cost_events(store, reversed(ledger.event_refs))
        with pytest.raises(CostAccountingError, match="already closed"):
            ledger.close()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cost_reducer_rejects_validly_shaped_but_false_declared_total() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        ledger = AttemptCostLedger(
            store,
            episode_id="episode-false-total",
            attempt_id="attempt-001",
            method_condition="M1",
            failure_origin="synthetic_injected",
        )
        ledger.record_cost(
            stage="project_repair",
            visibility_class="public",
            cost_delta={"outer_repair_attempts": 1},
        )
        ledger.close(zero_axes=set(COST_AXES) - {"outer_repair_attempts"})

        false_store = ArtifactStore(root / "false-store")
        first_event = json.loads(store.read_verified(ledger.event_refs[0]))
        first_ref = false_store.put_validated_json(
            "attempt-events/episode-false-total/attempt-001/000000",
            first_event,
            contract_key="attempt_event",
        )
        false_close = json.loads(store.read_verified(ledger.event_refs[-1]))
        false_close["cost_delta"]["outer_repair_attempts"] = 2
        unsigned = {key: value for key, value in false_close.items() if key != "event_id"}
        encoded = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        false_close["event_id"] = "attempt-event-" + hashlib.sha256(encoded).hexdigest()
        false_ref = false_store.put_validated_json(
            "attempt-events/episode-false-total/attempt-001/000001",
            false_close,
            contract_key="attempt_event",
        )

        with pytest.raises(CostAccountingError, match="does not match raw events"):
            reconcile_cost_events(false_store, (first_ref, false_ref))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cost_ledger_rejects_a_second_writer_for_the_same_attempt_slot() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        kwargs = {
            "episode_id": "episode-fork",
            "attempt_id": "attempt-001",
            "method_condition": "M0",
            "failure_origin": None,
        }
        first = AttemptCostLedger(store, **kwargs)
        second = AttemptCostLedger(store, **kwargs)
        first.record_cost(
            stage="public_lint",
            visibility_class="public",
            cost_delta={"public_tool_calls": 1},
            started_at=1.0,
        )
        with pytest.raises(ArtifactConflictError, match="different content"):
            second.record_cost(
                stage="public_synthesis",
                visibility_class="public",
                cost_delta={"public_tool_calls": 1},
                started_at=2.0,
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_trajectory_v2_becomes_complete_only_with_matching_terminal_candidate() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        ledger = AttemptCostLedger(
            store,
            episode_id="episode-terminal",
            attempt_id="attempt-000",
            method_condition="M5",
            failure_origin="natural_llm",
            candidate_id="episode-terminal-attempt-000",
            input_artifact_hashes=("a" * 64,),
        )
        ledger.record_cost(
            stage="attempt_lifecycle",
            visibility_class="accounting",
            cost_delta={"wall_time": 0.1},
            output_artifact_hashes=("b" * 64,),
        )
        ledger.close(zero_axes=set(COST_AXES) - set(ledger.observed_axes))
        summary = reconcile_cost_events(store, ledger.event_refs)
        terminal_ref = store.put_validated_json(
            "terminal-candidates/episode-terminal-attempt-000",
            {
                "contract_version": "terminal-candidate-v1",
                "candidate_id": "episode-terminal-attempt-000",
                "episode_id": "episode-terminal",
                "method_condition_id": "M5",
                "project_name": "counter_8bit",
                "project_envelope_sha256": "c" * 64,
                "requirement_projection_sha256": "d" * 64,
                "creation_event_id": "event-" + "e" * 64,
                "project_files": [
                    {
                        "path": "rtl/top.v",
                        "artifact_key": "candidate-files/rtl/top.v",
                        "sha256": "f" * 64,
                    }
                ],
                "public_evidence_sha256": [],
            },
            contract_key="terminal_candidate",
        )

        trajectory = reconcile_attempt_trajectory(
            store,
            [summary.artifact_ref],
            terminal_candidate_ref=terminal_ref,
        )

        assert trajectory.payload["lineage_complete"] is True
        assert trajectory.payload["missing_lineage_reasons"] == []
        assert trajectory.payload["terminal_candidate_ref"] == terminal_ref.to_dict()
        assert store.read_verified(trajectory.artifact_ref)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_router_drives_model_and_tool_costs_into_the_active_attempt() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        router = AttemptCostLedgerRouter()
        ledger = AttemptCostLedger(
            store,
            episode_id="episode-routed",
            attempt_id="attempt-000",
            method_condition="M0",
            failure_origin=None,
        )
        router.activate(ledger)
        budget = ModelCallBudget(1, attempt_cost_ledger_provider=router.current)
        call_id, started = budget.reserve("direct_generation", "generate", 12)
        budget.finish(
            call_id,
            "direct_generation",
            "generate",
            started,
            error=RuntimeError("failed"),
        )
        runner = AccountingCommandRunner(_PassingRunner(), router)
        runner.run(["tool"], root, "lint")

        ledger.close(zero_axes=set(COST_AXES) - set(ledger.observed_axes))
        result = reconcile_cost_events(store, ledger.event_refs)

        assert result.payload["axes"]["logical_model_calls"]["value"] == 1
        assert result.payload["axes"]["public_tool_calls"]["value"] == 1
        assert result.payload["axes"]["eda_time"]["value"] == pytest.approx(0.01)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_agent_closes_one_reconciled_cost_summary_for_a_normal_attempt() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        router = AttemptCostLedgerRouter()

        def factory(attempt_id: int) -> AttemptCostLedger:
            return AttemptCostLedger(
                store,
                episode_id="sample-accounted",
                attempt_id=f"attempt-{attempt_id:03d}",
                method_condition="M0",
                failure_origin=None,
            )

        agent = DataGenerationAgent(
            root / "dataset",
            command_runner=_PassingRunner(),
            attempt_cost_ledger_factory=factory,
            attempt_cost_router=router,
        )
        result = agent.run_one(
            "sample-accounted",
            "Design an 8-bit counter.",
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
        )

        assert router.current() is None
        assert len(agent.last_cost_summaries) == 1
        assert result["cost_summary_refs"] == [
            agent.last_cost_summaries[0].artifact_ref.to_dict()
        ]
        assert result["canonical_trajectory_ref"]["key"] == (
            "trajectories/sample-accounted/M0"
        )
        canonical = agent.last_canonical_trajectory
        assert canonical is not None
        assert canonical.payload["contract_version"] == "trajectory-v2"
        assert canonical.payload["attempts"][0]["cost_summary_ref"] == (
            agent.last_cost_summaries[0].artifact_ref.to_dict()
        )
        assert canonical.payload["lineage_complete"] is False
        assert canonical.payload["missing_lineage_reasons"] == [
            "attempt-000:candidate_id_missing",
            "terminal_candidate_seal_unavailable:accounting_identity_missing",
        ]
        summary = agent.last_cost_summaries[0].payload
        assert summary["accounting_closed"] is True
        assert summary["axes"]["public_tool_calls"]["value"] >= 1
        assert summary["axes"]["wall_time"]["value"] >= 0
        assert summary["axes"]["logical_model_calls"]["value"] == 0
        assert summary["axes"]["planner_parser_schema_retries"]["value"] == 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    (
        "hidden_status",
        "expected_hidden_l2",
        "expected_development_vpp_status",
        "expected_development_vpp",
        "expected_vpp_reasons",
    ),
    [
        (
            "pass",
            {"status": "pass", "reason": None},
            "evaluated",
            True,
            [],
        ),
        (
            "fail",
            {"status": "fail", "reason": None},
            "evaluated",
            False,
            ["hidden_l2_failed"],
        ),
        (
            "opaque",
            {"status": "not_run", "reason": "invalid_evaluator_outcome"},
            "not_evaluated",
            None,
            ["hidden_l2_not_run:invalid_evaluator_outcome"],
        ),
    ],
)
def test_agent_development_authority_binds_public_and_hidden_to_one_terminal(
    hidden_status: str,
    expected_hidden_l2: dict[str, str | None],
    expected_development_vpp_status: str,
    expected_development_vpp: bool | None,
    expected_vpp_reasons: list[str],
) -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        router = AttemptCostLedgerRouter()

        def factory(attempt_id: int) -> AttemptCostLedger:
            return AttemptCostLedger(
                store,
                episode_id="sample-authority",
                attempt_id=f"attempt-{attempt_id:03d}",
                method_condition="M0",
                failure_origin=None,
                candidate_id=f"sample-authority-attempt-{attempt_id:03d}",
            )

        hidden_hashes: list[str] = []
        hidden = DevelopmentHiddenEvaluationAuthority(
            store,
            ArtifactStore(root / "hidden-evaluator"),
            lambda evaluator_input: hidden_hashes.append(
                evaluator_input.terminal_candidate_sha256
            )
            or {"outcome": hidden_status, "private_case": "must-not-leak"},
        )
        public_runner = _RecordingPassingRunner()
        agent = DataGenerationAgent(
            root / "dataset",
            command_runner=public_runner,
            project_generator=_StaticProjectGenerator(),
            max_attempts=1,
            attempt_cost_ledger_factory=factory,
            attempt_cost_router=router,
            development_public_candidate_store=store,
            development_public_evaluator_store=ArtifactStore(root / "public-evaluator"),
            development_public_workspace_root=root / "public-workspaces",
            development_trusted_public_l2_harness=_trusted_public_l2_harness(),
            development_hidden_evaluation_authority=hidden,
            development_hidden_private_commitment=b"private",
        )
        result = agent.run_one(
            "sample-authority",
            "Design an 8-bit counter.",
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
            metadata={
                "method_condition": "M0",
                "analysis_population": "excluded",
                "requirement": "Design an 8-bit counter.",
            },
        )

        terminal_ref = ArtifactRef(**agent.last_canonical_trajectory.payload["terminal_candidate_ref"])
        terminal_public_ref = ArtifactRef(**result["development_terminal_public_outcome_ref"])
        terminal_public = read_verified_development_public_outcome(
            store, terminal_public_ref
        )
        assert terminal_public["terminal_candidate_sha256"] == terminal_ref.sha256
        assert hidden_hashes == [terminal_ref.sha256]
        assert terminal_public["stage_outcomes"]["public_l2"] == {
            "status": "pass",
            "reason": None,
        }
        assert terminal_public["public_l2_harness"] == {
            "status": "available",
            "harness_id": "trusted-counter8-v1",
            "manifest_sha256": "e" * 64,
            "bundle_sha256": "f" * 64,
            "reason": None,
        }
        assert public_runner.stages.count("public_l2_compile") == 2
        assert public_runner.stages.count("public_l2_sim") == 2
        assert agent.last_cost_summaries[0].payload["axes"]["public_tool_calls"][
            "value"
        ] >= 8
        trajectory = agent.last_canonical_trajectory.payload
        assert trajectory["development_terminal_selection_ref"] == result[
            "development_terminal_selection_ref"
        ]
        assert trajectory["development_selected_public_outcome_ref"] == result[
            "development_selected_public_outcome_ref"
        ]
        assert trajectory["development_terminal_public_outcome_ref"] == result[
            "development_terminal_public_outcome_ref"
        ]
        hidden_conformance_ref = ArtifactRef(
            **result["development_hidden_conformance_outcome_ref"]
        )
        hidden_conformance = read_verified_development_hidden_conformance_outcome(
            store,
            hidden_conformance_ref,
        )
        assert hidden_conformance["hidden_l2"] == expected_hidden_l2
        assert "must-not-leak" not in json.dumps(hidden_conformance)
        assert trajectory["development_hidden_conformance_outcome_ref"] == (
            hidden_conformance_ref.to_dict()
        )
        _, public_projection_ref = project_development_public_evaluation(
            store,
            sample_dir=root / "dataset" / "sample-authority",
            episode_id="sample-authority",
            method_condition="M0",
            analysis_population="excluded",
            terminal_public_outcome_ref=terminal_public_ref,
        )
        episode_outcome, _ = reconcile_development_episode_outcome(
            store,
            public_evaluation_ref=public_projection_ref,
            trajectory_ref=agent.last_canonical_trajectory.artifact_ref,
        )
        assert (
            episode_outcome["development_vpp_l3_status"]
            == expected_development_vpp_status
        )
        assert episode_outcome["development_vpp_l3"] is expected_development_vpp
        assert episode_outcome["development_vpp_l3_reasons"] == expected_vpp_reasons
        assert episode_outcome["vpp_l3_status"] == "not_evaluated"
        assert episode_outcome["vpp_l3"] is None

        mismatched_hidden = json.loads(json.dumps(hidden_conformance))
        mismatched_hidden["public_profile_sha256"] = "0" * 64
        hidden_without_id = {
            key: value
            for key, value in mismatched_hidden.items()
            if key != "outcome_id"
        }
        hidden_encoded = (
            json.dumps(hidden_without_id, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        mismatched_hidden["outcome_id"] = "hidden-conformance-outcome-" + (
            hashlib.sha256(hidden_encoded).hexdigest()
        )
        mismatched_hidden_ref = store.put_validated_json(
            "hidden-conformance-outcomes/sample-authority-mismatch",
            mismatched_hidden,
            contract_key="development_hidden_conformance_outcome",
        )
        with pytest.raises(
            CostAccountingError, match="hidden conformance requirement profile mismatch"
        ):
            reconcile_attempt_trajectory(
                store,
                [summary.artifact_ref for summary in agent.last_cost_summaries],
                terminal_candidate_ref=terminal_ref,
                development_hidden_outcome_ref=result[
                    "development_hidden_outcome_ref"
                ],
                development_hidden_conformance_outcome_ref=mismatched_hidden_ref,
                development_terminal_selection_ref=ArtifactRef(
                    **result["development_terminal_selection_ref"]
                ),
                development_selected_public_outcome_ref=ArtifactRef(
                    **result["development_selected_public_outcome_ref"]
                ),
                development_terminal_public_outcome_ref=terminal_public_ref,
            )

        mismatched_payload = json.loads(json.dumps(terminal_public))
        mismatched_payload["public_l2_harness"] = {
            "status": "available",
            "harness_id": "different-harness-v1",
            "manifest_sha256": "1" * 64,
            "bundle_sha256": "2" * 64,
            "reason": None,
        }
        without_id = {
            key: value
            for key, value in mismatched_payload.items()
            if key != "outcome_id"
        }
        encoded = (
            json.dumps(without_id, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        mismatched_payload["outcome_id"] = "public-outcome-" + hashlib.sha256(
            encoded
        ).hexdigest()
        mismatched_terminal_ref = store.put_validated_json(
            "public-authority-outcomes/sample-authority/M0-mismatch",
            mismatched_payload,
            contract_key="development_terminal_public_outcome",
        )
        with pytest.raises(
            CostAccountingError, match="harness commitments disagree"
        ):
            reconcile_attempt_trajectory(
                store,
                [
                    summary.artifact_ref for summary in agent.last_cost_summaries
                ],
                terminal_candidate_ref=terminal_ref,
                development_hidden_outcome_ref=result[
                    "development_hidden_outcome_ref"
                ],
                development_terminal_selection_ref=ArtifactRef(
                    **result["development_terminal_selection_ref"]
                ),
                development_selected_public_outcome_ref=ArtifactRef(
                    **result["development_selected_public_outcome_ref"]
                ),
                development_terminal_public_outcome_ref=(
                    mismatched_terminal_ref
                ),
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_direct_generator_reserves_parser_retry_before_second_model_call() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        ledger = AttemptCostLedger(
            store,
            episode_id="sample-parser-retry",
            attempt_id="attempt-000",
            method_condition="M0",
            failure_origin="natural_llm",
        )
        request = ProjectRequest(task_type="counter", width=8, project_name="counter_8bit")
        platform = PlatformProfile(name="generic", vendor="generic", toolchain="open_source")
        valid_files = _canonical_project().files
        client = _SequenceChatClient(
            ["not-json", json.dumps({"files": valid_files})]
        )
        budget = ModelCallBudget(
            2,
            attempt_cost_ledger=ledger,
            max_parser_schema_retries=1,
        )

        generated = DirectProjectGenerator(
            budget.client(client, "direct_generation"),
            max_attempts=2,
        ).generate(request, platform)

        assert generated.project_name == "counter_8bit"
        ledger.close(zero_axes=set(COST_AXES) - set(ledger.observed_axes))
        summary = reconcile_cost_events(store, ledger.event_refs).payload
        assert summary["axes"]["logical_model_calls"]["value"] == 2
        assert summary["axes"]["planner_parser_schema_retries"]["value"] == 1
        assert budget.summary()["remaining_parser_schema_retries"] == 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("method_condition", ["M0", "M1", "M2", "M3"])
def test_agent_seals_direct_terminal_candidate_into_trajectory_v2(
    method_condition: str,
) -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        router = AttemptCostLedgerRouter()

        class _CanonicalGenerator:
            def generate(self, request, platform):
                return _canonical_project()

        def factory(attempt_id: int) -> AttemptCostLedger:
            return AttemptCostLedger(
                store,
                episode_id=f"sample-{method_condition.lower()}",
                attempt_id=f"attempt-{attempt_id:03d}",
                method_condition=method_condition,
                failure_origin="natural_llm",
                candidate_id=f"sample-{method_condition.lower()}-attempt-{attempt_id:03d}",
                input_artifact_hashes=("a" * 64,),
            )

        agent = DataGenerationAgent(
            root / "dataset",
            command_runner=_PassingRunner(),
            project_generator=_CanonicalGenerator(),
            attempt_cost_ledger_factory=factory,
            attempt_cost_router=router,
        )
        result = agent.run_one(
            f"sample-{method_condition.lower()}",
            "Design a counter.",
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
        )

        trajectory = agent.last_canonical_trajectory
        assert trajectory is not None
        assert trajectory.payload["lineage_complete"] is True
        terminal_ref = trajectory.payload["terminal_candidate_ref"]
        assert terminal_ref is not None
        assert result["canonical_trajectory_ref"] == trajectory.artifact_ref.to_dict()
        terminal = json.loads(store.read_verified(terminal_ref["key"]))
        assert terminal["candidate_id"] == (
            f"sample-{method_condition.lower()}-attempt-000"
        )
        envelope = json.loads(
            store.read_verified(
                f"project-envelopes/sample-{method_condition.lower()}-attempt-000"
            )
        )
        assert {record["owner"] for record in envelope["files"]} == {"model"}
        assert all(record["editable"] is False for record in envelope["files"])
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("method_condition", ["M4", "M5"])
def test_agent_seals_skeleton_terminal_with_composite_ownership(
    method_condition: str,
) -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        router = AttemptCostLedgerRouter()

        class _CompositeGenerator:
            def generate(self, request, platform):
                return _canonical_project(composite=True)

        def factory(attempt_id: int) -> AttemptCostLedger:
            return AttemptCostLedger(
                store,
                episode_id=f"sample-{method_condition.lower()}",
                attempt_id=f"attempt-{attempt_id:03d}",
                method_condition=method_condition,
                failure_origin="natural_llm",
                candidate_id=f"sample-{method_condition.lower()}-attempt-{attempt_id:03d}",
                input_artifact_hashes=("a" * 64,),
            )

        agent = DataGenerationAgent(
            root / "dataset",
            command_runner=_PassingRunner(),
            project_generator=_CompositeGenerator(),
            attempt_cost_ledger_factory=factory,
            attempt_cost_router=router,
        )
        agent.run_one(
            f"sample-{method_condition.lower()}",
            "Design a counter.",
            ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
            PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
        )

        trajectory = agent.last_canonical_trajectory
        assert trajectory is not None
        assert trajectory.payload["lineage_complete"] is True
        envelope = json.loads(
            store.read_verified(
                f"project-envelopes/sample-{method_condition.lower()}-attempt-000"
            )
        )
        rtl_record = next(
            record for record in envelope["files"] if record["path"] == "rtl/top.v"
        )
        manifest_record = next(
            record for record in envelope["files"] if record["path"] == "manifest.json"
        )
        assert rtl_record["owner"] == "composite"
        assert {region["owner"] for region in rtl_record["regions"]} == {
            "model",
            "trusted_builder",
        }
        assert manifest_record["owner"] == "trusted_builder"
        assert manifest_record["editable"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_agent_emergency_close_preserves_unobserved_axes_as_unavailable() -> None:
    root = _test_root()
    try:
        store = ArtifactStore(root / "store")
        router = AttemptCostLedgerRouter()

        def factory(attempt_id: int) -> AttemptCostLedger:
            return AttemptCostLedger(
                store,
                episode_id="sample-aborted",
                attempt_id=f"attempt-{attempt_id:03d}",
                method_condition="M0",
                failure_origin=None,
            )

        class _AbortingAgent(DataGenerationAgent):
            def _run_one_impl(self, *args, **kwargs):
                self._start_cost_attempt(0)
                raise RuntimeError("unexpected abort")

        agent = _AbortingAgent(
            root / "dataset",
            attempt_cost_ledger_factory=factory,
            attempt_cost_router=router,
        )
        with pytest.raises(RuntimeError, match="unexpected abort"):
            agent.run_one(
                "sample-aborted",
                "abort",
                ProjectRequest(task_type="counter", width=8, project_name="counter_8bit"),
                PlatformProfile(name="generic", vendor="generic", toolchain="open_source"),
            )

        assert router.current() is None
        summary = agent.last_cost_summaries[0].payload
        assert summary["axes"]["wall_time"]["status"] == "measured"
        assert summary["axes"]["logical_model_calls"] == {
            "status": "unavailable",
            "value": None,
            "reason": "attempt_aborted_before_accounting_close",
        }
        assert agent.last_canonical_trajectory is not None
        assert agent.last_canonical_trajectory.payload["missing_lineage_reasons"] == [
            "attempt-000:candidate_id_missing",
            "attempt-000:candidate_output_hash_missing",
            "terminal_candidate_ref_missing",
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)
