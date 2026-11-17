"""Requirement-derived ABI goldens and real-parser construction boundaries."""

from __future__ import annotations

import copy
import json
import subprocess

import pytest

from sr2fpga_agent.local_tools import executable_env, resolve_executable
from sr2fpga_agent.pc.abi import pack_tensor_beat, tensor_beats
from sr2fpga_agent.pc.checker import check_design
from sr2fpga_agent.pc.emitter import (
    BEHAVIOR_CONTRACT,
    PcBuildError,
    build_structure,
    compose_behavior,
    write_project,
)


def _descriptor():
    return {"shape": [{"axis": "N", "extent": 1}, {"axis": "C", "extent": 3}],
            "element": {"kind": "sint", "width": 8},
            "quantization": {"kind": "affine", "granularity": "per_tensor",
                             "scale": {"numerator": 1, "denominator": 8},
                             "zero_point": -3, "range": {"min": -128, "max": 127}},
            "layout": {"order": ["N", "C"], "lane_axis": "C", "lanes": 2,
                       "tail": "zero_pad_mask"},
            "sequence": {"kind": "dense", "frame_fact": "frame", "reset_fact": "reset"}}


def _fixture():
    signature = {"parameters": {}, "domains": {"d": {"clock": "rising", "reset": {
        "kind": "sync", "polarity": "active_low"}}}, "tensor_contracts": {"T": _descriptor()},
        "ports": {name: {"kind": "stream", "direction": direction,
                         "protocol": "ready_valid_v1", "domain": "d",
                         "payload": {"kind": "tensor_beat", "contract": "T"}}
                  for name, direction in [("rx", "input"), ("tx", "output")]}}
    boundary = {"rtl_top": "PipeTop", "signature": copy.deepcopy(signature), "parameter_values": {},
                "abi": {"domains": {"d": {"clock": "clk", "reset": "rst_n"}}, "ports": {
                    "rx": {"payload": "in_data", "valid": "in_valid", "ready": "in_ready"},
                    "tx": {"payload": "out_data", "valid": "out_valid", "ready": "out_ready"}}}}
    def net(src_i, src_p, dst_i, dst_p):
        return {"source": {"kind": "endpoint", "endpoint": {"instance": src_i, "port": src_p}},
                "sinks": [{"instance": dst_i, "port": dst_p}]}
    design = {"entry": "Top", "modules": {
        "Top": {"signature": {"source": "requirement_boundary"}, "implementation": {
            "kind": "structural", "instances": {"pipe": {"module": "Pipe", "parameters": {},
                                                            "domains": {"d": "d"}}},
            "nets": {"input": net("self", "rx", "pipe", "rx"),
                     "output": net("pipe", "tx", "self", "tx")}}},
        "Pipe": {"signature": {"source": "declared", **signature}, "implementation": {
            "kind": "behavioral", "execution": "clocked", "intent": "Tensor identity",
            "tensor_rules": {"identity": {"kind": "identity", "fact": "identity",
                                          "input": "rx", "output": "tx"}}}}},
        "requirement_map": []}
    facts = {name: {"role": "guarantee"} for name in ["frame", "reset", "identity"]}
    return design, boundary, facts


def _build():
    design, boundary, facts = _fixture()
    checked = check_design(design, boundary, facts=facts)
    bindings = {key: {"id": key, "sha256": "0" * 64}
                for key in ["requirements", "target_profile", "capability_profile"]}
    return build_structure(checked, bindings=bindings)


_BODY = """assign p_tx_payload = p_rx_payload;
assign p_tx_valid = p_rx_valid;
assign p_rx_ready = p_tx_ready;"""


def _bundle(build, body=_BODY):
    return {"contract_version": BEHAVIOR_CONTRACT, "build_plan_sha256": build.build_plan_sha256,
            "units": {unit: {"body": body} for unit in build.units}}


def test_tensor_abi_has_independent_hex_and_coordinate_goldens():
    descriptor = _descriptor()
    assert pack_tensor_beat(descriptor, [-128, 127]) == 0x37F80
    assert pack_tensor_beat(descriptor, [-3, None]) == 0x100FD
    assert list(tensor_beats(descriptor)) == [
        {"group": None, "coordinates": [{"N": 0, "C": 0}, {"N": 0, "C": 1}]},
        {"group": None, "coordinates": [{"N": 0, "C": 2}, None]},
    ]


def test_partial_groups_have_explicit_outer_and_inner_order():
    descriptor = _descriptor()
    descriptor["sequence"].update(kind="partial_sum", reduction_axis="K", groups=2,
                                   group_order="outermost")
    assert [b["group"] for b in tensor_beats(descriptor)] == [0, 0, 1, 1]
    descriptor["sequence"]["group_order"] = "innermost"
    assert [b["group"] for b in tensor_beats(descriptor)] == [0, 1, 0, 1]


def test_structure_is_deterministic_wiring_with_reverse_ready():
    build = _build()
    assert build == _build()
    top = build.files["rtl/top.sv"]
    assert "input logic [17:0] in_data" in top
    assert "assign w_pipe__p_rx_payload = in_data;" in top
    assert "assign in_ready = w_pipe__p_rx_ready;" in top
    assert "assign w_pipe__p_tx_ready = out_ready;" in top
    assert "always" not in top
    unit = next(iter(build.units.values()))
    assert "always" not in unit["header"]
    assert build.abi_map["instances"]["self"]["abi"]["ports"]["rx"]["layout"]["mask"] == {
        "lsb": 16, "width": 2}


