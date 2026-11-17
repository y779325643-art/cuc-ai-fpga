"""Method-neutral evaluator, safe feedback and terminal score-slot invariants."""
from dataclasses import replace
import copy
import hashlib
from importlib import import_module
import json
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from sr2fpga_agent.artifact_store import ArtifactConflictError
from sr2fpga_agent.execution.evaluation import (
    EvaluationResult, Pc21Evaluator, TerminalEvaluationAuthority, TrustedSuite,
    assert_supported_case, expected_public_abi,
)
from sr2fpga_agent.execution.isolation import IsolationUnavailable, candidate_sha256
from sr2fpga_agent.models import ToolResult, canonical_json_bytes
from sr2fpga_agent.pc.context import check_task_design, load_public_task
from sr2fpga_agent.pc.emitter import build_structure
from sr2fpga_agent.pc.inputs import ParseLimits, TrustedContext, TrustedSource
from sr2fpga_agent.local_tools import resolve_executable


def task_fixture(tmp_path, case="qkv"):
    package = "sr2fpga_agent.tasks.llm_" + ("attention" if case == "attention" else case)
    module = import_module(package)
    value = module.build_development_task()
    assets = []
    asset_root = tmp_path / "public"
    asset_root.mkdir(parents=True)
    for index, (name, content) in enumerate(value["public_assets"].items()):
        path = f"asset-{index}.json"
        (asset_root / path).write_bytes(content)
        assets.append({"id": name, "path": path, "size_bytes": len(content),
                       "sha256": hashlib.sha256(content).hexdigest()})
    requirements = {"contract_version": "development-public-context-v2", "analysis_population": "development",
                    "requirement_id": value["task_id"], "revision_id": "test-v1", "public_text": value["public_text"],
                    "boundary": value["boundary"]["boundary"], "fact_records": [
                        {"fact_id": key, **fact, "provenance": "system_assumption", "source_ids": ["test"]}
                        for key, fact in value["facts"].items()], "public_assets": assets}
    context = TrustedContext(TrustedSource("requirements", canonical_json_bytes(requirements)),
                             TrustedSource("target", canonical_json_bytes(value["target_profile"])),
                             TrustedSource("capability", canonical_json_bytes(value["capability_profile"])))
    task = load_public_task(context, asset_root=asset_root, limits=ParseLimits(8_000_000, 128))
    checked = check_task_design(module.reference_design(), task)
    build = build_structure(checked, bindings=context.bindings(), toolchain_id=task.target["target_id"])
    bodies = import_module(package + ".reference").reference_behavior_bodies()
    files = dict(build.files)
    for unit in build.units.values():
        files[unit["path"]] = unit["header"] + bodies[unit["module_id"]] + "\nendmodule\n"
    files["manifest.json"] = canonical_json_bytes(build.manifest).decode()
    return task, files


class FakeBackend:
    isolation_qualified = False

    def __init__(self, task, *, fail_stage=None, exit_code=1, wrong_width=False):
        self.task, self.fail_stage, self.exit_code, self.wrong_width = task, fail_stage, exit_code, wrong_width
        self.calls = []

    def policy(self):
        return {"backend": "fake-local-unqualified"}

    def run(self, command, cwd, stage, limits):
        self.calls.append(stage)
        if stage == "parser":
            top, ports = expected_public_abi(self.task)
            parsed = {name: {"direction": direction, "bits": list(range(width + int(self.wrong_width)))}
                      for name, (direction, width) in ports.items()}
            (cwd / "candidate.json").write_text(json.dumps({"modules": {top: {"ports": parsed}}}))
        status = "failed" if stage == self.fail_stage else "passed"
        return ToolResult(stage, command, status, self.exit_code if status == "failed" else 0,
                          "PRIVATE_CANARY_OUTPUT", "PRIVATE_CANARY_PATH", 0.01)


def suite(check=lambda stdout: {"observed": True}):
    return TrustedSuite("synthetic-public-suite", "trusted_tb", lambda: "module trusted_tb;endmodule",
                        check, "b" * 64)


