"""Exercise public prompt contracts without a model service or HDL tools."""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.execution.budgets import B4_MODEL_CALLS, BudgetLedger, BudgetLimits
from sr2fpga_agent.execution import gateway as gateway_module
from sr2fpga_agent.execution import proposals as proposals_module
from sr2fpga_agent.execution.gateway import ModelGateway, ModelStageFailure, ReplayTransport
from sr2fpga_agent.execution.prompt_guidance import COMMON_MODEL_GUIDANCE, MODEL_GUIDANCE_VERSION
from sr2fpga_agent.execution.proposals import (
    BEHAVIOR_FORMAT,
    BODY_HDL_RULES,
    BODY_OWNERSHIP_GUIDANCE,
    DESIGN_FORMAT,
    JSON_ONLY_FORMAT,
    MODEL_FILE_RULES,
    PROJECT_FORMAT,
    REPAIR_FORMAT,
    parse_proposal,
)
from sr2fpga_agent.execution.runtime import PairedBlockRuntime
from sr2fpga_agent.pc.inputs import ParseLimits, PcParseError


STAGES = (
    ("direct_project", ("M0", "M1"), PROJECT_FORMAT),
    ("untyped_plan", ("M2",), "Return a concise untyped implementation plan as plain text."),
    ("pc_plan", ("M3", "M4", "M5"), DESIGN_FORMAT),
    ("project_from_plan", ("M2",), PROJECT_FORMAT),
    ("project_from_pc", ("M3",), PROJECT_FORMAT),
    ("behavior", ("M4", "M5"), BEHAVIOR_FORMAT),
    ("repair_M1", ("M1",), REPAIR_FORMAT),
    ("repair_M5", ("M5",), REPAIR_FORMAT),
)


def gateway_fixture(tmp_path, stage):
    limits = {
        method: BudgetLimits.for_method(
            method,
            max_total_input_tokens=200_000,
            max_total_output_tokens=10_000,
            max_single_output_tokens=512,
            max_context_tokens=100_000,
            max_public_tool_calls=0,
            max_active_seconds=30,
            max_eda_seconds=30,
            max_cpu_seconds=60,
            max_memory_bytes=1_000_000,
        )
        for method in B4_MODEL_CALLS
    }
    store = ArtifactStore(tmp_path / "store")
    ledger = BudgetLedger(store, "prompt-guidance-test", limits)
    transport = ReplayTransport({stage: ["{}"]})
    return ModelGateway(store, ledger, transport, max_call_seconds=2), store, transport


@pytest.mark.parametrize("stage,consumers,format_text", STAGES)
def test_all_initial_and_repair_gateway_stages_share_versioned_public_guidance(
    tmp_path, stage, consumers, format_text
):
    gateway, store, transport = gateway_fixture(tmp_path, stage)
    gateway.call("prompt-check", stage, consumers, {"public_text": "A public stream task"},
                 output_format=format_text)
    assert len(transport.requests) == 1
    system = transport.requests[0]["messages"][0]["content"]
    assert COMMON_MODEL_GUIDANCE in system
    assert system.count(MODEL_GUIDANCE_VERSION) == 1
    assert "read_verilog -sv -noautowire" in system
    assert "iverilog -g2012" in system and "vvp" in system
    key = "pc21-model/" + hashlib.sha256(b"prompt-check").hexdigest() + "/request"
    request = json.loads(store.read_verified(key))
    assert request["model_guidance_version"] == MODEL_GUIDANCE_VERSION
    assert request["messages"][0]["content"] == system
    if stage == "untyped_plan":
        assert JSON_ONLY_FORMAT not in system
    else:
        assert JSON_ONLY_FORMAT in system


def test_guidance_version_is_bound_to_frozen_request_identity(tmp_path, monkeypatch):
    gateway, store, transport = gateway_fixture(tmp_path, "direct_project")
    gateway.call("prompt-check", "direct_project", ("M0", "M1"), {}, output_format=PROJECT_FORMAT)
    monkeypatch.setattr(gateway_module, "MODEL_GUIDANCE_VERSION", "pc21-generic-hdl-guidance-next")
    with pytest.raises(ModelStageFailure, match="identity_changed"):
        gateway.call("prompt-check", "direct_project", ("M0", "M1"), {}, output_format=PROJECT_FORMAT)
    assert len(transport.requests) == 1
    assert store.reference("generation-closed") is None


class PromptCaptured(RuntimeError):
    pass


