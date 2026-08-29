from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from sr2fpga_agent.artifact_store import ArtifactIntegrityError, ArtifactRef, ArtifactStore
from sr2fpga_agent.agent import DataGenerationAgent as RealDataGenerationAgent
from sr2fpga_agent.cost_accounting import (
    COST_AXES,
    DURATION_COST_AXES,
    AttemptCostLedger,
    reconcile_attempt_trajectory,
    reconcile_cost_events,
)
from sr2fpga_agent.block_preparation import SharedCheckpointResumeError
from sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
from sr2fpga_agent.episode_executor import EpisodeExecutor, PreCandidateState
from sr2fpga_agent.episode_outcome import (
    EpisodeOutcomeError,
    project_development_public_evaluation,
    reconcile_development_episode_outcome,
)
from sr2fpga_agent.evaluator_dispatch import DevelopmentHiddenEvaluationAuthority
from sr2fpga_agent.frozen_context import (
    build_development_episode_pack,
    context_from_validated_episode_pack,
    freeze_ready_requirement_context,
    frozen_project_name,
)
from sr2fpga_agent.full_pack_smoke import (
    FullPackMethodRecord,
    FullPackReconciliationError,
    FullPackRunnerArtifactRecord,
    FullPackScenarioRecord,
    assemble_excluded_run_full_pack,
    assemble_excluded_run_full_pack_with_cost_views,
    assemble_excluded_run_full_pack_with_outcomes,
    reconcile_excluded_full_pack,
    reconcile_full_pack_runner_artifacts,
)
from sr2fpga_agent.method_adapters import (
    GenerationServices,
    MethodAdapterRegistry,
    MethodArtifactGateway,
    PairedArtifactCoordinator,
    PairingKey,
    RepairController,
    SharedArtifactRefs,
)
from sr2fpga_agent.method_contract import method_policy_sha256
from sr2fpga_agent.measurement_freeze import freeze_fingerprint
from sr2fpga_agent.models import (
    GeneratedProject,
    PlatformProfile,
    ProjectRequest,
    ToolResult,
)
from sr2fpga_agent.parsers import parse_system_his_v12
from sr2fpga_agent.paired_measurement import build_episode_measurement
from sr2fpga_agent.paired_block import (
    build_balanced_method_orders,
    load_development_paired_block,
    write_development_paired_block,
)
from sr2fpga_agent.paired_cost_views import (
    read_development_paired_block_cost_reconciliation,
)
from sr2fpga_agent.project_contract import build_project_envelope
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.public_evaluator import (
    DevelopmentTerminalPublicEvaluationAuthority,
    PublicEvaluatorResult,
)
from sr2fpga_agent.public_l2_harness import load_development_public_l2_harness
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary
from sr2fpga_agent.runner import (
    RunnerConfig,
    SourceConnection,
    TaskConfig,
    planned_samples,
    run_batch,
    runner_preflight,
)
from sr2fpga_agent.system_his_fidelity import build_frozen_requirement_trace


_TEST_ROOT = Path(__file__).resolve().parent / ".runner_tmp"


def _new_test_root() -> Path:
    root = _TEST_ROOT / f"full-pack-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def _platform() -> PlatformProfile:
    return PlatformProfile("generic_verilog", "generic", "open_source")


def _project(tag: str) -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "counter8",
        "top": {
            "module": "top",
            "source": "rtl/top.v",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {"path": "rtl/top.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [],
        "build": {"toolchain_id": "open_source", "language_standard": "verilog-2005"},
    }
    return GeneratedProject(
        "counter8",
        {
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "rtl/top.v": (
                f"// {tag}\n"
                "module top(input clk, output [7:0] count); "
                "assign count = 8'd1; endmodule\n"
            ),
        },
    )


class _StaticClient:
    def __init__(self, response: str, *, failure: Exception | None = None) -> None:
        self.response = response
        self.failure = failure
        self.calls: list[list[dict[str, str]]] = []

    def stream_chat(self, messages):
        self.calls.append(messages)
        if self.failure is not None:
            raise self.failure
        return self.response

    def chat(self, messages):
        self.calls.append(messages)
        if self.failure is not None:
            raise self.failure
        return self.response


class _TwoStageGeneratorStub:
    def __init__(self, req2his_client, project_client) -> None:
        self.system_his_generator = SimpleNamespace(client=req2his_client)
        self.his_project_generator = SimpleNamespace(client=project_client)


class _PassingCommandRunner:
    def run(self, command, cwd, stage, timeout_seconds=30):
        stdout = "TEST_PASS\n" if stage == "candidate_sim_run" else ""
        if stage == "synth":
            stdout = "Number of cells: 1\n  SB_LUT4 1\n"
        return ToolResult(
            stage=stage,
            command=list(command),
            status="passed",
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_seconds=0.001,
        )


def _runner_model_responses(
    metadata: dict,
    *,
    task_type: str,
    width: int,
) -> tuple[str, str, str]:
    context = context_from_validated_episode_pack(metadata["episode_pack"])
    platform = _platform()
    request = ProjectRequest(
        task_type,
        width,
        frozen_project_name(context),
        context.public_text,
    )
    project = ProjectGenerator().generate(request, platform)
    system_his = parse_system_his_v12(project.files["system_his.json"])
    system_his["intent"]["requirement_trace"] = build_frozen_requirement_trace(
        context,
        system_his,
    )
    top = system_his["top"]
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": project.project_name,
        "top": {
            "module": system_his["artifacts"]["top_module"],
            "source": system_his["artifacts"]["rtl_sources"][0],
            "interface": {
                "ports": [
                    {
                        "name": port["name"],
                        "direction": port["dir"],
                        "width": port["width"],
                    }
                    for port in top["ports"]
                ]
            },
        },
        "sources": [
            {"path": path, "role": "rtl_source", "language": "verilog"}
            for path in system_his["artifacts"]["rtl_sources"]
        ],
        "artifacts": [
            {
                "path": "constraints/timing.sdc",
                "role": "constraint",
                "applicability": "advisory",
            },
            {
                "path": "sim/tb_top.v",
                "role": "candidate_testbench",
                "applicability": "advisory",
            },
            {
                "path": "reports/predicted_qor.json",
                "role": "predicted_qor",
                "applicability": "advisory",
            },
        ],
        "build": {
            "toolchain_id": "open_source",
            "language_standard": "verilog-2005",
        },
    }
    free_files = {
        path: content
        for path, content in project.files.items()
        if path not in {"manifest.json", "system_his.json"}
    }
    free_files["manifest.json"] = json.dumps(manifest)
    free_project = json.dumps(
        {"project_name": project.project_name, "files": free_files}
    )
    skeleton = build_contract_skeleton_project(request, platform, system_his)
    behavior_response = json.dumps(
        {
            "behavior_files": {
                path: "// deterministic fake-provider behavior body"
                for path, content in skeleton.files.items()
                if "BEHAVIOR_HOLE" in content
            }
        }
    )
    return json.dumps(system_his), free_project, behavior_response


class _DirectFacade:
    def emit_project(self, context):
        return _project("shared-direct")


class _UntypedFacade:
    def emit_plan(self, context):
        return {"steps": ["counter state", "registered output"]}

    def emit_project(self, context, plan):
        assert plan["steps"]
        return _project("m2-untyped")


class _HisFacade:
    def emit_his(self, context):
        return {"schema_version": "system-his-v1.2", "intent": {"design_goal": "counter"}}

    def emit_free_project(self, context, system_his):
        return _project("m3-free")

    def emit_skeleton_project(self, context, system_his):
        return _project("shared-skeleton")


class _ValidationFacade:
    def __init__(self, reports=None) -> None:
        self.reports = list(reports or [_h_report(True)])
        self.calls = 0

    def validate_his(self, context, system_his):
        report = self.reports[min(self.calls, len(self.reports) - 1)]
        self.calls += 1
        return report


class _RepairFacade:
    def __init__(self) -> None:
        self.his_calls = 0
        self.project_calls = 0

    def correct_his(self, context, system_his, diagnosis):
        self.his_calls += 1
        return {**system_his, "corrected": True}

    def repair_project(self, context, project, diagnosis):
        self.project_calls += 1
        return _project("project-repaired")


def _h_report(passed: bool, failed_stage: str | None = None) -> dict:
    report = {"passed": passed}
    for stage in ("h0", "h1", "h2", "h3"):
        report[stage] = {
            "status": "fail" if stage == failed_stage else ("pass" if passed else "not_run"),
            "diagnostics": [f"{stage} failed"] if stage == failed_stage else [],
        }
    return report


def _pairing(context, paired_block_id: str) -> PairingKey:
    return PairingKey(
        paired_block_id=paired_block_id,
        requirement_revision_id=context.revision_id,
        semantic_instance_id="semantic-counter-001",
        decoding_seed=17,
        model_provenance_sha256="a" * 64,
    )


def _seal_candidate(store, project, context, *, method: str, episode_id: str, candidate_id: str):
    policies = {
        path: {"owner": "model", "origin": "model_generated", "editable": False}
        for path in project.files
    }
    envelope = build_project_envelope(
        project,
        episode_id=episode_id,
        method_condition_id=method,
        method_policy_sha256=method_policy_sha256(method),
        snapshot_id="snapshot-000",
        file_policies=policies,
    )
    envelope_ref = store.put_validated_json(
        f"envelopes/{candidate_id}", envelope, contract_key="project_envelope"
    )
    creation = store.append_event(episode_id, "candidate_created", {})
    return store.seal_candidate(
        candidate_id,
        project=project,
        project_envelope_ref=envelope_ref,
        requirement_projection_sha256=context.public_projection_sha256,
        creation_event_ref=creation,
    )


