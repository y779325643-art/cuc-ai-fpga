"""Public PC rule delivery and generic examples; no models or EDA tools."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.execution.budgets import B4_MODEL_CALLS, BudgetLedger, BudgetLimits
from sr2fpga_agent.execution import gateway as gateway_module
from sr2fpga_agent.execution.gateway import ModelGateway, ModelStageFailure, ReplayTransport
from sr2fpga_agent.execution.prompt_guidance import COMMON_MODEL_GUIDANCE, MODEL_GUIDANCE_VERSION
from sr2fpga_agent.pc.checker import check_design
from sr2fpga_agent.pc.semantics import PcSemanticError


STAGES = (
    ("direct_project", ("M0", "M1")),
    ("untyped_plan", ("M2",)),
    ("pc_plan", ("M3", "M4", "M5")),
    ("project_from_plan", ("M2",)),
    ("project_from_pc", ("M3",)),
    ("behavior", ("M4", "M5")),
    ("repair_M1", ("M1",)),
    ("repair_M5", ("M5",)),
)


def _gateway(tmp_path, stage):
    limits = {
        method: BudgetLimits.for_method(
            method,
            max_total_input_tokens=100_000,
            max_total_output_tokens=2_000,
            max_single_output_tokens=128,
            max_context_tokens=30_000,
            max_public_tool_calls=0,
            max_active_seconds=30,
            max_eda_seconds=0,
            max_cpu_seconds=0,
            max_memory_bytes=1_000_000,
        )
        for method in B4_MODEL_CALLS
    }
    store = ArtifactStore(tmp_path / "store")
    ledger = BudgetLedger(store, "public-semantic-guidance", limits)
    transport = ReplayTransport({stage: ["{}"]})
    return ModelGateway(store, ledger, transport, max_call_seconds=2), store, transport


@pytest.mark.parametrize("stage,consumers", STAGES)
def test_semantic_guidance_reaches_every_stage_and_is_persisted(tmp_path, stage, consumers):
    gateway, store, transport = _gateway(tmp_path, stage)
    gateway.call("public-rules", stage, consumers, {"public_text": "A generic stream task"},
                 output_format="Return the artifact requested by this fixture.")
    assert len(transport.requests) == 1
    content = transport.requests[0]["messages"][0]["content"]
    assert COMMON_MODEL_GUIDANCE in content
    assert "PC structure rules below apply only when a PC design is requested" in content
    assert "Direct stages need not produce a PC" in content
    assert "signature.ports" in content and "signature.tensor_contracts" in content
    assert "implementation.buffer_rules" in content and "implementation.states" in content
    assert "does not infer an algorithm" in content
    key = "pc21-model/" + hashlib.sha256(b"public-rules").hexdigest() + "/request"
    request = json.loads(store.read_verified(key))
    assert request["model_guidance_version"] == "pc21-public-guidance-v2"
    assert request["messages"][0]["content"] == content


def test_semantic_guidance_change_cannot_reuse_an_existing_model_operation(tmp_path, monkeypatch):
    gateway, _store, transport = _gateway(tmp_path, "pc_plan")
    arguments = ("public-rules", "pc_plan", ("M3", "M4", "M5"), {})
    gateway.call(*arguments, output_format="Return a design.")
    monkeypatch.setattr(gateway_module, "COMMON_MODEL_GUIDANCE", COMMON_MODEL_GUIDANCE + " Changed.")
    with pytest.raises(ModelStageFailure, match="identity_changed"):
        gateway.call(*arguments, output_format="Return a design.")
    assert len(transport.requests) == 1


def test_guidance_is_task_independent_and_preserves_tool_compatibility_advice():
    lowered = COMMON_MODEL_GUIDANCE.lower()
    for private_or_case_term in (
        "qkv", "ffn", "attention", "oracle", "reference", "expected output", "golden",
    ):
        assert private_or_case_term not in lowered
    assert MODEL_GUIDANCE_VERSION == "pc21-public-guidance-v2"
    for advice in (
        "read_verilog -sv -noautowire", "iverilog -g2012", "vvp", "unpacked parameter",
        "localparam arrays", "array assignment patterns", "case statements", "packed constants",
        "explicit function argument", "always_comb", "exactly once as a main relation",
        "not another main relation", "not automatically expressible", "finite implementation boundary",
        "original public boundary remains authoritative",
    ):
        assert advice in COMMON_MODEL_GUIDANCE


def _generic_tensor_boundary():
    descriptor = {
        "shape": [{"axis": "Item", "extent": 3}],
        "element": {"kind": "sint", "width": 8},
        "quantization": {"kind": "integer"},
        "layout": {"order": ["Item"], "lane_axis": "Item", "lanes": 2,
                   "tail": "zero_pad_mask"},
        "sequence": {"kind": "dense", "frame_fact": "Frame", "reset_fact": "Reset"},
    }
    ports = {
        name: {"kind": "stream", "direction": direction, "domain": "d",
               "protocol": "ready_valid_v1", "payload": {"kind": "tensor_beat", "contract": "PacketTensor"}}
        for name, direction in (("rx", "input"), ("tx", "output"))
    }
    return {
        "rtl_top": "GenericStream",
        "parameter_values": {},
        "signature": {"parameters": {}, "domains": {"d": {"clock": "rising", "reset": {"kind": "none"}}},
                      "ports": ports, "tensor_contracts": {"PacketTensor": descriptor}},
        "abi": {"domains": {"d": {"clock": "clk", "reset": None}}, "ports": {
            name: {"payload": name + "_data", "valid": name + "_valid", "ready": name + "_ready"}
            for name in ports
        }},
    }


def test_generic_namespace_explanation_matches_actual_checker_without_behavior_proof():
    boundary = _generic_tensor_boundary()
    design = {
        "entry": "Top", "modules": {"Top": {
            "signature": {"source": "requirement_boundary"},
            "implementation": {
                "kind": "behavioral", "execution": "clocked", "intent": "Implement the public relation",
                "tensor_rules": {"Work": {"kind": "compute", "fact": "Math", "inputs": ["rx"],
                                         "outputs": ["tx"]}},
            },
        }}, "requirement_map": [],
    }
    facts = {name: {"role": "guarantee"} for name in ("Frame", "Reset", "Math")}
    checked = check_design(design, boundary, facts=facts)
    assert checked.instances["self"].port_widths == {"rx": 18, "tx": 18}
    assert "algorithm_correctness" in checked.deferred_checks
    assert {"path": "self.tensor_rules.Work", "kind": "compute", "status": "not_evaluated"} in (
        checked.verification_obligations
    )
    for wrong_namespace in ("PacketTensor", "rx_data"):
        damaged = deepcopy(design)
        damaged["modules"]["Top"]["implementation"]["tensor_rules"]["Work"]["inputs"] = [wrong_namespace]
        with pytest.raises(PcSemanticError, match="unknown tensor port"):
            check_design(damaged, boundary, facts=facts)
