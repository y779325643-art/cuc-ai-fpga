"""PC 2.1 M0-M5 shared initial DAG, bounded repair and immutable terminals.

The controller consumes only public evaluation feedback during generation.
Terminal-private execution is a separate operation after the entire batch is
sealed. No reference implementation is imported as a generation service.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, replace
import hashlib
import io
import json
from pathlib import Path
import random
import subprocess
import time
import zipfile
from typing import Any, Callable, Mapping, Sequence

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.models import ToolResult, canonical_json_bytes
from sr2fpga_agent.pc.context import PublicTask, check_task_design
from sr2fpga_agent.pc.emitter import StructureBuild, build_structure, compose_behavior
from sr2fpga_agent.pc.inputs import ParseLimits, assemble_project_contract
from sr2fpga_agent.tasks.llm import CASE_FAMILIES

from .budgets import B4_MODEL_CALLS, BudgetError, BudgetExceeded, BudgetLedger, BudgetLimits
from .evaluation import (EvaluationResult, Pc21Evaluator, TerminalEvaluationAuthority,
                         TrustedSuite, assert_supported_case, task_identity)
from .gateway import ModelGateway, ModelStageFailure, TextTransport
from .locking import file_lock
from .isolation import IsolationUnavailable, LocalDevelopmentBackend, ToolLimits, candidate_sha256, public_task_projection
from .proposals import (BEHAVIOR_FORMAT, BODY_OWNERSHIP_GUIDANCE, DESIGN_FORMAT, PROJECT_FORMAT, REPAIR_FORMAT,
                        admit_project, apply_project_patch, parse_proposal)


METHODS = tuple(B4_MODEL_CALLS)


class RuntimeIntegrityError(RuntimeError):
    """Trusted context was actually violated; generation/claims cannot continue."""


class CompositionInfrastructureError(RuntimeError):
    """An unavailable/crashed frontend is not a candidate body defect."""


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def runtime_source_snapshot() -> dict[str, str]:
    package = Path(__file__).parents[1]
    paths = sorted([*package.rglob("*.py"), *(package.parents[2] / "contracts").rglob("*.json")])
    return {str(path.relative_to(package.parents[2])): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def terminal_value(terminal: Mapping[str, Any], public: Mapping[str, Any] | None, hidden: Mapping[str, Any]) -> int | None:
    if (hidden["hidden_execution_status"] == "integrity_error"
            or public is not None and public.get("outcome", {}).get("execution_status") == "integrity_error"):
        raise RuntimeIntegrityError("integrity violation cannot be reduced to an ordinary missing result")
    accepted = public is not None and public.get("public", {}).get("accepted", False)
    known_failure = ((terminal["candidate"] is None and not terminal["infrastructure"])
                     or public is not None and public.get("outcome", {}).get("semantic_status") == "fail")
    return 1 if accepted and hidden["hidden_semantic_status"] == "pass" else (
        0 if known_failure or hidden["hidden_semantic_status"] == "fail" else None)


@dataclass(frozen=True)
class RuntimeIdentity:
    campaign_id: str
    family_id: str
    design_cluster_id: str
    dependency_group_id: str | None
    semantic_instance_id: str
    replicate_id: str
    population_id: str = "llm_inference_subsystems_v1"

    def slot(self, method: str) -> dict[str, str]:
        return {"campaign_id": self.campaign_id, "population_id": self.population_id,
                "semantic_instance_id": self.semantic_instance_id, "replicate_id": self.replicate_id,
                "condition_id": method}


class PairedBlockRuntime:
    """One six-condition block, with replayable initial and repair operations.

    Roots must be selected by the operator and kept inaccessible to a candidate.
    Text transports receive no root or evaluator object. Local tools explicitly
    lack OS qualification; formal readiness never follows from this class.
    """

    def __init__(self, public_task: PublicTask, *, case: str, identity: RuntimeIdentity,
                 output_root: Path, evaluator_root: Path, transport: TextTransport,
                 limits: Mapping[str, BudgetLimits], tool_limits: ToolLimits,
                 backend: Any | None = None, schedule_seed: int = 0,
                 allow_model_calls: bool = False, max_model_call_seconds: float = 120,
                 public_suite: TrustedSuite | None = None,
                 final_limits: Mapping[str, BudgetLimits] | None = None,
                 evaluator_factory: Callable[..., Any] = Pc21Evaluator) -> None:
        assert_supported_case(case, public_task)
        if identity.family_id != CASE_FAMILIES[case]:
            raise ValueError("runtime family identity does not match the public task case")
        for name, value in asdict(identity).items():
            if name == "dependency_group_id" and value is None:
                continue
            if not isinstance(value, str) or not value or value != value.strip():
                raise ValueError("runtime identities must be explicit nonempty trimmed strings")
        if set(limits) != set(METHODS):
            raise ValueError("a paired block must configure all six methods")
        if identity.population_id != "llm_inference_subsystems_v1":
            raise ValueError("runtime population mismatch")
        if type(schedule_seed) is not int or schedule_seed < 0:
            raise ValueError("schedule seed must be a nonnegative integer")
        self.root, self.private_root = Path(output_root).resolve(), Path(evaluator_root).resolve()
        if (self.root == self.private_root or self.root.is_relative_to(self.private_root)
                or self.private_root.is_relative_to(self.root)):
            raise ValueError("candidate/control and evaluator-private roots must be disjoint")
        self.root.mkdir(parents=True, exist_ok=True)
        self.private_root.mkdir(parents=True, exist_ok=True)
        self.store = ArtifactStore(self.root / "store")
        self.task, self.case, self.identity = public_task, case, identity
        self.backend = backend or LocalDevelopmentBackend()
        self.tool_limits, self.schedule_seed = tool_limits, schedule_seed
        if tool_limits.timeout_seconds > public_task.target["tool_timeout_seconds"]:
            raise ValueError("tool timeout exceeds the bound public target")
        self.ledger = BudgetLedger(self.store, _sha(asdict(identity)), limits)
        self.final_limits = final_limits
        self.gateway = ModelGateway(self.store, self.ledger, transport, allow_model_calls=allow_model_calls,
                                    max_call_seconds=max_model_call_seconds)
        self.public = public_task_projection(public_task)
        self.public_suite = public_suite or TrustedSuite.for_development_case(case)
        self.evaluator_factory = evaluator_factory
        self._active_operation = "unassigned"
        self._active_consumers: tuple[str, ...] = ()
        self._tool_index = 0
        self.events: list[dict[str, Any]] = []
        configuration = {"runtime_version": "pc21-m0-m5-development-v1", "identity": asdict(identity),
            "case": case, "bindings": public_task.sources.bindings(), "schedule_seed": schedule_seed,
            "tool_limits": asdict(tool_limits), "backend": self.backend.policy(),
            "public_suite_sha256": self.public_suite.commitment_sha256,
            "source_class": transport.source_class, "tokenizer_id": transport.tokenizer_id,
            "max_model_call_seconds": max_model_call_seconds,
            "model_identity": transport.public_identity() if hasattr(transport, "public_identity") else None}
        self.store.put_blob("configuration", canonical_json_bytes(configuration), media_type="application/json")
        self._source_guard()

    def _source_guard(self) -> None:
        current = runtime_source_snapshot()
        ref = self.store.reference("source-bindings")
        if ref is None:
            package = Path(__file__).parents[1]
            repository = package.parents[2]
            archive_bytes = io.BytesIO()
            with zipfile.ZipFile(archive_bytes, "w", compression=zipfile.ZIP_STORED) as archive:
                for relative, expected in current.items():
                    content = (repository / relative).read_bytes()
                    if hashlib.sha256(content).hexdigest() != expected:
                        raise RuntimeIntegrityError("source changed while capturing preparation bytes")
                    archive.writestr(Path(relative).as_posix(), content)
            archive_ref = self.store.put_blob("trusted-source-archive", archive_bytes.getvalue(), media_type="application/zip")
            try:
                revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository,
                    capture_output=True, text=True, timeout=5, check=False)
                git_head = revision.stdout.strip() if revision.returncode == 0 else None
            except (OSError, subprocess.TimeoutExpired):
                git_head = None
            self.store.put_blob("code-state", canonical_json_bytes({"git_head": git_head,
                "capture_scope": "actual_agent_python_and_contract_json_bytes_including_uncommitted_sources",
                "source_archive": archive_ref.to_dict(), "source_bindings_sha256": _sha(current)}), media_type="application/json")
            self.store.put_blob("source-bindings", canonical_json_bytes(current), media_type="application/json")
        elif self.store.read_verified(ref) != canonical_json_bytes(current):
            raise ValueError("runtime/checker/evaluator/contracts changed after block preparation")

    def _event(self, kind: str, **payload: Any) -> None:
        self.store.append_event("pc21-runtime", kind, payload)
        self.events.append({"event_type": kind, **payload})

    def _cached(self, operation: str, consumers: Sequence[str], action: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        self._source_guard()
        key = "nodes/" + _sha(operation)
        previous = self.store.reference(key)
        if previous is not None:
            return json.loads(self.store.read_verified(previous))
        self._active_operation, self._active_consumers, self._tool_index = operation, tuple(consumers), 0
        try:
            value = action()
        except BudgetExceeded as error:
            value = {"ok": False, "reason": "resource_budget_exhausted", "diagnostic": str(error), "resource_exhausted": True}
        except (CompositionInfrastructureError, IsolationUnavailable) as error:
            value = {"ok": False, "reason": "tool_infrastructure_error", "diagnostic": self._diagnostic(error), "infrastructure": True}
        encoded = canonical_json_bytes(value)
        self.store.put_blob(key, encoded, media_type="application/json")
        return json.loads(encoded)

    def _meter_pure(self, stage: str, operation: Callable[[], Any]) -> Any:
        consumers = self._active_consumers
        cache_key = "pure/" + _sha(self._active_operation + "/" + stage)
        prior = self.store.reference(cache_key)
        if prior is not None:
            saved = json.loads(self.store.read_verified(prior))
            self.ledger.reconcile(saved["reservation_id"], observed=saved["usage"], outcome=saved["outcome"])
            if saved["kind"] == "error":
                raise ValueError(saved["error"])
            return StructureBuild(**saved["value"]) if saved["kind"] == "build" else saved["value"]
        wall_bound = min(float(self.ledger.remaining(m, "active_seconds")) for m in consumers)
        cpu_bound = min(float(self.ledger.remaining(m, "cpu_seconds")) for m in consumers)
        if wall_bound <= 0 or cpu_bound <= 0:
            raise BudgetExceeded("no deterministic checking resource remains")
        reservation = self.ledger.reserve(self._active_operation + "/" + stage, consumers,
                                          active_seconds=wall_bound, cpu_seconds=cpu_bound)
        self.ledger.dispatch(reservation.reservation_id)
        wall, cpu = time.monotonic(), time.process_time()
        outcome = "completed"
        usage = None
        try:
            value = operation()
            usage = {"active_seconds": time.monotonic() - wall, "cpu_seconds": time.process_time() - cpu}
            self.store.put_blob(cache_key, canonical_json_bytes({"reservation_id": reservation.reservation_id,
                "usage": usage, "outcome": "completed", "kind": "build" if isinstance(value, StructureBuild) else "json",
                "value": asdict(value) if isinstance(value, StructureBuild) else value}), media_type="application/json")
            return value
        except ValueError as error:
            outcome = "failed"
            usage = {"active_seconds": time.monotonic() - wall, "cpu_seconds": time.process_time() - cpu}
            self.store.put_blob(cache_key, canonical_json_bytes({"reservation_id": reservation.reservation_id,
                "usage": usage, "outcome": outcome, "kind": "error", "error": str(error)}), media_type="application/json")
            raise
        except Exception:
            outcome = "failed"
            raise
        finally:
            if usage is None:
                usage = {"active_seconds": time.monotonic() - wall, "cpu_seconds": time.process_time() - cpu}
            self.ledger.reconcile(reservation.reservation_id, outcome=outcome,
                                  observed=usage)

    def _tool_budget(self, stage: str, limits: ToolLimits, execute: Callable[[], ToolResult]) -> ToolResult:
        consumers = self._active_consumers
        self._tool_index += 1
        operation = self._active_operation + f"/tool-{self._tool_index:03d}-" + stage
        reservation = self.ledger.reserve(operation, consumers, public_tool_calls=1,
            active_seconds=limits.timeout_seconds, eda_seconds=limits.timeout_seconds,
            cpu_seconds=limits.cpu_seconds, memory_bytes=limits.memory_bytes)
        self.ledger.dispatch(reservation.reservation_id)
        try:
            result = execute()
        except Exception:
            self.ledger.reconcile(reservation.reservation_id, outcome="unknown",
                observed={"active_seconds": None, "eda_seconds": None, "cpu_seconds": None, "memory_bytes": None})
            raise
        self.ledger.reconcile(reservation.reservation_id, outcome="completed" if result.status == "passed" else "failed",
            observed={"active_seconds": result.duration_seconds, "eda_seconds": result.duration_seconds,
                      "cpu_seconds": None, "memory_bytes": None},
            unavailable_reasons={"cpu_seconds": "worker_cpu_usage_unmeasured", "memory_bytes": "worker_peak_memory_unmeasured"})
        return result

    def _frontend_runner(self, command: list[str], cwd: Path, timeout: float) -> ToolResult:
        limits = replace(self.tool_limits, timeout_seconds=min(timeout, self.tool_limits.timeout_seconds))
        result = self._tool_budget("composition", limits, lambda: self.backend.run(command, cwd, "composition", limits))
        if result.status == "missing_tool" or result.exit_code is not None and (
                result.exit_code < 0 or result.exit_code > 255):
            raise CompositionInfrastructureError("composition tool unavailable or crashed")
        return result

    def _call(self, operation: str, stage: str, consumers: Sequence[str], payload: Mapping[str, Any], fmt: str) -> dict[str, Any]:
        if self.store.reference("integrity-stop") is not None:
            raise RuntimeIntegrityError("block stopped after an integrity violation")
        if self.store.reference("generation-closed") is not None:
            raise PermissionError("generation is sealed; private results cannot open another model opportunity")
        try:
            response = self.gateway.call(operation, stage, consumers, {"public_task": self.public, **payload}, output_format=fmt)
            self._source_guard()
            return {"ok": True, "text": response.text}
        except (ModelStageFailure, BudgetError) as error:
            self._event("model_stage_failed", operation=operation, stage=stage, reason=str(error))
            return {"ok": False, "reason": str(error), "resource_exhausted": isinstance(error, BudgetExceeded) or (
                isinstance(error, ModelStageFailure) and error.reason in {
                    "output_budget_exhausted", "active_budget_exhausted", "model_budget_exceeded"}), "infrastructure": (
                isinstance(error, ModelStageFailure) and error.reason in {
                    "provider_call_failed", "transport_execution_unknown", "model_operation_dispatch_unresolved"}),
                    "previous_output": error.response.text if isinstance(error, ModelStageFailure) and error.response else None}

    def _check_pc(self, text: str) -> dict[str, Any]:
        def check():
            pc = assemble_project_contract(text.encode(), self.task.sources, limits=ParseLimits(8_000_000, 128))
            check_task_design(pc["design"], self.task)
            return {"ok": True, "pc": pc}
        try:
            return self._meter_pure("pc-check", check)
        except ValueError as error:
            return {"ok": False, "reason": "pc_rejected", "diagnostic": self._diagnostic(error), "previous_output": text}

    def _diagnostic(self, error: Exception) -> str:
        return str(error).replace(str(self.private_root), "<tool-work>").replace(str(self.root), "<control>")[:6000]

    def _build(self, pc: dict[str, Any]) -> StructureBuild:
        def build():
            checked = check_task_design(pc["design"], self.task)
            return build_structure(checked, bindings=pc["bindings"], toolchain_id=self.task.target["target_id"])
        return self._meter_pure("structure-build", build)

    def _compose(self, build: StructureBuild, bundle: dict[str, Any]) -> dict[str, Any]:
        project = compose_behavior(build, bundle, timeout_seconds=self.tool_limits.timeout_seconds,
            scratch_root=self.private_root / "c" / _sha(self._active_operation)[:12],
            frontend_runner=self._frontend_runner)
        return {"files": project.files, "construction_origin_map": project.construction_origin_map,
                "build_plan_sha256": project.build_plan_sha256}

    def _admit(self, files: dict[str, str], *, pc=None, build=None, bundle=None,
               construction_origin_map=None, parent=None) -> dict[str, Any]:
        files = admit_project(files)
        digest = candidate_sha256(files)
        record = {"candidate_sha256": digest, "files": files, "pc": pc,
                  "build": asdict(build) if build is not None else None, "bundle": bundle,
                  "construction_origin_map": construction_origin_map, "parent_candidate_sha256": parent,
                  "source_class": self.gateway.transport.source_class}
        key = "candidate-records/" + _sha(record)
        existing = self.store.reference(key)
        reference = self.store.put_blob(key, canonical_json_bytes(record), media_type="application/json")
        if existing is None:
            self._event("candidate_committed", candidate_sha256=digest, parent_candidate_sha256=parent,
                        operation=self._active_operation)
        return {**record, "artifact_ref": reference.to_dict()}

    def _evaluate(self, candidate: dict[str, Any], consumers: Sequence[str], operation: str) -> dict[str, Any]:
        def run():
            cycle = self.ledger.reserve(operation + "/public-cycle", consumers, public_cycles=1)
            self.ledger.dispatch(cycle.reservation_id)
            evaluator = self.evaluator_factory(self.case, self.task, self.private_root / "public", backend=self.backend,
                tool_budget=self._tool_budget, synthesize=True, suite=self.public_suite, limits=self.tool_limits)
            try:
                result = evaluator.evaluate(copy.deepcopy(candidate["files"]), evaluation_id=_sha(operation), visibility="public")
            finally:
                self.ledger.reconcile(cycle.reservation_id, observed={}, outcome="completed")
            private = result.to_dict(include_private=True)
            self.store.put_blob("public-outcomes/" + _sha(operation), canonical_json_bytes(private), media_type="application/json")
            if result.execution_status == "integrity_error":
                self.store.put_blob("integrity-stop", canonical_json_bytes({"operation": operation}), media_type="application/json")
                raise RuntimeIntegrityError("public worker reported an integrity violation")
            return {"ok": True, "public": result.public_feedback(), "outcome": result.to_dict(),
                    "candidate_sha256": candidate["candidate_sha256"]}
        try:
            return self._cached(operation, consumers, run)
        except BudgetError as error:
            return {"ok": False, "public": {"accepted": False, "diagnostic_codes": ["public_budget_exhausted"]},
                    "resource_exhausted": True, "reason": str(error), "candidate_sha256": candidate["candidate_sha256"]}

    def _project_node(self, operation: str, stage: str, consumers: Sequence[str], payload: dict[str, Any]) -> dict[str, Any]:
        def execute():
            shared_formats = {"project_proposal_schema": ContractRegistry().load_schema("pc21_project_proposal").document,
                              "project_manifest_schema": ContractRegistry().load_schema("project_package").document}
            proposed = self._call(operation, stage, consumers, {**payload, **shared_formats}, PROJECT_FORMAT)
            if not proposed["ok"]:
                return proposed
            try:
                document = parse_proposal(proposed["text"], "pc21_project_proposal")
                candidate = self._meter_pure("project-admission", lambda: self._admit(document["files"], pc=payload.get("pc")))
                return {"ok": True, "candidate": candidate}
            except ValueError as error:
                return {"ok": False, "reason": "project_rejected", "diagnostic": self._diagnostic(error), "previous_output": proposed["text"]}
        return self._cached(operation, consumers, execute)

    def _body_node(self, operation: str, consumers: Sequence[str], pc: dict[str, Any],
                   *, previous_build: dict[str, Any] | None = None,
                   feedback: dict[str, Any] | None = None) -> dict[str, Any]:
        def execute():
            try:
                build = StructureBuild(**previous_build) if previous_build is not None else self._build(pc)
                if build.units:
                    proposed = self._call(operation, "behavior", consumers,
                        {"pc": pc, "build_plan_sha256": build.build_plan_sha256, "required_units": build.units,
                         "behavior_bundle_schema": ContractRegistry().load_schema("pc21_behavior_bundle").document,
                         "behavior_body_ownership": BODY_OWNERSHIP_GUIDANCE,
                         "public_feedback": feedback}, BEHAVIOR_FORMAT)
                    if not proposed["ok"]:
                        return {**proposed, "pc": pc, "build": asdict(build)}
                    bundle = parse_proposal(proposed["text"], "pc21_behavior_bundle")
                else:
                    self._event("behavior_not_applicable", operation=operation, reason="no_behavior_units")
                    bundle = {"contract_version": "pc21-behavior-bundle-v1", "build_plan_sha256": build.build_plan_sha256, "units": {}}
                composed = self._compose(build, bundle)
                candidate = self._admit(composed["files"], pc=pc, build=build, bundle=bundle,
                                        construction_origin_map=composed["construction_origin_map"])
                return {"ok": True, "candidate": candidate, "pc": pc, "build": asdict(build), "bundle": bundle}
            except ValueError as error:
                return {"ok": False, "reason": "behavior_rejected", "diagnostic": self._diagnostic(error),
                        "pc": pc, "build": asdict(build) if "build" in locals() else None,
                        "previous_output": proposed["text"] if "proposed" in locals() and proposed["ok"] else None}
        return self._cached(operation, consumers, execute)

    @staticmethod
    def _state(initial: dict[str, Any]) -> dict[str, Any]:
        return {"last_candidate": initial.get("candidate"), "pc": initial.get("pc"),
                "build": initial.get("build"), "bundle": initial.get("bundle"),
                "feedback": {k: v for k, v in initial.items() if k in {"reason", "diagnostic", "previous_output"}},
                "evaluation": None, "infrastructure": initial.get("infrastructure", False),
                "resource_exhausted": initial.get("resource_exhausted", False), "repairs": []}

    def _repair(self, method: str, state: dict[str, Any]) -> None:
        ordinal = 0
        checkpoints = sorted(ref.key for ref in self.store.event_refs("pc21-checkpoint-" + method))
        if checkpoints:
            event = json.loads(self.store.read_verified(checkpoints[-1]))
            saved = event["payload"]
            ordinal = saved["ordinal"]
            state.clear()
            state.update(saved["state"])
        while not state["infrastructure"] and not state.get("resource_exhausted", False):
            if state["evaluation"] is not None and state["evaluation"].get("public", {}).get("accepted"):
                return
            ordinal += 1
            operation = f"repair-{method}-{ordinal:03d}"
            recoverable = any(self.store.reference(prefix) is not None for prefix in (
                "nodes/" + _sha(operation), "pc21-model/" + hashlib.sha256(operation.encode()).hexdigest() + "/request",
                "pc21-model/" + hashlib.sha256((operation + "/fill").encode()).hexdigest() + "/request"))
            calls_before = self.ledger.remaining(method, "model_calls")
            if calls_before <= 0 and not recoverable:
                break
            def execute():
                candidate = state["last_candidate"]
                if method == "M5" and state["pc"] is not None and state["build"] is not None and state["bundle"] is None:
                    return self._body_node(operation + "/fill", (method,), state["pc"], previous_build=state["build"], feedback=state["feedback"])
                permitted = (["replace_project"] if candidate is None else ["replace_project", "replace_project_files"]) if method == "M1" else (
                    ["replace_design"] if state["pc"] is None or state["build"] is None else ["replace_design", "replace_behavior_units"])
                response = self._call(operation, "repair_" + method, (method,), {
                    "permitted_actions": permitted, "public_feedback": state["feedback"],
                    "current_candidate_sha256": candidate["candidate_sha256"] if candidate else None,
                    "current_files": candidate["files"] if candidate else None, "pc": state["pc"],
                    "build": state["build"], "behavior_bundle": state["bundle"],
                    "behavior_body_ownership": BODY_OWNERSHIP_GUIDANCE if method == "M5" else None,
                    "repair_proposal_schema": ContractRegistry().load_schema("pc21_repair_proposal").document,
                    "project_manifest_schema": ContractRegistry().load_schema("project_package").document,
                    "design_schema": ContractRegistry().load_schema("design_proposal_2_1").document if method == "M5" else None},
                    REPAIR_FORMAT)
                if not response["ok"]:
                    return response
                try:
                    proposal = parse_proposal(response["text"], "pc21_repair_proposal")
                    action = proposal["action"]
                    if action not in permitted:
                        raise ValueError("action is not permitted in this method/state")
                    if action == "replace_project":
                        if candidate and candidate_sha256(proposal["files"]) == candidate["candidate_sha256"]:
                            raise ValueError("replacement makes no byte change")
                        return {"ok": True, "candidate": self._admit(proposal["files"],
                            parent=candidate["candidate_sha256"] if candidate else None), "action": action}
                    if action == "replace_project_files":
                        files = apply_project_patch(candidate["files"], proposal)
                        return {"ok": True, "candidate": self._admit(files, parent=candidate["candidate_sha256"]), "action": action}
                    if action == "replace_design":
                        if state["pc"] is not None and proposal["design"] == state["pc"]["design"]:
                            raise ValueError("design proposal makes no semantic byte change")
                        checked = self._check_pc(canonical_json_bytes(proposal["design"]).decode())
                        if not checked["ok"]:
                            return {**checked, "pc": None, "build": None, "bundle": None}
                        build = self._build(checked["pc"])
                        return {"ok": True, "pc": checked["pc"], "build": asdict(build), "bundle": None, "action": action}
                    build = StructureBuild(**state["build"])
                    expected_parent = candidate["candidate_sha256"] if candidate else None
                    if proposal["base_candidate_sha256"] != expected_parent or proposal["build_plan_sha256"] != build.build_plan_sha256:
                        raise ValueError("behavior patch parent or plan mismatch")
                    if not set(proposal["units"]) <= set(build.units):
                        raise ValueError("behavior patch contains an unknown unit")
                    bundle = copy.deepcopy(state["bundle"])
                    if bundle is None:
                        bundle = {"contract_version": "pc21-behavior-bundle-v1", "build_plan_sha256": build.build_plan_sha256, "units": {}}
                    bundle["units"].update(proposal["units"])
                    if bundle == state["bundle"]:
                        raise ValueError("behavior patch makes no byte change")
                    composed = self._compose(build, bundle)
                    return {"ok": True, "pc": state["pc"], "build": asdict(build), "bundle": bundle,
                            "candidate": self._admit(composed["files"], pc=state["pc"], build=build, bundle=bundle,
                                construction_origin_map=composed["construction_origin_map"], parent=expected_parent), "action": action}
                except ValueError as error:
                    return {"ok": False, "reason": "repair_proposal_rejected", "diagnostic": self._diagnostic(error), "previous_output": response["text"]}
            try:
                update = self._cached(operation, (method,), execute)
            except BudgetError as error:
                state["feedback"] = {"reason": "resource_budget_exhausted", "diagnostic": str(error)}
                break
            state["infrastructure"] = update.get("infrastructure", False)
            state["resource_exhausted"] = update.get("resource_exhausted", False)
            for key in ("pc", "build", "bundle"):
                if key in update:
                    state[key] = update[key]
            state["feedback"] = {k: v for k, v in update.items() if k in {"reason", "diagnostic", "previous_output"}}
            if update.get("candidate") is not None:
                old = state["last_candidate"]
                state["last_candidate"] = update["candidate"]
                state["evaluation"] = self._evaluate(update["candidate"], (method,), operation + "/public")
                state["feedback"] = state["evaluation"].get("public", state["feedback"])
                state["infrastructure"] = state["evaluation"].get("outcome", {}).get("execution_status") == "infrastructure_error"
                state["resource_exhausted"] = state["evaluation"].get("resource_exhausted", False)
                state["repairs"].append({"operation": operation, "action": update.get("action", "replace_behavior_units"),
                    "parent_candidate_sha256": old["candidate_sha256"] if old else None,
                    "candidate_sha256": update["candidate"]["candidate_sha256"],
                    "public_rechecked": state["evaluation"].get("ok", False)})
            self._event("repair_observed", method=method, operation=operation, ok=update.get("ok", False),
                        candidate_sha256=state["last_candidate"]["candidate_sha256"] if state["last_candidate"] else None)
            self.store.append_event("pc21-checkpoint-" + method, "repair_checkpoint", {"ordinal": ordinal, "state": state})
            if not update.get("ok") and self.ledger.remaining(method, "model_calls") == calls_before and not recoverable:
                break

    def generate(self) -> dict[str, Any]:
        with file_lock(self.root / "generation.lock"):
            return self._generate_locked()

    def _generate_locked(self) -> dict[str, Any]:
        self._source_guard()
        sealed = self.store.reference("generation-closed")
        if sealed is not None:
            return json.loads(self.store.read_verified(sealed))
        states: dict[str, dict[str, Any]] = {}
        rng = random.Random(self.schedule_seed)
        order = ["SD", "SC", "UP"]
        rng.shuffle(order)
        for node in order:
            if node == "SD":
                initial = self._project_node("initial-SD", "direct_project", ("M0", "M1"), {})
                for method in ("M0", "M1"):
                    states[method] = self._state(initial)
                if initial.get("candidate"):
                    evaluated = self._evaluate(initial["candidate"], ("M0", "M1"), "initial-SD/public")
                    for method in ("M0", "M1"):
                        states[method]["evaluation"] = copy.deepcopy(evaluated)
                        states[method]["feedback"] = evaluated.get("public", {})
                        states[method]["infrastructure"] = evaluated.get("outcome", {}).get("execution_status") == "infrastructure_error"
                        states[method]["resource_exhausted"] = evaluated.get("resource_exhausted", False)
            elif node == "UP":
                plan = self._cached("initial-UP", ("M2",), lambda: self._call("initial-UP", "untyped_plan", ("M2",), {},
                    "Return a concise untyped implementation plan as plain text. Do not use a Project Contract or emit RTL yet."))
                initial = self._project_node("initial-M2", "project_from_plan", ("M2",), {"untyped_plan": plan["text"]}) if plan["ok"] else plan
                states["M2"] = self._state(initial)
                if initial.get("candidate"):
                    states["M2"]["evaluation"] = self._evaluate(initial["candidate"], ("M2",), "initial-M2/public")
            else:
                def plan_pc():
                    proposed = self._call("initial-SC", "pc_plan", ("M3", "M4", "M5"),
                        {"design_schema": ContractRegistry().load_schema("design_proposal_2_1").document}, DESIGN_FORMAT)
                    return self._check_pc(proposed["text"]) if proposed["ok"] else proposed
                planned = self._cached("initial-SC", ("M3", "M4", "M5"), plan_pc)
                branches = ["M3", "SB"]
                rng.shuffle(branches)
                for branch in branches:
                    consumers = ("M3",) if branch == "M3" else ("M4", "M5")
                    if not planned["ok"]:
                        initial = planned
                    elif branch == "M3":
                        initial = self._project_node("initial-M3", "project_from_pc", consumers, {"pc": planned["pc"]})
                    else:
                        initial = self._body_node("initial-SB", consumers, planned["pc"])
                    for method in consumers:
                        states[method] = self._state(initial)
                        if planned["ok"]:
                            states[method]["pc"] = planned["pc"]
                    if initial.get("candidate"):
                        evaluated = self._evaluate(initial["candidate"], consumers, "initial-" + branch + "/public")
                        for method in consumers:
                            states[method]["evaluation"] = copy.deepcopy(evaluated)
                            states[method]["feedback"] = evaluated.get("public", {})
                            states[method]["infrastructure"] = evaluated.get("outcome", {}).get("execution_status") == "infrastructure_error"
                            states[method]["resource_exhausted"] = evaluated.get("resource_exhausted", False)
        for method in ("M1", "M5"):
            self._repair(method, states[method])
        terminals = {}
        for method in METHODS:
            state = states[method]
            terminals[method] = {"candidate": state["last_candidate"], "public_evaluation": state["evaluation"],
                "infrastructure": state["infrastructure"], "reason": state["feedback"], "repairs": state["repairs"]}
        result = {"runtime_version": "pc21-m0-m5-development-v1", "official": False,
                  "identity": asdict(self.identity), "source_class": self.gateway.transport.source_class,
                  "terminals": terminals, "budget": self.ledger.snapshot(), "schedule": order}
        self.store.put_blob("generation-closed", canonical_json_bytes(result), media_type="application/json")
        return json.loads(canonical_json_bytes(result))


def finalize_batch(blocks: Sequence[PairedBlockRuntime], *, private_root: Path,
                   private_suites: Mapping[str, TrustedSuite]) -> dict[str, Any]:
    """Seal every planned slot before running any terminal-private suite.

    No model gateway is handed to the authority or hidden evaluator. This helper
    is for explicitly labelled development suites, not official held-out data.
    """
    if not blocks or len({block.identity.campaign_id for block in blocks}) != 1:
        raise ValueError("a finalization batch needs one nonempty campaign")
    private_root = Path(private_root).resolve()
    for block in blocks:
        if (private_root == block.root or private_root.is_relative_to(block.root)
                or block.root.is_relative_to(private_root)):
            raise ValueError("terminal authority must be disjoint from every candidate/control root")
        if block.final_limits is None or set(block.final_limits) != set(METHODS):
            raise ValueError("terminal evaluation requires an explicit separate six-method tool budget")
        for other in blocks:
            if (block.private_root == other.root or block.private_root.is_relative_to(other.root)
                    or other.root.is_relative_to(block.private_root)):
                raise ValueError("every private worker root must be disjoint from every control root")
    generated = [block.generate() for block in blocks]
    planned = [block.identity.slot(method) for block in blocks for method in METHODS]
    authority = TerminalEvaluationAuthority(private_root, planned_slots=planned)
    workers = {}
    terminal_ledgers = {}
    for block, generation in zip(blocks, generated):
        final_ledger = BudgetLedger(ArtifactStore(block.private_root / "terminal-accounting"),
                                   "terminal-" + _sha(asdict(block.identity)), block.final_limits)
        terminal_ledgers[id(block)] = final_ledger
        for method in METHODS:
            suite = private_suites[block.case]
            if (suite.commitment_sha256 == block.public_suite.commitment_sha256
                    or suite.testbench_sha256 == block.public_suite.testbench_sha256):
                raise ValueError("terminal-private replay must have its own frozen suite identity")
            counter = [0]
            def final_tool_budget(stage, limits, execute, *, consumer=method, budget=final_ledger, index=counter,
                                  block_key=_sha(asdict(block.identity))):
                index[0] += 1
                axis = "hidden_tool_calls" if stage.startswith("hidden_") else "final_public_tool_calls"
                reservation = budget.reserve(block_key + "/" + consumer + f"/{index[0]:03d}-" + stage,
                    (consumer,), **{axis: 1}, active_seconds=limits.timeout_seconds,
                    eda_seconds=limits.timeout_seconds, cpu_seconds=limits.cpu_seconds, memory_bytes=limits.memory_bytes,
                    metadata={"visibility_class": "evaluator_private" if axis == "hidden_tool_calls" else "control_only"})
                budget.dispatch(reservation.reservation_id)
                try:
                    result = execute()
                except Exception:
                    budget.reconcile(reservation.reservation_id, observed={"active_seconds": None, "eda_seconds": None,
                        "cpu_seconds": None, "memory_bytes": None}, outcome="unknown")
                    raise
                budget.reconcile(reservation.reservation_id, observed={"active_seconds": result.duration_seconds,
                    "eda_seconds": result.duration_seconds, "cpu_seconds": None, "memory_bytes": None},
                    outcome="completed" if result.status == "passed" else "failed")
                return result
            evaluator = block.evaluator_factory(block.case, block.task, block.private_root / "terminal-private",
                backend=block.backend, synthesize=True, suite=suite, limits=block.tool_limits, tool_budget=final_tool_budget)
            public_worker = block.evaluator_factory(block.case, block.task, block.private_root / "terminal-public",
                backend=block.backend, synthesize=True, suite=block.public_suite, limits=block.tool_limits,
                tool_budget=final_tool_budget)
            slot = block.identity.slot(method)
            terminal = generation["terminals"][method]
            candidate = terminal["candidate"]
            authority.seal_terminal(slot, files=candidate["files"] if candidate else None,
                task_sha256=task_identity(block.task), suite_sha256=suite.commitment_sha256,
                tool_policy_sha256=evaluator.tool_policy_sha256, reason="no_complete_candidate" if candidate is None else None)
            workers[(id(block), method)] = (evaluator, public_worker)
    barrier = authority.close_barrier()
    records = []
    for block, generation in zip(blocks, generated):
        for method in METHODS:
            slot = block.identity.slot(method)
            terminal = generation["terminals"][method]
            public = terminal["public_evaluation"]
            evaluator, public_worker = workers[(id(block), method)]
            candidate = terminal["candidate"]
            final_public_store = ArtifactStore(block.private_root / "final-public-store")
            final_public_key = "public/" + authority._key(slot)
            saved = final_public_store.reference(final_public_key)
            if saved is not None:
                final_public = EvaluationResult(**json.loads(final_public_store.read_verified(saved)))
                expected = (candidate["candidate_sha256"], task_identity(block.task), block.public_suite.commitment_sha256,
                            public_worker.tool_policy_sha256)
                actual = (final_public.candidate_sha256, final_public.task_sha256, final_public.suite_sha256,
                          final_public.tool_policy_sha256)
                if final_public.visibility != "public" or actual != expected:
                    raise RuntimeIntegrityError("final public evidence does not bind the sealed candidate/context")
                public = {"public": final_public.public_feedback(), "outcome": final_public.to_dict()}
            elif candidate is not None and (public is None or not public.get("ok", False)
                                          or public.get("outcome", {}).get("execution_status") == "infrastructure_error"):
                try:
                    final_public = public_worker.evaluate(copy.deepcopy(candidate["files"]),
                        evaluation_id="final-public-" + authority._key(slot), visibility="public")
                except BudgetError:
                    final_public = EvaluationResult(candidate["candidate_sha256"], task_identity(block.task),
                        block.public_suite.commitment_sha256, public_worker.tool_policy_sha256, "public",
                        "infrastructure_error", None, {level: "not_run" for level in ("l0", "l1", "l2", "l3")},
                        isolation_qualified=block.backend.isolation_qualified)
                final_public_store.put_blob(final_public_key, canonical_json_bytes(final_public.to_dict(include_private=True)),
                                            media_type="application/json")
                public = {"public": final_public.public_feedback(), "outcome": final_public.to_dict()}
            if public is not None and public.get("outcome", {}).get("execution_status") == "integrity_error":
                raise RuntimeIntegrityError("final public check reported an integrity violation")
            accepted = public is not None and public.get("public", {}).get("accepted", False)
            if terminal["candidate"] is not None and not accepted:
                authority.close_without_execution(slot, reason="public_prerequisite_not_passed")
            else:
                def execute_hidden(files, worker=evaluator, key=authority._key(slot), owner=block):
                    try:
                        return worker.evaluate(files, evaluation_id="hidden-" + key, visibility="hidden")
                    except BudgetError:
                        return EvaluationResult(candidate_sha256(files), task_identity(owner.task), worker.suite.commitment_sha256,
                            worker.tool_policy_sha256, "hidden", "infrastructure_error", None,
                            {level: "not_run" for level in ("l0", "l1", "l2", "l3")},
                            isolation_qualified=owner.backend.isolation_qualified)
                authority.evaluate_once(slot, execute_hidden)
            hidden = authority.analysis_result(slot)
            if hidden["hidden_execution_status"] == "integrity_error":
                raise RuntimeIntegrityError("terminal worker reported an integrity violation; affected results are invalid")
            value = terminal_value(terminal, public, hidden)
            statuses = {generation["budget"]["methods"][method]["status"],
                        terminal_ledgers[id(block)].snapshot()["methods"][method]["status"]}
            budget_status = "exceeded" if "exceeded" in statuses else "unverifiable" if "unverifiable" in statuses else "compliant"
            records.append({"slot": slot, "identity": asdict(block.identity),
                "candidate_sha256": candidate["candidate_sha256"] if candidate else None,
                "task_sha256": task_identity(block.task), "suite_sha256": private_suites[block.case].commitment_sha256,
                "method_condition": method, "endpoint": "B4" if method in {"M1", "M5"} else "initial",
                "value": value, "outcome_class": "design_outcome" if value is not None else "infrastructure_unscorable",
                "budget_status": budget_status,
                "integrity_status": "intact" if block.backend.isolation_qualified else "unverifiable",
                "reason": hidden.get("reason", "terminal_evaluated"), "official": False})
    return {"official": False, "barrier": barrier, "records": records,
            "terminal_costs": {str(index): terminal_ledgers[id(block)].snapshot() for index, block in enumerate(blocks)}}
