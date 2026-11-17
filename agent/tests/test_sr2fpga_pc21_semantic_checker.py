"""Requirement-derived positive and counterexample coverage for PC2.1 H1/H2.

Fixtures are declarations, not qualified hardware or outcome-producing tasks.
"""

from copy import deepcopy

import pytest

from sr2fpga_agent.pc.checker import check_design
from sr2fpga_agent.pc.expressions import MAX_INTEGER, evaluate
from sr2fpga_agent.pc.semantics import PcSemanticError


FACTS = {name: {"role": "guarantee"} for name in ("Frame", "Reset", "Math", "Buffer")}
FACTS["Service"] = {"role": "assumption"}


def tensor(*, lanes=2, tail="zero_pad_mask", extent=3, sequence=None):
    return {
        "shape": [{"axis": "N", "extent": 1}, {"axis": "C", "extent": extent}],
        "element": {"kind": "sint", "width": 8},
        "quantization": {"kind": "integer"},
        "layout": {"order": ["N", "C"], "lane_axis": "C", "lanes": lanes, "tail": tail},
        "sequence": sequence or {"kind": "dense", "frame_fact": "Frame", "reset_fact": "Reset"},
    }


def boundary(payload=None, *, clock="rising"):
    payload = deepcopy(payload or {"kind": "uint", "width": 8})
    return {"rtl_top": "Example", "parameter_values": {},
            "signature": {"parameters": {}, "domains": {"d": {"clock": clock, "reset": {"kind": "none"}}},
                          "ports": {
                              "rx": {"kind": "stream", "direction": "input", "protocol": "ready_valid_v1", "domain": "d", "payload": deepcopy(payload)},
                              "tx": {"kind": "stream", "direction": "output", "protocol": "ready_valid_v1", "domain": "d", "payload": deepcopy(payload)},
                          }},
            "abi": {"domains": {"d": {"clock": "clk" if clock == "rising" else None, "reset": None}},
                    "ports": {"rx": {"payload": "rx_data", "valid": "rx_valid", "ready": "rx_ready"},
                              "tx": {"payload": "tx_data", "valid": "tx_valid", "ready": "tx_ready"}}}}


def behavior(public, *, rule="identity"):
    body = {"kind": "behavioral", "execution": "clocked", "intent": "Implement public task"}
    if "tensor_contracts" in public["signature"]:
        body["tensor_rules"] = {"Relation": {"kind": rule, "fact": "Math", "input": "rx", "output": "tx"}}
    return {"entry": "Top", "modules": {"Top": {"signature": {"source": "requirement_boundary"}, "implementation": body}}, "requirement_map": []}


def structural(public):
    declared = deepcopy(public["signature"])
    declared["source"] = "declared"
    body = {"kind": "behavioral", "execution": "clocked", "intent": "Leaf"}
    if "tensor_contracts" in declared:
        # Local names may differ across a net without changing semantics.
        declared["tensor_contracts"]["Local"] = declared["tensor_contracts"].pop("T")
        for port in declared["ports"].values():
            port["payload"]["contract"] = "Local"
        body["tensor_rules"] = {"Relation": {"kind": "identity", "fact": "Math", "input": "rx", "output": "tx"}}
    return {"entry": "Top", "modules": {
        "Top": {"signature": {"source": "requirement_boundary"}, "implementation": {
            "kind": "structural", "instances": {"leaf": {"module": "Leaf", "parameters": {}, "domains": {"d": "d"}}},
            "nets": {"in": {"source": {"kind": "endpoint", "endpoint": {"instance": "self", "port": "rx"}}, "sinks": [{"instance": "leaf", "port": "rx"}]},
                     "out": {"source": {"kind": "endpoint", "endpoint": {"instance": "leaf", "port": "tx"}}, "sinks": [{"instance": "self", "port": "tx"}]}}}},
        "Leaf": {"signature": declared, "implementation": body}}, "requirement_map": []}


def tensor_boundary():
    result = boundary({"kind": "tensor_beat", "contract": "T"})
    result["signature"]["tensor_contracts"] = {"T": tensor()}
    return result


