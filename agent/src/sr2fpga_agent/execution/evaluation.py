"""PC-neutral public evaluation and durable, evaluator-private terminal slots.

All cases use their existing independent oracle/harness mathematics. Model
feedback is an explicit projection; hidden outcomes cannot enter repair.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import hashlib
from importlib import import_module
import json
from pathlib import Path
import re
from typing import Any, Callable

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.models import GeneratedProject, ToolResult, canonical_json_bytes
from sr2fpga_agent.parsers import check_project_package_l0, resolve_project_manifest
from sr2fpga_agent.pc.expressions import evaluate
from sr2fpga_agent.pc.inputs import ParseLimits, _parse
from sr2fpga_agent.path_safety import validate_project_relative_path

from .isolation import (
    CandidateBoundaryError, IsolationUnavailable, LocalDevelopmentBackend,
    ToolLimits, candidate_sha256, validate_candidate_sources,
)
from .public_feedback import (
    FEEDBACK_REVISION, functional_diagnostics, source_diagnostics, validate_diagnostics,
)


_CASES = {"qkv": "llm_qkv", "attention": "llm_attention", "ffn": "llm_ffn"}
_SLOT_FIELDS = ("campaign_id", "population_id", "semantic_instance_id", "replicate_id", "condition_id")
_DIAGNOSTICS = {"candidate_boundary", "l0_invalid", "abi_mismatch", "parser_rejected",
                "compile_rejected", "functional_mismatch", "synthesis_rejected",
                "tool_unavailable", "tool_timeout", "tool_crash", "tool_protocol_error", "isolation_unavailable",
                "trusted_context_changed"}


def _sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def task_identity(task: Any) -> str:
    return _sha(task.sources.bindings())


class EvaluationIntegrityError(RuntimeError):
    pass


def _verify_public_task(task: Any) -> None:
    for name, projection in (("requirements", task.requirements), ("target_profile", task.target),
                             ("capability_profile", task.capability)):
        source = getattr(task.sources, name)
        if _parse(source.content, ParseLimits(max(1, len(source.content)), 128)) != projection:
            raise EvaluationIntegrityError("public projection differs from its frozen original bytes")
    assets = task.requirements["public_assets"]
    if set(task.asset_bytes) != {asset["id"] for asset in assets}:
        raise EvaluationIntegrityError("public asset identities changed")
    for asset in assets:
        content = task.asset_bytes[asset["id"]]
        if len(content) != asset["size_bytes"] or hashlib.sha256(content).hexdigest() != asset["sha256"]:
            raise EvaluationIntegrityError("public asset bytes changed")


def assert_supported_case(case: str, task: Any) -> None:
    """Bind the fixed trusted oracle to the public meaning it actually implements.

    A valid new requirement document is not automatically supported by an old
    fixed-shape oracle. Provenance/paths may vary; mathematical facts may not.
    """
    if case not in _CASES:
        raise ValueError("unknown evaluator case")
    _verify_public_task(task)
    factory = import_module("sr2fpga_agent.tasks." + _CASES[case] + ".task").build_development_task()
    requirements = task.requirements
    expected_facts = factory["facts"]
    actual_facts = {record["fact_id"]: {name: record[name] for name in ("value", "role", "required_mapping")}
                    for record in requirements["fact_records"]}
    if (requirements["requirement_id"] != factory["task_id"]
            or requirements["public_text"] != factory["public_text"]
            or task.boundary != factory["boundary"]["boundary"]
            or actual_facts != expected_facts
            or task.asset_bytes != factory["public_assets"]
            or task.target["clock_period_ns"] != factory["target_profile"]["clock_period_ns"]
            or task.target["max_simulation_cycles"] != factory["target_profile"]["max_simulation_cycles"]):
        raise ValueError("unsupported public task profile for the fixed trusted case oracle")


@dataclass(frozen=True)
class TrustedSuite:
    suite_id: str
    testbench_top: str
    render: Callable[[], str] = field(repr=False, compare=False)
    check: Callable[[str], Any] = field(repr=False, compare=False)
    commitment_sha256: str
    testbench_sha256: str | None = None
    source_sha256: tuple[tuple[str, str], ...] = field(default=(), repr=False)
    _frozen_testbench: str = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", self.commitment_sha256):
            raise ValueError("trusted suite requires a SHA256 policy commitment")
        rendered = self.render()
        if not isinstance(rendered, str):
            raise ValueError("trusted suite must render text")
        testbench_sha = hashlib.sha256(rendered.encode()).hexdigest()
        if self.testbench_sha256 is not None and testbench_sha != self.testbench_sha256:
            raise EvaluationIntegrityError("trusted suite rendering changed during commitment")
        object.__setattr__(self, "testbench_sha256", testbench_sha)
        object.__setattr__(self, "_frozen_testbench", rendered)
        source_identity = [(Path(path).name, digest) for path, digest in self.source_sha256]
        object.__setattr__(self, "commitment_sha256", _sha({
            "declared_policy": self.commitment_sha256, "suite_id": self.suite_id,
            "testbench_top": self.testbench_top, "testbench_sha256": testbench_sha,
            "sources": source_identity,
        }))
        self.verify()

    def verify(self) -> None:
        rendered = self.render()
        if not isinstance(rendered, str) or hashlib.sha256(rendered.encode()).hexdigest() != self.testbench_sha256:
            raise EvaluationIntegrityError("trusted testbench changed after suite commitment")
        for path, expected in self.source_sha256:
            try:
                actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            except OSError:
                raise EvaluationIntegrityError("trusted suite dependency is unavailable") from None
            if actual != expected:
                raise EvaluationIntegrityError("trusted suite dependency changed")

    @classmethod
    def for_development_case(cls, case: str) -> "TrustedSuite":
        if case not in _CASES:
            raise ValueError("unknown evaluator case")
        module = import_module("sr2fpga_agent.tasks." + _CASES[case] + ".harness")
        case_root = Path(module.__file__).parent
        dependencies = tuple((str(path.resolve()), hashlib.sha256(path.read_bytes()).hexdigest())
                             for path in sorted(case_root.glob("*.py")))
        commitment = _sha({"suite": case + "-public-development-v1", "version": "pc21-case-suite-v1"})
        return cls(case + "-public-development-v1", module.TESTBENCH_TOP,
                   module.render_testbench, module.check_trace, commitment,
                   source_sha256=dependencies)


@dataclass(frozen=True)
class EvaluationResult:
    candidate_sha256: str
    task_sha256: str
    suite_sha256: str
    tool_policy_sha256: str
    visibility: str
    execution_status: str
    semantic_status: str | None
    stages: dict[str, str]
    diagnostic_codes: tuple[str, ...] = ()
    isolation_qualified: bool = False
    private_record_ref: dict[str, Any] | None = field(default=None, repr=False)
    public_diagnostics: tuple[dict[str, Any], ...] = field(default=(), repr=False)

    def __post_init__(self) -> None:
        if self.visibility not in {"public", "hidden"}:
            raise ValueError("invalid result visibility")
        if self.execution_status not in {"completed", "infrastructure_error", "integrity_error"}:
            raise ValueError("invalid execution status")
        if self.semantic_status not in {"pass", "fail", None}:
            raise ValueError("invalid semantic status")
        if self.execution_status != "completed" and self.semantic_status is not None:
            raise ValueError("uncompleted execution cannot carry a semantic result")
        if set(self.stages) != {"l0", "l1", "l2", "l3"} or any(
                value not in {"pass", "fail", "not_run"} for value in self.stages.values()):
            raise ValueError("invalid evaluation stage status")
        if self.semantic_status == "pass" and any(value != "pass" for value in self.stages.values()):
            raise ValueError("pass requires every common evaluation stage")
        if not set(self.diagnostic_codes) <= _DIAGNOSTICS:
            raise ValueError("unknown model-visible diagnostic code")
        object.__setattr__(self, "public_diagnostics", validate_diagnostics(self.public_diagnostics))

    @property
    def accepted(self) -> bool:
        return self.execution_status == "completed" and self.semantic_status == "pass"

    def public_feedback(self) -> dict[str, Any]:
        if self.visibility != "public":
            raise PermissionError("hidden results cannot become model feedback")
        from sr2fpga_agent.contract_registry import ContractRegistry
        result = {"contract_version": "pc21-public-feedback-v2", "feedback_revision": FEEDBACK_REVISION,
                "accepted": self.accepted, "stages": dict(self.stages),
                "diagnostic_codes": list(self.diagnostic_codes),
                "isolation_qualified": self.isolation_qualified,
                "diagnostics": list(validate_diagnostics(self.public_diagnostics))}
        errors = ContractRegistry().load_schema("pc21_public_feedback_v2").validate(result)
        if errors:
            raise ValueError("public feedback does not conform to its registered contract")
        return result

    def to_dict(self, *, include_private: bool = False) -> dict[str, Any]:
        if self.visibility == "hidden" and not include_private:
            return {"candidate_sha256": self.candidate_sha256, "task_sha256": self.task_sha256,
                    "suite_sha256": self.suite_sha256, "tool_policy_sha256": self.tool_policy_sha256,
                    "visibility": "hidden", "generation_visible": False, "repair_visible": False}
        value = asdict(self)
        if not include_private:
            value.pop("private_record_ref", None)
        return value


def _type_width(value: dict[str, Any], parameters: dict[str, int], tensors: dict[str, Any]) -> int:
    kind = value["kind"]
    if kind == "record":
        return sum(_type_width(item["type"], parameters, tensors) for item in value["fields"])
    if kind == "tensor_beat":
        descriptor = tensors[value["contract"]]
        lanes = evaluate(descriptor["layout"]["lanes"], parameters)
        return lanes * descriptor["element"]["width"] + (lanes if descriptor["layout"]["tail"] == "zero_pad_mask" else 0)
    return evaluate(value["width"], parameters)


def expected_public_abi(task: Any) -> tuple[str, dict[str, tuple[str, int]]]:
    """Derive the requirement-owned ABI without invoking a candidate PC emitter."""
    boundary = task.boundary
    signature = boundary["signature"]
    result: dict[str, tuple[str, int]] = {}
    for mapping in boundary["abi"]["domains"].values():
        for name in mapping.values():
            if name is not None:
                if name in result:
                    raise ValueError("public physical ABI collision")
                result[name] = ("input", 1)
    for logical, port in signature["ports"].items():
        mapping = boundary["abi"]["ports"][logical]
        payload = port["payload"] if port["kind"] == "stream" else port["type"]
        width = _type_width(payload, boundary["parameter_values"], signature.get("tensor_contracts", {}))
        for role, name in mapping.items():
            if name in result:
                raise ValueError("public physical ABI collision")
            direction = port["direction"]
            if role == "ready":
                direction = "output" if direction == "input" else "input"
            result[name] = (direction, width if role in {"payload", "signal"} else 1)
    top = boundary["rtl_top"]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", top):
        raise ValueError("unsupported public RTL top")
    return top, result


class Pc21Evaluator:
    """Trusted, method-neutral worker over one exact candidate file map."""

    def __init__(self, case: str, public_task: Any, evaluator_root: Path, *, backend=None,
                 tool_budget: Callable[[str, ToolLimits, Callable[[], ToolResult]], ToolResult] | None = None,
                 synthesize: bool = True, suite: TrustedSuite | None = None,
                 limits: ToolLimits | None = None):
        if case not in _CASES:
            raise ValueError("unknown evaluator case")
        assert_supported_case(case, public_task)
        self.case, self.task = case, public_task
        self.root = Path(evaluator_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = ArtifactStore(self.root / "private-store")
        self.backend = backend or LocalDevelopmentBackend()
        self.tool_budget, self.synthesize = tool_budget, synthesize
        self.suite = suite or TrustedSuite.for_development_case(case)
        self.limits = limits or ToolLimits(timeout_seconds=public_task.target["tool_timeout_seconds"])
        _verify_public_task(self.task)
        self._task_sha256 = task_identity(self.task)
        self.tool_policy_sha256 = self._tool_policy_identity()

    def _tool_policy_identity(self) -> str:
        return _sha({"backend": self.backend.policy(), "limits": asdict(self.limits),
                     "synthesize": self.synthesize, "candidate_policy": "restricted-model-rtl-v1",
                     "feedback_revision": FEEDBACK_REVISION})

    def _run(self, command: list[str], work: Path, stage: str, visibility: str,
             candidate_files: dict[str, str]) -> ToolResult:
        _verify_public_task(self.task)
        self.suite.verify()
        if self._tool_policy_identity() != self.tool_policy_sha256 or task_identity(self.task) != self._task_sha256:
            raise EvaluationIntegrityError("task or tool execution policy changed after worker creation")
        def execute():
            return self.backend.run(command, work, stage, self.limits)
        def verify_candidate():
            for path, expected in candidate_files.items():
                target = work / path
                if target.is_symlink() or not target.is_file() or target.read_bytes() != expected.encode("utf-8"):
                    raise EvaluationIntegrityError("candidate bytes changed inside the evaluator worker")
        verify_candidate()
        result = (self.tool_budget(visibility + "_" + stage, self.limits, execute)
                  if self.tool_budget is not None else execute())
        verify_candidate()
        return result

    def evaluate(self, files: dict[str, str], *, evaluation_id: str,
                 visibility: str = "public") -> EvaluationResult:
        if visibility not in {"public", "hidden"} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", evaluation_id):
            raise ValueError("invalid evaluator scope or identity")
        files = json.loads(canonical_json_bytes(files))
        digest = candidate_sha256(files)
        # Keep logical identities complete in the store; tool frontends on
        # Windows may reject a valid existing file once its path exceeds MAX_PATH.
        work = self.root / ("w-" + hashlib.sha256(evaluation_id.encode("utf-8")).hexdigest()[:16])
        work.mkdir(exist_ok=False)
        stages = {name: "not_run" for name in ("l0", "l1", "l2", "l3")}
        diagnostics: list[str] = []
        public_diagnostics: list[dict[str, Any]] = []
        private: dict[str, Any] = {"evaluation_id": evaluation_id, "candidate_sha256": digest,
                                   "visibility": visibility, "tools": []}
        execution, semantic = "completed", "fail"
        phase = "l0"
        try:
            _verify_public_task(self.task)
            self.suite.verify()
            if self._tool_policy_identity() != self.tool_policy_sha256 or task_identity(self.task) != self._task_sha256:
                raise EvaluationIntegrityError("task or tool execution policy changed")
            validate_candidate_sources(files)
            manifest = resolve_project_manifest(files)
            if manifest.is_legacy:
                raise CandidateBoundaryError("canonical FPP is required")
            l0 = check_project_package_l0(GeneratedProject(manifest.project_name, files))
            if not l0.passed:
                diagnostics.append("l0_invalid")
                raise CandidateBoundaryError("candidate common package validation failed")
            top, ports = expected_public_abi(self.task)
            actual = {port.name: port.direction for port in manifest.top_ports or ()}
            if manifest.top_module != top or actual != {name: item[0] for name, item in ports.items()}:
                diagnostics.append("abi_mismatch")
                raise CandidateBoundaryError("candidate violates requirement-owned ABI")
            if any(language not in {"verilog", "systemverilog"} for language in manifest.source_languages.values()):
                raise CandidateBoundaryError("unsupported source language")
            stages["l0"] = "pass"
            for path, text in files.items():
                validate_project_relative_path(path)
                target = work / path
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(text)
            # Real candidate-only frontend prevents dependencies on trusted TB internals.
            phase = "l1"
            parser_script = ("read_verilog -sv -noautowire " + " ".join(manifest.sources)
                             + "; hierarchy -check -top " + top + "; proc; check -assert; write_json candidate.json")
            commands = [("l1", "parser", ["yosys", "-Q", "-T", "-p", parser_script])]
            for level, stage, command in commands:
                result = self._run(command, work, stage, visibility, files)
                private["tools"].append(asdict(result))
                if visibility == "public":
                    public_diagnostics.extend(source_diagnostics(result, candidate_files=files,
                                              declared_sources=manifest.sources, work=work))
                self._require_tool(result, diagnostics, "parser_rejected")
                try:
                    parsed = json.loads((work / "candidate.json").read_text(encoding="utf-8"))
                    physical_ports = parsed["modules"][top]["ports"]
                    observed = {name: (port["direction"], len(port["bits"])) for name, port in physical_ports.items()}
                except (OSError, ValueError, KeyError, TypeError):
                    diagnostics.append("tool_protocol_error")
                    raise _ToolInfrastructureError() from None
                if observed != ports:
                    diagnostics.append("abi_mismatch")
                    raise CandidateBoundaryError("real parser found a requirement ABI mismatch")
                stages[level] = "pass"
            testbench = self.suite._frozen_testbench
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.suite.testbench_top):
                raise ValueError("invalid trusted suite top")
            (work / "trusted_testbench.sv").write_text(testbench, encoding="utf-8")
            phase = "l2"
            for stage, command in [
                ("compile", ["iverilog", "-v", "-g2012", "-s", self.suite.testbench_top,
                             "-o", "simulation.vvp", *manifest.sources, "trusted_testbench.sv"]),
                ("simulate", ["vvp", "simulation.vvp"]),
            ]:
                result = self._run(command, work, stage, visibility, files)
                private["tools"].append(asdict(result))
                if visibility == "public" and stage == "compile":
                    public_diagnostics.extend(source_diagnostics(result, candidate_files=files,
                                              declared_sources=manifest.sources, work=work))
                self._require_tool(result, diagnostics, "compile_rejected" if stage == "compile" else "functional_mismatch")
            try:
                trace = self.suite.check(result.stdout)
            except ValueError as error:
                diagnostics.append("functional_mismatch")
                if visibility == "public":
                    public_diagnostics.extend(functional_diagnostics(error))
                raise CandidateBoundaryError("independent transaction checker rejected output") from None
            private["trace"] = asdict(trace) if hasattr(trace, "__dataclass_fields__") else trace
            stages["l2"] = "pass"
            if self.synthesize:
                phase = "l3"
                script = "read_verilog -sv " + " ".join(manifest.sources) + "; synth -top " + top + "; stat"
                result = self._run(["yosys", "-Q", "-T", "-p", script], work, "synthesize", visibility, files)
                private["tools"].append(asdict(result))
                self._require_tool(result, diagnostics, "synthesis_rejected")
                stages["l3"] = "pass"
            else:
                stages["l3"] = "not_run"
            semantic = "pass" if self.synthesize else None
        except IsolationUnavailable:
            execution, semantic = "infrastructure_error", None
            diagnostics.append("isolation_unavailable")
        except EvaluationIntegrityError:
            execution, semantic = "integrity_error", None
            diagnostics.append("trusted_context_changed")
        except _ToolInfrastructureError:
            execution, semantic = "infrastructure_error", None
        except (CandidateBoundaryError, ValueError) as error:
            if not diagnostics:
                diagnostics.append("candidate_boundary" if phase == "l0" else "functional_mismatch")
            private["rejection"] = str(error)
        except OSError as error:
            execution, semantic = "infrastructure_error", None
            private["infrastructure_error"] = type(error).__name__
            diagnostics.append("tool_unavailable")
        if stages[phase] == "not_run" and execution == "completed":
            stages[phase] = "fail"
        assert set(diagnostics) <= _DIAGNOSTICS
        private.update(execution_status=execution, semantic_status=semantic, stages=stages,
                       diagnostic_codes=list(dict.fromkeys(diagnostics)))
        ref = self.store.put_blob("records/" + evaluation_id, canonical_json_bytes(private), media_type="application/json")
        self.store.append_event("evaluation", "candidate_evaluated", {
            "candidate_sha256": digest, "scope": visibility, "private_record_ref": ref.to_dict(),
            "execution_status": execution, "semantic_status": semantic,
        })
        return EvaluationResult(digest, self._task_sha256, self.suite.commitment_sha256,
                                self.tool_policy_sha256, visibility, execution, semantic,
                                stages, tuple(dict.fromkeys(diagnostics)),
                                bool(self.backend.isolation_qualified), ref.to_dict(), tuple(public_diagnostics))

    @staticmethod
    def _require_tool(result: ToolResult, diagnostics: list[str], failure_code: str) -> None:
        if result.status == "passed":
            return
        if result.status == "missing_tool":
            diagnostics.append("tool_unavailable")
            raise _ToolInfrastructureError()
        if result.exit_code in {3221225477, -1073741819, -11}:
            diagnostics.append("tool_crash")
            raise _ToolInfrastructureError()
        diagnostics.append("tool_timeout" if result.status == "timeout" else failure_code)
        raise CandidateBoundaryError("candidate tool stage did not pass")


class _ToolInfrastructureError(RuntimeError):
    pass


class TerminalEvaluationAuthority:
    """Frozen slot bindings, a complete seal barrier and once-only hidden results.

    Analysis reads are distinct from opaque receipts. Crashes after dispatch
    leave an unknown execution state that is not blindly re-dispatched.
    """

    def __init__(self, private_root: Path, *, planned_slots: list[dict[str, Any]],
                 max_infrastructure_retries: int = 0):
        if type(max_infrastructure_retries) is not int or max_infrastructure_retries < 0:
            raise ValueError("invalid infrastructure retry limit")
        self.root = Path(private_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = ArtifactStore(self.root / "store")
        self.slots = {self._key(slot): self._identity(slot) for slot in planned_slots}
        if not self.slots or len(self.slots) != len(planned_slots):
            raise ValueError("terminal plan must contain unique slots")
        self.max_infrastructure_retries = max_infrastructure_retries
        self.store.put_blob("plan", canonical_json_bytes({"slots": self.slots,
                           "max_infrastructure_retries": max_infrastructure_retries}), media_type="application/json")

    @staticmethod
    def _identity(slot: dict[str, Any]) -> dict[str, Any]:
        identity = {name: slot[name] for name in _SLOT_FIELDS}
        if any(isinstance(value, bool) or not isinstance(value, (str, int)) or str(value) == ""
               for value in identity.values()) or identity["condition_id"] not in {f"M{i}" for i in range(6)}:
            raise ValueError("invalid terminal slot identity")
        return identity

    @classmethod
    def _key(cls, slot: dict[str, Any]) -> str:
        return _sha(cls._identity(slot))

    @contextmanager
    def _lock(self):
        from .locking import file_lock
        with file_lock(self.root / "authority.lock"):
            yield

    def seal_terminal(self, slot: dict[str, Any], *, files: dict[str, str] | None,
                      task_sha256: str, suite_sha256: str, tool_policy_sha256: str,
                      reason: str | None = None) -> dict[str, Any]:
        key = self._key(slot)
        if key not in self.slots:
            raise ValueError("unplanned terminal slot")
        for digest in (task_sha256, suite_sha256, tool_policy_sha256):
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("terminal context must contain SHA256 bindings")
        if files is None and not reason:
            raise ValueError("terminal-null requires a reason")
        payload = {"slot": self.slots[key], "candidate_sha256": candidate_sha256(files) if files is not None else None,
                   "files": files, "task_sha256": task_sha256, "suite_sha256": suite_sha256,
                   "tool_policy_sha256": tool_policy_sha256, "reason": reason}
        with self._lock():
            if self.store.reference("barrier") is not None and self.store.reference("seals/" + key) is None:
                raise ValueError("cannot add a terminal after barrier")
            ref = self.store.put_blob("seals/" + key, canonical_json_bytes(payload), media_type="application/json")
        return {"terminal_id": "terminal-" + ref.sha256, "slot_id": key,
                "candidate_sha256": payload["candidate_sha256"]}

    def close_barrier(self) -> dict[str, Any]:
        with self._lock():
            refs = {key: self.store.reference("seals/" + key) for key in self.slots}
            if any(ref is None for ref in refs.values()):
                raise ValueError("all planned slots must be terminal before hidden evaluation")
            payload = {"plan_sha256": self.store.reference("plan").sha256,
                       "seals": {key: ref.sha256 for key, ref in refs.items()}}
            ref = self.store.put_blob("barrier", canonical_json_bytes(payload), media_type="application/json")
        return {"barrier_id": "barrier-" + ref.sha256, "slots": len(refs)}

    def close_without_execution(self, slot: dict[str, Any], *, reason: str) -> dict[str, Any]:
        """Close a fixed terminal with an unmet public prerequisite, retaining it."""
        key = self._key(slot)
        if key not in self.slots or not isinstance(reason, str) or not reason or len(reason) > 256:
            raise ValueError("invalid unexecuted hidden closure")
        with self._lock():
            if self.store.reference("barrier") is None:
                raise PermissionError("hidden closure requires the complete terminal barrier")
            if self.store.reference("outcomes/" + key) is not None:
                previous = json.loads(self.store.read_verified("outcomes/" + key))
                if previous["hidden_execution_status"] != "not_run" or previous.get("reason") != reason:
                    raise ValueError("hidden slot already has a different frozen closure")
                return self._receipt(key)
            if self.store.reference("integrity-stop") is not None:
                raise PermissionError("hidden authority stopped after an integrity violation")
            if self.store.reference(f"dispatch/{key}-0") is not None:
                raise IsolationUnavailable("a dispatched hidden execution cannot be relabeled not_run")
            seal = json.loads(self.store.read_verified("seals/" + key))
            if seal["files"] is not None and candidate_sha256(seal["files"]) != seal["candidate_sha256"]:
                raise ValueError("sealed candidate bytes changed")
            outcome = {"slot": seal["slot"], "candidate_sha256": seal["candidate_sha256"],
                       "hidden_execution_status": "not_run", "hidden_semantic_status": None,
                       "reason": reason, "execution_count": 0, "semantic_commit_count": 0}
            self.store.put_blob("outcomes/" + key, canonical_json_bytes(outcome), media_type="application/json")
            return self._receipt(key)

    def evaluate_once(self, slot: dict[str, Any], evaluator: Callable[[dict[str, str]], EvaluationResult]) -> dict[str, Any]:
        key = self._key(slot)
        if key not in self.slots:
            raise ValueError("unplanned hidden slot")
        with self._lock():
            if self.store.reference("barrier") is None:
                raise PermissionError("hidden evaluation requires the complete terminal barrier")
            if self.store.reference("outcomes/" + key) is not None:
                return self._receipt(key)
            if self.store.reference("integrity-stop") is not None:
                raise PermissionError("hidden authority stopped after an integrity violation")
            seal = json.loads(self.store.read_verified("seals/" + key))
            if seal["files"] is None:
                outcome = {"slot": seal["slot"], "candidate_sha256": None,
                           "hidden_execution_status": "not_run", "hidden_semantic_status": None,
                           "reason": seal["reason"], "execution_count": 0, "semantic_commit_count": 0}
            else:
                if candidate_sha256(seal["files"]) != seal["candidate_sha256"]:
                    raise ValueError("sealed candidate bytes changed")
                history = []
                for ordinal in range(self.max_infrastructure_retries + 1):
                    dispatch_key = f"dispatch/{key}-{ordinal}"
                    if self.store.reference(dispatch_key) is not None:
                        execution_ref = self.store.reference(f"executions/{key}-{ordinal}")
                        if execution_ref is None:
                            raise IsolationUnavailable("hidden dispatch outcome is unknown; automatic replay is forbidden")
                        result = EvaluationResult(**json.loads(self.store.read_verified(execution_ref)))
                    else:
                        self.store.put_blob(dispatch_key, canonical_json_bytes({"candidate_sha256": seal["candidate_sha256"],
                                            "ordinal": ordinal}), media_type="application/json")
                        result = evaluator(json.loads(canonical_json_bytes(seal["files"])))
                    expected = (seal["candidate_sha256"], seal["task_sha256"], seal["suite_sha256"], seal["tool_policy_sha256"])
                    actual = (result.candidate_sha256, result.task_sha256, result.suite_sha256, result.tool_policy_sha256)
                    if actual != expected or result.visibility != "hidden":
                        self.store.put_blob("integrity-stop", canonical_json_bytes({"slot_id": key,
                                            "reason": "hidden_context_binding_changed"}), media_type="application/json")
                        raise ValueError("hidden worker changed a frozen candidate, task, suite or tool context")
                    history.append(result.to_dict(include_private=True))
                    self.store.put_blob(f"executions/{key}-{ordinal}", canonical_json_bytes(history[-1]), media_type="application/json")
                    if result.execution_status == "integrity_error":
                        self.store.put_blob("integrity-stop", canonical_json_bytes({"slot_id": key,
                                            "reason": "worker_reported_integrity_error"}), media_type="application/json")
                    if result.execution_status != "infrastructure_error":
                        break
                outcome = {"slot": seal["slot"], "candidate_sha256": seal["candidate_sha256"],
                           "hidden_execution_status": result.execution_status,
                           "hidden_semantic_status": result.semantic_status,
                           "execution_count": len(history), "semantic_commit_count": int(result.execution_status == "completed"),
                           "executions": history}
                if outcome["semantic_commit_count"]:
                    if result.semantic_status not in {"pass", "fail"}:
                        raise ValueError("completed hidden worker must commit pass or fail")
                    one_shot = self.store.reference("one-shot/hidden-semantic-" + key)
                    if one_shot is None:
                        self.store.consume_once("hidden-semantic-" + key, seal["candidate_sha256"])
                    else:
                        consumed = json.loads(self.store.read_verified(one_shot))
                        if consumed["subject_sha256"] != seal["candidate_sha256"]:
                            raise ValueError("hidden semantic commit changed subject")
            self.store.put_blob("outcomes/" + key, canonical_json_bytes(outcome), media_type="application/json")
            return self._receipt(key)

    def _receipt(self, key: str) -> dict[str, Any]:
        self.analysis_result(self.slots[key])
        ref = self.store.reference("outcomes/" + key)
        return {"opaque_outcome_id": "hidden-" + ref.sha256, "slot_id": key,
                "generation_visible": False, "repair_visible": False, "official": False}

    def analysis_result(self, slot: dict[str, Any]) -> dict[str, Any]:
        if self.store.reference("barrier") is None:
            raise PermissionError("analysis requires the terminal barrier")
        key = self._key(slot)
        if key not in self.slots:
            raise ValueError("unplanned analysis slot")
        barrier = json.loads(self.store.read_verified("barrier"))
        expected_seals = {identity: self.store.reference("seals/" + identity) for identity in self.slots}
        if (barrier["plan_sha256"] != self.store.reference("plan").sha256
                or set(barrier["seals"]) != set(self.slots)
                or any(ref is None or ref.sha256 != barrier["seals"][identity]
                       for identity, ref in expected_seals.items())):
            raise ValueError("terminal barrier and frozen plan/seals disagree")
        seal = json.loads(self.store.read_verified(expected_seals[key]))
        outcome = json.loads(self.store.read_verified("outcomes/" + key))
        if seal["slot"] != self.slots[key] or outcome["slot"] != seal["slot"]:
            raise ValueError("hidden outcome changed planned slot identity")
        if (outcome["candidate_sha256"] != seal["candidate_sha256"]
                or seal["files"] is not None and candidate_sha256(seal["files"]) != seal["candidate_sha256"]):
            raise ValueError("hidden outcome and sealed candidate disagree")
        commit = self.store.reference("one-shot/hidden-semantic-" + key)
        if outcome["hidden_execution_status"] == "not_run":
            if (outcome["execution_count"] != 0 or outcome["semantic_commit_count"] != 0
                    or outcome["hidden_semantic_status"] is not None or commit is not None
                    or self.store.reference(f"dispatch/{key}-0") is not None):
                raise ValueError("unexecuted hidden closure has execution or semantic credit")
            return outcome
        count = outcome["execution_count"]
        if type(count) is not int or not 1 <= count <= self.max_infrastructure_retries + 1:
            raise ValueError("hidden execution count violates the frozen retry limit")
        executions = []
        for ordinal in range(count):
            dispatched = json.loads(self.store.read_verified(f"dispatch/{key}-{ordinal}"))
            if dispatched != {"candidate_sha256": seal["candidate_sha256"], "ordinal": ordinal}:
                raise ValueError("hidden dispatch changed candidate or retry identity")
            record = json.loads(self.store.read_verified(f"executions/{key}-{ordinal}"))
            result = EvaluationResult(**record)
            if (result.visibility != "hidden" or result.candidate_sha256 != seal["candidate_sha256"]
                    or result.task_sha256 != seal["task_sha256"] or result.suite_sha256 != seal["suite_sha256"]
                    or result.tool_policy_sha256 != seal["tool_policy_sha256"]):
                raise ValueError("hidden execution changed frozen context")
            if executions and executions[-1]["execution_status"] != "infrastructure_error":
                raise ValueError("hidden retry followed a semantic or integrity result")
            executions.append(record)
        if (outcome["executions"] != executions or outcome["hidden_execution_status"] != executions[-1]["execution_status"]
                or outcome["hidden_semantic_status"] != executions[-1]["semantic_status"]
                or self.store.reference(f"dispatch/{key}-{count}") is not None):
            raise ValueError("hidden summary does not match its exact execution sequence")
        completed = outcome["hidden_execution_status"] == "completed"
        if outcome["semantic_commit_count"] != int(completed) or (commit is not None) != completed:
            raise ValueError("hidden semantic commit count or receipt disagrees")
        if completed:
            consumed = json.loads(self.store.read_verified(commit))
            if (consumed["operation_id"] != "hidden-semantic-" + key
                    or consumed["subject_sha256"] != seal["candidate_sha256"]):
                raise ValueError("hidden semantic one-shot changed subject")
        elif outcome["hidden_execution_status"] == "infrastructure_error" and count != self.max_infrastructure_retries + 1:
            raise ValueError("hidden infrastructure retry budget was not exhausted")
        return outcome
