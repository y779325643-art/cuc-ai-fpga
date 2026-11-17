"""Candidate-location allowlists and private-data rejection without HDL tools."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.execution.evaluation import EvaluationResult
from sr2fpga_agent.execution.public_feedback import (
    FEEDBACK_REVISION, HINTS, MAX_DIAGNOSTICS, functional_diagnostics, source_diagnostics, validate_diagnostics,
)
from sr2fpga_agent.models import ToolResult


FILES = {"rtl/top.sv": "module top;\nlocalparam signed [7:0] W [0:3] = '{1,2,3,4};\nendmodule\n"}
WORK = Path("public-feedback-unit-work").resolve()
CANARY = "PRIVATE_CANARY_VECTOR_SEED_647301"


def failed(stderr, *, stdout=CANARY, stage="parser", status="failed", exit_code=1):
    return ToolResult(stage, ["unit-test-no-process"], status, exit_code, stdout, stderr, 0.01)


def project(result, *, files=FILES, sources=("rtl/top.sv",)):
    return source_diagnostics(result, candidate_files=files, declared_sources=sources, work=WORK)


def result(*, semantic="fail", visibility="public", diagnostics=()):
    stages = {key: "pass" for key in ("l0", "l1", "l2", "l3")}
    if semantic == "fail":
        stages["l2"] = "fail"
    return EvaluationResult("a" * 64, "b" * 64, "c" * 64, "d" * 64, visibility,
                            "completed", semantic, stages, (), False, None, diagnostics)


def test_verified_candidate_parameter_array_location_has_a_fixed_hint_only():
    diagnostics = project(failed("rtl/top.sv:2: ERROR: syntax error, unexpected '[' " + CANARY))
    assert diagnostics == ({"stage": "parser", "category": "unsupported_parameter_array",
                            "hint": HINTS["unsupported_parameter_array"], "candidate_file": "rtl/top.sv", "line": 2},)
    assert CANARY not in json.dumps(diagnostics)


def test_parameter_array_hint_requires_candidate_source_evidence():
    files = {"rtl/top.sv": "module top;\nlocalparam signed [7:0] W = 8'd1;\nendmodule\n"}
    diagnostics = project(failed("rtl/top.sv:2: ERROR: syntax error, unexpected '['"), files=files)
    assert diagnostics[0]["category"] == "syntax_error"


def test_absolute_candidate_path_is_replaced_with_its_declared_relative_path():
    diagnostics = project(failed(str(WORK / "rtl/top.sv") + ":1: syntax error", stage="compile"))
    assert diagnostics[0]["candidate_file"] == "rtl/top.sv"
    assert str(WORK) not in json.dumps(diagnostics)


@pytest.mark.parametrize("location", [
    "trusted_testbench.sv:1", "/private/evaluator/trusted_testbench.sv:2", "rtl/undeclared.sv:1",
    "rtl/../private.sv:1", "rtl/top.sv:0", "rtl/top.sv:4", "rtl/top.sv:99999999999999999",
    "\x1b[31mrtl/top.sv:1", "C:/private/another-worker/rtl/top.sv:1",
])
def test_untrusted_or_invalid_source_locations_are_dropped(location):
    diagnostics = project(failed(location + ": syntax error: " + CANARY))
    assert diagnostics == ({"stage": "parser", "category": "parser_failure", "hint": HINTS["parser_failure"]},)
    assert CANARY not in json.dumps(diagnostics)


def test_stdout_and_trusted_testbench_errors_never_supply_candidate_locations():
    diagnostic = project(failed("trusted_testbench.sv:1: syntax error: " + CANARY,
                               stdout="rtl/top.sv:2: syntax error: " + CANARY, stage="compile"))
    assert diagnostic[0]["category"] == "compile_failure"
    assert "candidate_file" not in diagnostic[0]
    assert CANARY not in json.dumps(diagnostic)


@pytest.mark.parametrize("status,exit_code", [("passed", 0), ("timeout", None), ("missing_tool", None),
                                             ("failed", 3221225477), ("failed", -11)])
def test_infrastructure_or_success_does_not_become_candidate_syntax_feedback(status, exit_code):
    assert project(failed("rtl/top.sv:2: syntax error", status=status, exit_code=exit_code)) == ()


def test_diagnostic_count_is_bounded_and_schema_validated():
    files = {"rtl/top.sv": "\n".join("wire line_" + str(i) + ";" for i in range(20))}
    stderr = "\n".join("rtl/top.sv:" + str(i) + ": syntax error " + CANARY for i in range(1, 20))
    diagnostics = project(failed(stderr), files=files)
    assert len(diagnostics) == MAX_DIAGNOSTICS
    feedback = result(diagnostics=diagnostics).public_feedback()
    assert not ContractRegistry().load_schema("pc21_public_feedback_v2").validate(feedback)
    assert len(json.dumps(feedback)) < 4096


@pytest.mark.parametrize("message,category,stream", [
    ("unexpected or wrong q output", "output_mismatch", "q"),
    ("unexpected or wrong k output", "output_mismatch", "k"),
    ("unexpected or wrong v output", "output_mismatch", "v"),
    ("changed stalled q token", "stalled_output_changed", "q"),
    ("invalid or unknown trace signal: output valid persisted following a reset edge", "reset_output_valid", None),
    ("bounded completion exceeded", "completion_bound", None),
    ("next invocation input before all outputs completed", "transaction_overlap", None),
    ("full cache did not backpressure all inputs", "cache_backpressure", None),
])
def test_known_checker_messages_map_to_fixed_public_categories(message, category, stream):
    diagnostic = functional_diagnostics(ValueError(message))[0]
    assert diagnostic["category"] == category
    assert diagnostic.get("stream") == stream
    assert diagnostic["hint"] == HINTS[category]
    assert "cycle" not in diagnostic and "actual" not in diagnostic and "expected" not in diagnostic


@pytest.mark.parametrize("message", [
    CANARY, "unexpected or wrong q output " + CANARY,
    "changed stalled " + CANARY + " token", "output mismatch at cycle 781: got a7812, expected 3c982",
    "invalid or unknown trace signal: " + CANARY, "expected 3 completed invocations, observed 2",
])
def test_unknown_checker_exceptions_never_export_values_paths_or_seeds(message):
    diagnostic = functional_diagnostics(ValueError(message))
    assert diagnostic == ({"stage": "functional", "category": "functional_mismatch", "hint": HINTS["functional_mismatch"]},)
    assert CANARY not in json.dumps(diagnostic)
    assert message not in json.dumps(diagnostic)


@pytest.mark.parametrize("changes", [
    {"hint": CANARY}, {"category": CANARY}, {"private_path": CANARY}, {"stream": CANARY},
    {"stage": "functional"}, {"candidate_file": "../private.sv"}, {"line": True}, {"line": 0},
    {"line": 1000001}, {"candidate_file": "rtl/../private.sv"}, {"candidate_file": "rtl/" + "x" * 241 + ".sv"},
])
def test_restored_diagnostic_fields_and_bounds_are_validated(changes):
    diagnostic = {"stage": "parser", "category": "syntax_error", "hint": HINTS["syntax_error"],
                  "candidate_file": "rtl/top.sv", "line": 1, **changes}
    with pytest.raises(ValueError):
        validate_diagnostics([diagnostic])


def test_hidden_boundary_and_acceptance_predicate_are_unchanged():
    diagnostics = functional_diagnostics(ValueError("unexpected or wrong q output"))
    passing = result(semantic="pass", diagnostics=diagnostics)
    failing = result(diagnostics=diagnostics)
    assert passing.accepted and passing.public_feedback()["accepted"] is True
    assert not failing.accepted and failing.public_feedback()["accepted"] is False
    hidden = replace(failing, visibility="hidden")
    with pytest.raises(PermissionError, match="hidden"):
        hidden.public_feedback()
    assert set(hidden.to_dict()) == {"candidate_sha256", "task_sha256", "suite_sha256", "tool_policy_sha256",
                                      "visibility", "generation_visible", "repair_visible"}
    assert "diagnostics" not in json.dumps(hidden.to_dict())


def test_old_result_dict_and_positional_constructor_remain_readable():
    current = result().to_dict(include_private=True)
    current.pop("public_diagnostics")
    restored = EvaluationResult(**json.loads(json.dumps(current)))
    assert restored.public_feedback()["diagnostics"] == []
    assert restored.public_feedback()["feedback_revision"] == FEEDBACK_REVISION
    private = {"key": "unit-test-private-reference"}
    positional = EvaluationResult("a" * 64, "b" * 64, "c" * 64, "d" * 64, "public", "completed", "fail",
                                  {key: "fail" for key in ("l0", "l1", "l2", "l3")}, (), False, private)
    assert positional.private_record_ref == private and positional.public_diagnostics == ()


def test_registered_feedback_schema_rejects_raw_or_unbounded_fields():
    schema = ContractRegistry().load_schema("pc21_public_feedback_v2")
    good = result().public_feedback()
    assert not schema.validate(good)
    for changed in ({**good, "raw_stdout": CANARY}, {**good, "feedback_revision": "old"},
                    {**good, "diagnostics": [functional_diagnostics(ValueError(CANARY))[0]] * (MAX_DIAGNOSTICS + 1)},
                    {**good, "diagnostics": [{"stage": "functional", "category": "functional_mismatch", "hint": CANARY}]}):
        assert schema.validate(changed)