@pytest.mark.parametrize(("expr", "value"), [
    ({"op": "clog2", "arg": 1}, 0), ({"op": "clog2", "arg": 9}, 4),
    ({"op": "ceil_div", "args": [13, 4]}, 4), ({"op": "sub", "args": [9, 2]}, 7),
    ({"op": "min", "args": [9, 2]}, 2), ({"op": "max", "args": [9, 2]}, 9),
    ({"op": "mul", "args": [{"param": "W"}, 3]}, 24),
])
def test_finite_expression_golden_values(expr, value):
    assert evaluate(expr, {"W": 8}) == value


@pytest.mark.parametrize("expr", [
    {"param": "Missing"}, {"op": "ceil_div", "args": [1, 0]},
    {"op": "sub", "args": [1, 2]}, {"op": "add", "args": [MAX_INTEGER, 1]},
    {"op": "clog2", "arg": 0}, True, 1.0, "1+2", {"op": "pow", "args": [2, 8]},
    {"op": "mul", "args": [0, {"op": "sub", "args": [0, 1]}]},
])
def test_expressions_reject_invalid_intermediate_and_unsupported_programs(expr):
    with pytest.raises(PcSemanticError):
        evaluate(expr, {})


def test_expression_depth_is_bounded():
    expr = 1
    for _ in range(65):
        expr = {"op": "clog2", "arg": expr}
    with pytest.raises(PcSemanticError, match="depth"):
        evaluate(expr, {})


def test_hierarchy_elaboration_retains_parameters_and_not_evaluated_obligations():
    public = boundary()
    public["signature"]["parameters"] = {"W": {"minimum": 1, "maximum": 16}}
    public["parameter_values"] = {"W": 8}
    for port in public["signature"]["ports"].values():
        port["payload"]["width"] = {"param": "W"}
    design = structural(public)
    design["modules"]["Top"]["implementation"]["instances"]["leaf"]["parameters"] = {"W": {"param": "W"}}
    original = deepcopy((design, public))
    checked = check_design(design, public)
    assert checked.instances["self/leaf"].parameters == {"W": 8}
    assert checked.instances["self/leaf"].port_widths == {"rx": 8, "tx": 8}
    assert checked.scope == "schema_and_listed_static_checks_only"
    assert all(item["status"] == "not_evaluated" for item in checked.verification_obligations)
    assert (design, public) == original


@pytest.mark.parametrize("value", [0, 17])
def test_actual_parameter_values_must_obey_declared_range(value):
    public = boundary()
    public["signature"]["parameters"] = {"W": {"minimum": 1, "maximum": 16}}
    public["parameter_values"] = {"W": value}
    with pytest.raises(PcSemanticError, match="outside"):
        check_design(behavior(public), public)


def test_zero_width_from_clog2_one_is_rejected_without_implicit_fix():
    public = boundary({"kind": "uint", "width": {"op": "clog2", "arg": 1}})
    with pytest.raises(PcSemanticError, match="zero"):
        check_design(behavior(public), public)


@pytest.mark.parametrize("damage", ["signed", "record_order", "fixed_fraction", "cross_domain", "direction", "undriven", "multiple_driver", "broadcast", "deep_endpoint", "unused_stream"])
def test_structural_connection_counterexamples(damage):
    data_type = {"kind": "uint", "width": 8}
    if damage == "record_order":
        data_type = {"kind": "record", "fields": [{"name": "a", "type": {"kind": "bits", "width": 4}}, {"name": "b", "type": {"kind": "bits", "width": 4}}]}
    elif damage == "fixed_fraction":
        data_type = {"kind": "fixed", "width": 8, "signed": True, "fraction_bits": 3}
    public = boundary(data_type)
    design = structural(public)
    top = design["modules"]["Top"]["implementation"]
    leaf = design["modules"]["Leaf"]["signature"]
    cap = None
    if damage == "signed":
        leaf["ports"]["rx"]["payload"]["kind"] = "sint"
    elif damage == "record_order":
        leaf["ports"]["rx"]["payload"]["fields"].reverse()
    elif damage == "fixed_fraction":
        leaf["ports"]["rx"]["payload"]["fraction_bits"] = 2
    elif damage == "cross_domain":
        public["signature"]["domains"]["other"] = deepcopy(public["signature"]["domains"]["d"])
        public["abi"]["domains"]["other"] = {"clock": "other_clk", "reset": None}
        public["signature"]["ports"]["rx"]["domain"] = "other"
        cap = {"max_clock_domains": 2}
    elif damage == "direction":
        top["nets"]["in"]["source"]["endpoint"]["port"] = "tx"
    elif damage == "undriven":
        del top["nets"]["out"]
    elif damage == "multiple_driver":
        top["nets"]["duplicate"] = deepcopy(top["nets"]["out"])
    elif damage == "broadcast":
        top["nets"]["in"]["sinks"].append({"instance": "self", "port": "tx"})
    elif damage == "deep_endpoint":
        top["nets"]["in"]["sinks"][0]["instance"] = "unknown"
    else:
        del top["nets"]["out"]
        top["unused_values"] = [{"instance": "leaf", "port": "tx"}]
    with pytest.raises(PcSemanticError):
        check_design(design, public, cap)


