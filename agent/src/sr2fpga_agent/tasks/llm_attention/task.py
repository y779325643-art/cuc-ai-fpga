"""Public fixed-profile GQA semantics; evaluator inputs and answers stay separate."""

from __future__ import annotations

import copy
import hashlib
import json

QUERY_HEADS, KV_HEADS, HEAD_DIM, MAX_CONTEXT, LANES = 4, 2, 3, 4, 2
SCORE_NUMERATOR, SCORE_DENOMINATOR, SCORE_LIMIT = 37, 1024, 8
EXP_LUT = (256, 199, 155, 121, 94, 73, 57, 44, 35, 27, 21, 16, 13, 10, 8, 6, 5)
COMPLETION_CYCLES = 256
MAX_SIMULATION_CYCLES = 4000


def _tensor(heads: int, denominator: int) -> dict:
    return {
        "shape": [{"axis": "H", "extent": heads}, {"axis": "D", "extent": HEAD_DIM}],
        "element": {"kind": "sint", "width": 8},
        "quantization": {"kind": "affine", "granularity": "per_tensor",
                         "scale": {"numerator": 1, "denominator": denominator},
                         "zero_point": 0, "range": {"min": -128, "max": 127}},
        "layout": {"order": ["H", "D"], "lane_axis": "D", "lanes": LANES,
                   "tail": "zero_pad_mask"},
        "sequence": {"kind": "dense", "frame_fact": "frame", "reset_fact": "reset"},
    }


def signature() -> dict:
    tensors = {"Query": _tensor(QUERY_HEADS, 8), "Key": _tensor(KV_HEADS, 8),
               "Value": _tensor(KV_HEADS, 4), "Context": _tensor(QUERY_HEADS, 4)}
    return {"parameters": {}, "domains": {"d": {"clock": "rising", "reset": {
        "kind": "sync", "polarity": "active_low"}}}, "tensor_contracts": tensors,
        "ports": {name: {"kind": "stream", "direction": direction,
                         "protocol": "ready_valid_v1", "domain": "d",
                         "payload": {"kind": "tensor_beat", "contract": contract}}
                  for name, direction, contract in (("q", "input", "Query"),
                      ("k", "input", "Key"), ("v", "input", "Value"),
                      ("context", "output", "Context"))}}