def test_semantic_change_invalidates_behavior_identity_even_at_same_width():
    original = _build()
    design, boundary, facts = _fixture()
    boundary["signature"]["tensor_contracts"]["T"]["quantization"]["zero_point"] = 2
    design["modules"]["Pipe"]["signature"]["tensor_contracts"]["T"]["quantization"]["zero_point"] = 2
    changed = build_structure(check_design(design, boundary, facts=facts),
                              bindings=original.build_plan["identity"]["bindings"])
    assert original.build_plan_sha256 != changed.build_plan_sha256
    assert set(original.units) != set(changed.units)


@pytest.mark.parametrize("change", ["missing", "extra", "plan", "structure"])
def test_bundle_and_protected_structure_fail_before_parser(change, tmp_path):
    build = _build()
    bundle = _bundle(build)
    if change == "missing":
        bundle["units"].clear()
    elif change == "extra":
        bundle["units"]["unknown"] = {"body": _BODY}
    elif change == "plan":
        bundle["build_plan_sha256"] = "1" * 64
    else:
        build.files["rtl/top.sv"] += "// altered\n"
    with pytest.raises(PcBuildError):
        compose_behavior(build, bundle, yosys="certainly-missing-yosys", scratch_root=tmp_path)


@pytest.mark.parametrize("body", [
    '`include "private.sv"', 'initial $readmemh("private", storage);',
    "endmodule module extra; endmodule", "assign p_tx_payload = other.internal;",
    "(* blackbox *) wire trick;", "assign p_tx_payload = $random;",
])
def test_forbidden_dependencies_do_not_reach_a_tool(body, tmp_path):
    build = _build()
    with pytest.raises(PcBuildError):
        compose_behavior(build, _bundle(build, body), yosys="certainly-missing-yosys", scratch_root=tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.skipif(resolve_executable("yosys") is None, reason="real Yosys frontend unavailable")
def test_real_parser_accepts_body_and_canonical_package_compiles(tmp_path):
    build = _build()
    project = compose_behavior(build, _bundle(build), scratch_root=tmp_path / "parse",
                               behavior_origin="hand_authored_development_control")
    root = write_project(project, tmp_path / "project")
    manifest = json.loads(project.files["manifest.json"])
    assert manifest["contract_version"] == "project-package-v1"
    assert all(origin["body"] == "hand_authored_development_control"
               for origin in project.construction_origin_map.values() if "unit_id" in origin)
    assert all(item["returncode"] == 0 for item in project.parser_evidence.values())
    if resolve_executable("iverilog") is not None:
        (root / "testbench.sv").write_text("""module tb;
reg clk=0, rst_n=0, in_valid=0, out_ready=0;
reg [17:0] in_data=0;
wire [17:0] out_data;
wire in_ready, out_valid;
PipeTop dut(clk,rst_n,in_data,in_valid,in_ready,out_data,out_valid,out_ready);
initial begin
  #1; rst_n=1; in_valid=1; in_data=18'h37f80; out_ready=1;
  #1; if(out_data!==18'h37f80 || !out_valid || !in_ready) $fatal(1);
  out_ready=0; in_data=18'h100fd;
  #1; if(out_data!==18'h100fd || !out_valid || in_ready) $fatal(1);
  $finish;
end
endmodule
""", encoding="utf-8")
        # This installed Windows compiler is qualified with explicit verbose
        # mode; the nonverbose invocation crashed with an empty tool log.
        result = subprocess.run([str(resolve_executable("iverilog")), "-v", "-g2012", "-s", "tb",
                                 "-o", "compiled.out", *[s["path"] for s in manifest["sources"]],
                                 "testbench.sv"],
                                cwd=root, env=executable_env(), capture_output=True, timeout=20)
        (root / "compiler-result.json").write_text(json.dumps({
            "returncode": result.returncode, "stdout": result.stdout.decode(errors="replace"),
            "stderr": result.stderr.decode(errors="replace")}), encoding="utf-8")
        assert result.returncode == 0, result.stderr.decode(errors="replace")
        simulation = subprocess.run([str(resolve_executable("vvp")), "compiled.out"],
                                    cwd=root, env=executable_env(), capture_output=True, timeout=20)
        assert simulation.returncode == 0, simulation.stderr.decode(errors="replace")
    with pytest.raises(FileExistsError):
        write_project(project, root)


@pytest.mark.skipif(resolve_executable("yosys") is None, reason="real Yosys frontend unavailable")
@pytest.mark.parametrize("body,match", [
    (_BODY + "\nassign p_rx_payload = 18'h0;", "protected input"),
    (_BODY + "\nwire q; hidden child(q);", "architectural instance"),
    (_BODY + "\ninput extra;", "parser rejected|port set"),
])
def test_real_parser_enforces_ast_and_signature_boundaries(body, match, tmp_path):
    build = _build()
    with pytest.raises(PcBuildError, match=match):
        compose_behavior(build, _bundle(build, body), scratch_root=tmp_path)


@pytest.mark.skipif(resolve_executable("yosys") is None, reason="real Yosys frontend unavailable")
def test_function_inputs_are_local_and_allowed_by_real_parser(tmp_path):
    build = _build()
    body = """function [17:0] identity;
input [17:0] value;
begin identity = value; end
endfunction
assign p_tx_payload = identity(p_rx_payload);
assign p_tx_valid = p_rx_valid;
assign p_rx_ready = p_tx_ready;"""
    project = compose_behavior(build, _bundle(build, body), scratch_root=tmp_path)
    assert len(project.files) == 3