def test_equal_width_tensor_layout_conflict_rejected_but_local_rename_allowed():
    public = tensor_boundary()
    design = structural(public)
    checked = check_design(design, public, facts=FACTS)
    descriptor = checked.instances["self"].tensor_contracts["T"]
    assert descriptor["derived"]["beat_bits"] == 18
    assert descriptor["derived"]["beats_per_invocation"] == 2
    local = design["modules"]["Leaf"]["signature"]["tensor_contracts"]["Local"]
    local["layout"].update(order=["C", "N"], lane_axis="N")
    with pytest.raises(PcSemanticError, match="type/encoding mismatch"):
        check_design(design, public, facts=FACTS)


@pytest.mark.parametrize("damage", ["duplicate_axis", "zero_extent", "missing_axis", "lane_axis", "zero_lanes", "exact_tail", "width", "scale", "zero_point", "range", "per_axis_length", "per_axis_axis", "missing_fact", "fact_role", "unused_contract", "unknown_contract"])
def test_tensor_descriptor_counterexamples(damage):
    public = tensor_boundary()
    t = public["signature"]["tensor_contracts"]["T"]
    if damage == "duplicate_axis":
        t["shape"].append({"axis": "C", "extent": 3})
    elif damage == "zero_extent":
        t["shape"][1]["extent"] = 0
    elif damage == "missing_axis":
        t["layout"]["order"] = ["C"]
    elif damage == "lane_axis":
        t["layout"]["lane_axis"] = "N"
    elif damage == "zero_lanes":
        t["layout"]["lanes"] = 0
    elif damage == "exact_tail":
        t["layout"]["tail"] = "exact"
    elif damage == "width":
        t["element"]["width"] = 33
    elif damage in {"scale", "zero_point", "range"}:
        t["quantization"] = {"kind": "affine", "granularity": "per_tensor", "scale": {"numerator": 1, "denominator": 8}, "zero_point": 0, "range": {"min": -128, "max": 127}}
        if damage == "scale":
            t["quantization"]["scale"] = {"numerator": 2, "denominator": 8}
        elif damage == "zero_point":
            t["quantization"]["zero_point"] = 128
        else:
            t["quantization"]["range"]["min"] = -129
    elif damage in {"per_axis_length", "per_axis_axis"}:
        t["quantization"] = {"kind": "affine", "granularity": "per_axis", "axis": "C" if damage == "per_axis_length" else "Missing", "scales": [{"numerator": 1, "denominator": 8}], "zero_points": [0], "range": {"min": -128, "max": 127}}
    elif damage == "missing_fact":
        t["sequence"]["frame_fact"] = "Missing"
    elif damage == "fact_role":
        t["sequence"]["reset_fact"] = "Service"
    elif damage == "unused_contract":
        public["signature"]["tensor_contracts"]["Extra"] = deepcopy(t)
    else:
        public["signature"]["ports"]["rx"]["payload"]["contract"] = "Missing"
    with pytest.raises(PcSemanticError):
        check_design(behavior(public), public, facts=FACTS)


def test_per_axis_tables_follow_logical_extent_and_shape_object_order_is_irrelevant():
    public = tensor_boundary()
    t = public["signature"]["tensor_contracts"]["T"]
    t["quantization"] = {"kind": "affine", "granularity": "per_axis", "axis": "C", "scales": [{"numerator": 1, "denominator": d} for d in (8, 4, 2)], "zero_points": [0, 1, -1], "range": {"min": -128, "max": 127}}
    design = structural(public)
    design["modules"]["Leaf"]["signature"]["tensor_contracts"]["Local"]["shape"].reverse()
    check_design(design, public, facts=FACTS)


