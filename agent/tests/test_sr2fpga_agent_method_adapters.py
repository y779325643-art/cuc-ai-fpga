import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.episode_executor import EpisodeExecutor, PreCandidateState
from sr2fpga_agent.frozen_context import freeze_ready_requirement_context
from sr2fpga_agent.method_adapters import (
    GenerationServices,
    HisMethodAdapter,
    MethodAdapterRegistry,
    MethodArtifactGateway,
    MethodStageFailure,
    PairedArtifactCoordinator,
    PairingKey,
    PlanningArtifactEmission,
    PlanningArtifactKind,
    ProjectCandidateEmission,
    RepairController,
    SharedArtifactRefs,
    StructuredDirectMethodAdapter,
)
from sr2fpga_agent.method_contract import MethodConditionId
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary


def _platform() -> PlatformProfile:
    return PlatformProfile("generic_verilog", "generic", "open_source")


def _context():
    request = ProjectRequest(
        "counter",
        8,
        "counter8",
        "Build an 8-bit synchronous counter with active-low reset.",
    )
    return freeze_ready_requirement_context(
        evaluate_requirement_boundary(request, _platform()),
        _platform(),
    )


def _project(tag: str = "initial") -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "counter8",
        "top": {
            "module": "top",
            "source": "rtl/design.v",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {"path": "rtl/design.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [],
        "build": {"toolchain_id": "open_source", "language_standard": "verilog-2005"},
    }
    return GeneratedProject(
        "counter8",
        {
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "rtl/design.v": f"// {tag}\nmodule top(input clk, output [7:0] count); endmodule\n",
        },
    )


class _DirectFacade:
    def __init__(self) -> None:
        self.calls = 0
        self.projections: list[str] = []

    def emit_project(self, context):
        self.calls += 1
        self.projections.append(context.public_projection_sha256)
        return _project()


class _UntypedFacade:
    def __init__(self) -> None:
        self.plan_calls = 0
        self.project_calls = 0

    def emit_plan(self, context):
        self.plan_calls += 1
        return {"steps": ["counter state", "registered output"]}

    def emit_project(self, context, plan):
        self.project_calls += 1
        assert plan["steps"]
        return _project("m2")


class _HisFacade:
    def __init__(self) -> None:
        self.his_calls = 0
        self.free_calls = 0
        self.skeleton_calls = 0

    def emit_his(self, context):
        self.his_calls += 1
        return {"schema_version": "system-his-v1.2", "intent": {"design_goal": "counter"}}

    def emit_free_project(self, context, system_his):
        self.free_calls += 1
        return _project("m3-free")

    def emit_skeleton_project(self, context, system_his):
        self.skeleton_calls += 1
        return _project("m4-skeleton")


class _RepairFacade:
    def __init__(self) -> None:
        self.his_calls = 0
        self.project_calls = 0

    def correct_his(self, context, system_his, diagnosis):
        self.his_calls += 1
        return {**system_his, "corrected": True}

    def repair_project(self, context, project, diagnosis):
        self.project_calls += 1
        return _project("repaired")


class _ValidationFacade:
    def __init__(self, reports) -> None:
        self.reports = list(reports)
        self.calls = 0
        self.payloads = []

    def validate_his(self, context, system_his):
        self.payloads.append(dict(system_his))
        report = self.reports[min(self.calls, len(self.reports) - 1)]
        self.calls += 1
        return report


def _services(
    tmp_path, *, direct=None, untyped=None, his=None, validation=None, repair=None
):
    store = ArtifactStore(tmp_path / "store")
    return store, GenerationServices(
        artifacts=MethodArtifactGateway(store),
        episode_id="episode-001",
        direct=direct,
        untyped=untyped,
        system_his=his,
        his_validation=validation,
        repair=repair,
    )


def _pairing(context) -> PairingKey:
    return PairingKey(
        paired_block_id="pair-001",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="semantic-counter-001",
        decoding_seed=17,
        model_provenance_sha256="a" * 64,
    )


def test_m0_m1_consume_one_shared_initial_project(tmp_path) -> None:
    context = _context()
    direct = _DirectFacade()
    store, services = _services(tmp_path, direct=direct)
    coordinator = PairedArtifactCoordinator(store)
    shared_project = coordinator.materialize_initial_project(
        _pairing(context), lambda: direct.emit_project(context)
    )
    shared = SharedArtifactRefs(initial_project=shared_project)

    m0 = MethodAdapterRegistry().create("M0").emit_initial(context, services, shared)
    m1 = MethodAdapterRegistry().create("M1").emit_initial(context, services, shared)
    coordinator.materialize_initial_project(_pairing(context), lambda: direct.emit_project(context))

    assert isinstance(m0, ProjectCandidateEmission)
    assert isinstance(m1, ProjectCandidateEmission)
    assert m0.artifact_ref.sha256 == m1.artifact_ref.sha256
    assert m0.project_package_sha256 == m1.project_package_sha256
    assert direct.calls == 1
    assert direct.projections == [context.public_projection_sha256]


def test_m2_emits_untyped_plan_and_never_uses_his_or_skeleton(tmp_path) -> None:
    context = _context()
    untyped = _UntypedFacade()
    his = _HisFacade()
    _, services = _services(tmp_path, untyped=untyped, his=his)
    adapter = MethodAdapterRegistry().create("M2")

    planning = adapter.emit_initial(context, services, SharedArtifactRefs())
    candidate = adapter.emit_project_from_validated_planning(
        context, planning, services, SharedArtifactRefs()
    )

    assert isinstance(adapter, StructuredDirectMethodAdapter)
    assert isinstance(planning, PlanningArtifactEmission)
    assert planning.kind is PlanningArtifactKind.UNTYPED_PLAN
    assert isinstance(candidate, ProjectCandidateEmission)
    assert (untyped.plan_calls, untyped.project_calls) == (1, 1)
    assert (his.his_calls, his.free_calls, his.skeleton_calls) == (0, 0, 0)


def test_m3_m4_share_his_but_select_free_vs_skeleton_project(tmp_path) -> None:
    context = _context()
    his = _HisFacade()
    store, services = _services(tmp_path, his=his)
    coordinator = PairedArtifactCoordinator(store)
    shared_his = coordinator.materialize_system_his(
        _pairing(context), lambda: his.emit_his(context)
    )
    shared = SharedArtifactRefs(system_his=shared_his)
    m3 = MethodAdapterRegistry().create("M3")
    m4 = MethodAdapterRegistry().create("M4")

    m3_plan = m3.emit_initial(context, services, shared)
    m4_plan = m4.emit_initial(context, services, shared)
    m3_project = m3.emit_project_from_validated_planning(context, m3_plan, services, shared)
    m4_project = m4.emit_project_from_validated_planning(context, m4_plan, services, shared)

    assert isinstance(m3, HisMethodAdapter) and isinstance(m4, HisMethodAdapter)
    assert m3_plan.artifact_ref.sha256 == m4_plan.artifact_ref.sha256
    assert isinstance(m3_project, ProjectCandidateEmission)
    assert isinstance(m4_project, ProjectCandidateEmission)
    assert his.his_calls == 1
    assert his.free_calls == 1
    assert his.skeleton_calls == 1


def test_m4_m5_can_consume_one_shared_skeleton_project(tmp_path) -> None:
    context = _context()
    his = _HisFacade()
    store, services = _services(tmp_path, his=his)
    coordinator = PairedArtifactCoordinator(store)
    shared_his = coordinator.materialize_system_his(_pairing(context), lambda: his.emit_his(context))
    shared_project = coordinator.materialize_initial_project(
        _pairing(context), lambda: his.emit_skeleton_project(context, {"shared": True})
    )
    shared = SharedArtifactRefs(initial_project=shared_project, system_his=shared_his)

    outputs = []
    for method in ("M4", "M5"):
        adapter = MethodAdapterRegistry().create(method)
        planning = adapter.emit_initial(context, services, shared)
        outputs.append(
            adapter.emit_project_from_validated_planning(context, planning, services, shared)
        )

    assert outputs[0].artifact_ref.sha256 == outputs[1].artifact_ref.sha256
    assert outputs[0].project_package_sha256 == outputs[1].project_package_sha256
    assert his.skeleton_calls == 1


@pytest.mark.parametrize("method", ["M0", "M2", "M3", "M4"])
def test_repair_controller_rejects_methods_without_project_repair_privilege(
    tmp_path, method
) -> None:
    context = _context()
    repair = _RepairFacade()
    store, services = _services(tmp_path, repair=repair)
    candidate = services.artifacts.put_project("candidate/input", _project())
    adapter = MethodAdapterRegistry().create(method)

    with pytest.raises(PermissionError, match="does not allow project repair"):
        RepairController().repair_project(adapter, context, candidate, {}, services)

    assert repair.project_calls == 0


def test_only_m5_can_correct_his_and_m1_m5_can_repair_project(tmp_path) -> None:
    context = _context()
    repair = _RepairFacade()
    _, services = _services(tmp_path, repair=repair)
    planning = services.artifacts.put_planning(
        "planning/input", PlanningArtifactKind.SYSTEM_HIS, {"schema_version": "system-his-v1.2"}
    )
    candidate = services.artifacts.put_project("candidate/input", _project())
    controller = RepairController()

    with pytest.raises(PermissionError, match="does not allow System-HIS correction"):
        controller.correct_his(MethodAdapterRegistry().create("M4"), context, planning, {}, services)
    corrected = controller.correct_his(
        MethodAdapterRegistry().create("M5"), context, planning, {}, services
    )
    repaired_m1 = controller.repair_project(
        MethodAdapterRegistry().create("M1"), context, candidate, {}, services
    )
    repaired_m5 = controller.repair_project(
        MethodAdapterRegistry().create("M5"), context, candidate, {}, services
    )

    assert isinstance(corrected, PlanningArtifactEmission)
    assert isinstance(repaired_m1, ProjectCandidateEmission)
    assert isinstance(repaired_m5, ProjectCandidateEmission)
    assert repair.his_calls == 1
    assert repair.project_calls == 2


def test_missing_capability_returns_first_class_stage_failure(tmp_path) -> None:
    context = _context()
    _, services = _services(tmp_path)

    emission = MethodAdapterRegistry().create(MethodConditionId.M2).emit_initial(
        context, services, SharedArtifactRefs()
    )

    assert isinstance(emission, MethodStageFailure)
    assert emission.stage == "untyped_plan"


def _h_report(*, passed: bool, failed_stage: str | None = None):
    report = {"passed": passed}
    for stage in ("h0", "h1", "h2", "h3"):
        report[stage] = {
            "status": "fail" if stage == failed_stage else ("pass" if passed else "not_run"),
            "diagnostics": [f"{stage} failed"] if stage == failed_stage else [],
        }
    return report


@pytest.mark.parametrize("method", ["M3", "M4"])
def test_executor_stops_nonrepair_his_methods_before_project_emission(tmp_path, method) -> None:
    context = _context()
    his = _HisFacade()
    repair = _RepairFacade()
    validation = _ValidationFacade([_h_report(passed=False, failed_stage="h1")])
    _, services = _services(
        tmp_path, his=his, validation=validation, repair=repair
    )

    outcome = EpisodeExecutor(max_his_corrections=2).emit_candidate(
        MethodAdapterRegistry().create(method), context, services
    )

    assert outcome.final_state is PreCandidateState.NO_COMPLETE_CANDIDATE
    assert outcome.candidate is None
    assert outcome.failure.stage == "h1"
    assert outcome.his_corrections_used == 0
    assert validation.calls == 1
    assert (his.free_calls, his.skeleton_calls) == (0, 0)
    assert repair.his_calls == 0


def test_executor_m5_repairs_his_revalidates_all_h_and_only_then_lowers(tmp_path) -> None:
    context = _context()
    his = _HisFacade()
    repair = _RepairFacade()
    validation = _ValidationFacade(
        [_h_report(passed=False, failed_stage="h0"), _h_report(passed=True)]
    )
    _, services = _services(
        tmp_path, his=his, validation=validation, repair=repair
    )

    outcome = EpisodeExecutor(max_his_corrections=1).emit_candidate(
        MethodAdapterRegistry().create("M5"), context, services
    )

    assert outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert isinstance(outcome.candidate, ProjectCandidateEmission)
    assert outcome.his_corrections_used == 1
    assert validation.calls == 2
    assert validation.payloads[1]["corrected"] is True
    assert repair.his_calls == 1
    assert his.skeleton_calls == 1
    assert outcome.state_trace == (
        PreCandidateState.METHOD_PREPARED,
        PreCandidateState.PLANNING_ARTIFACT_EMITTED,
        PreCandidateState.H_VALIDATED,
        PreCandidateState.HIS_CORRECTION_REQUESTED,
        PreCandidateState.PLANNING_ARTIFACT_EMITTED,
        PreCandidateState.H_VALIDATED,
        PreCandidateState.CANDIDATE_EMITTED,
    )


def test_executor_his_correction_budget_exhaustion_is_first_class(tmp_path) -> None:
    context = _context()
    his = _HisFacade()
    repair = _RepairFacade()
    validation = _ValidationFacade([_h_report(passed=False, failed_stage="h2")])
    _, services = _services(
        tmp_path, his=his, validation=validation, repair=repair
    )

    outcome = EpisodeExecutor(max_his_corrections=0).emit_candidate(
        MethodAdapterRegistry().create("M5"), context, services
    )

    assert outcome.final_state is PreCandidateState.NO_COMPLETE_CANDIDATE
    assert outcome.failure.message == "System-HIS correction budget exhausted"
    assert repair.his_calls == 0
    assert his.skeleton_calls == 0


def test_executor_m2_bypasses_h_validation_and_emits_project(tmp_path) -> None:
    context = _context()
    untyped = _UntypedFacade()
    validation = _ValidationFacade([_h_report(passed=False, failed_stage="h0")])
    _, services = _services(tmp_path, untyped=untyped, validation=validation)

    outcome = EpisodeExecutor(max_his_corrections=3).emit_candidate(
        MethodAdapterRegistry().create("M2"), context, services
    )

    assert outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert validation.calls == 0
    assert outcome.h_report is None
    assert outcome.state_trace == (
        PreCandidateState.METHOD_PREPARED,
        PreCandidateState.PLANNING_ARTIFACT_EMITTED,
        PreCandidateState.CANDIDATE_EMITTED,
    )


def test_executor_rejects_illegal_post_terminal_transition(tmp_path) -> None:
    direct = _DirectFacade()
    _, services = _services(tmp_path, direct=direct)
    adapter = MethodAdapterRegistry().create("M0")
    states = [PreCandidateState.METHOD_PREPARED, PreCandidateState.CANDIDATE_EMITTED]

    with pytest.raises(RuntimeError, match="illegal pre-candidate transition"):
        EpisodeExecutor._transition(
            states, services, adapter, PreCandidateState.NO_COMPLETE_CANDIDATE
        )
