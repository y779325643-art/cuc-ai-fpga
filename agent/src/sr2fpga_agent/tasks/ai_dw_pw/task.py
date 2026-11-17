"""Public meaning and assets, separate from evaluator inputs and expected values."""

from __future__ import annotations

import copy
import hashlib
import json

HEIGHT, WIDTH, CIN, COUT, LANES = 4, 5, 3, 5, 2
INPUT_ZERO, MID_ZERO = -3, 2
OUTPUT_ZEROS = (-5, 7, -9, 3, -2)
OUTPUT_DENOMINATORS = (4, 8, 2, 4, 8)
DW_WEIGHTS = (
    ((1, -1, 2), (0, 3, -2), (1, 0, -1)),
    ((-2, 1, 0), (2, -1, 1), (0, 1, 2)),
    ((1, 2, -1), (-1, 1, 0), (2, -2, 1)),
)
DW_BIAS = (-5, 3, 1)
PW_WEIGHTS = ((1, -2, 3), (-3, 1, 2), (2, 2, -1), (1, 0, -2), (-2, 3, 1))
PW_BIAS = (-7, 5, 1, -3, 9)


def _tensor(channels: int, quantization: dict) -> dict:
    return {
        "shape": [{"axis": a, "extent": n} for a, n in
                  (("N", 1), ("H", HEIGHT), ("W", WIDTH), ("C", channels))],
        "element": {"kind": "sint", "width": 8},
        "quantization": quantization,
        "layout": {"order": ["N", "H", "W", "C"], "lane_axis": "C",
                   "lanes": LANES, "tail": "zero_pad_mask"},
        "sequence": {"kind": "dense", "frame_fact": "frame", "reset_fact": "reset"},
    }


def _quant(zero: int, denominator: int) -> dict:
    return {"kind": "affine", "granularity": "per_tensor",
            "scale": {"numerator": 1, "denominator": denominator}, "zero_point": zero,
            "range": {"min": -128, "max": 127}}


def signatures() -> tuple[dict, dict, dict]:
    output_q = {"kind": "affine", "granularity": "per_axis", "axis": "C",
                "scales": [{"numerator": 1, "denominator": d} for d in (4, 2, 8, 4, 2)],
                "zero_points": list(OUTPUT_ZEROS), "range": {"min": -128, "max": 127}}
    tensors = {"input_tensor": _tensor(CIN, _quant(INPUT_ZERO, 4)),
               "mid_tensor": _tensor(CIN, _quant(MID_ZERO, 4)),
               "output_tensor": _tensor(COUT, output_q)}

    def signature(rx: str, tx: str) -> dict:
        return {"parameters": {}, "domains": {"d": {"clock": "rising", "reset": {
            "kind": "sync", "polarity": "active_low"}}}, "ports": {
                name: {"kind": "stream", "direction": direction,
                       "protocol": "ready_valid_v1", "payload": {
                           "kind": "tensor_beat", "contract": contract}, "domain": "d"}
                for name, direction, contract in (("rx", "input", rx), ("tx", "output", tx))},
            "tensor_contracts": {k: copy.deepcopy(tensors[k]) for k in dict.fromkeys((rx, tx))}}
    return (signature("input_tensor", "output_tensor"),
            signature("input_tensor", "mid_tensor"), signature("mid_tensor", "output_tensor"))


