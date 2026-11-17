"""Public namespace aids are faithful, detached and included before accounting."""
from __future__ import annotations

import copy
from importlib import import_module
import json

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.execution import public_interfaces as public_interfaces_module
from sr2fpga_agent.execution.gateway import ModelStageFailure
from sr2fpga_agent.execution.public_interfaces import (
    PUBLIC_INTERFACE_INDEX_VERSION,
    indexed_public_payload,
    public_interface_index,
)
from sr2fpga_agent.models import canonical_json_bytes
from agent.tests.test_sr2fpga_pc21_prompt_guidance import STAGES, gateway_fixture


def boundary_for(case):
    return import_module("sr2fpga_agent.tasks.llm_" + case).build_development_task()["boundary"]["boundary"]


@pytest.mark.parametrize("case,expected", (
    ("qkv", {"rx": "X", "q": "Q", "k": "K", "v": "V"}),
    ("attention", {"q": "Query", "k": "Key", "v": "Value", "context": "Context"}),
    ("ffn", {"rx": "hidden", "tx": "hidden"}),
))
def test_current_public_case_namespaces_remain_distinct(case, expected):
    boundary = boundary_for(case)
    index = public_interface_index(boundary)
    assert index["scope"] == "requirement_entry_boundary"
    assert index["view_version"] == PUBLIC_INTERFACE_INDEX_VERSION
    rows = {row["logical_port"]: row for row in index["ports"]}
    assert {name: row["tensor_contract"] for name, row in rows.items()} == expected
    for name, row in rows.items():
        assert row["direction"] == boundary["signature"]["ports"][name]["direction"]
        assert row["abi"] == boundary["abi"]["ports"][name]
    assert index["domains"] == [{"domain": "d", "abi": {"clock": "clk", "reset": "rst_n"}}]


def test_public_index_is_sorted_detached_and_does_not_supply_architecture():
    boundary = boundary_for("qkv")
    original = copy.deepcopy(boundary)
    index = public_interface_index(boundary)
    reordered = copy.deepcopy(boundary)
    reordered["signature"]["ports"] = dict(reversed(list(reordered["signature"]["ports"].items())))
    assert canonical_json_bytes(index) == canonical_json_bytes(public_interface_index(reordered))
    assert "modules" not in index and "tensor_rules" not in index and "states" not in index
    index["ports"][0]["abi"]["payload"] = "changed"
    index["domains"][0]["abi"]["clock"] = "changed"
    index["parameter_values"]["extra"] = 7
    assert boundary == original


def test_index_ignores_unrelated_metadata_and_does_not_expand_into_private_material():
    boundary = boundary_for("qkv")
    marker = "PRIVATE_DATA_MUST_NOT_BE_INDEXED"
    boundary["oracle"] = marker
    boundary["signature"]["ports"]["rx"]["implementation"] = marker
    boundary["abi"]["ports"]["rx"]["private_path"] = marker
    assert marker not in json.dumps(public_interface_index(boundary))


def test_non_tensor_public_ports_keep_their_abi_without_fabricated_tensor_ids():
    boundary = {
        "rtl_top": "PublicBlock", "parameter_values": {"W": 8},
        "signature": {"parameters": {"W": {"minimum": 1, "maximum": 16}},
            "domains": {"d": {"clock": "rising", "reset": {"kind": "none"}}}, "ports": {
            "enable": {"kind": "value", "direction": "input", "domain": None,
                       "type": {"kind": "uint", "width": 1}},
            "rx": {"kind": "stream", "direction": "input", "domain": "d",
                   "protocol": "ready_valid_v1", "payload": {"kind": "uint", "width": {"param": "W"}}},
        }},
        "abi": {"domains": {"d": {"clock": "clk", "reset": None}}, "ports": {
            "enable": {"signal": "enable_pin"},
            "rx": {"payload": "data_pin", "valid": "valid_pin", "ready": "ready_pin"},
        }},
    }
    assert ContractRegistry().load_schema("development_public_boundary").validate({
        "contract_version": "development-public-boundary-v1",
        "validation_scope": "boundary_shape_only", "boundary": boundary,
    }) == ()
    index = public_interface_index(boundary)
    assert all("tensor_contract" not in row for row in index["ports"])
    assert index["ports"][0]["abi"] == {"signal": "enable_pin"}
    assert index["ports"][1]["payload_kind"] == "uint"
    assert index["parameter_values"] == {"W": 8}


@pytest.mark.parametrize("stage,consumers,format_text", STAGES)
def test_every_initial_and_repair_request_receives_the_same_public_index(
    tmp_path, stage, consumers, format_text,
):
    gateway, store, transport = gateway_fixture(tmp_path, stage)
    boundary = boundary_for("qkv")
    public = {"public_task": {"boundary": boundary, "public_text": "public task"}}
    before = copy.deepcopy(public)
    gateway.call("entry-index", stage, consumers, public, output_format=format_text)
    wire = transport.requests[0]
    value = json.loads(wire["messages"][-1]["content"])
    assert value["public_interface_index"] == public_interface_index(boundary)
    assert value["public_task"] == before["public_task"] and public == before
    assert wire["max_output_tokens"] > 0
    # Replay accounting is explicitly synthetic, but it must include the index.
    counted = transport.count_input_tokens(wire["messages"])
    assert gateway.ledger.snapshot()["actual"]["observed"]["input_tokens"] == counted
    assert counted > transport.count_input_tokens([
        wire["messages"][0], {"role": "user", "content": canonical_json_bytes(before).decode()},
    ])


def test_gateway_owned_index_cannot_be_overridden_and_no_task_payload_is_unchanged():
    assert indexed_public_payload({"public_text": "public"}) == {"public_text": "public"}
    with pytest.raises(ValueError, match="derived by the model gateway"):
        indexed_public_payload({"public_interface_index": {"ports": []}})


def test_index_revision_changes_frozen_request_identity_without_redispatch(tmp_path, monkeypatch):
    gateway, _, transport = gateway_fixture(tmp_path, "direct_project")
    public = {"public_task": {"boundary": boundary_for("qkv")}}
    gateway.call("entry-index", "direct_project", ("M0", "M1"), public, output_format="text")
    monkeypatch.setattr(public_interfaces_module, "PUBLIC_INTERFACE_INDEX_VERSION", "different-index-view")
    with pytest.raises(ModelStageFailure, match="identity_changed"):
        gateway.call("entry-index", "direct_project", ("M0", "M1"), public, output_format="text")
    assert len(transport.requests) == 1
