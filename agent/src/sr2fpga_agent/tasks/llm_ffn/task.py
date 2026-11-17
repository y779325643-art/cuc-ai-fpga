"""Candidate-visible synthetic gated-FFN meaning and immutable public assets."""

from __future__ import annotations

import copy
import hashlib
import json

TOKENS, DIN, DFF, LANES = 2, 5, 7, 2
INPUT_BEATS = OUTPUT_BEATS = 6
COMPLETION_CYCLES = 512
GATE_WEIGHTS = ((1,-2,1,0,2),(-1,1,2,-2,0),(2,0,-1,1,-2),(0,2,-2,1,1),
                (-2,1,0,2,-1),(1,1,-1,-1,2),(-1,-2,2,0,1))
UP_WEIGHTS = ((-1,2,0,1,1),(2,-1,1,0,-2),(1,1,-2,2,0),(-2,0,1,1,2),
              (0,-2,2,-1,1),(2,1,0,-2,1),(1,-1,2,1,-2))
DOWN_WEIGHTS = ((1,-2,0,1,2,-1,1),(-1,1,2,0,-2,1,2),(2,0,-1,2,1,-2,1),
                (0,2,-2,1,-1,1,2),(-2,1,1,-1,2,0,-1))
GATE_BIAS = (1,-3,5,-1,3,-5,7)
UP_BIAS = (-2,4,1,-3,5,2,-4)
DOWN_BIAS = (3,-1,5,-5,1)
# Frozen code-space table: q=-128..127, output approximates 4*SiLU(q/4).
# Generated once with Decimal precision 70 and ROUND_HALF_EVEN, then retained as
# exact public integers. Runtime evaluation never calls exp or floating point.
SILU_LUT = (
    (0,) * 116 + (-1,) * 11 + (0, 0, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                              13, 14, 15, 16, 17, 18, 19, 20)
    + tuple(range(21, 128))
)


def _tensor(channels: int) -> dict:
    return {"shape": [{"axis": "T", "extent": TOKENS}, {"axis": "C", "extent": channels}],
            "element": {"kind": "sint", "width": 8},
            "quantization": {"kind": "affine", "granularity": "per_tensor",
                             "scale": {"numerator": 1, "denominator": 4},
                             "zero_point": 0, "range": {"min": -128, "max": 127}},
            "layout": {"order": ["T", "C"], "lane_axis": "C", "lanes": LANES,
                       "tail": "zero_pad_mask"},
            "sequence": {"kind": "dense", "frame_fact": "frame", "reset_fact": "reset"}}


def _signature(ports: tuple[tuple[str, str, str], ...]) -> dict:
    tensors = {"hidden": _tensor(DIN), "expanded": _tensor(DFF)}
    return {"parameters": {}, "domains": {"d": {"clock": "rising", "reset": {
        "kind": "sync", "polarity": "active_low"}}}, "ports": {
            name: {"kind": "stream", "direction": direction, "protocol": "ready_valid_v1",
                   "payload": {"kind": "tensor_beat", "contract": tensor}, "domain": "d"}
            for name, direction, tensor in ports},
            "tensor_contracts": {name: copy.deepcopy(tensors[name]) for name in dict.fromkeys(
                tensor for _, _, tensor in ports)}}


def signatures() -> dict[str, dict]:
    return {
        "top": _signature((("rx", "input", "hidden"), ("tx", "output", "hidden"))),
        "fork": _signature((("rx", "input", "hidden"), ("features", "output", "hidden"),
                             ("residual", "output", "hidden"))),
        "project": _signature((("rx", "input", "hidden"), ("gate", "output", "expanded"),
                                ("up", "output", "expanded"))),
        "fuse": _signature((("gate", "input", "expanded"), ("up", "input", "expanded"),
                             ("residual", "input", "hidden"), ("tx", "output", "hidden"))),
    }