def build_development_task() -> dict:
    """Return public data only. Oracle, test frames and expected values are absent.

    The engineering profile is deliberately fixed, development-only and exposed.
    The existing boundary wrapper remains shape-only; task readiness is not inferred.
    """
    signature, _, _ = signatures()
    assets = {"dw_pw_weights": (json.dumps({"dw_order": "C,KH,KW", "pw_order": "Cout,Cin",
              "dw_weights": DW_WEIGHTS, "dw_bias": DW_BIAS,
              "pw_weights": PW_WEIGHTS, "pw_bias": PW_BIAS},
              sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")}
    facts_values = {
        "compute": {"operator": "DW3x3_requant_relu_PW1x1", "convolution": "cross_correlation",
                    "padding": "SAME", "stride": 1, "depth_multiplier": 1,
                    "shape": [1, HEIGHT, WIDTH, CIN], "output_channels": COUT,
                    "dw_formula": "bias[c]+sum((input[n,h+kh-1,w+kw-1,c]+3)*dw[c,kh,kw])",
                    "padding_raw": INPUT_ZERO, "accumulator": "signed_int32_no_overflow",
                    "dw_weight_scale": [1, 2], "pw_weight_scale": [1, 4], "weight_zero_point": 0,
                    "bias_units": "the corresponding centered product accumulator units"},
        "numeric": {"input_scale": [1, 4], "input_zero": INPUT_ZERO, "mid_scale": [1, 4],
                    "mid_zero": MID_ZERO, "mid": "max(2,sat_int8(nearest_even(dw_acc/2)+2))",
                    "pw_formula": "pw_bias[o]+sum((mid[c]-2)*pw[o,c])",
                    "output": "sat_int8(nearest_even(pw_acc/output_denominator[o])+output_zero[o])",
                    "output_denominators": list(OUTPUT_DENOMINATORS), "output_zeros": list(OUTPUT_ZEROS),
                    "output_activation": "none", "rounding": "nearest_even_signed_exact_rational",
                    "saturation": [-128, 127], "bias_before_requantization": True},
        "frame": {"input_beats": 40, "output_beats": 60, "interleave": False,
                  "next_input": "after previous final output acceptance; earlier in_ready may remain low",
                  "order": "N,H,W,C; lane0 at LSB, mask[j] at bit16+j; invalid lanes raw0/mask0",
                  "valid_raw_zero": "affine raw0 is not padding or invalid lane"},
        "reset": {"kind": "synchronous_active_low", "effect": "cancel all pending work/output; restart at first input beat",
                  "output_valid": "must be 0 following every reset edge"},
        "stream": {"transfer": "rising-edge valid&&ready", "hold": "valid and complete payload stable while stalled",
                   "masks": "each pixel: input 3 then1, output3 then3 then1"},
        "completion": {"max_cycles": 2048, "from": "first input offer to final output acceptance",
                       "under_assumptions": ["environment"], "ii_requirement": "none"},
        "environment": {"source": "stable until acceptance; pause at most2 consecutive cycles",
                        "sink": "stall at most2 consecutive offered-valid cycles; no cross-invocation interleave"},
        "assets": {k: {"sha256": hashlib.sha256(v).hexdigest(), "bytes": len(v),
                       "origin": "hand-authored nondegenerate development constants", "license": "repository project terms",
                       "format": "UTF-8 JSON signed decimal integers"} for k, v in assets.items()},
    }
    facts = {name: {"role": "assumption" if name == "environment" else "guarantee",
                    "required_mapping": name != "environment", "value": value}
             for name, value in facts_values.items()}
    boundary = {"contract_version": "development-public-boundary-v1", "validation_scope": "boundary_shape_only",
                "boundary": {"rtl_top": "AiDwPwDev", "signature": signature, "parameter_values": {},
                "abi": {"domains": {"d": {"clock": "clk", "reset": "rst_n"}}, "ports": {
                    "rx": {"payload": "in_payload", "valid": "in_valid", "ready": "in_ready"},
                    "tx": {"payload": "out_payload", "valid": "out_valid", "ready": "out_ready"}}}}}
    return {"task_id": "ai_dw_pw_development_4x5_c3_c5_v1", "family": "ai_dw_pw_block",
            "development_only": True, "boundary": boundary, "facts": facts,
            "required_trace_facts": [k for k, v in facts.items() if v["required_mapping"]],
            "public_text": "Fixed development DW→requant/ReLU→PW task. Exact algorithm, ABI, assets and environment are in facts and boundary; internal decomposition is free.",
            "public_assets": assets,
            "target_profile": {"id": "generic_synth_development", "clock_period_ns": 10,
                               "physical_implementation": "not_requested"},
            "capability_profile": {"id": "pc21_dw_pw_development_v1", "max_elements": 1024,
                                   "max_lanes": 2, "max_width": 32, "max_instances": 16}}


def reference_design() -> dict:
    """Hand-authored control PC, never represented as a candidate/model result."""
    _, dw_signature, pw_signature = signatures()
    def ep(instance: str, port: str) -> dict:
        return {"instance": instance, "port": port}
    def net(source: dict, sink: dict) -> dict:
        return {"source": {"kind": "endpoint", "endpoint": source}, "sinks": [sink]}
    return {"entry": "AiDwPwDev", "modules": {
        "AiDwPwDev": {"signature": {"source": "requirement_boundary"}, "implementation": {
            "kind": "structural", "instances": {
                "dw": {"module": "DepthwiseStage", "parameters": {}, "domains": {"d": "d"}},
                "pw": {"module": "PointwiseStage", "parameters": {}, "domains": {"d": "d"}}},
            "nets": {"input": net(ep("self", "rx"), ep("dw", "rx")),
                     "intermediate": net(ep("dw", "tx"), ep("pw", "rx")),
                     "output": net(ep("pw", "tx"), ep("self", "tx"))}}},
        "DepthwiseStage": {"signature": {"source": "declared", **dw_signature}, "implementation": {
            "kind": "behavioral", "execution": "clocked", "intent": "DW 3x3 SAME cross-correlation, signed nearest-even requant, saturation then ReLU; fixed public assets.",
            "tensor_rules": {"compute": {"kind": "compute", "fact": "compute", "inputs": ["rx"], "outputs": ["tx"]}}}},
        "PointwiseStage": {"signature": {"source": "declared", **pw_signature}, "implementation": {
            "kind": "behavioral", "execution": "clocked", "intent": "PW 1x1 centered MAC with distinct output-channel scales and zero-points, signed nearest-even requant and saturation.",
            "tensor_rules": {"compute": {"kind": "compute", "fact": "compute", "inputs": ["rx"], "outputs": ["tx"]}}}}},
        "requirement_map": [{"fact": fact, "targets": [{"kind": "module", "module": "AiDwPwDev"}]}
                            for fact in build_development_task()["required_trace_facts"]]}
