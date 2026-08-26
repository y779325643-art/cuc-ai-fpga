"""Explicit pre-candidate execution state machine for Paper-1 methods."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from sr2fpga_agent.frozen_context import FrozenRequirementContext
from sr2fpga_agent.method_adapters import (
    GenerationServices,
    MethodAdapter,
    MethodStageFailure,
    PlanningArtifactEmission,
    PlanningArtifactKind,
    ProjectCandidateEmission,
    RepairController,
    SharedArtifactRefs,
)


class PreCandidateState(str, Enum):
    METHOD_PREPARED = "method_prepared"
    PLANNING_ARTIFACT_EMITTED = "planning_artifact_emitted"
    H_VALIDATED = "h_validated"
    HIS_CORRECTION_REQUESTED = "his_correction_requested"
    CANDIDATE_EMITTED = "candidate_emitted"
    NO_COMPLETE_CANDIDATE = "no_complete_candidate"


@dataclass(frozen=True)
class PreCandidateOutcome:
    final_state: PreCandidateState
    state_trace: tuple[PreCandidateState, ...]
    candidate: ProjectCandidateEmission | None
    planning_artifact: PlanningArtifactEmission | None
    h_report: Mapping[str, Any] | None
    failure: MethodStageFailure | None
    his_corrections_used: int


class EpisodeExecutor:
    """Run only method preparation through complete candidate emission.

    Public evaluation, project repair, terminal selection, hidden evaluation,
    and L4 remain later execution phases.
    """

    def __init__(self, *, max_his_corrections: int = 0) -> None:
        if max_his_corrections < 0:
            raise ValueError("max_his_corrections must be non-negative")
        self.max_his_corrections = max_his_corrections
        self._repair = RepairController()

    def emit_candidate(
        self,
        adapter: MethodAdapter,
        context: FrozenRequirementContext,
        services: GenerationServices,
        shared_artifacts: SharedArtifactRefs = SharedArtifactRefs(),
    ) -> PreCandidateOutcome:
        states: list[PreCandidateState] = []
        self._transition(states, services, adapter, PreCandidateState.METHOD_PREPARED)
        emission = adapter.emit_initial(context, services, shared_artifacts)
        if isinstance(emission, MethodStageFailure):
            return self._failed(states, services, adapter, emission, None, None, 0)
        if isinstance(emission, ProjectCandidateEmission):
            self._transition(
                states,
                services,
                adapter,
                PreCandidateState.CANDIDATE_EMITTED,
                artifact_sha256=emission.artifact_ref.sha256,
                project_package_sha256=emission.project_package_sha256,
            )
            return PreCandidateOutcome(
                states[-1], tuple(states), emission, None, None, None, 0
            )

        planning = emission
        self._transition(
            states,
            services,
            adapter,
            PreCandidateState.PLANNING_ARTIFACT_EMITTED,
            planning_kind=planning.kind.value,
            artifact_sha256=planning.artifact_ref.sha256,
        )
        if planning.kind is PlanningArtifactKind.UNTYPED_PLAN:
            if adapter.contract.emits_system_his:
                failure = MethodStageFailure(
                    "planning_representation",
                    "RepresentationMismatch",
                    "System-HIS method emitted an untyped plan",
                )
                return self._failed(states, services, adapter, failure, planning, None, 0)
            return self._lower(adapter, context, services, shared_artifacts, planning, states, None, 0)

        if not adapter.contract.emits_system_his:
            failure = MethodStageFailure(
                "planning_representation",
                "RepresentationMismatch",
                "non-HIS method emitted System-HIS",
            )
            return self._failed(states, services, adapter, failure, planning, None, 0)
        if services.his_validation is None:
            failure = MethodStageFailure(
                "h_validation", "UnavailableCapability", "missing H validation facade"
            )
            return self._failed(states, services, adapter, failure, planning, None, 0)

        corrections = 0
        h_report: Mapping[str, Any] | None = None
        while True:
            payload = services.artifacts.read_planning(planning)
            try:
                h_report = services.his_validation.validate_his(context, payload)
            except Exception as exc:
                failure = MethodStageFailure("h_validation", type(exc).__name__, str(exc))
                return self._failed(
                    states, services, adapter, failure, planning, h_report, corrections
                )
            if not isinstance(h_report, Mapping) or not isinstance(h_report.get("passed"), bool):
                failure = MethodStageFailure(
                    "h_validation",
                    "InvalidValidationReport",
                    "H validation facade returned no boolean passed field",
                )
                return self._failed(
                    states, services, adapter, failure, planning, h_report, corrections
                )
            failed_stage, diagnostics = _failed_h_details(h_report)
            self._transition(
                states,
                services,
                adapter,
                PreCandidateState.H_VALIDATED,
                passed=h_report["passed"],
                failed_h_stage=failed_stage,
            )
            if h_report["passed"]:
                return self._lower(
                    adapter,
                    context,
                    services,
                    shared_artifacts,
                    planning,
                    states,
                    h_report,
                    corrections,
                )
            if (
                not adapter.contract.allows_his_correction
                or corrections >= self.max_his_corrections
            ):
                reason = (
                    "method contract does not allow System-HIS correction"
                    if not adapter.contract.allows_his_correction
                    else "System-HIS correction budget exhausted"
                )
                failure = MethodStageFailure(failed_stage or "h_validation", "HValidationFailed", reason)
                return self._failed(
                    states, services, adapter, failure, planning, h_report, corrections
                )
            self._transition(
                states,
                services,
                adapter,
                PreCandidateState.HIS_CORRECTION_REQUESTED,
                failed_h_stage=failed_stage,
                input_artifact_sha256=planning.artifact_ref.sha256,
            )
            parent_planning_sha256 = planning.artifact_ref.sha256
            diagnosis = {
                "failed_h_stage": failed_stage,
                "diagnostics": diagnostics,
                "h_report": dict(h_report),
            }
            try:
                planning = self._repair.correct_his(
                    adapter, context, planning, diagnosis, services
                )
            except Exception as exc:
                failure = MethodStageFailure("his_correction", type(exc).__name__, str(exc))
                return self._failed(
                    states, services, adapter, failure, planning, h_report, corrections
                )
            corrections += 1
            self._transition(
                states,
                services,
                adapter,
                PreCandidateState.PLANNING_ARTIFACT_EMITTED,
                planning_kind=planning.kind.value,
                artifact_sha256=planning.artifact_ref.sha256,
                correction_attempt=corrections,
                parent_artifact_sha256=parent_planning_sha256,
            )

    def _lower(
        self,
        adapter,
        context,
        services,
        shared_artifacts,
        planning,
        states,
        h_report,
        corrections,
    ) -> PreCandidateOutcome:
        lower = getattr(adapter, "emit_project_from_validated_planning", None)
        if not callable(lower):
            failure = MethodStageFailure(
                "project_emission",
                "UnavailableCapability",
                "planning adapter cannot emit a project",
            )
            return self._failed(
                states, services, adapter, failure, planning, h_report, corrections
            )
        emission = lower(context, planning, services, shared_artifacts)
        if isinstance(emission, MethodStageFailure):
            return self._failed(
                states, services, adapter, emission, planning, h_report, corrections
            )
        self._transition(
            states,
            services,
            adapter,
            PreCandidateState.CANDIDATE_EMITTED,
            artifact_sha256=emission.artifact_ref.sha256,
            project_package_sha256=emission.project_package_sha256,
        )
        return PreCandidateOutcome(
            states[-1], tuple(states), emission, planning, h_report, None, corrections
        )

    def _failed(
        self,
        states,
        services,
        adapter,
        failure,
        planning,
        h_report,
        corrections,
    ) -> PreCandidateOutcome:
        self._transition(
            states,
            services,
            adapter,
            PreCandidateState.NO_COMPLETE_CANDIDATE,
            failure_stage=failure.stage,
            error_type=failure.error_type,
            message=failure.message,
        )
        return PreCandidateOutcome(
            states[-1], tuple(states), None, planning, h_report, failure, corrections
        )

    @staticmethod
    def _transition(states, services, adapter, state, **payload) -> None:
        previous = states[-1] if states else None
        allowed = {
            None: {PreCandidateState.METHOD_PREPARED},
            PreCandidateState.METHOD_PREPARED: {
                PreCandidateState.PLANNING_ARTIFACT_EMITTED,
                PreCandidateState.CANDIDATE_EMITTED,
                PreCandidateState.NO_COMPLETE_CANDIDATE,
            },
            PreCandidateState.PLANNING_ARTIFACT_EMITTED: {
                PreCandidateState.H_VALIDATED,
                PreCandidateState.CANDIDATE_EMITTED,
                PreCandidateState.NO_COMPLETE_CANDIDATE,
            },
            PreCandidateState.H_VALIDATED: {
                PreCandidateState.HIS_CORRECTION_REQUESTED,
                PreCandidateState.CANDIDATE_EMITTED,
                PreCandidateState.NO_COMPLETE_CANDIDATE,
            },
            PreCandidateState.HIS_CORRECTION_REQUESTED: {
                PreCandidateState.PLANNING_ARTIFACT_EMITTED,
                PreCandidateState.NO_COMPLETE_CANDIDATE,
            },
            PreCandidateState.CANDIDATE_EMITTED: set(),
            PreCandidateState.NO_COMPLETE_CANDIDATE: set(),
        }
        if state not in allowed[previous]:
            prior = previous.value if previous is not None else "start"
            raise RuntimeError(f"illegal pre-candidate transition: {prior} -> {state.value}")
        states.append(state)
        services.artifacts.append_event(
            services.episode_id,
            "episode_state_transition",
            {
                "state": state.value,
                "method_condition_id": adapter.contract.method_condition.value,
                **payload,
            },
        )


def _failed_h_details(report: Mapping[str, Any]) -> tuple[str | None, list[str]]:
    for stage in ("h0", "h1", "h2", "h3"):
        stage_report = report.get(stage)
        if isinstance(stage_report, Mapping) and stage_report.get("status") == "fail":
            diagnostics = stage_report.get("diagnostics", [])
            return stage, [str(item) for item in diagnostics] if isinstance(diagnostics, list) else []
    return None, []