def build_development_task() -> dict:
    """Public problem only; no evaluator inputs, expected outputs or harness."""
    asset = (json.dumps({"matrix_order": "output_channel,input_channel",
                         "gate_weights": GATE_WEIGHTS, "up_weights": UP_WEIGHTS,
                         "down_weights": DOWN_WEIGHTS, "gate_bias": GATE_BIAS,
                         "up_bias": UP_BIAS, "down_bias": DOWN_BIAS,
                         "silu_lut_input_codes": [-128, 127], "silu_lut": SILU_LUT},
                        sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    values = {
        "compute": {"operator": "quantized_gated_ffn_with_residual", "tokens": TOKENS,
                    "hidden_size": DIN, "intermediate_size": DFF,
                    "input_boundary": "already-normalized hidden state; normalization is external",
                    "gate_up": "g/u=sat8(RNE((bias+sum(x*w))/4))",
                    "activation": "a=SILU_LUT[g+128]; frozen table is exact task semantics",
                    "gate_product": "z=sat8(RNE(a*u/4))",
                    "down_residual": "y=sat8(RNE((down_bias+sum(z*down_weight))/4)+x)",
                    "bias_position": "once, before projection requantization",
                    "model_scope": "synthetic integer engineering profile; not checkpoint or language quality"},
        "numeric": {"element": "signed INT8", "all_activation_scale": [1, 4],
                    "all_zero_points": 0, "weight_scale": [1, 4],
                    "accumulator": "signed INT32 without overflow", "rounding": "signed_nearest_even",
                    "saturation": [-128, 127], "residual": "same token and channel after down requant"},
        "activation": {"kind": "public_SiLU_lookup_approximation", "entries": 256,
                       "index": "signed gate code+128", "input_output_scale": [1, 4],
                       "origin": "Decimal precision70, round-half-even, frozen integer codes",
                       "claim": "table equivalence only; no approximation-error or model-quality claim"},
        "frame": {"input_beats": INPUT_BEATS, "output_beats": OUTPUT_BEATS,
                  "order": "T then C; lane0 LSB; masks11,11,01 for each hidden token",
                  "streaming": "outputs may start after each complete input token; full-frame buffering is not required",
                  "interleave": False, "next_input": "after final output acceptance"},
        "stream": {"transfer": "rising-edge valid&&ready",
                   "hold": "valid and all payload bits stable while stalled",
                   "invalid_lanes": "raw0 with mask0; per-token tail restarts"},
        "reset": {"kind": "synchronous_active_low", "effect": "cancel all partial and pending work",
                  "output_valid": "0 after reset edge; next invocation begins at token0/channel0"},
        "completion": {"max_cycles": COMPLETION_CYCLES,
                       "from": "first input offer to final output acceptance",
                       "under_assumptions": ["environment"]},
        "environment": {"source": "stable until accepted; at most2 consecutive pause cycles",
                        "sink": "normal completing invocations: at most2 consecutive offered-valid stalls; no interleave",
                        "reset_probe": "a subsequently reset-cancelled invocation may be output-stalled until reset; completion is not demanded for cancelled work"},
        "assets": {"ffn_constants": {"sha256": hashlib.sha256(asset).hexdigest(),
                                      "size_bytes": len(asset), "origin": "repository synthetic constants"}},
    }
    facts = {name: {"role": "assumption" if name == "environment" else "guarantee",
                    "required_mapping": name != "environment", "value": value}
             for name, value in values.items()}
    boundary = {"contract_version": "development-public-boundary-v1",
                "validation_scope": "boundary_shape_only", "boundary": {
                    "rtl_top": "LlmGatedFfnDev", "signature": signatures()["top"],
                    "parameter_values": {}, "abi": {"domains": {"d": {"clock": "clk", "reset": "rst_n"}},
                        "ports": {"rx": {"payload": "in_payload", "valid": "in_valid", "ready": "in_ready"},
                                  "tx": {"payload": "out_payload", "valid": "out_valid", "ready": "out_ready"}}}}}
    return {"task_id": "llm_gated_ffn_development_t2_d5_f7_v1", "family": "llm_gated_ffn",
            "development_only": True, "boundary": boundary, "facts": facts,
            "required_trace_facts": [name for name, fact in facts.items() if fact["required_mapping"]],
            "public_text": "Quantized LLM gated FFN: gate/up projections, frozen SiLU LUT, product, down projection and residual. Exact public facts/assets define all arithmetic; normalization is outside the boundary.",
            "public_assets": {"ffn_constants": asset},
            "target_profile": {"contract_version": "pc21-development-target-v1",
                               "target_id": "generic_yosys_llm_ffn_development", "language": "systemverilog",
                               "synthesis_scope": "generic_yosys", "clock_period_ns": 10,
                               "tool_timeout_seconds": 60, "max_simulation_cycles": 4000},
            "capability_profile": {"contract_version": "pc21-development-capability-v1", "limits": {
                "max_instances": 64, "max_hierarchy_depth": 16, "max_width": 4096,
                "max_tensor_elements": 4096, "supported_reset_kinds": ["none", "sync"],
                "max_clock_domains": 1}}}


def reference_design() -> dict:
    """Explicit hand-authored structural control; internal decomposition is free."""
    sig = signatures()
    def net(source: str, source_port: str, sink: str, sink_port: str) -> dict:
        return {"source": {"kind": "endpoint", "endpoint": {"instance": source, "port": source_port}},
                "sinks": [{"instance": sink, "port": sink_port}]}
    modules = {"LlmGatedFfnDev": {"signature": {"source": "requirement_boundary"}, "implementation": {
        "kind": "structural", "instances": {
            name: {"module": module, "parameters": {}, "domains": {"d": "d"}}
            for name, module in (("fork", "FfnInputFork"), ("project", "FfnGateUp"),
                                 ("fuse", "FfnFuseDownResidual"))}, "nets": {
                "input": net("self", "rx", "fork", "rx"),
                "features": net("fork", "features", "project", "rx"),
                "residual": net("fork", "residual", "fuse", "residual"),
                "gate": net("project", "gate", "fuse", "gate"),
                "up": net("project", "up", "fuse", "up"),
                "output": net("fuse", "tx", "self", "tx")}}}}
    for module, key, inputs, outputs in (
            ("FfnInputFork", "fork", ["rx"], ["features", "residual"]),
            ("FfnGateUp", "project", ["rx"], ["gate", "up"]),
            ("FfnFuseDownResidual", "fuse", ["gate", "up", "residual"], ["tx"])):
        rule = ({"kind": "fork", "fact": "frame", "input": "rx", "outputs": outputs}
                if key == "fork" else {"kind": "compute", "fact": "compute", "inputs": inputs, "outputs": outputs})
        modules[module] = {"signature": {"source": "declared", **sig[key]}, "implementation": {
            "kind": "behavioral", "execution": "clocked", "intent": module + " exact public arithmetic and ordered transactions",
            "tensor_rules": {"main": rule}}}
    return {"entry": "LlmGatedFfnDev", "modules": modules,
            "requirement_map": [{"fact": fact, "targets": [{"kind": "module", "module": "LlmGatedFfnDev"}]}
                                for fact in build_development_task()["required_trace_facts"]]}
