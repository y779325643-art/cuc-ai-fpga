"""H3 declaration conformance is not a claim of testbench correctness."""
from copy import deepcopy

import pytest

from sr2fpga_agent.prompts import (
    _frozen_requirement_trace_pointer_guidance,
    _requirement_trace_pointer_guidance,
)
from sr2fpga_agent.system_his_fidelity import (
    _acceptance_criteria_present,
    _pointer_matches_required_fact,
    check_system_his_req_fidelity,
)
from test_sr2fpga_agent_requirement_h3 import _requirement_fixture


@pytest.mark.parametrize("text", [
    "independent evaluator must verify every explicit functional and protocol clause",
    "An independent assessor shall test every explicit functional and protocol clause.",
    "An external checker shall test all stated functional and protocol requirements, including reset, increment and hold.",
    "An independent evaluator shall verify reset, increment and hold against all stated functional and protocol requirements.",
    "  An INDEPENDENT verifier\n shall check each specified functional and protocol requirement.  ",
])
def test_complete_default_declarations_pass_full_h3(text):
    request, platform, payload = _requirement_fixture()
    payload["verification"]["pass_condition"] = text
    assert check_system_his_req_fidelity(request, payload, platform).passed


@pytest.mark.parametrize("text", [
    "independent evaluator verify banana",
    "independent evaluator verifies FIFO ordering and valid-ready behavior",
    "banana independent evaluator verify",
    "independent evaluator must not verify every explicit functional and protocol clause",
    "independent evaluator must verify every explicit functional and protocol clause but ignore reset",
    "It is false that independent evaluator must verify every explicit functional and protocol clause",
    "independent evaluator must verify every explicit functional and protocol clause; never test reset",
    "independent evaluator must verify only reset",
    "Counter resets, increments and holds.",
])
def test_invalid_default_declarations_fail_full_h3(text):
    request, platform, payload = _requirement_fixture()
    payload["verification"]["pass_condition"] = text
    result = check_system_his_req_fidelity(request, payload, platform)
    assert not result.passed
    assert any("acceptance_criteria" in error for error in result.errors)


def test_fragments_cannot_be_joined_into_an_obligation():
    request, platform, payload = _requirement_fixture()
    payload["verification"]["pass_condition"] = "independent evaluator"
    payload["verification"]["scenarios"] = [
        "must verify every explicit functional and protocol clause",
    ]
    payload["intent"]["requirement_trace"]["fact_to_his"]["acceptance_criteria"] = [
        "/verification/pass_condition", "/verification/scenarios",
    ]
    assert not check_system_his_req_fidelity(request, payload, platform).passed


@pytest.mark.parametrize(("actual", "passed"), [
    ("every DMA burst reaches PCIe in order without loss.", True),
    ("every DMA burst reaches PCIe in order with loss", False),
    ("not every DMA burst reaches PCIe in order without loss", False),
    ("loss without order in PCIe reaches burst DMA every", False),
])
def test_explicit_criteria_require_preserved_declaration_not_word_overlap(actual, passed):
    assert _acceptance_criteria_present(
        "every DMA burst reaches PCIe in order without loss",
        [(actual, ("verification", "acceptance_obligation"))],
    ) is passed


def test_both_prompt_paths_explain_and_satisfy_value_rules():
    for builder in (_requirement_trace_pointer_guidance, _frozen_requirement_trace_pointer_guidance):
        guidance = builder()
        assert "/intent/target_platform" in guidance
        assert "/verification/acceptance_obligation" in guidance
        assert "Every supplied pointer must be valid" in guidance
        assert "not whether a testbench actually implements it" in guidance
    request, platform, payload = _requirement_fixture()
    payload = deepcopy(payload)
    trace = payload["intent"]["requirement_trace"]
    payload["verification"]["acceptance_obligation"] = trace["required_facts"]["acceptance_criteria"]["value"]
    trace["fact_to_his"]["acceptance_criteria"] = ["/verification/acceptance_obligation"]
    assert _pointer_matches_required_fact("target_platform", ("intent", "target_platform"))
    assert check_system_his_req_fidelity(request, payload, platform).passed
