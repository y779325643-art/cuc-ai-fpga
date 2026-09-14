"""System-HIS generation and lowering from frozen public context."""

from __future__ import annotations

import json
import copy
import re
from dataclasses import replace
from typing import Any, Callable, Mapping

from sr2fpga_agent.episode_executor import EpisodeExecutor
from sr2fpga_agent.contract_skeleton import (
    CANONICAL_PREDICTED_QOR_PATH,
    CANONICAL_TIMING_CONSTRAINT_PATH,
    build_contract_skeleton_project,
    merge_behavior_files,
)
from sr2fpga_agent.frozen_context import (
    FrozenRequirementContext,
    frozen_public_project_request,
    platform_profile_sha256,
)
from sr2fpga_agent.his_validation import (
    SystemHisValidationError,
    validate_frozen_system_his_payload_h_stages,
)
from sr2fpga_agent.method_adapters import (
    GenerationServices,
    MethodAdapterRegistry,
    PairedArtifactCoordinator,
    PairingKey,
    PlanningArtifactEmission,
    ProjectCandidateEmission,
    SkeletonProjectOutput,
    SharedArtifactRefs,
)
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.parsers import (
    parse_behavior_files,
    parse_project_files,
    parse_system_his_payload,
    resolve_project_manifest,
)
from sr2fpga_agent.path_safety import build_patch_metadata
from sr2fpga_agent.prompts import (
    _frozen_his_free_project_messages,
    _frozen_his_skeleton_messages,
    _frozen_project_repair_messages,
    _frozen_system_his_correction_messages,
    _frozen_system_his_messages,
    _with_his_project_retry_feedback,
)
from sr2fpga_agent.providers import ModelOutputTruncated, ModelOutputEmpty
from sr2fpga_agent.rtl_identifier_checker import check_rtl_identifiers
from sr2fpga_agent.system_his_checker import check_his_project_consistency
from sr2fpga_agent.project_contract import project_package_sha256, verify_project_envelope