def test_partial_sum_counts_and_reduce_relation_preserve_numeric_and_invocation_identity():
    public = tensor_boundary()
    t = public["signature"]["tensor_contracts"]["T"]
    t["sequence"] = {"kind": "partial_sum", "frame_fact": "Frame", "reset_fact": "Reset", "reduction_axis": "K", "groups": 3, "group_order": "innermost"}
    public["signature"]["tensor_contracts"]["Result"] = tensor()
    public["signature"]["tensor_contracts"]["Result"]["element"]["width"] = 16
    public["signature"]["ports"]["tx"]["payload"]["contract"] = "Result"
    design = behavior(public)
    design["modules"]["Top"]["implementation"]["tensor_rules"]["Relation"] = {"kind": "reduce_sum", "fact": "Math", "input": "rx", "output": "tx", "initialize": "zero_before_group0", "commit": "after_all_groups", "requantize": "forbidden_until_commit", "overflow": "error"}
    checked = check_design(design, public, facts=FACTS)
    assert checked.instances["self"].tensor_contracts["T"]["derived"]["beats_per_invocation"] == 6
    public["signature"]["tensor_contracts"]["Result"]["element"]["width"] = 4
    with pytest.raises(PcSemanticError, match="narrow"):
        check_design(design, public, facts=FACTS)


@pytest.mark.parametrize("damage", ["omitted", "duplicate", "reverse", "wrong_fact"])
def test_main_tensor_rule_coverage_and_fact_roles(damage):
    public = tensor_boundary()
    design = behavior(public)
    rules = design["modules"]["Top"]["implementation"]["tensor_rules"]
    if damage == "omitted":
        rules.clear()
    elif damage == "duplicate":
        rules["Other"] = deepcopy(rules["Relation"])
    elif damage == "reverse":
        rules["Relation"].update(input="tx", output="rx")
    else:
        rules["Relation"]["fact"] = "Service"
    with pytest.raises(PcSemanticError):
        check_design(design, public, facts=FACTS)


def test_low_capacity_tensor_fifo_remains_static_only():
    public = tensor_boundary()
    design = behavior(public)
    body = design["modules"]["Top"]["implementation"]
    body["states"] = {"Queue": {"kind": "fifo", "domain": "d", "element_type": {"kind": "tensor_beat", "contract": "T"}, "depth": 1, "read_mode": "registered", "full_exchange": "allow_push_with_pop", "empty_exchange": "store_only", "reset_contents": "invalidate"}}
    body["buffer_rules"] = {"Stored": {"fact": "Buffer", "state": "Queue", "input": "rx", "output": "tx", "capacity_unit": "beats"}}
    checked = check_design(design, public, facts=FACTS)
    assert checked.instances["self"].states["Queue"]["depth"] == 1
    assert {"path": "self.buffer_rules.Stored", "kind": "startup_and_steady_state_liveness", "status": "not_evaluated"} in checked.verification_obligations
    body["states"]["Queue"]["depth"] = 0
    with pytest.raises(PcSemanticError, match="positive"):
        check_design(design, public, facts=FACTS)


def test_requirement_mapping_is_coverage_only_and_cannot_invent_facts():
    public = boundary()
    design = behavior(public)
    facts = {"Math": {"role": "guarantee", "required_mapping": True}}
    with pytest.raises(PcSemanticError, match="missing required"):
        check_design(design, public, facts=facts)
    design["requirement_map"] = [{"fact": "Math", "targets": [{"kind": "module", "module": "Top"}]}]
    checked = check_design(design, public, facts=facts)
    assert "algorithm_correctness" in checked.deferred_checks
    design["requirement_map"][0]["fact"] = "Invented"
    with pytest.raises(PcSemanticError, match="unknown public fact"):
        check_design(design, public, facts=facts)


@pytest.mark.parametrize("cap", [{"max_instances": 1}, {"max_hierarchy_depth": 0}, {"max_width": 4}, {"max_clock_domains": 0}, {"unknown": 1}, {"supported_reset_kinds": []}])
def test_capability_restrictions_fail_closed(cap):
    public = boundary()
    with pytest.raises(PcSemanticError):
        check_design(structural(public), public, cap)


