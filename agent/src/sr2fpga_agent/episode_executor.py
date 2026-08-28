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
    ProjectOutputRepairCapable,
    ProjectOutputNoProgressFailure,
    ProjectCandidateEmission,
    RepairableProjectOutputFailure,
    RepairController,
    SharedArtifactRefs,
)


class PreCandidateState(str, Enum):
    METHOD_PREPARED = "method_prepared"
    PLANNING_ARTIFACT_EMITTED = "planning_artifact_emitted"
    H_VALIDATED = "h_validated"
    HIS_CORRECTION_REQUESTED = "his_correction_requested"
    PROJECT_OUTPUT_REJECTED = "project_output_rejected"
    PROJECT_OUTPUT_REPAIR_REQUESTED = "project_output_repair_requested"
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
    project_output_repairs_used: int


class EpisodeExecutor:
    """Run only method preparation through complete candidate emission.

    Public evaluation, project repair, terminal selection, hidden evaluation,
    and L4 remain later execution phases.
    """

    def __init__(
        self,
        *,
        max_his_corrections: int = 0,
        max_project_output_repairs: int = 0,
        max_shared_pre_candidate_repairs: int | None = None,
    ) -> None:
        if max_his_corrections < 0:
            raise ValueError("max_his_corrections must be non-negative")
        if max_project_output_repairs < 0:
            raise ValueError("max_project_output_repairs must be non-negative")
        if (
            max_shared_pre_candidate_repairs is not None
            and max_shared_pre_candidate_repairs < 0
        ):
            raise ValueError("max_shared_pre_candidate_repairs must be non-negative")
        self.max_his_corrections = max_his_corrections
        self.max_project_output_repairs = max_project_output_repairs
        self.max_shared_pre_candidate_repairs = max_shared_pre_candidate_repairs
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
                states[-1], tuple(states), emission, None, None, None, 0, 0
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
        output_repairs=0,
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
        while isinstance(emission, RepairableProjectOutputFailure):
            self._transition(
                states,
                services,
                adapter,
                PreCandidateState.PROJECT_OUTPUT_REJECTED,
                failure_stage=emission.stage,
                error_type=emission.error_type,
                message=emission.message,
                invalid_output_artifact_sha256=emission.invalid_output_ref.sha256,
                planning_artifact_sha256=emission.planning_artifact_sha256,
                skeleton_project_sha256=emission.skeleton_project_sha256,
            )
            unavailable_reason = self._project_output_repair_unavailable_reason(
                adapter,
                corrections=corrections,
                output_repairs=output_repairs,
            )
            if unavailable_reason is not None:
                failure = MethodStageFailure(
                    "his2project_output_repair",
                    "RepairBudgetUnavailable",
                    f"{unavailable_reason}; rejected output: {emission.message}",
                )
                return self._failed(
                    states,
                    services,
                    adapter,
                    failure,
                    planning,
                    h_report,
                    corrections,
                    output_repairs,
                )
            self._transition(
                states,
                services,
                adapter,
                PreCandidateState.PROJECT_OUTPUT_REPAIR_REQUESTED,
                repair_attempt=output_repairs + 1,
                invalid_output_artifact_sha256=emission.invalid_output_ref.sha256,
                planning_artifact_sha256=emission.planning_artifact_sha256,
                skeleton_project_sha256=emission.skeleton_project_sha256,
            )
            output_repairs += 1
            try:
                repaired = adapter.repair_project_output(
                    context,
                    planning,
                emission,
                services,
                attempt=output_repairs,
            )
            except Exception as exc:
                repaired = MethodStageFailure(
                    "his2project_output_repair",
                    type(exc).__name__,
                    str(exc),
                )
            if isinstance(repaired, MethodStageFailure) and not isinstance(
                repaired,
                RepairableProjectOutputFailure,
            ):
                return self._failed(
                    states,
                    services,
                    adapter,
                    repaired,
                    planning,
                    h_report,
                    corrections,
                    output_repairs,
                )
            emission = repaired
        if isinstance(emission, MethodStageFailure):
            return self._failed(
                states,
                services,
                adapter,
                emission,
                planning,
                h_report,
                corrections,
                output_repairs,
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
            states[-1],
            tuple(states),
            emission,
            planning,
            h_report,
            None,
            corrections,
            output_repairs,
        )

    def _project_output_repair_unavailable_reason(
        self,
        adapter,
        *,
        corrections: int,
        output_repairs: int,
    ) -> str | None:
        if not isinstance(adapter, ProjectOutputRepairCapable):
            return "method adapter does not support HIS2PROJECT output repair"
        if output_repairs >= self.max_project_output_repairs:
            return "HIS2PROJECT output repair budget exhausted"
        if (
            self.max_shared_pre_candidate_repairs is not None
            and corrections + output_repairs >= self.max_shared_pre_candidate_repairs
        ):
            return "shared pre-candidate repair budget exhausted"
        return None

    def _failed(
        self,
        states,
        services,
        adapter,
        failure,
        planning,
        h_report,
        corrections,
        output_repairs=0,
    ) -> PreCandidateOutcome:
        extra = {}
        if isinstance(failure, RepairableProjectOutputFailure):
            extra = {
                "invalid_output_artifact_sha256": failure.invalid_output_ref.sha256,
                "planning_artifact_sha256": failure.planning_artifact_sha256,
                "skeleton_project_sha256": failure.skeleton_project_sha256,
            }
        elif isinstance(failure, ProjectOutputNoProgressFailure):
            extra = {
                "parent_output_artifact_ref": failure.parent_output_ref.to_dict(),
                "produced_output_artifact_ref": failure.produced_output_ref.to_dict(),
                "planning_artifact_sha256": failure.planning_artifact_sha256,
                "skeleton_project_sha256": failure.skeleton_project_sha256,
            }
        self._transition(
            states,
            services,
            adapter,
            PreCandidateState.NO_COMPLETE_CANDIDATE,
            failure_stage=failure.stage,
            error_type=failure.error_type,
            message=failure.message,
            **extra,
        )
        return PreCandidateOutcome(
            states[-1],
            tuple(states),
            None,
            planning,
            h_report,
            failure,
            corrections,
            output_repairs,
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
                PreCandidateState.PROJECT_OUTPUT_REJECTED,
                PreCandidateState.CANDIDATE_EMITTED,
                PreCandidateState.NO_COMPLETE_CANDIDATE,
            },
            PreCandidateState.HIS_CORRECTION_REQUESTED: {
                PreCandidateState.PLANNING_ARTIFACT_EMITTED,
                PreCandidateState.NO_COMPLETE_CANDIDATE,
            },
            PreCandidateState.PROJECT_OUTPUT_REJECTED: {
                PreCandidateState.PROJECT_OUTPUT_REPAIR_REQUESTED,
                PreCandidateState.NO_COMPLETE_CANDIDATE,
            },
            PreCandidateState.PROJECT_OUTPUT_REPAIR_REQUESTED: {
                PreCandidateState.PROJECT_OUTPUT_REJECTED,
                PreCandidateState.CANDIDATE_EMITTED,
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