def build_development_task() -> dict:
    """Return public data only; this is a synthetic engineering profile."""
    assets = {"attention_exp_lut": (json.dumps({"delta_min": 0, "delta_max": 16,
        "values": EXP_LUT, "interpretation": "integer approximation to 256*exp(-delta/4)"},
        sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")}
    values = {
        "compute": {"operator": "stateful_grouped_query_decode_attention",
                    "query_heads": QUERY_HEADS, "kv_heads": KV_HEADS, "head_dimension": HEAD_DIM,
                    "head_mapping": "kv_head=floor(query_head/(query_heads/kv_heads))",
                    "order": "collect Q,K,V; atomically append K,V; attend over all valid cached tokens including the new token",
                    "causal_scope": "only accepted past and current tokens; no future token exists in the cache"},
        "numeric": {"query_key_scale": [1, 8], "value_context_scale": [1, 4],
                    "zero_points": 0, "raw_range": [-128, 127],
                    "inverse_sqrt_dimension_approximation": [37, 64],
                    "score_grid": [1, 4], "score_index": "clip(RNE(dot(Q,K)*37/1024),-8,8)",
                    "weight": "EXP_LUT[max_score_index-score_index]",
                    "context_raw": "sat_int8(RNE(sum(weight*cached_V)/sum(weight)))",
                    "rounding": "signed exact rational nearest-even",
                    "probability_quantization": "none; normalize the final integer weighted sum once",
                    "profile_scope": "frozen quantized engineering approximation, not exact real softmax or a model-quality claim"},
        "cache": {"capacity_tokens": MAX_CONTEXT, "initial_valid_length": 0,
                  "append": "one token per complete Q/K/V invocation, committed only after all three inputs are accepted",
                  "persistence": "all previous K/V survive successive decode invocations until reset",
                  "full": "all input ready signals remain low after the fourth invocation until reset",
                  "storage_reset": "logical invalidation by valid_length=0; no physical memory clearing requirement"},
        "frame": {"q_beats": 8, "k_beats": 4, "v_beats": 4, "context_beats": 8,
                  "order": "head-major then D; each head is padded independently; masks 3,1",
                  "next_invocation": "no new input invocation before previous final context beat is accepted",
                  "input_order": "the three complete input streams may arrive in any order; no invocation interleaving"},
        "stream": {"transfer": "rising-edge valid&&ready", "hold": "valid and complete payload stable while stalled",
                   "tail": "invalid lane has raw bits zero and mask zero; valid raw zero is a numerical zero"},
        "reset": {"kind": "synchronous_active_low", "effect": "cancel partial input and output, invalidate the entire KV cache",
                  "output_valid": "zero following every reset edge"},
        "completion": {"max_cycles": COMPLETION_CYCLES, "from": "first Q/K/V input offer to last context acceptance",
                       "under_assumptions": ["environment"]},
        "environment": {"capacity": "at most four completed append/decode invocations between resets",
                        "source": "stable until accepted, with at most two idle cycles between beats and streams",
                        "sink": "at most two consecutive stalled offered-valid cycles",
                        "interleave": False},
        "assets": {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                          "origin": "public hand-specified integer exp approximation table",
                          "format": "UTF-8 JSON integers"} for name, data in assets.items()},
    }
    facts = {name: {"role": "assumption" if name == "environment" else "guarantee",
                    "required_mapping": name != "environment", "value": value}
             for name, value in values.items()}
    return {"task_id": "llm_gqa_decode_h4_kv2_d3_t4_v1", "family": "llm_kv_cache_decode_attention",
            "development_only": True,
            "boundary": {"contract_version": "development-public-boundary-v1", "validation_scope": "boundary_shape_only",
                "boundary": {"rtl_top": "LlmAttentionDev", "signature": signature(), "parameter_values": {},
                    "abi": {"domains": {"d": {"clock": "clk", "reset": "rst_n"}}, "ports": {
                        name: {"payload": name + "_payload", "valid": name + "_valid", "ready": name + "_ready"}
                        for name in ("q", "k", "v", "context")}}}},
            "facts": facts, "required_trace_facts": [name for name, fact in facts.items() if fact["required_mapping"]],
            "public_text": "Fixed synthetic quantized GQA decode with a real persistent append-only KV cache. Exact approximation, ABI, append/reset and environment semantics are public facts.",
            "public_assets": assets,
            "target_profile": {"contract_version": "pc21-development-target-v1", "target_id": "llm-attention-generic-yosys-v1",
                "language": "systemverilog", "synthesis_scope": "generic_yosys", "clock_period_ns": 10,
                "tool_timeout_seconds": 60, "max_simulation_cycles": MAX_SIMULATION_CYCLES},
            "capability_profile": {"contract_version": "pc21-development-capability-v1", "limits": {
                "max_instances": 64, "max_hierarchy_depth": 16, "max_width": 4096,
                "max_tensor_elements": 4096, "supported_reset_kinds": ["none", "sync"], "max_clock_domains": 1}}}


def reference_design() -> dict:
    """Hand-authored PC control, not a candidate model artifact."""
    def endpoint(owner: str, port: str) -> dict:
        return {"instance": owner, "port": port}
    def net(source: str, sink: str, port: str) -> dict:
        return {"source": {"kind": "endpoint", "endpoint": endpoint(source, port)},
                "sinks": [endpoint(sink, port)]}
    states = {"validLength": {"kind": "register", "domain": "d", "type": {"kind": "uint", "width": 3},
                               "reset": {"kind": "value", "raw_value": 0}}}
    for name in ("keyCache", "valueCache"):
        states[name] = {"kind": "memory", "domain": "d", "element_type": {"kind": "sint", "width": 8},
                        "depth": MAX_CONTEXT * KV_HEADS * HEAD_DIM, "organization": "simple_dual_port", "read_latency_cycles": 0,
                        "read_during_write": "forbidden", "initialization": {"kind": "none"}, "reset_contents": "preserve"}
    return {"entry": "LlmAttentionDev", "modules": {
        "LlmAttentionDev": {"signature": {"source": "requirement_boundary"}, "implementation": {
            "kind": "structural", "instances": {"attention": {"module": "CachedDecodeAttention", "parameters": {}, "domains": {"d": "d"}}},
            "nets": {**{name: net("self", "attention", name) for name in ("q", "k", "v")},
                     "context": net("attention", "self", "context")}}},
        "CachedDecodeAttention": {"signature": {"source": "declared", **copy.deepcopy(signature())}, "implementation": {
            "kind": "behavioral", "execution": "clocked", "intent": "Persist and append GQA K/V; scaled integer QK, stable max-subtracted public exp LUT and exact-ratio AV; reset invalidates cache.",
            "states": states, "tensor_rules": {"decode": {"kind": "compute", "fact": "compute", "inputs": ["q", "k", "v"], "outputs": ["context"]}}}}},
        "requirement_map": [{"fact": fact, "targets": [{"kind": "module", "module": "CachedDecodeAttention"}]}
                            for fact in build_development_task()["required_trace_facts"]]}