def test_combinational_domains_do_not_consume_clock_or_allow_state():
    public = boundary(clock="none")
    design = behavior(public)
    design["modules"]["Top"]["implementation"]["execution"] = "combinational"
    assert check_design(design, public).instances["self"].domains == {"d": "d"}
    design["modules"]["Top"]["implementation"]["states"] = {"R": {"kind": "register", "domain": "d", "type": {"kind": "uint", "width": 8}, "reset": {"kind": "none"}}}
    with pytest.raises(PcSemanticError, match="cannot have state"):
        check_design(design, public)


@pytest.mark.parametrize("kind", ["fork", "repack", "requantize", "zip_add", "compute"])
def test_finite_tensor_relations_accept_only_their_declared_transformations(kind):
    public = tensor_boundary()
    rule = {"kind": kind, "fact": "Math", "input": "rx", "output": "tx"}
    if kind == "fork":
        public["signature"]["ports"]["copy"] = deepcopy(public["signature"]["ports"]["tx"])
        public["abi"]["ports"]["copy"] = {"payload": "copy_data", "valid": "copy_valid", "ready": "copy_ready"}
        rule = {"kind": kind, "fact": "Math", "input": "rx", "outputs": ["tx", "copy"]}
    elif kind in {"repack", "requantize"}:
        public["signature"]["tensor_contracts"]["Result"] = deepcopy(public["signature"]["tensor_contracts"]["T"])
        public["signature"]["ports"]["tx"]["payload"]["contract"] = "Result"
        output = public["signature"]["tensor_contracts"]["Result"]
        if kind == "repack":
            output["layout"].update(lanes=1, tail="exact")
        else:
            output["element"]["width"] = 4
            output["quantization"] = {"kind": "affine", "granularity": "per_tensor", "scale": {"numerator": 1, "denominator": 2}, "zero_point": -1, "range": {"min": -8, "max": 7}}
            rule.update(arithmetic="exact_affine_v1", rounding="nearest_even", overflow="saturate")
    elif kind == "zip_add":
        public["signature"]["ports"]["other"] = deepcopy(public["signature"]["ports"]["rx"])
        public["abi"]["ports"]["other"] = {"payload": "other_data", "valid": "other_valid", "ready": "other_ready"}
        rule = {"kind": kind, "fact": "Math", "inputs": ["rx", "other"], "output": "tx", "pairing": "same_invocation_and_coordinate", "arithmetic": "same_scale_centered_sum", "rounding": "nearest_even", "overflow": "error"}
    elif kind == "compute":
        rule = {"kind": kind, "fact": "Math", "inputs": ["rx"], "outputs": ["tx"]}
    design = behavior(public)
    design["modules"]["Top"]["implementation"]["tensor_rules"]["Relation"] = rule
    checked = check_design(design, public, facts=FACTS)
    assert {"path": "self.tensor_rules.Relation", "kind": kind, "status": "not_evaluated"} in checked.verification_obligations
    # These relations never authorize changing invocation/reset identity.
    if kind != "compute":
        public["signature"]["tensor_contracts"]["Other"] = deepcopy(public["signature"]["tensor_contracts"]["T"])
        public["signature"]["tensor_contracts"]["Other"]["sequence"]["frame_fact"] = "Math"
        public["signature"]["ports"]["tx"]["payload"]["contract"] = "Other"
        # Retain Result use when present, so rejection specifically tests relation.
        public["signature"]["tensor_contracts"].pop("Result", None)
        with pytest.raises(PcSemanticError):
            check_design(design, public, facts=FACTS)


