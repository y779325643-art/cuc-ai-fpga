"""Pure PC 2.1 configuration elaboration and listed static checks.

No RTL, model, family implementation or evaluator is invoked. Public facts and
asset identities are supplied by the trusted public-context loader, separately
from candidate declarations. A successful result never establishes behavior.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.public_boundary import (
    check_public_boundary_domains,
    check_public_boundary_ports,
)

from .expressions import bind_parameters, evaluate, natural
from .semantics import (
    PcSemanticError,
    validate_acyclic_modules,
    validate_entry_module,
    validate_instance_modules,
    validate_reachable_modules,
    validate_signature_sources,
)
from .tensors import check_tensor_rules, resolve_tensor, storage_range

# Local development resource ceilings, not frozen campaign budgets. A trusted
# capability source may lower or explicitly select these values. Hard ceilings
# protect the checker itself and do not alter the PC expression integer range.
DEFAULT_CAPABILITY = {
    "max_instances": 4096,
    "max_hierarchy_depth": 64,
    "max_width": 1048576,
    "max_tensor_elements": 1048576,
    "supported_reset_kinds": ["none", "sync"],
    "max_clock_domains": 1,
}


@dataclass(frozen=True)
class CheckedInstance:
    path: str
    module_id: str
    parameters: dict[str, int]
    signature: dict[str, Any]
    domains: dict[str, str]
    implementation: dict[str, Any]
    children: dict[str, str]
    port_types: dict[str, dict[str, Any]]
    port_widths: dict[str, int]
    tensor_contracts: dict[str, dict[str, Any]]
    states: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckedDesign:
    design: dict[str, Any]
    boundary: dict[str, Any]
    capability: dict[str, Any]
    entry: str
    instances: dict[str, CheckedInstance]
    verification_obligations: tuple[dict[str, Any], ...]
    scope: str = "schema_and_listed_static_checks_only"
    deferred_checks: tuple[str, ...] = (
        "algorithm_correctness", "actual_tensor_layout_and_arithmetic",
        "accepted_transaction_identity", "backpressure_and_reset_behavior",
        "actual_state_implementation", "combinational_cycles", "deadlock_and_liveness",
        "timing_and_resource_implementation", "public_asset_content_and_loading",
    )


def _require(condition: bool, path: str, message: str) -> None:
    if not condition:
        raise PcSemanticError(f"{path}: {message}")


def _capability(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    result = deepcopy(DEFAULT_CAPABILITY)
    if payload is not None:
        _require(isinstance(payload, Mapping), "$.capability", "expected an object")
        unknown = set(payload) - set(result)
        _require(not unknown, "$.capability", "unsupported capability fields: " + ", ".join(sorted(unknown)))
        result.update(deepcopy(dict(payload)))
    for key in ("max_instances", "max_hierarchy_depth", "max_width", "max_tensor_elements"):
        natural(result[key], "$.capability." + key, positive=True)
    natural(result["max_clock_domains"], "$.capability.max_clock_domains")
    _require(result["max_hierarchy_depth"] <= 128, "$.capability.max_hierarchy_depth",
             "checker hierarchy limit is 128")
    _require(result["max_instances"] <= 100000, "$.capability.max_instances",
             "checker instance limit is 100000")
    _require(result["max_width"] <= 1048576, "$.capability.max_width",
             "checker packed-width limit is 1048576")
    resets = result["supported_reset_kinds"]
    _require(isinstance(resets, list) and all(type(item) is str for item in resets)
             and len(set(resets)) == len(resets) and set(resets) <= {"none", "sync", "async"},
             "$.capability.supported_reset_kinds", "invalid reset support list")
    return result


def resolve_type(data_type: Mapping[str, Any], parameters: Mapping[str, int],
                 tensors: Mapping[str, Any], used_tensors: set[str], path: str,
                 *, max_width: int, depth: int = 0) -> dict[str, Any]:
    """Resolve a semantic packed type; signedness and record order are retained."""
    _require(depth <= 64, path, "type nesting limit exceeded")
    kind = data_type["kind"]
    result = deepcopy(dict(data_type))
    if kind == "tensor_beat":
        name = data_type["contract"]
        _require(name in tensors, path + ".contract", f"undefined local tensor contract {name}")
        used_tensors.add(name)
        return {"kind": kind, "descriptor": deepcopy(tensors[name]),
                "width": tensors[name]["derived"]["beat_bits"]}
    if kind == "record":
        names: set[str] = set()
        fields = []
        for i, item in enumerate(data_type["fields"]):
            _require(item["name"] not in names, path + ".fields", "duplicate record field")
            names.add(item["name"])
            fields.append({"name": item["name"], "type": resolve_type(
                item["type"], parameters, tensors, used_tensors, f"{path}.fields[{i}].type",
                max_width=max_width, depth=depth + 1)})
        result["fields"] = fields
        width = sum(item["type"]["width"] for item in fields)
    else:
        _require(kind in {"bits", "uint", "sint", "fixed"}, path, "unsupported type")
        width = evaluate(data_type["width"], parameters, path + ".width")
        if kind == "fixed":
            fraction = evaluate(data_type["fraction_bits"], parameters, path + ".fraction_bits")
            _require(fraction <= width, path + ".fraction_bits", "fraction bits exceed total width")
            result["fraction_bits"] = fraction
    _require(1 <= width <= max_width, path + ".width", "zero or unsupported packed width")
    result["width"] = width
    return result


def _raw_range(data_type: Mapping[str, Any]) -> tuple[int, int]:
    if data_type["kind"] == "sint" or (data_type["kind"] == "fixed" and data_type["signed"]):
        return storage_range({"kind": "sint", "width": data_type["width"]})
    return storage_range({"kind": "uint", "width": data_type["width"]})


def check_design(design: Mapping[str, Any], boundary: Mapping[str, Any],
                 capability: Mapping[str, Any] | None = None, *,
                 facts: Mapping[str, Mapping[str, Any]] | None = None,
                 public_assets: Iterable[str] = ()) -> CheckedDesign:
    """Check and elaborate only the actual public-boundary configuration.

    ``boundary`` is the existing development boundary core or wrapper. ``facts``
    maps trusted public IDs to records with ``role`` and optional
    ``required_mapping``. It is never inferred from candidate requirement_map.
    Limits are development capabilities, not experiment authorization.
    """
    registry = ContractRegistry()
    errors = registry.load_schema("design_proposal_2_1").validate(design)
    _require(not errors, "$.design", "; ".join(errors[:12]))
    design = deepcopy(dict(design))
    if "boundary" in boundary:
        wrapper = deepcopy(dict(boundary))
        boundary = wrapper["boundary"]
    else:
        boundary = deepcopy(dict(boundary))
        wrapper = {"contract_version": "development-public-boundary-v1",
                   "validation_scope": "boundary_shape_only", "boundary": boundary}
    errors = check_public_boundary_ports(wrapper, registry=registry)
    errors += check_public_boundary_domains(wrapper, registry=registry)
    _require(not errors, "$.boundary", "; ".join(errors[:12]))
    cap = _capability(capability)
    facts = deepcopy(dict(facts or {}))
    assets = set(public_assets)
    _require(all(isinstance(name, str) for name in assets), "$.public_assets", "asset IDs must be strings")
    for name, record in facts.items():
        _require(isinstance(record, Mapping) and record.get("role") in {"guarantee", "assumption"},
                 "$.facts." + name, "public fact role must be guarantee or assumption")

    def fact(name: str, role: str, path: str) -> None:
        _require(name in facts, path, f"unknown public fact {name}")
        _require(facts[name]["role"] == role, path, f"public fact {name} must be {role}")

    for check in (validate_entry_module, validate_instance_modules, validate_acyclic_modules,
                  validate_reachable_modules, validate_signature_sources):
        check(design)
    instances: dict[str, CheckedInstance] = {}
    obligations: list[dict[str, Any]] = []
    top_domains = boundary["signature"]["domains"]
    _require(sum(domain["clock"] == "rising" for domain in top_domains.values()) <= cap["max_clock_domains"],
             "$.boundary.signature.domains", "clock domain capability exceeded")
    physical: list[str] = []
    for mapping in boundary["abi"]["ports"].values():
        physical.extend(mapping.values())
    for mapping in boundary["abi"]["domains"].values():
        physical.extend(value for value in mapping.values() if value is not None)
    _require(len(physical) == len(set(physical)), "$.boundary.abi", "physical pin names collide")

    def elaborate(module_id: str, path: str, values: Mapping[str, Any],
                  parent_parameters: Mapping[str, int], root_domains: dict[str, str], depth: int) -> None:
        _require(depth <= cap["max_hierarchy_depth"], path, "hierarchy depth limit exceeded")
        _require(len(instances) < cap["max_instances"], path, "instance expansion limit exceeded")
        module = design["modules"][module_id]
        signature = deepcopy(boundary["signature"] if path == "self" else module["signature"])
        signature.pop("source", None)
        parameters = bind_parameters(signature["parameters"], values, parent_parameters, path + ".parameters")
        domains = signature["domains"]
        _require(set(root_domains) == set(domains), path + ".domains", "domain bindings must exactly cover declarations")
        for name, domain in domains.items():
            _require(domain["reset"]["kind"] in cap["supported_reset_kinds"], path + ".domains." + name,
                     "reset kind unsupported by capability")
            _require(domain["clock"] != "none" or domain["reset"]["kind"] == "none", path + ".domains." + name,
                     "clock=none requires reset=none")
        tensors = {name: resolve_tensor(value, parameters, path + ".tensor_contracts." + name,
                                       fact, max_elements=cap["max_tensor_elements"], max_width=cap["max_width"])
                   for name, value in sorted(signature.get("tensor_contracts", {}).items())}
        used_tensors: set[str] = set()
        port_types: dict[str, dict[str, Any]] = {}
        for name, port in signature["ports"].items():
            p = path + ".ports." + name
            _require(port["domain"] is None or port["domain"] in domains, p + ".domain", "undefined port domain")
            port_types[name] = resolve_type(port["payload"] if port["kind"] == "stream" else port["type"],
                                            parameters, tensors, used_tensors, p, max_width=cap["max_width"])
            port["payload" if port["kind"] == "stream" else "type"] = deepcopy(port_types[name])
        if "tensor_contracts" in signature:
            signature["tensor_contracts"] = deepcopy(tensors)
        implementation = module["implementation"]
        children: dict[str, str] = {}
        states: dict[str, dict[str, Any]] = {}
        # Reserve the current node before descending to enforce global limits.
        instances[path] = CheckedInstance(path, module_id, parameters, signature, root_domains,
                                          deepcopy(implementation), children, port_types,
                                          {name: value["width"] for name, value in port_types.items()}, tensors, states)
        if implementation["kind"] == "structural":
            for child_name, child in sorted(implementation["instances"].items()):
                _require(child_name != "self", path + ".instances.self", "self is a reserved endpoint name")
                child_signature = design["modules"][child["module"]]["signature"]
                _require(set(child["domains"]) == set(child_signature["domains"]), path + ".instances." + child_name,
                         "child domain bindings must exactly cover declarations")
                mapping: dict[str, str] = {}
                for slot, parent_slot in child["domains"].items():
                    _require(parent_slot in domains, path + ".instances." + child_name + ".domains." + slot,
                             "undefined parent domain")
                    requested, supplied = child_signature["domains"][slot], domains[parent_slot]
                    _require(requested["clock"] == "none" or supplied["clock"] == "rising", path + ".instances." + child_name,
                             "child clock consumption incompatible with parent domain")
                    _require(requested["reset"]["kind"] == "none" or requested["reset"] == supplied["reset"],
                             path + ".instances." + child_name, "child reset incompatible with parent domain")
                    mapping[slot] = root_domains[parent_slot]
                child_path = path + "/" + child_name
                children[child_name] = child_path
                elaborate(child["module"], child_path, child["parameters"], parameters, mapping, depth + 1)
            _check_nets(instances[path], instances, cap["max_width"])
        else:
            if implementation["execution"] == "combinational":
                _require(not implementation.get("states"), path + ".states", "combinational module cannot have state")
                _require(all(domain["clock"] == "none" for domain in domains.values()), path + ".domains",
                         "combinational module cannot consume clock/reset")
            else:
                _require(any(domain["clock"] == "rising" for domain in domains.values()), path + ".domains",
                         "clocked module requires a rising-edge domain")
            for name, state in implementation.get("states", {}).items():
                p = path + ".states." + name
                state = deepcopy(state)
                _require(state["domain"] in domains and domains[state["domain"]]["clock"] == "rising", p + ".domain",
                         "state requires a declared consuming clock domain")
                key = "type" if state["kind"] == "register" else "element_type"
                state[key] = resolve_type(state[key], parameters, tensors, used_tensors, p + "." + key,
                                          max_width=cap["max_width"])
                if state["kind"] == "register" and state["reset"]["kind"] == "value":
                    low, high = _raw_range(state[key])
                    _require(low <= state["reset"]["raw_value"] <= high, p + ".reset", "register reset value not representable")
                    _require(domains[state["domain"]]["reset"]["kind"] != "none", p + ".reset",
                             "reset value requires a reset-consuming domain")
                elif state["kind"] != "register":
                    state["depth"] = evaluate(state["depth"], parameters, p + ".depth")
                    natural(state["depth"], p + ".depth", positive=True)
                    if state["kind"] == "memory":
                        state["read_latency_cycles"] = evaluate(state["read_latency_cycles"], parameters, p + ".read_latency_cycles")
                        init = state["initialization"]
                        if init["kind"] == "public_asset":
                            _require(init["asset_id"] in assets, p + ".initialization", "undefined public asset")
                states[name] = state
            for name, rule in implementation.get("numeric_rules", {}).items():
                p = path + ".numeric_rules." + name
                fact(rule["fact"], "guarantee", p + ".fact")
                resolve_type(rule["result_type"], parameters, tensors, used_tensors, p + ".result_type", max_width=cap["max_width"])
                obligations.append({"path": p, "kind": "numeric_implementation", "status": "not_evaluated"})
            _check_timing(implementation, signature["ports"], domains, root_domains, parameters, fact, path)
            obligations.extend({"path": path + ".timing." + name, "kind": "timing_implementation",
                                "status": "not_evaluated"} for name in sorted(implementation.get("timing", {})))
            # Domain compatibility follows bound identity, not local slot spelling.
            bound_ports = deepcopy(signature["ports"])
            for port in bound_ports.values():
                if port["domain"] is not None:
                    port["domain"] = root_domains[port["domain"]]
            bound_states = deepcopy(states)
            for state in bound_states.values():
                state["domain"] = root_domains[state["domain"]]
            obligations.extend(check_tensor_rules(implementation, bound_ports, port_types, bound_states, path, fact))
            obligations.append({"path": path, "kind": "behavioral_implementation", "status": "not_evaluated"})
        _require(used_tensors == set(tensors), path + ".tensor_contracts",
                 "unreferenced local tensor contracts: " + ", ".join(sorted(set(tensors) - used_tensors)))

    elaborate(design["entry"], "self", boundary["parameter_values"], {},
              {name: name for name in top_domains}, 0)
    _check_requirement_map(design, instances, facts)
    return CheckedDesign(design, deepcopy(dict(boundary)), cap, design["entry"], instances, tuple(obligations))


def _check_nets(instance: CheckedInstance, instances: Mapping[str, CheckedInstance], max_width: int) -> None:
    path, body = instance.path, instance.implementation
    sources: set[tuple[str, str]] = set()
    receivers: set[tuple[str, str]] = set()
    stream_sources: set[tuple[str, str]] = set()
    all_sources: set[tuple[str, str]] = set()
    all_receivers: set[tuple[str, str]] = set()

    def endpoint(value: Mapping[str, str], source: bool, p: str) -> tuple[dict[str, Any], dict[str, Any], str | None, tuple[str, str]]:
        owner, name = value["instance"], value["port"]
        _require(owner == "self" or owner in instance.children, p, "endpoint is not self or an immediate child")
        target = instance if owner == "self" else instances[instance.children[owner]]
        _require(name in target.signature["ports"], p, "undefined endpoint port")
        port = target.signature["ports"][name]
        expected = ("input" if source else "output") if owner == "self" else ("output" if source else "input")
        _require(port["direction"] == expected, p, "endpoint direction is not a legal source/sink")
        domain = None if port["domain"] is None else target.domains[port["domain"]]
        return port, target.port_types[name], domain, (owner, name)

    for owner, target in [("self", instance)] + [(name, instances[child]) for name, child in instance.children.items()]:
        for name, port in target.signature["ports"].items():
            source = port["direction"] == ("input" if owner == "self" else "output")
            (all_sources if source else all_receivers).add((owner, name))
    for name, net in sorted(body["nets"].items()):
        p = path + ".nets." + name
        source = net["source"]
        if source["kind"] == "endpoint":
            port, data_type, domain, source_id = endpoint(source["endpoint"], True, p + ".source")
            sources.add(source_id)
            if port["kind"] == "stream":
                _require(source_id not in stream_sources, p, "stream source used by multiple nets")
                stream_sources.add(source_id)
        else:
            data_type = resolve_type(source["type"], instance.parameters, {}, set(), p + ".source.type", max_width=max_width)
            low, high = _raw_range(data_type)
            _require(low <= source["raw_value"] <= high, p + ".source.raw_value", "constant is not representable")
            port, domain = {"kind": "value"}, None
        if port["kind"] == "stream":
            _require(len(net["sinks"]) == 1, p, "stream must be point-to-point")
        for i, sink in enumerate(net["sinks"]):
            sink_port, sink_type, sink_domain, sink_id = endpoint(sink, False, f"{p}.sinks[{i}]")
            _require(sink_id not in receivers, p, "receiver has multiple drivers")
            receivers.add(sink_id)
            _require(port["kind"] == sink_port["kind"] and data_type == sink_type, p, "net type/encoding mismatch")
            _require(source["kind"] == "constant" or domain == sink_domain, p, "net crosses domain identity")
    unused: set[tuple[str, str]] = set()
    for i, value in enumerate(body.get("unused_values", [])):
        port, _, _, source_id = endpoint(value, True, f"{path}.unused_values[{i}]")
        _require(port["kind"] == "value", path + ".unused_values", "unused stream requires an explicit sink")
        _require(source_id not in unused and source_id not in sources, path + ".unused_values", "duplicate or connected unused source")
        unused.add(source_id)
    _require(receivers == all_receivers, path + ".nets", "undriven receivers: " + repr(sorted(all_receivers - receivers)))
    _require(sources | unused == all_sources, path + ".nets", "unconsumed sources: " + repr(sorted(all_sources - sources - unused)))


def _check_timing(body: Mapping[str, Any], ports: Mapping[str, Any], domains: Mapping[str, Any],
                  domain_bindings: Mapping[str, str], parameters: Mapping[str, int], fact: Any, path: str) -> None:
    for name, rule in body.get("timing", {}).items():
        p = path + ".timing." + name
        fact(rule["fact"], "guarantee", p + ".fact")
        assumptions = rule["under_assumptions"]
        _require(len(assumptions) == len(set(assumptions)), p, "duplicate timing assumption")
        for assumption in assumptions:
            fact(assumption, "assumption", p + ".under_assumptions")
        domain = rule["domain"]
        _require(domain in domains and domains[domain]["clock"] == "rising", p + ".domain", "timing needs a clock domain")
        for key, direction in (("input", "input"), ("output", "output")):
            if key not in rule:
                continue
            port = ports.get(rule[key])
            _require(port is not None and port["kind"] == "stream" and port["direction"] == direction
                     and domain_bindings[port["domain"]] == domain_bindings[domain],
                     p + "." + key, "timing port direction/domain mismatch")
        maximum = evaluate(rule["max_cycles"], parameters, p + ".max_cycles")
        if rule["kind"] == "latency":
            minimum = evaluate(rule["min_cycles"], parameters, p + ".min_cycles")
            _require(minimum <= maximum, p, "minimum latency exceeds maximum")
        else:
            natural(maximum, p + ".max_cycles", positive=True)


def _check_requirement_map(design: Mapping[str, Any], instances: Mapping[str, CheckedInstance],
                           facts: Mapping[str, Any]) -> None:
    mapped: set[str] = set()
    modules = design["modules"]
    for i, mapping in enumerate(design["requirement_map"]):
        p = f"$.design.requirement_map[{i}]"
        name = mapping["fact"]
        _require(name in facts, p + ".fact", "unknown public fact")
        _require(name not in mapped, p, "duplicate fact mapping")
        mapped.add(name)
        seen: set[tuple[str, str, str]] = set()
        for target in mapping["targets"]:
            module_id = target["module"]
            _require(module_id in modules, p, "undefined mapping module")
            key = (target["kind"], module_id, target.get("name", ""))
            _require(key not in seen, p, "duplicate mapping target")
            seen.add(key)
            if target["kind"] == "module":
                continue
            expanded = next(value for value in instances.values() if value.module_id == module_id)
            kind = target["kind"]
            names = (expanded.signature["ports"] if kind == "port" else
                     expanded.states if kind == "state" else
                     expanded.implementation.get("nets", {}))
            _require(target["name"] in names, p, "undefined mapping target")
    required = {name for name, value in facts.items() if value.get("required_mapping", False)}
    _require(required <= mapped, "$.design.requirement_map", "missing required fact mappings: " + ", ".join(sorted(required - mapped)))