def test_excluded_full_pack_reconciles_m0_m5_and_required_scenarios() -> None:
    tmp_path = _new_test_root()
    platform = _platform()
    ready = evaluate_requirement_boundary(
        ProjectRequest(
            "counter",
            8,
            "counter8",
            "Build an 8-bit synchronous counter with active-low reset.",
        ),
        platform,
    )
    context = freeze_ready_requirement_context(ready, platform)
    packs = {
        method: build_development_episode_pack(
            context,
            episode_id=f"full-pack-{method.lower()}",
            analysis_population="excluded",
            method_condition=method,
            evaluator_metadata={"smoke": "cd9-excluded"},
        )
        for method in ("M0", "M1", "M2", "M3", "M4", "M5")
    }
    method_store = ArtifactStore(tmp_path / "method-store")
    gateway = MethodArtifactGateway(method_store)
    coordinator = PairedArtifactCoordinator(method_store)
    direct = _DirectFacade()
    untyped = _UntypedFacade()
    his = _HisFacade()
    validation = _ValidationFacade()
    repair = _RepairFacade()
    shared_direct = coordinator.materialize_initial_project(
        _pairing(context, "pair-direct"), lambda: direct.emit_project(context)
    )
    shared_his = coordinator.materialize_system_his(
        _pairing(context, "pair-his"), lambda: his.emit_his(context)
    )
    shared_skeleton = coordinator.materialize_initial_project(
        _pairing(context, "pair-skeleton"),
        lambda: his.emit_skeleton_project(context, {"shared": True}),
    )

    outcomes = {}
    for method in ("M0", "M1", "M2", "M3", "M4", "M5"):
        services = GenerationServices(
            artifacts=gateway,
            episode_id=f"full-pack-{method.lower()}",
            direct=direct,
            untyped=untyped,
            system_his=his,
            his_validation=validation,
            repair=repair,
        )
        shared = SharedArtifactRefs()
        if method in {"M0", "M1"}:
            shared = SharedArtifactRefs(initial_project=shared_direct)
        elif method == "M3":
            shared = SharedArtifactRefs(system_his=shared_his)
        elif method in {"M4", "M5"}:
            shared = SharedArtifactRefs(
                initial_project=shared_skeleton,
                system_his=shared_his,
            )
        outcomes[method] = EpisodeExecutor().emit_candidate(
            MethodAdapterRegistry().create(method), context, services, shared
        )

    method_records = []
    for method, outcome in outcomes.items():
        assert outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
        assert outcome.candidate is not None
        planning_kind = outcome.planning_artifact.kind.value if outcome.planning_artifact else None
        method_records.append(
            FullPackMethodRecord(
                method_condition=method,
                analysis_population="excluded",
                pack_sha256=packs[method].pack_sha256,
                public_projection_sha256=context.public_projection_sha256,
                candidate_artifact_key=outcome.candidate.artifact_ref.key,
                candidate_artifact_sha256=outcome.candidate.artifact_ref.sha256,
                project_package_sha256=outcome.candidate.project_package_sha256,
                skeleton_artifact_sha256=(
                    shared_skeleton.project_package_sha256
                    if method in {"M4", "M5"}
                    else None
                ),
                planning_kind=planning_kind,
                planning_artifact_sha256=(
                    outcome.planning_artifact.artifact_ref.sha256
                    if outcome.planning_artifact
                    else None
                ),
                h_status="pass" if method in {"M3", "M4", "M5"} else "not_applicable",
                skeleton_mode=(
                    "none_free_full_project"
                    if method == "M3"
                    else "behavior_files" if method in {"M4", "M5"} else "none"
                ),
            )
        )

    h_store = ArtifactStore(tmp_path / "h-repair-store")
    h_validation = _ValidationFacade([_h_report(False, "h0"), _h_report(True)])
    h_repair = _RepairFacade()
    h_outcome = EpisodeExecutor(max_his_corrections=1).emit_candidate(
        MethodAdapterRegistry().create("M5"),
        context,
        GenerationServices(
            artifacts=MethodArtifactGateway(h_store),
            episode_id="scenario-h-repair",
            system_his=_HisFacade(),
            his_validation=h_validation,
            repair=h_repair,
        ),
    )
    assert h_outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert h_validation.calls == 2
    assert h_repair.his_calls == 1

    m1_services = GenerationServices(
        artifacts=gateway,
        episode_id="scenario-project-repair",
        repair=repair,
    )
    repaired = RepairController().repair_project(
        MethodAdapterRegistry().create("M1"),
        context,
        outcomes["M1"].candidate,
        {"stage": "lint", "failure_type": "undefined_signal"},
        m1_services,
    )
    original_project = gateway.read_project(outcomes["M1"].candidate)
    repaired_project = gateway.read_project(repaired)
    public_before = "fail" if "project-repaired" not in original_project.files["rtl/top.v"] else "pass"
    public_after = "pass" if "project-repaired" in repaired_project.files["rtl/top.v"] else "fail"
    assert (public_before, public_after) == ("fail", "pass")

    non_ready = evaluate_requirement_boundary(
        ProjectRequest(
            "counter",
            8,
            "ambiguous-counter",
            "Build an 8-bit counter with a host interface.",
        ),
        platform,
    )
    assert non_ready.disposition == "needs_clarification"

    candidate_store = ArtifactStore(tmp_path / "candidate-store")
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    m0_project = gateway.read_project(outcomes["M0"].candidate)
    m1_project = gateway.read_project(outcomes["M1"].candidate)
    m0_seal = _seal_candidate(
        candidate_store,
        m0_project,
        context,
        method="M0",
        episode_id="hidden-fail-episode",
        candidate_id="hidden-fail-candidate",
    )
    m1_seal = _seal_candidate(
        candidate_store,
        m1_project,
        context,
        method="M1",
        episode_id="hidden-infra-episode",
        candidate_id="hidden-infra-candidate",
    )
    fail_commitment = evaluator_store.put_blob("private/fail-commitment", b"private-fail")
    infra_commitment = evaluator_store.put_blob("private/infra-commitment", b"private-infra")
    hidden_calls = []
    fail_authority = DevelopmentHiddenEvaluationAuthority(
        candidate_store,
        evaluator_store,
        lambda value: hidden_calls.append("fail") or {"outcome": "fail", "case": "private"},
    )
    fail_ref = fail_authority.evaluate_once(
        terminal_candidate_ref=m0_seal,
        private_commitment_ref=fail_commitment,
        public_contract_sha256="b" * 64,
        public_profile_sha256="c" * 64,
        tool_environment_policy_sha256="d" * 64,
        decoding_seed=17,
    )

    def infrastructure_failure(value):
        hidden_calls.append("infrastructure")
        raise RuntimeError("private evaluator infrastructure detail")

    infra_authority = DevelopmentHiddenEvaluationAuthority(
        candidate_store,
        evaluator_store,
        infrastructure_failure,
    )
    infra_ref = infra_authority.evaluate_once(
        terminal_candidate_ref=m1_seal,
        private_commitment_ref=infra_commitment,
        public_contract_sha256="b" * 64,
        public_profile_sha256="c" * 64,
        tool_environment_policy_sha256="d" * 64,
        decoding_seed=17,
    )
    assert hidden_calls == ["fail", "infrastructure"]
    assert set(fail_ref.to_dict()) == {"outcome_id", "contract_id"}
    assert set(infra_ref.to_dict()) == {"outcome_id", "contract_id"}

    scenarios = [
        FullPackScenarioRecord(
            "scenario-success",
            "success",
            "excluded",
            context.public_projection_sha256,
            None,
            "passed",
            {
                "method_count": 6,
                "scope": "pre_candidate_emission_conformance",
            },
        ),
        FullPackScenarioRecord(
            "scenario-h-repair",
            "h_repair",
            "excluded",
            context.public_projection_sha256,
            "M5",
            "passed",
            {"his_corrections_used": 1, "rerun_complete_h_validation": True},
        ),
        FullPackScenarioRecord(
            "scenario-project-repair",
            "project_repair",
            "excluded",
            context.public_projection_sha256,
            "M1",
            "passed",
            {
                "repair_calls_attempted": 1,
                "repair_transitions": 1,
                "rerun_performed": True,
                "automatic_pass_credit": True,
            },
        ),
        FullPackScenarioRecord(
            "scenario-non-ready",
            "non_ready",
            "excluded",
            context.public_projection_sha256,
            None,
            non_ready.disposition,
            {"generation_calls": 0},
        ),
        FullPackScenarioRecord(
            "scenario-hidden-fail",
            "hidden_fail",
            "excluded",
            context.public_projection_sha256,
            "M0",
            "fail",
            {
                "opaque_outcome_only": True,
                "opaque_outcome_id": fail_ref.outcome_id,
                "repair_after_hidden": False,
            },
        ),
        FullPackScenarioRecord(
            "scenario-infrastructure-not-run",
            "infrastructure_not_run",
            "excluded",
            context.public_projection_sha256,
            "M1",
            "not_run",
            {
                "reason": "evaluator_exception",
                "opaque_outcome_id": infra_ref.outcome_id,
                "replacement_episode": False,
            },
        ),
    ]
    report_store = ArtifactStore(tmp_path / "report-store")
    with mock.patch.object(
        report_store,
        "put_validated_json",
        wraps=report_store.put_validated_json,
    ) as validated_write:
        report, report_ref = reconcile_excluded_full_pack(
            report_store,
            smoke_id="cd9-unit-full-pack",
            methods=method_records,
            scenarios=scenarios,
        )

    assert validated_write.call_count == 1
    assert validated_write.call_args.kwargs["contract_key"] == "full_pack_smoke_report"

    assert report["contract_version"] == "full-pack-smoke-report-v1"
    assert report["registered_evidence_contract"] is True
    assert report["official_outcome"] is False
    assert report["g3_accepted"] is False
    assert report["g4b_authorized"] is False
    assert report["rq1_evidence"] is False
    assert report["rq2_evidence"] is False
    assert report["reconciliation"]["all_required_scenarios_present"] is True
    assert report["reconciliation"]["full_axis_costs_reconciled"] is False
    assert report["reconciliation"]["blocking_gaps"] == [
        "full_axis_event_derived_cost_reconciliation",
        "runner_owned_public_terminal_hidden_pipeline",
    ]
    persisted = json.loads(report_store.read_verified(report_ref))
    assert persisted == report
    serialized = json.dumps(report, sort_keys=True)
    assert "private evaluator infrastructure detail" not in serialized
    assert '"case": "private"' not in serialized


def test_full_pack_reconciliation_rejects_missing_scenario() -> None:
    tmp_path = _new_test_root()
    record = FullPackMethodRecord(
        method_condition="M0",
        analysis_population="excluded",
        pack_sha256="a" * 64,
        public_projection_sha256="b" * 64,
        candidate_artifact_key="candidate/m0",
        candidate_artifact_sha256="c" * 64,
        project_package_sha256="d" * 64,
    )
    records = [
        FullPackMethodRecord(
            **{
                **record.__dict__,
                "method_condition": method,
                "pack_sha256": f"{index + 1:x}" * 64,
                "candidate_artifact_key": f"candidate/{method.lower()}",
                "planning_kind": "untyped_plan" if method == "M2" else (
                    "system_his" if method in {"M3", "M4", "M5"} else None
                ),
                "planning_artifact_sha256": "e" * 64 if method in {"M3", "M4", "M5"} else None,
                "skeleton_artifact_sha256": (
                    "f" * 64 if method in {"M4", "M5"} else None
                ),
                "skeleton_mode": "none_free_full_project" if method == "M3" else (
                    "behavior_files" if method in {"M4", "M5"} else "none"
                ),
            }
        )
        for index, method in enumerate(("M0", "M1", "M2", "M3", "M4", "M5"))
    ]
    with pytest.raises(FullPackReconciliationError, match="missing scenarios"):
        reconcile_excluded_full_pack(
            ArtifactStore(tmp_path / "store"),
            smoke_id="missing-scenario",
            methods=records,
            scenarios=[],
        )


