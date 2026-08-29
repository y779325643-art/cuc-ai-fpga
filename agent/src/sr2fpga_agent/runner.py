"""Autonomous batch runner for SR2FPGA trajectory generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from sr2fpga_agent.agent import DataGenerationAgent, openxc7_tool_probe_command
from sr2fpga_agent.baseline_report import baseline_rows, render_markdown
from sr2fpga_agent.cli import (
    build_project_generator_for_connection,
    build_repairer,
    build_repairer_for_connection,
)
from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.block_cost_accounting import BlockPreparationCostLedger
from sr2fpga_agent.block_preparation import (
    BlockPreparationFacades,
    PreparedBlockArtifacts,
    prepare_development_paired_block,
    read_development_shared_checkpoint_manifest,
)
from sr2fpga_agent.cost_accounting import (
    AttemptCostLedger,
    AttemptCostLedgerRouter,
    validate_accounting_failure_origin,
)
from sr2fpga_agent.providers import (
    AnthropicCompatibleClient,
    AnthropicCompatibleConfig,
    OpenAICompatibleClient,
    OpenAICompatibleConfig,
)
from sr2fpga_agent.failure_injector import FailureInjectingProjectGenerator
from sr2fpga_agent.generation import (
    DirectProjectGenerator,
    FrozenContextDirectProjectFacade,
    FrozenContextDirectProjectGenerator,
    FrozenContextHisGeneratorBridge,
)
from sr2fpga_agent.generation.context_his import (
    FrozenContextSystemHisCorrectionFacade,
    FrozenContextSystemHisFacade,
    FrozenContextSystemHisValidationFacade,
)
from sr2fpga_agent.generation.context_plan import FrozenContextUntypedPlanFacade
from sr2fpga_agent.family_recipe import select_family_recipe
from sr2fpga_agent.model_gateway_provenance import write_model_gateway_provenance
from sr2fpga_agent.provider_seed_capability import (
    load_development_provider_seed_capability,
    require_paired_confirmatory_seed_capability,
)
from sr2fpga_agent.his_correction_outcome import (
    reconcile_development_his_correction_outcome,
)
from sr2fpga_agent.frozen_context import (
    build_development_episode_pack,
    context_from_validated_episode_pack,
    freeze_ready_requirement_context,
)
from sr2fpga_agent.measurement_freeze import (
    build_measurement_freeze,
    write_or_validate_freeze,
)
from sr2fpga_agent.local_tools import resolve_executable
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.model_budget import ModelCallBudget, client_for_stage
from sr2fpga_agent.episode_executor import EpisodeExecutor
from sr2fpga_agent.episode_outcome import (
    project_development_public_evaluation,
    reconcile_development_episode_outcome,
)
from sr2fpga_agent.pre_candidate_outcome import (
    reconcile_development_pre_candidate_stop_outcome,
)
from sr2fpga_agent.method_adapters import (
    GenerationServices,
    MethodAdapterRegistry,
    MethodArtifactGateway,
    PairingKey,
    PairedArtifactCoordinator,
    PlanningArtifactEmission,
    PlanningArtifactKind,
    ProjectCandidateEmission,
    SharedArtifactRefs,
)
from sr2fpga_agent.paired_block import (
    build_balanced_method_orders,
    build_development_paired_block,
    development_paired_block_reference,
    load_development_paired_block,
    write_development_paired_block,
)
from sr2fpga_agent.paired_measurement import collect_paired_results
from sr2fpga_agent.project_generator import COMPONENT_TOPOLOGIES, ProjectGenerator
from sr2fpga_agent.project_contract import project_package_sha256
from sr2fpga_agent.public_l2_harness import (
    PublicL2HarnessError,
    load_development_public_l2_harness,
)
from sr2fpga_agent.recorder import DatasetRecorder
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary
from sr2fpga_agent.requirement_audit import load_requirement_audit_manifest
from sr2fpga_agent.system_his_compatibility import load_system_his_compatibility_envelope
from sr2fpga_agent.task_catalog import task_family_spec_for_alias
from sr2fpga_agent.evaluator_dispatch import DevelopmentHiddenEvaluationAuthority
from sr2fpga_agent.testbench_checker import check_testbench_static_issues
from sr2fpga_agent.tool_environment import (
    collect_development_tool_environment,
    tool_version_projection,
)
from sr2fpga_agent.l4_tool_environment import (
    L4_VERSION_PROBE_ENV,
    collect_development_l4_tool_environment,
    l4_tool_version_projection,
)


VALID_MEASUREMENT_POINTS = {
    "a_first_attempt_no_tools",
    "b_tool_in_loop_repair",
    "c_finetuned_first_attempt_no_tools",
}

VALID_REQUIREMENT_STYLES = {"contract", "natural_component", "simple_prompt"}
VALID_EVALUATION_LINES = {"line_a", "line_b"}
VALID_ANALYSIS_POPULATIONS = {
    "development",
    "excluded",
    "official_vpp",
    "ambiguity_audit",
}
IMPLEMENTED_METHOD_CONDITIONS = {
    "M0",
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "reference_deterministic",
    "oracle_his_ceiling",
}
EPISODE_PACK_METHOD_CONDITIONS = {"M0", "M1", "M2", "M3", "M4", "M5"}
REQ2HIS_API_KINDS = {"openai_compat", "anthropic_compat", "deepseek-his-v12"}
DEVELOPMENT_HIDDEN_AUTHORITY_DIR = "development_hidden_authority"
DEVELOPMENT_PUBLIC_AUTHORITY_DIR = "development_public_authority"
_PAIRED_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHARED_INITIAL_CALL_CEILING = {
    "M0": 1,
    "M1": 1,
    "M2": 0,
    "M3": 1,
    "M4": 2,
    "M5": 2,
}
_BLOCK_PREPARATION_PHYSICAL_CALL_CEILING = 3


@dataclass(frozen=True)
class TaskConfig:
    source: str
    task_type: str
    widths: list[int]
    count: int
    failure_injectors: list[str] = field(default_factory=list)
    difficulty_tier: str = ""
    failure_origin: str = ""
    topology_ids: list[str] = field(default_factory=list)
    measurement_point: str = ""
    requirement_style: str = "simple_prompt"
    evaluation_line: str = "line_b"
    requirement: str = ""
    method_condition: str = ""
    analysis_population: str = "development"
    requirement_audit_manifest: str = ""
    public_l2_harness_manifest: str = ""
    semantic_instance_id: str = ""
    replicate_id: str = ""
    decoding_seed: int | None = None
    paired_block_id: str = ""
    execution_schedule_seed: int | None = None
    decoding_control_mode: str = ""


@dataclass(frozen=True)
class SourceConnection:
    name: str
    kind: str
    model: str = ""
    base_url: str = ""
    api_key_env: str = ""
    generation_mode: str = ""
    timeout_seconds: int = 120
    transport_attempts: int = 3
    max_tokens: int = 0
    wire_api: str = "chat_completions"
    reasoning_effort: str = ""
    disable_response_storage: bool = False
    system_his_schema_version: str = ""
    seed_capability_manifest: str = ""


@dataclass(frozen=True)
class L4OpenConfig:
    tool: str = "openxc7_nextpnr"
    target_part: str = "XC7Z020CLG484-2"
    board_profile: str = "ac820_zynq"
    run_policy: str = "never"
    timeout_seconds: int = 600
    family_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class L4CommercialConfig:
    tool: str = "vivado"
    command: str = "vivado"
    target_part: str = "XC7Z020CLG484-2"
    run_policy: str = "never"
    timeout_seconds: int = 1800


@dataclass(frozen=True)
class RunnerConfig:
    dataset_root: Path
    export_root: Path
    run_root: Path
    provider: str
    repair_provider: str
    max_attempts: int
    refresh_exports: bool
    line_b_targets: dict[str, float | int]
    tasks: list[TaskConfig]
    max_model_calls: int = 0
    model: str = "deepseek-v4-pro"
    base_url: str = "https://api.deepseek.com"
    api_key_env: str = "DEEPSEEK_API_KEY"
    platform: str = "generic_verilog"
    env_file: Path = Path("")
    sample_id_prefix: str = "runner"
    sources: dict[str, "SourceConnection"] = field(default_factory=dict)
    enable_openxc7_l4: bool = False
    run_l4_open: bool = False
    l4_open: L4OpenConfig = field(default_factory=L4OpenConfig)
    run_l4_commercial: bool = False
    l4_commercial: L4CommercialConfig = field(default_factory=L4CommercialConfig)
    run_independent_oracle: bool = False
    requirement_audit_manifest: str = ""
    require_paired_confirmatory_seed_control: bool = False


@dataclass(frozen=True)
class PlannedSample:
    sample_id: str
    source: str
    task_type: str
    width: int
    project_name: str
    requirement: str
    failure_injectors: list[str] = field(default_factory=list)
    family_id: str = ""
    difficulty_tier: str = "T1"
    failure_origin: str = ""
    topology_id: str = ""
    measurement_point: str = ""
    requirement_style: str = "simple_prompt"
    evaluation_line: str = "line_b"
    paired_requirement_id: str = ""
    requirement_sha256: str = ""
    method_condition: str = ""
    analysis_population: str = "development"
    requirement_audit_manifest: str = ""
    public_l2_harness_manifest: str = ""
    semantic_instance_id: str = ""
    replicate_id: str = ""
    decoding_seed: int | None = None
    paired_block_id: str = ""
    execution_schedule_seed: int | None = None
    decoding_control_mode: str = ""
    pairing_identity_source: str = ""

    def metadata(
        self,
        config: RunnerConfig,
        *,
        paired_block_ref: ArtifactRef | None = None,
    ) -> dict[str, Any]:
        connection = resolve_source_connection(config, self.source)
        schema_version = _sample_system_his_schema_version(self, config)
        request = _project_request_for_sample(self)
        platform = _platform_profile_for_config(config)
        boundary = evaluate_requirement_boundary(request, platform)
        method_condition = _sample_method_condition(self, config)
        model_call_ceiling = _sample_model_call_ceiling(self, config, method_condition)
        repair_provider_resolved = "none"
        if method_condition in {"M1", "M5"}:
            repair_provider_resolved = (
                self.source
                if config.repair_provider == "same_as_source"
                else config.repair_provider
            )
        metadata = {
            "source": self.source,
            "generator_provider": self.source,
            "model": connection.model,
            "failure_origin": _sample_failure_origin(self, config),
            "family_id": self.family_id,
            "difficulty_tier": self.difficulty_tier,
            "measurement_point": self.measurement_point
            or _measurement_point_for_method(config, method_condition),
            "evaluation_line": self.evaluation_line,
            "repair_provider": config.repair_provider,
            "repair_provider_policy": config.repair_provider,
            "repair_provider_resolved": repair_provider_resolved,
            "failure_injectors": list(self.failure_injectors),
            "task_type": self.task_type,
            "width": self.width,
            "system_his_schema_version": schema_version,
            "training_split": _training_split(schema_version),
            "contract_skeleton_mode": _contract_skeleton_mode(self, config),
            "topology_id": self.topology_id,
            "requirement_style": self.requirement_style,
            "paired_requirement_id": self.paired_requirement_id,
            "requirement_sha256": self.requirement_sha256,
            "method_condition": method_condition,
            "analysis_population": self.analysis_population,
            "semantic_instance_id": self.semantic_instance_id,
            "replicate_id": self.replicate_id,
            "decoding_seed": self.decoding_seed,
            "paired_block_id": self.paired_block_id,
            "execution_schedule_seed": self.execution_schedule_seed,
            "decoding_control_mode": self.decoding_control_mode,
            "pairing_identity_source": self.pairing_identity_source,
            "requirement_audit_manifest": self.requirement_audit_manifest,
            "requirement_boundary": boundary.to_dict(),
            "model_call_budget": {
                "max_model_calls": model_call_ceiling,
                "model_calls_used": 0,
                "model_calls_failed": 0,
                "remaining_model_calls": model_call_ceiling,
                "max_parser_schema_retries": 0,
                "parser_schema_retries_used": 0,
                "remaining_parser_schema_retries": 0,
                "token_accounting": "unavailable_provider_response",
                "input_tokens": None,
                "output_tokens": None,
                "cached_tokens": None,
                "calls": [],
            },
        }
        if paired_block_ref is not None:
            metadata["paired_block_ref"] = paired_block_ref.to_dict()
        if (
            boundary.disposition == "ready"
            and method_condition in EPISODE_PACK_METHOD_CONDITIONS
            and self.analysis_population in {"development", "excluded"}
        ):
            context = freeze_ready_requirement_context(boundary, platform)
            metadata["episode_pack"] = build_development_episode_pack(
                context,
                episode_id=self.sample_id,
                analysis_population=self.analysis_population,
                method_condition=method_condition,
                evaluator_metadata={
                    "family_id": self.family_id,
                    "task_type": self.task_type,
                    "topology_id": self.topology_id,
                    "difficulty_tier": self.difficulty_tier,
                    "semantic_instance_id": self.semantic_instance_id,
                    "replicate_id": self.replicate_id,
                    "decoding_seed": self.decoding_seed,
                    "paired_block_id": self.paired_block_id,
                    "execution_schedule_seed": self.execution_schedule_seed,
                    "decoding_control_mode": self.decoding_control_mode,
                    "pairing_identity_source": self.pairing_identity_source,
                },
                paired_block_ref=(
                    paired_block_ref.to_dict()
                    if paired_block_ref is not None
                    else None
                ),
            ).to_dict()
        if (
            boundary.disposition == "ready"
            and connection.kind in REQ2HIS_API_KINDS
            and connection.generation_mode == "two_stage"
        ):
            metadata["family_recipe_decision"] = select_family_recipe(
                request,
                boundary.envelope,
            ).to_dict()
        return metadata


@dataclass(frozen=True)
class _PlannedPairedBlock:
    payload: dict[str, Any]
    artifact_ref: ArtifactRef
    sample_ids: tuple[str, ...]


@dataclass(frozen=True)
class PreparedBlockRuntime:
    prepared: PreparedBlockArtifacts
    member_sample_ids: tuple[str, ...]
    exclusive_model_call_ceilings: dict[str, int]


class _RunnerDirectMethodProjectGenerator:
    """Bridge M0/M1 through the same paired method-artifact authority."""

    his_source_used_for_generation = None

    def __init__(
        self,
        *,
        method_condition: str,
        context,
        services: GenerationServices,
        coordinator: PairedArtifactCoordinator,
        pairing: PairingKey,
        direct: FrozenContextDirectProjectFacade | None,
        prepared_initial_project: ProjectCandidateEmission | None = None,
    ) -> None:
        self._adapter = MethodAdapterRegistry().create(method_condition)
        self._context = context
        self._services = services
        self._coordinator = coordinator
        self._pairing = pairing
        self._direct = direct
        self._prepared_initial_project = prepared_initial_project
        self.last_outcome = None

    def generate(self, _request: ProjectRequest, _platform: PlatformProfile):
        if self._prepared_initial_project is not None:
            expected_key = f"paired/{self._pairing.digest()}/direct-initial-project"
            if self._prepared_initial_project.artifact_ref.key != expected_key:
                raise ValueError(
                    "prepared Direct project key does not match pairing checkpoint"
                )
            self._services.artifacts.read_project(self._prepared_initial_project)
            shared_project = self._prepared_initial_project
        else:
            if self._direct is None:
                raise RuntimeError("Direct method requires an initial-project capability")
            shared_project = self._coordinator.materialize_initial_project(
                self._pairing,
                lambda: self._direct.emit_project(self._context),
            )
        outcome = EpisodeExecutor().emit_candidate(
            self._adapter,
            self._context,
            self._services,
            SharedArtifactRefs(initial_project=shared_project),
        )
        if outcome.candidate is None:
            failure = outcome.failure
            if failure is None:
                raise RuntimeError("Direct adapter produced no complete candidate")
            raise RuntimeError(
                f"{failure.stage} failed with {failure.error_type}: {failure.message}"
            )
        self.last_outcome = outcome
        return self._services.artifacts.read_project(outcome.candidate)


class _RunnerUntypedPlanProjectGenerator:
    """Bridge the first-class M2 adapter into the legacy generator slot."""

    his_source_used_for_generation = None

    def __init__(self, *, context, services: GenerationServices) -> None:
        self._adapter = MethodAdapterRegistry().create("M2")
        self._context = context
        self._services = services
        self.last_outcome = None

    def generate(self, _request: ProjectRequest, _platform: PlatformProfile):
        outcome = EpisodeExecutor().emit_candidate(
            self._adapter,
            self._context,
            self._services,
        )
        if outcome.candidate is None:
            failure = outcome.failure
            if failure is None:
                raise RuntimeError("M2 adapter produced no complete candidate")
            raise RuntimeError(
                f"{failure.stage} failed with {failure.error_type}: {failure.message}"
            )
        self.last_outcome = outcome
        return self._services.artifacts.read_project(outcome.candidate)


@dataclass(frozen=True)
class RunState:
    run_id: str
    next_index: int
    completed_samples: list[str]
    buckets: dict[str, list[str]]
    failure_types: dict[str, int]
    exports_refreshed: bool
    config_fingerprint: str = ""


def load_runner_config(path: Path) -> RunnerConfig:
    raw = _load_mapping(path)
    if "request_mode" in raw:
        raise SystemExit(
            "request_mode has been removed; all requests now use the unified open-world path"
        )
    if "family_recipe" in raw:
        raise SystemExit(
            "family_recipe has been removed; recipe selection now uses the automatic policy"
        )
    run_l4_open = _parse_bool(
        raw.get("run_l4_open", raw.get("enable_openxc7_l4", False)),
        "run_l4_open",
    )
    run_l4_commercial = _parse_bool(raw.get("run_l4_commercial", False), "run_l4_commercial")
    run_independent_oracle = _parse_bool(
        raw.get("run_independent_oracle", False),
        "run_independent_oracle",
    )
    raw_audit_manifest = raw.get("requirement_audit_manifest", "")
    requirement_audit_manifest = ""
    if raw_audit_manifest is not None:
        requirement_audit_manifest = str(raw_audit_manifest).strip()
    return RunnerConfig(
        dataset_root=Path(str(raw["dataset_root"])),
        export_root=Path(str(raw["export_root"])),
        run_root=Path(str(raw["run_root"])),
        provider=str(raw.get("provider", "deterministic")),
        repair_provider=str(raw.get("repair_provider", "none")),
        max_attempts=int(raw.get("max_attempts", 1)),
        refresh_exports=_parse_bool(raw.get("refresh_exports", True), "refresh_exports"),
        line_b_targets=dict(raw.get("line_b_targets", {})),
        tasks=[_load_task_config(item, raw) for item in raw.get("tasks", [])],
        max_model_calls=int(raw.get("max_model_calls", 0)),
        model=str(raw.get("model", "deepseek-v4-pro")),
        base_url=str(raw.get("base_url", "https://api.deepseek.com")),
        api_key_env=str(raw.get("api_key_env", "DEEPSEEK_API_KEY")),
        platform=str(raw.get("platform", "generic_verilog")),
        env_file=Path(str(raw.get("env_file", ""))),
        sample_id_prefix=str(raw.get("sample_id_prefix", "runner")),
        sources=_load_sources(raw.get("sources", {})),
        enable_openxc7_l4=run_l4_open,
        run_l4_open=run_l4_open,
        l4_open=_load_l4_open_config(
            raw.get("l4_open", {}),
            default_run_policy="after_l3_pass" if run_l4_open else "never",
        ),
        run_l4_commercial=run_l4_commercial,
        l4_commercial=_load_l4_commercial_config(
            raw.get("l4_commercial", {}),
            default_run_policy="after_l3_pass" if run_l4_commercial else "never",
        ),
        run_independent_oracle=run_independent_oracle,
        requirement_audit_manifest=requirement_audit_manifest,
        require_paired_confirmatory_seed_control=_parse_bool(
            raw.get("require_paired_confirmatory_seed_control", False),
            "require_paired_confirmatory_seed_control",
        ),
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run an autonomous SR2FPGA trajectory batch.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--preflight", action="store_true", help="Check runner readiness without generating samples")
    parser.add_argument(
        "--validate-provider",
        action="store_true",
        help="During preflight, make a minimal provider auth request without generating samples",
    )
    args = parser.parse_args(argv)

    config = load_runner_config(args.config)
    if args.preflight:
        report = runner_preflight(config, run_id=args.run_id or None, validate_provider=args.validate_provider)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report["ok"]:
            raise SystemExit(1)
        return
    summary = run_batch(config, run_id=args.run_id or None, resume=not args.no_resume)
    print(f"run_id={summary['run_id']}")
    print(f"total_completed={summary['total_completed']}")
    print(f"success_l3={len(summary['buckets'].get('success_l3', []))}")
    print(f"repair_trajectory={len(summary['buckets'].get('repair_trajectory', []))}")
    print(f"not_run={len(summary['buckets'].get('not_run', []))}")
    print(f"rejected={len(summary['buckets'].get('rejected', []))}")


def runner_preflight(
    config: RunnerConfig,
    run_id: str | None = None,
    validate_provider: bool = False,
) -> dict[str, Any]:
    """Check whether a runner config is ready to launch without creating samples."""
    loaded_env_keys = _load_env_file(config.env_file)
    samples = planned_samples(config)
    paired_block_plans = _plan_development_paired_blocks(config, samples)
    block_preparation_policies = _plan_block_preparation_policy(
        config, samples, paired_block_plans
    )
    planned_block_refs = _paired_block_refs_by_sample(
        paired_block_plans,
        {
            paired_block_id: plan.artifact_ref
            for paired_block_id, plan in paired_block_plans.items()
        },
    )
    run_dir = config.run_root / run_id if run_id else None
    required_tools = ("verilator", "iverilog", "vvp", "yosys")
    tools = _discover_tool_statuses(required_tools)
    errors: list[str] = []
    warnings: list[str] = []

    missing_tools = [tool for tool, status in tools.items() if status == "missing"]
    if missing_tools:
        warnings.append("missing HDL tools: " + ", ".join(missing_tools))

    if run_dir is not None and run_dir.exists():
        warnings.append("run directory already exists: " + str(run_dir))

    if not samples:
        errors.append("no planned samples")
    errors.extend(_analysis_population_errors(samples))
    seed_capabilities, seed_capability_errors = _seed_capability_diagnostics(
        config, samples
    )
    errors.extend(seed_capability_errors)
    for manifest in sorted(
        {
            sample.public_l2_harness_manifest
            for sample in samples
            if sample.public_l2_harness_manifest
        }
    ):
        try:
            load_development_public_l2_harness(Path(manifest))
        except PublicL2HarnessError as exc:
            errors.append(f"invalid public L2 harness manifest: {exc}")
    provider_auth, auth_errors = _source_auth_diagnostics(config, samples, validate_provider)
    errors.extend(auth_errors)

    providers = {sample.source for sample in samples}
    providers.add(config.repair_provider)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "planned_samples": len(samples),
        "samples": [
            _preflight_sample_preview(
                sample,
                config,
                paired_block_ref=planned_block_refs.get(sample.sample_id),
            )
            for sample in samples
        ],
        "run_dir": str(run_dir) if run_dir is not None else "",
        "tools": tools,
        "providers": sorted(provider for provider in providers if provider),
        "env_file": _env_file_label(config.env_file),
        "api_keys": _api_key_diagnostics(config, loaded_env_keys),
        "provider_auth": provider_auth,
        "provider_seed_capabilities": seed_capabilities,
        "block_preparation_policies": block_preparation_policies,
    }


def _preflight_sample_preview(
    sample: PlannedSample,
    config: RunnerConfig,
    *,
    paired_block_ref: ArtifactRef | None = None,
) -> dict[str, Any]:
    metadata = sample.metadata(config, paired_block_ref=paired_block_ref)
    preview = {
        "sample_id": sample.sample_id,
        "source": sample.source,
        "task_type": sample.task_type,
        "family_id": sample.family_id,
        "width": sample.width,
        "requirement_style": str(metadata["requirement_style"]),
        "requirement": sample.requirement,
        "difficulty_tier": str(metadata["difficulty_tier"]),
        "topology_id": str(metadata["topology_id"]),
        "failure_origin": str(metadata["failure_origin"]),
        "measurement_point": str(metadata["measurement_point"]),
        "evaluation_line": str(metadata["evaluation_line"]),
        "system_his_schema_version": str(metadata["system_his_schema_version"]),
        "training_split": str(metadata["training_split"]),
        "contract_skeleton_mode": str(metadata["contract_skeleton_mode"]),
        "method_condition": str(metadata["method_condition"]),
        "analysis_population": str(metadata["analysis_population"]),
        "semantic_instance_id": str(metadata["semantic_instance_id"]),
        "replicate_id": str(metadata["replicate_id"]),
        "decoding_seed": metadata["decoding_seed"],
        "paired_block_id": str(metadata["paired_block_id"]),
        "execution_schedule_seed": metadata["execution_schedule_seed"],
        "decoding_control_mode": str(metadata["decoding_control_mode"]),
        "pairing_identity_source": str(metadata["pairing_identity_source"]),
        "requirement_audit_manifest": str(metadata["requirement_audit_manifest"]),
        "requirement_boundary": {
            key: metadata["requirement_boundary"][key]
            for key in (
                "boundary_version",
                "requirement_id",
                "envelope_sha256",
                "capability_profile_id",
                "capability_profile_sha256",
                "disposition",
                "decision_sha256",
            )
        },
    }
    if "family_recipe_decision" in metadata:
        preview["family_recipe_decision"] = metadata["family_recipe_decision"]
    if "episode_pack" in metadata:
        pack = metadata["episode_pack"]
        preview["episode_pack"] = {
            "pack_id": pack["pack_id"],
            "pack_sha256": pack["pack_sha256"],
            "public_projection_sha256": pack["public_context"][
                "public_projection_sha256"
            ],
        }
        if paired_block_ref is not None:
            preview["episode_pack"]["paired_block_ref"] = (
                paired_block_ref.to_dict()
            )
    return preview


def _discover_tool_statuses(tools: tuple[str, ...]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for tool in tools:
        statuses[tool] = "found" if shutil.which(tool) or resolve_executable(tool) else "missing"
    return statuses


def _project_request_for_sample(sample: PlannedSample) -> ProjectRequest:
    return ProjectRequest(
        task_type=sample.task_type,
        width=sample.width,
        project_name=sample.project_name,
        description=sample.requirement,
    )


def _platform_profile_for_config(config: RunnerConfig) -> PlatformProfile:
    return PlatformProfile(name=config.platform, vendor="generic", toolchain="open_source")


def run_batch(config: RunnerConfig, run_id: str | None = None, resume: bool = True) -> dict[str, Any]:
    samples = planned_samples(config)
    paired_block_plans = _plan_development_paired_blocks(config, samples)
    block_preparation_policies = _plan_block_preparation_policy(
        config, samples, paired_block_plans
    )
    protocol_errors = _analysis_population_errors(samples)
    _, seed_capability_errors = _seed_capability_diagnostics(config, samples)
    protocol_errors.extend(seed_capability_errors)
    if protocol_errors:
        raise SystemExit("; ".join(protocol_errors))
    _load_env_file(config.env_file)
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = config.run_root / run_id
    state_path = run_dir / "run_state.json"
    events_path = run_dir / "events.jsonl"
    summary_path = run_dir / "summary.json"
    config_fingerprint = _config_fingerprint(config)
    run_dir.mkdir(parents=True, exist_ok=True)
    existing_run = state_path.exists()

    if resume and existing_run:
        state = read_run_state(state_path)
        if state.config_fingerprint and state.config_fingerprint != config_fingerprint:
            raise SystemExit(
                f"Run config fingerprint mismatch for {run_id}: "
                f"existing {state.config_fingerprint}, current {config_fingerprint}"
            )
    else:
        state = initial_run_state(run_id, config_fingerprint=config_fingerprint)
        write_run_state(state_path, state)

    method_artifact_store = ArtifactStore(run_dir / "method_artifacts")
    paired_block_refs = _materialize_development_paired_blocks(
        paired_block_plans,
        method_artifact_store,
    )
    paired_block_refs_by_sample = _paired_block_refs_by_sample(
        paired_block_plans,
        paired_block_refs,
    )
    samples = _order_samples_by_paired_blocks(
        samples,
        paired_block_plans,
        paired_block_refs,
        method_artifact_store,
    )
    paired_execution_ordinals = _paired_execution_ordinals(
        samples,
        paired_block_plans,
        paired_block_refs,
        method_artifact_store,
    )
    tool_environment = collect_development_tool_environment()
    tool_environment_ref = method_artifact_store.put_validated_json(
        "tool-environments/development-preflight",
        tool_environment,
        contract_key="development_tool_environment",
    )
    l4_tool_environment = collect_development_l4_tool_environment(
        open_enabled=config.run_l4_open and config.l4_open.run_policy != "never",
        commercial_enabled=(
            config.run_l4_commercial and config.l4_commercial.run_policy != "never"
        ),
        probe_authorized=_l4_version_probe_authorized(),
        open_probe_command=openxc7_tool_probe_command(),
        vivado_command=(
            os.environ.get("SR2FPGA_VIVADO_COMMAND") or config.l4_commercial.command
        ),
    )
    l4_tool_environment_ref = method_artifact_store.put_validated_json(
        "tool-environments/development-l4-preflight",
        l4_tool_environment,
        contract_key="development_l4_tool_environment",
    )
    tool_versions = _measurement_tool_versions(
        config,
        tool_environment=tool_environment,
    )
    tool_versions.update(l4_tool_version_projection(l4_tool_environment))
    freeze_manifest = _measurement_freeze_manifest(
        config,
        run_id,
        config_fingerprint,
        samples,
        tool_versions=tool_versions,
        tool_environment_ref=tool_environment_ref.to_dict(),
        l4_tool_environment_ref=l4_tool_environment_ref.to_dict(),
        paired_block_refs=paired_block_refs_by_sample,
        paired_execution_ordinals=paired_execution_ordinals,
        block_preparation_policies=block_preparation_policies,
    )
    freeze_fingerprint = write_or_validate_freeze(
        run_dir / "measurement_freeze.json",
        freeze_manifest,
        resume=resume and existing_run,
    )
    prepared_blocks = _prepare_complete_blocks(
        config=config,
        samples=samples,
        paired_block_plans=paired_block_plans,
        paired_block_refs=paired_block_refs,
        store=method_artifact_store,
        freeze_fingerprint=freeze_fingerprint,
    )
    block_preparation_audit = {
        paired_block_id: _prepared_block_audit_record(
            block_preparation_policies[paired_block_id], runtime
        )
        for paired_block_id, runtime in sorted(prepared_blocks.items())
    }
    _write_json(
        run_dir / "config.json",
        _run_config_projection(config, block_preparation_audit),
    )
    project_generators: dict[str, object | None] = {}
    repairers: dict[str, object | None] = {}
    paired_artifact_coordinator = PairedArtifactCoordinator(method_artifact_store)
    development_hidden_authority = (
        _development_hidden_authority_for_run(
            run_dir,
            candidate_store=method_artifact_store,
        )
        if any(
            sample.analysis_population in {"development", "excluded"}
            for sample in samples
        )
        else None
    )

    for index, sample in enumerate(samples):
        if index < state.next_index or should_skip_sample(state, sample.sample_id):
            continue
        if (config.dataset_root / sample.sample_id).exists():
            state = _record_rejected(state, sample.sample_id, index + 1, "sample_exists")
            _append_event(events_path, {"event": "sample_exists", "sample_id": sample.sample_id})
            write_run_state(state_path, state)
            continue

        paired_block_ref = paired_block_refs_by_sample.get(sample.sample_id)
        execution_ordinal = paired_execution_ordinals.get(sample.sample_id)
        prepared_block_runtime = prepared_blocks.get(sample.paired_block_id)
        sample_block_preparation_audit = block_preparation_audit.get(
            sample.paired_block_id
        )
        sample_metadata = sample.metadata(
            config,
            paired_block_ref=paired_block_ref,
        )
        sample_metadata["freeze_fingerprint"] = freeze_fingerprint
        sample_metadata["tool_environment_ref"] = tool_environment_ref.to_dict()
        sample_metadata["l4_tool_environment_ref"] = (
            l4_tool_environment_ref.to_dict()
        )
        if sample_block_preparation_audit is not None:
            sample_metadata["block_preparation_audit"] = dict(
                sample_block_preparation_audit
            )
        episode_pack_ref = None
        episode_pack = sample_metadata.get("episode_pack")
        if isinstance(episode_pack, dict):
            episode_pack_ref = method_artifact_store.put_validated_json(
                f"episode-packs/{sample.sample_id}",
                episode_pack,
                contract_key="episode_pack",
            )
        event_sink = _generation_event_sink(
            events_path,
            sample,
            config,
            artifact_store=method_artifact_store,
            paired_block_ref=paired_block_ref,
            execution_ordinal=execution_ordinal,
            block_preparation_audit=sample_block_preparation_audit,
        )
        method_condition = str(sample_metadata.get("method_condition", "")).strip().upper()
        attempt_cost_router = (
            AttemptCostLedgerRouter()
            if method_condition in IMPLEMENTED_METHOD_CONDITIONS
            else None
        )
        standalone_model_call_ceiling = int(
            sample_metadata["model_call_budget"]["max_model_calls"]
        )
        runtime_model_call_ceiling = standalone_model_call_ceiling
        if prepared_block_runtime is not None:
            runtime_model_call_ceiling = prepared_block_runtime.exclusive_model_call_ceilings[
                method_condition
            ]
            sample_metadata["standalone_model_call_ceiling"] = (
                standalone_model_call_ceiling
            )
            sample_metadata["exclusive_model_call_ceiling"] = (
                runtime_model_call_ceiling
            )
        model_budget = ModelCallBudget(
            runtime_model_call_ceiling,
            event_sink=event_sink,
            attempt_cost_ledger_provider=(
                attempt_cost_router.current if attempt_cost_router is not None else None
            ),
            max_parser_schema_retries=int(
                sample_metadata["model_call_budget"]["max_parser_schema_retries"]
            ),
            standalone_max_calls=(
                standalone_model_call_ceiling
                if prepared_block_runtime is not None
                else None
            ),
            budget_scope=(
                "paired_block_exclusive"
                if prepared_block_runtime is not None
                else "standalone"
            ),
        )
        boundary = sample_metadata.get("requirement_boundary")
        boundary_ready = isinstance(boundary, dict) and boundary.get("disposition") == "ready"
        if boundary_ready:
            sample_project_generator = _project_generator_for_sample(
                project_generators,
                config,
                sample,
                events_path,
                model_budget=model_budget,
                metadata=sample_metadata,
                method_artifact_store=method_artifact_store,
                paired_artifact_coordinator=paired_artifact_coordinator,
                paired_block_ref=paired_block_ref,
                execution_ordinal=execution_ordinal,
                prepared_block_runtime=prepared_block_runtime,
                block_preparation_audit=sample_block_preparation_audit,
            )
            sample_repairer = (
                _repairer_for_sample(
                    repairers,
                    config,
                    sample,
                    model_budget=model_budget,
                )
                if method_condition in {"M1", "M5"}
                and model_budget.max_calls > 0
                else None
            )
        else:
            # Preserve the stop outcome without resolving credentials or
            # constructing a method-specific model client.  The common intake
            # decision is authoritative before generation allocation.
            sample_project_generator = None
            sample_repairer = None
        request = _project_request_for_sample(sample)
        platform = _platform_profile_for_config(config)
        trusted_public_l2_harness = (
            load_development_public_l2_harness(
                Path(sample.public_l2_harness_manifest)
            )
            if sample.public_l2_harness_manifest
            else None
        )
        attempt_cost_ledger_factory = None
        if attempt_cost_router is not None:
            accounting_input_hashes = {
                freeze_fingerprint,
                tool_environment_ref.sha256,
                l4_tool_environment_ref.sha256,
            }
            if episode_pack_ref is not None:
                accounting_input_hashes.add(episode_pack_ref.sha256)
            if paired_block_ref is not None:
                accounting_input_hashes.add(paired_block_ref.sha256)
            if prepared_block_runtime is not None:
                accounting_input_hashes.add(
                    prepared_block_runtime.prepared.manifest_ref.sha256
                )
                accounting_input_hashes.update(
                    reference.sha256
                    for reference in prepared_block_runtime.prepared.event_refs
                )
            if trusted_public_l2_harness is not None:
                accounting_input_hashes.update(
                    {
                        trusted_public_l2_harness.manifest_sha256,
                        trusted_public_l2_harness.bundle_sha256,
                    }
                )
            episode_pack = sample_metadata.get("episode_pack")
            if isinstance(episode_pack, dict):
                public_context = episode_pack.get("public_context")
                if isinstance(public_context, dict):
                    public_projection_sha256 = public_context.get(
                        "public_projection_sha256"
                    )
                    if isinstance(public_projection_sha256, str):
                        accounting_input_hashes.add(public_projection_sha256)

            def attempt_cost_ledger_factory(attempt_id: int) -> AttemptCostLedger:
                return AttemptCostLedger(
                    method_artifact_store,
                    episode_id=sample.sample_id,
                    attempt_id=f"attempt-{attempt_id:03d}",
                    method_condition=method_condition,
                    failure_origin=str(sample_metadata["failure_origin"]) or None,
                    candidate_id=f"{sample.sample_id}-attempt-{attempt_id:03d}",
                    input_artifact_hashes=accounting_input_hashes,
                )

        agent = DataGenerationAgent(
            config.dataset_root,
            project_generator=sample_project_generator,
            repairer=sample_repairer,
            repair_provider_name=str(sample_metadata["repair_provider_resolved"]),
            max_attempts=_sample_attempt_limit(config, method_condition),
            enable_openxc7_l4=_l4_open_enabled_for_sample(config, sample),
            openxc7_tool=config.l4_open.tool,
            openxc7_part=config.l4_open.target_part,
            openxc7_board_profile=config.l4_open.board_profile,
            openxc7_timeout_seconds=config.l4_open.timeout_seconds,
            enable_vivado_l4=_l4_commercial_enabled_for_sample(config, sample),
            vivado_tool=config.l4_commercial.tool,
            vivado_command=config.l4_commercial.command,
            vivado_part=config.l4_commercial.target_part,
            vivado_timeout_seconds=config.l4_commercial.timeout_seconds,
            enable_independent_oracle=config.run_independent_oracle,
            development_hidden_evaluation_authority=development_hidden_authority,
            development_hidden_private_commitment=_development_hidden_private_commitment(
                str(config.dataset_root),
                sample,
                sample_metadata,
                run_id=run_id,
            ),
            development_public_candidate_store=(
                method_artifact_store
                if sample.analysis_population in {"development", "excluded"}
                else None
            ),
            development_public_evaluator_store=(
                ArtifactStore(
                    run_dir / DEVELOPMENT_PUBLIC_AUTHORITY_DIR / "evaluator_store"
                )
                if sample.analysis_population in {"development", "excluded"}
                else None
            ),
            development_public_workspace_root=(
                run_dir
                / DEVELOPMENT_PUBLIC_AUTHORITY_DIR
                / "workspaces"
                / sample.sample_id
                if sample.analysis_population in {"development", "excluded"}
                else None
            ),
            development_trusted_public_l2_harness=trusted_public_l2_harness,
            attempt_cost_ledger_factory=attempt_cost_ledger_factory,
            attempt_cost_router=attempt_cost_router,
            tool_versions=tool_versions,
            tool_environment_ref=tool_environment_ref.to_dict(),
            l4_tool_environment=l4_tool_environment,
            l4_tool_environment_ref=l4_tool_environment_ref.to_dict(),
        )
        result = agent.run_one(
            sample_id=sample.sample_id,
            requirement=sample.requirement,
            request=request,
            platform=platform,
            metadata=sample_metadata,
        )
        _update_sample_model_budget(
            config.dataset_root / sample.sample_id,
            model_budget.summary(),
        )
        labels = _read_labels(config.dataset_root / sample.sample_id)
        bucket = classify_sample_bucket(labels)
        state = _record_completed(state, sample.sample_id, index + 1, bucket, config.dataset_root / sample.sample_id)
        completion_event = {
            "event": "sample_completed",
            "sample_id": sample.sample_id,
            "source": sample.source,
            "failure_origin": _sample_failure_origin(sample, config),
            "difficulty_tier": sample.difficulty_tier,
            "task_type": sample.task_type,
            "semantic_instance_id": sample.semantic_instance_id,
            "decoding_seed": sample.decoding_seed,
            "paired_block_id": sample.paired_block_id,
            "pairing_identity_source": sample.pairing_identity_source,
            "width": sample.width,
            "pass_level": result["pass_level"],
            "bucket": bucket,
        }
        if sample.replicate_id:
            completion_event.update(
                {
                    "replicate_id": sample.replicate_id,
                    "execution_schedule_seed": sample.execution_schedule_seed,
                    "decoding_control_mode": sample.decoding_control_mode,
                }
            )
        if paired_block_ref is not None:
            completion_event["paired_block_ref"] = paired_block_ref.to_dict()
            completion_event["execution_ordinal"] = execution_ordinal
            completion_event["freeze_fingerprint"] = freeze_fingerprint
        if sample_block_preparation_audit is not None:
            completion_event["block_preparation_audit"] = dict(
                sample_block_preparation_audit
            )
        if result.get("cost_summary_refs"):
            completion_event["cost_summary_refs"] = list(result["cost_summary_refs"])
        if result.get("canonical_trajectory_ref"):
            completion_event["canonical_trajectory_ref"] = dict(
                result["canonical_trajectory_ref"]
            )
        if result.get("development_hidden_outcome_ref"):
            completion_event["development_hidden_outcome_ref"] = dict(
                result["development_hidden_outcome_ref"]
            )
        if result.get("development_hidden_conformance_outcome_ref"):
            completion_event["development_hidden_conformance_outcome_ref"] = dict(
                result["development_hidden_conformance_outcome_ref"]
            )
        for ref_field in (
            "development_terminal_selection_ref",
            "development_selected_public_outcome_ref",
            "development_terminal_public_outcome_ref",
        ):
            if result.get(ref_field):
                completion_event[ref_field] = dict(result[ref_field])
        if (
            result.get("development_terminal_public_outcome_ref")
            and sample_metadata.get("analysis_population") == "excluded"
        ):
            public_evaluation, public_evaluation_ref = (
                project_development_public_evaluation(
                    method_artifact_store,
                    sample_dir=Path(result["sample_dir"]),
                    episode_id=sample.sample_id,
                    method_condition=method_condition,
                    analysis_population="excluded",
                    terminal_public_outcome_ref=ArtifactRef(
                        **result["development_terminal_public_outcome_ref"]
                    ),
                )
            )
            completion_event["development_public_evaluation_ref"] = (
                public_evaluation_ref.to_dict()
            )
            repair_projection = public_evaluation["repair"]
            if (
                repair_projection["reconciliation_status"] == "complete"
                and not repair_projection["issues"]
            ):
                trajectory_ref_payload = result.get("canonical_trajectory_ref")
                if not isinstance(trajectory_ref_payload, dict):
                    raise RuntimeError(
                        "excluded terminal outcome is missing canonical trajectory lineage"
                    )
                _, episode_outcome_ref = reconcile_development_episode_outcome(
                    method_artifact_store,
                    public_evaluation_ref=public_evaluation_ref,
                    trajectory_ref=ArtifactRef(**trajectory_ref_payload),
                )
                completion_event["development_episode_outcome_ref"] = (
                    episode_outcome_ref.to_dict()
                )
        if episode_pack_ref is not None:
            completion_event["method_condition"] = method_condition
            completion_event["analysis_population"] = str(
                sample_metadata["analysis_population"]
            )
            completion_event["episode_pack_ref"] = episode_pack_ref.to_dict()
            completion_event["episode_pack_sha256"] = episode_pack["pack_sha256"]
            completion_event["public_projection_sha256"] = episode_pack[
                "public_context"
            ]["public_projection_sha256"]
        method_artifact_record = _method_artifact_completion_record(
            sample_project_generator,
            sample_metadata,
        )
        if method_artifact_record is not None:
            completion_event["method_artifacts"] = method_artifact_record
            failure_record = method_artifact_record.get("failure")
            if (
                sample_metadata.get("analysis_population") == "excluded"
                and method_condition == "M4"
                and isinstance(failure_record, dict)
                and failure_record.get("stage") in {"h0", "h1", "h2", "h3"}
            ):
                if episode_pack_ref is None or not result.get(
                    "canonical_trajectory_ref"
                ):
                    raise RuntimeError(
                        "M4 H-stage stop is missing episode-pack or trajectory lineage"
                    )
                planning_ref_payload = method_artifact_record.get(
                    "planning_artifact_ref"
                )
                event_ref_payloads = method_artifact_record.get(
                    "method_event_refs"
                )
                if (
                    not isinstance(planning_ref_payload, dict)
                    or not isinstance(event_ref_payloads, list)
                ):
                    raise RuntimeError("M4 H-stage stop method artifacts are incomplete")
                _, stop_outcome_ref = (
                    reconcile_development_pre_candidate_stop_outcome(
                        method_artifact_store,
                        episode_pack_ref=episode_pack_ref,
                        planning_artifact_ref=ArtifactRef(**planning_ref_payload),
                        method_event_refs=(
                            ArtifactRef(**payload) for payload in event_ref_payloads
                        ),
                        trajectory_ref=ArtifactRef(
                            **result["canonical_trajectory_ref"]
                        ),
                        platform=platform,
                    )
                )
                completion_event[
                    "development_pre_candidate_stop_outcome_ref"
                ] = stop_outcome_ref.to_dict()
            if (
                sample_metadata.get("analysis_population") == "excluded"
                and method_condition == "M5"
                and method_artifact_record.get("his_corrections_used") == 1
            ):
                required_refs = {
                    "initial_planning_artifact_ref": method_artifact_record.get(
                        "initial_planning_artifact_ref"
                    ),
                    "planning_artifact_ref": method_artifact_record.get(
                        "planning_artifact_ref"
                    ),
                    "candidate_artifact_ref": method_artifact_record.get(
                        "candidate_artifact_ref"
                    ),
                    "canonical_trajectory_ref": result.get(
                        "canonical_trajectory_ref"
                    ),
                    "development_episode_outcome_ref": completion_event.get(
                        "development_episode_outcome_ref"
                    ),
                }
                event_ref_payloads = method_artifact_record.get("method_event_refs")
                if (
                    episode_pack_ref is None
                    or not all(isinstance(value, dict) for value in required_refs.values())
                    or not isinstance(event_ref_payloads, list)
                ):
                    raise RuntimeError(
                        "M5 HIS correction is missing artifact-derived acceptance lineage"
                    )
                _, correction_outcome_ref = (
                    reconcile_development_his_correction_outcome(
                        method_artifact_store,
                        episode_pack_ref=episode_pack_ref,
                        initial_his_ref=ArtifactRef(
                            **required_refs["initial_planning_artifact_ref"]
                        ),
                        corrected_his_ref=ArtifactRef(
                            **required_refs["planning_artifact_ref"]
                        ),
                        method_event_refs=(
                            ArtifactRef(**payload) for payload in event_ref_payloads
                        ),
                        candidate_artifact_ref=ArtifactRef(
                            **required_refs["candidate_artifact_ref"]
                        ),
                        trajectory_ref=ArtifactRef(
                            **required_refs["canonical_trajectory_ref"]
                        ),
                        development_episode_outcome_ref=ArtifactRef(
                            **required_refs["development_episode_outcome_ref"]
                        ),
                        platform=platform,
                    )
                )
                completion_event[
                    "development_his_correction_outcome_ref"
                ] = correction_outcome_ref.to_dict()
        _append_event(events_path, completion_event)
        write_run_state(state_path, state)

    if config.refresh_exports:
        DatasetRecorder(config.dataset_root).export_training_views(config.export_root)
        state = RunState(
            run_id=state.run_id,
            next_index=state.next_index,
            completed_samples=state.completed_samples,
            buckets=state.buckets,
            failure_types=state.failure_types,
            exports_refreshed=True,
            config_fingerprint=state.config_fingerprint,
        )
        write_run_state(state_path, state)

    paired_results: dict[str, Any] = {}
    if config.repair_provider == "same_as_source":
        measured_sample_ids = [
            sample_id
            for sample_id in state.completed_samples
            if _sample_has_measurement(config.dataset_root / sample_id)
        ]
        paired_results = collect_paired_results(config.dataset_root, measured_sample_ids)
        paired_results["missing_measurement_samples"] = [
            sample_id for sample_id in state.completed_samples if sample_id not in set(measured_sample_ids)
        ]
        _write_json(run_dir / "paired_results.json", paired_results)

    summary = _summary(config, state)
    if paired_results:
        summary["paired_results"] = paired_results
    summary["freeze_fingerprint"] = freeze_fingerprint
    if block_preparation_audit:
        summary["audit_only"] = {
            "block_preparations": block_preparation_audit,
        }
    _write_json(summary_path, summary)
    (run_dir / "baseline_report.md").write_text(
        render_markdown(str(summary["run_id"]), baseline_rows(summary), summary=summary),
        encoding="utf-8",
    )
    return summary


def _analysis_population_errors(samples: list[PlannedSample]) -> list[str]:
    errors: list[str] = []
    if any(sample.analysis_population == "official_vpp" for sample in samples):
        errors.append(
            "official_vpp execution is disabled until a signed G4b episode-pack projection "
            "and evaluator-owned hidden channel are wired"
        )
    if any(sample.analysis_population == "ambiguity_audit" for sample in samples):
        errors.append(
            "ambiguity_audit cases require the sealed evaluator-owned requirement-audit "
            "artifact path; they must not enter the project runner"
        )
        validated: set[str] = set()
        for sample in samples:
            if sample.analysis_population != "ambiguity_audit":
                continue
            if not sample.requirement_audit_manifest:
                errors.append(
                    f"ambiguity_audit sample {sample.sample_id} is missing requirement_audit_manifest"
                )
                continue
            if sample.requirement_audit_manifest in validated:
                continue
            validated.add(sample.requirement_audit_manifest)
            try:
                load_requirement_audit_manifest(sample.requirement_audit_manifest)
            except ValueError as error:
                errors.append(
                    f"ambiguity_audit manifest '{sample.requirement_audit_manifest}' is invalid "
                    f"for sample {sample.sample_id}: {error}"
                )
    return errors


def _development_hidden_authority_for_run(
    run_dir: Path,
    *,
    candidate_store: ArtifactStore,
) -> DevelopmentHiddenEvaluationAuthority:
    authority_root = run_dir / DEVELOPMENT_HIDDEN_AUTHORITY_DIR
    evaluator_store = ArtifactStore(authority_root / "evaluator_store")
    return DevelopmentHiddenEvaluationAuthority(
        candidate_store,
        evaluator_store,
        _development_hidden_evaluator,
    )


def _development_hidden_evaluator(_input) -> dict[str, str]:
    return {
        "outcome": "opaque",
        "private_execution": "completed",
        "evaluator_scope": "development_hidden",
    }


def _development_hidden_private_commitment(
    dataset_root: str,
    sample: PlannedSample,
    metadata: dict[str, Any],
    *,
    run_id: str | None,
) -> bytes:
    payload = {
        "evaluation_scope": "excluded_paired_block_hidden_commitment",
        "run_id": run_id or "",
        "requirement_sha256": sample.requirement_sha256,
        "semantic_instance_id": sample.semantic_instance_id,
        "replicate_id": sample.replicate_id,
        "decoding_seed": sample.decoding_seed,
        "paired_block_id": sample.paired_block_id,
        "execution_schedule_seed": sample.execution_schedule_seed,
        "decoding_control_mode": sample.decoding_control_mode,
        "paired_block_sha256": (
            metadata.get("paired_block_ref", {}).get("sha256")
            if isinstance(metadata.get("paired_block_ref"), dict)
            else None
        ),
        "analysis_population": str(metadata.get("analysis_population", "")),
    }
    if sample.analysis_population != "excluded":
        payload.update(
            {
                "dataset_root": dataset_root,
                "sample_id": sample.sample_id,
                "task_type": sample.task_type,
                "method_condition": str(metadata.get("method_condition", "")),
            }
        )
    digest = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(digest.encode("utf-8")).digest()


def initial_run_state(run_id: str, config_fingerprint: str = "") -> RunState:
    return RunState(
        run_id=run_id,
        next_index=0,
        completed_samples=[],
        buckets={
            "success_l3": [],
            "repair_trajectory": [],
            "not_run": [],
            "rejected": [],
        },
        failure_types={},
        exports_refreshed=False,
        config_fingerprint=config_fingerprint,
    )


def read_run_state(path: Path) -> RunState:
    data = json.loads(path.read_text(encoding="utf-8"))
    return RunState(
        run_id=str(data["run_id"]),
        next_index=int(data["next_index"]),
        completed_samples=[str(item) for item in data.get("completed_samples", [])],
        buckets={str(key): [str(item) for item in value] for key, value in data.get("buckets", {}).items()},
        failure_types={str(key): int(value) for key, value in data.get("failure_types", {}).items()},
        exports_refreshed=bool(data.get("exports_refreshed", False)),
        config_fingerprint=str(data.get("config_fingerprint", "")),
    )


def write_run_state(path: Path, state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def should_skip_sample(state: RunState, sample_id: str) -> bool:
    return sample_id in set(state.completed_samples)


def classify_sample_bucket(labels: dict[str, Any]) -> str:
    if _passes_at_least(str(labels.get("pass_level", "")), "L3"):
        return "success_l3"
    if labels.get("pass_level") == "GEN_FAIL":
        return "rejected"
    if int(labels.get("failure_count", 0)) > 0:
        return "repair_trajectory"
    if labels.get("l2_sim_status") == "not_run":
        return "not_run"
    return "rejected"


def _config_to_jsonable(config: RunnerConfig) -> dict[str, Any]:
    payload = asdict(config)
    for task in payload["tasks"]:
        if not task["requirement"]:
            del task["requirement"]
    for source_name, connection in config.sources.items():
        source_payload = payload["sources"][source_name]
        source_payload["seed_capability_ref"] = _seed_capability_manifest_ref(
            connection
        )
        del source_payload["seed_capability_manifest"]
    payload["dataset_root"] = str(config.dataset_root)
    payload["export_root"] = str(config.export_root)
    payload["run_root"] = str(config.run_root)
    payload["env_file"] = _env_file_label(config.env_file)
    return payload


def _run_config_projection(
    config: RunnerConfig,
    block_preparation_audit: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = _config_to_jsonable(config)
    if block_preparation_audit:
        payload["audit_only"] = {
            "block_preparations": {
                paired_block_id: dict(record)
                for paired_block_id, record in sorted(
                    block_preparation_audit.items()
                )
            }
        }
    return payload


def _config_fingerprint(config: RunnerConfig) -> str:
    payload = json.dumps(_config_to_jsonable(config), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _measurement_freeze_manifest(
    config: RunnerConfig,
    run_id: str,
    config_fingerprint: str,
    samples: list[PlannedSample],
    *,
    tool_versions: dict[str, str] | None = None,
    tool_environment_ref: dict[str, Any] | None = None,
    l4_tool_environment_ref: dict[str, Any] | None = None,
    paired_block_refs: Mapping[str, ArtifactRef] | None = None,
    paired_execution_ordinals: Mapping[str, int] | None = None,
    block_preparation_policies: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    source_names = sorted({sample.source for sample in samples})
    source_records = []
    for source_name in source_names:
        connection = resolve_source_connection(config, source_name)
        source_records.append(
            {
                "name": source_name,
                "kind": connection.kind,
                "model": connection.model or connection.kind,
                "generation_mode": connection.generation_mode,
                "timeout_seconds": connection.timeout_seconds,
                "transport_attempts": connection.transport_attempts,
                "max_tokens": connection.max_tokens,
                "wire_api": connection.wire_api,
                "reasoning_effort": connection.reasoning_effort,
                "disable_response_storage": connection.disable_response_storage,
                "seed_capability_ref": _seed_capability_manifest_ref(connection),
            }
        )
    block_refs = paired_block_refs or {}
    execution_ordinals = paired_execution_ordinals or {}
    sample_records = [
        _measurement_freeze_sample_record(
            sample,
            config,
            paired_block_ref=block_refs.get(sample.sample_id),
            execution_ordinal=execution_ordinals.get(sample.sample_id),
        )
        for sample in samples
    ]
    timeouts = {
        f"source:{record['name']}": int(record["timeout_seconds"])
        for record in source_records
    }
    timeouts["l4_open"] = config.l4_open.timeout_seconds
    manifest = build_measurement_freeze(
        run_id=run_id,
        config_fingerprint=config_fingerprint,
        sample_records=sample_records,
        source_records=source_records,
        max_attempts=config.max_attempts,
        timeouts=timeouts,
        tool_versions=(
            dict(tool_versions)
            if tool_versions is not None
            else _measurement_tool_versions(config)
        ),
        l4_family_ids=list(getattr(config.l4_open, "family_ids", ())),
        tool_environment_ref=tool_environment_ref,
        l4_tool_environment_ref=l4_tool_environment_ref,
    )
    if block_preparation_policies:
        manifest["block_preparation_policies"] = {
            paired_block_id: dict(policy)
            for paired_block_id, policy in sorted(
                block_preparation_policies.items()
            )
        }
    return manifest


def _measurement_freeze_sample_record(
    sample: PlannedSample,
    config: RunnerConfig,
    *,
    paired_block_ref: ArtifactRef | None = None,
    execution_ordinal: int | None = None,
) -> dict[str, Any]:
    record = {
        "sample_id": sample.sample_id,
        "source": sample.source,
        "family_id": sample.family_id,
        "task_type": sample.task_type,
        "topology_id": sample.topology_id,
        "width": sample.width,
        "requirement_style": sample.requirement_style,
        "paired_requirement_id": sample.paired_requirement_id,
        "requirement_sha256": sample.requirement_sha256,
        "method_condition": _sample_method_condition(sample, config),
        "analysis_population": sample.analysis_population,
        "semantic_instance_id": sample.semantic_instance_id,
        "decoding_seed": sample.decoding_seed,
        "paired_block_id": sample.paired_block_id,
        "pairing_identity_source": sample.pairing_identity_source,
        "max_model_calls": _sample_model_call_ceiling(sample, config),
    }
    if sample.replicate_id:
        record.update(
            {
                "replicate_id": sample.replicate_id,
                "execution_schedule_seed": sample.execution_schedule_seed,
                "decoding_control_mode": sample.decoding_control_mode,
            }
        )
    if paired_block_ref is not None:
        record["paired_block_ref"] = paired_block_ref.to_dict()
        record["execution_ordinal"] = execution_ordinal
    metadata = sample.metadata(config)
    boundary = metadata["requirement_boundary"]
    record["requirement_boundary"] = {
        key: boundary[key]
        for key in (
            "boundary_version",
            "requirement_id",
            "envelope_sha256",
            "capability_profile_id",
            "capability_profile_sha256",
            "disposition",
            "decision_sha256",
        )
    }
    decision = metadata.get("family_recipe_decision")
    if decision is not None:
        record["family_recipe_decision"] = decision
    pack = metadata.get("episode_pack")
    if pack is not None:
        record["episode_pack"] = pack
    return record


def _measurement_tool_versions(
    config: RunnerConfig,
    *,
    tool_environment: dict[str, Any] | None = None,
) -> dict[str, str]:
    versions = tool_version_projection(
        tool_environment or collect_development_tool_environment()
    )
    versions["l4_open"] = config.l4_open.tool if config.run_l4_open else "disabled"
    return versions


def _l4_version_probe_authorized() -> bool:
    return os.environ.get(L4_VERSION_PROBE_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _load_env_file(path: Path) -> set[str]:
    loaded: set[str] = set()
    if path == Path("") or not path.is_file():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _strip_env_value(value.strip())
        loaded.add(key)
    return loaded


def _strip_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _env_file_label(path: Path) -> str:
    return "" if path == Path("") else str(path)


def _api_key_diagnostics(config: RunnerConfig, loaded_env_keys: set[str]) -> dict[str, dict[str, object]]:
    value = os.environ.get(config.api_key_env, "")
    source = ""
    if value:
        source = _env_file_label(config.env_file) if config.api_key_env in loaded_env_keys else "environment"
    return {
        config.api_key_env: {
            "present": bool(value),
            "source": source,
            "fingerprint": _secret_fingerprint(value) if value else "",
        }
    }


def _secret_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def _seed_capability_diagnostics(
    config: RunnerConfig,
    samples: list[PlannedSample],
) -> tuple[dict[str, dict[str, str]], list[str]]:
    diagnostics: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    source_names = {sample.source for sample in samples}
    if config.repair_provider and config.repair_provider not in {
        "none",
        "same_as_source",
    }:
        source_names.add(config.repair_provider)
    for source in sorted(source_names):
        connection = resolve_source_connection(config, source)
        if connection.kind == "deterministic":
            diagnostics[source] = {
                "status": "not_applicable",
                "classification": "not_applicable",
                "paired_confirmatory_eligible": "false",
            }
            continue
        if connection.wire_api == "responses":
            diagnostics[source] = {
                "status": "ineligible",
                "classification": "seed_not_forwarded",
                "paired_confirmatory_eligible": "false",
            }
            if config.require_paired_confirmatory_seed_control:
                errors.append(
                    f"source {source} wire_api=responses cannot use a "
                    "seed-control capability because the adapter does not "
                    "forward seed"
                )
            continue
        if not connection.seed_capability_manifest:
            diagnostics[source] = {
                "status": "unavailable",
                "classification": "unverified",
                "paired_confirmatory_eligible": "false",
            }
            if config.require_paired_confirmatory_seed_control:
                errors.append(
                    f"source {source} lacks a provider seed capability manifest"
                )
            continue
        payload: dict[str, Any] | None = None
        try:
            payload = load_development_provider_seed_capability(
                connection.seed_capability_manifest
            )
            require_paired_confirmatory_seed_capability(
                payload,
                provider_adapter=(
                    "anthropic_compatible"
                    if connection.kind == "anthropic_compat"
                    else "openai_compatible"
                ),
                provider_model=connection.model,
                gateway_base_url=connection.base_url,
            )
        except ValueError as exc:
            diagnostics[source] = {
                "status": "ineligible",
                "classification": (
                    str(payload.get("seed_control_classification", "invalid"))
                    if payload is not None
                    else "invalid"
                ),
                "paired_confirmatory_eligible": "false",
            }
            if config.require_paired_confirmatory_seed_control:
                errors.append(f"source {source} seed-control ineligible: {exc}")
            continue
        diagnostics[source] = {
            "status": "eligible_candidate",
            "classification": str(payload["seed_control_classification"]),
            "paired_confirmatory_eligible": "true",
            "capability_profile_id": str(payload["capability_profile_id"]),
        }
    return diagnostics, errors


def _seed_capability_manifest_ref(
    connection: SourceConnection,
) -> dict[str, Any] | None:
    if not connection.seed_capability_manifest:
        return None
    manifest_path = Path(connection.seed_capability_manifest)
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise ValueError(
            "provider seed capability manifest is unreadable: "
            + connection.seed_capability_manifest
        ) from exc
    payload = load_development_provider_seed_capability(
        connection.seed_capability_manifest
    )
    return {
        "capability_profile_id": str(payload["capability_profile_id"]),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "seed_control_classification": str(
            payload["seed_control_classification"]
        ),
        "paired_confirmatory_eligible": bool(
            payload["paired_confirmatory_eligible"]
        ),
    }


def _source_auth_diagnostics(
    config: RunnerConfig,
    samples: list[PlannedSample],
    validate_provider: bool,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    diagnostics: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    seen: set[str] = set()
    for sample in samples:
        _check_source_auth(config, sample.source, seen, diagnostics, errors, validate_provider)
    if config.repair_provider and config.repair_provider not in {"none", "same_as_source"}:
        _check_source_auth(config, config.repair_provider, seen, diagnostics, errors, validate_provider)
    return diagnostics, errors


def _check_source_auth(
    config: RunnerConfig,
    source: str,
    seen: set[str],
    diagnostics: dict[str, dict[str, str]],
    errors: list[str],
    validate_provider: bool,
) -> None:
    if source in seen:
        return
    seen.add(source)
    connection = resolve_source_connection(config, source)
    if connection.kind == "deterministic":
        return
    if connection.kind not in LLM_SOURCE_KINDS:
        errors.append(
            f"Source '{source}' has unsupported kind '{connection.kind}'. "
            f"Supported kinds: {sorted(LLM_SOURCE_KINDS)}."
        )
        return
    api_key = os.environ.get(connection.api_key_env, "")
    if not api_key:
        diagnostics[source] = {
            "status": "skipped",
            "detail": f"{connection.api_key_env} is not set",
        }
        errors.append(f"{connection.api_key_env} is not set for source {source}")
        return
    if not validate_provider:
        diagnostics[source] = {"status": "not_checked", "detail": ""}
        return
    client = _preflight_client(connection, api_key)
    try:
        client.stream_chat(
            [
                {"role": "system", "content": "Return a tiny JSON object for authentication preflight."},
                {"role": "user", "content": "Return {\"ok\": true}."},
            ]
        )
    except RuntimeError as exc:
        diagnostics[source] = {
            "status": "failed",
            "detail": _sanitize_secret(str(exc), api_key),
        }
        errors.append(f"{source} provider auth failed")
        return
    diagnostics[source] = {"status": "ok", "detail": ""}


def _provider_auth_timeout_seconds(connection: SourceConnection) -> int:
    return max(20, min(connection.timeout_seconds, 120))


def _preflight_client(connection: SourceConnection, api_key: str):
    timeout_seconds = _provider_auth_timeout_seconds(connection)
    if connection.kind == "anthropic_compat":
        return AnthropicCompatibleClient(
            AnthropicCompatibleConfig(
                api_key=api_key,
                model=connection.model,
                base_url=connection.base_url,
                timeout_seconds=timeout_seconds,
                max_tokens=connection.max_tokens or 16384,
                transport_attempts=connection.transport_attempts,
            )
        )
    return OpenAICompatibleClient(
        OpenAICompatibleConfig(
            api_key=api_key,
            model=connection.model,
            base_url=connection.base_url,
            timeout_seconds=timeout_seconds,
            max_tokens=connection.max_tokens,
            transport_attempts=connection.transport_attempts,
            wire_api=connection.wire_api,
            reasoning_effort=connection.reasoning_effort,
            disable_response_storage=connection.disable_response_storage,
        )
    )


def _sanitize_secret(text: str, secret: str) -> str:
    if not secret:
        return text
    return text.replace(secret, "<redacted>")


def _record_completed(
    state: RunState,
    sample_id: str,
    next_index: int,
    bucket: str,
    sample_dir: Path,
) -> RunState:
    buckets = {key: list(value) for key, value in state.buckets.items()}
    buckets.setdefault(bucket, [])
    if sample_id not in buckets[bucket]:
        buckets[bucket].append(sample_id)

    completed_samples = list(state.completed_samples)
    if sample_id not in completed_samples:
        completed_samples.append(sample_id)

    failure_types = dict(state.failure_types)
    for failure_type, count in _sample_failure_types(sample_dir).items():
        failure_types[failure_type] = failure_types.get(failure_type, 0) + count

    return RunState(
        run_id=state.run_id,
        next_index=next_index,
        completed_samples=completed_samples,
        buckets=buckets,
        failure_types=failure_types,
        exports_refreshed=state.exports_refreshed,
        config_fingerprint=state.config_fingerprint,
    )


def _record_rejected(state: RunState, sample_id: str, next_index: int, failure_type: str) -> RunState:
    buckets = {key: list(value) for key, value in state.buckets.items()}
    buckets.setdefault("rejected", [])
    if sample_id not in buckets["rejected"]:
        buckets["rejected"].append(sample_id)

    completed_samples = list(state.completed_samples)
    if sample_id not in completed_samples:
        completed_samples.append(sample_id)

    failure_types = dict(state.failure_types)
    failure_types[failure_type] = failure_types.get(failure_type, 0) + 1

    return RunState(
        run_id=state.run_id,
        next_index=next_index,
        completed_samples=completed_samples,
        buckets=buckets,
        failure_types=failure_types,
        exports_refreshed=state.exports_refreshed,
        config_fingerprint=state.config_fingerprint,
    )


def _read_labels(sample_dir: Path) -> dict[str, Any]:
    return json.loads((sample_dir / "eval" / "labels.json").read_text(encoding="utf-8"))


def _sample_has_measurement(sample_dir: Path) -> bool:
    path = sample_dir / "eval" / "trajectory.json"
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and isinstance(payload.get("measurement"), dict)


def _sample_failure_types(sample_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    attempts_dir = sample_dir / "attempts"
    if not attempts_dir.exists():
        return counts
    for diagnosis_path in sorted(attempts_dir.glob("attempt_*/diagnosis.json")):
        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
        failure_type = str(diagnosis.get("failure_type", "unknown"))
        counts[failure_type] = counts.get(failure_type, 0) + 1
    return counts


def _failure_family(failure_type: str, stage: str = "") -> str:
    if failure_type == "generation_failed" or stage == "generation":
        return "generation_failure"
    if failure_type == "repair_failed" or stage == "repair":
        return "repair_failure"
    if failure_type == "l0_contract_violation":
        return "artifact_contract_failure"
    if stage == "testbench_static_check" or failure_type in {
        "testbench_missing_functional_oracle",
        "testbench_internal_signal_access",
        "testbench_observation_race",
        "testbench_stimulus_reaccept_risk",
    }:
        return "testbench_failure"
    if stage in {"rtl_identifier_check", "lint", "sim_compile"}:
        return "rtl_compile_failure"
    if stage == "sim_run":
        return "rtl_sim_failure"
    if stage == "synth":
        return "synth_failure"
    if failure_type in {"syntax_error", "module_not_found", "parameter_mismatch", "port_mismatch", "width_mismatch"}:
        return "rtl_compile_failure"
    if failure_type == "sample_exists":
        return "sample_rejection"
    return "unknown_failure"


def _sample_failure_families(sample_dir: Path) -> set[str]:
    families: set[str] = set()
    attempts_dir = sample_dir / "attempts"
    if not attempts_dir.exists():
        return families
    for diagnosis_path in sorted(attempts_dir.glob("attempt_*/diagnosis.json")):
        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
        families.add(
            _failure_family(
                str(diagnosis.get("failure_type", "unknown")),
                str(diagnosis.get("stage", "")),
            )
        )
    return families


def _sample_attempt_stage_transitions(sample_dir: Path) -> dict[str, int]:
    stages: list[str] = []
    attempts_dir = sample_dir / "attempts"
    if not attempts_dir.exists():
        return {}
    for diagnosis_path in sorted(attempts_dir.glob("attempt_*/diagnosis.json")):
        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
        stage = str(diagnosis.get("stage", "")).strip()
        if stage:
            stages.append(stage)

    transitions: dict[str, int] = {}
    for from_stage, to_stage in zip(stages, stages[1:]):
        transition = f"{from_stage}->{to_stage}"
        transitions[transition] = transitions.get(transition, 0) + 1
    return transitions


def _sample_latent_testbench_issues(sample_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for testbench_path in sorted(sample_dir.glob("attempts/attempt_*/generated_project/sim/tb_top.v")):
        issues = check_testbench_static_issues(testbench_path.read_text(encoding="utf-8"))
        for issue in issues:
            counts[issue.failure_type] = counts.get(issue.failure_type, 0) + 1
    return counts


def _summary(config: RunnerConfig, state: RunState) -> dict[str, Any]:
    calibration = _calibration_breakdown(config.dataset_root, state.completed_samples)
    return {
        "run_id": state.run_id,
        "config_fingerprint": state.config_fingerprint,
        "total_planned": len(planned_samples(config)),
        "total_completed": len(state.completed_samples),
        "next_index": state.next_index,
        "buckets": state.buckets,
        "failure_types": state.failure_types,
        "failure_family_breakdown": calibration["failure_family_breakdown"],
        "attempt_stage_transition_breakdown": calibration["attempt_stage_transition_breakdown"],
        "latent_testbench_issue_breakdown": calibration["latent_testbench_issue_breakdown"],
        "metadata_breakdown": calibration["metadata_breakdown"],
        "pass_level_breakdown": calibration["pass_level_breakdown"],
        "levels": calibration["levels"],
        "generated_his_credit": calibration["generated_his_credit"],
        "generated_his_pass_level_breakdown": calibration["generated_his_pass_level_breakdown"],
        "derived_training_views": calibration["derived_training_views"],
        "h_stage": calibration["h_stage"],
        "l4_open": calibration["l4_open"],
        "l4_open_skip_reasons": calibration["l4_open_skip_reasons"],
        "l4_commercial": calibration["l4_commercial"],
        "l4_commercial_skip_reasons": calibration["l4_commercial_skip_reasons"],
        "toolchain_environment_failures": calibration["toolchain_environment_failures"],
        "oracle_strength": calibration["oracle_strength"],
        "independent_oracle": calibration["independent_oracle"],
        "repair_metrics": calibration["repair_metrics"],
        "calibration_matrix": calibration["calibration_matrix"],
        "contract_metrics": calibration["contract_metrics"],
        "exports_refreshed": state.exports_refreshed,
        "line_b_targets": config.line_b_targets,
    }


def _calibration_breakdown(dataset_root: Path, sample_ids: list[str]) -> dict[str, dict[str, dict[str, int]]]:
    metadata_fields = (
        "source",
        "failure_origin",
        "requirement_style",
        "contract_skeleton_mode",
        "difficulty_tier",
        "topology_id",
        "measurement_point",
        "evaluation_line",
    )
    metadata_breakdown: dict[str, dict[str, int]] = {field: {} for field in metadata_fields}
    failure_family_breakdown: dict[str, int] = {}
    attempt_stage_transition_breakdown: dict[str, int] = {}
    latent_testbench_issue_breakdown: dict[str, int] = {}
    pass_level_breakdown: dict[str, int] = {}
    levels = {
        "l0": {"pass": 0, "fail": 0},
        "l1": {"pass": 0, "fail": 0},
        "l2": {"pass": 0, "fail": 0},
        "l3": {"pass": 0, "fail": 0},
        "l4_open": {"pass": 0, "fail": 0, "not_run": 0},
    }
    generated_his_credit: dict[str, int] = {}
    generated_his_pass_level_breakdown: dict[str, int] = {}
    derived_training_views: dict[str, dict[str, Any]] = {}
    h_stage = {
        "h0": {"pass": 0, "fail": 0},
        "h1": {"pass": 0, "fail": 0},
        "h2": {"pass": 0, "fail": 0},
        "h3": {"pass": 0, "fail": 0, "not_applicable": 0},
    }
    l4_open = {"pass": 0, "fail": 0, "not_run": 0}
    l4_open_skip_reasons: dict[str, int] = {}
    l4_commercial = {"pass": 0, "fail": 0, "not_run": 0}
    l4_commercial_skip_reasons: dict[str, int] = {}
    toolchain_environment_failures: dict[str, int] = {}
    oracle_strength = {
        "samples": 0,
        "reference_passed": 0,
        "mutation_cases": 0,
        "killed": 0,
        "mutation_score": 0.0,
        "surviving_mutations": {},
        "non_scoreable_mutations": {},
        "line_a_ready": 0,
        "line_a_not_ready": 0,
    }
    independent_oracle = {
        "pass": 0,
        "fail": 0,
        "not_run": 0,
        "infrastructure_error": 0,
        "model_denominator": 0,
        "model_failures": 0,
        "by_domain": {},
        "by_family": {},
    }
    repair_metrics = {
        "total_patches": 0,
        "valid_patches": 0,
        "invalid_edit_surface": 0,
        "fixed_target": 0,
        "automatic_pass_credit": 0,
        "regressing_patches": 0,
        "regression_rate": 0.0,
    }
    calibration_counts: dict[str, dict[str, dict[str, Any]]] = {
        field: {} for field in (*metadata_fields, "failure_family")
    }
    total_labeled = 0
    l0_contract_failures = 0
    for sample_id in sample_ids:
        sample_dir = dataset_root / sample_id
        labels_path = sample_dir / "eval" / "labels.json"
        if not labels_path.exists():
            continue
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
        metadata = _read_sample_metadata(sample_dir)
        total_labeled += 1
        l0_contract_failed = labels.get("checks", {}).get("l0_complete") is False
        if l0_contract_failed:
            l0_contract_failures += 1
        pass_level = str(labels.get("pass_level", "unknown"))
        pass_level_breakdown[pass_level] = pass_level_breakdown.get(pass_level, 0) + 1
        _count_level_labels(levels, labels)
        _count_generated_his_credit(generated_his_credit, generated_his_pass_level_breakdown, labels, pass_level)
        _count_derived_training_views(derived_training_views, sample_dir)
        _count_h_stage_labels(h_stage, labels)
        l4_status = _l4_open_status(labels)
        l4_open[l4_status] += 1
        l4_skip_reason = _l4_open_skip_reason(labels, l4_status)
        if l4_skip_reason is not None:
            l4_open_skip_reasons[l4_skip_reason] = l4_open_skip_reasons.get(l4_skip_reason, 0) + 1
            if l4_skip_reason == "toolchain_environment_failure":
                toolchain_environment_failures["l4_open"] = toolchain_environment_failures.get("l4_open", 0) + 1
        commercial_status = _l4_commercial_status(labels)
        l4_commercial[commercial_status] += 1
        commercial_skip_reason = _l4_commercial_skip_reason(labels, commercial_status)
        if commercial_skip_reason is not None:
            l4_commercial_skip_reasons[commercial_skip_reason] = (
                l4_commercial_skip_reasons.get(commercial_skip_reason, 0) + 1
            )
            if commercial_skip_reason == "toolchain_environment_failure":
                toolchain_environment_failures["l4_commercial"] = (
                    toolchain_environment_failures.get("l4_commercial", 0) + 1
                )
        _count_oracle_strength(oracle_strength, sample_dir)
        _count_independent_oracle(independent_oracle, labels, metadata)
        _count_repair_metrics(repair_metrics, sample_dir)
        for metadata_field in metadata_fields:
            value = str(metadata.get(metadata_field, "")).strip()
            if not value:
                continue
            metadata_breakdown[metadata_field][value] = (
                metadata_breakdown[metadata_field].get(value, 0) + 1
            )
            _record_calibration_cell(
                calibration_counts[metadata_field], value, pass_level, l0_contract_failed
            )
        for failure_family in sorted(_sample_failure_families(sample_dir)):
            failure_family_breakdown[failure_family] = failure_family_breakdown.get(failure_family, 0) + 1
            _record_calibration_cell(
                calibration_counts["failure_family"],
                failure_family,
                pass_level,
                l0_contract_failed,
            )
        for transition, count in _sample_attempt_stage_transitions(sample_dir).items():
            attempt_stage_transition_breakdown[transition] = (
                attempt_stage_transition_breakdown.get(transition, 0) + count
            )
        for issue_type, count in _sample_latent_testbench_issues(sample_dir).items():
            latent_testbench_issue_breakdown[issue_type] = latent_testbench_issue_breakdown.get(issue_type, 0) + count
    return {
        "metadata_breakdown": metadata_breakdown,
        "failure_family_breakdown": failure_family_breakdown,
        "attempt_stage_transition_breakdown": attempt_stage_transition_breakdown,
        "latent_testbench_issue_breakdown": latent_testbench_issue_breakdown,
        "pass_level_breakdown": pass_level_breakdown,
        "levels": levels,
        "generated_his_credit": generated_his_credit,
        "generated_his_pass_level_breakdown": generated_his_pass_level_breakdown,
        "derived_training_views": derived_training_views,
        "h_stage": h_stage,
        "l4_open": l4_open,
        "l4_open_skip_reasons": l4_open_skip_reasons,
        "l4_commercial": l4_commercial,
        "l4_commercial_skip_reasons": l4_commercial_skip_reasons,
        "toolchain_environment_failures": toolchain_environment_failures,
        "oracle_strength": _finalize_oracle_strength(oracle_strength),
        "independent_oracle": independent_oracle,
        "repair_metrics": _finalize_repair_metrics(repair_metrics),
        "calibration_matrix": _calibration_rates(calibration_counts),
        "contract_metrics": {
            "total_labeled": total_labeled,
            "l0_contract_failures": l0_contract_failures,
            "cross_file_consistency_error_rate": (
                0.0 if total_labeled == 0 else l0_contract_failures / total_labeled
            ),
        },
    }


def _count_oracle_strength(summary: dict[str, Any], sample_dir: Path) -> None:
    path = sample_dir / "eval" / "trajectory.json"
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return
    strength = payload.get("oracle_strength") if isinstance(payload, dict) else None
    if not isinstance(strength, dict):
        return
    summary["samples"] += 1
    summary["reference_passed"] += int(strength.get("reference_pass") is True)
    summary["mutation_cases"] += _safe_nonnegative_int(strength.get("mutation_cases"), 0)
    summary["killed"] += _safe_nonnegative_int(strength.get("killed"), 0)
    survivors = strength.get("surviving_mutations", [])
    if isinstance(survivors, list):
        for mutation in survivors:
            if isinstance(mutation, str):
                counts = summary["surviving_mutations"]
                counts[mutation] = counts.get(mutation, 0) + 1
    non_scoreable = strength.get("non_scoreable_mutations", [])
    if isinstance(non_scoreable, list):
        for mutation in non_scoreable:
            if isinstance(mutation, str):
                counts = summary["non_scoreable_mutations"]
                counts[mutation] = counts.get(mutation, 0) + 1
    readiness = strength.get("line_a_ready")
    if readiness is True:
        summary["line_a_ready"] += 1
    elif readiness is False:
        summary["line_a_not_ready"] += 1


def _finalize_oracle_strength(summary: dict[str, Any]) -> dict[str, Any]:
    mutation_cases = int(summary["mutation_cases"])
    return {
        **summary,
        "mutation_score": 0.0 if mutation_cases == 0 else round(int(summary["killed"]) / mutation_cases, 2),
    }


_ORACLE_DOMAIN_BY_FAMILY = {
    "fir_filter": "numeric",
    "matrix_vector_mac": "numeric",
    "matched_filter": "signal",
    "peak_detector": "signal",
    "p_pulse_radar_signal": "signal",
    "sobel_threshold": "image",
    "p_vision_defect_core": "image",
    "qtable_update_core": "rl",
    "p_rl_qlearning_accel": "rl",
}


def _count_independent_oracle(
    summary: dict[str, Any],
    labels: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    status = str(labels.get("independent_oracle_status", "not_run"))
    if status not in {"pass", "fail", "not_run", "infrastructure_error"}:
        status = "infrastructure_error"
    summary[status] += 1
    if status in {"pass", "fail"}:
        summary["model_denominator"] += 1
        summary["model_failures"] += int(status == "fail")

    family_id = str(metadata.get("family_id", "")).strip() or "unknown"
    domain = str(metadata.get("oracle_domain", "")).strip() or _ORACLE_DOMAIN_BY_FAMILY.get(
        family_id,
        "other",
    )
    for breakdown_field, value in (("by_domain", domain), ("by_family", family_id)):
        counts = summary[breakdown_field].setdefault(
            value,
            {"pass": 0, "fail": 0, "not_run": 0, "infrastructure_error": 0},
        )
        counts[status] += 1


def _count_repair_metrics(summary: dict[str, Any], sample_dir: Path) -> None:
    path = sample_dir / "eval" / "trajectory.json"
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return
    patches = payload.get("patches") if isinstance(payload, dict) else None
    if not isinstance(patches, list):
        return
    for patch in patches:
        if not isinstance(patch, dict):
            continue
        summary["total_patches"] += 1
        status = str(patch.get("status", ""))
        if status == "valid":
            summary["valid_patches"] += 1
        elif status == "invalid_edit_surface":
            summary["invalid_edit_surface"] += 1
        summary["automatic_pass_credit"] += int(patch.get("automatic_pass_credit") is True)
        regression = patch.get("repair_regression")
        regression = regression if isinstance(regression, dict) else {}
        summary["fixed_target"] += int(regression.get("fixed_target") is True)
        regressions = patch.get("regressions")
        regressed_levels = regression.get("regressed_levels")
        regressed_scenarios = regression.get("regressed_scenarios")
        has_regression = any(
            isinstance(value, list) and bool(value)
            for value in (regressions, regressed_levels, regressed_scenarios)
        )
        if status == "valid" and has_regression:
            summary["regressing_patches"] += 1


def _finalize_repair_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    valid_patches = int(summary["valid_patches"])
    return {
        **summary,
        "regression_rate": (
            0.0 if valid_patches == 0 else round(int(summary["regressing_patches"]) / valid_patches, 4)
        ),
    }


def _l4_open_status(labels: dict[str, Any]) -> str:
    status = labels.get("l4_open_status")
    if status in {"pass", "fail", "not_run"}:
        return status
    checks = labels.get("checks", {})
    checks = checks if isinstance(checks, dict) else {}
    value = checks.get("l4_open_pass", checks.get("l4_lite_timing_pass"))
    if value is True:
        return "pass"
    if value is False and labels.get("l4_failure_family"):
        return "fail"
    return "not_run"


def _l4_open_skip_reason(labels: dict[str, Any], status: str) -> str | None:
    if status != "not_run":
        return None
    reason = labels.get("l4_open_skip_reason")
    if isinstance(reason, str) and reason:
        return reason
    checks = labels.get("checks", {})
    checks = checks if isinstance(checks, dict) else {}
    return "l3_failed" if checks.get("l3_synth_pass") is False else "not_selected_by_policy"


def _l4_commercial_status(labels: dict[str, Any]) -> str:
    status = labels.get("l4_commercial_status")
    if status in {"pass", "fail", "not_run"}:
        return status
    checks = labels.get("checks", {})
    checks = checks if isinstance(checks, dict) else {}
    return "pass" if checks.get("l4_commercial_pass") is True else "not_run"


def _l4_commercial_skip_reason(labels: dict[str, Any], status: str) -> str | None:
    if status != "not_run":
        return None
    reason = labels.get("l4_commercial_skip_reason")
    if isinstance(reason, str) and reason:
        return reason
    checks = labels.get("checks", {})
    checks = checks if isinstance(checks, dict) else {}
    return "l3_failed" if checks.get("l3_synth_pass") is False else "not_selected_by_policy"


def _count_h_stage_labels(h_stage: dict[str, dict[str, int]], labels: dict[str, Any]) -> None:
    for stage in ("h0", "h1", "h2"):
        status = labels.get(f"{stage}_status")
        if status in {"pass", "fail"}:
            h_stage[stage][status] += 1
        elif status is None and f"{stage}_pass" in labels:
            bucket = "pass" if labels.get(f"{stage}_pass") is True else "fail"
            h_stage[stage][bucket] += 1
    h3_status = labels.get("h3_status")
    if h3_status in {"pass", "fail", "not_applicable"}:
        h_stage["h3"][h3_status] += 1
    elif h3_status is None and "h3_pass" in labels:
        bucket = "pass" if labels.get("h3_pass") is True else "fail"
        h_stage["h3"][bucket] += 1


def _count_level_labels(levels: dict[str, dict[str, int]], labels: dict[str, Any]) -> None:
    checks = labels.get("checks", {})
    checks = checks if isinstance(checks, dict) else {}
    level_checks = {
        "l0": "l0_complete",
        "l1": "l1_lint_pass",
        "l2": "l2_sim_pass",
        "l3": "l3_synth_pass",
    }
    for level, check_name in level_checks.items():
        if level == "l2":
            explicit_status = labels.get("l2_sim_status")
            if explicit_status in {"pass", "fail", "not_run"}:
                levels[level][explicit_status] = levels[level].get(explicit_status, 0) + 1
                continue
        value = checks.get(check_name)
        if value is True:
            levels[level]["pass"] += 1
        elif value is False:
            levels[level]["fail"] += 1

    l4_status = _l4_open_status(labels)
    levels["l4_open"][l4_status] += 1


def _count_generated_his_credit(
    generated_his_credit: dict[str, int],
    generated_his_pass_level_breakdown: dict[str, int],
    labels: dict[str, Any],
    pass_level: str,
) -> None:
    credit = labels.get("generated_his_pass_credit")
    if credit is False:
        reason = str(labels.get("generated_his_no_credit_reason") or "unknown")
        key = f"no_credit_{reason}"
        generated_his_credit[key] = generated_his_credit.get(key, 0) + 1
        return
    generated_his_credit["credited"] = generated_his_credit.get("credited", 0) + 1
    generated_level = str(labels.get("generated_his_pass_level") or pass_level)
    generated_his_pass_level_breakdown[generated_level] = generated_his_pass_level_breakdown.get(generated_level, 0) + 1


def _count_derived_training_views(views: dict[str, dict[str, Any]], sample_dir: Path) -> None:
    trajectory_path = sample_dir / "eval" / "trajectory.json"
    if not trajectory_path.exists():
        return
    try:
        trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    if not isinstance(trajectory, dict):
        return
    sample_views = trajectory.get("derived_training_views", {})
    if not isinstance(sample_views, dict):
        return
    for view_name, value in sample_views.items():
        if not isinstance(value, dict):
            continue
        normalized_view_name = str(view_name)
        row = views.setdefault(
            normalized_view_name,
            {
                "available": False,
                "official_eval_unit": False,
                "standalone_pass_credit": False,
                "project_level_pass_credit": False,
                "rows": 0,
                "file_level_passed": 0,
            },
        )
        row["available"] = bool(row["available"] or value.get("available") is True)
        if normalized_view_name == "req2file":
            row["official_eval_unit"] = False
            row["standalone_pass_credit"] = False
            row["project_level_pass_credit"] = False
        else:
            row["official_eval_unit"] = bool(row["official_eval_unit"] or value.get("official_eval_unit") is True)
            row["standalone_pass_credit"] = bool(
                row["standalone_pass_credit"] or value.get("standalone_pass_credit") is True
            )
            row["project_level_pass_credit"] = bool(
                row["project_level_pass_credit"] or value.get("project_level_pass_credit") is True
            )
        row["rows"] += _derived_training_view_rows(normalized_view_name, value, sample_dir)
        row["file_level_passed"] += _safe_nonnegative_int(value.get("file_level_passed"), 0)


def _derived_training_view_rows(view_name: str, value: dict[str, Any], sample_dir: Path) -> int:
    if "rows" in value:
        parsed = _safe_nonnegative_int(value.get("rows"), -1)
        if parsed >= 0:
            return parsed
    if view_name != "req2file":
        return 0
    project_dir = sample_dir / "final" / "generated_project"
    if not project_dir.exists():
        return 0
    return sum(
        1
        for path in project_dir.rglob("*")
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(project_dir).parts)
    )


def _safe_nonnegative_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _record_calibration_cell(
    cells: dict[str, dict[str, Any]],
    value: str,
    pass_level: str,
    l0_contract_failed: bool,
) -> None:
    cell = cells.setdefault(value, {"total": 0, "pass_levels": {}, "l0_contract_failures": 0})
    cell["total"] += 1
    cell["pass_levels"][pass_level] = cell["pass_levels"].get(pass_level, 0) + 1
    if l0_contract_failed:
        cell["l0_contract_failures"] += 1


def _calibration_rates(counts: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, dict[str, Any]]]:
    matrix: dict[str, dict[str, dict[str, Any]]] = {}
    for calibration_field, cells in counts.items():
        matrix[calibration_field] = {}
        for value, cell in cells.items():
            total = int(cell["total"])
            l3_count = sum(
                int(count)
                for pass_level, count in cell["pass_levels"].items()
                if _passes_at_least(str(pass_level), "L3")
            )
            l0_contract_failures = int(cell.get("l0_contract_failures", 0))
            matrix[calibration_field][value] = {
                "total": total,
                "pass_levels": cell["pass_levels"],
                "l3_pass_rate": 0.0 if total == 0 else l3_count / total,
                "l0_contract_failures": l0_contract_failures,
                "cross_file_consistency_error_rate": (
                    0.0 if total == 0 else l0_contract_failures / total
                ),
            }
    return matrix


_PASS_LEVEL_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5}


def _passes_at_least(pass_level: str, minimum: str) -> bool:
    return _PASS_LEVEL_ORDER.get(pass_level, -1) >= _PASS_LEVEL_ORDER[minimum]


def _read_sample_metadata(sample_dir: Path) -> dict[str, Any]:
    path = sample_dir / "metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_event(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _parse_bool(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise SystemExit(f"{name} must be a boolean")


def _load_l4_open_config(raw: Any, default_run_policy: str = "never") -> L4OpenConfig:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise SystemExit("l4_open must be a mapping")
    run_policy = str(raw.get("run_policy", default_run_policy))
    allowed_policies = {"never", "after_l3_pass", "representative_subset", "always"}
    if run_policy not in allowed_policies:
        raise SystemExit("l4_open.run_policy must be one of: never, after_l3_pass, representative_subset, always")
    raw_family_ids = raw.get("family_ids", [])
    if not isinstance(raw_family_ids, list) or not all(
        isinstance(family_id, str) and family_id.strip() for family_id in raw_family_ids
    ):
        raise SystemExit("l4_open.family_ids must be a list of non-empty strings")
    return L4OpenConfig(
        tool=str(raw.get("tool", "openxc7_nextpnr")),
        target_part=str(raw.get("target_part", "XC7Z020CLG484-2")),
        board_profile=str(raw.get("board_profile", "ac820_zynq")),
        run_policy=run_policy,
        timeout_seconds=int(raw.get("timeout_seconds", 600)),
        family_ids=tuple(str(family_id).strip() for family_id in raw_family_ids),
    )


def _load_l4_commercial_config(raw: Any, default_run_policy: str = "never") -> L4CommercialConfig:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise SystemExit("l4_commercial must be a mapping")
    run_policy = str(raw.get("run_policy", default_run_policy))
    allowed_policies = {"never", "after_l3_pass", "representative_subset", "always"}
    if run_policy not in allowed_policies:
        raise SystemExit(
            "l4_commercial.run_policy must be one of: never, after_l3_pass, representative_subset, always"
        )
    return L4CommercialConfig(
        tool=str(raw.get("tool", "vivado")),
        command=str(raw.get("command", "vivado")),
        target_part=str(raw.get("target_part", "XC7Z020CLG484-2")),
        run_policy=run_policy,
        timeout_seconds=int(raw.get("timeout_seconds", 1800)),
    )


def _l4_open_enabled_for_config(config: RunnerConfig) -> bool:
    if not config.enable_openxc7_l4:
        return False
    return config.l4_open.run_policy in {"after_l3_pass", "always"}


def _l4_open_enabled_for_sample(config: RunnerConfig, sample: PlannedSample) -> bool:
    if not config.enable_openxc7_l4 or config.l4_open.run_policy == "never":
        return False
    if config.l4_open.family_ids:
        return sample.family_id in config.l4_open.family_ids
    if _l4_open_enabled_for_config(config):
        return True
    if not config.enable_openxc7_l4 or config.l4_open.run_policy != "representative_subset":
        return False
    alias = sample.topology_id or sample.task_type
    return task_family_spec_for_alias(alias).l4_open_policy in {
        "representative_subset",
        "required_for_flagship",
    }


def _l4_commercial_enabled_for_config(config: RunnerConfig) -> bool:
    if not config.run_l4_commercial:
        return False
    return config.l4_commercial.run_policy in {"after_l3_pass", "always"}


def _l4_commercial_enabled_for_sample(config: RunnerConfig, sample: PlannedSample) -> bool:
    if _l4_commercial_enabled_for_config(config):
        return True
    if not config.run_l4_commercial or config.l4_commercial.run_policy != "representative_subset":
        return False
    alias = sample.topology_id or sample.task_type
    return task_family_spec_for_alias(alias).l4_commercial_policy == "tcad_subset"


def _load_optional_string(item: dict[str, Any], field_name: str) -> str:
    if field_name not in item:
        return ""
    value = item[field_name]
    if not isinstance(value, str):
        raise SystemExit(f"{field_name} must be a string")
    return value.strip()


def _load_task_config(item: dict[str, Any], raw: dict[str, Any]) -> TaskConfig:
    if "family_recipe" in item:
        raise SystemExit(
            "task family_recipe has been removed; recipe selection now uses the automatic policy"
        )
    widths = [int(width) for width in item.get("widths", [8])]
    count = int(item.get("count", 1))
    if count > 0 and not widths:
        raise SystemExit("Task widths must not be empty when count is positive")
    measurement_point = str(item.get("measurement_point", ""))
    if measurement_point and measurement_point not in VALID_MEASUREMENT_POINTS:
        allowed = ", ".join(sorted(VALID_MEASUREMENT_POINTS))
        raise SystemExit(f"Unsupported measurement_point: {measurement_point}. Expected one of: {allowed}")
    requirement_style = str(item.get("requirement_style", "simple_prompt"))
    if requirement_style not in VALID_REQUIREMENT_STYLES:
        allowed = ", ".join(sorted(VALID_REQUIREMENT_STYLES))
        raise SystemExit(f"Unsupported requirement_style: {requirement_style}. Expected one of: {allowed}")
    task_type = str(item["task_type"])
    topology_ids = [str(topology_id) for topology_id in item.get("topology_ids", [])]
    difficulty_tier = str(item["difficulty_tier"]) if "difficulty_tier" in item else ""
    evaluation_line = str(item.get("evaluation_line", "line_b"))
    if evaluation_line not in VALID_EVALUATION_LINES:
        allowed = ", ".join(sorted(VALID_EVALUATION_LINES))
        raise SystemExit(f"Unsupported evaluation_line: {evaluation_line}. Expected one of: {allowed}")
    requirement = item.get("requirement", "")
    if not isinstance(requirement, str):
        raise SystemExit("Task requirement must be a string")
    method_condition = str(item.get("method_condition", ""))
    if method_condition and method_condition not in IMPLEMENTED_METHOD_CONDITIONS:
        allowed = ", ".join(sorted(IMPLEMENTED_METHOD_CONDITIONS))
        raise SystemExit(
            f"Unsupported or not-yet-implemented method_condition: {method_condition}. "
            f"Current adapters: {allowed}"
        )
    analysis_population = str(item.get("analysis_population", "development"))
    if analysis_population not in VALID_ANALYSIS_POPULATIONS:
        allowed = ", ".join(sorted(VALID_ANALYSIS_POPULATIONS))
        raise SystemExit(
            f"Unsupported analysis_population: {analysis_population}. Expected one of: {allowed}"
        )
    if analysis_population == "official_vpp" and not method_condition:
        raise SystemExit("official_vpp tasks require an explicit method_condition")
    if analysis_population == "ambiguity_audit" and method_condition:
        raise SystemExit("ambiguity_audit is A_req, not an M0-M5 method_condition")
    raw_manifest = item.get("requirement_audit_manifest", raw.get("requirement_audit_manifest", ""))
    requirement_audit_manifest = ""
    if raw_manifest is not None:
        requirement_audit_manifest = str(raw_manifest).strip()
    public_l2_harness_manifest = str(
        item.get("public_l2_harness_manifest", "") or ""
    ).strip()
    if public_l2_harness_manifest and analysis_population not in {
        "development",
        "excluded",
    }:
        raise SystemExit(
            "public_l2_harness_manifest is restricted to development/excluded tasks"
        )
    semantic_instance_id = _load_optional_string(item, "semantic_instance_id")
    replicate_id = _load_optional_string(item, "replicate_id")
    paired_block_id = _load_optional_string(item, "paired_block_id")
    decoding_seed = item.get("decoding_seed")
    execution_schedule_seed = item.get("execution_schedule_seed")
    decoding_control_mode = _load_optional_string(item, "decoding_control_mode")
    _validate_task_pairing_identity(
        analysis_population=analysis_population,
        method_condition=method_condition,
        count=count,
        semantic_instance_id=semantic_instance_id,
        replicate_id=replicate_id,
        decoding_seed=decoding_seed,
        decoding_seed_supplied="decoding_seed" in item,
        paired_block_id=paired_block_id,
        execution_schedule_seed=execution_schedule_seed,
        decoding_control_mode=decoding_control_mode,
    )
    return TaskConfig(
        source=str(item.get("source", raw.get("provider", "deterministic"))),
        task_type=task_type,
        widths=widths,
        count=count,
        failure_injectors=[str(injector) for injector in item.get("failure_injectors", [])],
        difficulty_tier=difficulty_tier,
        failure_origin=str(item.get("failure_origin", "")),
        topology_ids=topology_ids,
        measurement_point=measurement_point,
        requirement_style=requirement_style,
        evaluation_line=evaluation_line,
        requirement=requirement.strip(),
        method_condition=method_condition,
        analysis_population=analysis_population,
        requirement_audit_manifest=requirement_audit_manifest,
        public_l2_harness_manifest=public_l2_harness_manifest,
        semantic_instance_id=semantic_instance_id,
        replicate_id=replicate_id,
        decoding_seed=decoding_seed,
        paired_block_id=paired_block_id,
        execution_schedule_seed=execution_schedule_seed,
        decoding_control_mode=decoding_control_mode,
    )


LLM_SOURCE_KINDS = {
    "openai_compat",
    "anthropic_compat",
    "deepseek",
    "deepseek-his-v12",
    "deepseek-oracle-his-v12",
}

VETTED_TWO_STAGE_KINDS = {"deepseek-his-v12", "deepseek-oracle-his-v12"}


def resolve_source_connection(config: RunnerConfig, source: str) -> SourceConnection:
    if source in config.sources:
        return config.sources[source]
    if source == "deterministic":
        return SourceConnection(name="deterministic", kind="deterministic")
    if source == "deepseek-oracle-his-v12":
        kind, mode = "deepseek-oracle-his-v12", "oracle_his2project"
    elif source == "deepseek-his-v12":
        kind, mode = "deepseek-his-v12", "two_stage"
    elif source == "deepseek" or source.startswith("deepseek-"):
        kind, mode = "deepseek", "direct"
    else:
        kind, mode = "openai_compat", "two_stage"
    return SourceConnection(
        name=source,
        kind=kind,
        model=config.model,
        base_url=config.base_url,
        api_key_env=config.api_key_env,
        generation_mode=mode,
    )


_GENERATION_MODE_BY_KIND = {
    "openai_compat": "two_stage",
    "anthropic_compat": "two_stage",
    "deepseek-his-v12": "two_stage",
    "deepseek-oracle-his-v12": "oracle_his2project",
    "deepseek": "direct",
    "deterministic": "",
}


def _load_sources(raw: dict[str, Any]) -> dict[str, SourceConnection]:
    sources: dict[str, SourceConnection] = {}
    for name, item in raw.items():
        kind = str(item.get("kind", "openai_compat"))
        generation_mode = str(item.get("generation_mode", ""))
        expected_mode = _GENERATION_MODE_BY_KIND.get(kind)
        if generation_mode and expected_mode is not None and generation_mode != expected_mode:
            raise SystemExit(
                f"Source {name!r}: kind {kind!r} requires generation_mode {expected_mode!r}"
            )
        if not generation_mode:
            generation_mode = expected_mode or ""
        system_his_schema_version = str(item.get("system_his_schema_version", ""))
        if system_his_schema_version not in {"", "system-his-v1.1", "system-his-v1.2"}:
            raise SystemExit(
                f"Source {name!r}: system_his_schema_version must be system-his-v1.1 or system-his-v1.2"
            )
        wire_api = str(item.get("wire_api", "chat_completions"))
        if wire_api not in {"chat_completions", "responses"}:
            raise SystemExit(
                f"Source {name!r}: wire_api must be chat_completions or responses"
            )
        reasoning_effort = str(item.get("reasoning_effort", ""))
        if reasoning_effort not in {
            "",
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
        }:
            raise SystemExit(f"Source {name!r}: unsupported reasoning_effort")
        disable_response_storage = item.get("disable_response_storage", False)
        if not isinstance(disable_response_storage, bool):
            raise SystemExit(
                f"Source {name!r}: disable_response_storage must be a boolean"
            )
        if wire_api != "responses" and reasoning_effort:
            raise SystemExit(
                f"Source {name!r}: reasoning_effort requires wire_api=responses"
            )
        if wire_api != "responses" and disable_response_storage:
            raise SystemExit(
                f"Source {name!r}: disable_response_storage requires "
                "wire_api=responses"
            )
        sources[str(name)] = SourceConnection(
            name=str(name),
            kind=kind,
            model=str(item.get("model", "")),
            base_url=str(item.get("base_url", "")),
            api_key_env=str(item.get("api_key_env", "")),
            generation_mode=generation_mode,
            timeout_seconds=int(item.get("timeout_seconds", 120)),
            transport_attempts=int(item.get("transport_attempts", 3)),
            max_tokens=int(item.get("max_tokens", 0)),
            wire_api=wire_api,
            reasoning_effort=reasoning_effort,
            disable_response_storage=disable_response_storage,
            system_his_schema_version=system_his_schema_version,
            seed_capability_manifest=str(item.get("seed_capability_manifest", "")),
        )
    return sources


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise SystemExit("PyYAML is required for YAML runner configs; use .json or install pyyaml") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SystemExit("Runner config must be a mapping")
    return data


def _validate_task_pairing_identity(
    *,
    analysis_population: str,
    method_condition: str,
    count: int,
    semantic_instance_id: str,
    replicate_id: str,
    decoding_seed: Any,
    decoding_seed_supplied: bool,
    paired_block_id: str,
    execution_schedule_seed: Any,
    decoding_control_mode: str,
) -> None:
    identity_supplied = (
        bool(semantic_instance_id),
        bool(replicate_id),
        bool(paired_block_id),
        execution_schedule_seed is not None,
        bool(decoding_control_mode),
        decoding_seed_supplied,
    )
    any_supplied = any(identity_supplied)
    complete_identity = all(identity_supplied)
    if any_supplied and not complete_identity:
        raise SystemExit(
            "first-class pairing identity requires semantic_instance_id, "
            "replicate_id, paired_block_id, decoding_control_mode, and "
            "execution_schedule_seed together"
        )
    if decoding_seed is not None and (
        not isinstance(decoding_seed, int)
        or isinstance(decoding_seed, bool)
        or decoding_seed < 0
    ):
        raise SystemExit("first-class pairing identity decoding_seed must be non-negative")
    if execution_schedule_seed is not None and (
        not isinstance(execution_schedule_seed, int)
        or isinstance(execution_schedule_seed, bool)
        or execution_schedule_seed < 0
    ):
        raise SystemExit(
            "first-class pairing identity execution_schedule_seed must be non-negative"
        )
    if decoding_control_mode not in {
        "",
        "documented_seed_control",
        "stochastic_blocked",
    }:
        raise SystemExit(
            "first-class pairing identity decoding_control_mode must be "
            "documented_seed_control or stochastic_blocked"
        )
    if decoding_control_mode == "documented_seed_control" and decoding_seed is None:
        raise SystemExit(
            "first-class pairing identity documented_seed_control requires a "
            "non-negative decoding_seed"
        )
    for label, value in (
        ("semantic_instance_id", semantic_instance_id),
        ("replicate_id", replicate_id),
        ("paired_block_id", paired_block_id),
    ):
        if value and not _PAIRED_ID_RE.fullmatch(value):
            raise SystemExit(
                f"first-class pairing identity {label} contains unsafe characters"
            )
    if complete_identity and count != 1:
        raise SystemExit(
            "first-class pairing identity maps to exactly one planned sample; task count must be 1"
        )
    if (
        analysis_population == "excluded"
        and method_condition in EPISODE_PACK_METHOD_CONDITIONS
        and not complete_identity
    ):
        raise SystemExit(
            "excluded M0-M5 tasks require first-class pairing identity: "
            "semantic_instance_id, replicate_id, paired_block_id, "
            "decoding_control_mode, and execution_schedule_seed"
        )


def _resolve_planned_pairing_identity(
    task: TaskConfig,
    requirement_sha256: str,
) -> tuple[str, str, int | None, str, int | None, str, str]:
    if task.semantic_instance_id:
        return (
            task.semantic_instance_id,
            task.replicate_id,
            task.decoding_seed,
            task.paired_block_id,
            task.execution_schedule_seed,
            task.decoding_control_mode,
            "explicit",
        )
    digest = hashlib.sha256(
        f"development-pairing-v1:{requirement_sha256}".encode("utf-8")
    ).hexdigest()
    seed = int(digest[24:32], 16) or 1
    semantic_instance_id = f"development-{digest[:24]}"
    paired_block_id = "paired-" + hashlib.sha256(
        f"{semantic_instance_id}:{seed}:{requirement_sha256}".encode("utf-8")
    ).hexdigest()[:24]
    return (
        semantic_instance_id,
        "",
        seed,
        paired_block_id,
        None,
        "",
        "development_derived",
    )


def _validate_planned_pairing_blocks(samples: list[PlannedSample]) -> None:
    blocks: dict[str, tuple[str, str, int | None, int | None, str, str]] = {}
    block_methods: dict[str, list[str]] = {}
    methods: set[tuple[str, str]] = set()
    for sample in samples:
        if (
            sample.analysis_population != "excluded"
            or sample.method_condition not in EPISODE_PACK_METHOD_CONDITIONS
        ):
            continue
        identity = (
            sample.semantic_instance_id,
            sample.replicate_id,
            sample.decoding_seed,
            sample.execution_schedule_seed,
            sample.decoding_control_mode,
            sample.requirement_sha256,
        )
        existing = blocks.setdefault(sample.paired_block_id, identity)
        if existing != identity:
            raise SystemExit(
                f"paired_block_id {sample.paired_block_id!r} is bound to conflicting "
                "semantic instance, replicate, decoding seed, schedule seed, "
                "decoding mode, or requirement"
            )
        method_key = (sample.paired_block_id, sample.method_condition)
        if method_key in methods:
            raise SystemExit(
                f"paired_block_id {sample.paired_block_id!r} contains duplicate "
                f"method_condition {sample.method_condition}"
            )
        methods.add(method_key)
        block_methods.setdefault(sample.paired_block_id, []).append(
            sample.method_condition
        )
    for paired_block_id, method_order in block_methods.items():
        if len(method_order) != len(EPISODE_PACK_METHOD_CONDITIONS):
            continue
        if set(method_order) != EPISODE_PACK_METHOD_CONDITIONS:
            raise SystemExit(
                f"paired_block_id {paired_block_id!r} must contain exactly M0-M5"
            )
        schedule_seed = blocks[paired_block_id][3]
        assert schedule_seed is not None
        if tuple(method_order) not in build_balanced_method_orders(schedule_seed):
            raise SystemExit(
                f"paired_block_id {paired_block_id!r} method order is not a "
                "balanced order derived from execution_schedule_seed"
            )


def planned_samples(config: RunnerConfig) -> list[PlannedSample]:
    if config.max_attempts < 1:
        raise SystemExit("max_attempts must be >= 1")
    if config.max_model_calls < 0:
        raise SystemExit("max_model_calls must be >= 0")
    samples: list[PlannedSample] = []
    sequence = 1
    for task in config.tasks:
        _validate_task_pairing_identity(
            analysis_population=task.analysis_population,
            method_condition=task.method_condition,
            count=task.count,
            semantic_instance_id=task.semantic_instance_id,
            replicate_id=task.replicate_id,
            decoding_seed=task.decoding_seed,
            decoding_seed_supplied=(
                task.decoding_seed is not None
                or task.decoding_control_mode == "stochastic_blocked"
            ),
            paired_block_id=task.paired_block_id,
            execution_schedule_seed=task.execution_schedule_seed,
            decoding_control_mode=task.decoding_control_mode,
        )
        if task.count > 0 and not task.widths:
            raise SystemExit("Task widths must not be empty when count is positive")
        produced = 0
        while produced < task.count:
            for topology_id, task_type, family_id, difficulty_tier, width in _task_expansion_items(task):
                if produced >= task.count:
                    break
                sample_key = topology_id or task_type
                sample_id = f"sample_{config.sample_id_prefix}_{sample_key}_{width}_{sequence:06d}"
                project_name = f"{config.sample_id_prefix}_{sample_key}_{width}_{sequence:06d}"
                requirement = task.requirement.strip() or _default_requirement(
                    task_type,
                    width,
                    topology_id=topology_id,
                    requirement_style=task.requirement_style,
                )
                requirement_sha256 = hashlib.sha256(requirement.encode("utf-8")).hexdigest()
                (
                    semantic_instance_id,
                    replicate_id,
                    decoding_seed,
                    paired_block_id,
                    execution_schedule_seed,
                    decoding_control_mode,
                    pairing_identity_source,
                ) = _resolve_planned_pairing_identity(task, requirement_sha256)
                samples.append(
                    PlannedSample(
                        sample_id=sample_id,
                        source=task.source,
                        task_type=task_type,
                        width=width,
                        project_name=project_name,
                        requirement=requirement,
                        failure_injectors=list(task.failure_injectors),
                        family_id=family_id,
                        difficulty_tier=difficulty_tier,
                        failure_origin=task.failure_origin,
                        topology_id=topology_id,
                        measurement_point=task.measurement_point,
                        requirement_style=task.requirement_style,
                        evaluation_line=task.evaluation_line,
                        paired_requirement_id=f"{family_id}:{requirement_sha256[:16]}",
                        requirement_sha256=requirement_sha256,
                        method_condition=task.method_condition,
                        analysis_population=task.analysis_population,
                        requirement_audit_manifest=task.requirement_audit_manifest,
                        public_l2_harness_manifest=task.public_l2_harness_manifest,
                        semantic_instance_id=semantic_instance_id,
                        replicate_id=replicate_id,
                        decoding_seed=decoding_seed,
                        paired_block_id=paired_block_id,
                        execution_schedule_seed=execution_schedule_seed,
                        decoding_control_mode=decoding_control_mode,
                        pairing_identity_source=pairing_identity_source,
                    )
                )
                sequence += 1
                produced += 1
    max_samples = int(config.line_b_targets.get("max_samples", len(samples)))
    _validate_planned_pairing_blocks(samples)
    selected = samples[:max_samples]
    _validate_paired_block_truncation(samples, selected)
    return selected


def _validate_paired_block_truncation(
    all_samples: list[PlannedSample],
    selected_samples: list[PlannedSample],
) -> None:
    declared_counts: dict[str, int] = {}
    selected_counts: dict[str, int] = {}
    for sample in all_samples:
        if sample.analysis_population == "excluded" and sample.replicate_id:
            declared_counts[sample.paired_block_id] = (
                declared_counts.get(sample.paired_block_id, 0) + 1
            )
    for sample in selected_samples:
        if sample.analysis_population == "excluded" and sample.replicate_id:
            selected_counts[sample.paired_block_id] = (
                selected_counts.get(sample.paired_block_id, 0) + 1
            )
    for paired_block_id, declared_count in declared_counts.items():
        selected_count = selected_counts.get(paired_block_id, 0)
        if declared_count == len(EPISODE_PACK_METHOD_CONDITIONS) and selected_count not in {
            0,
            declared_count,
        }:
            raise SystemExit(
                f"max_samples truncates complete paired_block_id {paired_block_id!r}"
            )


def _task_expansion_items(task: TaskConfig) -> list[tuple[str, str, str, str, int]]:
    if task.task_type != "component_topology":
        try:
            catalog_spec = task_family_spec_for_alias(task.task_type)
        except KeyError:
            return [("", task.task_type, "", "unclassified", width) for width in task.widths]
        return [
            ("", task.task_type, catalog_spec.family_id, catalog_spec.sr2fpga_tier, width)
            for width in task.widths
        ]
    topology_ids = task.topology_ids or sorted(_topology_id_to_task_type())
    items: list[tuple[str, str, str, str, int]] = []
    topology_lookup = _topology_id_to_task_type()
    for topology_id in topology_ids:
        if topology_id not in topology_lookup:
            raise SystemExit(f"Unsupported topology_id: {topology_id}")
        task_type = topology_lookup[topology_id]
        catalog_spec = task_family_spec_for_alias(topology_id)
        for width in task.widths:
            items.append((topology_id, task_type, catalog_spec.family_id, catalog_spec.sr2fpga_tier, width))
    return items


def _topology_id_to_task_type() -> dict[str, str]:
    return {str(spec["topology_id"]): task_type for task_type, spec in COMPONENT_TOPOLOGIES.items()}


def _default_requirement(
    task_type: str,
    width: int,
    topology_id: str = "",
    requirement_style: str = "simple_prompt",
) -> str:
    if requirement_style == "simple_prompt":
        return _simple_prompt_requirement(task_type, width)
    if requirement_style == "natural_component" and topology_id:
        return _natural_component_requirement(task_type, width, topology_id)
    return (
        f"Design a {width}-bit {task_type} as a complete SR2FPGA Verilog RTL project. "
        "Use an appropriate multi-file RTL structure for the requested design; "
        "include system_his.json, manifest.json, "
        "timing constraints, a bounded self-checking testbench that prints TEST_PASS on success "
        f"or TEST_FAIL on failure, and predicted QoR.{_topology_requirement_clause(task_type, topology_id)}"
    )


def _simple_prompt_requirement(task_type: str, width: int) -> str:
    prompts = {
        "counter": (
            f"Generate an {width}-bit FPGA RTL project that implements a synchronous counter with enable and reset."
        ),
        "fifo": (
            f"Generate an {width}-bit FPGA RTL project that implements a small synchronous FIFO with ready/valid flow control."
        ),
        "simple_fsm": (
            f"Generate a {width}-state FPGA RTL project that implements a simple command/state machine."
        ),
        "ram_read_write": (
            f"Generate a {width}-bit FPGA RTL project that implements a small synchronous RAM with read and write access."
        ),
        "uart_tx": (
            f"Generate an {width}-bit FPGA RTL project that implements a UART transmitter."
        ),
        "spi_master": (
            f"Generate an {width}-bit FPGA RTL project that implements a simple SPI master."
        ),
        "pwm_controller": (
            f"Generate an {width}-bit FPGA RTL project that implements a configurable PWM controller."
        ),
        "fir_filter": (
            f"Generate an {width}-bit FPGA RTL project that implements a small streaming FIR filter."
        ),
        "streaming_valid_ready": (
            f"Generate an {width}-bit FPGA RTL project that implements a valid-ready streaming datapath."
        ),
        "matrix_vector_mac": (
            f"Generate an {width}-bit FPGA RTL project that implements a small matrix-vector multiply-accumulate datapath."
        ),
        "alu_control_unit": (
            f"Generate an {width}-bit FPGA RTL project that implements an ALU with a simple control unit."
        ),
        "crc_stream_checker": (
            f"Generate an {width}-bit FPGA RTL project that implements a streaming CRC checker."
        ),
        "composed_event_counter": (
            f"Generate an {width}-bit FPGA RTL project that counts incoming event pulses."
        ),
        "composed_stream_accumulator": (
            f"Generate an {width}-bit FPGA RTL project that accepts a valid-ready input stream and accumulates samples."
        ),
        "composed_stream_fork": (
            f"Generate an {width}-bit FPGA RTL project that duplicates one valid-ready input stream to two output streams."
        ),
        "composed_dual_stream_join": (
            f"Generate an {width}-bit FPGA RTL project that joins two input streams, accumulates joined samples, "
            "and exposes one output stream."
        ),
        "composed_vector_mac_pipeline": (
            f"Generate an {width}-bit FPGA RTL project that accepts paired feature and weight streams, "
            "computes a fixed-length vector MAC score with bias, and exposes one score stream."
        ),
        "composed_td_update_core": (
            f"Generate an {width}-bit FPGA RTL project that accepts reward, value, next_value, gamma, "
            "and alpha inputs, computes TD error, and emits an updated value stream."
        ),
        "composed_policy_value_shell": (
            f"Generate an {width}-bit FPGA RTL project with config registers, two observation inputs, "
            "policy score comparison, selected action output, and value estimate output."
        ),
        "composed_replay_sample_shell": (
            f"Generate an {width}-bit FPGA RTL project with a host-side replay sample write interface, "
            "a small replay store, fabric-side sample readout, and occupancy status."
        ),
        "composed_host_protocol_shell": (
            f"Generate an {width}-bit FPGA RTL project with AXI-lite-style control/status writes and reads, "
            "AXI-stream-style sample output, and irq reporting."
        ),
        "composed_rl_accelerator_shell": (
            f"Generate an {width}-bit FPGA RTL project with host configuration, sample capture, "
            "policy/value scoring, TD update, result streaming, and irq reporting."
        ),
        "composed_batch_rl_accelerator_shell": (
            f"Generate an {width}-bit FPGA RTL project with shared host configuration, two-lane batch sample capture, "
            "dual-lane policy/value scoring, dual-lane TD update, result staging, and irq reporting."
        ),
        "composed_replay_arbiter_shell": (
            f"Generate an {width}-bit FPGA RTL project with host transition packetization, indexed replay sample "
            "requests, read/write arbitration, sample packet output, occupancy status, and irq reporting."
        ),
    }
    return prompts.get(task_type, f"Generate an {width}-bit {task_type} FPGA RTL project.")


def _natural_component_requirement(task_type: str, width: int, topology_id: str) -> str:
    topology = COMPONENT_TOPOLOGIES[task_type]
    title = _natural_component_title(task_type)
    components = _natural_component_summary(task_type)
    behavior = _topology_expected_behavior(task_type)
    edges = "; ".join(f"{edge['from']} -> {edge['to']}" for edge in topology["edges"])
    return (
        f"Build an {width}-bit {title} as a complete SR2FPGA Verilog RTL project. "
        f"This is component topology {topology_id}, difficulty tier {topology['difficulty_tier']}. "
        f"Use {components}. The design must implement this black-box behavior: {behavior}. "
        "Keep rtl/top.v as the integration wrapper and keep each reusable component in a separate RTL file. "
        f"Preserve these interface contracts: {edges}. "
        "Include system_his.json, manifest.json, timing constraints, predicted QoR, and a bounded "
        "self-checking testbench that prints TEST_PASS only on success or TEST_FAIL on failure."
    )


def _natural_component_title(task_type: str) -> str:
    titles = {
        "composed_event_counter": "event-counting subsystem",
        "composed_stream_accumulator": "streaming accumulator datapath",
        "composed_stream_fork": "valid-ready stream fork datapath",
        "composed_dual_stream_join": "dual-stream join datapath",
        "composed_vector_mac_pipeline": "vector MAC feature pipeline",
        "composed_td_update_core": "TD-error value-update datapath",
        "composed_policy_value_shell": "policy/value accelerator shell",
        "composed_replay_sample_shell": "replay sample host/fabric shell",
        "composed_host_protocol_shell": "host protocol control and stream shell",
        "composed_rl_accelerator_shell": "synthetic RL accelerator shell",
        "composed_batch_rl_accelerator_shell": "two-lane batch RL accelerator shell",
        "composed_replay_arbiter_shell": "replay arbiter host/fabric shell",
    }
    return titles[task_type]


def _natural_component_summary(task_type: str) -> str:
    summaries = {
        "composed_event_counter": "an event_gate in front of a counter_core",
        "composed_stream_accumulator": "a skid_buffer feeding an accumulator_core",
        "composed_stream_fork": "a skid_buffer feeding a stream_fork and two stream_stage outputs",
        "composed_dual_stream_join": (
            "two skid_buffer instances feeding stream_join, then accumulator_core, then stream_stage"
        ),
        "composed_vector_mac_pipeline": (
            "feature and weight skid_buffer instances feeding vector_mac_core, then stream_stage"
        ),
        "composed_td_update_core": (
            "td_input_stage feeding discount_core, then td_update_core, then stream_stage"
        ),
        "composed_policy_value_shell": (
            "config_reg_bank and observation_stage feeding policy_score_core, then action_select_core, "
            "then stream_stage"
        ),
        "composed_replay_sample_shell": (
            "host_sample_stage feeding replay_store, then sample_pack_core and sample_read_stage, "
            "with occupancy_counter status"
        ),
        "composed_host_protocol_shell": (
            "axi_lite_write_ctrl and axi_lite_read_ctrl feeding control_reg_bank, then "
            "sample_stream_adapter and irq_status"
        ),
        "composed_rl_accelerator_shell": (
            "host_config_bank and sample_capture_stage feeding policy_value_core, then "
            "td_update_core and result_stream_stage"
        ),
        "composed_batch_rl_accelerator_shell": (
            "batch_config_bank and batch_sample_buffer feeding dual_policy_value_core, then "
            "dual_td_update_core and batch_result_stage"
        ),
        "composed_replay_arbiter_shell": (
            "host_transition_packetizer and replay_index_allocator feeding replay_request_arbiter, then "
            "replay_memory_bank and sample_packet_stage"
        ),
    }
    return summaries[task_type]


def _topology_requirement_clause(task_type: str, topology_id: str) -> str:
    if not topology_id:
        return ""
    topology = COMPONENT_TOPOLOGIES[task_type]
    nodes = ", ".join(f"{node['id']}:{node['component']}" for node in topology["nodes"])
    edges = "; ".join(f"{edge['from']} -> {edge['to']}" for edge in topology["edges"])
    behavior = _topology_expected_behavior(task_type)
    return (
        f" Use component topology {topology_id} at difficulty tier {topology['difficulty_tier']}. "
        f"Instantiate nodes {nodes}. Wire required edges: {edges}. "
        f"Expected behavior: {behavior}. "
        "Keep rtl/top.v as the integration wrapper and keep submodules in separate RTL files."
    )


def _topology_expected_behavior(task_type: str) -> str:
    behaviors = {
        "composed_event_counter": "event_valid pulses pass through an event gate and increment the counter core",
        "composed_stream_accumulator": (
            "valid input samples pass through a skid buffer and accumulate into the running sum"
        ),
        "composed_stream_fork": (
            "valid input samples pass through a skid buffer and are duplicated to two output stages"
        ),
        "composed_dual_stream_join": (
            "two valid-ready input streams are buffered, synchronized, joined, accumulated, and staged"
        ),
        "composed_vector_mac_pipeline": (
            "paired feature and weight streams are buffered, multiplied and accumulated over a fixed vector length, "
            "biased, and staged as score output"
        ),
        "composed_td_update_core": (
            "a reward, value, next value, discount factor, and learning rate tuple is staged, "
            "converted into a temporal-difference error, and used to emit an updated value"
        ),
        "composed_policy_value_shell": (
            "configuration writes set weights, biases, and enable; observation pairs are staged, "
            "scored, compared, and emitted as selected action plus value estimate"
        ),
        "composed_replay_sample_shell": (
            "host-side transition samples are staged into a small replay store, then read back in FIFO order "
            "through a fabric-side valid-ready sample output with occupancy reporting"
        ),
        "composed_host_protocol_shell": (
            "AXI-lite-style writes configure sample registers and start streaming; one AXI-stream-style payload "
            "is emitted, status can be read back, and irq remains asserted until cleared"
        ),
        "composed_rl_accelerator_shell": (
            "configuration writes set weights, biases, alpha, and enable; sample tuples are captured, "
            "scored into a selected action and value estimate, updated through a TD datapath, "
            "and staged as a result stream with episode irq reporting"
        ),
        "composed_batch_rl_accelerator_shell": (
            "configuration writes set shared weights, biases, alpha, and enable; a two-lane batch is captured, "
            "each lane is scored and updated through duplicated policy/value and TD datapaths, "
            "and both lane results are staged with batch_done irq reporting"
        ),
        "composed_replay_arbiter_shell": (
            "host transition packets are written into a depth-4 replay memory, indexed sample requests are "
            "gated by occupancy and arbitrated behind host writes, and accepted read packets are staged with irq reporting"
        ),
    }
    return behaviors[task_type]


def _sample_failure_origin(sample: PlannedSample, config: RunnerConfig) -> str:
    if sample.failure_origin:
        origin = sample.failure_origin
    elif sample.failure_injectors:
        origin = "synthetic_injected"
    else:
        connection = resolve_source_connection(config, sample.source)
        if connection.kind in LLM_SOURCE_KINDS:
            origin = "natural_llm"
        elif connection.kind == "deterministic":
            origin = "deterministic_template"
        else:
            origin = sample.source
    try:
        validated = validate_accounting_failure_origin(origin)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if validated is None:
        raise SystemExit("sample failure origin cannot be null")
    return validated


def _sample_method_condition(sample: PlannedSample, config: RunnerConfig) -> str:
    """Resolve the method independently from provider/model provenance."""

    connection = resolve_source_connection(config, sample.source)
    repair_enabled = config.repair_provider not in {"", "none", "deterministic"} and config.max_attempts > 1
    if connection.kind == "deterministic":
        inferred = "reference_deterministic"
    elif connection.generation_mode == "direct":
        inferred = "M1" if repair_enabled else "M0"
    elif connection.generation_mode == "two_stage":
        inferred = "M5" if repair_enabled else "M4"
    elif connection.generation_mode == "oracle_his2project":
        inferred = "oracle_his_ceiling"
    else:
        raise SystemExit(
            f"Cannot resolve method_condition for source {sample.source!r} "
            f"with generation_mode {connection.generation_mode!r}"
        )
    compatible_explicit = (
        connection.generation_mode == "direct"
        and sample.method_condition in {"M0", "M1"}
    ) or (
        connection.generation_mode == "two_stage"
        and sample.method_condition in {"M2", "M3", "M4", "M5"}
    )
    if sample.method_condition and sample.method_condition != inferred and not compatible_explicit:
        raise SystemExit(
            f"method_condition {sample.method_condition!r} is inconsistent with source "
            f"{sample.source!r}, generation_mode {connection.generation_mode!r}, and repair budget"
        )
    return sample.method_condition or inferred


def _sample_model_call_ceiling(
    sample: PlannedSample,
    config: RunnerConfig,
    method_condition: str | None = None,
) -> int:
    if config.max_model_calls > 0:
        return config.max_model_calls
    method = method_condition or _sample_method_condition(sample, config)
    if method == "reference_deterministic":
        return 0
    if method in {"M0", "oracle_his_ceiling"}:
        return 1
    if method == "M1":
        return max(1, config.max_attempts)
    if method in {"M2", "M3", "M4"}:
        return 2
    if method == "M5":
        return 2 + max(0, config.max_attempts - 1)
    raise SystemExit(f"No model-call allocation is implemented for {method}")


def _exclusive_model_call_ceiling(
    config: RunnerConfig,
    sample: PlannedSample,
    method_condition: str,
) -> int:
    standalone = _sample_model_call_ceiling(sample, config, method_condition)
    try:
        shared = _SHARED_INITIAL_CALL_CEILING[method_condition]
    except KeyError as exc:
        raise SystemExit(
            f"No shared-prerequisite allocation is implemented for {method_condition}"
        ) from exc
    if standalone < shared:
        raise SystemExit(
            f"{method_condition} standalone model-call ceiling {standalone} is below "
            f"its shared prerequisite ceiling {shared}"
        )
    return standalone - shared


def _sample_attempt_limit(config: RunnerConfig, method_condition: str) -> int:
    if method_condition in {"M1", "M5"}:
        return max(1, config.max_attempts)
    return 1


def _sample_system_his_schema_version(sample: PlannedSample, config: RunnerConfig) -> str:
    connection = resolve_source_connection(config, sample.source)
    if connection.system_his_schema_version:
        return connection.system_his_schema_version
    if connection.kind == "deterministic":
        return "system-his-v1.2"
    if connection.kind in REQ2HIS_API_KINDS and connection.generation_mode == "two_stage":
        return "system-his-v1.2"
    if connection.kind in VETTED_TWO_STAGE_KINDS and connection.generation_mode in {"two_stage", "oracle_his2project"}:
        return "system-his-v1.2"
    if connection.generation_mode == "direct":
        return "not_applicable"
    return "unknown"


def _contract_skeleton_mode(sample: PlannedSample, config: RunnerConfig) -> str:
    connection = resolve_source_connection(config, sample.source)
    method_condition = _sample_method_condition(sample, config)
    if method_condition == "M2":
        return "none"
    if method_condition == "M3":
        return "none_free_full_project"
    if connection.generation_mode in {"two_stage", "oracle_his2project"}:
        return "behavior_files"
    if connection.kind == "deterministic":
        return "deterministic_template"
    if connection.kind in LLM_SOURCE_KINDS:
        return "legacy_full_project"
    return connection.kind or sample.source


def _training_split(schema_version: str) -> str:
    return load_system_his_compatibility_envelope().classify(schema_version).training_partition


def _measurement_point(config: RunnerConfig) -> str:
    if config.repair_provider != "none" and config.max_attempts > 1:
        return "b_tool_in_loop_repair"
    return "a_first_attempt_no_tools"


def _measurement_point_for_method(
    config: RunnerConfig,
    method_condition: str,
) -> str:
    if method_condition in {"M1", "M5"}:
        return _measurement_point(config)
    return "a_first_attempt_no_tools"


def _project_generator_for_sample(
    project_generators: dict[str, object | None],
    config: RunnerConfig,
    sample: PlannedSample,
    events_path: Path,
    model_budget: ModelCallBudget | None = None,
    metadata: dict[str, Any] | None = None,
    method_artifact_store: ArtifactStore | None = None,
    paired_artifact_coordinator: PairedArtifactCoordinator | None = None,
    paired_block_ref: ArtifactRef | None = None,
    execution_ordinal: int | None = None,
    prepared_block_runtime: PreparedBlockRuntime | None = None,
    block_preparation_audit: Mapping[str, Any] | None = None,
) -> object | None:
    validated_block_preparation_audit = _validated_block_preparation_audit(
        metadata,
        prepared_block_runtime,
        block_preparation_audit,
    )
    connection = resolve_source_connection(config, sample.source)
    cache_key = f"{sample.source}:{sample.sample_id}"
    if connection.generation_mode in {"two_stage", "oracle_his2project"}:
        cache_key = f"{sample.source}:{sample.sample_id}"
    if metadata is not None and metadata.get("method_condition") in {"M0", "M1"}:
        cache_key = f"{sample.source}:{sample.sample_id}"
    if cache_key not in project_generators:
        method_condition = str((metadata or {}).get("method_condition", ""))
        if (
            prepared_block_runtime is not None
            and method_condition in {"M0", "M1", "M3", "M4", "M5"}
        ):
            exclusive_client = None
            if method_condition == "M3":
                if model_budget is None:
                    raise SystemExit("prepared M3 dispatch requires an exclusive budget")
                exclusive_client = _model_client_for_sample(
                    config,
                    sample,
                    model_budget=model_budget,
                    stage="his2project",
                )
            elif method_condition == "M5" and model_budget is not None:
                if model_budget.max_calls > 0:
                    exclusive_client = _model_client_for_sample(
                        config,
                        sample,
                        model_budget=model_budget,
                        stage="system_his_repair",
                    )
            project_generators[cache_key] = _bind_runner_method_generator(
                None,
                metadata,
                config=config,
                sample=sample,
                method_artifact_store=method_artifact_store,
                paired_artifact_coordinator=paired_artifact_coordinator,
                prepared_block_runtime=prepared_block_runtime,
                exclusive_model_client=exclusive_client,
            )
            project_generator = project_generators[cache_key]
            if not sample.failure_injectors:
                return project_generator
            base_generator = project_generator or ProjectGenerator()
            return FailureInjectingProjectGenerator(
                base_generator, sample.failure_injectors
            )
        event_sink = (
            _generation_event_sink(
                events_path,
                sample,
                config,
                artifact_store=method_artifact_store,
                paired_block_ref=paired_block_ref,
                execution_ordinal=execution_ordinal,
                block_preparation_audit=validated_block_preparation_audit,
            )
            if connection.generation_mode in {"two_stage", "oracle_his2project"}
            else None
        )
        build_kwargs: dict[str, Any] = {"event_sink": event_sink}
        if sample.decoding_seed is not None:
            build_kwargs["decoding_seed"] = sample.decoding_seed
        if model_budget is not None:
            build_kwargs["model_budget"] = model_budget
        generator = build_project_generator_for_connection(
            connection,
            **build_kwargs,
        )
        generator = _bind_runner_method_generator(
            generator,
            metadata,
            config=config,
            sample=sample,
            method_artifact_store=method_artifact_store,
            paired_artifact_coordinator=paired_artifact_coordinator,
        )
        generator = _bind_frozen_direct_generator(generator, metadata)
        project_generators[cache_key] = generator
    project_generator = project_generators[cache_key]
    if not sample.failure_injectors:
        return project_generator
    base_generator = project_generator or ProjectGenerator()
    return FailureInjectingProjectGenerator(base_generator, sample.failure_injectors)


def _validated_block_preparation_audit(
    metadata: Mapping[str, Any] | None,
    prepared_block_runtime: PreparedBlockRuntime | None,
    block_preparation_audit: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    metadata_audit = (
        metadata.get("block_preparation_audit") if metadata is not None else None
    )
    for value in (metadata_audit, block_preparation_audit):
        if value is not None and not isinstance(value, Mapping):
            raise TypeError("block preparation audit must be a mapping or null")
    if prepared_block_runtime is None:
        if metadata_audit is not None or block_preparation_audit is not None:
            raise SystemExit("block preparation audit requires a prepared runtime")
        return None
    if metadata_audit is None or block_preparation_audit is None:
        raise SystemExit("prepared runtime requires block preparation audit metadata")
    audit = dict(metadata_audit)
    if audit != dict(block_preparation_audit):
        raise SystemExit("block preparation audit arguments do not match metadata")
    expected_fields = {
        "evaluation_scope",
        "paired_block_ref",
        "preparation_policy_sha256",
        "physical_initial_model_call_ceiling",
        "exclusive_model_call_ceilings",
        "checkpoint_manifest_ref",
        "block_event_refs",
        "official_outcome",
        "official_authority",
        "pass_credit_authority",
        "g3_accepted",
        "g4b_authorized",
    }
    if set(audit) != expected_fields:
        raise SystemExit("block preparation audit fields do not match runtime contract")
    prepared = prepared_block_runtime.prepared
    expected_refs = {
        "paired_block_ref": prepared.paired_block_ref.to_dict(),
        "checkpoint_manifest_ref": prepared.manifest_ref.to_dict(),
        "block_event_refs": [
            reference.to_dict() for reference in prepared.event_refs
        ],
    }
    if any(audit[field] != value for field, value in expected_refs.items()):
        raise SystemExit("block preparation audit refs do not match prepared runtime")
    if audit["exclusive_model_call_ceilings"] != (
        prepared_block_runtime.exclusive_model_call_ceilings
    ):
        raise SystemExit("block preparation audit ceilings do not match prepared runtime")
    if audit["evaluation_scope"] != "excluded_development_conformance_only":
        raise SystemExit("block preparation audit scope is invalid")
    if audit["physical_initial_model_call_ceiling"] != 3:
        raise SystemExit("block preparation audit physical ceiling is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", audit["preparation_policy_sha256"]):
        raise SystemExit("block preparation audit policy hash is invalid")
    if any(
        audit[field] is not False
        for field in (
            "official_outcome",
            "official_authority",
            "pass_credit_authority",
            "g3_accepted",
            "g4b_authorized",
        )
    ):
        raise SystemExit("block preparation audit cannot grant authority")
    return audit


def _model_client_for_sample(
    config: RunnerConfig,
    sample: PlannedSample,
    *,
    model_budget: ModelCallBudget,
    stage: str,
):
    connection = resolve_source_connection(config, sample.source)
    api_key = os.environ.get(connection.api_key_env)
    if not api_key:
        raise SystemExit(f"{connection.api_key_env} is not set")
    if connection.kind == "anthropic_compat":
        client = AnthropicCompatibleClient(
            AnthropicCompatibleConfig(
                api_key=api_key,
                model=connection.model,
                base_url=connection.base_url,
                timeout_seconds=connection.timeout_seconds,
                max_tokens=connection.max_tokens or 16384,
                transport_attempts=connection.transport_attempts,
                requested_seed=sample.decoding_seed,
            )
        )
    elif connection.kind in {
        "openai_compat",
        "deepseek",
        "deepseek-his-v12",
        "deepseek-oracle-his-v12",
    }:
        client = OpenAICompatibleClient(
            OpenAICompatibleConfig(
                api_key=api_key,
                model=connection.model,
                base_url=connection.base_url,
                timeout_seconds=connection.timeout_seconds,
                max_tokens=connection.max_tokens,
                transport_attempts=connection.transport_attempts,
                seed=sample.decoding_seed,
                wire_api=connection.wire_api,
                reasoning_effort=connection.reasoning_effort,
                disable_response_storage=connection.disable_response_storage,
            )
        )
    else:
        raise SystemExit(f"Unsupported source kind: {connection.kind}")
    return model_budget.client(client, stage)


def _bind_frozen_direct_generator(generator, metadata: dict[str, Any] | None):
    if (
        metadata is None
        or metadata.get("method_condition") not in {"M0", "M1"}
        or not isinstance(generator, DirectProjectGenerator)
    ):
        return generator
    pack = metadata.get("episode_pack")
    if not isinstance(pack, dict):
        raise SystemExit("M0/M1 development execution requires a validated episode_pack")
    return FrozenContextDirectProjectGenerator(
        generator.client,
        context_from_validated_episode_pack(pack),
    )


def _bind_runner_method_generator(
    generator,
    metadata: dict[str, Any] | None,
    *,
    config: RunnerConfig,
    sample: PlannedSample,
    method_artifact_store: ArtifactStore | None,
    paired_artifact_coordinator: PairedArtifactCoordinator | None,
    prepared_block_runtime: PreparedBlockRuntime | None = None,
    exclusive_model_client: Any | None = None,
):
    method_condition = str((metadata or {}).get("method_condition", ""))
    if method_condition not in {"M0", "M1", "M2", "M3", "M4", "M5"}:
        return generator
    if method_artifact_store is None or paired_artifact_coordinator is None:
        raise SystemExit(f"{method_condition} Runner dispatch requires a method artifact store")
    pack = (metadata or {}).get("episode_pack")
    if not isinstance(pack, dict):
        raise SystemExit(f"{method_condition} development execution requires a validated episode_pack")
    context = context_from_validated_episode_pack(pack)
    prepared = (
        prepared_block_runtime.prepared
        if prepared_block_runtime is not None
        else None
    )
    if prepared_block_runtime is not None:
        if sample.sample_id not in prepared_block_runtime.member_sample_ids:
            raise SystemExit("prepared block does not contain the dispatched sample")
        if prepared is None or prepared.paired_block_ref != ArtifactRef(
            **(metadata or {})["paired_block_ref"]
        ):
            raise SystemExit("prepared block does not match dispatched paired block")
    if method_condition in {"M0", "M1"}:
        direct = None
        if prepared is None:
            direct_client = getattr(generator, "client", None)
            if not isinstance(generator, DirectProjectGenerator) or direct_client is None:
                raise SystemExit(
                    f"{method_condition} requires a Direct source with a model client"
                )
            direct = FrozenContextDirectProjectFacade(direct_client)
        elif prepared.direct_initial_project is None:
            raise RuntimeError("prepared Direct checkpoint is unavailable")
        services = GenerationServices(
            artifacts=MethodArtifactGateway(method_artifact_store),
            episode_id=sample.sample_id,
            direct=direct,
        )
        return _RunnerDirectMethodProjectGenerator(
            method_condition=method_condition,
            context=context,
            services=services,
            coordinator=paired_artifact_coordinator,
            pairing=_runner_pairing_key(config, sample, context),
            direct=direct,
            prepared_initial_project=(
                prepared.direct_initial_project if prepared is not None else None
            ),
        )
    if prepared is not None and method_condition in {"M3", "M4", "M5"}:
        platform = _platform_profile_for_config(config)
        pairing = _runner_pairing_key(config, sample, context)
        if prepared.system_his is None:
            raise RuntimeError("prepared System-HIS checkpoint is unavailable")
        if method_condition == "M3":
            system_his = FrozenContextSystemHisFacade(
                None,
                exclusive_model_client,
                platform,
            )
            shared = SharedArtifactRefs(system_his=prepared.system_his)
            trusted_skeleton = None
            if exclusive_model_client is None:
                raise RuntimeError("prepared M3 requires a free-project capability")
        else:
            if (
                prepared.skeleton_initial_project is None
                or prepared.trusted_skeleton is None
            ):
                raise RuntimeError("prepared skeleton checkpoint is unavailable")
            system_his = None
            shared = SharedArtifactRefs(
                system_his=prepared.system_his,
                initial_project=prepared.skeleton_initial_project,
            )
            trusted_skeleton = prepared.trusted_skeleton
        services = GenerationServices(
            artifacts=MethodArtifactGateway(method_artifact_store),
            episode_id=sample.sample_id,
            system_his=system_his,
            his_validation=FrozenContextSystemHisValidationFacade(platform),
            repair=(
                FrozenContextSystemHisCorrectionFacade(
                    exclusive_model_client,
                    platform,
                )
                if method_condition == "M5"
                and exclusive_model_client is not None
                else None
            ),
        )
        return FrozenContextHisGeneratorBridge(
            method_condition=method_condition,
            context=context,
            services=services,
            coordinator=paired_artifact_coordinator,
            pairing=pairing,
            system_his=system_his,
            prepared_shared_artifacts=shared,
            prepared_trusted_skeleton=trusted_skeleton,
            max_his_corrections=(
                1
                if method_condition == "M5" and exclusive_model_client is not None
                else 0
            ),
        )
    system_his_generator = getattr(generator, "system_his_generator", None)
    project_generator = getattr(generator, "his_project_generator", None)
    req2his_client = getattr(system_his_generator, "client", None)
    project_client = getattr(project_generator, "client", None)
    if req2his_client is None or project_client is None:
        raise SystemExit(
            f"{method_condition} requires a two-stage source with separate REQ2HIS and project clients"
        )

    if method_condition == "M2":
        services = GenerationServices(
            artifacts=MethodArtifactGateway(method_artifact_store),
            episode_id=sample.sample_id,
            untyped=FrozenContextUntypedPlanFacade(req2his_client, project_client),
        )
        return _RunnerUntypedPlanProjectGenerator(
            context=context,
            services=services,
        )
    platform = _platform_profile_for_config(config)
    system_his = FrozenContextSystemHisFacade(
        req2his_client,
        project_client,
        platform,
    )
    pairing = _runner_pairing_key(config, sample, context)
    services = GenerationServices(
        artifacts=MethodArtifactGateway(method_artifact_store),
        episode_id=sample.sample_id,
        system_his=system_his,
        his_validation=FrozenContextSystemHisValidationFacade(platform),
        repair=(
            FrozenContextSystemHisCorrectionFacade(
                client_for_stage(req2his_client, "system_his_repair"),
                platform,
            )
            if method_condition == "M5"
            else None
        ),
    )
    return FrozenContextHisGeneratorBridge(
        method_condition=method_condition,
        context=context,
        services=services,
        coordinator=paired_artifact_coordinator,
        pairing=pairing,
        system_his=system_his,
        max_his_corrections=1 if method_condition == "M5" else 0,
    )


def _runner_model_provenance_sha256(
    config: RunnerConfig,
    sample: PlannedSample,
) -> str:
    return hashlib.sha256(
        json.dumps(
            _runner_block_model_identity(config, sample),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _plan_development_paired_blocks(
    config: RunnerConfig,
    samples: list[PlannedSample],
) -> dict[str, _PlannedPairedBlock]:
    grouped: dict[str, list[PlannedSample]] = {}
    for sample in samples:
        if (
            sample.analysis_population == "excluded"
            and sample.method_condition in EPISODE_PACK_METHOD_CONDITIONS
            and sample.pairing_identity_source == "explicit"
        ):
            grouped.setdefault(sample.paired_block_id, []).append(sample)

    plans: dict[str, _PlannedPairedBlock] = {}
    for paired_block_id, block_samples in grouped.items():
        if len(block_samples) != len(EPISODE_PACK_METHOD_CONDITIONS):
            continue
        member_ids = tuple(sample.sample_id for sample in block_samples)
        if any(
            sample.paired_block_id == paired_block_id
            and sample.sample_id not in member_ids
            for sample in samples
        ):
            raise SystemExit(
                f"paired_block_id {paired_block_id!r} is reused outside its "
                "excluded explicit member set"
            )
        metadata = [sample.metadata(config) for sample in block_samples]
        episode_packs = [item.get("episode_pack") for item in metadata]
        if not all(isinstance(pack, dict) for pack in episode_packs):
            continue
        projections = {
            pack["public_context"]["public_projection_sha256"]
            for pack in episode_packs
            if isinstance(pack, dict)
        }
        if len(projections) != 1:
            raise SystemExit(
                f"paired_block_id {paired_block_id!r} uses conflicting public projections"
            )
        model_identities = [
            _runner_block_model_identity(config, sample) for sample in block_samples
        ]
        if any(identity != model_identities[0] for identity in model_identities[1:]):
            raise SystemExit(
                f"paired_block_id {paired_block_id!r} uses conflicting model or "
                "gateway configuration"
            )
        block_model_provenance_sha256 = hashlib.sha256(
            json.dumps(
                model_identities[0],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        first = block_samples[0]
        payload = build_development_paired_block(
            paired_block_id=paired_block_id,
            semantic_instance_id=first.semantic_instance_id,
            replicate_id=first.replicate_id,
            public_projection_sha256=next(iter(projections)),
            model_provenance_sha256=block_model_provenance_sha256,
            decoding_control_mode=first.decoding_control_mode,
            requested_decoding_seed=first.decoding_seed,
            execution_schedule_seed=int(first.execution_schedule_seed),
            method_order=tuple(sample.method_condition for sample in block_samples),
        )
        plans[paired_block_id] = _PlannedPairedBlock(
            payload=payload,
            artifact_ref=development_paired_block_reference(payload),
            sample_ids=member_ids,
        )
    return plans


def _plan_block_preparation_policy(
    config: RunnerConfig,
    samples: list[PlannedSample],
    paired_blocks: Mapping[str, _PlannedPairedBlock],
) -> dict[str, dict[str, Any]]:
    by_sample_id = {sample.sample_id: sample for sample in samples}
    policies: dict[str, dict[str, Any]] = {}
    for paired_block_id, plan in sorted(paired_blocks.items()):
        block_samples = [by_sample_id[sample_id] for sample_id in plan.sample_ids]
        by_method = {sample.method_condition: sample for sample in block_samples}
        if set(by_method) != set(_SHARED_INITIAL_CALL_CEILING):
            raise SystemExit(
                f"paired_block_id {paired_block_id!r} has no complete preparation method set"
            )
        direct_connection = resolve_source_connection(config, by_method["M0"].source)
        his_connection = resolve_source_connection(config, by_method["M4"].source)
        if direct_connection.generation_mode != "direct":
            raise SystemExit("block preparation M0 source must use direct generation")
        if his_connection.generation_mode != "two_stage":
            raise SystemExit("block preparation M4 source must use two-stage generation")
        identities = {
            method: _runner_block_model_identity(config, sample)
            for method, sample in by_method.items()
        }
        if any(identity != identities["M0"] for identity in identities.values()):
            raise SystemExit(
                f"paired_block_id {paired_block_id!r} uses conflicting preparation "
                "source or model identity"
            )
        first = by_method["M0"]
        pack = first.metadata(config).get("episode_pack")
        if not isinstance(pack, dict):
            raise SystemExit("block preparation requires a validated episode_pack")
        context = context_from_validated_episode_pack(pack)
        pairing = _runner_pairing_key(config, first, context)
        if pairing.model_provenance_sha256 != plan.payload["model_provenance_sha256"]:
            raise SystemExit("block preparation identity does not match paired-block plan")
        prefix = f"paired/{pairing.digest()}"
        exclusive = {
            method: _exclusive_model_call_ceiling(config, by_method[method], method)
            for method in _SHARED_INITIAL_CALL_CEILING
        }
        policy: dict[str, Any] = {
            "policy_version": "development-block-preparation-policy-v1",
            "evaluation_scope": "excluded_development_conformance_only",
            "paired_block_id": paired_block_id,
            "paired_block_ref": plan.artifact_ref.to_dict(),
            "member_sample_ids": list(plan.sample_ids),
            "physical_initial_model_call_ceiling": (
                _BLOCK_PREPARATION_PHYSICAL_CALL_CEILING
            ),
            "exclusive_model_call_ceilings": exclusive,
            "expected_checkpoint_graph": [
                {
                    "checkpoint_id": "direct_initial_project",
                    "parent_checkpoint_ids": [],
                    "consumer_methods": ["M0", "M1"],
                    "planned_artifact_key": f"{prefix}/direct-initial-project",
                },
                {
                    "checkpoint_id": "shared_system_his",
                    "parent_checkpoint_ids": [],
                    "consumer_methods": ["M3", "M4", "M5"],
                    "planned_artifact_key": f"{prefix}/system-his",
                },
                {
                    "checkpoint_id": "skeleton_initial_project",
                    "parent_checkpoint_ids": ["shared_system_his"],
                    "consumer_methods": ["M4", "M5"],
                    "planned_artifact_key": f"{prefix}/skeleton-initial-project",
                    "planned_trusted_skeleton_key": f"{prefix}/trusted-skeleton",
                },
            ],
            "official_outcome": False,
            "official_authority": False,
            "pass_credit_authority": False,
            "g3_accepted": False,
            "g4b_authorized": False,
        }
        policy["preparation_policy_sha256"] = hashlib.sha256(
            json.dumps(
                policy,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        policies[paired_block_id] = policy
    return policies


def _prepare_complete_blocks(
    *,
    config: RunnerConfig,
    samples: list[PlannedSample],
    paired_block_plans: Mapping[str, _PlannedPairedBlock],
    paired_block_refs: Mapping[str, ArtifactRef],
    store: ArtifactStore,
    freeze_fingerprint: str,
) -> dict[str, PreparedBlockRuntime]:
    if not re.fullmatch(r"[0-9a-f]{64}", freeze_fingerprint):
        raise ValueError("block preparation requires a valid freeze fingerprint")
    policies = _plan_block_preparation_policy(config, samples, paired_block_plans)
    by_sample_id = {sample.sample_id: sample for sample in samples}
    prepared_blocks: dict[str, PreparedBlockRuntime] = {}
    for paired_block_id, plan in sorted(paired_block_plans.items()):
        paired_block_ref = paired_block_refs[paired_block_id]
        if paired_block_ref != plan.artifact_ref:
            raise RuntimeError("materialized paired block does not match preparation plan")
        block_samples = [by_sample_id[sample_id] for sample_id in plan.sample_ids]
        by_method = {sample.method_condition: sample for sample in block_samples}
        direct_sample = by_method["M0"]
        his_sample = by_method["M4"]
        direct_pack = direct_sample.metadata(
            config, paired_block_ref=paired_block_ref
        ).get("episode_pack")
        his_pack = his_sample.metadata(
            config, paired_block_ref=paired_block_ref
        ).get("episode_pack")
        if not isinstance(direct_pack, dict) or not isinstance(his_pack, dict):
            raise SystemExit("block preparation requires validated episode packs")
        context = context_from_validated_episode_pack(direct_pack)
        his_context = context_from_validated_episode_pack(his_pack)
        if (
            context.revision_id != his_context.revision_id
            or context.public_projection_sha256
            != his_context.public_projection_sha256
        ):
            raise SystemExit("block preparation sources use different frozen contexts")
        pairing = _runner_pairing_key(config, direct_sample, context)
        if pairing != _runner_pairing_key(config, his_sample, his_context):
            raise SystemExit("block preparation sources use different effective identities")
        policy = policies[paired_block_id]
        if policy["paired_block_ref"] != paired_block_ref.to_dict():
            raise RuntimeError("block preparation policy names another paired block")
        policy_sha256 = str(policy["preparation_policy_sha256"])
        existing = _load_prepared_block_runtime(
            store,
            paired_block_ref=paired_block_ref,
            preparation_policy_sha256=policy_sha256,
            member_sample_ids=plan.sample_ids,
            exclusive_model_call_ceilings=dict(
                policy["exclusive_model_call_ceilings"]
            ),
        )
        if existing is not None:
            prepared_blocks[paired_block_id] = existing
            continue
        ledger = BlockPreparationCostLedger(
            store,
            paired_block_ref=paired_block_ref,
            failure_origin=_sample_failure_origin(direct_sample, config),
        )
        preparation_budget = ModelCallBudget(
            _BLOCK_PREPARATION_PHYSICAL_CALL_CEILING,
            attempt_cost_ledger=ledger,
        )
        direct_client = _model_client_for_sample(
            config,
            direct_sample,
            model_budget=preparation_budget,
            stage="block_direct_initial",
        )
        req2his_client = _model_client_for_sample(
            config,
            his_sample,
            model_budget=preparation_budget,
            stage="block_req2his",
        )
        project_client = _model_client_for_sample(
            config,
            his_sample,
            model_budget=preparation_budget,
            stage="block_skeleton_initial",
        )
        platform = _platform_profile_for_config(config)
        prepared = prepare_development_paired_block(
            store,
            paired_block_ref=paired_block_ref,
            pairing=pairing,
            context=context,
            platform=platform,
            facades=BlockPreparationFacades(
                direct=FrozenContextDirectProjectFacade(direct_client),
                system_his=FrozenContextSystemHisFacade(
                    req2his_client,
                    project_client,
                    platform,
                ),
                his_validation=FrozenContextSystemHisValidationFacade(platform),
            ),
            model_budget=preparation_budget,
            preparation_policy_sha256=policy_sha256,
        )
        prepared_blocks[paired_block_id] = PreparedBlockRuntime(
            prepared=prepared,
            member_sample_ids=plan.sample_ids,
            exclusive_model_call_ceilings=dict(
                policy["exclusive_model_call_ceilings"]
            ),
        )
    return prepared_blocks


def _prepared_block_audit_record(
    policy: Mapping[str, Any],
    runtime: PreparedBlockRuntime,
) -> dict[str, Any]:
    return {
        "evaluation_scope": "excluded_development_conformance_only",
        "paired_block_ref": runtime.prepared.paired_block_ref.to_dict(),
        "preparation_policy_sha256": policy["preparation_policy_sha256"],
        "physical_initial_model_call_ceiling": policy[
            "physical_initial_model_call_ceiling"
        ],
        "exclusive_model_call_ceilings": dict(
            runtime.exclusive_model_call_ceilings
        ),
        "checkpoint_manifest_ref": runtime.prepared.manifest_ref.to_dict(),
        "block_event_refs": [
            reference.to_dict() for reference in runtime.prepared.event_refs
        ],
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }


def _load_prepared_block_runtime(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    preparation_policy_sha256: str,
    member_sample_ids: tuple[str, ...],
    exclusive_model_call_ceilings: dict[str, int],
) -> PreparedBlockRuntime | None:
    key = (
        f"shared-checkpoint-manifests/{paired_block_ref.sha256}/"
        f"{preparation_policy_sha256}"
    )
    manifest_ref = store.reference(key)
    if manifest_ref is None:
        return None
    manifest = read_development_shared_checkpoint_manifest(store, manifest_ref)
    if manifest["manifest_status"] != "complete":
        raise RuntimeError("existing block preparation manifest is incomplete")
    nodes = {node["checkpoint_id"]: node for node in manifest["nodes"]}
    direct = _project_emission_from_checkpoint(store, nodes["direct_initial_project"])
    system_his_ref = ArtifactRef(**nodes["shared_system_his"]["artifact_ref"])
    store.read_verified(system_his_ref)
    system_his = PlanningArtifactEmission(
        PlanningArtifactKind.SYSTEM_HIS,
        system_his_ref,
    )
    skeleton = _project_emission_from_checkpoint(
        store, nodes["skeleton_initial_project"]
    )
    trusted_ref = ArtifactRef(
        **nodes["skeleton_initial_project"]["trusted_skeleton_ref"]
    )
    trusted = _project_emission_from_ref(store, trusted_ref)
    prepared = PreparedBlockArtifacts(
        paired_block_ref=paired_block_ref,
        manifest_ref=manifest_ref,
        direct_initial_project=direct,
        system_his=system_his,
        skeleton_initial_project=skeleton,
        trusted_skeleton=trusted,
        event_refs=tuple(
            ArtifactRef(**reference) for reference in manifest["block_event_refs"]
        ),
    )
    return PreparedBlockRuntime(
        prepared=prepared,
        member_sample_ids=member_sample_ids,
        exclusive_model_call_ceilings=exclusive_model_call_ceilings,
    )


def _project_emission_from_checkpoint(
    store: ArtifactStore,
    node: Mapping[str, Any],
) -> ProjectCandidateEmission:
    reference = ArtifactRef(**node["artifact_ref"])
    emission = _project_emission_from_ref(store, reference)
    if emission.project_package_sha256 != node["project_package_sha256"]:
        raise ValueError("prepared checkpoint project digest mismatch")
    return emission


def _project_emission_from_ref(
    store: ArtifactStore,
    reference: ArtifactRef,
) -> ProjectCandidateEmission:
    payload = json.loads(store.read_verified(reference))
    if not isinstance(payload, dict):
        raise ValueError("prepared project artifact must be an object")
    project = GeneratedProject(
        project_name=str(payload["project_name"]),
        files=dict(payload["files"]),
    )
    return ProjectCandidateEmission(reference, project_package_sha256(project))


def _materialize_development_paired_blocks(
    plans: Mapping[str, _PlannedPairedBlock],
    store: ArtifactStore,
) -> dict[str, ArtifactRef]:
    references: dict[str, ArtifactRef] = {}
    for paired_block_id, plan in plans.items():
        payload = plan.payload
        expected_reference = plan.artifact_ref
        reference = write_development_paired_block(
            store,
            paired_block_id=payload["paired_block_id"],
            semantic_instance_id=payload["semantic_instance_id"],
            replicate_id=payload["replicate_id"],
            public_projection_sha256=payload["public_projection_sha256"],
            model_provenance_sha256=payload["model_provenance_sha256"],
            decoding_control_mode=payload["decoding_control_mode"],
            requested_decoding_seed=payload["requested_decoding_seed"],
            execution_schedule_seed=payload["execution_schedule_seed"],
            method_order=tuple(payload["method_order"]),
        )
        if reference != expected_reference:
            raise RuntimeError(
                f"paired_block_id {paired_block_id!r} materialization mismatch"
            )
        if load_development_paired_block(store, reference) != payload:
            raise RuntimeError(
                f"paired_block_id {paired_block_id!r} verified read-back mismatch"
            )
        references[paired_block_id] = reference
    return references


def _runner_block_model_identity(
    config: RunnerConfig,
    sample: PlannedSample,
) -> dict[str, Any]:
    connection = resolve_source_connection(config, sample.source)
    return {
        "provider_adapter": (
            "anthropic_compatible"
            if connection.kind == "anthropic_compat"
            else "deterministic"
            if connection.kind == "deterministic"
            else "openai_compatible"
        ),
        "model": connection.model,
        "gateway_base_url_sha256": hashlib.sha256(
            connection.base_url.rstrip("/").encode("utf-8")
        ).hexdigest(),
        "max_tokens": connection.max_tokens,
        "wire_api": connection.wire_api,
        "reasoning_effort": connection.reasoning_effort,
        "disable_response_storage": connection.disable_response_storage,
        "decoding_control_mode": sample.decoding_control_mode,
        "requested_decoding_seed": sample.decoding_seed,
    }


def _order_samples_by_paired_blocks(
    samples: list[PlannedSample],
    plans: Mapping[str, _PlannedPairedBlock],
    paired_block_refs: Mapping[str, ArtifactRef],
    store: ArtifactStore,
) -> list[PlannedSample]:
    ordered = list(samples)
    for paired_block_id, reference in paired_block_refs.items():
        block = load_development_paired_block(store, reference)
        member_ids = set(plans[paired_block_id].sample_ids)
        positions = [
            index
            for index, sample in enumerate(ordered)
            if sample.sample_id in member_ids
        ]
        by_method = {ordered[index].method_condition: ordered[index] for index in positions}
        if set(by_method) != set(block["method_order"]):
            raise SystemExit(
                f"paired_block_id {paired_block_id!r} sample set does not match artifact"
            )
        for index, method in zip(positions, block["method_order"], strict=True):
            ordered[index] = by_method[method]
    return ordered


def _paired_execution_ordinals(
    samples: list[PlannedSample],
    plans: Mapping[str, _PlannedPairedBlock],
    paired_block_refs: Mapping[str, ArtifactRef],
    store: ArtifactStore,
) -> dict[str, int]:
    ordinals: dict[str, int] = {}
    for paired_block_id, reference in paired_block_refs.items():
        block = load_development_paired_block(store, reference)
        rank = {method: index for index, method in enumerate(block["method_order"])}
        member_ids = set(plans[paired_block_id].sample_ids)
        for sample in samples:
            if sample.sample_id in member_ids:
                ordinals[sample.sample_id] = rank[sample.method_condition]
    return ordinals


def _paired_block_refs_by_sample(
    plans: Mapping[str, _PlannedPairedBlock],
    paired_block_refs: Mapping[str, ArtifactRef],
) -> dict[str, ArtifactRef]:
    return {
        sample_id: paired_block_refs[paired_block_id]
        for paired_block_id, plan in plans.items()
        for sample_id in plan.sample_ids
    }


def _runner_pairing_key(config: RunnerConfig, sample: PlannedSample, context) -> PairingKey:
    model_provenance_sha256 = _runner_model_provenance_sha256(config, sample)
    if not sample.semantic_instance_id or not sample.paired_block_id:
        raise SystemExit("Runner method dispatch requires first-class pairing identity")
    if sample.decoding_seed is not None and (
        not isinstance(sample.decoding_seed, int)
        or isinstance(sample.decoding_seed, bool)
        or sample.decoding_seed < 0
    ):
        raise SystemExit("Runner method dispatch requires a non-negative decoding_seed")
    return PairingKey(
        paired_block_id=sample.paired_block_id,
        requirement_revision_id=context.revision_id,
        semantic_instance_id=sample.semantic_instance_id,
        replicate_id=sample.replicate_id,
        decoding_seed=sample.decoding_seed,
        model_provenance_sha256=model_provenance_sha256,
    )


def _method_artifact_completion_record(
    generator: object | None,
    metadata: dict[str, Any],
) -> dict[str, Any] | None:
    current = generator
    if isinstance(current, FailureInjectingProjectGenerator):
        current = current.base_generator
    outcome = getattr(current, "last_outcome", None)
    if outcome is None:
        return None
    candidate = getattr(outcome, "candidate", None)
    planning = getattr(outcome, "planning_artifact", None)
    skeleton = getattr(current, "last_skeleton_artifact", None)
    h_report = getattr(outcome, "h_report", None)
    h_status = "not_applicable"
    if isinstance(h_report, dict):
        h_status = "pass" if h_report.get("passed") is True else "fail"
    if candidate is None:
        failure = getattr(outcome, "failure", None)
        return {
            "method_condition": str(metadata["method_condition"]),
            "candidate_artifact_ref": None,
            "project_package_sha256": None,
            "planning_kind": planning.kind.value if planning is not None else None,
            "planning_artifact_ref": (
                planning.artifact_ref.to_dict() if planning is not None else None
            ),
            "skeleton_artifact_ref": None,
            "skeleton_project_sha256": None,
            "h_status": h_status,
            "final_state": outcome.final_state.value,
            "state_trace": [state.value for state in outcome.state_trace],
            "method_event_refs": [
                reference.to_dict()
                for reference in getattr(current, "last_method_event_refs", ())
            ],
            "failure": (
                {
                    "stage": failure.stage,
                    "error_type": failure.error_type,
                    "message": failure.message,
                }
                if failure is not None
                else None
            ),
            "skeleton_mode": str(metadata["contract_skeleton_mode"]),
            "his_corrections_used": int(outcome.his_corrections_used),
        }
    record = {
        "method_condition": str(metadata["method_condition"]),
        "candidate_artifact_ref": candidate.artifact_ref.to_dict(),
        "project_package_sha256": candidate.project_package_sha256,
        "planning_kind": planning.kind.value if planning is not None else None,
        "planning_artifact_ref": (
            planning.artifact_ref.to_dict() if planning is not None else None
        ),
        "skeleton_artifact_ref": (
            skeleton.artifact_ref.to_dict() if skeleton is not None else None
        ),
        "skeleton_project_sha256": (
            skeleton.project_package_sha256 if skeleton is not None else None
        ),
        "h_status": h_status,
        "skeleton_mode": str(metadata["contract_skeleton_mode"]),
        "his_corrections_used": int(outcome.his_corrections_used),
    }
    if str(metadata["method_condition"]) == "M5":
        record.update(
            {
                "initial_planning_artifact_ref": (
                    current.last_initial_planning_artifact.artifact_ref.to_dict()
                    if getattr(current, "last_initial_planning_artifact", None)
                    is not None
                    else None
                ),
                "final_state": outcome.final_state.value,
                "state_trace": [state.value for state in outcome.state_trace],
                "method_event_refs": [
                    reference.to_dict()
                    for reference in getattr(current, "last_method_event_refs", ())
                ],
            }
        )
    return record


def _repairer_for_config(config: RunnerConfig):
    if config.repair_provider in config.sources:
        return build_repairer_for_connection(resolve_source_connection(config, config.repair_provider))
    return build_repairer(
        provider=config.repair_provider,
        model=config.model,
        base_url=config.base_url,
        api_key_env=config.api_key_env,
    )


def _repairer_for_sample(
    repairers: dict[str, object | None],
    config: RunnerConfig,
    sample: PlannedSample,
    model_budget: ModelCallBudget | None = None,
) -> object | None:
    provider_name = config.repair_provider
    if provider_name == "same_as_source":
        provider_name = sample.source
    if provider_name in {"", "none", "deterministic"}:
        return None
    cache_key = (
        provider_name
        if model_budget is None and sample.decoding_seed is None
        else f"{provider_name}:{sample.sample_id}"
    )
    if cache_key not in repairers:
        connection = resolve_source_connection(config, provider_name)
        build_kwargs: dict[str, Any] = {}
        if model_budget is not None:
            build_kwargs["model_budget"] = model_budget
        if sample.decoding_seed is not None:
            build_kwargs["decoding_seed"] = sample.decoding_seed
        repairers[cache_key] = build_repairer_for_connection(connection, **build_kwargs)
    return repairers[cache_key]


def _generation_event_sink(
    events_path: Path,
    sample: PlannedSample,
    config: RunnerConfig,
    *,
    artifact_store: ArtifactStore | None = None,
    paired_block_ref: ArtifactRef | None = None,
    execution_ordinal: int | None = None,
    block_preparation_audit: Mapping[str, Any] | None = None,
):
    if block_preparation_audit is not None and not isinstance(
        block_preparation_audit, Mapping
    ):
        raise TypeError("block preparation audit must be a mapping or null")

    def emit(payload: dict[str, Any]) -> None:
        enriched = {
            **payload,
            "sample_id": sample.sample_id,
            "source": sample.source,
            "failure_origin": _sample_failure_origin(sample, config),
            "difficulty_tier": sample.difficulty_tier,
            "topology_id": sample.topology_id,
            "requirement_style": sample.requirement_style,
            "measurement_point": sample.measurement_point,
            "semantic_instance_id": sample.semantic_instance_id,
            "decoding_seed": sample.decoding_seed,
            "paired_block_id": sample.paired_block_id,
            "pairing_identity_source": sample.pairing_identity_source,
        }
        if sample.replicate_id:
            enriched.update(
                {
                    "replicate_id": sample.replicate_id,
                    "execution_schedule_seed": sample.execution_schedule_seed,
                    "decoding_control_mode": sample.decoding_control_mode,
                }
            )
        if paired_block_ref is not None:
            enriched["paired_block_ref"] = paired_block_ref.to_dict()
            enriched["execution_ordinal"] = execution_ordinal
        if block_preparation_audit is not None:
            enriched["block_preparation_audit"] = dict(
                block_preparation_audit
            )
        method_condition = _sample_method_condition(sample, config)
        if artifact_store is not None and method_condition in IMPLEMENTED_METHOD_CONDITIONS:
            provenance_ref = write_model_gateway_provenance(
                artifact_store,
                episode_id=sample.sample_id,
                analysis_population=sample.analysis_population,
                method_condition=method_condition,
                event=enriched,
            )
            if provenance_ref is not None:
                enriched["model_gateway_provenance_ref"] = provenance_ref.to_dict()
        _append_event(
            events_path,
            enriched,
        )

    return emit


def _update_sample_model_budget(sample_dir: Path, summary: dict[str, Any]) -> None:
    metadata_path = sample_dir / "metadata.json"
    if not metadata_path.exists():
        return
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"sample metadata must be an object: {metadata_path}")
    payload["model_call_budget"] = summary
    _write_json(metadata_path, payload)


if __name__ == "__main__":
    main()