def test_zip_add_affine_sum_allows_different_scales_but_centered_sum_rejects_them():
    public = tensor_boundary()
    public["signature"]["ports"]["other"] = deepcopy(public["signature"]["ports"]["rx"])
    public["abi"]["ports"]["other"] = {"payload": "other_data", "valid": "other_valid", "ready": "other_ready"}
    public["signature"]["tensor_contracts"]["Other"] = deepcopy(public["signature"]["tensor_contracts"]["T"])
    public["signature"]["tensor_contracts"]["Other"]["quantization"] = {"kind": "affine", "granularity": "per_tensor", "scale": {"numerator": 1, "denominator": 8}, "zero_point": 3, "range": {"min": -128, "max": 127}}
    public["signature"]["ports"]["other"]["payload"]["contract"] = "Other"
    design = behavior(public)
    rule = {"kind": "zip_add", "fact": "Math", "inputs": ["rx", "other"], "output": "tx", "pairing": "same_invocation_and_coordinate", "arithmetic": "exact_affine_sum_v1", "rounding": "floor", "overflow": "saturate"}
    design["modules"]["Top"]["implementation"]["tensor_rules"]["Relation"] = rule
    check_design(design, public, facts=FACTS)
    rule["arithmetic"] = "same_scale_centered_sum"
    with pytest.raises(PcSemanticError, match="identical numeric"):
        check_design(design, public, facts=FACTS)
    rule["inputs"] = ["rx", "rx"]
    with pytest.raises(PcSemanticError, match="duplicate"):
        check_design(design, public, facts=FACTS)


@pytest.mark.parametrize("damage", ["state_domain", "reset_value", "reset_absent", "memory_asset", "timing_assumption", "timing_range", "timing_direction", "duplicate_assumption"])
def test_behavioral_state_and_timing_references(damage):
    public = boundary()
    public["signature"]["domains"]["d"]["reset"] = {"kind": "sync", "polarity": "active_low"}
    public["abi"]["domains"]["d"]["reset"] = "rst_n"
    design = behavior(public)
    body = design["modules"]["Top"]["implementation"]
    body["states"] = {"R": {"kind": "register", "domain": "d", "type": {"kind": "sint", "width": 8}, "reset": {"kind": "value", "raw_value": -128}}}
    body["timing"] = {"Latency": {"kind": "latency", "fact": "Math", "input": "rx", "output": "tx", "domain": "d", "start_event": "accept", "end_event": "offer", "min_cycles": 0, "max_cycles": 3, "under_assumptions": ["Service"]}}
    check_design(design, public, facts=FACTS)
    if damage == "state_domain":
        body["states"]["R"]["domain"] = "Missing"
    elif damage == "reset_value":
        body["states"]["R"]["reset"]["raw_value"] = 128
    elif damage == "reset_absent":
        public["signature"]["domains"]["d"]["reset"] = {"kind": "none"}
        public["abi"]["domains"]["d"]["reset"] = None
    elif damage == "memory_asset":
        body["states"] = {"Weights": {"kind": "memory", "domain": "d", "element_type": {"kind": "sint", "width": 8}, "depth": 8, "organization": "single_port", "read_latency_cycles": 1, "read_during_write": "old_data", "initialization": {"kind": "public_asset", "asset_id": "Missing"}, "reset_contents": "preserve"}}
    elif damage == "timing_assumption":
        body["timing"]["Latency"]["under_assumptions"] = ["Math"]
    elif damage == "timing_range":
        body["timing"]["Latency"]["min_cycles"] = 4
    elif damage == "timing_direction":
        body["timing"]["Latency"]["input"] = "tx"
    else:
        body["timing"]["Latency"]["under_assumptions"] = ["Service", "Service"]
    with pytest.raises(PcSemanticError):
        check_design(design, public, facts=FACTS)


def test_explicit_value_fanout_and_typed_constant_are_legal():
    public = boundary()
    public["signature"]["domains"] = {}
    public["abi"]["domains"] = {}
    public["signature"]["ports"] = {"a": {"kind": "value", "direction": "input", "domain": None, "type": {"kind": "sint", "width": 8}},
                                    "b": {"kind": "value", "direction": "output", "domain": None, "type": {"kind": "sint", "width": 8}},
                                    "c": {"kind": "value", "direction": "output", "domain": None, "type": {"kind": "sint", "width": 8}},
                                    "d": {"kind": "value", "direction": "output", "domain": None, "type": {"kind": "sint", "width": 8}}}
    public["abi"]["ports"] = {name: {"signal": name} for name in ("a", "b", "c", "d")}
    design = {"entry": "Top", "modules": {"Top": {"signature": {"source": "requirement_boundary"}, "implementation": {
        "kind": "structural", "instances": {}, "nets": {
            "Fanout": {"source": {"kind": "endpoint", "endpoint": {"instance": "self", "port": "a"}}, "sinks": [{"instance": "self", "port": port} for port in ("b", "c")]},
            "Constant": {"source": {"kind": "constant", "type": {"kind": "sint", "width": 8}, "raw_value": -128}, "sinks": [{"instance": "self", "port": "d"}]}}}}}, "requirement_map": []}
    check_design(design, public)
    design["modules"]["Top"]["implementation"]["nets"]["Constant"]["source"]["raw_value"] = 128
    with pytest.raises(PcSemanticError, match="constant is not representable"):
        check_design(design, public)


