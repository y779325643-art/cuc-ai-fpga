"""Requirement-to-System-HIS generation."""

from __future__ import annotations

from typing import Any, Callable

from sr2fpga_agent.family_recipe import FamilyRecipeDecision, select_family_recipe
from sr2fpga_agent.his_validation import SystemHisValidationError, validate_system_his_candidate
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.model_budget import client_for_stage, record_parser_schema_retry
from sr2fpga_agent.prompts import _system_his_v12_messages
from sr2fpga_agent.providers import OpenAICompatibleClient
from sr2fpga_agent.repair import SystemHisRepairer
from sr2fpga_agent.requirement_boundary import (
    evaluate_requirement_boundary,
    requirement_capability_gaps,
)
from sr2fpga_agent.requirement_envelope import (
    RequirementEnvelope,
    RequirementRouteResult,
)
from sr2fpga_agent.system_his_capabilities import (
    SystemHisBackendCapabilities,
)


class RequirementClarificationRequired(ValueError):
    """A requirement has semantic choices that must be resolved first."""

    def __init__(
        self,
        envelope: RequirementEnvelope,
        ambiguity_keys: tuple[str, ...],
    ) -> None:
        selected = tuple(
            item for item in envelope.critical_ambiguities if item.key in ambiguity_keys
        )[:3]
        self.requirement_id = envelope.requirement_id
        self.ambiguity_keys = tuple(item.key for item in selected)
        self.questions = tuple(item.question for item in selected)
        numbered = "\n".join(
            f"{index}. {question}" for index, question in enumerate(self.questions, start=1)
        )
        super().__init__(
            "requirement_clarification_required: resolve these questions before model generation"
            + (f"\n{numbered}" if numbered else "")
        )


class RequirementCapabilityGapError(ValueError):
    """A requirement needs a backend adapter absent from the registry."""

    def __init__(self, requirement_id: str, gaps: tuple[str, ...]) -> None:
        self.requirement_id = requirement_id
        self.capability_gaps = gaps
        super().__init__(
            "capability_gap/needs_adapter: current generic System-HIS lowerer cannot preserve "
            + ", ".join(gaps)
        )


class SystemHisGenerator:
    """Generate a System-HIS v1.2 architecture contract from a short request."""

    def __init__(
        self,
        client: OpenAICompatibleClient,
        max_attempts: int = 1,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.client = client
        self.max_attempts = max_attempts
        self.event_sink = event_sink
        # H-stage correction is a separate declared model stage.  Keeping its
        # budget label distinct from the first REQ2HIS emission makes stage
        # allocation and failed repair calls auditable.
        self.repairer = SystemHisRepairer(client_for_stage(client, "system_his_repair"))

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> dict[str, Any]:
        requirement_envelope, requirement_route, family_recipe_decision = _prepare_requirement(
            request,
            platform,
        )
        messages = _system_his_v12_messages(
            request,
            platform,
            requirement_envelope=requirement_envelope,
            requirement_route=requirement_route,
            family_recipe_decision=family_recipe_decision,
        )
        if self.max_attempts < 1:
            raise RuntimeError("System-HIS generator did not run")
        content = self.client.stream_chat(messages)
        try:
            return validate_system_his_candidate(request, content, platform=platform)
        except SystemHisValidationError as exc:
            last_error = exc

        for attempt_id in range(self.max_attempts - 1):
            record_parser_schema_retry(self.client, "validate_system_his_candidate")
            self._emit_retry_event(request, attempt_id, last_error)
            try:
                return self.repairer.repair(
                    request,
                    platform,
                    last_error.candidate_output,
                    last_error.report,
                    requirement_envelope=requirement_envelope,
                    requirement_route=requirement_route,
                    family_recipe_decision=family_recipe_decision,
                )
            except SystemHisValidationError as exc:
                last_error = exc
        raise last_error

    def _emit_retry_event(
        self,
        request: ProjectRequest,
        attempt_id: int,
        exc: SystemHisValidationError,
    ) -> None:
        if self.event_sink is None:
            return
        self.event_sink(
            {
                "event": "generation_stage_retry",
                "stage": "req2his",
                "attempt_id": attempt_id,
                "next_attempt_id": attempt_id + 1,
                "repair_layer": "system_his",
                "failed_h_stage": exc.failed_h_stage,
                "diagnostics": exc.diagnostics,
                "project_name": request.project_name,
                "task_type": request.task_type,
                "width": request.width,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )


def _prepare_requirement(
    request: ProjectRequest,
    platform: PlatformProfile,
) -> tuple[RequirementEnvelope, RequirementRouteResult, FamilyRecipeDecision]:
    boundary = evaluate_requirement_boundary(request, platform)
    if boundary.disposition == "needs_clarification":
        raise RequirementClarificationRequired(
            boundary.envelope,
            boundary.clarification_fact_ids,
        )
    if boundary.disposition == "capability_gap":
        raise RequirementCapabilityGapError(
            boundary.requirement_id,
            boundary.capability_gap_ids,
        )
    # Recipe is a generation-information privilege. It is deliberately selected
    # only after the shared method-neutral boundary has returned ready.
    family_recipe_decision = select_family_recipe(request, boundary.envelope)
    return boundary.envelope, boundary.route, family_recipe_decision


def _requirement_capability_gaps(
    envelope: RequirementEnvelope,
    backend: SystemHisBackendCapabilities,
) -> tuple[str, ...]:
    return requirement_capability_gaps(envelope, backend)
