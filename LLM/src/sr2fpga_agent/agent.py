"""High-level SR2FPGA data generation orchestration."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any

from LLM.src.sr2fpga_agent.log_parser import (
    classify_failure,
    parse_test_fail_mismatches,
    parse_tool_warnings,
    parse_yosys_stats,
)
from LLM.src.sr2fpga_agent.his_validation import (
    first_failed_h_stage,
    h_stage_labels,
    validate_system_his_h_stages,
)
from LLM.src.sr2fpga_agent.models import (
    GeneratedProject,
    PatchMetadata,
    PlatformProfile,
    ProjectRequest,
    RepairResult,
    ToolResult,
)
from LLM.src.sr2fpga_agent.openxc7_report import parse_openxc7_report
from LLM.src.sr2fpga_agent.oracle_runner import run_oracle_scenarios, write_oracle_run_evidence
from LLM.src.sr2fpga_agent.oracles import (
    OracleBundle,
    build_oracle_bundle_for_request,
    sanitize_oracle_profile,
)
from LLM.src.sr2fpga_agent.oracles.types import OracleRunEvidence
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.path_safety import (
    build_patch_metadata,
    build_yosys_script,
    finalize_patch_metadata,
    project_file_target,
    validate_sample_id,
)
from LLM.src.sr2fpga_agent.recorder import AttemptRecord, DatasetRecorder
from LLM.src.sr2fpga_agent.rtl_identifier_checker import check_rtl_identifiers, rtl_identifier_tool_result
from LLM.src.sr2fpga_agent.system_his_checker import L0CheckResult, check_project_l0
from LLM.src.sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity
from LLM.src.sr2fpga_agent.semantic_trace import diagnose_semantic_trace, parse_semantic_trace
from LLM.src.sr2fpga_agent.testbench_checker import (
    build_oracle_strength,
    check_testbench_static_issues,
    testbench_observation_tool_result,
)
from LLM.src.sr2fpga_agent.failure_injector import oracle_mutation_projects
from LLM.src.sr2fpga_agent.tool_runner import CommandRunner
from LLM.src.sr2fpga_agent.vivado_report import run_vivado_reference


class DataGenerationAgent:
    """Generate one dataset sample and run the lightweight tool pipeline."""

    def __init__(
        self,
        dataset_root: Path,
        command_runner: CommandRunner | None = None,
        project_generator: ProjectGenerator | None = None,
        repairer: object | None = None,
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
    ) -> None:
        self.dataset_root = dataset_root
        self.recorder = DatasetRecorder(dataset_root)
        self.command_runner = command_runner or CommandRunner()
        self.project_generator = project_generator or ProjectGenerator()
        self.repairer = repairer
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

    def run_one(
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
            project = self.project_generator.generate(request, platform)
        except Exception as exc:
            return self._record_generation_failure(sample_id, sample_dir, request, exc)

        all_stage_entries: list[dict[str, Any]] = []
        failure_count = 0
        final_attempt_id = 0
        final_tool_results: dict[str, ToolResult] = {}
        final_project = project
        final_his_validation: dict[str, Any] | None = None
        final_oracle_bundle: OracleBundle | None = None
        final_oracle_evidence: OracleRunEvidence | None = None
        final_oracle_profile = _oracle_not_run_profile(
            request.task_type,
            "disabled_by_config" if not self.enable_independent_oracle else "unsupported_family",
        )
        patches: list[PatchMetadata] = []
        pending_patch_attempt_id: int | None = None

        for attempt_id in range(self.max_attempts):
            final_attempt_id = attempt_id
            final_project = project
            project_dir = sample_dir / "attempts" / f"attempt_{attempt_id:03d}" / "generated_project"
            _write_project(project_dir, project)

            his_validation = validate_system_his_h_stages(
                request,
                project,
                his_source_used_for_generation=_his_source_used_for_generation(self.project_generator),
            )
            final_his_validation = his_validation
            h_stage_failed = not his_validation["passed"]
            l0_result: L0CheckResult | None = None
            attempt_oracle_bundle: OracleBundle | None = None
            attempt_oracle_evidence: OracleRunEvidence | None = None
            oracle_infrastructure_failure = False
            if h_stage_failed:
                tool_results = {"his_validation": _h_stage_tool_result(his_validation)}
            else:
                l0_result = check_project_l0(project)
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
                        if attempt_oracle_bundle is not None and attempt_oracle_evidence is None and "sim_run" not in tool_results:
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
                tool_results = {"l0_consistency": _l0_tool_result(l0_result)}
            final_oracle_bundle = attempt_oracle_bundle
            final_oracle_evidence = attempt_oracle_evidence
            final_tool_results = tool_results
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
            diagnosis = _diagnose_first_failure(tool_results, l0_result=l0_result)
            patch_diff = ""
            patch_metadata = None

            if diagnosis is not None:
                if not oracle_infrastructure_failure:
                    failure_count += 1
                if h_stage_failed:
                    pass
                elif oracle_infrastructure_failure:
                    pass
                elif self.repairer is not None and attempt_id + 1 < self.max_attempts:
                    try:
                        repair_result = self.repairer.repair(project, diagnosis)
                    except Exception as exc:
                        tool_results = {
                            **tool_results,
                            "repair": _repair_failure_tool_result(exc),
                        }
                        diagnosis = _repair_failure_diagnosis(exc, upstream_diagnosis=diagnosis)
                    else:
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
                        patches.append(patch_metadata)
                        if patch_metadata.status == "valid":
                            project = repair_result.generated_project
                            pending_patch_attempt_id = attempt_id
                        else:
                            tool_results = {
                                **tool_results,
                                "repair": _repair_failure_tool_result(ValueError("invalid_edit_surface")),
                            }
                            diagnosis = _repair_failure_diagnosis(
                                ValueError("invalid_edit_surface"),
                                upstream_diagnosis=diagnosis,
                            )

            all_stage_entries.extend(_stage_entries(attempt_id, tool_results, diagnosis, bool(patch_diff)))
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

            if diagnosis is None:
                break
            if h_stage_failed:
                break
            if oracle_infrastructure_failure:
                break
            if diagnosis.get("stage") == "repair":
                break

        l4_open = _l4_open_record(
            final_tool_results,
            self.enable_openxc7_l4,
            final_attempt_id,
            tool=self.openxc7_tool,
            board_profile=self.openxc7_board_profile,
            project_dir=project_dir,
        )
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
        )
        measured_qor = _measured_qor(final_tool_results, l4_open, l4_commercial)
        trajectory = _trajectory(sample_id, all_stage_entries)
        if patches:
            trajectory["patches"] = [patch.to_dict() for patch in patches]
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
        if not labels["automatic_pass_credit"]:
            labels["automatic_pass_credit_reason"] = (
                "independent_oracle_infrastructure_error"
                if final_oracle_profile.get("status") == "infrastructure_error"
                else _automatic_pass_credit_reason(patches)
            )
        if final_his_validation is not None:
            trajectory["his_validation"] = final_his_validation
        trajectory["oracle_profile"] = final_oracle_profile
        req_his_fidelity = _req_his_fidelity(request, final_project)
        if req_his_fidelity is not None:
            trajectory["req_his_fidelity"] = req_his_fidelity
        self.recorder.write_final(
            sample_id,
            final_project,
            labels=labels,
            measured_qor=measured_qor,
            tool_versions={"verilator": "unknown", "iverilog": "unknown", "yosys": "unknown"},
            trajectory=trajectory,
        )
        return {"sample_dir": str(sample_dir), "pass_level": labels["pass_level"]}

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

    def _record_generation_failure(
        self,
        sample_id: str,
        sample_dir: Path,
        request: ProjectRequest,
        exc: Exception,
    ) -> dict[str, Any]:
        failed_project = GeneratedProject(project_name=request.project_name, files={})
        tool_results = {
            "generation": ToolResult(
                stage="generation",
                command=["project_generator"],
                status="failed",
                exit_code=1,
                stdout="",
                stderr=str(exc),
                duration_seconds=0.0,
            )
        }
        diagnosis = {
            "failure_type": "generation_failed",
            "stage": "generation",
            "root_cause": str(exc),
            "affected_files": _generation_failure_affected_files(exc),
        }
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
        )
        l4_commercial = _l4_commercial_record(tool_results, self.enable_vivado_l4, tool=self.vivado_tool)
        labels = _generation_failure_labels(l4_open, l4_commercial)
        trajectory = _trajectory(sample_id, _stage_entries(0, tool_results, diagnosis, False))
        self.recorder.write_final(
            sample_id,
            failed_project,
            labels=labels,
            measured_qor=_measured_qor(tool_results, l4_open, l4_commercial),
            tool_versions={"verilator": "unknown", "iverilog": "unknown", "yosys": "unknown"},
            trajectory=trajectory,
        )
        return {"sample_dir": str(sample_dir), "pass_level": labels["pass_level"]}

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
        manifest = json.loads((project_dir / "manifest.json").read_text(encoding="utf-8"))
        sources = list(manifest["sources"])
        testbench = manifest["simulation"]["testbench"]
        top_module = manifest["top_module"]

        results: dict[str, ToolResult] = {}
        identifier_issues = check_rtl_identifiers(project, sources)
        results["rtl_identifier_check"] = rtl_identifier_tool_result(identifier_issues)
        if results["rtl_identifier_check"].status != "passed":
            return results

        results["lint"] = self.command_runner.run(
            ["verilator", "--lint-only", "-Wall", *sources],
            cwd=project_dir,
            stage="lint",
        )
        if results["lint"].status != "passed":
            return results

        testbench_issues = check_testbench_static_issues(project.files.get(testbench, ""))
        results["testbench_static_check"] = testbench_observation_tool_result(testbench_issues)
        if results["testbench_static_check"].status != "passed":
            return results

        results["sim_compile"] = self.command_runner.run(
            ["iverilog", "-g2012", "-o", "sim.out", *sources, testbench],
            cwd=project_dir,
            stage="sim_compile",
        )
        if results["sim_compile"].status != "passed":
            return results

        if oracle_bundle is None:
            results["sim_run"] = self.command_runner.run(
                ["vvp", "sim.out"],
                cwd=project_dir,
                stage="sim_run",
            )
            results["sim_run"] = _validate_simulation_output(results["sim_run"])
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
                sim_result = _oracle_boundary_failure_tool_result(exc, "oracle_runner_exception")
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
                        sim_result = _oracle_boundary_failure_tool_result(exc, "oracle_evidence_write_failed")
            results["sim_run"] = sim_result
            if oracle_evidence_out is not None:
                oracle_evidence_out.append(evidence)
        if results["sim_run"].status != "passed":
            return results

        try:
            yosys_script = build_yosys_script(sources, top_module)
        except ValueError as exc:
            results["synth"] = _synth_input_tool_result(exc)
            return results
        results["synth"] = self.command_runner.run(
            ["yosys", "-p", yosys_script],
            cwd=project_dir,
            stage="synth",
            timeout_seconds=60,
        )
        if results["synth"].status != "passed" or not self.enable_openxc7_l4:
            return results

        results["pnr"] = self.command_runner.run(
            _openxc7_pnr_command(project_dir, platform, command_prefix=self.openxc7_command, part=self.openxc7_part),
            cwd=project_dir,
            stage="pnr",
            timeout_seconds=self.openxc7_timeout_seconds,
        )
        return results


def _write_project(project_dir: Path, project: GeneratedProject) -> None:
    for relative_path, content in project.files.items():
        target = project_file_target(project_dir, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _l0_tool_result(result: L0CheckResult) -> ToolResult:
    return ToolResult(
        stage="l0_consistency",
        command=["system_his_checker"],
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
    return evidence is not None and evidence.failure_origin in {
        "oracle_environment_failure",
        "toolchain_environment_failure",
    }


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


def _generation_failure_affected_files(exc: Exception) -> list[str]:
    message = str(exc).lower()
    if "system-his" in message or "system_his" in message:
        return ["system_his.json"]
    return []


def _diagnose_first_failure(
    tool_results: dict[str, ToolResult],
    l0_result: L0CheckResult | None = None,
) -> dict[str, Any] | None:
    for result in tool_results.values():
        if result.status != "passed":
            if result.stage == "pnr" and _is_l4_non_model_not_run_result(result):
                continue
            log_text = f"{result.stdout}\n{result.stderr}"
            if result.stage == "l0_consistency":
                return {
                    "failure_type": "l0_contract_violation",
                    "stage": result.stage,
                    "root_cause": log_text.strip() or result.status,
                    "affected_files": ["system_his.json", "manifest.json"],
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
    l0_pass = not (
        tool_results.get("l0_consistency") is not None and tool_results["l0_consistency"].status != "passed"
    ) and not blocked_by_h_stage
    lint_pass = not blocked_by_h_stage and tool_results.get("lint") is not None and tool_results["lint"].status == "passed"
    sim_compile_pass = (
        tool_results.get("sim_compile") is not None and tool_results["sim_compile"].status == "passed"
    )
    sim_run_pass = tool_results.get("sim_run") is not None and tool_results["sim_run"].status == "passed"
    synth_pass = tool_results.get("synth") is not None and tool_results["synth"].status == "passed"
    pnr_pass = l4_open["status"] == "pass"
    oracle_profile = oracle_profile or _oracle_not_run_profile("", "disabled_by_config")
    independent_oracle_status = str(oracle_profile.get("status", "not_run"))
    oracle_infrastructure_error = independent_oracle_status == "infrastructure_error"

    raw_tool_pass_level = f"{failed_h_stage.upper()}_FAIL" if failed_h_stage else ("L0" if l0_pass else "L0_FAIL")
    if lint_pass:
        raw_tool_pass_level = "L1"
    if lint_pass and sim_compile_pass and sim_run_pass:
        raw_tool_pass_level = "L2"
    if lint_pass and sim_compile_pass and sim_run_pass and synth_pass:
        raw_tool_pass_level = "L3"
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
        "failure_origin": oracle_profile.get("failure_origin"),
        "automatic_pass_credit": not oracle_infrastructure_error,
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
            "l2_hidden_pass": oracle_profile.get("class_status", {}).get("hidden_deterministic") == "pass",
            "l2_randomized_pass": oracle_profile.get("class_status", {}).get("randomized_fixed_seed") == "pass",
            "l2_stress_pass": oracle_profile.get("class_status", {}).get("stress") == "pass",
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
    labels.setdefault("generated_his_pass_credit", True)
    if labels["generated_his_pass_credit"]:
        labels["generated_his_pass_level"] = pass_level
        labels["generated_his_no_credit_reason"] = None
    else:
        labels["generated_his_pass_level"] = "NO_CREDIT_ORACLE_FALLBACK"
        labels["generated_his_no_credit_reason"] = "oracle_fallback"
    return labels


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
        return record
    synth = tool_results.get("synth")
    if synth is None or synth.status != "passed":
        record["skip_reason"] = "l3_failed"
        return record
    pnr = tool_results.get("pnr")
    if pnr is None:
        record["skip_reason"] = "not_selected_by_policy"
        return record
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
    return record


def _l4_commercial_record(
    tool_results: dict[str, ToolResult],
    enabled: bool,
    *,
    tool: str = "vivado",
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
    return record


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
) -> dict[str, Any]:
    record = _l4_commercial_record(tool_results, enabled, tool=tool)
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
        return record
    except subprocess.TimeoutExpired:
        record["skip_reason"] = "tool_timeout"
        return record
    except OSError:
        record["skip_reason"] = "toolchain_environment_failure"
        return record

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
    return record


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
    wrapper = Path(__file__).resolve().parents[3] / "scripts" / "openxc7_pnr.sh"
    if not wrapper.is_file():
        return ["openxc7_pnr"]
    if os.name == "nt":
        return ["wsl", "bash", _windows_path_to_wsl(wrapper)]
    return ["bash", str(wrapper)]


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


def _req_his_fidelity(request: ProjectRequest, project: GeneratedProject) -> dict[str, Any] | None:
    content = project.files.get("system_his.json")
    if content is None:
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return check_system_his_req_fidelity(request, payload).metrics
