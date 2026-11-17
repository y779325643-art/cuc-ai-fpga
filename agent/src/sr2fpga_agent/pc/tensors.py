"""Configuration-local tensor descriptors and finite declared relationships.

These checks do not execute kernels or manufacture an oracle from model intent.
"""

from __future__ import annotations

from copy import deepcopy
from math import gcd
from typing import Any, Callable, Mapping

from .expressions import evaluate, natural
from .semantics import PcSemanticError


def _require(condition: bool, path: str, message: str) -> None:
    if not condition:
        raise PcSemanticError(f"{path}: {message}")


def storage_range(element: Mapping[str, Any]) -> tuple[int, int]:
    width = element["width"]
    if element["kind"] == "sint":
        return -(1 << (width - 1)), (1 << (width - 1)) - 1
    return 0, (1 << width) - 1


def resolve_tensor(contract: Mapping[str, Any], parameters: Mapping[str, int],
                   path: str, fact: Callable[[str, str, str], None],
                   *, max_elements: int, max_width: int) -> dict[str, Any]:
    """Canonicalize axes by name, retaining explicit traversal and sequence."""
    result = deepcopy(dict(contract))
    shape: dict[str, int] = {}
    elements = 1
    for i, axis in enumerate(contract["shape"]):
        _require(axis["axis"] not in shape, path + ".shape", "duplicate tensor axis")
        extent = evaluate(axis["extent"], parameters, f"{path}.shape[{i}].extent")
        natural(extent, path + ".shape", positive=True)
        shape[axis["axis"]] = extent
        elements *= extent
        _require(elements <= max_elements, path + ".shape", "tensor element limit exceeded")
    result["shape"] = [{"axis": axis, "extent": shape[axis]} for axis in sorted(shape)]
    width = evaluate(contract["element"]["width"], parameters, path + ".element.width")
    _require(1 <= width <= 32, path + ".element.width", "tensor width must be 1..32")
    result["element"]["width"] = width
    quant = result["quantization"]
    low, high = storage_range(result["element"])
    if quant["kind"] == "affine":
        qlow, qhigh = quant["range"]["min"], quant["range"]["max"]
        _require(low <= qlow <= qhigh <= high, path + ".quantization.range",
                 "code range is not representable")
        if quant["granularity"] == "per_axis":
            axis = quant["axis"]
            _require(axis in shape, path + ".quantization.axis", "unknown quantization axis")
            _require(len(quant["scales"]) == len(quant["zero_points"]) == shape[axis],
                     path + ".quantization", "per-axis table length must equal logical extent")
            scales, zeros = quant["scales"], quant["zero_points"]
        else:
            scales, zeros = [quant["scale"]], [quant["zero_point"]]
        for scale in scales:
            numerator = natural(scale["numerator"], path + ".quantization.scale", positive=True)
            denominator = natural(scale["denominator"], path + ".quantization.scale", positive=True)
            _require(gcd(numerator, denominator) == 1, path + ".quantization.scale",
                     "scale must be a reduced rational")
        _require(all(type(zero) is int and qlow <= zero <= qhigh for zero in zeros),
                 path + ".quantization.zero_point", "zero-point outside code range")
    layout = result["layout"]
    order = layout["order"]
    _require(len(order) == len(shape) and set(order) == set(shape), path + ".layout.order",
             "layout order must be an exact axis permutation")
    _require(layout["lane_axis"] == order[-1], path + ".layout.lane_axis",
             "lane axis must be the fastest axis")
    lanes = evaluate(layout["lanes"], parameters, path + ".layout.lanes")
    natural(lanes, path + ".layout.lanes", positive=True)
    layout["lanes"] = lanes
    fastest = shape[layout["lane_axis"]]
    if layout["tail"] == "exact":
        _require(fastest % lanes == 0, path + ".layout.tail", "exact lanes must divide axis extent")
    beat_bits = lanes * width + (lanes if layout["tail"] == "zero_pad_mask" else 0)
    _require(beat_bits <= max_width, path + ".layout", "tensor beat width limit exceeded")
    sequence = result["sequence"]
    for key in ("frame_fact", "reset_fact"):
        fact(sequence[key], "guarantee", path + ".sequence." + key)
    groups = 1
    if sequence["kind"] == "partial_sum":
        _require(sequence["reduction_axis"] not in shape, path + ".sequence.reduction_axis",
                 "reduction axis must differ from output axes")
        groups = evaluate(sequence["groups"], parameters, path + ".sequence.groups")
        natural(groups, path + ".sequence.groups", positive=True)
        sequence["groups"] = groups
    dense_beats = (elements // fastest) * ((fastest + lanes - 1) // lanes)
    natural(dense_beats * groups, path + ".sequence.beats_per_invocation", positive=True)
    result["derived"] = {"elements": elements, "lane_bits": lanes * width,
                         "mask_bits": beat_bits - lanes * width, "beat_bits": beat_bits,
                         "dense_beats": dense_beats, "dense_beats_per_invocation": dense_beats,
                         "beats_per_invocation": dense_beats * groups}
    return result


def _equivalent(a: dict[str, Any], b: dict[str, Any], omit: set[str]) -> bool:
    return {k: v for k, v in a.items() if k not in omit | {"derived"}} == {
        k: v for k, v in b.items() if k not in omit | {"derived"}}


def _zero_points(tensor: dict[str, Any]) -> list[int]:
    q = tensor["quantization"]
    if q["kind"] == "integer":
        return [0]
    return [q["zero_point"]] if q["granularity"] == "per_tensor" else q["zero_points"]


def check_tensor_rules(implementation: Mapping[str, Any], ports: Mapping[str, Any],
                       port_types: Mapping[str, Any], states: Mapping[str, Any], path: str,
                       fact: Callable[[str, str, str], None]) -> tuple[dict[str, Any], ...]:
    tensor_ports = {name for name, payload in port_types.items() if payload["kind"] == "tensor_beat"}
    used: set[str] = set()
    obligations: list[dict[str, Any]] = []

    def tensor(name: str, direction: str, rule_path: str) -> dict[str, Any]:
        _require(name in tensor_ports, rule_path, f"unknown tensor port {name}")
        _require(ports[name]["direction"] == direction, rule_path, f"wrong direction for {name}")
        return port_types[name]["descriptor"]

    for name, rule in sorted(implementation.get("tensor_rules", {}).items()):
        p = path + ".tensor_rules." + name
        fact(rule["fact"], "guarantee", p + ".fact")
        ins = rule.get("inputs", [rule["input"]] if "input" in rule else [])
        outs = rule.get("outputs", [rule["output"]] if "output" in rule else [])
        names = ins + outs
        _require(len(set(names)) == len(names), p, "duplicate tensor relation port")
        _require(not used.intersection(names), p, "tensor port belongs to more than one main relation")
        inputs = [tensor(port, "input", p) for port in ins]
        outputs = [tensor(port, "output", p) for port in outs]
        _require(len({ports[port]["domain"] for port in names}) == 1, p,
                 "tensor relation must stay in one domain")
        used.update(names)
        kind = rule["kind"]
        a, b = inputs[0], outputs[0]
        if kind in {"identity", "fork"}:
            _require(all(_equivalent(a, output, set()) for output in outputs), p,
                     "identity/fork requires identical tensor contracts")
        elif kind == "repack":
            _require(_equivalent(a, b, {"layout"}), p, "repack changes logical or numeric meaning")
        elif kind == "requantize":
            _require(a["sequence"]["kind"] == b["sequence"]["kind"] == "dense", p,
                     "requantize requires dense tensors")
            _require(_equivalent(a, b, {"element", "quantization"}), p,
                     "requantize must preserve shape/layout/sequence")
            _require(rule["arithmetic"] == "exact_affine_v1", p, "unsupported requantize arithmetic")
        elif kind == "zip_add":
            _require(all(value["sequence"]["kind"] == "dense" for value in inputs + outputs), p,
                     "zip_add requires dense tensors")
            _require(all(_equivalent(value, b, {"element", "quantization"}) for value in inputs), p,
                     "zip_add requires same shape/layout/sequence")
            if rule["arithmetic"] == "same_scale_centered_sum":
                _require(all(value["element"] == b["element"] and
                             value["quantization"] == b["quantization"] for value in inputs),
                         p, "centered sum requires identical numeric encoding")
        elif kind == "reduce_sum":
            _require(a["sequence"]["kind"] == "partial_sum" and b["sequence"]["kind"] == "dense", p,
                     "reduce_sum requires partial_sum to dense")
            _require(a["shape"] == b["shape"] and a["layout"] == b["layout"], p,
                     "reduce_sum must preserve coordinates and layout")
            _require(all(a["sequence"][key] == b["sequence"][key]
                         for key in ("frame_fact", "reset_fact")), p,
                     "reduce_sum must preserve invocation/reset identity")
            _require(a["element"]["kind"] == b["element"]["kind"] and
                     a["element"]["width"] <= b["element"]["width"], p,
                     "reduce_sum cannot change signedness or narrow storage")
            qa, qb = deepcopy(a["quantization"]), deepcopy(b["quantization"])
            qa.pop("range", None)
            qb.pop("range", None)
            _require(qa == qb and all(zero == 0 for zero in _zero_points(a)), p,
                     "reduce_sum requires preserved scales and zero-centered partial sums")
            if rule["overflow"] == "wrap":
                q = b["quantization"]
                full = storage_range(b["element"])
                _require(q["kind"] == "integer" or (q["range"]["min"], q["range"]["max"]) == full,
                         p, "wrap requires full storage range")
        elif kind != "compute":
            raise PcSemanticError(f"{p}: unsupported tensor relation {kind}")
        obligations.append({"path": p, "kind": kind, "status": "not_evaluated"})
    _require(used == tensor_ports, path + ".tensor_rules",
             "every tensor port must belong to exactly one main relation; missing: " +
             ", ".join(sorted(tensor_ports - used)))
    bound_states: set[str] = set()
    for name, rule in sorted(implementation.get("buffer_rules", {}).items()):
        p = path + ".buffer_rules." + name
        fact(rule["fact"], "guarantee", p + ".fact")
        state_name = rule["state"]
        _require(state_name in states and states[state_name]["kind"] == "fifo", p,
                 "buffer state must name a local FIFO")
        _require(state_name not in bound_states, p, "FIFO has duplicate buffer bindings")
        bound_states.add(state_name)
        a = tensor(rule["input"], "input", p)
        b = tensor(rule["output"], "output", p)
        state = states[state_name]
        _require(_equivalent(a, b, set()) and state["element_type"] == port_types[rule["input"]], p,
                 "buffer FIFO and both ports must carry identical complete tensor beats")
        _require(state["domain"] == ports[rule["input"]]["domain"] == ports[rule["output"]]["domain"],
                 p, "buffer must stay in one domain")
        obligations.append({"path": p, "kind": "startup_and_steady_state_liveness",
                            "status": "not_evaluated"})
    for name, state in states.items():
        if state["kind"] == "fifo" and state["element_type"]["kind"] == "tensor_beat":
            _require(name in bound_states, path + ".states." + name,
                     "tensor FIFO requires a buffer binding")
    return tuple(obligations)