@pytest.mark.parametrize("method", ("M1", "M5"))
def test_runtime_repair_assembly_has_one_repair_root_and_shared_file_rules(tmp_path, method):
    runtime = object.__new__(PairedBlockRuntime)
    runtime.store = ArtifactStore(tmp_path / "store")
    runtime.ledger = SimpleNamespace(remaining=lambda *args: 1)
    runtime._cached = lambda operation, consumers, action: action()
    captured = {}

    def capture(operation, stage, consumers, payload, format_text):
        captured.update(stage=stage, payload=payload, format=format_text)
        raise PromptCaptured()

    runtime._call = capture
    with pytest.raises(PromptCaptured):
        runtime._repair(method, PairedBlockRuntime._state({"ok": False}))
    assert captured["stage"] == "repair_" + method
    assert captured["format"] == REPAIR_FORMAT
    assert MODEL_FILE_RULES in captured["format"]
    assert "For files in replace_project or replace_project_files:" in captured["format"]
    assert "For units in replace_behavior_units:" in captured["format"]
    assert 'contract_version="pc21-repair-proposal-v1"' in captured["format"]
    assert '"contract_version":"pc21-project-proposal-v1"' not in captured["format"]
    assert PROJECT_FORMAT not in captured["format"]
    if method == "M5":
        assert captured["payload"]["behavior_body_ownership"] == BODY_OWNERSHIP_GUIDANCE
        assert BODY_HDL_RULES in captured["format"]


def test_runtime_behavior_request_explains_framework_owned_module_wrapper():
    runtime = object.__new__(PairedBlockRuntime)
    runtime._cached = lambda operation, consumers, action: action()
    runtime._build = lambda pc: SimpleNamespace(
        build_plan_sha256="a" * 64,
        units={"public-unit": {"header": "module Example(input logic clk);\n"}},
    )
    captured = {}

    def capture(operation, stage, consumers, payload, format_text):
        captured.update(payload=payload, format=format_text)
        raise PromptCaptured()

    runtime._call = capture
    with pytest.raises(PromptCaptured):
        runtime._body_node("initial-SB", ("M4", "M5"), {})
    assert captured["format"] == BEHAVIOR_FORMAT
    assert captured["payload"]["behavior_body_ownership"] == BODY_OWNERSHIP_GUIDANCE
    assert "framework adds the module header and the final endmodule" in BODY_OWNERSHIP_GUIDANCE
    assert "Do not output module, endmodule" in BODY_OWNERSHIP_GUIDANCE


def test_common_guidance_is_generic_tool_policy_with_portable_expression_advice():
    lowered = COMMON_MODEL_GUIDANCE.lower()
    for private_or_case_term in ("qkv", "oracle", "reference", "q_bias", "k_w", "expected output"):
        assert private_or_case_term not in lowered
    for advice in ("unpacked parameter", "localparam arrays", "array assignment patterns",
                   "case statements", "packed constants", "explicit function argument", "always_comb"):
        assert advice in COMMON_MODEL_GUIDANCE


@pytest.mark.parametrize("wrap", (
    lambda text: "```json\n" + text + "\n```",
    lambda text: "Here is the proposal:\n" + text,
    lambda text: text + "\n{}",
))
def test_json_guidance_does_not_weaken_strict_proposal_parsing(wrap):
    value = {"contract_version": "pc21-project-proposal-v1", "files": {"manifest.json": "{}"}}
    text = json.dumps(value)
    assert parse_proposal(text, "pc21_project_proposal") == value
    with pytest.raises(ValueError):
        parse_proposal(wrap(text), "pc21_project_proposal")


@pytest.mark.parametrize("contract_key,contract", (
    ("pc21_project_proposal", "pc21-project-proposal-v1"),
    ("pc21_behavior_bundle", "pc21-behavior-bundle-v1"),
    ("pc21_repair_proposal", "pc21-repair-proposal-v1"),
))
def test_json_syntax_diagnostic_names_the_actual_proposal_without_echoing_text(contract_key, contract):
    candidate_marker = "UNTRUSTED_CANDIDATE_TEXT_DO_NOT_ECHO"
    for malformed in ("```json\n" + candidate_marker + "\n```", '{"x": ' + candidate_marker + '}'):
        with pytest.raises(PcParseError) as caught:
            parse_proposal(malformed, contract_key)
        message = str(caught.value)
        assert "invalid " + contract + " JSON" in message
        assert "invalid PC JSON" not in message
        assert candidate_marker not in message
        if malformed.startswith("```"):
            assert "Markdown code fences are forbidden" in message


@pytest.mark.parametrize("text,message", (
    (" " * 33, "PC JSON exceeds max_bytes"),
    ('{"a":[[[[0]]]]}', "PC JSON exceeds max_depth"),
    ('{"a":1,"a":2}', "duplicate JSON object key"),
    ('{"a":1.5}', "PC JSON requires integer number literals"),
    ("[]", "PC JSON root must be an object"),
    (r'{"a":"\ud800"}', "PC JSON contains an unpaired Unicode surrogate"),
))
def test_proposal_syntax_diagnostic_preserves_other_parser_rejections(monkeypatch, text, message):
    monkeypatch.setattr(proposals_module, "ParseLimits", lambda *args: ParseLimits(32, 4))
    with pytest.raises(PcParseError) as caught:
        parse_proposal(text, "pc21_repair_proposal")
    assert str(caught.value) == message