def test_public_evaluator_charges_every_subcall_and_filters_raw_private_material(tmp_path):
    task, files = task_fixture(tmp_path)
    backend = FakeBackend(task)
    charged = []
    def budget(stage, limits, execute):
        charged.append(stage)
        return execute()
    evaluator = Pc21Evaluator("qkv", task, tmp_path / "private", backend=backend,
                               suite=suite(), tool_budget=budget)
    result = evaluator.evaluate(files, evaluation_id="attempt0")
    assert result.accepted
    assert charged == ["public_parser", "public_compile", "public_simulate", "public_synthesize"]
    assert "PRIVATE_CANARY" not in json.dumps(result.public_feedback())
    assert "PRIVATE_CANARY" not in json.dumps(result.to_dict())
    private = json.loads(evaluator.store.read_verified(result.private_record_ref["key"]))
    assert private["tools"][0]["stdout"] == "PRIVATE_CANARY_OUTPUT"
    assert result.isolation_qualified is False


def test_common_evaluation_never_requires_a_pc_file_or_model_testbench(tmp_path):
    task, files = task_fixture(tmp_path)
    assert "pc.json" not in files and not any(path.startswith("sim/") for path in files)
    result = Pc21Evaluator("qkv", task, tmp_path / "private", backend=FakeBackend(task), suite=suite()).evaluate(
        files, evaluation_id="direct")
    assert result.accepted


def test_real_frontend_abi_width_mismatch_stops_before_private_testbench(tmp_path):
    task, files = task_fixture(tmp_path)
    backend = FakeBackend(task, wrong_width=True)
    evaluator = Pc21Evaluator("qkv", task, tmp_path / "private", backend=backend, suite=suite())
    result = evaluator.evaluate(files, evaluation_id="wrongwidth")
    assert not result.accepted and result.stages["l1"] == "fail"
    assert result.diagnostic_codes == ("abi_mismatch",)
    assert backend.calls == ["parser"]
    physical = "w-" + hashlib.sha256(b"wrongwidth").hexdigest()[:16]
    assert not (tmp_path / "private" / physical / "trusted_testbench.sv").exists()


def test_long_logical_evaluation_id_uses_short_fresh_tool_directory_without_losing_identity(tmp_path):
    task, files = task_fixture(tmp_path)
    evaluator = Pc21Evaluator("qkv", task, tmp_path / "private", backend=FakeBackend(task), suite=suite())
    logical = "a" * 64
    result = evaluator.evaluate(files, evaluation_id=logical)
    physical = "w-" + hashlib.sha256(logical.encode()).hexdigest()[:16]
    assert result.accepted
    assert len(physical) == 18 and (tmp_path / "private" / physical).is_dir()
    assert not (tmp_path / "private" / logical).exists()
    assert result.private_record_ref["key"] == "records/" + logical
    raw = json.loads(evaluator.store.read_verified(result.private_record_ref["key"]))
    assert raw["evaluation_id"] == logical
    with pytest.raises(FileExistsError):
        evaluator.evaluate(files, evaluation_id=logical)


def test_source_policy_blocks_candidate_pass_forgery_before_any_tool(tmp_path):
    task, files = task_fixture(tmp_path)
    path = next(name for name in files if name.endswith(".sv"))
    files[path] += '\ninitial $display("TRACE_END 100");\n'
    backend = FakeBackend(task)
    result = Pc21Evaluator("qkv", task, tmp_path / "private", backend=backend, suite=suite()).evaluate(
        files, evaluation_id="forged")
    assert result.semantic_status == "fail"
    assert result.diagnostic_codes == ("candidate_boundary",)
    assert backend.calls == []


def test_changed_frozen_public_projection_is_integrity_error(tmp_path):
    task, files = task_fixture(tmp_path)
    evaluator = Pc21Evaluator("qkv", task, tmp_path / "private", backend=FakeBackend(task), suite=suite())
    task.requirements["public_text"] += "changed"
    result = evaluator.evaluate(files, evaluation_id="changed")
    assert result.execution_status == "integrity_error" and result.semantic_status is None


def test_tool_cannot_change_candidate_bytes_between_compile_and_simulation(tmp_path):
    task, files = task_fixture(tmp_path)
    backend = FakeBackend(task)
    original_run = backend.run
    def changed(command, cwd, stage, limits):
        result = original_run(command, cwd, stage, limits)
        if stage == "compile":
            (cwd / "rtl/top.sv").write_text("module changed;endmodule\n")
        return result
    backend.run = changed
    result = Pc21Evaluator("qkv", task, tmp_path / "private", backend=backend, suite=suite()).evaluate(
        files, evaluation_id="changedbytes")
    assert result.execution_status == "integrity_error" and result.semantic_status is None
    assert backend.calls == ["parser", "compile"]