class FrozenContextSystemHisFacade:
    """One-call REQ2HIS and skeleton lowering with no evaluator metadata."""

    def __init__(
        self,
        req2his_client: Any | None,
        project_client: Any | None,
        platform: PlatformProfile,
        *,
        project_output_repair_client: Any | None = None,
    ) -> None:
        self._req2his_client = req2his_client
        self._project_client = project_client
        self._project_output_repair_client = project_output_repair_client
        self._platform = platform
        self.last_skeleton_project: GeneratedProject | None = None

    def emit_his(self, context: FrozenRequirementContext) -> Mapping[str, Any]:
        self._check_platform(context)
        if self._req2his_client is None:
            raise RuntimeError("missing REQ2HIS model client")
        try:
            content = self._req2his_client.stream_chat(_frozen_system_his_messages(context))
        except (ModelOutputTruncated, ModelOutputEmpty) as exc:
            return _unparsed_his_output(exc.content, str(exc))
        try:
            parsed = parse_system_his_payload(content)
        except ValueError as exc:
            return _unparsed_his_output(content, str(exc))
        return _normalize_his_project_identity(context, parsed)

    def emit_free_project(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
    ) -> GeneratedProject:
        self._check_platform(context)
        if self._project_client is None:
            raise RuntimeError("missing free-project model client")
        payload = dict(system_his)
        project_name = frozen_public_project_request(context).project_name
        content = self._project_client.stream_chat(
            _frozen_his_free_project_messages(
                context, payload, project_name=project_name
            )
        )
        files = parse_project_files(
            content,
            expected_task_type=None,
            manifest_policy="canonical",
        )
        project = _attach_frozen_system_his(
            GeneratedProject(project_name, files), payload
        )
        _validate_his_project(project)
        return project

    def emit_skeleton_project(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
    ) -> GeneratedProject:
        output = self.emit_skeleton_project_output(context, system_his)
        return self.lower_skeleton_project_output(context, system_his, output)

    def emit_skeleton_project_output(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
    ) -> SkeletonProjectOutput:
        if self._project_client is None:
            raise RuntimeError("missing HIS2PROJECT model client")
        payload = dict(system_his)
        skeleton = self._build_skeleton(context, payload)
        _validate_static_his_skeleton(skeleton)
        content = self._project_client.stream_chat(
            _frozen_his_skeleton_messages(context, payload, skeleton.files)
        )
        return SkeletonProjectOutput(
            content=content,
            skeleton_project_sha256=project_package_sha256(skeleton),
        )

    def lower_skeleton_project_output(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
        output: SkeletonProjectOutput,
    ) -> GeneratedProject:
        payload = dict(system_his)
        skeleton = self._build_skeleton(context, payload)
        if project_package_sha256(skeleton) != output.skeleton_project_sha256:
            raise ValueError("deterministic skeleton changed across HIS2PROJECT output handling")
        project = merge_behavior_files(
            skeleton,
            parse_behavior_files(output.content),
        )
        _validate_his_project(project)
        return project

    def repair_skeleton_project_output(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
        previous_output: SkeletonProjectOutput,
        error: str,
    ) -> SkeletonProjectOutput:
        if self._project_output_repair_client is None:
            raise RuntimeError("missing HIS2PROJECT output repair client")
        payload = dict(system_his)
        skeleton = self._build_skeleton(context, payload)
        skeleton_sha256 = project_package_sha256(skeleton)
        if skeleton_sha256 != previous_output.skeleton_project_sha256:
            raise ValueError("deterministic skeleton changed before HIS2PROJECT output repair")
        _validate_static_his_skeleton(skeleton)
        messages = _frozen_his_skeleton_messages(context, payload, skeleton.files)
        content = self._project_output_repair_client.stream_chat(
            _with_his_project_retry_feedback(
                messages,
                error,
                previous_output.content,
            )
        )
        return SkeletonProjectOutput(
            content=content,
            skeleton_project_sha256=skeleton_sha256,
        )

    def _build_skeleton(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
    ) -> GeneratedProject:
        self._check_platform(context)
        request = frozen_public_project_request(context)
        skeleton = _canonicalize_skeleton(
            build_contract_skeleton_project(request, self._platform, system_his),
            system_his,
            self._platform,
        )
        self.last_skeleton_project = skeleton
        return skeleton

    def _check_platform(self, context: FrozenRequirementContext) -> None:
        if platform_profile_sha256(self._platform) != context.platform_profile_sha256:
            raise ValueError("PlatformProfile does not match frozen requirement context")