@pytest.mark.parametrize("damage", ["bad_range", "missing_parameter", "unknown_parameter", "wrong_scope", "missing_domain", "unknown_domain", "reset_polarity", "duplicate_record", "fixed_fraction"])
def test_parameter_type_and_domain_scope_counterexamples(damage):
    public = boundary()
    public["signature"]["parameters"] = {"W": {"minimum": 1, "maximum": 16}}
    public["parameter_values"] = {"W": 8}
    for port in public["signature"]["ports"].values():
        port["payload"]["width"] = {"param": "W"}
    design = structural(public)
    child = design["modules"]["Top"]["implementation"]["instances"]["leaf"]
    child["parameters"] = {"W": {"param": "W"}}
    leaf = design["modules"]["Leaf"]["signature"]
    if damage == "bad_range":
        leaf["parameters"]["W"] = {"minimum": 9, "maximum": 8}
    elif damage == "missing_parameter":
        child["parameters"] = {}
    elif damage == "unknown_parameter":
        child["parameters"]["Extra"] = 1
    elif damage == "wrong_scope":
        child["parameters"]["W"] = {"param": "ChildOnly"}
    elif damage == "missing_domain":
        child["domains"] = {}
    elif damage == "unknown_domain":
        child["domains"]["d"] = "Missing"
    elif damage == "reset_polarity":
        public["signature"]["domains"]["d"]["reset"] = {"kind": "sync", "polarity": "active_low"}
        public["abi"]["domains"]["d"]["reset"] = "rst_n"
        leaf["domains"]["d"]["reset"] = {"kind": "sync", "polarity": "active_high"}
    elif damage == "duplicate_record":
        leaf["ports"]["rx"]["payload"] = {"kind": "record", "fields": [{"name": "a", "type": {"kind": "uint", "width": 4}}, {"name": "a", "type": {"kind": "uint", "width": 4}}]}
    else:
        leaf["ports"]["rx"]["payload"] = {"kind": "fixed", "width": 8, "signed": True, "fraction_bits": 9}
    with pytest.raises(PcSemanticError):
        check_design(design, public)


def test_clockless_child_domain_may_share_parent_identity_without_consuming_pins():
    public = boundary()
    design = structural(public)
    leaf = design["modules"]["Leaf"]
    leaf["signature"]["domains"]["d"]["clock"] = "none"
    leaf["implementation"]["execution"] = "combinational"
    checked = check_design(design, public)
    assert checked.instances["self/leaf"].domains == {"d": "d"}
    assert checked.instances["self/leaf"].signature["domains"]["d"]["clock"] == "none"


def test_unbound_async_reset_is_not_qualified_by_a_declaration():
    public = boundary()
    public["signature"]["domains"]["d"]["reset"] = {"kind": "async", "polarity": "active_low", "release": "synchronous_to_domain"}
    public["abi"]["domains"]["d"]["reset"] = "rst_n"
    with pytest.raises(PcSemanticError, match="unsupported"):
        check_design(behavior(public), public)
    checked = check_design(behavior(public), public, {"supported_reset_kinds": ["none", "sync", "async"]})
    assert "backpressure_and_reset_behavior" in checked.deferred_checks


def test_capability_tensor_element_limit_and_unreferenced_fifo_binding_fail_closed():
    public = tensor_boundary()
    design = behavior(public)
    with pytest.raises(PcSemanticError, match="element limit"):
        check_design(design, public, {"max_tensor_elements": 2}, facts=FACTS)
    design["modules"]["Top"]["implementation"]["states"] = {"Queue": {"kind": "fifo", "domain": "d", "element_type": {"kind": "tensor_beat", "contract": "T"}, "depth": 1, "read_mode": "registered", "full_exchange": "allow_push_with_pop", "empty_exchange": "store_only", "reset_contents": "invalidate"}}
    with pytest.raises(PcSemanticError, match="requires a buffer binding"):
        check_design(design, public, facts=FACTS)