@pytest.mark.parametrize("damage", ["numeric", "boundary", "identity", "public_text"])
def test_schema_valid_rebound_task_cannot_use_an_incompatible_fixed_oracle(tmp_path, damage):
    task, _ = task_fixture(tmp_path)
    requirements = copy.deepcopy(task.requirements)
    if damage == "numeric":
        fact = next(item for item in requirements["fact_records"] if item["fact_id"] == "numeric")
        fact["value"]["input_zero"] = 7
    elif damage == "boundary":
        requirements["boundary"]["rtl_top"] = "AnotherTop"
    elif damage == "identity":
        requirements["requirement_id"] = "another-valid-id"
    else:
        requirements["public_text"] = "A contradictory but nonempty new requirement"
    context = replace(task.sources, requirements=TrustedSource("new-requirements", canonical_json_bytes(requirements)))
    changed = replace(task, sources=context, requirements=requirements)
    with pytest.raises(ValueError, match="unsupported public task profile"):
        assert_supported_case("qkv", changed)


def test_wrapper_provenance_changes_do_not_change_fixed_oracle_semantics(tmp_path):
    task, _ = task_fixture(tmp_path)
    requirements = copy.deepcopy(task.requirements)
    for fact in requirements["fact_records"]:
        fact["source_ids"] = ["another-public-provenance-id"]
        fact["provenance"] = "user_explicit"
    context = replace(task.sources, requirements=TrustedSource("new-requirements", canonical_json_bytes(requirements)))
    assert_supported_case("qkv", replace(task, sources=context, requirements=requirements))


@pytest.mark.parametrize("exit_code,execution,semantic", [(1, "completed", "fail"),
                                                         (3221225477, "infrastructure_error", None)])
def test_tool_crash_is_distinct_from_a_candidate_compile_failure(tmp_path, exit_code, execution, semantic):
    task, files = task_fixture(tmp_path)
    evaluator = Pc21Evaluator("qkv", task, tmp_path / "private", suite=suite(),
                               backend=FakeBackend(task, fail_stage="compile", exit_code=exit_code))
    result = evaluator.evaluate(files, evaluation_id="compilefailure")
    assert result.execution_status == execution and result.semantic_status == semantic
    assert result.stages["l3"] == "not_run"


def test_checker_failure_is_observed_l2_failure_and_safe_code_only(tmp_path):
    task, files = task_fixture(tmp_path)
    def rejected(stdout):
        raise ValueError("PRIVATE_CANARY_EXPECTED_VECTOR")
    result = Pc21Evaluator("qkv", task, tmp_path / "private", backend=FakeBackend(task), suite=suite(rejected)).evaluate(
        files, evaluation_id="mathfailure")
    assert result.stages["l2"] == "fail" and result.semantic_status == "fail"
    assert result.public_feedback()["diagnostic_codes"] == ["functional_mismatch"]
    assert "PRIVATE_CANARY" not in json.dumps(result.public_feedback())


@pytest.mark.parametrize("stage", ["parser", "compile"])
def test_public_failed_frontend_reports_only_declared_candidate_source_location(tmp_path, stage):
    task, files = task_fixture(tmp_path)
    backend = FakeBackend(task, fail_stage=stage)
    original = backend.run
    def diagnosed(command, cwd, current_stage, limits):
        raw = original(command, cwd, current_stage, limits)
        return replace(raw, stderr=(str(cwd / "rtl/top.sv") + ":3: syntax error PRIVATE_CANARY_IDENTIFIER\n"
                                   + "trusted_testbench.sv:2: syntax error PRIVATE_CANARY_EXPECTED_VECTOR"))
    backend.run = diagnosed
    result = Pc21Evaluator("qkv", task, tmp_path / "private", backend=backend, suite=suite()).evaluate(
        files, evaluation_id="safe-location-" + stage)
    feedback = result.public_feedback()
    assert not result.accepted
    assert feedback["contract_version"] == "pc21-public-feedback-v2"
    assert feedback["diagnostics"][0]["candidate_file"] == "rtl/top.sv"
    assert feedback["diagnostics"][0]["line"] == 3
    assert "PRIVATE_CANARY" not in json.dumps(feedback)
    assert "trusted_testbench" not in json.dumps(feedback)
    assert str(tmp_path) not in json.dumps(feedback)