class FrozenContextSystemHisValidationFacade:
    def __init__(self, platform: PlatformProfile) -> None:
        self._platform = platform

    def validate_his(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return validate_frozen_system_his_payload_h_stages(
            context,
            dict(system_his),
            platform=self._platform,
        )


class FrozenContextHisGeneratorBridge:
    """Bridge a frozen-context HIS method into the Agent generator slot."""

    his_source_used_for_generation = "generated"

    def __init__(
        self,
        *,
        method_condition: str,
        context: FrozenRequirementContext,
        services: GenerationServices,
        system_his: FrozenContextSystemHisFacade | None,
        coordinator: PairedArtifactCoordinator | None = None,
        pairing: PairingKey | None = None,
        prepared_shared_artifacts: SharedArtifactRefs | None = None,
        prepared_trusted_skeleton: ProjectCandidateEmission | None = None,
        max_his_corrections: int = 0,
        max_project_output_repairs: int = 0,
        max_shared_pre_candidate_repairs: int | None = None,
    ) -> None:
        if (coordinator is None) != (pairing is None):
            raise ValueError("coordinator and pairing must be supplied together")
        self._adapter = MethodAdapterRegistry().create(method_condition)
        self._context = context
        self._services = services
        self._system_his = system_his
        self._coordinator = coordinator
        self._pairing = pairing
        self._prepared_shared_artifacts = prepared_shared_artifacts
        self._prepared_trusted_skeleton = prepared_trusted_skeleton
        self._max_his_corrections = max_his_corrections
        self._max_project_output_repairs = max_project_output_repairs
        self._max_shared_pre_candidate_repairs = max_shared_pre_candidate_repairs
        self.last_outcome = None
        self.last_initial_planning_artifact = None
        self.last_skeleton_artifact = None
        self.last_method_event_refs = ()

    def generate(
        self,
        _request: ProjectRequest,
        _platform: PlatformProfile,
    ) -> GeneratedProject:
        shared = self._prepared_shared_artifacts or SharedArtifactRefs()
        self._validate_prepared_artifacts(shared)
        if shared.system_his is not None:
            self.last_initial_planning_artifact = shared.system_his
        elif self._coordinator is not None and self._pairing is not None:
            if self._system_his is None:
                raise RuntimeError("missing System-HIS generation capability")
            shared_his = self._coordinator.materialize_system_his(
                self._pairing,
                lambda: self._system_his.emit_his(self._context),
            )
            self.last_initial_planning_artifact = shared_his
            shared = _merge_shared_system_his(shared, shared_his)

        outcome = EpisodeExecutor(
            max_his_corrections=self._max_his_corrections,
            max_project_output_repairs=self._max_project_output_repairs,
            max_shared_pre_candidate_repairs=self._max_shared_pre_candidate_repairs,
        ).emit_candidate(
            self._adapter,
            self._context,
            self._services,
            shared,
        )
        self.last_outcome = outcome
        if self.last_initial_planning_artifact is None:
            self.last_initial_planning_artifact = outcome.planning_artifact
        self.last_method_event_refs = self._services.artifacts.event_refs(
            self._services.episode_id
        )
        if outcome.candidate is None:
            failure = outcome.failure
            if failure is None:
                raise RuntimeError("method adapter produced no complete candidate")
            if (
                failure.stage in {"h0", "h1", "h2", "h3"}
                and outcome.planning_artifact is not None
                and isinstance(outcome.h_report, Mapping)
            ):
                planning = self._services.artifacts.read_planning(
                    outcome.planning_artifact
                )
                raise SystemHisValidationError(
                    json.dumps(planning, ensure_ascii=False, sort_keys=True),
                    dict(outcome.h_report),
                    candidate_artifact_sha256=(
                        outcome.planning_artifact.artifact_ref.sha256
                    ),
                )
            raise RuntimeError(
                f"{failure.stage} failed with {failure.error_type}: {failure.message}"
            )
        if self._adapter.contract.uses_deterministic_skeleton:
            if self._prepared_trusted_skeleton is not None:
                self._services.artifacts.read_project(self._prepared_trusted_skeleton)
                self.last_skeleton_artifact = self._prepared_trusted_skeleton
                return self._services.artifacts.read_project(outcome.candidate)
            if self._system_his is None:
                raise RuntimeError("missing HIS2PROJECT generation capability")
            skeleton = self._system_his.last_skeleton_project
            if skeleton is None:
                raise RuntimeError(
                    "skeleton method produced no deterministic skeleton artifact"
                )
            method = self._adapter.contract.method_condition.value
            self.last_skeleton_artifact = self._services.artifacts.put_project(
                f"method-emissions/{self._context.revision_id}/{method}/deterministic-skeleton",
                skeleton,
            )
        return self._services.artifacts.read_project(outcome.candidate)

    def _validate_prepared_artifacts(self, shared: SharedArtifactRefs) -> None:
        initial_project = shared.initial_project
        system_his = shared.system_his
        trusted_skeleton = self._prepared_trusted_skeleton
        has_prepared = any(
            value is not None
            for value in (initial_project, system_his, trusted_skeleton)
        )
        method = self._adapter.contract.method_condition.value
        if not has_prepared:
            return
        if not self._adapter.contract.emits_system_his:
            raise ValueError(f"{method} does not accept prepared HIS artifacts")
        if self._pairing is None:
            raise ValueError("prepared HIS artifacts require pairing identity")
        prefix = f"paired/{self._pairing.digest()}"
        if (
            system_his is not None
            and system_his.artifact_ref.key != f"{prefix}/system-his"
        ):
            raise ValueError(
                "prepared System-HIS key does not match pairing checkpoint"
            )
        if not self._adapter.contract.uses_deterministic_skeleton:
            if initial_project is not None or trusted_skeleton is not None:
                raise ValueError(
                    f"{method} does not accept a prepared project or trusted skeleton"
                )
            return
        if trusted_skeleton is not None and initial_project is None:
            raise ValueError("prepared trusted skeleton requires prepared project")
        if initial_project is None:
            return
        if system_his is None:
            raise ValueError("prepared project requires prepared System-HIS")
        if trusted_skeleton is None:
            raise ValueError("prepared project requires prepared trusted skeleton")
        expected_project_key = f"{prefix}/skeleton-initial-project"
        expected_trusted_key = f"{prefix}/trusted-skeleton"
        if initial_project.artifact_ref.key != expected_project_key:
            raise ValueError("prepared project key does not match pairing checkpoint")
        if trusted_skeleton.artifact_ref.key != expected_trusted_key:
            raise ValueError(
                "prepared trusted skeleton key does not match pairing checkpoint"
            )
        self._services.artifacts.read_project(initial_project)
        self._services.artifacts.read_project(trusted_skeleton)


def _merge_shared_system_his(
    shared: SharedArtifactRefs,
    system_his: PlanningArtifactEmission,
) -> SharedArtifactRefs:
    return replace(shared, system_his=system_his)


class FrozenContextSystemHisCorrectionFacade:
    """One-call M5 correction facade; outer executor owns all revalidation."""

    def __init__(
        self,
        client: Any,
        platform: PlatformProfile,
        *,
        project_client: Any | None = None,
        project_envelope: Mapping[str, Any] | None = None,
        event_ref_resolver: Callable[[str], bool] | None = None,
    ) -> None:
        self._client = client
        self._platform = platform
        self._project_client = project_client
        self._project_envelope = (
            copy.deepcopy(dict(project_envelope)) if project_envelope is not None else None
        )
        self._event_ref_resolver = event_ref_resolver

    def correct_his(
        self,
        context: FrozenRequirementContext,
        system_his: Mapping[str, Any],
        diagnosis: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        if platform_profile_sha256(self._platform) != context.platform_profile_sha256:
            raise ValueError("PlatformProfile does not match frozen requirement context")
        failed_stage = str(diagnosis.get("failed_h_stage", ""))
        if failed_stage not in {"h0", "h1", "h2", "h3"}:
            raise ValueError("System-HIS correction requires failed_h_stage h0-h3")
        raw_diagnostics = diagnosis.get("diagnostics", [])
        if not isinstance(raw_diagnostics, list) or not all(
            isinstance(item, str) for item in raw_diagnostics
        ):
            raise ValueError("System-HIS correction diagnostics must be a list of strings")
        try:
            content = self._client.stream_chat(
                _frozen_system_his_correction_messages(
                    context, dict(system_his), failed_h_stage=failed_stage,
                    diagnostics=list(raw_diagnostics),
                )
            )
        except (ModelOutputTruncated, ModelOutputEmpty) as exc:
            return _unparsed_his_output(exc.content, str(exc))
        try:
            parsed = parse_system_his_payload(content)
        except ValueError as exc:
            return _unparsed_his_output(content, str(exc))
        return _normalize_his_project_identity(context, parsed)

    def repair_project(
        self,
        context: FrozenRequirementContext,
        project: GeneratedProject,
        diagnosis: Mapping[str, Any],
    ) -> GeneratedProject:
        if self._project_client is None:
            raise RuntimeError("missing context-native M5 project repair client")
        if self._project_envelope is None or self._event_ref_resolver is None:
            raise RuntimeError("M5 project repair requires a trusted project envelope")
        if platform_profile_sha256(self._platform) != context.platform_profile_sha256:
            raise ValueError("PlatformProfile does not match frozen requirement context")
        envelope_errors = verify_project_envelope(
            project,
            self._project_envelope,
            event_ref_resolver=self._event_ref_resolver,
        )
        if envelope_errors:
            raise ValueError(
                "M5 project envelope does not match the current candidate: "
                + "; ".join(envelope_errors)
            )
        if self._project_envelope.get("method_condition_id") != "M5":
            raise ValueError("M5 project repair requires an M5 project envelope")
        failed_stage, diagnostics = _public_project_diagnosis(diagnosis)
        resolve_project_manifest(project.files)
        editable_sources = sorted(
            str(record["path"])
            for record in self._project_envelope.get("files", [])
            if isinstance(record, Mapping)
            and record.get("file_role") == "rtl_source"
            and record.get("owner") == "composite"
            and record.get("editable") is True
            and any(
                isinstance(region, Mapping)
                and region.get("owner") == "model"
                and region.get("editable") is True
                for region in record.get("regions", [])
            )
        )
        if not editable_sources:
            raise ValueError("M5 project has no model-editable behavior region")
        content = self._project_client.chat(
            _frozen_project_repair_messages(
                context,
                project,
                failed_stage=failed_stage,
                diagnostics=diagnostics,
                editable_sources=editable_sources,
            )
        )
        edited = _parse_rtl_repair_files(content, set(editable_sources))
        files = dict(project.files)
        files.update(edited)
        repaired = GeneratedProject(project.project_name, files)
        patch = build_patch_metadata(
            project,
            repaired,
            {
                "diagnosis_id": str(diagnosis.get("diagnosis_id", "public-repair")),
                "stage": failed_stage,
                "diagnostics": diagnostics,
            },
        )
        if not patch.allowed_edit_regions_respected:
            raise ValueError("M5 project repair violated the model edit surface")
        project_package_sha256(repaired)
        _validate_his_project(repaired)
        return repaired


def _canonicalize_skeleton(
    project: GeneratedProject,
    system_his: Mapping[str, Any],
    platform: PlatformProfile,
) -> GeneratedProject:
    files = dict(project.files)
    top = system_his.get("top") if isinstance(system_his.get("top"), dict) else {}
    artifacts = (
        system_his.get("artifacts")
        if isinstance(system_his.get("artifacts"), dict)
        else {}
    )
    rtl_sources = [
        path for path in artifacts.get("rtl_sources", []) if isinstance(path, str)
    ]
    top_source = rtl_sources[0] if rtl_sources else "rtl/top.v"
    top_module = str(artifacts.get("top_module") or top.get("name") or "top")
    ports = []
    for port in top.get("ports", []):
        if not isinstance(port, dict):
            continue
        width = port.get("width", 1)
        if isinstance(width, dict):
            width = width.get("resolved", width.get("expr", 1))
        ports.append(
            {
                "name": str(port.get("name", "")),
                "direction": str(port.get("direction", port.get("dir", "input"))),
                "width": width,
            }
        )
    artifact_roles = {
        "system_his.json": "system_his",
        CANONICAL_TIMING_CONSTRAINT_PATH: "constraint",
        "sim/tb_top.v": "candidate_testbench",
        CANONICAL_PREDICTED_QOR_PATH: "predicted_qor",
    }
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": project.project_name,
        "top": {
            "module": top_module,
            "source": top_source,
            "interface": {"ports": ports},
        },
        "sources": [
            {"path": path, "role": "rtl_source", "language": "verilog"}
            for path in rtl_sources
        ],
        "artifacts": [
            {"path": path, "role": role, "applicability": "advisory"}
            for path, role in artifact_roles.items()
            if path in files
        ],
        "build": {
            "toolchain_id": re.sub(r"[^A-Za-z0-9_.-]+", "_", platform.toolchain),
            "language_standard": "verilog-2005",
        },
    }
    files["manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    return GeneratedProject(project.project_name, files)


def _rtl_sources(project: GeneratedProject) -> list[str]:
    manifest = json.loads(project.files["manifest.json"])
    return [entry["path"] for entry in manifest["sources"]]


def _attach_frozen_system_his(
    project: GeneratedProject,
    system_his: Mapping[str, Any],
) -> GeneratedProject:
    files = dict(project.files)
    manifest = json.loads(files["manifest.json"])
    if manifest.get("project_name") != project.project_name:
        raise ValueError("M3 manifest project_name does not match frozen project name")
    if any(
        "BEHAVIOR_HOLE" in files.get(entry.get("path"), "")
        for entry in manifest.get("sources", [])
        if isinstance(entry, dict)
    ):
        raise ValueError("M3 free project must not contain BEHAVIOR_HOLE markers")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("canonical manifest artifacts must be a list")
    if any(
        isinstance(entry, dict) and entry.get("path") == "system_his.json"
        for entry in artifacts
    ):
        raise ValueError("M3 model output must not declare system_his.json")
    artifacts.append(
        {
            "path": "system_his.json",
            "role": "system_his",
            "applicability": "required",
        }
    )
    files["system_his.json"] = (
        json.dumps(system_his, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    files["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return GeneratedProject(project.project_name, files)


def _validate_his_project(project: GeneratedProject) -> None:
    issues = check_rtl_identifiers(project, _rtl_sources(project))
    if issues:
        raise ValueError("HIS2PROJECT RTL identifier check failed")
    crosscheck = check_his_project_consistency(project)
    if not crosscheck.passed:
        raise ValueError(
            "HIS2PROJECT RTL cross-check failed: " + "; ".join(crosscheck.errors)
        )


def _validate_static_his_skeleton(skeleton: GeneratedProject) -> None:
    crosscheck = check_his_project_consistency(skeleton)
    if not crosscheck.passed:
        raise ValueError(
            "static deterministic skeleton is inconsistent: "
            + "; ".join(crosscheck.errors)
        )


def _unparsed_his_output(content: str, error: str) -> dict[str, Any]:
    # Retain the exact failed response as a clearly tagged provisional artifact.
    # This is deliberately NOT a System-HIS object: unchanged H0 schema checks
    # reject it, so only an explicitly budgeted M5 correction can proceed.
    return {"contract_version": "unparsed-system-his-output-v1",
            "raw_output": content, "parse_error": error}


def _normalize_his_project_identity(
    context: FrozenRequirementContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = copy.deepcopy(dict(payload))
    expected = frozen_public_project_request(context).project_name
    if "project_name" in normalized:
        normalized["project_name"] = expected
    project = normalized.get("project")
    if isinstance(project, dict):
        if "name" in project:
            project["name"] = expected
        if "project_name" in project:
            project["project_name"] = expected
    return normalized


def _public_project_diagnosis(
    diagnosis: Mapping[str, Any],
) -> tuple[str, list[str]]:
    stage = str(diagnosis.get("stage", "")).strip()
    if not stage:
        raise ValueError("M5 project repair requires a public failure stage")
    raw = diagnosis.get("diagnostics", [])
    if not isinstance(raw, list) or not raw or not all(
        isinstance(item, str) and item.strip() for item in raw
    ):
        raise ValueError("M5 project repair diagnostics must be non-empty strings")
    return stage, list(raw)


def _parse_rtl_repair_files(content: str, allowed: set[str]) -> dict[str, str]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"M5 project repair output is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict) or set(payload) != {"rtl_files"}:
        raise ValueError("M5 project repair output must contain only rtl_files")
    raw = payload["rtl_files"]
    if not isinstance(raw, dict) or not raw:
        raise ValueError("M5 project repair rtl_files must be a non-empty object")
    paths = {str(path) for path in raw}
    if not paths.issubset(allowed):
        raise ValueError("M5 project repair attempted a non-editable path")
    return {str(path): str(value) for path, value in raw.items()}