def _minimal_smoke_inputs(projection: str):
    methods = []
    for index, method in enumerate(("M0", "M1", "M2", "M3", "M4", "M5")):
        methods.append(
            FullPackMethodRecord(
                method_condition=method,
                analysis_population="excluded",
                pack_sha256=f"{index + 1:x}" * 64,
                public_projection_sha256=projection,
                candidate_artifact_key=f"candidate/{method.lower()}",
                candidate_artifact_sha256=f"{index + 7:x}" * 64,
                project_package_sha256=(
                    "a" * 64
                    if method in {"M0", "M1"}
                    else f"{index + 1:x}" * 64
                ),
                skeleton_artifact_sha256=(
                    "f" * 64 if method in {"M4", "M5"} else None
                ),
                planning_kind=(
                    "untyped_plan"
                    if method == "M2"
                    else "system_his" if method in {"M3", "M4", "M5"} else None
                ),
                planning_artifact_sha256=(
                    "c" * 64 if method in {"M3", "M4"} else "d" * 64 if method == "M5" else None
                ),
                h_status="pass" if method in {"M3", "M4", "M5"} else "not_applicable",
                skeleton_mode=(
                    "none_free_full_project"
                    if method == "M3"
                    else "behavior_files" if method in {"M4", "M5"} else "none"
                ),
            )
        )
    scenarios = [
        FullPackScenarioRecord(
            "success", "success", "excluded", projection, None, "passed",
            {"method_count": 6, "scope": "pre_candidate_emission_conformance"},
        ),
        FullPackScenarioRecord(
            "h-repair", "h_repair", "excluded", projection, "M5", "passed",
            {"his_corrections_used": 1, "rerun_complete_h_validation": True},
        ),
        FullPackScenarioRecord(
            "project-repair", "project_repair", "excluded", projection, "M1", "passed",
            {
                "repair_calls_attempted": 1,
                "repair_transitions": 1,
                "rerun_performed": True,
                "automatic_pass_credit": True,
            },
        ),
        FullPackScenarioRecord(
            "non-ready", "non_ready", "excluded", projection, None,
            "needs_clarification", {"generation_calls": 0},
        ),
        FullPackScenarioRecord(
            "hidden-fail", "hidden_fail", "excluded", projection, "M0", "fail",
            {
                "opaque_outcome_only": True,
                "opaque_outcome_id": "hidden-outcome-" + "e" * 64,
                "repair_after_hidden": False,
            },
        ),
        FullPackScenarioRecord(
            "infra-not-run", "infrastructure_not_run", "excluded", projection,
            "M1", "not_run",
            {
                "reason": "evaluator_exception",
                "opaque_outcome_id": "hidden-outcome-" + "f" * 64,
                "replacement_episode": False,
            },
        ),
    ]
    return methods, scenarios


def _runner_artifacts(store: ArtifactStore, projection: str):
    records = []
    for index, method in enumerate(("M0", "M1", "M2", "M3", "M4", "M5")):
        episode_id = f"runner-{method.lower()}"
        candidate_id = f"{episode_id}-attempt-000"
        ledger = AttemptCostLedger(
            store,
            episode_id=episode_id,
            attempt_id="attempt-000",
            method_condition=method,
            failure_origin="synthetic_injected",
            candidate_id=candidate_id,
            input_artifact_hashes=(projection,),
        )
        cost_delta = {axis: 0 for axis in COST_AXES}
        cost_delta["public_tool_calls"] = 1
        ledger.record_cost(
            stage="excluded-runner-fixture",
            visibility_class="public",
            cost_delta=cost_delta,
            output_artifact_hashes=(f"{index + 1:x}" * 64,),
        )
        ledger.close()
        summary = reconcile_cost_events(store, ledger.event_refs)
        project = _project(method.lower())
        envelope = build_project_envelope(
            project,
            episode_id=episode_id,
            method_condition_id=method,
            method_policy_sha256=method_policy_sha256(method),
            snapshot_id=f"snapshot-{method.lower()}",
            file_policies={
                path: {"owner": "model", "origin": "model_generated", "editable": False}
                for path in project.files
            },
        )
        envelope_ref = store.put_validated_json(
            f"runner-envelopes/{method.lower()}",
            envelope,
            contract_key="project_envelope",
        )
        selection_ref = store.append_event(
            episode_id,
            "terminal_candidate_selected",
            {"candidate_id": candidate_id, "method_condition": method},
        )
        terminal_ref = store.seal_candidate(
            candidate_id,
            project=project,
            project_envelope_ref=envelope_ref,
            requirement_projection_sha256=projection,
            creation_event_ref=selection_ref,
        )
        hidden_ref = {
            "outcome_id": "hidden-outcome-" + f"{index + 1:x}" * 64,
            "contract_id": "development-hidden-outcome-v1",
        }
        trajectory = reconcile_attempt_trajectory(
            store,
            [summary.artifact_ref],
            terminal_candidate_ref=terminal_ref,
            development_hidden_outcome_ref=hidden_ref,
        )
        records.append(FullPackRunnerArtifactRecord(method, trajectory.artifact_ref))
    return records


def test_full_pack_runner_reconciliation_consumes_m0_m5_trajectory_cost_terminal_hidden() -> None:
    root = _new_test_root()
    store = ArtifactStore(root / "store")
    projection = "9" * 64
    methods, scenarios = _minimal_smoke_inputs(projection)
    _, smoke_ref = reconcile_excluded_full_pack(
        store,
        smoke_id="runner-full-pack",
        methods=methods,
        scenarios=scenarios,
    )
    runner_records = _runner_artifacts(store, projection)

    report, report_ref = reconcile_full_pack_runner_artifacts(
        store,
        smoke_id="runner-full-pack",
        source_smoke_report_ref=smoke_ref,
        runner_artifacts=runner_records,
    )

    assert report["g3_accepted"] is False
    assert report["official_outcome"] is False
    assert report["reconciliation"]["all_cost_axes_classified"] is True
    assert report["reconciliation"]["matching_terminal_seals"] is True
    assert report["reconciliation"]["opaque_hidden_ref_count"] == 6
    assert json.loads(store.read_verified(report_ref)) == report


