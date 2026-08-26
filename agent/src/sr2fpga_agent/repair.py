"""LLM-backed generated-project repair."""

from __future__ import annotations

from typing import Any

from sr2fpga_agent.family_recipe import (
    FamilyRecipeDecision,
    recipe_task_type,
    select_family_recipe,
)
from sr2fpga_agent.his_validation import (
    first_failed_h_stage,
    validate_system_his_candidate,
)
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest, RepairResult
from sr2fpga_agent.model_budget import record_parser_schema_retry
from sr2fpga_agent.parsers import (
    _diagnosis_mentions_path,
    _manifest_policy_for_project,
    _minimize_repaired_project,
    _project_system_his_schema,
    _project_task_type,
    _validate_repair_preserves_l0_when_not_repairing_l0,
    _validate_system_his_contract_unchanged,
    diff_projects,
    parse_project_files,
    parse_system_his_v12,
)
from sr2fpga_agent.path_safety import build_patch_metadata
from sr2fpga_agent.prompts import (
    _repair_messages,
    _system_his_v12_messages,
    _with_system_his_retry_feedback,
)
from sr2fpga_agent.providers import OpenAICompatibleClient
from sr2fpga_agent.requirement_envelope import (
    RequirementEnvelope,
    RequirementRouteResult,
    build_request_requirement_envelope,
    route_requirement,
)
from sr2fpga_agent.system_his_v12_checker import SCHEMA_VERSION as SYSTEM_HIS_V12_SCHEMA
from sr2fpga_agent.task_catalog import load_exact_task_family_aliases

class SystemHisRepairer:
    """Make one model call to repair a System-HIS candidate that failed H0-H3."""

    def __init__(self, client: OpenAICompatibleClient) -> None:
        self.client = client

    def repair(
        self,
        request: ProjectRequest,
        platform: PlatformProfile,
        candidate_output: str,
        validation_report: dict[str, Any],
        *,
        requirement_envelope: RequirementEnvelope | None = None,
        requirement_route: RequirementRouteResult | None = None,
        family_recipe_decision: FamilyRecipeDecision | None = None,
    ) -> dict[str, Any]:
        if requirement_envelope is None and requirement_route is None:
            requirement_envelope = build_request_requirement_envelope(request, platform)
            if family_recipe_decision is None:
                family_recipe_decision = select_family_recipe(request, requirement_envelope)
            route_family = (
                family_recipe_decision.family_id
                if family_recipe_decision.status == "applied"
                else request.task_type
            )
            requirement_route = route_requirement(
                requirement_envelope,
                declared_family=route_family,
                exact_family_aliases=load_exact_task_family_aliases(),
            )
        elif requirement_envelope is None or requirement_route is None:
            raise ValueError(
                "System-HIS repair requires both requirement_envelope and requirement_route"
            )
        if family_recipe_decision is None:
            family_recipe_decision = select_family_recipe(request, requirement_envelope)
        failed_stage = first_failed_h_stage(validation_report) or "h0"
        stage_report = validation_report.get(failed_stage, {})
        diagnostics = list(stage_report.get("diagnostics", [])) if isinstance(stage_report, dict) else []
        error_prefix = (
            "REQ2HIS fidelity failed"
            if failed_stage == "h3"
            else f"{failed_stage.upper()} validation failed"
        )
        error = error_prefix + ": " + ("; ".join(diagnostics) or "unknown validation error")
        messages = _with_system_his_retry_feedback(
            _system_his_v12_messages(
                request,
                platform,
                requirement_envelope=requirement_envelope,
                requirement_route=requirement_route,
                family_recipe_decision=family_recipe_decision,
            ),
            error,
            candidate_output,
            task_type=request.task_type,
            family_recipe_task_type=recipe_task_type(family_recipe_decision),
            requirement_trace_template=requirement_envelope.requirement_trace_template(),
        )
        repaired_output = self.client.stream_chat(messages)
        return validate_system_his_candidate(
            request,
            repaired_output,
            platform=platform,
        )


class ProjectRepairer:
    """Repair a generated project package using a model and tool diagnosis."""

    def __init__(self, client: OpenAICompatibleClient, max_attempts: int = 1) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def repair(self, project: GeneratedProject, diagnosis: dict[str, object]) -> RepairResult:
        messages = _repair_messages(project, diagnosis)
        manifest_policy = _manifest_policy_for_project(project.files)
        last_error: ValueError | None = None
        for _attempt in range(self.max_attempts):
            content = self.client.chat(messages)
            try:
                files = parse_project_files(
                    content,
                    expected_task_type=_project_task_type(project.files),
                    manifest_policy=manifest_policy,
                )
                if _project_system_his_schema(project.files) == SYSTEM_HIS_V12_SCHEMA:
                    if "system_his.json" not in files:
                        raise ValueError(
                            "Project repair omitted required system_his.json for a System-HIS method"
                        )
                    original_system_his: dict[str, Any] | None = None
                    try:
                        original_system_his = parse_system_his_v12(project.files["system_his.json"])
                    except ValueError:
                        original_system_his = None
                    try:
                        repaired_system_his = parse_system_his_v12(files["system_his.json"])
                    except ValueError as exc:
                        raise ValueError(f"Project repair system_his.json failed validation: {exc}") from exc
                    if original_system_his is not None and not _diagnosis_mentions_path(diagnosis, "system_his.json"):
                        try:
                            _validate_system_his_contract_unchanged(original_system_his, repaired_system_his)
                        except ValueError as exc:
                            raise ValueError(f"System-HIS v1.2 contract changed during RTL repair: {exc}") from exc
                repaired_project = _minimize_repaired_project(
                    project,
                    GeneratedProject(project_name=project.project_name, files=files),
                    diagnosis,
                )
                if _project_system_his_schema(project.files) == SYSTEM_HIS_V12_SCHEMA:
                    _validate_repair_preserves_l0_when_not_repairing_l0(repaired_project, diagnosis)
                patch_metadata = build_patch_metadata(project, repaired_project, diagnosis)
                return RepairResult(
                    generated_project=repaired_project,
                    patch_diff=diff_projects(project, repaired_project),
                    patch_metadata=patch_metadata,
                )
            except ValueError as exc:
                last_error = exc
                if _attempt + 1 < self.max_attempts:
                    record_parser_schema_retry(self.client, "parse_repaired_project")
        if last_error is not None:
            raise last_error
        raise RuntimeError("Project repairer did not run")
