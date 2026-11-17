"""Candidate-visible QKV projection facts and synthetic public assets.

This development profile preserves the distinct Q/KV head counts used by
grouped-query attention. It is a small exact integer engineering task, not a
released LLM checkpoint or an end-to-end language-model benchmark.
"""

from __future__ import annotations

import copy
import hashlib
import json

TOKENS, INPUT_DIM, QUERY_HEADS, KV_HEADS, HEAD_DIM, LANES = 2, 5, 4, 2, 3, 2
INPUT_ZERO = -2
WEIGHTS = {
    "q": ((1, -2, 0, 3, -1), (-1, 1, 2, 0, 1), (2, 0, -1, 1, -2),
          (0, 3, -2, -1, 1), (1, 1, 1, -2, 0), (-2, 0, 3, 1, 1),
          (3, -1, 1, 0, -2), (-1, 2, -2, 1, 0), (2, 1, 0, -3, 1),
          (-2, 1, 3, 0, -1), (0, -2, 1, 2, 1), (1, 3, -1, -2, 0)),
    "k": ((-1, 2, 1, 0, -2), (2, -1, 0, 1, 3), (0, 1, -3, 2, 1),
          (1, -2, 2, 0, 3), (-3, 1, 1, 2, 0), (2, 0, -1, -2, 1)),
    "v": ((1, 0, -1, 2, 1), (-2, 3, 1, -1, 0), (3, -1, 2, 0, -2),
          (-1, 1, 3, -2, 0), (2, -3, 0, 1, 2), (0, 2, -2, 3, -1)),
}
BIASES = {"q": (-3, 1, 5, -1, 3, -5, 7, -7, 9, -9, 11, -11),
          "k": (2, -2, 6, 4, -6, 8), "v": (-1, 3, -3, 5, -5, 7)}
OUTPUT_ZEROS = {"q": 1, "k": -1, "v": 3}
OUTPUT_DENOMINATORS = {"q": 2, "k": 4, "v": 2}
OUTPUT_SCALE_DENOMINATORS = {"q": 4, "k": 2, "v": 4}
MODULES = {"q": "QueryProjection", "k": "KeyProjection", "v": "ValueProjection"}


def _tensor(shape: list[tuple[str, int]], zero: int, scale_denominator: int) -> dict:
    return {
        "shape": [{"axis": axis, "extent": extent} for axis, extent in shape],
        "element": {"kind": "sint", "width": 8},
        "quantization": {"kind": "affine", "granularity": "per_tensor",
                         "scale": {"numerator": 1, "denominator": scale_denominator},
                         "zero_point": zero, "range": {"min": -128, "max": 127}},
        "layout": {"order": [axis for axis, _ in shape], "lane_axis": shape[-1][0],
                   "lanes": LANES, "tail": "zero_pad_mask"},
        "sequence": {"kind": "dense", "frame_fact": "frame", "reset_fact": "reset"},
    }


def _signature(port_contracts: dict[str, tuple[str, str]], tensors: dict) -> dict:
    return {"parameters": {}, "domains": {"d": {"clock": "rising", "reset": {
        "kind": "sync", "polarity": "active_low"}}},
        "ports": {name: {"kind": "stream", "direction": direction, "protocol": "ready_valid_v1",
                         "domain": "d", "payload": {"kind": "tensor_beat", "contract": contract}}
                  for name, (direction, contract) in port_contracts.items()},
        "tensor_contracts": {name: copy.deepcopy(tensors[name])
                             for name in dict.fromkeys(contract for _, contract in port_contracts.values())}}


def signatures() -> tuple[dict, dict, dict[str, dict]]:
    tensors = {"X": _tensor([("T", TOKENS), ("C", INPUT_DIM)], INPUT_ZERO, 4)}
    for branch in MODULES:
        heads = QUERY_HEADS if branch == "q" else KV_HEADS
        tensors[branch.upper()] = _tensor([("T", TOKENS), ("H", heads), ("D", HEAD_DIM)],
                                         OUTPUT_ZEROS[branch], OUTPUT_SCALE_DENOMINATORS[branch])
    top = _signature({"rx": ("input", "X"), **{b: ("output", b.upper()) for b in MODULES}}, tensors)
    broadcast = _signature({"rx": ("input", "X"), **{b: ("output", "X") for b in MODULES}}, tensors)
    projections = {b: _signature({"rx": ("input", "X"), "tx": ("output", b.upper())}, tensors)
                   for b in MODULES}
    return top, broadcast, projections