def test_episode_outcome_rejects_repair_count_not_in_cost_events() -> None:
    root = _new_test_root()
    store = ArtifactStore(root / "store")
    runner_records = _runner_artifacts(store, "9" * 64)
    trajectory_ref = next(
        record.trajectory_ref
        for record in runner_records
        if record.method_condition == "M1"
    )
    attempts = [
        {
            "attempt_id": 0,
            "pass_level": "L1",
            "failure_type": "simulation_mismatch",
            "repair_scope": "project",
            "repair_attempted": True,
            "repair_call_status": "succeeded",
        },
        {"attempt_id": 1, "pass_level": "L3", "failure_type": "none"},
    ]
    patches = [
        {
            "diagnosis_id": "d001",
            "files_touched": ["rtl/top.v"],
            "allowed_edit_regions_respected": True,
            "touched_trusted_artifacts": False,
            "status": "valid",
            "regressions": [],
        }
    ]
    measurement = build_episode_measurement(attempts=attempts, patches=patches)
    eval_dir = root / "legacy" / "eval"
    eval_dir.mkdir(parents=True)
    (eval_dir / "labels.json").write_text(
        json.dumps(
            {
                "pass_level": "L3",
                "l2_sim_status": "pass",
                "l2_sim_skip_reason": None,
                "checks": {
                    "l0_complete": True,
                    "l1_lint_pass": True,
                    "l2_sim_pass": True,
                    "l3_synth_pass": True,
                },
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "trajectory.json").write_text(
        json.dumps(
            {
                "sample_id": "runner-m1",
                "attempt_measurements": attempts,
                "patches": patches,
                "measurement": measurement,
            }
        ),
        encoding="utf-8",
    )
    _, public_ref = project_development_public_evaluation(
        store,
        sample_dir=root / "legacy",
        episode_id="runner-m1",
        method_condition="M1",
        analysis_population="excluded",
    )

    with pytest.raises(
        EpisodeOutcomeError, match="repair calls do not reconcile with cost events"
    ):
        reconcile_development_episode_outcome(
            store,
            public_evaluation_ref=public_ref,
            trajectory_ref=trajectory_ref,
        )


def test_episode_outcome_consumes_terminal_public_authority_projection() -> None:
    root = _new_test_root()
    store = ArtifactStore(root / "store")
    runner_records = _runner_artifacts(store, "9" * 64)
    trajectory_ref = next(
        record.trajectory_ref
        for record in runner_records
        if record.method_condition == "M0"
    )
    trajectory = json.loads(store.read_verified(trajectory_ref))
    terminal_ref = ArtifactRef(**trajectory["terminal_candidate_ref"])
    evaluator_store = ArtifactStore(root / "public-evaluator-store")
    authority = DevelopmentTerminalPublicEvaluationAuthority(
        store,
        evaluator_store,
        lambda _value, _evaluation_id: PublicEvaluatorResult(
            execution_status="completed",
            infrastructure_reason=None,
            stage_outcomes={
                "l0": {"status": "pass", "reason": None},
                "l1": {"status": "pass", "reason": None},
                "public_l2": {"status": "pass", "reason": None},
                "l3": {"status": "pass", "reason": None},
            },
            diagnostic_codes=(),
            raw_evaluator_record={"stdout": "private"},
            public_l2_harness={
                "status": "available",
                "harness_id": "trusted-runner-m0-v1",
                "manifest_sha256": "a" * 64,
                "bundle_sha256": "b" * 64,
                "reason": None,
            },
        ),
    )
    public_authority_outcome = authority.evaluate_once(
        terminal_candidate_ref=terminal_ref,
        public_contract_sha256=method_policy_sha256("M0"),
        public_profile_sha256="9" * 64,
        tool_environment_policy_sha256="f" * 64,
    )
    attempts = [
        {
            "attempt_id": 0,
            "pass_level": "L3",
            "failure_type": "none",
            "automatic_pass_credit": True,
            "repair_eligible": False,
            "repair_skip_reason": "initial_or_current_attempt_passed",
        }
    ]
    measurement = build_episode_measurement(attempts=attempts, patches=[])
    eval_dir = root / "legacy-authority" / "eval"
    eval_dir.mkdir(parents=True)
    (eval_dir / "labels.json").write_text(
        json.dumps(
            {
                "pass_level": "L3",
                "l2_sim_status": "pass",
                "l2_sim_skip_reason": None,
                "checks": {
                    "l0_complete": True,
                    "l1_lint_pass": True,
                    "l2_sim_pass": True,
                    "l3_synth_pass": True,
                },
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "trajectory.json").write_text(
        json.dumps(
            {
                "sample_id": "runner-m0",
                "attempt_measurements": attempts,
                "patches": [],
                "measurement": measurement,
            }
        ),
        encoding="utf-8",
    )
    public_projection, public_projection_ref = project_development_public_evaluation(
        store,
        sample_dir=root / "legacy-authority",
        episode_id="runner-m0",
        method_condition="M0",
        analysis_population="excluded",
        terminal_public_outcome_ref=public_authority_outcome.artifact_ref,
    )

    outcome, _ = reconcile_development_episode_outcome(
        store,
        public_evaluation_ref=public_projection_ref,
        trajectory_ref=trajectory_ref,
    )

    assert public_projection["public_authority_status"] == (
        "development_terminal_shadow_not_official"
    )
    assert public_projection["stage_outcomes"]["public_l2"] == {
        "status": "pass",
        "reason": None,
    }
    assert outcome["missingness"]["classification"] == "scoreable_public_record"
    assert outcome["vpp_l3_status"] == "not_evaluated"
    assert outcome["vpp_l3"] is None


def test_full_pack_runner_reconciliation_rejects_wrong_method_and_tamper() -> None:
    root = _new_test_root()
    store = ArtifactStore(root / "store")
    projection = "8" * 64
    methods, scenarios = _minimal_smoke_inputs(projection)
    _, smoke_ref = reconcile_excluded_full_pack(
        store,
        smoke_id="runner-negative",
        methods=methods,
        scenarios=scenarios,
    )
    records = _runner_artifacts(store, projection)
    mismatched = list(records)
    mismatched[2] = FullPackRunnerArtifactRecord("M2", records[1].trajectory_ref)
    with pytest.raises(FullPackReconciliationError, match="M2 trajectory method mismatch"):
        reconcile_full_pack_runner_artifacts(
            store,
            smoke_id="runner-negative",
            source_smoke_report_ref=smoke_ref,
            runner_artifacts=mismatched,
        )

    tampered_ref = records[0].trajectory_ref
    blob = store.root / "blobs" / tampered_ref.sha256[:2] / tampered_ref.sha256
    blob.write_bytes(b"tampered")
    with pytest.raises(ArtifactIntegrityError):
        reconcile_full_pack_runner_artifacts(
            store,
            smoke_id="runner-negative",
            source_smoke_report_ref=smoke_ref,
            runner_artifacts=records,
        )


def _excluded_completion_events(store: ArtifactStore, context, projection: str):
    methods, _ = _minimal_smoke_inputs(projection)
    method_inputs = {record.method_condition: record for record in methods}
    runner_records = _runner_artifacts(store, projection)
    trajectory_by_method = {
        record.method_condition: record.trajectory_ref for record in runner_records
    }
    shared_direct_ref = store.put_blob("method/shared-direct", b'{"project":"direct"}\n')
    shared_his_ref = store.put_blob("method/shared-his", b'{"his":"shared"}\n')
    shared_skeleton = MethodArtifactGateway(store).put_project(
        "method/shared-skeleton",
        _project("shared-skeleton"),
    )
    m2_plan_ref = store.put_blob("method/m2-plan", b'{"plan_text":"plain"}\n')
    m5_his_ref = store.put_blob("method/m5-his", b'{"his":"m5"}\n')
    events = []
    for method in ("M0", "M1", "M2", "M3", "M4", "M5"):
        episode_id = f"runner-{method.lower()}"
        pack = build_development_episode_pack(
            context,
            episode_id=episode_id,
            analysis_population="excluded",
            method_condition=method,
            evaluator_metadata={"scope": "assembler-test"},
        ).to_dict()
        pack_ref = store.put_validated_json(
            f"episode-packs/{episode_id}",
            pack,
            contract_key="episode_pack",
        )
        record = method_inputs[method]
        if method in {"M0", "M1"}:
            candidate_ref = shared_direct_ref
        else:
            candidate_ref = store.put_blob(
                f"method/{method.lower()}-candidate",
                json.dumps({"method": method}).encode("utf-8") + b"\n",
            )
        if method == "M2":
            planning_kind, planning_ref = "untyped_plan", m2_plan_ref
        elif method in {"M3", "M4"}:
            planning_kind, planning_ref = "system_his", shared_his_ref
        elif method == "M5":
            planning_kind, planning_ref = "system_his", m5_his_ref
        else:
            planning_kind, planning_ref = None, None
        events.append(
            {
                "event": "sample_completed",
                "sample_id": episode_id,
                "method_condition": method,
                "analysis_population": "excluded",
                "episode_pack_ref": pack_ref.to_dict(),
                "episode_pack_sha256": pack["pack_sha256"],
                "public_projection_sha256": projection,
                "canonical_trajectory_ref": trajectory_by_method[method].to_dict(),
                "method_artifacts": {
                    "method_condition": method,
                    "candidate_artifact_ref": candidate_ref.to_dict(),
                    "project_package_sha256": record.project_package_sha256,
                    "planning_kind": planning_kind,
                    "planning_artifact_ref": (
                        planning_ref.to_dict() if planning_ref is not None else None
                    ),
                    "skeleton_artifact_ref": (
                        shared_skeleton.artifact_ref.to_dict()
                        if method in {"M4", "M5"}
                        else None
                    ),
                    "skeleton_project_sha256": (
                        shared_skeleton.project_package_sha256
                        if method in {"M4", "M5"}
                        else None
                    ),
                    "h_status": record.h_status,
                    "skeleton_mode": (
                        "legacy_full_project"
                        if method in {"M0", "M1"}
                        else record.skeleton_mode
                    ),
                    "his_corrections_used": 0,
                },
            }
        )
    return events


def test_assemble_excluded_run_full_pack_from_closed_runner_events() -> None:
    root = _new_test_root()
    store = ArtifactStore(root / "store")
    ready = evaluate_requirement_boundary(
        ProjectRequest(
            "counter",
            8,
            "counter8",
            "Build an 8-bit synchronous counter with active-low reset.",
        ),
        _platform(),
    )
    context = freeze_ready_requirement_context(ready, _platform())
    projection = context.public_projection_sha256
    events = _excluded_completion_events(store, context, projection)
    events_path = root / "events.jsonl"
    events_path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    _, scenarios = _minimal_smoke_inputs(projection)

    smoke, smoke_ref, runner, runner_ref = assemble_excluded_run_full_pack(
        store,
        events_path=events_path,
        smoke_id="assembled-run",
        scenarios=scenarios,
    )

    assert smoke["g3_accepted"] is False
    assert runner["reconciliation"]["all_trajectories_verified"] is True
    assert json.loads(store.read_verified(smoke_ref)) == smoke
    assert json.loads(store.read_verified(runner_ref)) == runner


def _run_fake_complete_full_pack(
    monkeypatch,
    *,
    method_order,
    failed_stage=None,
    assemble_companions=True,
):
    root = _new_test_root()
    clock_ticks = iter(float(tick) for tick in range(100))
    monkeypatch.setattr(
        "sr2fpga_agent.model_budget.time",
        SimpleNamespace(monotonic=lambda: next(clock_ticks)),
    )
    harness_root = root / "trusted-public-l2"
    harness_manifest_path = harness_root / "manifest.json"
    requirement = (
        "Build an 8-bit signed integer streaming FIR filter with active-low reset."
    )
    direct = SourceConnection(
        name="direct",
        kind="deepseek",
        model="fake-model",
        generation_mode="direct",
    )
    his = SourceConnection(
        name="his",
        kind="openai_compat",
        model="fake-model",
        generation_mode="two_stage",
        system_his_schema_version="system-his-v1.2",
    )
    config = RunnerConfig(
        dataset_root=root / "datasets",
        export_root=root / "exports",
        run_root=root / "runs",
        provider="his",
        repair_provider="none",
        max_attempts=1,
        refresh_exports=False,
        sources={"direct": direct, "his": his},
        line_b_targets={"max_samples": 6},
        tasks=[
            TaskConfig(
                source="direct" if method in {"M0", "M1"} else "his",
                task_type="fir_filter",
                widths=[8],
                count=1,
                requirement=requirement,
                method_condition=method,
                analysis_population="excluded",
                semantic_instance_id="semantic-fir-full-pack-001",
                replicate_id="replicate-000",
                decoding_seed=17,
                paired_block_id="pair-fir-full-pack-001-seed-17",
                execution_schedule_seed=909991,
                decoding_control_mode="documented_seed_control",
                public_l2_harness_manifest=str(harness_manifest_path),
            )
            for method in method_order
        ],
    )
    samples = planned_samples(config)
    metadata = [sample.metadata(config) for sample in samples]
    his_response, free_project_response, behavior_response = _runner_model_responses(
        metadata[0],
        task_type="fir_filter",
        width=8,
    )
    harness_root.mkdir(parents=True)
    trusted_tb = (
        "module trusted_tb;\n"
        f"  {json.loads(his_response)['artifacts']['top_module']} dut();\n"
        "  initial begin #1; $finish; end\n"
        "endmodule\n"
    )
    trusted_tb_path = harness_root / "trusted_tb.v"
    trusted_tb_path.write_text(trusted_tb, encoding="utf-8", newline="\n")
    harness_manifest_path.write_text(
        json.dumps(
            {
                "contract_version": "development-public-l2-harness-v1",
                "harness_id": "excluded-fir-public-l2-v1",
                "evaluation_scope": "development_excluded_public_l2",
                "testbench_top": "trusted_tb",
                "language_standard": "verilog-2005",
                "files": [
                    {
                        "path": "trusted_tb.v",
                        "sha256": hashlib.sha256(
                            trusted_tb.encode("utf-8")
                        ).hexdigest(),
                    }
                ],
                "timeout_seconds": 20,
                "pass_rule": "simulator_exit_zero",
                "official_authority": False,
                "g4b_authorized": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    trusted_harness = load_development_public_l2_harness(harness_manifest_path)
    m2_plan_client = _StaticClient(
        "Use one registered counter module with active-low reset."
    )
    m2_project_client = _StaticClient(free_project_response)
    generators = [True]
    staged_clients = {
        "block_direct_initial": _StaticClient(
            free_project_response,
            failure=(
                RuntimeError("synthetic direct checkpoint failure")
                if failed_stage == "block_direct_initial"
                else None
            ),
        ),
        "block_req2his": _StaticClient(
            his_response,
            failure=(
                RuntimeError("synthetic System-HIS checkpoint failure")
                if failed_stage == "block_req2his"
                else None
            ),
        ),
        "block_skeleton_initial": _StaticClient(
            behavior_response,
            failure=(
                RuntimeError("synthetic skeleton checkpoint failure")
                if failed_stage == "block_skeleton_initial"
                else None
            ),
        ),
        "his2project": _StaticClient(free_project_response),
    }
    constructed_capabilities = []
    freeze_seen_before_provider_construction = []
    manifest_seen_before_model_method = []

    def checkpoint_manifest_exists():
        refs_root = (
            config.run_root
            / "excluded-m0-m5-full-pack"
            / "method_artifacts"
            / "refs"
            / "shared-checkpoint-manifests"
        )
        return refs_root.is_dir() and any(refs_root.rglob("*.json"))

    def build_generator(_connection, **_kwargs):
        manifest_seen_before_model_method.append(checkpoint_manifest_exists())
        _kwargs["event_sink"](
            {"event": "generation_stage_started", "stage": "req2his"}
        )
        assert generators.pop(0) is True
        model_budget = _kwargs["model_budget"]
        return _TwoStageGeneratorStub(
            model_budget.client(m2_plan_client, "two_stage"),
            model_budget.client(m2_project_client, "two_stage"),
        )

    def build_model_client(_config, sample, *, model_budget, stage):
        freeze_seen_before_provider_construction.append(
            (config.run_root / "excluded-m0-m5-full-pack" / "measurement_freeze.json").exists()
        )
        if stage == "his2project":
            manifest_seen_before_model_method.append(checkpoint_manifest_exists())
        constructed_capabilities.append((sample.method_condition, stage))
        return model_budget.client(staged_clients[stage], stage)

    def build_agent(dataset_root, **kwargs):
        return RealDataGenerationAgent(
            dataset_root,
            command_runner=_PassingCommandRunner(),
            **kwargs,
        )

    monkeypatch.setattr(
        "sr2fpga_agent.runner.build_project_generator_for_connection",
        build_generator,
    )
    monkeypatch.setattr(
        "sr2fpga_agent.runner._model_client_for_sample",
        build_model_client,
    )
    monkeypatch.setattr("sr2fpga_agent.runner.DataGenerationAgent", build_agent)
    monkeypatch.setattr(
        "sr2fpga_agent.runner._development_hidden_evaluator",
        lambda _value: {
            "outcome": "pass",
            "private_case": "excluded-full-pack-hidden-secret",
        },
    )

    preflight = runner_preflight(config, validate_provider=False)
    assert [sample["method_condition"] for sample in preflight["samples"]] == list(
        method_order
    )
    preflight_by_sample = {
        sample["sample_id"]: sample["episode_pack"] for sample in preflight["samples"]
    }
    summary = run_batch(config, run_id="excluded-m0-m5-full-pack", resume=False)
    run_dir = config.run_root / "excluded-m0-m5-full-pack"
    store = ArtifactStore(run_dir / "method_artifacts")
    events_path = run_dir / "events.jsonl"
    projection = metadata[0]["episode_pack"]["public_context"][
        "public_projection_sha256"
    ]
    run_events = [
        json.loads(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
    ]
    completion_events = [
        event for event in run_events if event.get("event") == "sample_completed"
    ]
    if failed_stage is not None or not assemble_companions:
        return SimpleNamespace(
            completion_events=completion_events,
            config=config,
            constructed_capabilities=constructed_capabilities,
            events_path=events_path,
            m2_plan_client=m2_plan_client,
            m2_project_client=m2_project_client,
            method_order=method_order,
            projection=projection,
            run_dir=run_dir,
            run_events=run_events,
            run_id="excluded-m0-m5-full-pack",
            staged_clients=staged_clients,
            store=store,
            summary=summary,
        )
    _, scenarios = _minimal_smoke_inputs(projection)
    smoke, smoke_ref, runner, runner_ref, costs, costs_ref = (
        assemble_excluded_run_full_pack_with_cost_views(
            store,
            events_path=events_path,
            smoke_id="actual-runner-full-pack",
            scenarios=scenarios,
            reducer_policy_sha256="6" * 64,
        )
    )
    _, _, _, _, outcomes, outcomes_ref = assemble_excluded_run_full_pack_with_outcomes(
        store,
        events_path=events_path,
        smoke_id="actual-runner-full-pack",
        scenarios=scenarios,
    )
    return SimpleNamespace(
        completion_events=completion_events,
        config=config,
        constructed_capabilities=constructed_capabilities,
        costs=costs,
        costs_ref=costs_ref,
        events_path=events_path,
        freeze_seen_before_provider_construction=freeze_seen_before_provider_construction,
        generators=generators,
        metadata=metadata,
        method_order=method_order,
        m2_plan_client=m2_plan_client,
        m2_project_client=m2_project_client,
        manifest_seen_before_model_method=manifest_seen_before_model_method,
        outcomes=outcomes,
        outcomes_ref=outcomes_ref,
        preflight=preflight,
        preflight_by_sample=preflight_by_sample,
        projection=projection,
        responses=(
            his_response.encode("utf-8"),
            free_project_response.encode("utf-8"),
            behavior_response.encode("utf-8"),
        ),
        run_dir=run_dir,
        run_events=run_events,
        run_id="excluded-m0-m5-full-pack",
        runner=runner,
        runner_ref=runner_ref,
        scenarios=scenarios,
        smoke=smoke,
        smoke_ref=smoke_ref,
        staged_clients=staged_clients,
        store=store,
        summary=summary,
        trusted_harness=trusted_harness,
    )


def _standalone_initial_calls(costs):
    return {
        record["method_condition"]: record["standalone_attributed_axes"][
            "logical_model_calls"
        ]["value"]
        for record in costs["method_records"]
    }


def _method_keyed_views(costs):
    return {
        "actual_block_axes": _order_invariant_axes(costs["actual_block_axes"]),
        "methods": {
            record["method_condition"]: {
                "terminal_status": record["terminal_status"],
                "exclusive_axes": _order_invariant_axes(record["exclusive_axes"]),
                "standalone_attributed_axes": _order_invariant_axes(
                    record["standalone_attributed_axes"]
                ),
            }
            for record in costs["method_records"]
        },
        "contrasts": {
            record["contrast_id"]: {
                "status": record["status"],
                "reason": record["reason"],
                "arms": {
                    arm["method_condition"]: _order_invariant_axes(arm["axes"])
                    for arm in record["arms"]
                },
                "signed_delta_axes": _order_invariant_axes(
                    record["signed_delta_axes"]
                ),
            }
            for record in costs["incremental_contrasts"]
        },
    }


def _order_invariant_axes(axes):
    return {
        axis: (
            {**measurement, "value": "measured_duration"}
            if axis in DURATION_COST_AXES and measurement["status"] == "measured"
            else measurement
        )
        for axis, measurement in axes.items()
    }


def _physical_provider_calls(completed):
    return sum(
        len(client.calls)
        for client in (
            *completed.staged_clients.values(),
            completed.m2_plan_client,
            completed.m2_project_client,
        )
    )


def _artifact_ref_path(store: ArtifactStore, reference: ArtifactRef) -> Path:
    path = store.root / "refs" / Path(*reference.key.split("/"))
    return path.with_name(path.name + ".ref.json")


def _artifact_blob_path(store: ArtifactStore, reference: ArtifactRef) -> Path:
    return store.root / "blobs" / reference.sha256[:2] / reference.sha256


def _replace_artifact_key_with_payload(
    store: ArtifactStore,
    reference: ArtifactRef,
    payload: dict,
    *,
    mutation: str,
) -> ArtifactRef:
    content = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    alternate = store.put_blob(
        f"resume-mutations/{mutation}",
        content,
        media_type=reference.media_type,
    )
    replacement = ArtifactRef(
        key=reference.key,
        sha256=alternate.sha256,
        size_bytes=alternate.size_bytes,
        media_type=alternate.media_type,
    )
    _artifact_ref_path(store, reference).write_text(
        json.dumps(
            replacement.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return replacement


def _file_tree_snapshot(root: Path) -> dict[str, tuple[int, str]]:
    return {
        path.relative_to(root).as_posix(): (
            path.stat().st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in root.rglob("*")
        if path.is_file()
    }


def _write_json_file(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _overwrite_artifact_payload(
    store: ArtifactStore, reference: ArtifactRef, payload: dict
) -> None:
    _artifact_blob_path(store, reference).write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def _persisted_preparation_audit(completed):
    config_path = completed.run_dir / "config.json"
    run_config = json.loads(config_path.read_text(encoding="utf-8"))
    paired_block_id, audit = next(
        iter(run_config["audit_only"]["block_preparations"].items())
    )
    return config_path, run_config, paired_block_id, audit


def _mutate_persisted_resume_factor(completed, mutation: str) -> None:
    config_path, run_config, _paired_block_id, audit = (
        _persisted_preparation_audit(completed)
    )
    manifest_ref = ArtifactRef(**audit["checkpoint_manifest_ref"])
    manifest = json.loads(completed.store.read_verified(manifest_ref))
    if mutation == "manifest_content":
        _artifact_blob_path(completed.store, manifest_ref).write_bytes(b"{}\n")
        return
    if mutation == "checkpoint_artifact_ref":
        direct_ref = ArtifactRef(**manifest["nodes"][0]["artifact_ref"])
        skeleton_ref = ArtifactRef(**manifest["nodes"][2]["artifact_ref"])
        replacement = ArtifactRef(
            key=direct_ref.key,
            sha256=skeleton_ref.sha256,
            size_bytes=skeleton_ref.size_bytes,
            media_type=skeleton_ref.media_type,
        )
        _artifact_ref_path(completed.store, direct_ref).write_text(
            json.dumps(
                replacement.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        return
    if mutation == "source_event_parent_sequence":
        event_ref = ArtifactRef(**audit["block_event_refs"][1])
        event = json.loads(completed.store.read_verified(event_ref))
        event["sequence"] += 1
        event["parent_event_id"] = "block-preparation-event-" + "0" * 64
        _overwrite_artifact_payload(completed.store, event_ref, event)
        return
    if mutation == "graph_consumer":
        manifest["nodes"][0]["consumer_methods"] = ["M0", "M2"]
        _overwrite_artifact_payload(completed.store, manifest_ref, manifest)
        return
    if mutation == "policy_hash":
        audit["preparation_policy_sha256"] = "f" * 64
        _write_json_file(config_path, run_config)
        return
    if mutation == "close_total":
        close_ref = ArtifactRef(**audit["block_event_refs"][-1])
        close_event = json.loads(completed.store.read_verified(close_ref))
        close_event["cost_delta"]["logical_model_calls"] += 1
        _overwrite_artifact_payload(completed.store, close_ref, close_event)
        return
    if mutation == "partial_state":
        audit.pop("checkpoint_manifest_ref")
        _write_json_file(config_path, run_config)
        return
    raise AssertionError(f"unknown resume mutation: {mutation}")


def _resume_side_effect_spies(monkeypatch):
    from sr2fpga_agent import runner as runner_module

    spies = {
        "paired_materialization": mock.Mock(
            wraps=runner_module._materialize_development_paired_blocks
        ),
        "tool_collection": mock.Mock(
            wraps=runner_module.collect_development_tool_environment
        ),
        "json_write": mock.Mock(wraps=runner_module._write_json),
    }
    monkeypatch.setattr(
        runner_module,
        "_materialize_development_paired_blocks",
        spies["paired_materialization"],
    )
    monkeypatch.setattr(
        runner_module,
        "collect_development_tool_environment",
        spies["tool_collection"],
    )
    monkeypatch.setattr(runner_module, "_write_json", spies["json_write"])
    return spies


def test_runner_resume_rejects_valid_manifest_substitution_before_side_effects(
    monkeypatch,
) -> None:
    completed = _run_fake_complete_full_pack(
        monkeypatch,
        method_order=build_balanced_method_orders(909991)[0],
        assemble_companions=False,
    )
    paired_block_id, audit = next(
        iter(completed.summary["audit_only"]["block_preparations"].items())
    )
    original_ref = ArtifactRef(**audit["checkpoint_manifest_ref"])
    manifest = json.loads(completed.store.read_verified(original_ref))
    manifest["nodes"] = list(reversed(manifest["nodes"]))
    replacement_ref = _replace_artifact_key_with_payload(
        completed.store,
        original_ref,
        manifest,
        mutation="valid-manifest-substitution",
    )
    assert replacement_ref != original_ref
    assert completed.store.reference(original_ref.key) == replacement_ref
    calls_before = _physical_provider_calls(completed)
    events_before = completed.events_path.read_bytes()
    files_before = _file_tree_snapshot(completed.run_dir)
    spies = _resume_side_effect_spies(monkeypatch)

    with pytest.raises(
        SharedCheckpointResumeError,
        match="requires a new run ID",
    ):
        run_batch(completed.config, run_id=completed.run_id, resume=True)

    assert paired_block_id in completed.summary["audit_only"]["block_preparations"]
    assert _physical_provider_calls(completed) == calls_before
    assert completed.events_path.read_bytes() == events_before
    assert _file_tree_snapshot(completed.run_dir) == files_before
    assert all(spy.call_count == 0 for spy in spies.values())


def test_runner_resume_rejects_coordinated_config_and_manifest_substitution(
    monkeypatch,
) -> None:
    completed = _run_fake_complete_full_pack(
        monkeypatch,
        method_order=build_balanced_method_orders(909991)[0],
        assemble_companions=False,
    )
    config_path, run_config, paired_block_id, config_audit = (
        _persisted_preparation_audit(completed)
    )
    original_ref = ArtifactRef(**config_audit["checkpoint_manifest_ref"])
    manifest = json.loads(completed.store.read_verified(original_ref))
    manifest["nodes"] = list(reversed(manifest["nodes"]))
    replacement_ref = _replace_artifact_key_with_payload(
        completed.store,
        original_ref,
        manifest,
        mutation="coordinated-valid-manifest-substitution",
    )
    config_audit["checkpoint_manifest_ref"] = replacement_ref.to_dict()
    _write_json_file(config_path, run_config)
    completion_audits = {
        json.dumps(event["block_preparation_audit"], sort_keys=True)
        for event in completed.run_events
        if event.get("event") == "sample_completed"
        and event.get("paired_block_id") == paired_block_id
    }
    assert completion_audits == {json.dumps(
        {
            **config_audit,
            "checkpoint_manifest_ref": original_ref.to_dict(),
        },
        sort_keys=True,
    )}
    calls_before = _physical_provider_calls(completed)
    events_before = completed.events_path.read_bytes()
    files_before = _file_tree_snapshot(completed.run_dir)
    spies = _resume_side_effect_spies(monkeypatch)

    with pytest.raises(
        SharedCheckpointResumeError,
        match="requires a new run ID",
    ):
        run_batch(completed.config, run_id=completed.run_id, resume=True)

    assert _physical_provider_calls(completed) == calls_before
    assert completed.events_path.read_bytes() == events_before
    assert _file_tree_snapshot(completed.run_dir) == files_before
    assert all(spy.call_count == 0 for spy in spies.values())


@pytest.mark.parametrize(
    "completion_mutation",
    ("remove_all", "duplicate_one"),
)
def test_runner_resume_requires_exact_planned_completion_consensus(
    monkeypatch, completion_mutation: str
) -> None:
    completed = _run_fake_complete_full_pack(
        monkeypatch,
        method_order=build_balanced_method_orders(909991)[0],
        assemble_companions=False,
    )
    events = [
        json.loads(line)
        for line in completed.events_path.read_text(encoding="utf-8").splitlines()
    ]
    completions = [event for event in events if event.get("event") == "sample_completed"]
    assert len(completions) == 6
    assert any(
        event.get("event") != "sample_completed"
        and isinstance(event.get("block_preparation_audit"), dict)
        for event in events
    )
    if completion_mutation == "remove_all":
        events = [
            event for event in events if event.get("event") != "sample_completed"
        ]
    else:
        events.append(dict(completions[0]))
    completed.events_path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    calls_before = _physical_provider_calls(completed)
    events_before = completed.events_path.read_bytes()
    files_before = _file_tree_snapshot(completed.run_dir)
    spies = _resume_side_effect_spies(monkeypatch)

    with pytest.raises(
        SharedCheckpointResumeError,
        match="requires a new run ID",
    ):
        run_batch(completed.config, run_id=completed.run_id, resume=True)

    assert _physical_provider_calls(completed) == calls_before
    assert completed.events_path.read_bytes() == events_before
    assert _file_tree_snapshot(completed.run_dir) == files_before
    assert all(spy.call_count == 0 for spy in spies.values())


def test_runner_rejects_legacy_resume_before_freeze_or_artifact_writes(
    monkeypatch,
) -> None:
    completed = _run_fake_complete_full_pack(
        monkeypatch,
        method_order=build_balanced_method_orders(909991)[0],
        assemble_companions=False,
    )
    config_path = completed.run_dir / "config.json"
    run_config = json.loads(config_path.read_text(encoding="utf-8"))
    run_config.pop("audit_only")
    config_path.write_text(
        json.dumps(run_config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    freeze_path = completed.run_dir / "measurement_freeze.json"
    measurement_freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    measurement_freeze.pop("block_preparation_policies")
    measurement_freeze["freeze_fingerprint"] = freeze_fingerprint(
        measurement_freeze
    )
    freeze_path.write_text(
        json.dumps(measurement_freeze, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    calls_before = _physical_provider_calls(completed)
    events_before = completed.events_path.read_bytes()
    files_before = _file_tree_snapshot(completed.run_dir)
    spies = _resume_side_effect_spies(monkeypatch)

    with pytest.raises(
        SharedCheckpointResumeError,
        match="requires a new run ID",
    ):
        run_batch(completed.config, run_id=completed.run_id, resume=True)

    assert _physical_provider_calls(completed) == calls_before
    assert completed.events_path.read_bytes() == events_before
    assert _file_tree_snapshot(completed.run_dir) == files_before
    assert all(spy.call_count == 0 for spy in spies.values())


@pytest.mark.parametrize(
    "mutation",
    (
        "manifest_content",
        "checkpoint_artifact_ref",
        "source_event_parent_sequence",
        "graph_consumer",
        "policy_hash",
        "close_total",
        "partial_state",
    ),
)
def test_runner_resume_negative_matrix_rejects_before_all_side_effects(
    monkeypatch, mutation: str
) -> None:
    completed = _run_fake_complete_full_pack(
        monkeypatch,
        method_order=build_balanced_method_orders(909991)[0],
        assemble_companions=False,
    )
    _mutate_persisted_resume_factor(completed, mutation)
    calls_before = _physical_provider_calls(completed)
    events_before = completed.events_path.read_bytes()
    files_before = _file_tree_snapshot(completed.run_dir)
    spies = _resume_side_effect_spies(monkeypatch)

    with pytest.raises(
        SharedCheckpointResumeError,
        match="requires a new run ID",
    ):
        run_batch(completed.config, run_id=completed.run_id, resume=True)

    assert _physical_provider_calls(completed) == calls_before
    assert completed.events_path.read_bytes() == events_before
    assert _file_tree_snapshot(completed.run_dir) == files_before
    assert all(spy.call_count == 0 for spy in spies.values())


@pytest.mark.parametrize(
    ("failed_stage", "blocked"),
    (
        ("block_direct_initial", {"M0", "M1"}),
        ("block_req2his", {"M3", "M4", "M5"}),
        ("block_skeleton_initial", {"M4", "M5"}),
    ),
)
def test_real_runner_checkpoint_failure_blocks_only_manifest_consumers(
    monkeypatch, failed_stage: str, blocked: set[str]
) -> None:
    completed = _run_fake_complete_full_pack(
        monkeypatch,
        method_order=build_balanced_method_orders(909991)[0],
        failed_stage=failed_stage,
    )
    completion_methods = {
        event["method_condition"] for event in completed.completion_events
    }
    blocked_events = [
        event
        for event in completed.run_events
        if event.get("event") == "sample_blocked_by_shared_checkpoint"
    ]

    all_methods = {"M0", "M1", "M2", "M3", "M4", "M5"}
    assert completion_methods == all_methods - blocked
    assert {event["method_condition"] for event in blocked_events} == blocked
    assert all(event["canonical_trajectory_ref"] is None for event in blocked_events)
    assert all(event["terminal_status"] == "blocked_by_shared_checkpoint" for event in blocked_events)
    assert {event["sample_id"] for event in blocked_events}.issubset(
        completed.summary["buckets"]["not_run"]
    )
    assert not any(
        capability[0] in blocked
        for capability in completed.constructed_capabilities
        if capability[1] not in {
            "block_direct_initial",
            "block_req2his",
            "block_skeleton_initial",
        }
    )


def test_real_runner_three_view_costs_are_order_invariant(monkeypatch) -> None:
    orders = build_balanced_method_orders(909991)
    first = _run_fake_complete_full_pack(monkeypatch, method_order=orders[0])
    second = _run_fake_complete_full_pack(monkeypatch, method_order=orders[3])

    assert first.method_order != second.method_order
    assert first.responses == second.responses
    assert _physical_provider_calls(first) == 6
    assert _physical_provider_calls(second) == 6
    assert first.costs["actual_block_axes"]["logical_model_calls"]["value"] == 6
    assert second.costs["actual_block_axes"]["logical_model_calls"]["value"] == 6
    expected_standalone_calls = {
        "M0": 1,
        "M1": 1,
        "M2": 2,
        "M3": 2,
        "M4": 2,
        "M5": 2,
    }
    assert _standalone_initial_calls(first.costs) == expected_standalone_calls
    assert _standalone_initial_calls(second.costs) == expected_standalone_calls
    assert _method_keyed_views(first.costs) == _method_keyed_views(second.costs)

    for completed in (first, second):
        assert completed.manifest_seen_before_model_method
        assert all(completed.manifest_seen_before_model_method)
        completion_by_method = {
            event["method_condition"]: event for event in completed.completion_events
        }
        audit = completed.completion_events[0]["block_preparation_audit"]
        assert all(
            event["block_preparation_audit"] == audit
            for event in completed.completion_events
        )
        manifest = json.loads(
            completed.store.read_verified(ArtifactRef(**audit["checkpoint_manifest_ref"]))
        )
        lineage_hashes = {
            ArtifactRef(**audit["checkpoint_manifest_ref"]).sha256,
            *(
                ArtifactRef(**reference).sha256
                for reference in audit["block_event_refs"]
            ),
        }
        for event in completed.completion_events:
            trajectory = json.loads(
                completed.store.read_verified(
                    ArtifactRef(**event["canonical_trajectory_ref"])
                )
            )
            assert all(
                lineage_hashes.issubset(attempt["input_artifact_hashes"])
                for attempt in trajectory["attempts"]
            )
        skeleton_node = next(
            node
            for node in manifest["nodes"]
            if node["checkpoint_id"] == "skeleton_initial_project"
        )
        complete_initial_ref = skeleton_node["artifact_ref"]
        assert completion_by_method["M4"]["method_artifacts"][
            "candidate_artifact_ref"
        ] == complete_initial_ref
        assert completion_by_method["M5"]["method_artifacts"][
            "candidate_artifact_ref"
        ] == complete_initial_ref
        first_method_event = next(
            event
            for event in completed.run_events
            if event.get("event")
            in {
                "generation_stage_started",
                "model_call_started",
                "model_call_finished",
                "model_call_failed",
            }
        )
        assert first_method_event["block_preparation_audit"][
            "checkpoint_manifest_ref"
        ] == audit["checkpoint_manifest_ref"]
        block_event_ids = set(
            completed.costs["source_event_partition"]["block_event_ids"]
        )
        assert all(
            block_event_ids.isdisjoint(method_event_ids)
            for method_event_ids in completed.costs["source_event_partition"][
                "method_event_ids"
            ].values()
        )
        assert all(
            completed.costs[field] is False
            for field in (
                "official_outcome",
                "official_authority",
                "pass_credit_authority",
                "rq1_evidence",
                "rq2_evidence",
                "g3_accepted",
                "g4b_authorized",
            )
        )
        assert completed.costs["reconciliation"]["all_authority_fields_false"] is True
        assert json.loads(completed.store.read_verified(completed.costs_ref)) == (
            completed.costs
        )
        assert read_development_paired_block_cost_reconciliation(
            completed.store, completed.costs_ref
        ) == completed.costs

    summary = first.summary
    generators = first.generators
    constructed_capabilities = first.constructed_capabilities
    freeze_seen_before_provider_construction = (
        first.freeze_seen_before_provider_construction
    )
    completion_events = first.completion_events
    store = first.store
    config = first.config
    run_dir = first.run_dir
    preflight = first.preflight
    preflight_by_sample = first.preflight_by_sample
    smoke = first.smoke
    smoke_ref = first.smoke_ref
    runner = first.runner
    runner_ref = first.runner_ref
    outcomes = first.outcomes
    outcomes_ref = first.outcomes_ref
    trusted_harness = first.trusted_harness
    staged_clients = first.staged_clients
    m2_plan_client = first.m2_plan_client
    m2_project_client = first.m2_project_client
    method_order = first.method_order
    events_path = first.events_path
    run_events = first.run_events
    scenarios = first.scenarios

    assert summary["total_completed"] == 6
    assert generators == []
    assert constructed_capabilities == [
        ("M0", "block_direct_initial"),
        ("M4", "block_req2his"),
        ("M4", "block_skeleton_initial"),
        ("M3", "his2project"),
    ]
    assert freeze_seen_before_provider_construction == [True, True, True, True]
    assert {event["method_condition"] for event in completion_events} == {
        "M0",
        "M1",
        "M2",
        "M3",
        "M4",
        "M5",
    }
    assert all(event["analysis_population"] == "excluded" for event in completion_events)
    assert all("canonical_trajectory_ref" in event for event in completion_events)
    assert all("development_hidden_outcome_ref" in event for event in completion_events)
    assert all(
        "development_hidden_conformance_outcome_ref" in event
        for event in completion_events
    )
    assert all(
        "development_public_evaluation_ref" in event for event in completion_events
    )
    assert all(
        "development_episode_outcome_ref" in event for event in completion_events
    )
    assert all("method_artifacts" in event for event in completion_events)
    paired_refs = {
        json.dumps(event["paired_block_ref"], sort_keys=True)
        for event in completion_events
    }
    assert len(paired_refs) == 1
    paired_ref = ArtifactRef(**completion_events[0]["paired_block_ref"])
    paired_block = load_development_paired_block(store, paired_ref)
    assert paired_block["method_order"] == [
        event["method_condition"] for event in completion_events
    ]
    assert paired_block["replicate_id"] == "replicate-000"
    assert paired_block["execution_schedule_seed"] == 909991
    assert paired_block["requested_decoding_seed"] == 17
    for event in completion_events:
        assert event["execution_ordinal"] == paired_block["method_order"].index(
            event["method_condition"]
        )
        assert event["replicate_id"] == paired_block["replicate_id"]
        assert event["execution_schedule_seed"] == 909991
        assert event["decoding_control_mode"] == "documented_seed_control"
        pack = json.loads(store.read_verified(ArtifactRef(**event["episode_pack_ref"])))
        assert pack["audit_only"]["paired_block_ref"] == paired_ref.to_dict()
        assert preflight_by_sample[event["sample_id"]]["pack_sha256"] == pack["pack_sha256"]
        assert preflight_by_sample[event["sample_id"]][
            "paired_block_ref"
        ] == paired_ref.to_dict()
    measurement_freeze = json.loads(
        (run_dir / "measurement_freeze.json").read_text(encoding="utf-8")
    )
    assert {
        json.dumps(record["paired_block_ref"], sort_keys=True)
        for record in measurement_freeze["samples"]
    } == paired_refs
    paired_block_id = paired_block["paired_block_id"]
    assert measurement_freeze["block_preparation_policies"] == preflight[
        "block_preparation_policies"
    ]
    policy = measurement_freeze["block_preparation_policies"][paired_block_id]
    assert policy["physical_initial_model_call_ceiling"] == 3
    assert policy["exclusive_model_call_ceilings"] == {
        "M0": 0,
        "M1": 0,
        "M2": 2,
        "M3": 1,
        "M4": 0,
        "M5": 0,
    }
    preparation_audit = summary["audit_only"]["block_preparations"][
        paired_block_id
    ]
    assert preparation_audit["preparation_policy_sha256"] == policy[
        "preparation_policy_sha256"
    ]
    assert all(
        event["block_preparation_audit"] == preparation_audit
        for event in completion_events
    )
    generation_events = [
        event
        for event in run_events
        if event.get("event")
        in {
            "generation_stage_started",
            "model_call_started",
            "model_call_finished",
            "model_call_failed",
        }
    ]
    assert generation_events
    assert all(
        event["block_preparation_audit"] == preparation_audit
        for event in generation_events
    )
    run_config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    assert run_config["audit_only"]["block_preparations"][paired_block_id] == (
        preparation_audit
    )
    manifest_ref = ArtifactRef(**preparation_audit["checkpoint_manifest_ref"])
    manifest = json.loads(store.read_verified(manifest_ref))
    assert manifest["preparation_policy_sha256"] == policy[
        "preparation_policy_sha256"
    ]
    preparation_event_hashes = {
        ArtifactRef(**reference).sha256
        for reference in preparation_audit["block_event_refs"]
    }
    assert preparation_event_hashes
    assert smoke["g3_accepted"] is False
    assert outcomes["summary"]["frozen_episode_count"] == 6
    assert outcomes["summary"]["retained_episode_count"] == 6
    assert outcomes["summary"]["vpp_not_evaluated_count"] == 6
    assert outcomes["summary"]["vpp_evaluated_count"] == 0
    assert outcomes["summary"]["development_vpp_evaluated_count"] == 6
    assert outcomes["summary"]["development_vpp_pass_count"] == 6
    assert outcomes["summary"]["development_vpp_fail_count"] == 0
    assert outcomes["summary"]["development_vpp_not_evaluated_count"] == 0
    assert outcomes["summary"]["replacement_count"] == 0
    assert outcomes["summary"]["repair_calls_attempted"] == 0
    assert outcomes["summary"]["repair_transitions"] == 0
    assert outcomes["summary"]["repair_successes"] == 0
    assert outcomes["summary"]["missingness_counts"] == {
        "scoreable_public_record": 6,
        "design_outcome": 0,
        "infrastructure_unscorable": 0,
    }
    assert outcomes["blocking_gaps"] == [
        "runtime_scenario_evidence_reconciliation",
        "official_public_terminal_hidden_authority",
        "g4b_campaign_authority",
    ]
    assert json.loads(store.read_verified(outcomes_ref)) == outcomes
    assert runner["reconciliation"]["all_trajectories_verified"] is True
    assert runner["paired_block_ref"] == paired_ref.to_dict()
    assert runner["method_order"] == paired_block["method_order"]
    assert runner["actual_method_order"] == paired_block["method_order"]
    assert runner["method_order_verified"] is True
    assert json.loads(store.read_verified(smoke_ref)) == smoke
    assert json.loads(store.read_verified(runner_ref)) == runner
    expected_harness_evidence = trusted_harness.public_evidence()
    completion_by_method = {
        event["method_condition"]: event for event in completion_events
    }
    standalone_ceilings = {"M0": 1, "M1": 1, "M2": 2, "M3": 2, "M4": 2, "M5": 2}
    for event in completion_events:
        sample_metadata = json.loads(
            (config.dataset_root / event["sample_id"] / "metadata.json").read_text(
                encoding="utf-8"
            )
        )
        method = event["method_condition"]
        assert sample_metadata["standalone_model_call_ceiling"] == (
            standalone_ceilings[method]
        )
        assert sample_metadata["exclusive_model_call_ceiling"] == policy[
            "exclusive_model_call_ceilings"
        ][method]
        assert sample_metadata["model_call_budget"]["max_model_calls"] == policy[
            "exclusive_model_call_ceilings"
        ][method]
        assert sample_metadata["model_call_budget"][
            "standalone_max_model_calls"
        ] == standalone_ceilings[method]
        assert sample_metadata["model_call_budget"]["model_call_budget_scope"] == (
            "paired_block_exclusive"
        )
        trajectory = json.loads(
            store.read_verified(ArtifactRef(**event["canonical_trajectory_ref"]))
        )
        selected = json.loads(
            store.read_verified(
                ArtifactRef(**trajectory["development_selected_public_outcome_ref"])
            )
        )
        terminal = json.loads(
            store.read_verified(
                ArtifactRef(**trajectory["development_terminal_public_outcome_ref"])
            )
        )
        assert selected["stage_outcomes"]["public_l2"] == {
            "status": "pass",
            "reason": None,
        }
        assert terminal["stage_outcomes"]["public_l2"] == {
            "status": "pass",
            "reason": None,
        }
        assert selected["public_l2_harness"] == expected_harness_evidence
        assert terminal["public_l2_harness"] == expected_harness_evidence
        cost_summary = json.loads(
            store.read_verified(
                ArtifactRef(**trajectory["attempts"][0]["cost_summary_ref"])
            )
        )
        assert (
            trusted_harness.manifest_sha256
            in trajectory["attempts"][0]["input_artifact_hashes"]
        )
        assert (
            trusted_harness.bundle_sha256
            in trajectory["attempts"][0]["input_artifact_hashes"]
        )
        assert paired_ref.sha256 in trajectory["attempts"][0]["input_artifact_hashes"]
        assert manifest_ref.sha256 in trajectory["attempts"][0]["input_artifact_hashes"]
        assert preparation_event_hashes.issubset(
            trajectory["attempts"][0]["input_artifact_hashes"]
        )
        assert cost_summary["axes"]["public_tool_calls"]["value"] >= 8

    first_method = method_order[0]
    assert first_method == "M1"
    first_trajectory = json.loads(
        store.read_verified(
            ArtifactRef(**completion_by_method[first_method]["canonical_trajectory_ref"])
        )
    )
    first_cost_summary = json.loads(
        store.read_verified(
            ArtifactRef(**first_trajectory["attempts"][0]["cost_summary_ref"])
        )
    )
    assert first_cost_summary["axes"]["logical_model_calls"]["value"] == 0

    all_prompt_calls = [
        *[call for client in staged_clients.values() for call in client.calls],
        *m2_plan_client.calls,
        *m2_project_client.calls,
    ]
    assert len(all_prompt_calls) == 6
    serialized_prompts = json.dumps(all_prompt_calls, ensure_ascii=False)
    forbidden_prompt_values = (
        paired_block_id,
        paired_ref.sha256,
        paired_ref.key,
        paired_block["replicate_id"],
        str(paired_block["execution_schedule_seed"]),
        policy["preparation_policy_sha256"],
        manifest_ref.sha256,
        manifest_ref.key,
        *(reference["sha256"] for reference in preparation_audit["block_event_refs"]),
        *first.costs["source_event_partition"]["block_event_ids"],
        "checkpoint_manifest_ref",
        "manifest_status",
        "parent_checkpoint_ids",
        "consumer_methods",
        "checkpoint_cost",
        "block_event_refs",
        "block_event_ids",
        "exclusive_model_call_ceilings",
        "standalone_attributed",
        "actual_block_consumption",
        "actual_block_axes",
        "execution_ordinal",
        "method_order",
        "sibling_method",
        "sibling_method_status",
        "sibling_method_outcomes",
        "reconciliation_output",
        "reconciliation_status",
        "source_event_partition",
        "hidden_commitments",
    )
    assert all(
        value not in config.tasks[0].requirement for value in forbidden_prompt_values
    )
    assert all(value not in serialized_prompts for value in forbidden_prompt_values)

    reordered_dir = run_dir / "tampered-completion-order"
    reordered_dir.mkdir()
    (reordered_dir / "measurement_freeze.json").write_text(
        (run_dir / "measurement_freeze.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (reordered_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in reversed(completion_events)) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(FullPackReconciliationError, match="execution order"):
        assemble_excluded_run_full_pack(
            store,
            events_path=reordered_dir / "events.jsonl",
            smoke_id="tampered-completion-order",
            scenarios=scenarios,
        )

    missing_block_trajectory = json.loads(
        store.read_verified(ArtifactRef(**completion_events[0]["canonical_trajectory_ref"]))
    )
    missing_block_trajectory["attempts"][0]["input_artifact_hashes"].remove(
        paired_ref.sha256
    )
    missing_block_trajectory_ref = store.put_validated_json(
        "tampered-trajectories/missing-paired-block-sha",
        missing_block_trajectory,
        contract_key="trajectory_v2",
    )
    missing_hash_events = [dict(event) for event in completion_events]
    missing_hash_events[0]["canonical_trajectory_ref"] = (
        missing_block_trajectory_ref.to_dict()
    )
    missing_hash_dir = run_dir / "tampered-trajectory-input"
    missing_hash_dir.mkdir()
    (missing_hash_dir / "measurement_freeze.json").write_text(
        (run_dir / "measurement_freeze.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (missing_hash_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in missing_hash_events) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(FullPackReconciliationError, match="trajectory attempt"):
        assemble_excluded_run_full_pack(
            store,
            events_path=missing_hash_dir / "events.jsonl",
            smoke_id="tampered-trajectory-input",
            scenarios=scenarios,
        )

    tampered_freeze = json.loads(
        (run_dir / "measurement_freeze.json").read_text(encoding="utf-8")
    )
    tampered_freeze["samples"][0]["execution_ordinal"] = 5
    tampered_freeze["freeze_fingerprint"] = freeze_fingerprint(tampered_freeze)
    tampered_freeze_events = [dict(event) for event in completion_events]
    for event in tampered_freeze_events:
        event["freeze_fingerprint"] = tampered_freeze["freeze_fingerprint"]
    tampered_freeze_dir = run_dir / "tampered-freeze-ordinal"
    tampered_freeze_dir.mkdir()
    (tampered_freeze_dir / "measurement_freeze.json").write_text(
        json.dumps(tampered_freeze),
        encoding="utf-8",
    )
    (tampered_freeze_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in tampered_freeze_events) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(FullPackReconciliationError, match="execution ordinal"):
        assemble_excluded_run_full_pack(
            store,
            events_path=tampered_freeze_dir / "events.jsonl",
            smoke_id="tampered-freeze-ordinal",
            scenarios=scenarios,
        )

    other_ref = write_development_paired_block(
        store,
        paired_block_id="pair-fir-full-pack-other",
        semantic_instance_id=paired_block["semantic_instance_id"],
        replicate_id=paired_block["replicate_id"],
        public_projection_sha256=paired_block["public_projection_sha256"],
        model_provenance_sha256=paired_block["model_provenance_sha256"],
        decoding_control_mode=paired_block["decoding_control_mode"],
        requested_decoding_seed=paired_block["requested_decoding_seed"],
        execution_schedule_seed=paired_block["execution_schedule_seed"],
        method_order=tuple(paired_block["method_order"]),
    )
    tampered_events = []
    replaced = False
    for line in events_path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event.get("event") == "sample_completed" and not replaced:
            event["paired_block_ref"] = other_ref.to_dict()
            replaced = True
        tampered_events.append(json.dumps(event))
    tampered_path = run_dir / "events-paired-ref-tampered.jsonl"
    tampered_path.write_text("\n".join(tampered_events) + "\n", encoding="utf-8")
    with pytest.raises(FullPackReconciliationError, match="paired-block reference"):
        assemble_excluded_run_full_pack(
            store,
            events_path=tampered_path,
            smoke_id="tampered-paired-ref",
            scenarios=scenarios,
        )

    provider_calls_before_resume = _physical_provider_calls(first)
    event_bytes_before_resume = events_path.read_bytes()
    manifest_bytes_before_resume = store.read_verified(manifest_ref)
    ref_paths_before_resume = sorted(
        path.relative_to(store.root).as_posix()
        for path in store.root.rglob("*.ref.json")
    )
    method_starts_before_resume = sum(
        event.get("event") == "generation_stage_started" for event in run_events
    )
    resumed = run_batch(config, run_id="excluded-m0-m5-full-pack", resume=True)
    assert resumed["total_completed"] == 6
    assert resumed["audit_only"]["block_preparations"][paired_block_id] == (
        preparation_audit
    )
    assert _physical_provider_calls(first) == provider_calls_before_resume
    assert events_path.read_bytes() == event_bytes_before_resume
    assert store.read_verified(manifest_ref) == manifest_bytes_before_resume
    assert sorted(
        path.relative_to(store.root).as_posix()
        for path in store.root.rglob("*.ref.json")
    ) == ref_paths_before_resume
    assert sum(
        event.get("event") == "generation_stage_started"
        for event in (
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
        )
    ) == method_starts_before_resume
    assert load_development_paired_block(store, paired_ref) == paired_block
    manifest_path = store.root / "refs" / Path(*manifest_ref.key.split("/"))
    manifest_path = manifest_path.with_name(manifest_path.name + ".ref.json")
    manifest_path.unlink()
    with pytest.raises(SharedCheckpointResumeError, match="new run ID"):
        run_batch(config, run_id="excluded-m0-m5-full-pack", resume=True)
    assert _physical_provider_calls(first) == provider_calls_before_resume
    assert events_path.read_bytes() == event_bytes_before_resume
    public_ref = ArtifactRef(**completion_events[0]["development_public_evaluation_ref"])
    public_blob = store.root / "blobs" / public_ref.sha256[:2] / public_ref.sha256
    public_blob.write_bytes(b"{}\n")
    with pytest.raises(ArtifactIntegrityError, match="artifact size mismatch"):
        reconcile_development_episode_outcome(
            store,
            public_evaluation_ref=public_ref,
            trajectory_ref=ArtifactRef(
                **completion_events[0]["canonical_trajectory_ref"]
            ),
        )


def test_assemble_excluded_run_full_pack_rejects_missing_method_artifacts() -> None:
    root = _new_test_root()
    store = ArtifactStore(root / "store")
    ready = evaluate_requirement_boundary(
        ProjectRequest(
            "counter",
            8,
            "counter8",
            "Build an 8-bit synchronous counter with active-low reset.",
        ),
        _platform(),
    )
    context = freeze_ready_requirement_context(ready, _platform())
    projection = context.public_projection_sha256
    events = _excluded_completion_events(store, context, projection)
    del events[3]["method_artifacts"]
    events_path = root / "events.jsonl"
    events_path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    _, scenarios = _minimal_smoke_inputs(projection)

    with pytest.raises(FullPackReconciliationError, match="M3 method artifacts are missing"):
        assemble_excluded_run_full_pack(
            store,
            events_path=events_path,
            smoke_id="assembled-negative",
            scenarios=scenarios,
        )


def test_assemble_excluded_run_full_pack_rejects_false_skeleton_identity() -> None:
    root = _new_test_root()
    store = ArtifactStore(root / "store")
    ready = evaluate_requirement_boundary(
        ProjectRequest(
            "counter",
            8,
            "counter8",
            "Build an 8-bit synchronous counter with active-low reset.",
        ),
        _platform(),
    )
    context = freeze_ready_requirement_context(ready, _platform())
    projection = context.public_projection_sha256
    events = _excluded_completion_events(store, context, projection)
    events[5]["method_artifacts"]["skeleton_project_sha256"] = "0" * 64
    events_path = root / "events.jsonl"
    events_path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    _, scenarios = _minimal_smoke_inputs(projection)

    with pytest.raises(
        FullPackReconciliationError,
        match="M5 deterministic skeleton artifact mismatch",
    ):
        assemble_excluded_run_full_pack(
            store,
            events_path=events_path,
            smoke_id="assembled-skeleton-negative",
            scenarios=scenarios,
        )