def test_public_checker_stream_hint_preserves_the_original_failure_predicate(tmp_path):
    task, files = task_fixture(tmp_path)
    def rejected(stdout):
        raise ValueError("unexpected or wrong q output")
    result = Pc21Evaluator("qkv", task, tmp_path / "private", backend=FakeBackend(task), suite=suite(rejected)).evaluate(
        files, evaluation_id="safe-q-stream")
    assert result.semantic_status == "fail" and result.stages["l2"] == "fail"
    assert result.diagnostic_codes == ("functional_mismatch",)
    assert result.public_feedback()["diagnostics"][0]["category"] == "output_mismatch"
    assert result.public_feedback()["diagnostics"][0]["stream"] == "q"


def test_feedback_revision_participates_in_frozen_tool_policy_identity(tmp_path, monkeypatch):
    task, files = task_fixture(tmp_path)
    backend = FakeBackend(task)
    evaluator = Pc21Evaluator("qkv", task, tmp_path / "private", backend=backend, suite=suite())
    original = evaluator.tool_policy_sha256
    monkeypatch.setattr("sr2fpga_agent.execution.evaluation.FEEDBACK_REVISION", "unit-test-next-feedback")
    assert evaluator._tool_policy_identity() != original
    result = evaluator.evaluate(files, evaluation_id="changed-feedback-revision")
    assert result.execution_status == "integrity_error" and result.semantic_status is None
    assert backend.calls == []


def test_suite_commitment_covers_oracle_sources_and_rejects_changed_stimuli(tmp_path):
    task, files = task_fixture(tmp_path)
    dependency = tmp_path / "synthetic_oracle.py"
    dependency.write_text("def answer(): return 1\n")
    source_hash = hashlib.sha256(dependency.read_bytes()).hexdigest()
    text = ["module trusted_tb;endmodule"]
    frozen = TrustedSuite("private-synthetic", "trusted_tb", lambda: text[0], lambda _: {}, "b" * 64,
                          source_sha256=((str(dependency), source_hash),))
    evaluator = Pc21Evaluator("qkv", task, tmp_path / "private", backend=FakeBackend(task), suite=frozen)
    dependency.write_text("def answer(): return 2\n")
    result = evaluator.evaluate(files, evaluation_id="changedoracle")
    assert result.execution_status == "integrity_error"
    text[0] += "// changed input stimulus"
    with pytest.raises(RuntimeError, match="testbench changed"):
        frozen.verify()


def test_default_suite_identity_includes_actual_case_oracle_and_task_files():
    trusted = TrustedSuite.for_development_case("attention")
    names = {path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1] for path, _ in trusted.source_sha256}
    assert {"oracle.py", "task.py", "harness.py"} <= names
    assert trusted.testbench_sha256 == hashlib.sha256(trusted.render().encode()).hexdigest()


def _slot(condition="M0"):
    return {"campaign_id": "development", "population_id": "synthetic", "semantic_instance_id": "task",
            "replicate_id": 1, "condition_id": condition}


FILES = {"manifest.json": "{}", "rtl/top.sv": "module T;endmodule"}


def _result(files=FILES, *, execution="completed", semantic="pass", visibility="hidden"):
    stages = dict.fromkeys(("l0", "l1", "l2", "l3"), "pass" if semantic == "pass" else "not_run")
    if semantic == "fail":
        stages["l2"] = "fail"
    return EvaluationResult(candidate_sha256(files), "a" * 64, "b" * 64, "c" * 64,
                            visibility, execution, semantic, stages)


def _seal(authority, slot, files=FILES, reason=None):
    return authority.seal_terminal(slot, files=files, task_sha256="a" * 64,
                                   suite_sha256="b" * 64, tool_policy_sha256="c" * 64, reason=reason)


def test_all_six_slots_must_close_before_hidden_and_terminal_null_is_retained(tmp_path):
    slots = [_slot(f"M{i}") for i in range(6)]
    authority = TerminalEvaluationAuthority(tmp_path / "authority", planned_slots=slots)
    _seal(authority, slots[0])
    with pytest.raises(ValueError, match="all planned"):
        authority.close_barrier()
    with pytest.raises(PermissionError, match="barrier"):
        authority.evaluate_once(slots[0], lambda _: _result())
    for slot in slots[1:]:
        _seal(authority, slot, files=None, reason="no_complete_candidate")
    assert authority.close_barrier()["slots"] == 6
    receipt = authority.evaluate_once(slots[1], lambda _: pytest.fail("terminal-null must not execute"))
    assert "hidden_semantic_status" not in receipt
    result = authority.analysis_result(slots[1])
    assert result["hidden_execution_status"] == "not_run"
    assert result["semantic_commit_count"] == 0


