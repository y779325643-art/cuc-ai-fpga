"""High-level SR2FPGA data generation orchestration."""

from __future__ import annotations

from dataclasses import asdict, replace
import difflib
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time
from typing import Any, Callable

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.cost_accounting import (
    COST_AXES,
    AccountingCommandRunner,
    AttemptCostLedger,
    AttemptCostLedgerRouter,
    ReconciledCostSummary,
    ReconciledTrajectory,
    reconcile_attempt_trajectory,
    reconcile_cost_events,
)
from sr2fpga_agent.contract_registry import ContractRegistry

from sr2fpga_agent.log_parser import (
    classify_failure,
    parse_test_fail_mismatches,
    parse_tool_warnings,
    parse_yosys_stats,
)
from sr2fpga_agent.evaluator_dispatch import DevelopmentHiddenEvaluationAuthority
from sr2fpga_agent.public_evaluator import (
    DevelopmentAttemptPublicEvaluationAuthority,
    DevelopmentPublicToolEvaluator,
    DevelopmentTerminalPublicEvaluationAuthority,
    read_verified_development_authoritative_attempt_public_outcome,
)
from sr2fpga_agent.public_l2_harness import DevelopmentTrustedPublicL2Harness
from sr2fpga_agent.terminal_selection import (
    TerminalSelectionCandidate,
    TerminalSelectionError,
    select_development_terminal_candidate,
)
from sr2fpga_agent.his_validation import (
    SystemHisValidationError,
    first_failed_h_stage,
    h_stage_labels,
    validate_frozen_system_his_payload_h_stages,
    validate_system_his_payload_h_stages,
    validate_system_his_h_stages,
)
from sr2fpga_agent.generation.req2his import (
    RequirementCapabilityGapError,
    RequirementClarificationRequired,
)
from sr2fpga_agent.frozen_context import (
    context_from_validated_episode_pack,
    validate_episode_pack,
)
from sr2fpga_agent.method_contract import method_policy_sha256
from sr2fpga_agent.project_contract import (
    build_composite_project_envelope,
    build_project_envelope,
)
from sr2fpga_agent.models import (
    GeneratedProject,
    PatchMetadata,
    PlatformProfile,
    ProjectRequest,
    RepairResult,  # noqa: F401 - compatibility re-export
    ToolResult,
)
from sr2fpga_agent.openxc7_report import parse_openxc7_report
from sr2fpga_agent.paired_measurement import build_episode_measurement
from sr2fpga_agent.oracle_runner import run_oracle_scenarios, write_oracle_run_evidence
from sr2fpga_agent.oracles import (
    OracleBundle,
    build_oracle_bundle_for_request,
    sanitize_oracle_profile,
)
from sr2fpga_agent.oracles.types import (
    INFRASTRUCTURE_FAILURE_ORIGINS,
    OracleRunEvidence,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.path_safety import (
    UnsupportedSynthesisLanguageError,
    build_patch_metadata,
    build_yosys_script,
    finalize_patch_metadata,
    project_file_target,
    validate_sample_id,
)
from sr2fpga_agent.parsers import parse_system_his_payload, resolve_project_manifest
from sr2fpga_agent.repository_paths import RepositoryPaths
from sr2fpga_agent.recorder import AttemptRecord, DatasetRecorder
from sr2fpga_agent.requirement_envelope import CriticalAmbiguity, RequirementEnvelope
from sr2fpga_agent.rtl_identifier_checker import check_rtl_identifiers, rtl_identifier_tool_result
from sr2fpga_agent.system_his_checker import (
    L0CheckResult,
    check_common_project_l0,
    check_his_project_consistency,
)
from sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity
from sr2fpga_agent.semantic_trace import diagnose_semantic_trace, parse_semantic_trace
from sr2fpga_agent.testbench_checker import (
    build_oracle_strength,
    check_testbench_static_issues,
    testbench_observation_tool_result,
)
from sr2fpga_agent.failure_injector import oracle_mutation_projects
from sr2fpga_agent.tool_runner import CommandRunner
from sr2fpga_agent.vivado_report import run_vivado_reference


class _RequirementBoundaryMetadataError(ValueError):
    """The evaluator-supplied requirement disposition is not usable."""


class DataGenerationAgent:
    """Generate one dataset sample and run the lightweight tool pipeline."""

    def __init__(
        self,
        dataset_root: Path,
        command_runner: CommandRunner | None = None,
        project_generator: ProjectGenerator | None = None,
        repairer: object | None = None,
        system_his_repairer: object | None = None,
        repair_provider_name: str | None = None,
        max_attempts: int = 1,
        enable_openxc7_l4: bool = False,
        openxc7_tool: str = "openxc7_nextpnr",
        openxc7_command: str | None = None,
        openxc7_part: str | None = None,
        openxc7_board_profile: str = "",
        openxc7_timeout_seconds: int = 1800,
        enable_vivado_l4: bool = False,
        vivado_tool: str = "vivado",
        vivado_command: str = "vivado",
        vivado_part: str = "XC7Z020CLG484-2",
        vivado_timeout_seconds: int = 1800,
        enable_independent_oracle: bool = False,
        development_hidden_evaluation_authority: DevelopmentHiddenEvaluationAuthority | None = None,
        development_hidden_private_commitment: bytes | None = None,
        development_attempt_public_evaluation_authority: (
            DevelopmentAttemptPublicEvaluationAuthority | None
        ) = None,
        development_terminal_public_evaluation_authority: (
            DevelopmentTerminalPublicEvaluationAuthority | None
        ) = None,
        development_public_candidate_store: ArtifactStore | None = None,
        development_public_evaluator_store: ArtifactStore | None = None,
        development_public_workspace_root: Path | None = None,
        development_trusted_public_l2_harness: (
            DevelopmentTrustedPublicL2Harness | None
        ) = None,
        attempt_cost_ledger_factory: Callable[[int], AttemptCostLedger] | None = None,
        attempt_cost_router: AttemptCostLedgerRouter | None = None,
        tool_versions: dict[str, str] | None = None,
        tool_environment_ref: dict[str, Any] | None = None,
        l4_tool_environment: dict[str, Any] | None = None,
        l4_tool_environment_ref: dict[str, Any] | None = None,
    ) -> None:
        self.dataset_root = dataset_root
        self.recorder = DatasetRecorder(dataset_root)
        if (attempt_cost_ledger_factory is None) != (attempt_cost_router is None):
            raise ValueError("attempt cost ledger factory and router must be configured together")
        self.attempt_cost_ledger_factory = attempt_cost_ledger_factory
        self.attempt_cost_router = attempt_cost_router
        self.tool_versions = dict(
            tool_versions
            if tool_versions is not None
            else {"verilator": "unknown", "iverilog": "unknown", "yosys": "unknown"}
        )
        self.tool_environment_ref = (
            dict(tool_environment_ref) if tool_environment_ref is not None else None
        )
        self.l4_tool_environment = (
            dict(l4_tool_environment) if l4_tool_environment is not None else None
        )
        self.l4_tool_environment_ref = (
            dict(l4_tool_environment_ref)
            if l4_tool_environment_ref is not None
            else None
        )
        base_command_runner = command_runner or CommandRunner()
        self.command_runner = (
            AccountingCommandRunner(base_command_runner, attempt_cost_router)
            if attempt_cost_router is not None
            else base_command_runner
        )
        configured_public_components = (
            development_public_candidate_store,
            development_public_evaluator_store,
            development_public_workspace_root,
        )
        if development_trusted_public_l2_harness is not None and not all(
            value is not None for value in configured_public_components
        ):
            raise ValueError(
                "trusted public L2 harness requires the automatic development public stores"
            )
        if any(value is not None for value in configured_public_components):
            if not all(value is not None for value in configured_public_components):
                raise ValueError(
                    "development public candidate store, evaluator store, and workspace are all required"
                )
            if (
                development_attempt_public_evaluation_authority is not None
                or development_terminal_public_evaluation_authority is not None
            ):
                raise ValueError("development public authority objects and stores are exclusive")
            assert development_public_candidate_store is not None
            assert development_public_evaluator_store is not None
            assert development_public_workspace_root is not None
            development_attempt_public_evaluation_authority = (
                DevelopmentAttemptPublicEvaluationAuthority(
                    development_public_candidate_store,
                    development_public_evaluator_store,
                    DevelopmentPublicToolEvaluator(
                        development_public_workspace_root / "attempts",
                        command_runner=self.command_runner,
                        trusted_public_l2_harness=(
                            development_trusted_public_l2_harness
                        ),
                    ),
                    authoritative=True,
                )
            )
            development_terminal_public_evaluation_authority = (
                DevelopmentTerminalPublicEvaluationAuthority(
                    development_public_candidate_store,
                    development_public_evaluator_store,
                    DevelopmentPublicToolEvaluator(
                        development_public_workspace_root / "terminal",
                        command_runner=self.command_runner,
                        trusted_public_l2_harness=(
                            development_trusted_public_l2_harness
                        ),
                    ),
                )
            )
        self.project_generator = project_generator or ProjectGenerator()
        self.repairer = repairer
        self.system_his_repairer = system_his_repairer or _embedded_system_his_repairer(
            self.project_generator
        )
        self.repair_provider_name = repair_provider_name
        self.max_attempts = max_attempts
        self.enable_openxc7_l4 = enable_openxc7_l4
        self.openxc7_tool = openxc7_tool
        self.openxc7_command = openxc7_command
        self.openxc7_part = openxc7_part
        self.openxc7_board_profile = openxc7_board_profile
        self.openxc7_timeout_seconds = openxc7_timeout_seconds
        self.enable_vivado_l4 = enable_vivado_l4
        self.vivado_tool = vivado_tool
        self.vivado_command = vivado_command
        self.vivado_part = vivado_part
        self.vivado_timeout_seconds = vivado_timeout_seconds
        self.enable_independent_oracle = enable_independent_oracle
        self.development_hidden_evaluation_authority = development_hidden_evaluation_authority
        self.development_hidden_private_commitment = (
            bytes(development_hidden_private_commitment)
            if development_hidden_private_commitment is not None
            else None
        )
        if (
            development_attempt_public_evaluation_authority is None
        ) != (development_terminal_public_evaluation_authority is None):
            raise ValueError(
                "development attempt and terminal public authorities must be configured together"
            )
        if (
            development_attempt_public_evaluation_authority is not None
            and not development_attempt_public_evaluation_authority.authoritative
        ):
            raise ValueError("development attempt public authority must be authoritative")
        self.development_attempt_public_evaluation_authority = (
            development_attempt_public_evaluation_authority
        )
        self.development_terminal_public_evaluation_authority = (
            development_terminal_public_evaluation_authority
        )
        self.last_cost_summaries: list[ReconciledCostSummary] = []
        self.last_canonical_trajectory: ReconciledTrajectory | None = None
        self._cost_artifact_store: ArtifactStore | None = None
        self._terminal_candidate_ref: ArtifactRef | None = None
        self._development_hidden_outcome_ref: dict[str, str] | None = None
        self._development_hidden_conformance_outcome_ref: ArtifactRef | None = None
        self._development_terminal_selection_ref: ArtifactRef | None = None
        self._development_selected_public_outcome_ref: ArtifactRef | None = None
        self._development_terminal_public_outcome_ref: ArtifactRef | None = None
        self._terminal_candidate_missing_reason = "terminal_candidate_ref_missing"
        self._active_cost_ledger: AttemptCostLedger | None = None
        self._active_cost_attempt_id: int | None = None
        self._active_cost_started = 0.0
        self._active_candidate_output_hashes: tuple[str, ...] = ()
        self._outer_repair_attempts_used = 0

    def run_one(
        self,
        sample_id: str,
        requirement: str,
        request: ProjectRequest,
        platform: PlatformProfile,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.last_cost_summaries = []
        self.last_canonical_trajectory = None
        self._cost_artifact_store = None
        self._terminal_candidate_ref = None
        self._development_hidden_outcome_ref = None
        self._development_hidden_conformance_outcome_ref = None
        self._development_terminal_selection_ref = None
        self._development_selected_public_outcome_ref = None
        self._development_terminal_public_outcome_ref = None
        self._terminal_candidate_missing_reason = "terminal_candidate_ref_missing"
        self._active_cost_ledger = None
        self._active_cost_attempt_id = None
        self._active_cost_started = 0.0
        self._active_candidate_output_hashes = ()
        self._outer_repair_attempts_used = 0
        try:
            result = self._run_one_impl(
                sample_id,
                requirement,
                request,
                platform,
                metadata=metadata,
            )
        except BaseException:
            self._finish_cost_attempt(emergency=True)
            self._reconcile_attempt_trajectory()
            raise
        self._finish_cost_attempt(emergency=False)
        self._reconcile_attempt_trajectory()
        if self.last_cost_summaries:
            result["cost_summary_refs"] = [
                summary.artifact_ref.to_dict() for summary in self.last_cost_summaries
            ]
        if self.last_canonical_trajectory is not None:
            result["canonical_trajectory_ref"] = (
                self.last_canonical_trajectory.artifact_ref.to_dict()
            )
        if self._development_hidden_outcome_ref is not None:
            result["development_hidden_outcome_ref"] = dict(
                self._development_hidden_outcome_ref
            )
        if self._development_hidden_conformance_outcome_ref is not None:
            result["development_hidden_conformance_outcome_ref"] = (
                self._development_hidden_conformance_outcome_ref.to_dict()
            )
        if self._development_terminal_selection_ref is not None:
            result["development_terminal_selection_ref"] = (
                self._development_terminal_selection_ref.to_dict()
            )
        if self._development_selected_public_outcome_ref is not None:
            result["development_selected_public_outcome_ref"] = (
                self._development_selected_public_outcome_ref.to_dict()
            )
        if self._development_terminal_public_outcome_ref is not None:
            result["development_terminal_public_outcome_ref"] = (
                self._development_terminal_public_outcome_ref.to_dict()
            )
        return result

    def _run_one_impl(
        self,
        sample_id: str,
        requirement: str,
        request: ProjectRequest,
        platform: PlatformProfile,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        validate_sample_id(sample_id)
        sample_dir = self.recorder.start_sample(sample_id, requirement, platform, metadata=metadata)
        try:
            boundary_stop = _requirement_boundary_stop(metadata)
        except _RequirementBoundaryMetadataError as exc:
            return self._record_generation_failure(
                sample_id,
                sample_dir,
                request,
                exc,
                metadata=metadata,
            )
        if boundary_stop is not None:
            return self._record_generation_failure(
                sample_id,
                sample_dir,
                request,
                boundary_stop,
                metadata=metadata,
            )
        self._start_cost_attempt(0)
        h_stages_applicable = _h_stages_applicable(metadata, self.project_generator)
        staged_his_generation = h_stages_applicable and _supports_staged_his_generation(
            self.project_generator
        )
        project: GeneratedProject | None = None
        if not staged_his_generation:
            try:
                project = self.project_generator.generate(request, platform)
            except Exception as exc:
                return self._record_generation_failure(
                    sample_id,
                    sample_dir,
                    request,
                    exc,
                    metadata=metadata,
                )

        pending_his_error: SystemHisValidationError | None = None
        pending_system_his: dict[str, Any] | None = None
        all_stage_entries: list[dict[str, Any]] = []
        attempt_measurements: list[dict[str, Any]] = []
        failure_count = 0
        final_attempt_id = 0
        final_tool_results: dict[str, ToolResult] = {}
        final_project = project or GeneratedProject(project_name=request.project_name, files={})
        final_his_validation: dict[str, Any] | None = None
        final_oracle_bundle: OracleBundle | None = None
        final_oracle_profile = _oracle_not_run_profile(
            request.task_type,
            "disabled_by_config" if not self.enable_independent_oracle else "unsupported_family",
        )
        patches: list[PatchMetadata] = []
        pending_patch_attempt_id: int | None = None
        development_selection_candidates: list[TerminalSelectionCandidate] = []
        development_outcomes: dict[str, dict[str, Any]] = {}
        development_his_validations: dict[str, dict[str, Any]] = {}
        development_authority_enabled = self._development_public_authority_enabled(
            metadata
        )

        for attempt_id in range(self.max_attempts):
            if attempt_id != self._active_cost_attempt_id:
                self._finish_cost_attempt(emergency=False)
                self._start_cost_attempt(attempt_id)
            final_attempt_id = attempt_id
            active_his_error = pending_his_error
            pending_his_error = None
            generation_error: Exception | None = None
            if project is None:
                if active_his_error is not None:
                    project = _system_his_candidate_project(request, active_his_error.candidate_output)
                else:
                    try:
                        system_his = pending_system_his
                        pending_system_his = None
                        if system_his is None:
                            system_his = self.project_generator.generate_system_his(request, platform)
                        project = self.project_generator.generate_from_system_his(
                            request,
                            platform,
                            system_his,
                        )
                    except SystemHisValidationError as exc:
                        active_his_error = exc
                        project = _system_his_candidate_project(request, exc.candidate_output)
                    except Exception as exc:
                        generation_error = exc
                        project = (
                            _system_his_candidate_project(
                                request,
                                json.dumps(system_his, ensure_ascii=False),
                            )
                            if system_his is not None
                            else GeneratedProject(project_name=request.project_name, files={})
                        )
            final_project = project
            project_dir = sample_dir / "attempts" / f"attempt_{attempt_id:03d}" / "generated_project"
            _write_project(project_dir, project)

            if active_his_error is not None:
                his_validation = active_his_error.report
            elif h_stages_applicable:
                his_validation = (
                    _not_run_h_stage_report("generation_failed_before_system_his_candidate")
                    if generation_error is not None and "system_his.json" not in project.files
                    else _validate_generated_project_h_stages(
                        request,
                        project,
                        metadata=metadata,
                        project_generator=self.project_generator,
                        platform=platform,
                    )
                )
            else:
                his_validation = _not_applicable_h_stage_report()
            final_his_validation = his_validation
            h_stage_failed = not his_validation["passed"]
            if h_stage_failed and active_his_error is None and staged_his_generation:
                active_his_error = SystemHisValidationError(
                    project.files.get("system_his.json", ""),
                    his_validation,
                )
            l0_result: L0CheckResult | None = None
            l0_checker = "common_project_l0"
            attempt_oracle_bundle: OracleBundle | None = None
            attempt_oracle_evidence: OracleRunEvidence | None = None
            oracle_infrastructure_failure = False
            authoritative_outcome: dict[str, Any] | None = None
            if generation_error is not None:
                tool_results = {"generation": _generation_failure_tool_result(generation_error)}
            elif h_stage_failed:
                tool_results = {"his_validation": _h_stage_tool_result(his_validation)}
            elif development_authority_enabled:
                candidate_ref, outcome_ref, authoritative_outcome = (
                    self._evaluate_development_attempt_publicly(
                        sample_id=sample_id,
                        request=request,
                        metadata=metadata,
                        project=project,
                        attempt_id=attempt_id,
                    )
                )
                development_selection_candidates.append(
                    TerminalSelectionCandidate(candidate_ref, outcome_ref)
                )
                development_outcomes[f"attempt-{attempt_id:03d}"] = authoritative_outcome
                development_his_validations[f"attempt-{attempt_id:03d}"] = his_validation
                tool_results = _authoritative_public_tool_results(authoritative_outcome)
            else:
                l0_result = check_common_project_l0(project)
                if l0_result.passed and h_stages_applicable:
                    l0_checker = "his_project_consistency"
                    l0_result = check_his_project_consistency(project)
            if l0_result is not None and l0_result.passed:
                if self.enable_independent_oracle:
                    family_id = str((metadata or {}).get("family_id") or request.task_type)
                    oracle_root = project_dir.parent / "eval" / "oracle"
                    try:
                        attempt_oracle_bundle = build_oracle_bundle_for_request(
                            family_id,
                            request,
                            oracle_root,
                        )
                    except Exception as exc:
                        oracle_infrastructure_failure = True
                        final_oracle_profile = _oracle_error_profile(family_id, exc)
                        tool_results = {"oracle_bundle": _oracle_bundle_failure_tool_result(exc)}
                    else:
                        evidence_out: list[OracleRunEvidence] = []
                        tool_results = self._run_pipeline(
                            project,
                            project_dir,
                            platform,
                            oracle_bundle=attempt_oracle_bundle,
                            oracle_evidence_out=evidence_out,
                            oracle_evidence_path=(oracle_root / "evidence.json") if attempt_oracle_bundle else None,
                        )
                        attempt_oracle_evidence = evidence_out[0] if evidence_out else None
                        if attempt_oracle_bundle is not None and attempt_oracle_evidence is None:
                            final_oracle_profile = _oracle_not_run_profile(family_id, "blocked_before_oracle")
                        else:
                            final_oracle_profile = _oracle_profile(
                                family_id,
                                attempt_oracle_bundle,
                                attempt_oracle_evidence,
                            )
                        oracle_infrastructure_failure = final_oracle_profile.get("status") == "infrastructure_error"
                else:
                    tool_results = self._run_pipeline(project, project_dir, platform)
            elif l0_result is not None:
                tool_results = {
                    "l0_consistency": _l0_tool_result(l0_result, checker=l0_checker)
                }
            final_oracle_bundle = attempt_oracle_bundle
            final_tool_results = tool_results
            tool_infrastructure_reason = (
                authoritative_outcome["infrastructure_reason"]
                if authoritative_outcome is not None
                else _tool_infrastructure_reason(tool_results)
            )
            tool_infrastructure_failure = tool_infrastructure_reason is not None
            tool_non_repairable_reason = _tool_non_repairable_reason(tool_results)
            if patches and pending_patch_attempt_id is not None:
                previous_patch = patches[-1]
                post_repair_results = {stage: result.status for stage, result in tool_results.items()}
                if (
                    previous_patch.repair_regression.get("target_failure") == "l0_consistency"
                    and l0_result is not None
                    and l0_result.passed
                ):
                    post_repair_results["l0_consistency"] = "passed"
                finalized_patch = finalize_patch_metadata(
                    previous_patch,
                    post_repair_results,
                )
                patches[-1] = finalized_patch
                self.recorder.update_patch_metadata(sample_id, pending_patch_attempt_id, finalized_patch)
                pending_patch_attempt_id = None
            diagnosis = (
                _system_his_failure_diagnosis(his_validation)
                if h_stage_failed
                else (
                    _authoritative_agent_diagnosis(
                        authoritative_outcome["repair_diagnosis"]
                    )
                    if authoritative_outcome is not None
                    and authoritative_outcome["repair_diagnosis"] is not None
                    else None
                )
                if development_authority_enabled
                else _diagnose_first_failure(
                    tool_results,
                    l0_result=l0_result,
                    system_his_applicable=l0_checker == "his_project_consistency",
                )
            )
            patch_diff = ""
            patch_metadata = None
            scheduled_his_retry = False
            repair_scope = (
                "system_his"
                if h_stage_failed
                else (
                    "project"
                    if diagnosis is not None
                    and not oracle_infrastructure_failure
                    and not tool_infrastructure_failure
                    and tool_non_repairable_reason is None
                    else None
                )
            )
            repair_attempted = False
            repair_call_status = "not_run"
            h_repair_eligible = (
                h_stage_failed
                and staged_his_generation
                and active_his_error is not None
                and self.system_his_repairer is not None
                and attempt_id + 1 < self.max_attempts
            )

            if diagnosis is not None:
                if not oracle_infrastructure_failure and not tool_infrastructure_failure:
                    failure_count += 1
                if h_repair_eligible:
                    repair_attempted = True
                    self._reserve_outer_repair_attempt()
                    try:
                        repaired_system_his = self.system_his_repairer.repair(
                            request,
                            platform,
                            active_his_error.candidate_output,
                            his_validation,
                        )
                    except SystemHisValidationError as exc:
                        repair_call_status = "candidate_failed_validation"
                        repaired_candidate = _system_his_candidate_project(
                            request,
                            exc.candidate_output,
                        )
                        patch_diff, patch_metadata = _system_his_patch(
                            final_project,
                            repaired_candidate,
                            his_validation,
                            exc.report,
                            diagnosis,
                            attempt_id=attempt_id,
                            provider_name=_system_his_repair_provider(metadata),
                        )
                        patches.append(patch_metadata)
                        pending_his_error = exc
                        project = None
                        scheduled_his_retry = True
                    except Exception as exc:
                        repair_call_status = "failed"
                        tool_results = {
                            **tool_results,
                            "repair": _repair_failure_tool_result(exc),
                        }
                        diagnosis = _repair_failure_diagnosis(
                            exc,
                            upstream_diagnosis=diagnosis,
                        )
                    else:
                        repair_call_status = "succeeded"
                        repaired_report = validate_system_his_payload_h_stages(
                            request,
                            repaired_system_his,
                            platform=platform,
                        )
                        repaired_candidate = _system_his_candidate_project(
                            request,
                            json.dumps(repaired_system_his, ensure_ascii=False, sort_keys=True),
                        )
                        patch_diff, patch_metadata = _system_his_patch(
                            final_project,
                            repaired_candidate,
                            his_validation,
                            repaired_report,
                            diagnosis,
                            attempt_id=attempt_id,
                            provider_name=_system_his_repair_provider(metadata),
                        )
                        patches.append(patch_metadata)
                        pending_system_his = repaired_system_his
                        project = None
                        scheduled_his_retry = True
                elif h_stage_failed:
                    pass
                elif oracle_infrastructure_failure or tool_infrastructure_failure:
                    pass
                elif self.repairer is not None and attempt_id + 1 < self.max_attempts:
                    repair_scope = "project"
                    repair_attempted = True
                    self._reserve_outer_repair_attempt()
                    try:
                        repair_result = self.repairer.repair(project, diagnosis)
                    except Exception as exc:
                        repair_call_status = "failed"
                        tool_results = {
                            **tool_results,
                            "repair": _repair_failure_tool_result(exc),
                        }
                        diagnosis = _repair_failure_diagnosis(exc, upstream_diagnosis=diagnosis)
                    else:
                        repair_call_status = "succeeded"
                        patch_diff = repair_result.patch_diff
                        patch_diagnosis = {
                            **diagnosis,
                            "diagnosis_id": f"d{attempt_id + 1:03d}",
                            "tool_result_before": {stage: result.status for stage, result in tool_results.items()},
                        }
                        patch_metadata = build_patch_metadata(
                            project,
                            repair_result.generated_project,
                            patch_diagnosis,
                            patch_id=f"p{attempt_id + 1:03d}",
                        )
                        patch_metadata = replace(
                            patch_metadata,
                            repair_provider_resolved=self.repair_provider_name,
                        )
                        patches.append(patch_metadata)
                        if patch_metadata.status == "valid":
                            project = repair_result.generated_project
                            pending_patch_attempt_id = attempt_id
                        else:
                            repair_call_status = "failed"
                            tool_results = {
                                **tool_results,
                                "repair": _repair_failure_tool_result(ValueError("invalid_edit_surface")),
                            }
                            diagnosis = _repair_failure_diagnosis(
                                ValueError("invalid_edit_surface"),
                                upstream_diagnosis=diagnosis,
                            )

            if h_stage_failed:
                repair_eligible = h_repair_eligible
                if h_repair_eligible:
                    repair_skip_reason = None
                elif not staged_his_generation or active_his_error is None:
                    repair_skip_reason = "h_stage_not_outer_repairable"
                elif self.system_his_repairer is None:
                    repair_skip_reason = "no_system_his_repairer"
                else:
                    repair_skip_reason = "repair_budget_exhausted"
            else:
                repair_eligible, repair_skip_reason = _repair_eligibility(
                    diagnosis=diagnosis,
                    h_stage_failed=False,
                    oracle_infrastructure_failure=(
                        oracle_infrastructure_failure or tool_infrastructure_failure
                    ),
                    has_repairer=self.repairer is not None,
                    attempt_id=attempt_id,
                    max_attempts=self.max_attempts,
                )
                if tool_non_repairable_reason == "capability_gap":
                    repair_eligible = False
                    repair_skip_reason = "capability_gap"
            attempt_measurement = {
                "attempt_id": attempt_id,
                "pass_level": _raw_tool_pass_level(tool_results, his_validation),
                "failure_type": (diagnosis or {}).get("failure_type", "none"),
                "automatic_pass_credit": not (
                    oracle_infrastructure_failure or tool_infrastructure_failure
                ),
                "repair_eligible": repair_eligible,
                "repair_skip_reason": repair_skip_reason,
            }
            if repair_scope is not None:
                attempt_measurement["repair_scope"] = repair_scope
                attempt_measurement["repair_attempted"] = repair_attempted
                attempt_measurement["repair_call_status"] = repair_call_status
            if tool_infrastructure_failure:
                attempt_measurement["infrastructure_reason"] = tool_infrastructure_reason
            elif oracle_infrastructure_failure:
                attempt_measurement["infrastructure_reason"] = "independent_oracle_infrastructure_error"
            attempt_measurements.append(attempt_measurement)

            final_tool_results = tool_results
            all_stage_entries.extend(_stage_entries(attempt_id, tool_results, diagnosis, bool(patch_diff)))
            self._active_candidate_output_hashes = (_sha256(final_project.files),)
            self.recorder.write_attempt(
                sample_id,
                AttemptRecord(
                    attempt_id=attempt_id,
                    generated_project=final_project,
                    tool_results=tool_results,
                    diagnosis=diagnosis,
                    patch_diff=patch_diff,
                    patch_metadata=patch_metadata,
                ),
            )

            if scheduled_his_retry:
                continue
            if diagnosis is None:
                break
            if generation_error is not None:
                break
            if h_stage_failed:
                break
            if oracle_infrastructure_failure or tool_infrastructure_failure:
                break
            if diagnosis.get("stage") == "repair":
                break

        selected_authoritative_outcome: dict[str, Any] | None = None
        if development_authority_enabled:
            try:
                (
                    final_project,
                    final_attempt_id,
                    final_tool_results,
                    final_his_validation,
                    selected_authoritative_outcome,
                ) = self._select_and_seal_development_terminal(
                    sample_id=sample_id,
                    request=request,
                    metadata=metadata,
                    candidates=development_selection_candidates,
                    outcomes=development_outcomes,
                    his_validations=development_his_validations,
                )
                project_dir = (
                    sample_dir
                    / "attempts"
                    / f"attempt_{final_attempt_id:03d}"
                    / "generated_project"
                )
            except TerminalSelectionError as exc:
                self._terminal_candidate_ref = None
                self._terminal_candidate_missing_reason = (
                    "terminal_candidate_seal_unavailable:" + str(exc).replace(" ", "_")
                )
        else:
            self._seal_terminal_candidate(
                sample_id=sample_id,
                request=request,
                metadata=metadata,
                project=final_project,
                final_attempt_id=final_attempt_id,
                tool_results=final_tool_results,
                his_validation=final_his_validation,
            )
        if (
            development_authority_enabled
            and self._terminal_candidate_ref is not None
            and self.enable_openxc7_l4
            and final_tool_results.get("synth") is not None
            and final_tool_results["synth"].status == "passed"
        ):
            final_tool_results["pnr"] = _normalize_missing_tool(
                self.command_runner.run(
                    _openxc7_pnr_command(
                        project_dir,
                        platform,
                        command_prefix=self.openxc7_command,
                        part=self.openxc7_part,
                    ),
                    cwd=project_dir,
                    stage="pnr",
                    timeout_seconds=self.openxc7_timeout_seconds,
                )
            )
        l4_open = _l4_open_record(
            final_tool_results,
            self.enable_openxc7_l4,
            final_attempt_id,
            tool=self.openxc7_tool,
            board_profile=self.openxc7_board_profile,
            project_dir=project_dir,
            core_tool_environment_ref=self.tool_environment_ref,
            l4_tool_environment=self.l4_tool_environment,
            l4_tool_environment_ref=self.l4_tool_environment_ref,
        )
        vivado_selected = (
            self.enable_vivado_l4
            and final_tool_results.get("synth") is not None
            and final_tool_results["synth"].status == "passed"
        )
        vivado_started = time.monotonic()
        l4_commercial = _run_l4_commercial_reference(
            final_tool_results,
            self.enable_vivado_l4,
            project_dir=project_dir,
            attempt_id=final_attempt_id,
            tool=self.vivado_tool,
            vivado_command=self.vivado_command,
            part=self.vivado_part,
            target_period_ns=1_000_000_000 / platform.clock_hz,
            timeout_seconds=self.vivado_timeout_seconds,
            core_tool_environment_ref=self.tool_environment_ref,
            l4_tool_environment=self.l4_tool_environment,
            l4_tool_environment_ref=self.l4_tool_environment_ref,
        )
        if vivado_selected and self._active_cost_ledger is not None:
            vivado_duration = l4_commercial.get("runtime_sec")
            if not isinstance(vivado_duration, (int, float)):
                vivado_duration = time.monotonic() - vivado_started
            self._active_cost_ledger.record_cost(
                stage="l4_commercial",
                visibility_class="public",
                status="completed" if l4_commercial.get("status") == "pass" else "failed",
                duration_seconds=max(0.0, float(vivado_duration)),
                cost_delta={
                    "public_tool_calls": 1,
                    "eda_time": max(0.0, float(vivado_duration)),
                },
            )
        measured_qor = _measured_qor(final_tool_results, l4_open, l4_commercial)
        if development_authority_enabled and self._terminal_candidate_ref is not None:
            self._run_development_terminal_public_evaluation(
                request=request,
                metadata=metadata,
            )
        development_hidden_outcome = self._run_development_hidden_evaluation(
            sample_id=sample_id,
            request=request,
            metadata=metadata,
            project=final_project,
            tool_results=final_tool_results,
            his_validation=final_his_validation,
        )
        trajectory = _trajectory(sample_id, all_stage_entries)
        if patches:
            trajectory["patches"] = [patch.to_dict() for patch in patches]
        trajectory["measurement"] = build_episode_measurement(
            attempts=attempt_measurements,
            patches=[patch.to_dict() for patch in patches],
            l4_open=l4_open,
        )
        trajectory["attempt_measurements"] = attempt_measurements
        if development_hidden_outcome is not None:
            trajectory["development_hidden_outcome"] = development_hidden_outcome
            self._development_hidden_outcome_ref = dict(development_hidden_outcome)
        oracle_strength = self._oracle_strength(
            final_project,
            sample_dir,
            platform,
            request.task_type,
            final_tool_results,
            oracle_bundle=final_oracle_bundle,
        )
        if oracle_strength is not None:
            trajectory["oracle_strength"] = oracle_strength
        labels = _labels(
            final_tool_results,
            l4_open,
            final_attempt_id=final_attempt_id,
            failure_count=failure_count,
            his_validation=final_his_validation,
            oracle_strength=oracle_strength,
            enforce_oracle_readiness=bool(metadata and metadata.get("evaluation_line") == "line_a"),
            expected_bram=_expected_bram(final_project),
            l4_commercial=l4_commercial,
            oracle_profile=final_oracle_profile,
        )
        labels["automatic_pass_credit"] = bool(labels.get("automatic_pass_credit", True)) and all(
            patch.automatic_pass_credit for patch in patches
        )
        if selected_authoritative_outcome is not None:
            labels["development_public_acceptance"] = bool(
                selected_authoritative_outcome["public_acceptance"]
            )
            labels["development_pass_credit_authority"] = True
            labels["official_outcome"] = False
            labels["automatic_pass_credit"] = bool(
                labels["automatic_pass_credit"]
                and selected_authoritative_outcome["public_acceptance"]
                and self._development_terminal_public_outcome_ref is not None
            )
        elif development_authority_enabled:
            labels["development_public_acceptance"] = False
            labels["development_pass_credit_authority"] = True
            labels["development_design_outcome"] = "fail"
            labels["official_outcome"] = False
            labels["automatic_pass_credit"] = False
        if not labels["automatic_pass_credit"]:
            final_tool_infrastructure_reason = _tool_infrastructure_reason(final_tool_results)
            development_credit_reason = None
            if selected_authoritative_outcome is not None:
                if not selected_authoritative_outcome["public_acceptance"]:
                    development_credit_reason = "development_public_acceptance_false"
                elif self._development_terminal_public_outcome_ref is None:
                    development_credit_reason = "terminal_public_outcome_unavailable"
            elif development_authority_enabled:
                development_credit_reason = "no_complete_development_terminal"
            labels["automatic_pass_credit_reason"] = (
                development_credit_reason
                or final_tool_infrastructure_reason
                or (
                    "independent_oracle_infrastructure_error"
                    if final_oracle_profile.get("status") == "infrastructure_error"
                    else _automatic_pass_credit_reason(patches)
                )
            )
        if final_his_validation is not None:
            trajectory["his_validation"] = final_his_validation
        trajectory["oracle_profile"] = final_oracle_profile
        req_his_fidelity = _req_his_fidelity(request, final_project, platform)
        if req_his_fidelity is not None:
            trajectory["req_his_fidelity"] = req_his_fidelity
        self.recorder.write_final(
            sample_id,
            final_project,
            labels=labels,
            measured_qor=measured_qor,
            tool_versions=self.tool_versions,
            trajectory=trajectory,
        )
        result: dict[str, Any] = {
            "sample_dir": str(sample_dir),
            "pass_level": labels["pass_level"],
        }
        failed_h_stage = (
            first_failed_h_stage(final_his_validation)
            if final_his_validation is not None
            else None
        )
        if failed_h_stage is not None:
            result["failure_type"] = "his_validation_failed"
            result["failed_h_stage"] = failed_h_stage
        elif (
            final_tool_results.get("generation") is not None
            and final_tool_results["generation"].status != "passed"
        ):
            result["failure_type"] = "generation_failed"
        return result

    def _start_cost_attempt(self, attempt_id: int) -> None:
        factory = self.attempt_cost_ledger_factory
        router = self.attempt_cost_router
        if factory is None or router is None:
            return
        ledger = factory(attempt_id)
        if self._cost_artifact_store is None:
            self._cost_artifact_store = ledger.store
        elif self._cost_artifact_store.root != ledger.store.root:
            raise ValueError("all attempt ledgers for one episode must share an artifact store")
        router.activate(ledger)
        self._active_cost_ledger = ledger
        self._active_cost_attempt_id = attempt_id
        self._active_cost_started = time.monotonic()
        self._active_candidate_output_hashes = ()

    def _reconcile_attempt_trajectory(self) -> None:
        store = self._cost_artifact_store
        if store is None or not self.last_cost_summaries:
            return
        self.last_canonical_trajectory = reconcile_attempt_trajectory(
            store,
            [summary.artifact_ref for summary in self.last_cost_summaries],
            terminal_candidate_ref=self._terminal_candidate_ref,
            terminal_candidate_missing_reason=self._terminal_candidate_missing_reason,
            development_hidden_outcome_ref=self._development_hidden_outcome_ref,
            development_hidden_conformance_outcome_ref=(
                self._development_hidden_conformance_outcome_ref
            ),
            development_terminal_selection_ref=self._development_terminal_selection_ref,
            development_selected_public_outcome_ref=(
                self._development_selected_public_outcome_ref
            ),
            development_terminal_public_outcome_ref=(
                self._development_terminal_public_outcome_ref
            ),
        )

    def _development_public_authority_enabled(
        self, metadata: dict[str, Any] | None
    ) -> bool:
        return (
            self.development_attempt_public_evaluation_authority is not None
            and self.development_terminal_public_evaluation_authority is not None
            and str((metadata or {}).get("method_condition", "")).strip().upper()
            in {"M0", "M1", "M2", "M3", "M4", "M5"}
            and str((metadata or {}).get("analysis_population", "development"))
            in {"development", "excluded"}
        )

    def _evaluate_development_attempt_publicly(
        self,
        *,
        sample_id: str,
        request: ProjectRequest,
        metadata: dict[str, Any] | None,
        project: GeneratedProject,
        attempt_id: int,
    ) -> tuple[ArtifactRef, ArtifactRef, dict[str, Any]]:
        authority = self.development_attempt_public_evaluation_authority
        ledger = self._active_cost_ledger
        store = self._cost_artifact_store
        if authority is None or ledger is None or store is None or ledger.candidate_id is None:
            raise ValueError("development public authority accounting identity is unavailable")
        if authority.candidate_store.root.resolve() != store.root.resolve():
            raise ValueError("development public authority candidate store mismatch")
        method_condition = ledger.method_condition
        attempt_identity = f"attempt-{attempt_id:03d}"
        if ledger.attempt_id != attempt_identity:
            raise ValueError("development public authority attempt identity mismatch")
        requirement_projection_sha256 = self._development_projection_sha256(
            metadata,
            request=request,
            method_condition=method_condition,
        )
        creation_event_ref = store.append_event(
            sample_id,
            "public_evaluation_candidate_created",
            {
                "candidate_id": ledger.candidate_id,
                "attempt_id": attempt_identity,
                "method_condition_id": method_condition,
            },
        )
        try:
            envelope_ref = self._build_project_envelope_ref(
                store=store,
                sample_id=sample_id,
                method_condition=method_condition,
                candidate_id=ledger.candidate_id,
                attempt_id=attempt_id,
                project=project,
            )
            candidate_ref = store.seal_public_evaluation_candidate(
                ledger.candidate_id,
                attempt_id=attempt_identity,
                project=project,
                project_envelope_ref=envelope_ref,
                requirement_projection_sha256=requirement_projection_sha256,
                creation_event_ref=creation_event_ref,
            )
        except ValueError as exc:
            candidate_ref = store.seal_unverified_public_evaluation_candidate(
                ledger.candidate_id,
                episode_id=sample_id,
                attempt_id=attempt_identity,
                method_condition_id=method_condition,
                project=project,
                project_envelope_reason=_public_envelope_failure_reason(exc),
                requirement_projection_sha256=requirement_projection_sha256,
                creation_event_ref=creation_event_ref,
            )
        outcome = authority.evaluate_once(
            public_evaluation_candidate_ref=candidate_ref,
            public_contract_sha256=method_policy_sha256(method_condition),
            public_profile_sha256=requirement_projection_sha256,
            tool_environment_policy_sha256=method_policy_sha256(method_condition),
        )
        payload = read_verified_development_authoritative_attempt_public_outcome(
            store, outcome.artifact_ref
        )
        return candidate_ref, outcome.artifact_ref, payload

    def _build_project_envelope_ref(
        self,
        *,
        store: ArtifactStore,
        sample_id: str,
        method_condition: str,
        candidate_id: str,
        attempt_id: int,
        project: GeneratedProject,
    ) -> ArtifactRef:
        snapshot_id = "snapshot-" + _sha256(
            {
                "episode_id": sample_id,
                "attempt_id": attempt_id,
                "candidate_id": candidate_id,
                "project": project.files,
            }
        )[:16]
        if method_condition in {"M4", "M5"}:
            trusted_event_ref = store.append_event(
                sample_id,
                "trusted_skeleton_materialized",
                {
                    "candidate_id": candidate_id,
                    "attempt_id": attempt_id,
                    "method_condition": method_condition,
                },
            )
            model_event_ref = store.append_event(
                sample_id,
                "model_behavior_materialized",
                {
                    "candidate_id": candidate_id,
                    "attempt_id": attempt_id,
                    "method_condition": method_condition,
                },
            )
            envelope = build_composite_project_envelope(
                project,
                episode_id=sample_id,
                method_condition_id=method_condition,
                snapshot_id=snapshot_id,
                trusted_builder_event_id=_trusted_event_id(store, trusted_event_ref),
                model_generation_event_id=_trusted_event_id(store, model_event_ref),
                event_ref_resolver=store.has_event_id,
            )
        else:
            envelope = build_project_envelope(
                project,
                episode_id=sample_id,
                method_condition_id=method_condition,
                method_policy_sha256=method_policy_sha256(method_condition),
                snapshot_id=snapshot_id,
                file_policies={
                    path: {"owner": "model", "origin": "model_generated", "editable": False}
                    for path in project.files
                },
            )
        return store.put_validated_json(
            f"project-envelopes/{candidate_id}",
            envelope,
            contract_key="project_envelope",
        )

    def _select_and_seal_development_terminal(
        self,
        *,
        sample_id: str,
        request: ProjectRequest,
        metadata: dict[str, Any] | None,
        candidates: list[TerminalSelectionCandidate],
        outcomes: dict[str, dict[str, Any]],
        his_validations: dict[str, dict[str, Any]],
    ) -> tuple[
        GeneratedProject,
        int,
        dict[str, ToolResult],
        dict[str, Any],
        dict[str, Any],
    ]:
        store = self._cost_artifact_store
        ledger = self._active_cost_ledger
        if store is None or ledger is None:
            raise TerminalSelectionError("accounting_identity_missing")
        evaluation_scope = str((metadata or {}).get("analysis_population", "development"))
        selection = select_development_terminal_candidate(
            store,
            episode_id=sample_id,
            method_condition=ledger.method_condition,
            evaluation_scope=evaluation_scope,
            attempt_profile="@1" if self.max_attempts == 1 else "@A",
            candidates=candidates,
        )
        self._development_terminal_selection_ref = selection.artifact_ref
        selected_attempt = selection.payload["selected_attempt_id"]
        selected_candidate_ref = _artifact_ref_from_payload(
            selection.payload["selected_public_evaluation_candidate_ref"]
        )
        selected_outcome_ref = _artifact_ref_from_payload(
            selection.payload["selected_public_outcome_ref"]
        )
        candidate_payload = json.loads(store.read_verified(selected_candidate_ref))
        envelope_payload = candidate_payload.get("project_envelope_ref")
        if not isinstance(envelope_payload, dict):
            raise TerminalSelectionError("selected_project_envelope_missing")
        selected_project = store.read_public_evaluation_candidate(selected_candidate_ref)
        selected_outcome = read_verified_development_authoritative_attempt_public_outcome(
            store, selected_outcome_ref
        )
        creation_event_ref = store.append_event(
            sample_id,
            "terminal_candidate_selected",
            {
                "candidate_id": selection.payload["selected_candidate_id"],
                "attempt_id": selected_attempt,
                "method_condition": ledger.method_condition,
                "selection_id": selection.payload["selection_id"],
                "selection_reason": selection.payload["selection_reason"],
                "public_acceptance": selected_outcome["public_acceptance"],
            },
        )
        self._terminal_candidate_ref = store.seal_candidate(
            selection.payload["selected_candidate_id"],
            project=selected_project,
            project_envelope_ref=_artifact_ref_from_payload(envelope_payload),
            requirement_projection_sha256=candidate_payload[
                "requirement_projection_sha256"
            ],
            creation_event_ref=creation_event_ref,
            public_evidence_refs=(selection.artifact_ref, selected_outcome_ref),
        )
        self._development_selected_public_outcome_ref = selected_outcome_ref
        self._terminal_candidate_missing_reason = "terminal_candidate_ref_missing"
        attempt_number = int(selected_attempt.removeprefix("attempt-"))
        return (
            selected_project,
            attempt_number,
            _authoritative_public_tool_results(selected_outcome),
            his_validations[selected_attempt],
            selected_outcome,
        )

    def _run_development_terminal_public_evaluation(
        self,
        *,
        request: ProjectRequest,
        metadata: dict[str, Any] | None,
    ) -> None:
        authority = self.development_terminal_public_evaluation_authority
        candidate_ref = self._terminal_candidate_ref
        selected_ref = self._development_selected_public_outcome_ref
        store = self._cost_artifact_store
        if authority is None or candidate_ref is None or selected_ref is None or store is None:
            return
        if authority.candidate_store.root.resolve() != store.root.resolve():
            raise ValueError("development terminal public authority candidate store mismatch")
        selected = read_verified_development_authoritative_attempt_public_outcome(
            store, selected_ref
        )
        method_condition = selected["method_condition"]
        requirement_projection_sha256 = self._development_projection_sha256(
            metadata,
            request=request,
            method_condition=method_condition,
        )
        outcome = authority.evaluate_once(
            terminal_candidate_ref=candidate_ref,
            public_contract_sha256=method_policy_sha256(method_condition),
            public_profile_sha256=requirement_projection_sha256,
            tool_environment_policy_sha256=method_policy_sha256(method_condition),
        )
        terminal_payload = outcome.payload
        if terminal_payload["terminal_candidate_sha256"] != candidate_ref.sha256:
            raise ValueError("terminal public outcome candidate hash mismatch")
        if terminal_payload["stage_outcomes"] != selected["stage_outcomes"]:
            raise ValueError("selected-attempt and terminal public outcomes disagree")
        if terminal_payload["public_l2_harness"] != selected["public_l2_harness"]:
            raise ValueError(
                "selected-attempt and terminal public L2 harness commitments disagree"
            )
        if terminal_payload["public_acceptance"] != selected["public_acceptance"]:
            raise ValueError("selected-attempt and terminal public acceptance disagree")
        self._development_terminal_public_outcome_ref = outcome.artifact_ref

    def _seal_terminal_candidate(
        self,
        *,
        sample_id: str,
        request: ProjectRequest,
        metadata: dict[str, Any] | None,
        project: GeneratedProject,
        final_attempt_id: int,
        tool_results: dict[str, ToolResult],
        his_validation: dict[str, Any] | None,
    ) -> None:
        ledger = self._active_cost_ledger
        store = self._cost_artifact_store
        if ledger is None or store is None or ledger.candidate_id is None:
            self._terminal_candidate_missing_reason = (
                "terminal_candidate_seal_unavailable:accounting_identity_missing"
            )
            return
        method_condition = ledger.method_condition
        candidate_id = ledger.candidate_id
        snapshot_id = "snapshot-" + _sha256(
            {
                "episode_id": sample_id,
                "attempt_id": final_attempt_id,
                "candidate_id": candidate_id,
                "project": project.files,
            }
        )[:16]
        try:
            if method_condition in {"M4", "M5"}:
                trusted_event_ref = store.append_event(
                    sample_id,
                    "trusted_skeleton_materialized",
                    {
                        "candidate_id": candidate_id,
                        "attempt_id": final_attempt_id,
                        "method_condition": method_condition,
                    },
                )
                model_event_ref = store.append_event(
                    sample_id,
                    "model_behavior_materialized",
                    {
                        "candidate_id": candidate_id,
                        "attempt_id": final_attempt_id,
                        "method_condition": method_condition,
                    },
                )
                envelope = build_composite_project_envelope(
                    project,
                    episode_id=sample_id,
                    method_condition_id=method_condition,
                    snapshot_id=snapshot_id,
                    trusted_builder_event_id=_trusted_event_id(store, trusted_event_ref),
                    model_generation_event_id=_trusted_event_id(store, model_event_ref),
                    event_ref_resolver=store.has_event_id,
                )
            else:
                envelope = build_project_envelope(
                    project,
                    episode_id=sample_id,
                    method_condition_id=method_condition,
                    method_policy_sha256=method_policy_sha256(method_condition),
                    snapshot_id=snapshot_id,
                    file_policies={
                        path: {
                            "owner": "model",
                            "origin": "model_generated",
                            "editable": False,
                        }
                        for path in project.files
                    },
                )
            envelope_ref = store.put_validated_json(
                f"project-envelopes/{candidate_id}",
                envelope,
                contract_key="project_envelope",
            )
            selection_event_ref = store.append_event(
                sample_id,
                "terminal_candidate_selected",
                {
                    "candidate_id": candidate_id,
                    "attempt_id": final_attempt_id,
                    "method_condition": method_condition,
                    "selection_rule": "at1" if self.max_attempts == 1 else "at_a",
                    "public_acceptance": _raw_tool_pass_level(
                        tool_results,
                        his_validation,
                    )
                    == "L3",
                },
            )
            requirement_projection_sha256 = self._development_projection_sha256(
                metadata,
                request=request,
                method_condition=method_condition,
            )
            self._terminal_candidate_ref = store.seal_candidate(
                candidate_id,
                project=project,
                project_envelope_ref=envelope_ref,
                requirement_projection_sha256=requirement_projection_sha256,
                creation_event_ref=selection_event_ref,
            )
            self._terminal_candidate_missing_reason = "terminal_candidate_ref_missing"
        except ValueError as exc:
            message = str(exc)
            if "project-package-v1" in message or "manifest.json" in message:
                reason = "noncanonical_project_package"
            elif "composite" in message or "behavior regions" in message:
                reason = "composite_ownership_unavailable"
            else:
                reason = "terminal_candidate_contract_invalid"
            self._terminal_candidate_ref = None
            self._terminal_candidate_missing_reason = (
                f"terminal_candidate_seal_unavailable:{reason}"
            )

    def _finish_cost_attempt(self, *, emergency: bool) -> None:
        ledger = self._active_cost_ledger
        router = self.attempt_cost_router
        if ledger is None or router is None:
            return
        elapsed = max(0.0, time.monotonic() - self._active_cost_started)
        if "wall_time" not in ledger.observed_axes:
            ledger.record_cost(
                stage="attempt_lifecycle",
                visibility_class="accounting",
                status="failed" if emergency else "completed",
                duration_seconds=elapsed,
                cost_delta={"wall_time": elapsed},
                output_artifact_hashes=self._active_candidate_output_hashes,
            )
        missing = set(COST_AXES) - set(ledger.observed_axes)
        if emergency:
            ledger.close(
                unavailable_axes={
                    axis: "attempt_aborted_before_accounting_close" for axis in sorted(missing)
                }
            )
        else:
            ledger.close(zero_axes=sorted(missing))
        summary = reconcile_cost_events(ledger.store, ledger.event_refs)
        self.last_cost_summaries.append(summary)
        router.deactivate(ledger)
        self._active_cost_ledger = None
        self._active_cost_attempt_id = None
        self._active_cost_started = 0.0
        self._active_candidate_output_hashes = ()

    def _reserve_outer_repair_attempt(self) -> None:
        ledger = self._active_cost_ledger
        if ledger is None:
            return
        self._outer_repair_attempts_used += 1
        ledger.reserve(
            "outer_repair_attempts",
            1,
            stage="outer_repair",
            visibility_class="public",
            limit=max(0, self.max_attempts - 1),
            used_after=self._outer_repair_attempts_used,
        )

    def _oracle_strength(
        self,
        project: GeneratedProject,
        sample_dir: Path,
        platform: PlatformProfile,
        task_type: str,
        reference_results: dict[str, ToolResult],
        oracle_bundle: OracleBundle | None = None,
    ) -> dict[str, object] | None:
        if reference_results.get("sim_run", ToolResult("", [], "", None, "", "", 0.0)).status != "passed":
            return None
        mutations = oracle_mutation_projects(project, task_type)
        if not mutations:
            return None
        results: dict[str, str | None] = {}
        details: dict[str, dict[str, object]] = {}
        for name, mutated_project in mutations.items():
            if mutated_project is None:
                results[name] = None
                details[name] = {
                    "outcome": "non_scoreable",
                    "sim_run_status": None,
                    "first_failure_stage": None,
                    "failure_type": None,
                    "mismatch_detail": [],
                    "artifact_dir": None,
                }
                continue
            project_dir = sample_dir / "oracle_mutations" / name
            _write_project(project_dir, mutated_project)
            if oracle_bundle is None:
                mutation_results = self._run_pipeline(mutated_project, project_dir, platform)
            else:
                mutation_results = self._run_pipeline(
                    mutated_project,
                    project_dir,
                    platform,
                    oracle_bundle=oracle_bundle,
                    oracle_evidence_path=project_dir / "eval" / "oracle_evidence.json",
                )
            sim_run = mutation_results.get("sim_run")
            results[name] = sim_run.status if sim_run is not None else None
            details[name] = _write_oracle_mutation_evidence(sample_dir, project_dir, mutation_results)
        strength = build_oracle_strength(True, results, task_type)
        strength["mutation_details"] = details
        return strength

    def _run_development_hidden_evaluation(
        self,
        *,
        sample_id: str,
        request: ProjectRequest,
        metadata: dict[str, Any] | None,
        project: GeneratedProject,
        tool_results: dict[str, ToolResult],
        his_validation: dict[str, Any] | None,
    ) -> dict[str, str] | None:
        authority = self.development_hidden_evaluation_authority
        private_commitment = self.development_hidden_private_commitment
        if authority is None or private_commitment is None:
            return None

        if str((metadata or {}).get("analysis_population", "development")) not in {
            "development",
            "excluded",
        }:
            return None

        if self._development_terminal_selection_ref is None:
            generation = tool_results.get("generation")
            if generation is not None and generation.status != "passed":
                return None
            synth = tool_results.get("synth")
            if synth is None or synth.status != "passed":
                return None
            failed_h_stage = first_failed_h_stage(his_validation)
            if failed_h_stage is not None:
                return None

        method_condition = str((metadata or {}).get("method_condition", "")).strip().upper()
        if not method_condition:
            return None
        try:
            method_policy = method_policy_sha256(method_condition)
        except (KeyError, ValueError):
            return None

        candidate_ref = self._terminal_candidate_ref
        cost_store = self._cost_artifact_store
        if candidate_ref is None or cost_store is None:
            return None
        if authority.candidate_store.root.resolve() != cost_store.root.resolve():
            return None

        requirement_projection_sha256 = self._development_projection_sha256(
            metadata,
            request=request,
            method_condition=method_condition,
        )

        try:
            private_commitment_ref = authority.store_private_commitment(
                sample_id,
                private_commitment,
            )
            hidden_started = time.monotonic()
            try:
                outcome = authority.evaluate_once(
                    terminal_candidate_ref=candidate_ref,
                    private_commitment_ref=private_commitment_ref,
                    public_contract_sha256=method_policy,
                    public_profile_sha256=requirement_projection_sha256,
                    tool_environment_policy_sha256=method_policy,
                    decoding_seed=int.from_bytes(
                        hashlib.sha256(sample_id.encode("utf-8")).digest()[:8],
                        "big",
                    ),
                )
                self._development_hidden_conformance_outcome_ref = (
                    authority.publish_sanitized_outcome(outcome)
                )
            except Exception:
                self._record_hidden_evaluator_cost(hidden_started, status="failed")
                raise
            self._record_hidden_evaluator_cost(hidden_started, status="completed")
            return outcome.to_dict()
        except Exception:
            return None

    def _record_hidden_evaluator_cost(self, started: float, *, status: str) -> None:
        ledger = self._active_cost_ledger
        if ledger is None:
            return
        duration = max(0.0, time.monotonic() - started)
        ledger.record_cost(
            stage="development_hidden_evaluator",
            visibility_class="evaluator_private",
            status=status,
            duration_seconds=duration,
            cost_delta={
                "hidden_evaluator_tool_calls": 1,
                "hidden_evaluator_runtime": duration,
            },
        )

    def _development_projection_sha256(
        self,
        metadata: dict[str, Any] | None,
        *,
        request: ProjectRequest,
        method_condition: str,
    ) -> str:
        pack = (metadata or {}).get("episode_pack")
        if isinstance(pack, dict):
            context = pack.get("public_context")
            public_projection = (
                context.get("public_projection_sha256")
                if isinstance(context, dict)
                else None
            )
            if isinstance(public_projection, str) and len(public_projection) == 64:
                return public_projection

        requirement = (metadata or {}).get("requirement", request.description)
        return _sha256(
            {
                "method_condition": method_condition,
                "task_type": request.task_type,
                "requirement": requirement,
                "project_name": request.project_name,
            }
        )

    def _record_generation_failure(
        self,
        sample_id: str,
        sample_dir: Path,
        request: ProjectRequest,
        exc: Exception,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        infrastructure_reason = _generation_infrastructure_reason(exc)
        boundary_failure = _generation_boundary_failure(exc)
        h_stages_applicable = _h_stages_applicable(metadata, self.project_generator)
        his_validation_failure = (
            exc if h_stages_applicable and isinstance(exc, SystemHisValidationError) else None
        )
        failure_type = (
            infrastructure_reason
            or (boundary_failure or {}).get("failure_type")
            or ("his_validation_failed" if his_validation_failure is not None else None)
            or "generation_failed"
        )
        generation_was_not_run = boundary_failure is not None
        failed_stage_name = "his_validation" if his_validation_failure is not None else "generation"
        failed_project = GeneratedProject(project_name=request.project_name, files={})
        tool_results = {
            failed_stage_name: ToolResult(
                stage=failed_stage_name,
                command=["project_generator"],
                status="not_run" if generation_was_not_run else "failed",
                exit_code=None if generation_was_not_run else 1,
                stdout="",
                stderr=str(exc),
                duration_seconds=0.0,
                skip_reason=failure_type if generation_was_not_run else None,
            )
        }
        diagnosis = {
            "failure_type": failure_type,
            "stage": failed_stage_name,
            "root_cause": str(exc),
            "affected_files": _generation_failure_affected_files(exc),
        }
        if boundary_failure is not None:
            diagnosis.update(boundary_failure)
        elif his_validation_failure is not None:
            diagnosis.update(
                {
                    "failed_h_stage": his_validation_failure.failed_h_stage,
                    "h_stage_diagnostics": list(his_validation_failure.diagnostics),
                    "his_validation": his_validation_failure.report,
                    "repair_scope": "system_his",
                }
            )
        self.recorder.write_attempt(
            sample_id,
            AttemptRecord(
                attempt_id=0,
                generated_project=failed_project,
                tool_results=tool_results,
                diagnosis=diagnosis,
            ),
        )
        l4_open = _l4_open_record(
            tool_results,
            self.enable_openxc7_l4,
            0,
            tool=self.openxc7_tool,
            board_profile=self.openxc7_board_profile,
            core_tool_environment_ref=self.tool_environment_ref,
            l4_tool_environment=self.l4_tool_environment,
            l4_tool_environment_ref=self.l4_tool_environment_ref,
        )
        l4_commercial = _l4_commercial_record(
            tool_results,
            self.enable_vivado_l4,
            tool=self.vivado_tool,
            core_tool_environment_ref=self.tool_environment_ref,
            l4_tool_environment=self.l4_tool_environment,
            l4_tool_environment_ref=self.l4_tool_environment_ref,
        )
        labels = _generation_failure_labels(l4_open, l4_commercial)
        if infrastructure_reason is not None:
            labels["automatic_pass_credit"] = False
            labels["automatic_pass_credit_reason"] = infrastructure_reason
            labels["failure_origin"] = "toolchain_environment_failure"
        elif boundary_failure is not None:
            labels["automatic_pass_credit"] = False
            labels["automatic_pass_credit_reason"] = failure_type
            labels["failure_origin"] = str(boundary_failure["failure_origin"])
            labels["generated_his_no_credit_reason"] = failure_type
            labels["l2_sim_skip_reason"] = failure_type
        elif his_validation_failure is not None:
            if his_validation_failure.candidate_artifact_sha256 is not None:
                self._active_candidate_output_hashes = (
                    his_validation_failure.candidate_artifact_sha256,
                )
            labels.update(h_stage_labels(his_validation_failure.report))
            labels["generated_his_pass_credit"] = False
            labels["generated_his_pass_level"] = "NO_CREDIT_HIS_VALIDATION_FAILED"
            labels["generated_his_no_credit_reason"] = (
                f"{his_validation_failure.failed_h_stage}_failed"
            )
            labels["l2_sim_skip_reason"] = "his_validation_failed"
        if not h_stages_applicable:
            labels.update(h_stage_labels(_not_applicable_h_stage_report()))
            labels["generated_his_pass_credit"] = False
            labels["generated_his_pass_level"] = "NOT_APPLICABLE"
            labels["generated_his_no_credit_reason"] = "method_does_not_emit_system_his"
        labels["failure_type"] = failure_type
        trajectory = _trajectory(sample_id, _stage_entries(0, tool_results, diagnosis, False))
        attempt_measurement = {
            "attempt_id": 0,
            "pass_level": "GEN_FAIL",
            "failure_type": diagnosis["failure_type"],
            "automatic_pass_credit": infrastructure_reason is None and boundary_failure is None,
            "repair_eligible": False,
            "repair_skip_reason": failure_type,
        }
        if infrastructure_reason is not None:
            attempt_measurement["infrastructure_reason"] = infrastructure_reason
        if his_validation_failure is not None:
            attempt_measurement["failed_h_stage"] = his_validation_failure.failed_h_stage
            attempt_measurement["repair_scope"] = "system_his"
        trajectory["measurement"] = build_episode_measurement(
            attempts=[attempt_measurement],
            patches=[],
            l4_open=l4_open,
        )
        self.recorder.write_final(
            sample_id,
            failed_project,
            labels=labels,
            measured_qor=_measured_qor(tool_results, l4_open, l4_commercial),
            tool_versions=self.tool_versions,
            trajectory=trajectory,
        )
        result: dict[str, Any] = {
            "sample_dir": str(sample_dir),
            "pass_level": labels["pass_level"],
            "failure_type": failure_type,
        }
        if boundary_failure is not None:
            for key in ("requirement_id", "questions", "ambiguity_keys", "capability_gaps"):
                if key in boundary_failure:
                    result[key] = boundary_failure[key]
        elif his_validation_failure is not None:
            result["failed_h_stage"] = his_validation_failure.failed_h_stage
        return result

    def _run_pipeline(
        self,
        project: GeneratedProject,
        project_dir: Path,
        platform: PlatformProfile,
        *,
        oracle_bundle: OracleBundle | None = None,
        oracle_evidence_out: list[OracleRunEvidence] | None = None,
        oracle_evidence_path: Path | None = None,
    ) -> dict[str, ToolResult]:
        manifest = resolve_project_manifest(project.files)
        sources = list(manifest.sources)
        testbench_paths = manifest.artifact_paths_by_role.get("candidate_testbench", ())
        testbench = testbench_paths[0] if len(testbench_paths) == 1 else None
        top_module = manifest.top_module

        results: dict[str, ToolResult] = {}
        identifier_issues = check_rtl_identifiers(project, sources)
        results["rtl_identifier_check"] = rtl_identifier_tool_result(identifier_issues)
        if results["rtl_identifier_check"].status != "passed":
            return results

        try:
            yosys_script = build_yosys_script(
                sources,
                top_module,
                manifest.source_languages,
            )
        except UnsupportedSynthesisLanguageError as exc:
            results["synth"] = _unsupported_synth_language_tool_result(exc)
            return results
        except ValueError as exc:
            yosys_input_error: ValueError | None = exc
        else:
            yosys_input_error = None

        results["lint"] = self.command_runner.run(
            ["verilator", "--lint-only", "-Wall", *sources],
            cwd=project_dir,
            stage="lint",
        )
        results["lint"] = _normalize_missing_tool(results["lint"])
        if results["lint"].status != "passed":
            return results

        # Candidate-provided testbenches are smoke diagnostics only. The current
        # package contract has no evaluator-owned trusted harness channel, so
        # these results cannot occupy or grant the formal L2 stages.
        results["sim_compile"] = _not_run_tool_result("sim_compile", "needs_oracle")
        results["sim_run"] = _not_run_tool_result("sim_run", "needs_oracle")

        if not testbench_paths:
            results["candidate_sim_compile"] = _not_run_tool_result(
                "candidate_sim_compile",
                "no_candidate_testbench",
            )
            results["candidate_sim_run"] = _not_run_tool_result(
                "candidate_sim_run",
                "no_candidate_testbench",
            )
        elif len(testbench_paths) != 1:
            results["candidate_sim_compile"] = _not_run_tool_result(
                "candidate_sim_compile",
                "multiple_candidate_testbenches",
            )
            results["candidate_sim_run"] = _not_run_tool_result(
                "candidate_sim_run",
                "multiple_candidate_testbenches",
            )
        else:
            testbench_needs_oracle = _testbench_needs_oracle(project.files[testbench])
            if testbench_needs_oracle:
                results["candidate_sim_compile"] = _not_run_tool_result(
                    "candidate_sim_compile",
                    "needs_oracle",
                )
                results["candidate_sim_run"] = _not_run_tool_result(
                    "candidate_sim_run",
                    "needs_oracle",
                )
            else:
                testbench_issues = check_testbench_static_issues(project.files[testbench])
                results["candidate_testbench_static_check"] = replace(
                    testbench_observation_tool_result(testbench_issues),
                    stage="candidate_testbench_static_check",
                )
                if results["candidate_testbench_static_check"].status != "passed":
                    results["candidate_sim_compile"] = _not_run_tool_result(
                        "candidate_sim_compile",
                        "candidate_static_check_failed",
                    )
                    results["candidate_sim_run"] = _not_run_tool_result(
                        "candidate_sim_run",
                        "candidate_static_check_failed",
                    )
                else:
                    results["candidate_sim_compile"] = self.command_runner.run(
                        ["iverilog", "-g2012", "-o", "sim.out", *sources, testbench],
                        cwd=project_dir,
                        stage="candidate_sim_compile",
                    )
                    results["candidate_sim_compile"] = _normalize_missing_tool(
                        results["candidate_sim_compile"]
                    )
                    if results["candidate_sim_compile"].status != "passed":
                        results["candidate_sim_run"] = _not_run_tool_result(
                            "candidate_sim_run",
                            "candidate_compile_not_passed",
                        )
                    else:
                        if oracle_bundle is None:
                            results["candidate_sim_run"] = self.command_runner.run(
                                ["vvp", "sim.out"],
                                project_dir,
                                stage="candidate_sim_run",
                            )
                            results["candidate_sim_run"] = _normalize_missing_tool(
                                results["candidate_sim_run"]
                            )
                            results["candidate_sim_run"] = _validate_simulation_output(
                                results["candidate_sim_run"]
                            )
                        else:
                            try:
                                evidence, sim_result = run_oracle_scenarios(
                                    self.command_runner,
                                    project_dir,
                                    oracle_bundle,
                                )
                            except Exception as exc:
                                evidence = _oracle_boundary_failure_evidence(
                                    oracle_bundle,
                                    exc,
                                    failure_type="oracle_runner_exception",
                                )
                                sim_result = _oracle_boundary_failure_tool_result(
                                    exc,
                                    "oracle_runner_exception",
                                )
                            else:
                                if oracle_evidence_path is not None:
                                    try:
                                        write_oracle_run_evidence(oracle_evidence_path, evidence)
                                    except Exception as exc:
                                        evidence = _oracle_boundary_failure_evidence(
                                            oracle_bundle,
                                            exc,
                                            failure_type="oracle_evidence_write_failed",
                                            scenario_results=evidence.scenario_results,
                                        )
                                        sim_result = _oracle_boundary_failure_tool_result(
                                            exc,
                                            "oracle_evidence_write_failed",
                                        )
                            results["candidate_sim_run"] = replace(
                                sim_result,
                                stage="candidate_sim_run",
                            )
                            if oracle_evidence_out is not None:
                                oracle_evidence_out.append(evidence)

        if yosys_input_error is not None:
            results["synth"] = _synth_input_tool_result(yosys_input_error)
            return results
        results["synth"] = self.command_runner.run(
            ["yosys", "-p", yosys_script],
            cwd=project_dir,
            stage="synth",
            timeout_seconds=60,
        )
        results["synth"] = _normalize_missing_tool(results["synth"])
        if results["synth"].status != "passed" or not self.enable_openxc7_l4:
            return results

        results["pnr"] = self.command_runner.run(
            _openxc7_pnr_command(project_dir, platform, command_prefix=self.openxc7_command, part=self.openxc7_part),
            cwd=project_dir,
            stage="pnr",
            timeout_seconds=self.openxc7_timeout_seconds,
        )
        results["pnr"] = _normalize_missing_tool(results["pnr"])
        return results


def _write_project(project_dir: Path, project: GeneratedProject) -> None:
    for relative_path, content in project.files.items():
        target = project_file_target(project_dir, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _l0_tool_result(
    result: L0CheckResult,
    *,
    checker: str = "system_his_checker",
) -> ToolResult:
    return ToolResult(
        stage="l0_consistency",
        command=[checker],
        status="failed",
        exit_code=1,
        stdout="\n".join(result.warnings) + ("\n" if result.warnings else ""),
        stderr="\n".join(result.errors) + ("\n" if result.errors else ""),
        duration_seconds=0.0,
    )


def _h_stage_tool_result(report: dict[str, Any]) -> ToolResult:
    failed_stage = first_failed_h_stage(report) or "h_stage"
    diagnostics = report.get(failed_stage, {}).get("diagnostics", [])
    return ToolResult(
        stage="his_validation",
        command=["system_his_h_stage_validator"],
        status="failed",
        exit_code=1,
        stdout="",
        stderr="\n".join(str(item) for item in diagnostics),
        duration_seconds=0.0,
    )


def _oracle_bundle_failure_tool_result(exc: Exception) -> ToolResult:
    return ToolResult(
        stage="oracle_bundle",
        command=["python_reference_builder"],
        status="failed",
        exit_code=1,
        stdout="",
        stderr=str(exc),
        duration_seconds=0.0,
    )


def _oracle_not_run_profile(family_id: str, skip_reason: str) -> dict[str, Any]:
    return {
        "kind": "python_reference",
        "family_id": family_id,
        "status": "not_run",
        "skip_reason": skip_reason,
        "scenario_counts": {},
        "class_status": {},
        "hidden_vectors_exported": False,
    }


def _oracle_error_profile(
    family_id: str,
    exc: Exception,
    *,
    failure_type: str = "oracle_bundle_invalid",
) -> dict[str, Any]:
    return {
        "kind": "python_reference",
        "family_id": family_id,
        "status": "infrastructure_error",
        "failure_origin": "oracle_environment_failure",
        "failure_type": failure_type,
        "diagnostics": [str(exc)],
        "scenario_counts": {},
        "class_status": {},
        "hidden_vectors_exported": False,
    }


def _oracle_profile(
    family_id: str,
    bundle: OracleBundle | None,
    evidence: OracleRunEvidence | None,
) -> dict[str, Any]:
    if bundle is None:
        return _oracle_not_run_profile(family_id, "unsupported_family")
    try:
        profile = sanitize_oracle_profile(bundle)
    except Exception as exc:
        return _oracle_error_profile(family_id, exc, failure_type="oracle_profile_invalid")
    if evidence is None:
        profile.update(
            {
                "status": "infrastructure_error",
                "failure_origin": "oracle_environment_failure",
                "failure_type": "oracle_evidence_missing",
                "class_status": {},
            }
        )
        return profile
    infrastructure = _oracle_evidence_is_infrastructure(evidence)
    profile.update(
        {
            "status": (
                "pass"
                if evidence.status == "passed"
                else "infrastructure_error"
                if infrastructure
                else "fail"
            ),
            "failure_origin": evidence.failure_origin,
            "failure_type": evidence.failure_type,
            "scenario_counts": evidence.scenario_counts(),
            "class_status": {
                scenario_class: evidence.class_status(scenario_class)
                for scenario_class in (
                    "hidden_deterministic",
                    "public_smoke",
                    "randomized_fixed_seed",
                    "stress",
                )
            },
        }
    )
    return profile


def _oracle_boundary_failure_evidence(
    bundle: OracleBundle,
    exc: Exception,
    *,
    failure_type: str,
    scenario_results: tuple[Any, ...] = (),
) -> OracleRunEvidence:
    return OracleRunEvidence(
        family_id=bundle.family_id,
        bundle_sha256=bundle.bundle_sha256,
        status="failed",
        failure_origin="oracle_environment_failure",
        failure_type=failure_type,
        scenario_results=scenario_results,
        diagnostics=(str(exc),),
    )


def _oracle_boundary_failure_tool_result(exc: Exception, failure_type: str) -> ToolResult:
    return ToolResult(
        stage="sim_run",
        command=["python_reference_oracle"],
        status="failed",
        exit_code=1,
        stdout="",
        stderr=f"{failure_type}: {exc}",
        duration_seconds=0.0,
    )


def _oracle_evidence_is_infrastructure(evidence: OracleRunEvidence | None) -> bool:
    return (
        evidence is not None
        and evidence.failure_origin in INFRASTRUCTURE_FAILURE_ORIGINS
    )


def _repair_failure_tool_result(exc: Exception) -> ToolResult:
    return ToolResult(
        stage="repair",
        command=["repairer"],
        status="failed",
        exit_code=1,
        stdout="",
        stderr=str(exc),
        duration_seconds=0.0,
    )


def _generation_failure_tool_result(exc: Exception) -> ToolResult:
    return ToolResult(
        stage="generation",
        command=["project_generator"],
        status="failed",
        exit_code=1,
        stdout="",
        stderr=str(exc),
        duration_seconds=0.0,
    )


def _synth_input_tool_result(exc: Exception) -> ToolResult:
    return ToolResult(
        stage="synth",
        command=["yosys"],
        status="failed",
        exit_code=1,
        stdout="",
        stderr=str(exc),
        duration_seconds=0.0,
    )


def _unsupported_synth_language_tool_result(exc: Exception) -> ToolResult:
    return ToolResult(
        stage="synth",
        command=["yosys"],
        status="not_run",
        exit_code=None,
        stdout="",
        stderr=str(exc),
        duration_seconds=0.0,
        skip_reason="capability_gap",
    )


def _normalize_missing_tool(result: ToolResult) -> ToolResult:
    if result.status != "missing_tool":
        return result
    return replace(
        result,
        status="not_run",
        exit_code=None,
        skip_reason="missing_tool",
    )


def _tool_infrastructure_reason(tool_results: dict[str, ToolResult]) -> str | None:
    for result in tool_results.values():
        if result.stage.startswith("candidate_"):
            continue
        if result.status == "missing_tool" or (
            result.status == "not_run" and result.skip_reason == "missing_tool"
        ):
            return "missing_tool"
    return None


def _tool_non_repairable_reason(tool_results: dict[str, ToolResult]) -> str | None:
    for result in tool_results.values():
        if result.status == "not_run" and result.skip_reason == "capability_gap":
            return "capability_gap"
    return _tool_infrastructure_reason(tool_results)


def _repair_failure_diagnosis(exc: Exception, upstream_diagnosis: dict[str, Any]) -> dict[str, Any]:
    return {
        "failure_type": _repair_failure_type(exc),
        "stage": "repair",
        "root_cause": str(exc),
        "affected_files": _generation_failure_affected_files(exc),
        "upstream_diagnosis": upstream_diagnosis,
    }


def _repair_failure_type(exc: Exception) -> str:
    message = str(exc).lower()
    if "introduced l0 contract violations" in message or "contract changed during rtl repair" in message:
        return "repair_contract_regression"
    return "repair_failed"


def _automatic_pass_credit_reason(patches: list[PatchMetadata]) -> str:
    if any(patch.status == "invalid_edit_surface" for patch in patches):
        return "invalid_edit_surface"
    if any(not patch.tool_result_after for patch in patches):
        return "repair_not_evaluated"
    return "repair_not_verified"


def _public_envelope_failure_reason(exc: ValueError) -> str:
    message = str(exc)
    if "project-package-v1" in message or "manifest.json" in message:
        return "noncanonical_project_package"
    if "composite" in message or "behavior regions" in message:
        return "composite_ownership_unavailable"
    return "project_envelope_contract_invalid"


def _artifact_ref_from_payload(payload: dict[str, Any]) -> ArtifactRef:
    return ArtifactRef(
        key=payload.get("key", payload.get("artifact_key")),
        sha256=payload["sha256"],
        size_bytes=payload["size_bytes"],
        media_type=payload["media_type"],
    )


def _authoritative_public_tool_results(
    outcome: dict[str, Any],
) -> dict[str, ToolResult]:
    stage_names = {
        "l0": "l0_consistency",
        "l1": "lint",
        "public_l2": "public_l2",
        "l3": "synth",
    }
    status_names = {"pass": "passed", "fail": "failed", "not_run": "not_run"}
    results: dict[str, ToolResult] = {}
    for evaluator_stage, tool_stage in stage_names.items():
        stage_outcome = outcome["stage_outcomes"][evaluator_stage]
        status = status_names[stage_outcome["status"]]
        reason = stage_outcome["reason"]
        results[tool_stage] = ToolResult(
            stage=tool_stage,
            command=["development_public_evaluator", evaluator_stage],
            status=status,
            exit_code=0 if status == "passed" else (1 if status == "failed" else None),
            stdout="",
            stderr="",
            duration_seconds=0.0,
            skip_reason=reason if status == "not_run" else None,
        )
    return results


def _authoritative_agent_diagnosis(
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    stage_names = {
        "l0": "l0_consistency",
        "l1": "lint",
        "public_l2": "public_l2",
        "l3": "synth",
    }
    return {**diagnosis, "stage": stage_names[diagnosis["stage"]]}


def _generation_failure_affected_files(exc: Exception) -> list[str]:
    message = str(exc).lower()
    if "system-his" in message or "system_his" in message:
        return ["system_his.json"]
    return []


def _diagnose_first_failure(
    tool_results: dict[str, ToolResult],
    l0_result: L0CheckResult | None = None,
    *,
    system_his_applicable: bool = True,
) -> dict[str, Any] | None:
    for result in tool_results.values():
        if result.status != "passed":
            if result.stage.startswith("candidate_"):
                continue
            if result.status in {"not_run", "missing_tool"}:
                continue
            if result.stage == "pnr" and _is_l4_non_model_not_run_result(result):
                continue
            log_text = f"{result.stdout}\n{result.stderr}"
            if result.stage == "l0_consistency":
                return {
                    "failure_type": "l0_contract_violation",
                    "stage": result.stage,
                    "root_cause": log_text.strip() or result.status,
                    "affected_files": (
                        ["system_his.json", "manifest.json"]
                        if system_his_applicable
                        else ["manifest.json"]
                    ),
                    "l0_errors": [] if l0_result is None else l0_result.errors,
                    "l0_warnings": [] if l0_result is None else l0_result.warnings,
                    "structured_diagnosis": _structured_diagnosis(
                        result,
                        log_text,
                        failure_type="l0_contract_violation",
                    ),
                }
            if result.stage == "his_validation":
                return {
                    "failure_type": "his_validation_failed",
                    "stage": result.stage,
                    "root_cause": log_text.strip() or result.status,
                    "affected_files": ["system_his.json"],
                    "structured_diagnosis": _structured_diagnosis(
                        result,
                        log_text,
                        failure_type="his_validation_failed",
                    ),
                }
            return {
                "failure_type": classify_failure(log_text),
                "stage": result.stage,
                "root_cause": log_text.strip() or result.status,
                "affected_files": [],
                "tool": result.command[0] if result.command else result.stage,
                "tool_status": result.status,
                "structured_diagnosis": _structured_diagnosis(result, log_text),
            }
    return None


def _system_his_failure_diagnosis(report: dict[str, Any]) -> dict[str, Any]:
    failed_stage = first_failed_h_stage(report) or "h0"
    stage_report = report.get(failed_stage, {})
    diagnostics = (
        list(stage_report.get("diagnostics", []))
        if isinstance(stage_report, dict)
        else []
    )
    detail = "; ".join(str(item) for item in diagnostics) or "unknown validation error"
    return {
        "failure_type": "his_validation_failed",
        "stage": "his_validation",
        "root_cause": f"System-HIS {failed_stage.upper()} validation failed: {detail}",
        "affected_files": ["system_his.json"],
        "failed_h_stage": failed_stage,
        "h_stage_diagnostics": diagnostics,
        "his_validation": report,
        "repair_scope": "system_his",
    }


def _write_oracle_mutation_evidence(
    sample_dir: Path,
    project_dir: Path,
    tool_results: dict[str, ToolResult],
) -> dict[str, object]:
    eval_dir = project_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    for stage, result in tool_results.items():
        log_text = result.stdout
        if result.stderr:
            log_text = f"{log_text}{result.stderr}"
        (eval_dir / f"{stage}.log").write_text(log_text, encoding="utf-8")
        (eval_dir / f"{stage}.json").write_text(
            json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    diagnosis = _diagnose_first_failure(tool_results)
    if diagnosis is not None:
        (project_dir / "diagnosis.json").write_text(
            json.dumps(diagnosis, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    sim_run = tool_results.get("sim_run")
    sim_status = sim_run.status if sim_run is not None else None
    outcome = "non_scoreable"
    if sim_status == "failed":
        outcome = "killed"
    elif sim_status == "passed":
        outcome = "survived"
    structured = diagnosis.get("structured_diagnosis", {}) if diagnosis is not None else {}
    return {
        "outcome": outcome,
        "sim_run_status": sim_status,
        "first_failure_stage": diagnosis.get("stage") if diagnosis is not None else None,
        "failure_type": diagnosis.get("failure_type") if diagnosis is not None else None,
        "mismatch_detail": structured.get("mismatch_detail", []) if isinstance(structured, dict) else [],
        "artifact_dir": project_dir.relative_to(sample_dir).as_posix(),
    }


def _structured_diagnosis(
    result: ToolResult,
    log_text: str,
    failure_type: str | None = None,
) -> dict[str, Any]:
    trace = parse_semantic_trace(log_text)
    has_trace = any(trace.values())
    failure_type = failure_type or classify_failure(log_text)
    return {
        "failure_type": failure_type,
        "warnings": parse_tool_warnings(log_text),
        "mismatch_detail": parse_test_fail_mismatches(log_text),
        "semantic_trace": diagnose_semantic_trace(trace) if has_trace else {},
        "resource_detail": parse_yosys_stats(log_text) if result.stage == "synth" else {},
        "bram_miss": False,
        "l4_failure_family": failure_type if result.stage == "pnr" else None,
    }


def _validate_simulation_output(result: ToolResult) -> ToolResult:
    if result.status != "passed":
        return result
    log_text = f"{result.stdout}\n{result.stderr}"
    if "TEST_FAIL" in log_text or "TEST_PASS" not in log_text:
        reason = "Simulation did not report TEST_PASS"
        if "TEST_FAIL" in log_text:
            reason = "Simulation reported TEST_FAIL"
        stderr = result.stderr
        if stderr:
            stderr = f"{stderr}\n{reason}\n"
        else:
            stderr = f"{reason}\n"
        return replace(result, status="failed", stderr=stderr)
    return result


def _testbench_needs_oracle(testbench: str) -> bool:
    return "SR2FPGA_ORACLE_STATUS: needs_oracle" in testbench


def _not_run_tool_result(stage: str, skip_reason: str) -> ToolResult:
    return ToolResult(
        stage=stage,
        command=[],
        status="not_run",
        exit_code=None,
        stdout="",
        stderr=f"{skip_reason}\n",
        duration_seconds=0.0,
        skip_reason=skip_reason,
    )


def _measured_qor(
    tool_results: dict[str, ToolResult],
    l4_open: dict[str, Any],
    l4_commercial: dict[str, Any] | None = None,
) -> dict[str, Any]:
    synth = tool_results.get("synth")
    if synth is None or synth.status != "passed":
        measured_qor = _empty_measured_qor()
    else:
        measured_qor = parse_yosys_stats(f"{synth.stdout}\n{synth.stderr}")
    measured_qor["l4_openxc7"] = {
        key: l4_open.get(key)
        for key in (
            "status",
            "skip_reason",
            "tool",
            "board_profile",
            "constraint_scope",
            "board_constraints_applied",
            "wns_ns",
            "fmax_mhz",
            "lut",
            "ff",
            "bram",
            "dsp",
            "drc_warnings",
            "critical_warnings",
            "runtime_sec",
            "report_paths",
            "provenance",
        )
    }
    measured_qor["l4_commercial"] = dict(l4_commercial or _l4_commercial_record(tool_results, False))
    if l4_open["status"] == "pass":
        measured_qor.update({key: l4_open[key] for key in ("wns_ns", "fmax_mhz", "lut", "ff", "bram", "dsp")})
    return measured_qor


def _generation_failure_labels(
    l4_open: dict[str, Any], l4_commercial: dict[str, Any] | None = None
) -> dict[str, Any]:
    l4_commercial = l4_commercial or _l4_commercial_record({}, False)
    return {
        "pass_level": "GEN_FAIL",
        "highest_official_level": "GEN_FAIL",
        "generated_his_pass_credit": False,
        "generated_his_pass_level": "NO_CREDIT_GENERATION_FAILED",
        "generated_his_no_credit_reason": "generation_failed",
        "h0_status": "not_run",
        "h1_status": "not_run",
        "h2_status": "not_run",
        "h3_status": "not_run",
        "h0_pass": False,
        "h1_pass": False,
        "h2_pass": False,
        "h3_pass": False,
        "l2_sim_status": "not_run",
        "l2_sim_skip_reason": "generation_failed",
        "l4_open_status": l4_open["status"],
        "l4_open_pass": False,
        "l4_open_skip_reason": l4_open["skip_reason"],
        "l4_commercial_status": l4_commercial["status"],
        "l4_commercial_pass": False,
        "l4_commercial_skip_reason": l4_commercial["skip_reason"],
        "l4_agreement_class": "not_applicable",
        "checks": {
            "generation_complete": False,
            "l0_complete": False,
            "l1_lint_pass": False,
            "l2_sim_pass": False,
            "l3_synth_pass": False,
            "l4_lite_timing_pass": False,
            "l4_open_pass": False,
            "l4_commercial_pass": False,
            "l4_commercial_tool": l4_commercial["tool"],
            "l4_agreement_class": "not_applicable",
        },
        "final_attempt_id": 0,
        "failure_count": 1,
    }


def _labels(
    tool_results: dict[str, ToolResult],
    l4_open: dict[str, Any],
    final_attempt_id: int,
    failure_count: int,
    his_validation: dict[str, Any] | None = None,
    oracle_strength: dict[str, object] | None = None,
    enforce_oracle_readiness: bool = False,
    expected_bram: int = 0,
    l4_commercial: dict[str, Any] | None = None,
    oracle_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    l4_commercial = l4_commercial or _l4_commercial_record(tool_results, False)
    l4_agreement_class = _l4_agreement_class(l4_open, l4_commercial)
    failed_h_stage = first_failed_h_stage(his_validation) if his_validation is not None else None
    blocked_by_h_stage = failed_h_stage is not None
    generation_failed = (
        tool_results.get("generation") is not None
        and tool_results["generation"].status != "passed"
    )
    l0_pass = not (
        tool_results.get("l0_consistency") is not None and tool_results["l0_consistency"].status != "passed"
    ) and not blocked_by_h_stage and not generation_failed
    lint_pass = not blocked_by_h_stage and tool_results.get("lint") is not None and tool_results["lint"].status == "passed"
    sim_compile_pass = (
        tool_results.get("sim_compile") is not None and tool_results["sim_compile"].status == "passed"
    )
    sim_run_pass = tool_results.get("sim_run") is not None and tool_results["sim_run"].status == "passed"
    l2_sim_status, l2_sim_skip_reason = _l2_sim_outcome(tool_results)
    synth_pass = tool_results.get("synth") is not None and tool_results["synth"].status == "passed"
    pnr_pass = l4_open["status"] == "pass"
    oracle_profile = oracle_profile or _oracle_not_run_profile("", "disabled_by_config")
    independent_oracle_status = str(oracle_profile.get("status", "not_run"))
    oracle_infrastructure_error = independent_oracle_status == "infrastructure_error"
    tool_infrastructure_reason = _tool_infrastructure_reason(tool_results)
    tool_infrastructure_error = tool_infrastructure_reason is not None

    raw_tool_pass_level = _raw_tool_pass_level(tool_results, his_validation)
    if lint_pass and sim_compile_pass and sim_run_pass and synth_pass and pnr_pass:
        raw_tool_pass_level = "L4"

    pass_level = raw_tool_pass_level
    oracle_not_ready = (
        enforce_oracle_readiness
        and oracle_strength is not None
        and oracle_strength.get("line_a_ready") is False
    )
    if oracle_not_ready and raw_tool_pass_level in {"L3", "L4"}:
        pass_level = "ORACLE_NOT_READY"
    if oracle_infrastructure_error:
        pass_level = "ORACLE_ERROR"

    labels = {
        "pass_level": pass_level,
        "highest_official_level": pass_level,
        "independent_oracle_status": independent_oracle_status,
        "failure_origin": (
            "toolchain_environment_failure"
            if tool_infrastructure_error
            else oracle_profile.get("failure_origin")
        ),
        "automatic_pass_credit": not (
            oracle_infrastructure_error or tool_infrastructure_error
        ),
        "l2_sim_status": l2_sim_status,
        "l2_sim_skip_reason": l2_sim_skip_reason,
        "l4_open_status": l4_open["status"],
        "l4_open_pass": pnr_pass,
        "l4_open_skip_reason": l4_open["skip_reason"],
        "l4_commercial_status": l4_commercial["status"],
        "l4_commercial_pass": l4_commercial["status"] == "pass",
        "l4_commercial_skip_reason": l4_commercial["skip_reason"],
        "l4_agreement_class": l4_agreement_class,
        "checks": {
            "l0_complete": l0_pass,
            "l1_lint_pass": lint_pass,
            "l2_sim_pass": lint_pass and sim_compile_pass and sim_run_pass,
            # The current independent bundle is diagnostic and is not the
            # evaluator-owned one-shot hidden authority.
            "l2_hidden_pass": False,
            "l2_randomized_pass": False,
            "l2_stress_pass": False,
            "l2_coverage_profile": (
                "independent_python_reference" if independent_oracle_status != "not_run" else None
            ),
            "l2_scenario_counts": dict(oracle_profile.get("scenario_counts", {})),
            "l3_synth_pass": synth_pass,
            "l4_lite_timing_pass": pnr_pass,
            "l4_open_pass": pnr_pass,
            "l4_open_tool": l4_open["tool"],
            "l4_commercial_pass": l4_commercial["status"] == "pass",
            "l4_commercial_tool": l4_commercial["tool"],
            "l4_agreement_class": l4_agreement_class,
        },
        "final_attempt_id": final_attempt_id,
        "failure_count": failure_count,
        "l1_warnings": _tool_warnings(tool_results.get("lint")),
        "l2_mismatch_detail": _tool_mismatches(tool_results.get("sim_run")),
        "l3_warnings": _tool_warnings(tool_results.get("synth")),
        "l3_bram_miss": synth_pass and expected_bram > 0 and parse_yosys_stats(
            _tool_log(tool_results.get("synth"))
        )["bram"] == 0,
        "l4_failure_family": l4_open.get("failure_family"),
    }
    if his_validation is not None:
        labels.update(h_stage_labels(his_validation))
    if oracle_strength is not None:
        labels.update(
            {
                "raw_tool_pass_level": raw_tool_pass_level,
                "oracle_strength_line_a_ready": oracle_strength.get("line_a_ready"),
                "oracle_strength_reference_pass": oracle_strength.get("reference_pass"),
                "oracle_strength_mutation_score": oracle_strength.get("mutation_score"),
                "oracle_strength_threshold": oracle_strength.get("threshold"),
            }
        )
    if failed_h_stage is not None:
        labels["generated_his_pass_credit"] = False
        labels["generated_his_pass_level"] = "NO_CREDIT_HIS_VALIDATION_FAILED"
        labels["generated_his_no_credit_reason"] = f"{failed_h_stage}_failed"
    elif _h_stages_not_applicable(his_validation):
        labels["generated_his_pass_credit"] = False
        labels["generated_his_pass_level"] = "NOT_APPLICABLE"
        labels["generated_his_no_credit_reason"] = "method_does_not_emit_system_his"
    elif labels.setdefault("generated_his_pass_credit", True):
        labels["generated_his_pass_level"] = pass_level
        labels["generated_his_no_credit_reason"] = None
    else:
        labels["generated_his_pass_level"] = "NO_CREDIT_ORACLE_FALLBACK"
        labels["generated_his_no_credit_reason"] = "oracle_fallback"
    return labels


def _l2_sim_outcome(tool_results: dict[str, ToolResult]) -> tuple[str, str | None]:
    sim_compile = tool_results.get("sim_compile")
    sim_run = tool_results.get("sim_run")
    if sim_compile is None:
        return "not_run", "not_reached"
    if sim_compile.status == "not_run":
        return "not_run", sim_compile.skip_reason or "not_reached"
    if sim_compile.status != "passed":
        return "fail", None
    if sim_run is None:
        return "not_run", "not_reached"
    if sim_run.status == "not_run":
        return "not_run", sim_run.skip_reason or "not_reached"
    if sim_run.status != "passed":
        return "fail", None
    return "pass", None


def _raw_tool_pass_level(
    tool_results: dict[str, ToolResult],
    his_validation: dict[str, Any] | None,
) -> str:
    """Return the highest H/L0-L3 level reached before optional physical implementation."""
    generation = tool_results.get("generation")
    if generation is not None and generation.status != "passed":
        return "GEN_FAIL"
    failed_h_stage = first_failed_h_stage(his_validation) if his_validation is not None else None
    if failed_h_stage:
        return f"{failed_h_stage.upper()}_FAIL"
    l0 = tool_results.get("l0_consistency")
    if l0 is not None and l0.status != "passed":
        return "L0_FAIL"
    lint = tool_results.get("lint")
    if lint is None or lint.status != "passed":
        return "L0"
    sim_compile = tool_results.get("sim_compile")
    sim_run = tool_results.get("sim_run")
    if (
        sim_compile is None
        or sim_compile.status != "passed"
        or sim_run is None
        or sim_run.status != "passed"
    ):
        return "L1"
    synth = tool_results.get("synth")
    if synth is None or synth.status != "passed":
        return "L2"
    return "L3"


def _repair_eligibility(
    *,
    diagnosis: dict[str, Any] | None,
    h_stage_failed: bool,
    oracle_infrastructure_failure: bool,
    has_repairer: bool,
    attempt_id: int,
    max_attempts: int,
) -> tuple[bool, str | None]:
    if oracle_infrastructure_failure:
        return False, "infrastructure_failure"
    if diagnosis is None:
        return False, "initial_or_current_attempt_passed"
    if h_stage_failed:
        return False, "h_stage_failed"
    if not has_repairer:
        return False, "no_repairer"
    if attempt_id + 1 >= max_attempts:
        return False, "repair_budget_exhausted"
    return True, None


def _generation_infrastructure_reason(exc: Exception) -> str | None:
    text = str(exc).lower()
    markers = (
        "api request failed",
        "api request timed out",
        "api response read timed out",
        "streaming response error",
        "streaming response contained no text",
        "overloaded_error",
        "provider unavailable",
        "connection refused",
        "connection reset",
        "temporary failure",
    )
    return "provider_infrastructure_failure" if any(marker in text for marker in markers) else None


def _requirement_boundary_stop(
    metadata: dict[str, Any] | None,
) -> RequirementClarificationRequired | RequirementCapabilityGapError | None:
    """Translate an evaluator-side boundary decision without recomputing it."""

    if metadata is None or "requirement_boundary" not in metadata:
        return None
    boundary = metadata["requirement_boundary"]
    if not isinstance(boundary, dict):
        raise _RequirementBoundaryMetadataError(
            "requirement_boundary metadata must be a JSON object"
        )
    if boundary.get("boundary_version") != "requirement-boundary-v1":
        raise _RequirementBoundaryMetadataError(
            "requirement_boundary metadata has an unsupported boundary_version"
        )
    requirement_id = boundary.get("requirement_id")
    if not isinstance(requirement_id, str) or not requirement_id:
        raise _RequirementBoundaryMetadataError(
            "requirement_boundary metadata requires a non-empty requirement_id"
        )
    disposition = boundary.get("disposition")
    if disposition == "ready":
        pack = metadata.get("episode_pack")
        if pack is not None:
            errors = validate_episode_pack(pack)
            if errors:
                raise _RequirementBoundaryMetadataError(
                    "episode_pack metadata is invalid: " + "; ".join(errors)
                )
            public_context = pack.get("public_context", {})
            if public_context.get("requirement_id") != requirement_id:
                raise _RequirementBoundaryMetadataError(
                    "episode_pack requirement_id does not match requirement_boundary"
                )
        return None
    if "episode_pack" in metadata:
        raise _RequirementBoundaryMetadataError(
            "non-ready requirement metadata must not contain an episode_pack"
        )
    if disposition == "needs_clarification":
        ambiguity_keys = _boundary_string_tuple(boundary, "clarification_fact_ids")
        questions = _boundary_string_tuple(boundary, "clarification_questions")
        if not ambiguity_keys or len(ambiguity_keys) != len(questions):
            raise _RequirementBoundaryMetadataError(
                "needs_clarification requires aligned clarification fact IDs and questions"
            )
        envelope = RequirementEnvelope(
            requirement_id=requirement_id,
            raw_requirement="",
            facts=(),
            capability_labels=(),
            critical_ambiguities=tuple(
                CriticalAmbiguity(key, question, "recorded requirement boundary decision")
                for key, question in zip(ambiguity_keys, questions)
            ),
        )
        return RequirementClarificationRequired(envelope, ambiguity_keys)
    if disposition == "capability_gap":
        capability_gaps = _boundary_string_tuple(boundary, "capability_gap_ids")
        if not capability_gaps:
            raise _RequirementBoundaryMetadataError(
                "capability_gap requires at least one capability_gap_id"
            )
        return RequirementCapabilityGapError(requirement_id, capability_gaps)
    raise _RequirementBoundaryMetadataError(
        "requirement_boundary metadata disposition must be ready, "
        "needs_clarification, or capability_gap"
    )


def _boundary_string_tuple(boundary: dict[str, Any], key: str) -> tuple[str, ...]:
    value = boundary.get(key)
    if not isinstance(value, (list, tuple)) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise _RequirementBoundaryMetadataError(
            f"requirement_boundary metadata {key} must be a list of non-empty strings"
        )
    return tuple(value)


def _generation_boundary_failure(exc: Exception) -> dict[str, Any] | None:
    if isinstance(exc, _RequirementBoundaryMetadataError):
        return {
            "failure_type": "invalid_requirement_boundary_metadata",
            "failure_origin": "requirement_boundary",
        }
    if isinstance(exc, RequirementClarificationRequired):
        return {
            "failure_type": "requirement_clarification_required",
            "failure_origin": "requirement_boundary",
            "requirement_id": exc.requirement_id,
            "ambiguity_keys": list(exc.ambiguity_keys),
            "questions": list(exc.questions),
        }
    if isinstance(exc, RequirementCapabilityGapError):
        return {
            "failure_type": "capability_gap",
            "failure_origin": "backend_capability_gap",
            "requirement_id": exc.requirement_id,
            "capability_gaps": list(exc.capability_gaps),
        }
    return None


def _l4_agreement_class(l4_open: dict[str, Any], l4_commercial: dict[str, Any]) -> str:
    open_status = l4_open.get("status")
    commercial_status = l4_commercial.get("status")
    if open_status not in {"pass", "fail"} or commercial_status not in {"pass", "fail"}:
        return "not_applicable"
    if open_status == commercial_status:
        return f"both_{open_status}"
    return f"open_{open_status}_commercial_{commercial_status}"


def _tool_log(result: ToolResult | None) -> str:
    return "" if result is None else f"{result.stdout}\n{result.stderr}"


def _tool_warnings(result: ToolResult | None) -> list[dict[str, str]]:
    return parse_tool_warnings(_tool_log(result))


def _tool_mismatches(result: ToolResult | None) -> list[dict[str, object]]:
    return parse_test_fail_mismatches(_tool_log(result))


def _expected_bram(project: GeneratedProject) -> int:
    predicted_qor = project.files.get("reports/predicted_qor.json")
    if predicted_qor is not None:
        try:
            payload = json.loads(predicted_qor)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("bram"), int):
            return payload["bram"]
    system_his = project.files.get("system_his.json")
    if system_his is not None:
        try:
            payload = json.loads(system_his)
        except json.JSONDecodeError:
            payload = None
        expected = payload.get("resources", {}).get("expected", {}) if isinstance(payload, dict) else {}
        if isinstance(expected, dict) and isinstance(expected.get("bram"), int):
            return expected["bram"]
    return 0


def _empty_measured_qor() -> dict[str, Any]:
    return {"lut": 0, "ff": 0, "bram": 0, "dsp": 0, "cell_count": 0, "cell_breakdown": {}}


def _sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _trusted_event_id(store: ArtifactStore, reference: ArtifactRef) -> str:
    event = json.loads(store.read_verified(reference))
    event_id = event.get("event_id") if isinstance(event, dict) else None
    if not isinstance(event_id, str) or not store.has_event_id(event_id):
        raise ValueError("trusted event reference does not resolve")
    return event_id


def _openxc7_wrapper_report_paths(project_dir: Path | None, attempt_id: int) -> list[str]:
    wrapper_reports = ("openxc7_nextpnr.log", "openxc7_report.json")
    return [
        f"attempts/attempt_{attempt_id:03d}/generated_project/eval/{name}"
        for name in wrapper_reports
        if project_dir is not None and (project_dir / "eval" / name).is_file()
    ]


def _l4_open_record(
    tool_results: dict[str, ToolResult],
    enabled: bool,
    attempt_id: int,
    tool: str,
    board_profile: str,
    project_dir: Path | None = None,
    core_tool_environment_ref: dict[str, Any] | None = None,
    l4_tool_environment: dict[str, Any] | None = None,
    l4_tool_environment_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "tool": tool,
        "board_profile": board_profile,
        "constraint_scope": "logical_only",
        "board_constraints_applied": False,
        "status": "not_run",
        "skip_reason": None,
        "wns_ns": None,
        "fmax_mhz": None,
        "lut": None,
        "ff": None,
        "bram": None,
        "dsp": None,
        "drc_warnings": [],
        "critical_warnings": [],
        "runtime_sec": None,
        "report_paths": [],
    }
    if not enabled:
        record["skip_reason"] = "disabled_by_config"
        return _finalize_l4_qor_record(
            record,
            lane="l4_open",
            source_stage="pnr",
            source_stage_status="not_run",
            project_dir=project_dir,
            attempt_id=attempt_id,
            core_tool_environment_ref=core_tool_environment_ref,
            l4_tool_environment=l4_tool_environment,
            l4_tool_environment_ref=l4_tool_environment_ref,
        )
    synth = tool_results.get("synth")
    if synth is None or synth.status != "passed":
        record["skip_reason"] = "l3_failed"
        return _finalize_l4_qor_record(
            record,
            lane="l4_open",
            source_stage="pnr",
            source_stage_status="not_run",
            project_dir=project_dir,
            attempt_id=attempt_id,
            core_tool_environment_ref=core_tool_environment_ref,
            l4_tool_environment=l4_tool_environment,
            l4_tool_environment_ref=l4_tool_environment_ref,
        )
    pnr = tool_results.get("pnr")
    if pnr is None:
        record["skip_reason"] = "not_selected_by_policy"
        return _finalize_l4_qor_record(
            record,
            lane="l4_open",
            source_stage="pnr",
            source_stage_status="not_run",
            project_dir=project_dir,
            attempt_id=attempt_id,
            core_tool_environment_ref=core_tool_environment_ref,
            l4_tool_environment=l4_tool_environment,
            l4_tool_environment_ref=l4_tool_environment_ref,
        )
    record["runtime_sec"] = pnr.duration_seconds
    record["report_paths"] = _openxc7_wrapper_report_paths(project_dir, attempt_id)
    if pnr.status == "passed":
        record["status"] = "pass"
        record.update(parse_openxc7_report(f"{pnr.stdout}\n{pnr.stderr}"))
        if not record["report_paths"]:
            record["report_paths"] = [
                f"attempts/attempt_{attempt_id:03d}/eval/pnr.log",
                f"attempts/attempt_{attempt_id:03d}/eval/pnr.json",
            ]
    elif pnr.status == "missing_tool":
        record["skip_reason"] = "missing_tool"
    elif pnr.status == "timeout":
        record["skip_reason"] = "tool_timeout"
    elif _is_l4_toolchain_environment_failure(pnr):
        record["skip_reason"] = "toolchain_environment_failure"
    else:
        record["status"] = "fail"
        record["failure_family"] = classify_failure(f"{pnr.stdout}\n{pnr.stderr}")
    return _finalize_l4_qor_record(
        record,
        lane="l4_open",
        source_stage="pnr",
        source_stage_status=_tool_result_stage_status(pnr),
        project_dir=project_dir,
        attempt_id=attempt_id,
        core_tool_environment_ref=core_tool_environment_ref,
        l4_tool_environment=l4_tool_environment,
        l4_tool_environment_ref=l4_tool_environment_ref,
        fallback_relative_paths=(
            f"attempts/attempt_{attempt_id:03d}/eval/pnr.log",
            f"attempts/attempt_{attempt_id:03d}/eval/pnr.json",
        ),
    )


def _l4_commercial_record(
    tool_results: dict[str, ToolResult],
    enabled: bool,
    *,
    tool: str = "vivado",
    core_tool_environment_ref: dict[str, Any] | None = None,
    l4_tool_environment: dict[str, Any] | None = None,
    l4_tool_environment_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "tool": tool,
        "status": "not_run",
        "skip_reason": None,
        "constraint_scope": "logical_only",
        "board_constraints_applied": False,
        "official_board_ready": False,
        "wns_ns": None,
        "fmax_mhz": None,
        "lut": None,
        "ff": None,
        "bram": None,
        "dsp": None,
        "drc_warnings": [],
        "expected_board_drc_exceptions": [],
        "invalidating_critical_warnings": [],
        "methodology_warnings": [],
        "runtime_sec": None,
        "report_paths": [],
    }
    if not enabled:
        record["skip_reason"] = "disabled_by_config"
    elif tool_results.get("synth") is None or tool_results["synth"].status != "passed":
        record["skip_reason"] = "l3_failed"
    else:
        record["skip_reason"] = "not_selected_by_policy"
    return _finalize_l4_qor_record(
        record,
        lane="l4_commercial",
        source_stage="l4_commercial",
        source_stage_status="not_run",
        project_dir=None,
        attempt_id=0,
        core_tool_environment_ref=core_tool_environment_ref,
        l4_tool_environment=l4_tool_environment,
        l4_tool_environment_ref=l4_tool_environment_ref,
    )


def _run_l4_commercial_reference(
    tool_results: dict[str, ToolResult],
    enabled: bool,
    *,
    project_dir: Path,
    attempt_id: int,
    tool: str,
    vivado_command: str,
    part: str,
    target_period_ns: float,
    timeout_seconds: int,
    core_tool_environment_ref: dict[str, Any] | None = None,
    l4_tool_environment: dict[str, Any] | None = None,
    l4_tool_environment_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = _l4_commercial_record(
        tool_results,
        enabled,
        tool=tool,
        core_tool_environment_ref=core_tool_environment_ref,
        l4_tool_environment=l4_tool_environment,
        l4_tool_environment_ref=l4_tool_environment_ref,
    )
    if record["skip_reason"] != "not_selected_by_policy":
        return record
    try:
        report = run_vivado_reference(
            project_dir,
            vivado_command=os.environ.get("SR2FPGA_VIVADO_COMMAND") or vivado_command,
            part=part,
            target_period_ns=target_period_ns,
            timeout_seconds=timeout_seconds,
        )
    except FileNotFoundError:
        record["skip_reason"] = "missing_tool"
        return _finalize_l4_qor_record(
            record,
            lane="l4_commercial",
            source_stage="l4_commercial",
            source_stage_status="infrastructure_error",
            project_dir=project_dir,
            attempt_id=attempt_id,
            core_tool_environment_ref=core_tool_environment_ref,
            l4_tool_environment=l4_tool_environment,
            l4_tool_environment_ref=l4_tool_environment_ref,
        )
    except subprocess.TimeoutExpired:
        record["skip_reason"] = "tool_timeout"
        return _finalize_l4_qor_record(
            record,
            lane="l4_commercial",
            source_stage="l4_commercial",
            source_stage_status="infrastructure_error",
            project_dir=project_dir,
            attempt_id=attempt_id,
            core_tool_environment_ref=core_tool_environment_ref,
            l4_tool_environment=l4_tool_environment,
            l4_tool_environment_ref=l4_tool_environment_ref,
        )
    except OSError:
        record["skip_reason"] = "toolchain_environment_failure"
        return _finalize_l4_qor_record(
            record,
            lane="l4_commercial",
            source_stage="l4_commercial",
            source_stage_status="infrastructure_error",
            project_dir=project_dir,
            attempt_id=attempt_id,
            core_tool_environment_ref=core_tool_environment_ref,
            l4_tool_environment=l4_tool_environment,
            l4_tool_environment_ref=l4_tool_environment_ref,
        )

    for key in record:
        if key in report:
            record[key] = report[key]
    status = report.get("status")
    record["status"] = status if status in {"pass", "fail"} else "fail"
    record["skip_reason"] = None
    record["report_paths"] = [
        f"attempts/attempt_{attempt_id:03d}/generated_project/{path}"
        for path in report.get("report_paths", [])
        if isinstance(path, str)
    ]
    return _finalize_l4_qor_record(
        record,
        lane="l4_commercial",
        source_stage="l4_commercial",
        source_stage_status="pass" if record["status"] == "pass" else "fail",
        project_dir=project_dir,
        attempt_id=attempt_id,
        core_tool_environment_ref=core_tool_environment_ref,
        l4_tool_environment=l4_tool_environment,
        l4_tool_environment_ref=l4_tool_environment_ref,
    )


def _tool_result_stage_status(result: ToolResult) -> str:
    if result.status == "passed":
        return "pass"
    if result.status == "failed":
        return "fail"
    if result.status in {"missing_tool", "timeout"}:
        return "infrastructure_error"
    return "not_run"


def _finalize_l4_qor_record(
    record: dict[str, Any],
    *,
    lane: str,
    source_stage: str,
    source_stage_status: str,
    project_dir: Path | None,
    attempt_id: int,
    core_tool_environment_ref: dict[str, Any] | None,
    l4_tool_environment: dict[str, Any] | None = None,
    l4_tool_environment_ref: dict[str, Any] | None = None,
    fallback_relative_paths: tuple[str, ...] = (),
) -> dict[str, Any]:
    relative_paths = {
        path
        for path in record.get("report_paths", [])
        if isinstance(path, str) and path
    }
    relative_paths.update(fallback_relative_paths)
    raw_evidence_refs = _l4_raw_evidence_refs(project_dir, relative_paths)
    incomplete_reasons: list[str] = []
    l4_tool_version_status = "not_run"
    l4_tool_version = None
    if source_stage_status == "not_run":
        incomplete_reasons.append("stage_not_run")
    else:
        l4_tool_version = _captured_l4_tool_version(l4_tool_environment, lane)
        if l4_tool_version is None:
            l4_tool_version_status = "not_captured"
            incomplete_reasons.append("l4_tool_version_not_captured")
        else:
            l4_tool_version_status = "captured"
        if not raw_evidence_refs:
            incomplete_reasons.append("raw_evidence_missing")
    if core_tool_environment_ref is None:
        incomplete_reasons.append("core_tool_environment_ref_missing")
    if l4_tool_environment_ref is None:
        incomplete_reasons.append("l4_tool_environment_ref_missing")
    provenance_status = "incomplete" if incomplete_reasons else "complete"
    provenance = {
        "contract_version": "development-l4-qor-provenance-v1",
        "lane": lane,
        "source_stage": source_stage,
        "source_stage_status": source_stage_status,
        "core_tool_environment_ref": (
            dict(core_tool_environment_ref)
            if core_tool_environment_ref is not None
            else None
        ),
        "l4_tool_environment_ref": (
            dict(l4_tool_environment_ref)
            if l4_tool_environment_ref is not None
            else None
        ),
        "raw_evidence_refs": raw_evidence_refs,
        "l4_tool_version_status": l4_tool_version_status,
        "l4_tool_version": l4_tool_version,
        "provenance_status": provenance_status,
        "incomplete_reasons": sorted(incomplete_reasons),
        "terminal_binding": False,
        "pass_credit_authority": False,
        "official_authority": False,
    }
    errors = ContractRegistry().load_schema("development_l4_qor_provenance").validate(
        provenance
    )
    if errors:
        raise ValueError("invalid development L4 QoR provenance: " + "; ".join(errors))
    record["provenance"] = provenance
    return record


def _captured_l4_tool_version(
    l4_tool_environment: dict[str, Any] | None,
    lane: str,
) -> str | None:
    if not isinstance(l4_tool_environment, dict):
        return None
    lanes = l4_tool_environment.get("lanes")
    lane_record = lanes.get(lane) if isinstance(lanes, dict) else None
    if not isinstance(lane_record, dict) or lane_record.get("status") != "complete":
        return None
    expected_name = "nextpnr-xilinx" if lane == "l4_open" else "vivado"
    tools = lane_record.get("tools")
    if not isinstance(tools, list):
        return None
    for tool in tools:
        if isinstance(tool, dict) and tool.get("name") == expected_name:
            version_line = tool.get("version_line")
            return version_line if isinstance(version_line, str) and version_line else None
    return None


def _l4_raw_evidence_refs(
    project_dir: Path | None,
    relative_paths: set[str],
) -> list[dict[str, Any]]:
    if project_dir is None:
        return []
    attempt_dir = project_dir.parent
    attempts_dir = attempt_dir.parent
    sample_root = attempts_dir.parent.resolve()
    refs: list[dict[str, Any]] = []
    for relative_path in sorted(relative_paths):
        path = (sample_root / Path(*relative_path.split("/"))).resolve()
        if not path.is_relative_to(sample_root) or not path.is_file():
            continue
        content = path.read_bytes()
        refs.append(
            {
                "path": relative_path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
            }
        )
    return refs


def _is_l4_non_model_not_run_result(result: ToolResult) -> bool:
    return result.status in {"missing_tool", "timeout"} or _is_l4_toolchain_environment_failure(result)


def _is_l4_toolchain_environment_failure(result: ToolResult) -> bool:
    text = f"{result.stdout}\n{result.stderr}".lower()
    environment_markers = (
        "toolchain_environment_failure",
        "missing executable:",
        "openxc7 chipdb not found",
        "chipdb not found",
    )
    return any(marker in text for marker in environment_markers)


def _openxc7_pnr_command(
    project_dir: Path,
    platform: PlatformProfile,
    command_prefix: str | None = None,
    part: str | None = None,
) -> list[str]:
    configured_prefix = command_prefix or os.environ.get("SR2FPGA_OPENXC7_PNR_COMMAND")
    prefix = _split_command_prefix(configured_prefix) if configured_prefix else _default_openxc7_command_prefix()
    part = part or os.environ.get("SR2FPGA_OPENXC7_PART") or _openxc7_part(platform)
    clock_period_ns = os.environ.get("SR2FPGA_OPENXC7_CLOCK_PERIOD_NS") or _clock_period_ns(platform.clock_hz)
    return [
        *prefix,
        _openxc7_project_dir_arg(project_dir),
        part,
        clock_period_ns,
    ]


def _split_command_prefix(command_prefix: str) -> list[str]:
    return shlex.split(command_prefix, posix=os.name != "nt")


def _default_openxc7_command_prefix() -> list[str]:
    wrapper = RepositoryPaths.discover().agent_scripts_dir / "openxc7_pnr.sh"
    if not wrapper.is_file():
        return ["openxc7_pnr"]
    if os.name == "nt":
        return ["wsl", "bash", _windows_path_to_wsl(wrapper)]
    return ["bash", str(wrapper)]


def openxc7_tool_probe_command() -> list[str] | None:
    """Return the probe-capable built-in wrapper command, never a custom launcher."""

    if os.environ.get("SR2FPGA_OPENXC7_PNR_COMMAND"):
        return None
    return [*_default_openxc7_command_prefix(), "--probe-tool-environment"]


def _windows_path_to_wsl(path: Path) -> str:
    text = path.resolve().as_posix()
    if len(text) >= 3 and text[1:3] == ":/":
        return f"/mnt/{text[0].lower()}/{text[3:]}"
    return text


def _openxc7_part(platform: PlatformProfile) -> str:
    return platform.part if platform.part != "generic" else "xc7z020clg400-1"


def _openxc7_project_dir_arg(project_dir: Path) -> str:
    text = str(project_dir.resolve())
    return text.replace("\\", "/") if os.name == "nt" else text


def _his_source_used_for_generation(project_generator: object) -> str:
    value = getattr(project_generator, "his_source_used_for_generation", "generated")
    return str(value) if value else "generated"


def _validate_generated_project_h_stages(
    request: ProjectRequest,
    project: GeneratedProject,
    *,
    metadata: dict[str, Any] | None,
    project_generator: object,
    platform: PlatformProfile,
) -> dict[str, Any]:
    """Use the frozen public context when an episode pack governs the method."""

    pack = (metadata or {}).get("episode_pack")
    if isinstance(pack, dict):
        try:
            payload = parse_system_his_payload(project.files.get("system_his.json", ""))
        except ValueError:
            # Preserve the established H0 diagnostic shape for malformed output;
            # no reconstructed request fact can affect a path that already fails H0.
            pass
        else:
            return validate_frozen_system_his_payload_h_stages(
                context_from_validated_episode_pack(pack),
                payload,
                platform=platform,
                his_source_used_for_generation=_his_source_used_for_generation(
                    project_generator
                ),
            )
    return validate_system_his_h_stages(
        request,
        project,
        his_source_used_for_generation=_his_source_used_for_generation(
            project_generator
        ),
        platform=platform,
    )


def _h_stages_applicable(
    metadata: dict[str, Any] | None,
    project_generator: object,
) -> bool:
    metadata = metadata or {}
    method_condition = str(metadata.get("method_condition", "")).strip().upper()
    if method_condition:
        method_id = method_condition.replace("_", " ").replace("-", " ").split()[0]
        return method_id not in {"M0", "M1", "M2"}
    if str(metadata.get("generation_mode", "")).strip().lower() == "direct":
        return False
    if str(metadata.get("contract_skeleton_mode", "")).strip() == "legacy_full_project":
        return False
    return type(project_generator).__name__ != "DirectProjectGenerator"


def _supports_staged_his_generation(project_generator: object) -> bool:
    return callable(getattr(project_generator, "generate_system_his", None)) and callable(
        getattr(project_generator, "generate_from_system_his", None)
    )


def _embedded_system_his_repairer(project_generator: object) -> object | None:
    system_his_generator = getattr(project_generator, "system_his_generator", None)
    repairer = getattr(system_his_generator, "repairer", None)
    return repairer if callable(getattr(repairer, "repair", None)) else None


def _system_his_candidate_project(
    request: ProjectRequest,
    candidate_output: str,
) -> GeneratedProject:
    content = candidate_output if candidate_output.endswith("\n") else candidate_output + "\n"
    return GeneratedProject(
        project_name=request.project_name,
        files={"system_his.json": content},
    )


def _system_his_patch(
    before_project: GeneratedProject,
    after_project: GeneratedProject,
    before_report: dict[str, Any],
    after_report: dict[str, Any],
    diagnosis: dict[str, Any],
    *,
    attempt_id: int,
    provider_name: str | None,
) -> tuple[str, PatchMetadata]:
    before_content = before_project.files.get("system_his.json", "")
    after_content = after_project.files.get("system_his.json", "")
    diff_lines = list(
        difflib.unified_diff(
            before_content.splitlines(),
            after_content.splitlines(),
            fromfile="a/system_his.json",
            tofile="b/system_his.json",
            lineterm="",
        )
    )
    patch_diff = "\n".join(diff_lines) + ("\n" if diff_lines else "")
    before_status = _h_status_map(before_report)
    after_status = _h_status_map(after_report)
    target = first_failed_h_stage(before_report) or "h0"
    regressions = sorted(
        stage
        for stage, status in before_status.items()
        if status == "pass" and after_status.get(stage) != "pass"
    )
    changed = before_content != after_content
    fixed_target = after_status.get(target) == "pass"
    metadata = PatchMetadata(
        patch_id=f"p{attempt_id + 1:03d}",
        format="unified_diff",
        diagnosis_id=f"d{attempt_id + 1:03d}",
        files_touched=["system_his.json"] if changed else [],
        allowed_edit_regions_respected=changed,
        expected_effect=str(diagnosis.get("root_cause", "")),
        tool_result_before=before_status,
        tool_result_after=after_status,
        regressions=regressions,
        touched_trusted_artifacts=False,
        status="valid" if changed else "empty_patch",
        automatic_pass_credit=changed and fixed_target and not regressions,
        repair_regression={
            "repair_scope": "system_his",
            "target_failure": target,
            "fixed_target": fixed_target,
            "regressed_levels": regressions,
            "regressed_scenarios": [],
            "hidden_tests_preserved": False,
        },
        repair_provider_resolved=provider_name,
    )
    return patch_diff, metadata


def _h_status_map(report: dict[str, Any]) -> dict[str, str]:
    return {
        stage: str(report.get(stage, {}).get("status", "not_run"))
        for stage in ("h0", "h1", "h2", "h3")
    }


def _system_his_repair_provider(metadata: dict[str, Any] | None) -> str | None:
    metadata = metadata or {}
    value = metadata.get("generator_provider") or metadata.get("source")
    return str(value) if value else None


def _not_run_h_stage_report(reason: str) -> dict[str, Any]:
    stage = {"status": "not_run", "diagnostics": []}
    return {
        "his_source_used_for_generation": "generated",
        "not_run_reason": reason,
        "h0": dict(stage),
        "h1": dict(stage),
        "h2": dict(stage),
        "h3": dict(stage),
        "passed": True,
    }


def _not_applicable_h_stage_report() -> dict[str, Any]:
    stage = {"status": "not_applicable", "diagnostics": []}
    return {
        "his_source_used_for_generation": "not_applicable",
        "not_applicable_reason": "method_does_not_emit_system_his",
        "h0": dict(stage),
        "h1": dict(stage),
        "h2": dict(stage),
        "h3": dict(stage),
        "passed": True,
    }


def _h_stages_not_applicable(report: dict[str, Any] | None) -> bool:
    if report is None:
        return False
    return all(
        isinstance(report.get(stage), dict)
        and report[stage].get("status") == "not_applicable"
        for stage in ("h0", "h1", "h2", "h3")
    )


def _clock_period_ns(clock_hz: int) -> str:
    if clock_hz <= 0:
        return "10.0"
    return f"{1_000_000_000 / clock_hz:.3f}"


def _stage_entries(
    attempt_id: int,
    tool_results: dict[str, ToolResult],
    diagnosis: dict[str, Any] | None,
    has_patch: bool,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for result in tool_results.values():
        entry = {
            "attempt_id": attempt_id,
            "stage": result.stage,
            "status": result.status,
            "tool": result.command[0] if result.command else "",
            "exit_code": result.exit_code,
            "command": result.command,
        }
        if diagnosis is not None and diagnosis["stage"] == result.stage:
            entry["failure_type"] = diagnosis["failure_type"]
            entry["diagnosis_path"] = f"attempts/attempt_{attempt_id:03d}/diagnosis.json"
            if has_patch:
                entry["patch_path"] = f"attempts/attempt_{attempt_id:03d}/patch.diff"
        entries.append(entry)
    return entries


def _trajectory(sample_id: str, attempts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "attempts": attempts,
    }


def _req_his_fidelity(
    request: ProjectRequest,
    project: GeneratedProject,
    platform: PlatformProfile | None = None,
) -> dict[str, Any] | None:
    content = project.files.get("system_his.json")
    if content is None:
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return check_system_his_req_fidelity(request, payload, platform).metrics
