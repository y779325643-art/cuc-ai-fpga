"""Development-only terminal public-evaluator boundary and shadow runner."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from sr2fpga_agent.models import (
    GeneratedProject,
    ToolResult,
    canonical_json_bytes as _canonical_json,
)
from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.parsers import check_project_package_l0, resolve_project_manifest
from sr2fpga_agent.path_safety import (
    UnsupportedSynthesisLanguageError,
    build_yosys_script,
    validate_project_relative_path,
)
from sr2fpga_agent.public_l2_harness import (
    DevelopmentTrustedPublicL2Harness,
    candidate_simulation_violations,
    instrument_trusted_completion,
    unavailable_public_l2_harness_evidence,
)
from sr2fpga_agent.rtl_identifier_checker import check_rtl_identifiers
from sr2fpga_agent.tool_runner import CommandRunner


@dataclass(frozen=True)
class PublicEvaluatorInput:
    terminal_project: GeneratedProject
    terminal_candidate_sha256: str
    public_contract_sha256: str
    public_profile_sha256: str
    tool_environment_policy_sha256: str


@dataclass(frozen=True)
class AttemptPublicEvaluatorInput:
    terminal_project: GeneratedProject
    public_evaluation_candidate_sha256: str
    public_contract_sha256: str
    public_profile_sha256: str
    tool_environment_policy_sha256: str


@dataclass(frozen=True)
class PublicEvaluatorResult:
    execution_status: str
    infrastructure_reason: str | None
    stage_outcomes: Mapping[str, Mapping[str, str | None]]
    diagnostic_codes: tuple[str, ...]
    raw_evaluator_record: Mapping[str, Any]
    public_l2_harness: Mapping[str, str | None] | None = None


@dataclass(frozen=True)
class DevelopmentPublicOutcome:
    payload: Mapping[str, Any]
    artifact_ref: ArtifactRef


class DevelopmentTerminalPublicEvaluationAuthority:
    """Run a sealed terminal candidate in a separate public evaluator store.

    This is a development shadow boundary only.  It cannot select candidates,
    grant pass credit, return diagnostics to repair, or mint official outcomes.
    """

    def __init__(
        self,
        candidate_store: ArtifactStore,
        evaluator_store: ArtifactStore,
        evaluator: Callable[[PublicEvaluatorInput, str], PublicEvaluatorResult],
    ) -> None:
        if candidate_store.root.resolve() == evaluator_store.root.resolve():
            raise ValueError("candidate and public evaluator stores must be separate")
        self._candidate_store = candidate_store
        self._evaluator_store = evaluator_store
        self._evaluator = evaluator

    def evaluate_once(
        self,
        *,
        terminal_candidate_ref: ArtifactRef,
        public_contract_sha256: str,
        public_profile_sha256: str,
        tool_environment_policy_sha256: str,
    ) -> DevelopmentPublicOutcome:
        for label, value in (
            ("public_contract_sha256", public_contract_sha256),
            ("public_profile_sha256", public_profile_sha256),
            ("tool_environment_policy_sha256", tool_environment_policy_sha256),
        ):
            _require_sha256(label, value)
        terminal = _read_terminal(self._candidate_store, terminal_candidate_ref)
        project = self._candidate_store.read_sealed_project(terminal_candidate_ref)
        ledger_payload = {
            "episode_id": terminal["episode_id"],
            "method_condition": terminal["method_condition_id"],
            "terminal_candidate_sha256": terminal_candidate_ref.sha256,
            "public_contract_sha256": public_contract_sha256,
            "public_profile_sha256": public_profile_sha256,
            "tool_environment_policy_sha256": tool_environment_policy_sha256,
        }
        ledger_digest = hashlib.sha256(_canonical_json(ledger_payload)).hexdigest()
        ledger_ref = self._evaluator_store.consume_once(
            f"public-{ledger_digest}", terminal_candidate_ref.sha256
        )
        evaluator_input = PublicEvaluatorInput(
            terminal_project=project,
            terminal_candidate_sha256=terminal_candidate_ref.sha256,
            public_contract_sha256=public_contract_sha256,
            public_profile_sha256=public_profile_sha256,
            tool_environment_policy_sha256=tool_environment_policy_sha256,
        )
        try:
            result = self._evaluator(evaluator_input, ledger_digest)
            _validate_result(result)
            raw_record: Mapping[str, Any] = result.raw_evaluator_record
        except Exception as exc:  # raw details remain evaluator-private
            result = PublicEvaluatorResult(
                execution_status="not_run",
                infrastructure_reason="evaluator_exception",
                stage_outcomes={
                    stage: _stage("not_run", "evaluator_exception")
                    for stage in ("l0", "l1", "public_l2", "l3")
                },
                diagnostic_codes=("evaluator_exception",),
                raw_evaluator_record={},
            )
            raw_record = {
                "private_exception_type": type(exc).__name__,
                "private_message": str(exc),
            }
        private_record = {
            "record_version": "development-terminal-public-private-v1",
            "evaluation_scope": "development_terminal_shadow_only",
            "ledger": ledger_payload,
            "one_shot_ledger_ref": ledger_ref.key,
            "execution_status": result.execution_status,
            "infrastructure_reason": result.infrastructure_reason,
            "raw_evaluator_record": dict(raw_record),
        }
        self._evaluator_store.put_blob(
            f"private-public-outcomes/{ledger_digest}",
            _canonical_json(private_record),
            media_type="application/json",
        )
        public_acceptance = all(
            result.stage_outcomes[stage]["status"] == "pass"
            for stage in ("l0", "l1", "public_l2", "l3")
        )
        without_id = {
            "contract_version": "development-terminal-public-outcome-v1",
            "evaluation_scope": "development_terminal_shadow_only",
            "evaluator_identity": "development-public-evaluator-v1",
            "episode_id": terminal["episode_id"],
            "method_condition": terminal["method_condition_id"],
            "terminal_candidate_sha256": terminal_candidate_ref.sha256,
            "public_contract_sha256": public_contract_sha256,
            "public_profile_sha256": public_profile_sha256,
            "tool_environment_policy_sha256": tool_environment_policy_sha256,
            "one_shot_ledger_ref": ledger_ref.key,
            "execution_status": result.execution_status,
            "infrastructure_reason": result.infrastructure_reason,
            "stage_outcomes": {
                stage: dict(result.stage_outcomes[stage])
                for stage in ("l0", "l1", "public_l2", "l3")
            },
            "public_l2_harness": _public_l2_harness_evidence(result),
            "diagnostic_codes": sorted(set(result.diagnostic_codes)),
            "public_acceptance": public_acceptance,
            "repair_visible": False,
            "pass_credit_authority": False,
            "official_outcome": False,
            "vpp_l3": None,
        }
        payload = {
            **without_id,
            "outcome_id": "public-outcome-"
            + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
        }
        reference = self._candidate_store.put_validated_json(
            f"public-authority-outcomes/{terminal['episode_id']}/{terminal['method_condition_id']}",
            payload,
            contract_key="development_terminal_public_outcome",
        )
        return DevelopmentPublicOutcome(payload, reference)

    @property
    def candidate_store(self) -> ArtifactStore:
        return self._candidate_store

    @property
    def evaluator_store(self) -> ArtifactStore:
        return self._evaluator_store


class DevelopmentAttemptPublicEvaluationAuthority:
    """Evaluate one immutable attempt under shadow or development authority."""

    def __init__(
        self,
        candidate_store: ArtifactStore,
        evaluator_store: ArtifactStore,
        evaluator: Callable[[AttemptPublicEvaluatorInput, str], PublicEvaluatorResult],
        *,
        authoritative: bool = False,
    ) -> None:
        if candidate_store.root.resolve() == evaluator_store.root.resolve():
            raise ValueError("candidate and public evaluator stores must be separate")
        self._candidate_store = candidate_store
        self._evaluator_store = evaluator_store
        self._evaluator = evaluator
        self._authoritative = authoritative

    def evaluate_once(
        self,
        *,
        public_evaluation_candidate_ref: ArtifactRef,
        public_contract_sha256: str,
        public_profile_sha256: str,
        tool_environment_policy_sha256: str,
    ) -> DevelopmentPublicOutcome:
        for label, value in (
            ("public_contract_sha256", public_contract_sha256),
            ("public_profile_sha256", public_profile_sha256),
            ("tool_environment_policy_sha256", tool_environment_policy_sha256),
        ):
            _require_sha256(label, value)
        candidate = _read_public_evaluation_candidate(
            self._candidate_store, public_evaluation_candidate_ref
        )
        project = self._candidate_store.read_public_evaluation_candidate(
            public_evaluation_candidate_ref
        )
        ledger_payload = {
            "episode_id": candidate["episode_id"],
            "attempt_id": candidate["attempt_id"],
            "method_condition": candidate["method_condition_id"],
            "public_evaluation_candidate_sha256": public_evaluation_candidate_ref.sha256,
            "public_contract_sha256": public_contract_sha256,
            "public_profile_sha256": public_profile_sha256,
            "tool_environment_policy_sha256": tool_environment_policy_sha256,
        }
        ledger_digest = hashlib.sha256(_canonical_json(ledger_payload)).hexdigest()
        ledger_ref = self._evaluator_store.consume_once(
            f"public-attempt-{ledger_digest}", public_evaluation_candidate_ref.sha256
        )
        evaluator_input = AttemptPublicEvaluatorInput(
            terminal_project=project,
            public_evaluation_candidate_sha256=public_evaluation_candidate_ref.sha256,
            public_contract_sha256=public_contract_sha256,
            public_profile_sha256=public_profile_sha256,
            tool_environment_policy_sha256=tool_environment_policy_sha256,
        )
        try:
            result = self._evaluator(evaluator_input, ledger_digest)
            _validate_result(result)
            raw_record: Mapping[str, Any] = result.raw_evaluator_record
        except Exception as exc:  # raw details remain evaluator-private
            result = PublicEvaluatorResult(
                execution_status="not_run",
                infrastructure_reason="evaluator_exception",
                stage_outcomes={
                    stage: _stage("not_run", "evaluator_exception")
                    for stage in ("l0", "l1", "public_l2", "l3")
                },
                diagnostic_codes=("evaluator_exception",),
                raw_evaluator_record={},
            )
            raw_record = {
                "private_exception_type": type(exc).__name__,
                "private_message": str(exc),
            }
        private_record = {
            "record_version": "development-attempt-public-private-v1",
            "evaluation_scope": (
                "development_attempt_authority"
                if self._authoritative
                else "development_attempt_shadow_only"
            ),
            "ledger": ledger_payload,
            "one_shot_ledger_ref": ledger_ref.key,
            "execution_status": result.execution_status,
            "infrastructure_reason": result.infrastructure_reason,
            "raw_evaluator_record": dict(raw_record),
        }
        self._evaluator_store.put_blob(
            f"private-public-attempt-outcomes/{ledger_digest}",
            _canonical_json(private_record),
            media_type="application/json",
        )
        complete_project = candidate.get("project_envelope_ref") is not None
        public_acceptance = complete_project and all(
            result.stage_outcomes[stage]["status"] == "pass"
            for stage in ("l0", "l1", "public_l2", "l3")
        )
        if self._authoritative:
            return self._authoritative_outcome(
                candidate=candidate,
                candidate_ref=public_evaluation_candidate_ref,
                ledger_ref=ledger_ref,
                public_contract_sha256=public_contract_sha256,
                public_profile_sha256=public_profile_sha256,
                tool_environment_policy_sha256=tool_environment_policy_sha256,
                result=result,
                complete_project=complete_project,
                public_acceptance=public_acceptance,
            )
        without_id = {
            "contract_version": "development-attempt-public-outcome-v1",
            "evaluation_scope": "development_attempt_shadow_only",
            "evaluator_identity": "development-public-evaluator-v1",
            "episode_id": candidate["episode_id"],
            "attempt_id": candidate["attempt_id"],
            "method_condition": candidate["method_condition_id"],
            "public_evaluation_candidate_sha256": public_evaluation_candidate_ref.sha256,
            "public_contract_sha256": public_contract_sha256,
            "public_profile_sha256": public_profile_sha256,
            "tool_environment_policy_sha256": tool_environment_policy_sha256,
            "one_shot_ledger_ref": ledger_ref.key,
            "execution_status": result.execution_status,
            "infrastructure_reason": result.infrastructure_reason,
            "stage_outcomes": {
                stage: dict(result.stage_outcomes[stage])
                for stage in ("l0", "l1", "public_l2", "l3")
            },
            "public_l2_harness": _public_l2_harness_evidence(result),
            "diagnostic_codes": sorted(set(result.diagnostic_codes)),
            "public_acceptance": public_acceptance,
            "repair_visible": False,
            "pass_credit_authority": False,
            "official_outcome": False,
            "vpp_l3": None,
        }
        payload = {
            **without_id,
            "outcome_id": "public-attempt-outcome-"
            + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
        }
        reference = self._candidate_store.put_validated_json(
            "public-attempt-authority-outcomes/"
            f"{candidate['episode_id']}/{candidate['attempt_id']}/"
            f"{candidate['method_condition_id']}",
            payload,
            contract_key="development_attempt_public_outcome",
        )
        return DevelopmentPublicOutcome(payload, reference)

    def _authoritative_outcome(
        self,
        *,
        candidate: Mapping[str, Any],
        candidate_ref: ArtifactRef,
        ledger_ref: ArtifactRef,
        public_contract_sha256: str,
        public_profile_sha256: str,
        tool_environment_policy_sha256: str,
        result: PublicEvaluatorResult,
        complete_project: bool,
        public_acceptance: bool,
    ) -> DevelopmentPublicOutcome:
        without_id = {
            "contract_version": "development-authoritative-attempt-public-outcome-v1",
            "evaluation_scope": "development_attempt_authority",
            "evaluator_identity": "development-public-evaluator-v1",
            "episode_id": candidate["episode_id"],
            "attempt_id": candidate["attempt_id"],
            "method_condition": candidate["method_condition_id"],
            "public_evaluation_candidate_sha256": candidate_ref.sha256,
            "public_contract_sha256": public_contract_sha256,
            "public_profile_sha256": public_profile_sha256,
            "tool_environment_policy_sha256": tool_environment_policy_sha256,
            "one_shot_ledger_ref": ledger_ref.key,
            "execution_status": result.execution_status,
            "infrastructure_reason": result.infrastructure_reason,
            "stage_outcomes": {
                stage: dict(result.stage_outcomes[stage])
                for stage in ("l0", "l1", "public_l2", "l3")
            },
            "public_l2_harness": _public_l2_harness_evidence(result),
            "diagnostic_codes": sorted(set(result.diagnostic_codes)),
            "repair_diagnosis": _authoritative_repair_diagnosis(
                result,
                complete_project=complete_project,
            ),
            "complete_project": complete_project,
            "public_acceptance": public_acceptance,
            "repair_visible": True,
            "terminal_selection_authority": True,
            "pass_credit_authority": True,
            "official_outcome": False,
            "vpp_l3": None,
        }
        payload = {
            **without_id,
            "outcome_id": "authoritative-public-attempt-outcome-"
            + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
        }
        reference = self._candidate_store.put_validated_json(
            "authoritative-public-attempt-outcomes/"
            f"{candidate['episode_id']}/{candidate['attempt_id']}/"
            f"{candidate['method_condition_id']}",
            payload,
            contract_key="development_authoritative_attempt_public_outcome",
        )
        return DevelopmentPublicOutcome(payload, reference)

    @property
    def authoritative(self) -> bool:
        return self._authoritative

    @property
    def candidate_store(self) -> ArtifactStore:
        return self._candidate_store

    @property
    def evaluator_store(self) -> ArtifactStore:
        return self._evaluator_store


class DevelopmentPublicToolEvaluator:
    """Method-neutral L0-L3 evaluator with an optional trusted public L2 harness."""

    def __init__(
        self,
        evaluator_workspace_root: Path,
        *,
        command_runner: CommandRunner | None = None,
        trusted_public_l2_harness: DevelopmentTrustedPublicL2Harness | None = None,
    ) -> None:
        self._workspace_root = Path(evaluator_workspace_root)
        self._command_runner = command_runner or CommandRunner()
        self._trusted_public_l2_harness = trusted_public_l2_harness

    def __call__(
        self,
        evaluator_input: PublicEvaluatorInput | AttemptPublicEvaluatorInput,
        evaluation_id: str,
    ) -> PublicEvaluatorResult:
        project = evaluator_input.terminal_project
        stage_outcomes = {
            stage: _stage("not_run", "upstream_stage_not_pass")
            for stage in ("l0", "l1", "public_l2", "l3")
        }
        diagnostics: list[str] = []
        raw: dict[str, Any] = {}
        public_l2_harness = (
            self._trusted_public_l2_harness.public_evidence()
            if self._trusted_public_l2_harness is not None
            else unavailable_public_l2_harness_evidence()
        )

        l0 = check_project_package_l0(project)
        try:
            manifest = resolve_project_manifest(project.files)
        except Exception as exc:
            manifest = None
            diagnostics.append("project_manifest_invalid")
            raw["manifest_exception"] = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
        identifier_issues = (
            check_rtl_identifiers(project, list(manifest.sources))
            if manifest is not None
            else ()
        )
        reserved_path_collisions = (
            _trusted_public_l2_reserved_path_collisions(project.files)
            if self._trusted_public_l2_harness is not None
            else ()
        )
        simulation_violations = (
            candidate_simulation_violations(
                project.files, manifest.sources,
                [item.content for item in self._trusted_public_l2_harness.files],
            )
            if manifest is not None and self._trusted_public_l2_harness is not None
            else ()
        )
        if (
            not l0.passed
            or manifest is None
            or identifier_issues
            or reserved_path_collisions
            or simulation_violations
        ):
            stage_outcomes["l0"] = _stage("fail", "public_l0_failed")
            if not l0.passed:
                diagnostics.append("common_project_l0_failed")
            if identifier_issues:
                diagnostics.append("rtl_identifier_check_failed")
            if reserved_path_collisions:
                diagnostics.append("public_l2_reserved_path_collision")
            diagnostics.extend(simulation_violations)
            raw["l0_errors"] = list(l0.errors)
            raw["identifier_issues"] = [str(issue) for issue in identifier_issues]
            raw["reserved_path_collisions"] = list(reserved_path_collisions)
            return PublicEvaluatorResult(
                "completed",
                None,
                stage_outcomes,
                tuple(sorted(set(diagnostics))),
                raw,
                public_l2_harness,
            )
        stage_outcomes["l0"] = _stage("pass", None)

        # The authority retains the full ID; native EDA tools need short paths.
        # Exclusive creation keeps even a digest-prefix collision fail-closed.
        workspace = self._workspace_root / hashlib.sha256(
            evaluation_id.encode("utf-8")
        ).hexdigest()[:16]
        workspace.mkdir(parents=True, exist_ok=False)
        for raw_path, content in sorted(project.files.items()):
            path = validate_project_relative_path(raw_path)
            target = workspace / Path(*path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")

        sources = list(manifest.sources)
        lint = self._command_runner.run(
            ["verilator", "--lint-only", "-Wall", "--top-module", manifest.top_module, *sources],
            cwd=workspace,
            stage="public_l1_lint",
        )
        raw["lint"] = asdict(lint)
        infrastructure = _tool_infrastructure_reason(lint)
        if infrastructure is not None:
            stage_outcomes["l1"] = _stage("not_run", infrastructure)
            diagnostics.append(infrastructure)
            return PublicEvaluatorResult(
                "not_run",
                infrastructure,
                stage_outcomes,
                tuple(sorted(set(diagnostics))),
                raw,
                public_l2_harness,
            )
        if lint.status != "passed":
            stage_outcomes["l1"] = _stage("fail", "lint_failed")
            diagnostics.append("lint_failed")
            return PublicEvaluatorResult(
                "completed",
                None,
                stage_outcomes,
                tuple(sorted(set(diagnostics))),
                raw,
                public_l2_harness,
            )
        stage_outcomes["l1"] = _stage("pass", None)
        public_l2_infrastructure: str | None = None
        if self._trusted_public_l2_harness is None:
            stage_outcomes["public_l2"] = _stage("not_run", "needs_oracle")
            diagnostics.append("public_l2_needs_oracle")
        else:
            public_l2_harness = self._trusted_public_l2_harness.public_evidence()
            public_l2_infrastructure = self._run_trusted_public_l2(
                workspace=workspace,
                sources=sources,
                stage_outcomes=stage_outcomes,
                diagnostics=diagnostics,
                raw=raw,
            )

        try:
            yosys_script = build_yosys_script(
                sources, manifest.top_module, manifest.source_languages
            )
        except UnsupportedSynthesisLanguageError:
            stage_outcomes["l3"] = _stage("fail", "unsupported_synthesis_language")
            diagnostics.append("unsupported_synthesis_language")
            return PublicEvaluatorResult(
                "completed",
                None,
                stage_outcomes,
                tuple(sorted(set(diagnostics))),
                raw,
                public_l2_harness,
            )
        except ValueError:
            stage_outcomes["l3"] = _stage("fail", "synthesis_input_invalid")
            diagnostics.append("synthesis_input_invalid")
            return PublicEvaluatorResult(
                "completed",
                None,
                stage_outcomes,
                tuple(sorted(set(diagnostics))),
                raw,
                public_l2_harness,
            )
        synth = self._command_runner.run(
            ["yosys", "-p", yosys_script], cwd=workspace, stage="public_l3_synth"
        )
        raw["synth"] = asdict(synth)
        infrastructure = _tool_infrastructure_reason(synth)
        if infrastructure is not None:
            stage_outcomes["l3"] = _stage("not_run", infrastructure)
            diagnostics.append(infrastructure)
            return PublicEvaluatorResult(
                "not_run",
                infrastructure,
                stage_outcomes,
                tuple(sorted(set(diagnostics))),
                raw,
                public_l2_harness,
            )
        if synth.status == "passed":
            stage_outcomes["l3"] = _stage("pass", None)
        else:
            stage_outcomes["l3"] = _stage("fail", "synthesis_failed")
            diagnostics.append("synthesis_failed")
        return PublicEvaluatorResult(
            "not_run" if public_l2_infrastructure is not None else "completed",
            public_l2_infrastructure,
            stage_outcomes,
            tuple(sorted(set(diagnostics))),
            raw,
            public_l2_harness,
        )

    def _run_trusted_public_l2(
        self,
        *,
        workspace: Path,
        sources: list[str],
        stage_outcomes: dict[str, dict[str, str | None]],
        diagnostics: list[str],
        raw: dict[str, Any],
    ) -> str | None:
        harness = self._trusted_public_l2_harness
        if harness is None:
            raise ValueError("trusted public L2 harness is unavailable")
        trusted_root = workspace / "__sr2fpga_trusted_public_l2"
        marker = "SR2FPGA_TRUSTED_COMPLETE_" + uuid.uuid4().hex
        harness_paths = {item.path for item in harness.files}
        trusted_paths: list[str] = []
        for item in harness.files:
            target = trusted_root / Path(*item.path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(instrument_trusted_completion(item.content, marker, harness_paths), encoding="utf-8", newline="\n")
            trusted_paths.append(target.relative_to(workspace).as_posix())

        image = "__sr2fpga_public_l2.vvp"
        language_flag = (
            "-g2012"
            if harness.language_standard == "systemverilog-2012"
            else "-g2005"
        )
        compile_result = self._command_runner.run(
            [
                "iverilog",
                "-u",
                language_flag,
                "-s",
                harness.testbench_top,
                "-o",
                image,
                *sources,
                *trusted_paths,
            ],
            cwd=workspace,
            stage="public_l2_compile",
            timeout_seconds=harness.timeout_seconds,
        )
        raw["public_l2_compile"] = asdict(compile_result)
        infrastructure = _tool_infrastructure_reason(compile_result)
        if infrastructure is not None:
            stage_outcomes["public_l2"] = _stage("not_run", infrastructure)
            diagnostics.append(infrastructure)
            return infrastructure
        if compile_result.status != "passed":
            stage_outcomes["public_l2"] = _stage("fail", "public_l2_compile_failed")
            diagnostics.append("public_l2_compile_failed")
            return None

        simulation = self._command_runner.run(
            ["vvp", "-N", image],
            cwd=workspace,
            stage="public_l2_sim",
            timeout_seconds=harness.timeout_seconds,
        )
        raw["public_l2_sim"] = asdict(simulation)
        infrastructure = _tool_infrastructure_reason(simulation)
        if infrastructure is not None:
            stage_outcomes["public_l2"] = _stage("not_run", infrastructure)
            diagnostics.append(infrastructure)
            return infrastructure
        if simulation.status == "passed" and marker in simulation.stdout.splitlines():
            stage_outcomes["public_l2"] = _stage("pass", None)
        else:
            stage_outcomes["public_l2"] = _stage("fail", "public_l2_failed")
            diagnostics.append("public_l2_failed")
        return None


def _trusted_public_l2_reserved_path_collisions(
    project_files: Mapping[str, str],
) -> tuple[str, ...]:
    collisions: list[str] = []
    for raw_path in project_files:
        try:
            path = validate_project_relative_path(raw_path)
        except ValueError:
            continue
        if path in {"__sr2fpga_public_l2.vvp", "__sr2fpga_trusted_public_l2"} or path.startswith(
            "__sr2fpga_trusted_public_l2/"
        ):
            collisions.append(path)
    return tuple(sorted(collisions))


def _read_verified_public_outcome(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    contract_key: str,
    id_prefix: str,
    label: str,
    registry: ContractRegistry | None,
) -> dict[str, Any]:
    """Verify one public-outcome artifact against its contract and content-derived ID."""

    try:
        payload = json.loads(store.read_verified(reference))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON") from exc
    contract = (registry or ContractRegistry()).load_schema(contract_key)
    errors = contract.validate(payload)
    if errors:
        raise ValueError(f"invalid {label}: " + "; ".join(errors))
    without_id = {key: value for key, value in payload.items() if key != "outcome_id"}
    expected = id_prefix + hashlib.sha256(_canonical_json(without_id)).hexdigest()
    if payload["outcome_id"] != expected:
        raise ValueError(f"{label} content-derived ID mismatch")
    _validate_outcome_harness_binding(payload)
    return payload


def read_verified_development_public_outcome(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    registry: ContractRegistry | None = None,
) -> dict[str, Any]:
    return _read_verified_public_outcome(
        store,
        reference,
        contract_key="development_terminal_public_outcome",
        id_prefix="public-outcome-",
        label="development public outcome",
        registry=registry,
    )


def read_verified_development_attempt_public_outcome(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    registry: ContractRegistry | None = None,
) -> dict[str, Any]:
    return _read_verified_public_outcome(
        store,
        reference,
        contract_key="development_attempt_public_outcome",
        id_prefix="public-attempt-outcome-",
        label="development attempt public outcome",
        registry=registry,
    )


def read_verified_development_authoritative_attempt_public_outcome(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    registry: ContractRegistry | None = None,
) -> dict[str, Any]:
    return _read_verified_public_outcome(
        store,
        reference,
        contract_key="development_authoritative_attempt_public_outcome",
        id_prefix="authoritative-public-attempt-outcome-",
        label="development authoritative attempt public outcome",
        registry=registry,
    )


def _read_terminal(store: ArtifactStore, reference: ArtifactRef) -> dict[str, Any]:
    try:
        payload = json.loads(store.read_verified(reference))
    except json.JSONDecodeError as exc:
        raise ValueError("terminal candidate is not valid JSON") from exc
    errors = ContractRegistry().load_schema("terminal_candidate").validate(payload)
    if errors:
        raise ValueError("invalid terminal candidate: " + "; ".join(errors))
    return payload


def _read_public_evaluation_candidate(
    store: ArtifactStore, reference: ArtifactRef
) -> dict[str, Any]:
    try:
        payload = json.loads(store.read_verified(reference))
    except json.JSONDecodeError as exc:
        raise ValueError("public-evaluation candidate is not valid JSON") from exc
    contract_key = (
        "public_evaluation_candidate"
        if payload.get("contract_version") == "public-evaluation-candidate-v1"
        else "public_evaluation_candidate_v2"
    )
    errors = ContractRegistry().load_schema(contract_key).validate(payload)
    if errors:
        raise ValueError("invalid public-evaluation candidate: " + "; ".join(errors))
    return payload


def _validate_result(result: PublicEvaluatorResult) -> None:
    if not isinstance(result, PublicEvaluatorResult):
        raise TypeError("public evaluator must return PublicEvaluatorResult")
    if result.execution_status not in {"completed", "not_run"}:
        raise ValueError("invalid public evaluator execution status")
    if (result.execution_status == "completed") != (
        result.infrastructure_reason is None
    ):
        raise ValueError("public evaluator infrastructure status mismatch")
    if set(result.stage_outcomes) != {"l0", "l1", "public_l2", "l3"}:
        raise ValueError("public evaluator stage set mismatch")
    for stage, outcome in result.stage_outcomes.items():
        if set(outcome) != {"status", "reason"}:
            raise ValueError(f"invalid {stage} public evaluator outcome")
        if outcome["status"] not in {"pass", "fail", "not_run"}:
            raise ValueError(f"invalid {stage} public evaluator status")
        reason = outcome["reason"]
        if reason is not None and (
            not isinstance(reason, str)
            or re.fullmatch(r"[a-z0-9][a-z0-9_.:-]*", reason) is None
        ):
            raise ValueError(f"invalid {stage} public evaluator reason")
    for code in result.diagnostic_codes:
        if (
            not isinstance(code, str)
            or re.fullmatch(r"[a-z0-9][a-z0-9_.:-]*", code) is None
        ):
            raise ValueError("invalid public evaluator diagnostic code")
    evidence = _public_l2_harness_evidence(result)
    _validate_public_l2_harness_evidence(evidence)
    if (
        result.stage_outcomes["public_l2"]["status"] in {"pass", "fail"}
        and evidence["status"] != "available"
    ):
        raise ValueError("public L2 pass/fail requires a trusted harness commitment")


def _public_l2_harness_evidence(
    result: PublicEvaluatorResult,
) -> dict[str, str | None]:
    if result.public_l2_harness is None:
        return unavailable_public_l2_harness_evidence()
    return dict(result.public_l2_harness)


def _validate_public_l2_harness_evidence(
    evidence: Mapping[str, str | None],
) -> None:
    if set(evidence) != {
        "status",
        "harness_id",
        "manifest_sha256",
        "bundle_sha256",
        "reason",
    }:
        raise ValueError("invalid public L2 harness evidence fields")
    if evidence["status"] == "available":
        harness_id = evidence["harness_id"]
        if not isinstance(harness_id, str) or re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._:-]*", harness_id
        ) is None:
            raise ValueError("invalid public L2 harness identity")
        _require_sha256("public_l2_harness.manifest_sha256", evidence["manifest_sha256"])
        _require_sha256("public_l2_harness.bundle_sha256", evidence["bundle_sha256"])
        if evidence["reason"] is not None:
            raise ValueError("available public L2 harness cannot have a missing reason")
        return
    if evidence != unavailable_public_l2_harness_evidence():
        raise ValueError("invalid unavailable public L2 harness evidence")


def _validate_outcome_harness_binding(payload: Mapping[str, Any]) -> None:
    evidence = payload.get("public_l2_harness")
    stage_status = payload["stage_outcomes"]["public_l2"]["status"]
    if evidence is None:
        if stage_status in {"pass", "fail"}:
            raise ValueError("public L2 outcome is missing a trusted harness commitment")
        return
    if not isinstance(evidence, Mapping):
        raise ValueError("invalid public L2 harness evidence")
    _validate_public_l2_harness_evidence(evidence)
    if stage_status in {"pass", "fail"} and evidence["status"] != "available":
        raise ValueError("public L2 pass/fail requires a trusted harness commitment")


def _authoritative_repair_diagnosis(
    result: PublicEvaluatorResult,
    *,
    complete_project: bool,
) -> dict[str, Any] | None:
    if result.execution_status != "completed":
        return None
    diagnostic_codes = sorted(set(result.diagnostic_codes))
    if not complete_project:
        return {
            "stage": "l0",
            "failure_type": "project_envelope_unavailable",
            "diagnostic_codes": sorted(
                set((*diagnostic_codes, "project_envelope_unavailable"))
            ),
        }
    for stage in ("l0", "l1", "public_l2", "l3"):
        outcome = result.stage_outcomes[stage]
        if outcome["status"] == "fail":
            return {
                "stage": stage,
                "failure_type": str(outcome["reason"] or f"{stage}_failed"),
                "diagnostic_codes": diagnostic_codes,
            }
    return None


def _tool_infrastructure_reason(result: ToolResult) -> str | None:
    if result.status == "missing_tool":
        return f"{result.stage}_tool_missing"
    if result.status == "timeout":
        return f"{result.stage}_timeout"
    return None


def _stage(status: str, reason: str | None) -> dict[str, str | None]:
    return {"status": status, "reason": reason}


def _require_sha256(label: str, value: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be lowercase SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be lowercase SHA-256") from exc
    if value.lower() != value:
        raise ValueError(f"{label} must be lowercase SHA-256")