def test_hidden_result_is_once_only_across_reopen_and_receipt_contains_no_score(tmp_path):
    root = tmp_path / "authority"
    authority = TerminalEvaluationAuthority(root, planned_slots=[_slot()])
    _seal(authority, _slot())
    authority.close_barrier()
    calls = []
    receipt = authority.evaluate_once(_slot(), lambda files: calls.append(files) or _result(files))
    reopened = TerminalEvaluationAuthority(root, planned_slots=[_slot()])
    assert reopened.evaluate_once(_slot(), lambda _: pytest.fail("no second semantic evaluation")) == receipt
    assert len(calls) == 1
    assert set(receipt) == {"opaque_outcome_id", "slot_id", "generation_visible", "repair_visible", "official"}
    assert reopened.analysis_result(_slot())["semantic_commit_count"] == 1
    hidden = _result()
    assert "semantic_status" not in hidden.to_dict()
    with pytest.raises(PermissionError):
        hidden.public_feedback()


def test_public_prerequisite_failure_closes_hidden_without_discarding_sealed_candidate(tmp_path):
    authority = TerminalEvaluationAuthority(tmp_path / "authority", planned_slots=[_slot()])
    _seal(authority, _slot())
    with pytest.raises(PermissionError):
        authority.close_without_execution(_slot(), reason="public_l2_failed")
    authority.close_barrier()
    receipt = authority.close_without_execution(_slot(), reason="public_l2_failed")
    assert authority.close_without_execution(_slot(), reason="public_l2_failed") == receipt
    outcome = authority.analysis_result(_slot())
    assert outcome["candidate_sha256"] == candidate_sha256(FILES)
    assert outcome["hidden_execution_status"] == "not_run"
    assert outcome["semantic_commit_count"] == 0
    assert outcome["hidden_semantic_status"] is None
    assert authority.evaluate_once(_slot(), lambda _: pytest.fail("closed slot cannot be evaluated later")) == receipt
    with pytest.raises(ValueError, match="different frozen closure"):
        authority.close_without_execution(_slot(), reason="another_reason")


def test_executed_hidden_slot_cannot_be_relabeled_not_run(tmp_path):
    authority = TerminalEvaluationAuthority(tmp_path / "authority", planned_slots=[_slot()])
    _seal(authority, _slot())
    authority.close_barrier()
    authority.evaluate_once(_slot(), lambda _: _result())
    with pytest.raises(ValueError, match="different frozen closure"):
        authority.close_without_execution(_slot(), reason="public_prerequisite_missing")


def test_same_slot_cannot_switch_candidate_or_suite(tmp_path):
    authority = TerminalEvaluationAuthority(tmp_path / "authority", planned_slots=[_slot()])
    _seal(authority, _slot())
    with pytest.raises(ArtifactConflictError):
        _seal(authority, _slot(), {**FILES, "README.md": "different"})
    with pytest.raises(ArtifactConflictError):
        authority.seal_terminal(_slot(), files=FILES, task_sha256="a" * 64,
                                suite_sha256="d" * 64, tool_policy_sha256="c" * 64)


def test_only_known_infrastructure_errors_can_retry_with_fixed_context(tmp_path):
    authority = TerminalEvaluationAuthority(tmp_path / "authority", planned_slots=[_slot()], max_infrastructure_retries=1)
    _seal(authority, _slot())
    authority.close_barrier()
    calls = []
    def evaluator(files):
        calls.append(files)
        return _result(files, execution="infrastructure_error", semantic=None) if len(calls) == 1 else _result(files)
    authority.evaluate_once(_slot(), evaluator)
    outcome = authority.analysis_result(_slot())
    assert outcome["execution_count"] == 2 and outcome["semantic_commit_count"] == 1
    assert calls[0] == calls[1] == FILES


def test_interrupted_unknown_dispatch_is_not_reissued(tmp_path):
    root = tmp_path / "authority"
    authority = TerminalEvaluationAuthority(root, planned_slots=[_slot()], max_infrastructure_retries=1)
    _seal(authority, _slot())
    authority.close_barrier()
    def lost_receipt(files):
        raise OSError("simulated process interruption after dispatch")
    with pytest.raises(OSError):
        authority.evaluate_once(_slot(), lost_receipt)
    reopened = TerminalEvaluationAuthority(root, planned_slots=[_slot()], max_infrastructure_retries=1)
    with pytest.raises(IsolationUnavailable, match="unknown"):
        reopened.evaluate_once(_slot(), lambda _: pytest.fail("unknown request cannot be repeated"))