def build_development_task() -> dict:
    signature, _, _ = signatures()
    asset = (json.dumps({"origin": "hand-authored synthetic development constants",
                         "weight_order": "output_head,head_dimension,input_channel",
                         "weights": WEIGHTS, "biases": BIASES},
                        sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    values = {
        "projection": {"operator": "independent_Q_K_V_linear_projections", "tokens": TOKENS,
                       "input_dim": INPUT_DIM, "query_heads": QUERY_HEADS, "kv_heads": KV_HEADS,
                       "head_dim": HEAD_DIM, "formula": "bias[o]+sum((input[c]+2)*weight[o,c])",
                       "weight_scale": [1, 2], "weight_zero_point": 0,
                       "bias_units": "centered product accumulator, added once before requantization",
                       "head_mapping": "Q has four heads; K and V each have two heads; no implicit KV duplication",
                       "scope": "projection only; no RoPE, normalization, attention or checkpoint weights"},
        "broadcast": {"copies": ["q", "k", "v"], "policy": "each input token delivered exactly once to each branch"},
        "numeric": {"input_scale": [1, 4], "input_zero": INPUT_ZERO,
                    "output_scale_denominators": OUTPUT_SCALE_DENOMINATORS,
                    "output_zeros": OUTPUT_ZEROS, "requantization_denominators": OUTPUT_DENOMINATORS,
                    "rounding": "signed exact nearest_even", "saturation": [-128, 127],
                    "accumulator": "signed_int32_without_overflow", "activation": "none"},
        "frame": {"input_beats": 6, "output_beats": {"q": 16, "k": 8, "v": 8},
                  "input_order": "T,C", "output_order": "T,H,D",
                  "next_input": "next invocation begins after all Q/K/V final output acceptances",
                  "streaming": "outputs may begin after their input token is accepted; output branches are independent",
                  "interleave": False, "tail": "each fastest-axis row uses its own zero-filled masked tail"},
        "stream": {"transfer": "rising-edge valid&&ready", "hold": "valid and all payload/mask bits stable during stall",
                   "independent_outputs": True, "invalid_lane": "raw0 and mask0, not an affine zero"},
        "reset": {"kind": "synchronous_active_low", "effect": "cancel current invocation and all pending branch tokens",
                  "output_valid": "all branches deassert following every reset edge"},
        "completion": {"max_cycles": 512, "from": "first input offer to final acceptance across all output branches",
                       "under_assumptions": ["environment"], "ii_requirement": "none"},
        "environment": {"source": "stable while stalled; at most two idle cycles between beats",
                        "sinks": "each output stalls at most two consecutive cycles; no invocation interleave"},
        "assets": {"qkv_weights": {"sha256": hashlib.sha256(asset).hexdigest(), "bytes": len(asset),
                                   "origin": "hand-authored synthetic constants", "license": "repository project terms",
                                   "format": "UTF-8 JSON signed decimal integers"}},
    }
    facts = {name: {"role": "assumption" if name == "environment" else "guarantee",
                    "required_mapping": name != "environment", "value": value}
             for name, value in values.items()}
    abi = {"domains": {"d": {"clock": "clk", "reset": "rst_n"}}, "ports": {
        "rx": {"payload": "in_payload", "valid": "in_valid", "ready": "in_ready"},
        **{b: {"payload": b + "_payload", "valid": b + "_valid", "ready": b + "_ready"} for b in MODULES}}}
    return {"task_id": "llm_qkv_development_t2_i5_h4_kv2_d3_v1", "family": "llm_quantized_qkv_projection",
            "development_only": True, "public_text": "Quantized decoder Q/K/V projections with distinct Q/KV head counts and independent output streams. Exact arithmetic, public synthetic assets and ABI are frozen below.",
            "boundary": {"contract_version": "development-public-boundary-v1", "validation_scope": "boundary_shape_only",
                         "boundary": {"rtl_top": "LlmQkvDev", "signature": signature,
                                      "parameter_values": {}, "abi": abi}},
            "facts": facts, "required_trace_facts": [name for name, fact in facts.items() if fact["required_mapping"]],
            "public_assets": {"qkv_weights": asset},
            "target_profile": {"contract_version": "pc21-development-target-v1", "target_id": "llm-qkv-generic-development-v1",
                               "language": "systemverilog", "synthesis_scope": "generic_yosys", "clock_period_ns": 10,
                               "tool_timeout_seconds": 60, "max_simulation_cycles": 10000},
            "capability_profile": {"contract_version": "pc21-development-capability-v1", "limits": {
                "max_instances": 32, "max_hierarchy_depth": 8, "max_width": 4096,
                "max_tensor_elements": 4096, "supported_reset_kinds": ["none", "sync"], "max_clock_domains": 1}}}


def reference_design() -> dict:
    _, broadcast, projections = signatures()

    def endpoint(instance: str, port: str) -> dict:
        return {"instance": instance, "port": port}

    def net(source: dict, sink: dict) -> dict:
        return {"source": {"kind": "endpoint", "endpoint": source}, "sinks": [sink]}

    modules = {"LlmQkvDev": {"signature": {"source": "requirement_boundary"}, "implementation": {
        "kind": "structural", "instances": {
            "broadcast": {"module": "InputBroadcast", "parameters": {}, "domains": {"d": "d"}},
            **{b: {"module": name, "parameters": {}, "domains": {"d": "d"}} for b, name in MODULES.items()}},
        "nets": {"input": net(endpoint("self", "rx"), endpoint("broadcast", "rx")),
                 **{b + "_input": net(endpoint("broadcast", b), endpoint(b, "rx")) for b in MODULES},
                 **{b + "_output": net(endpoint(b, "tx"), endpoint("self", b)) for b in MODULES}}}},
        "InputBroadcast": {"signature": {"source": "declared", **broadcast}, "implementation": {
            "kind": "behavioral", "execution": "clocked", "intent": "Exactly-once broadcast with independent branch backpressure",
            "tensor_rules": {"broadcast": {"kind": "fork", "fact": "broadcast", "input": "rx", "outputs": list(MODULES)}}}}}
    for branch, name in MODULES.items():
        modules[name] = {"signature": {"source": "declared", **projections[branch]}, "implementation": {
            "kind": "behavioral", "execution": "clocked", "intent": "Centered INT8 linear projection with public weights, signed RNE and saturation",
            "tensor_rules": {"projection": {"kind": "compute", "fact": "projection", "inputs": ["rx"], "outputs": ["tx"]}}}}
    return {"entry": "LlmQkvDev", "modules": modules,
            "requirement_map": [{"fact": fact, "targets": [{"kind": "module", "module": "LlmQkvDev"}]}
                                for fact in build_development_task()["required_trace_facts"]]}