def test_durable_completed_execution_is_reconciled_without_rerunning_worker(tmp_path):
    authority = TerminalEvaluationAuthority(tmp_path / "authority", planned_slots=[_slot()])
    seal = _seal(authority, _slot())
    authority.close_barrier()
    key = seal["slot_id"]
    authority.store.put_blob(f"dispatch/{key}-0", canonical_json_bytes({"candidate_sha256": candidate_sha256(FILES), "ordinal": 0}))
    authority.store.put_blob(f"executions/{key}-0", canonical_json_bytes(_result().to_dict(include_private=True)), media_type="application/json")
    authority.evaluate_once(_slot(), lambda _: pytest.fail("durable completed result must be recovered"))
    assert authority.analysis_result(_slot())["semantic_commit_count"] == 1


def test_analysis_readback_rejects_an_outcome_rebound_to_another_candidate(tmp_path, monkeypatch):
    authority = TerminalEvaluationAuthority(tmp_path / "authority", planned_slots=[_slot()])
    seal = _seal(authority, _slot())
    authority.close_barrier()
    authority.evaluate_once(_slot(), lambda _: _result())
    key = "outcomes/" + seal["slot_id"]
    original_read = authority.store.read_verified
    wrong = json.loads(original_read(key))
    wrong["candidate_sha256"] = "d" * 64
    def read_with_rebound_summary(reference):
        return canonical_json_bytes(wrong) if reference == key else original_read(reference)
    monkeypatch.setattr(authority.store, "read_verified", read_with_rebound_summary)
    with pytest.raises(ValueError, match="sealed candidate disagree"):
        authority.analysis_result(_slot())


def test_concurrent_hidden_request_cannot_execute_a_second_worker(tmp_path):
    root = tmp_path / "authority"
    first = TerminalEvaluationAuthority(root, planned_slots=[_slot()])
    second = TerminalEvaluationAuthority(root, planned_slots=[_slot()])
    _seal(first, _slot())
    first.close_barrier()
    entered, release = threading.Event(), threading.Event()
    calls = []
    def running(files):
        calls.append(files)
        entered.set()
        assert release.wait(5)
        return _result(files)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(first.evaluate_once, _slot(), running)
        assert entered.wait(5)
        try:
            with pytest.raises(RuntimeError):
                second.evaluate_once(_slot(), lambda _: pytest.fail("no concurrent second worker"))
        finally:
            release.set()
        receipt = future.result(timeout=5)
    assert second.evaluate_once(_slot(), lambda _: pytest.fail("completed result is immutable")) == receipt
    assert len(calls) == 1


def test_changed_worker_binding_stops_the_authority(tmp_path):
    authority = TerminalEvaluationAuthority(tmp_path / "authority", planned_slots=[_slot("M0"), _slot("M1")])
    _seal(authority, _slot("M0"))
    _seal(authority, _slot("M1"))
    authority.close_barrier()
    with pytest.raises(ValueError, match="frozen"):
        authority.evaluate_once(_slot("M0"), lambda _: replace(_result(), suite_sha256="d" * 64))
    with pytest.raises(PermissionError, match="integrity"):
        authority.evaluate_once(_slot("M1"), lambda _: pytest.fail("integrity breach stops scope"))


@pytest.mark.skipif(any(resolve_executable(tool) is None for tool in ("yosys", "iverilog", "vvp")),
                    reason="real parser and HDL tools required")
def test_real_attention_control_passes_common_worker_with_private_trace(tmp_path):
    task, files = task_fixture(tmp_path, "attention")
    evaluator = Pc21Evaluator("attention", task, tmp_path / "private")
    result = evaluator.evaluate(files, evaluation_id="realcontrol")
    assert result.accepted, result.to_dict(include_private=True)
    assert result.isolation_qualified is False
    assert "trace" not in result.to_dict()
    raw = json.loads(evaluator.store.read_verified(result.private_record_ref["key"]))
    assert raw["trace"]["completed_invocations"] == 6
    assert raw["trace"]["output_beats"] == 48
