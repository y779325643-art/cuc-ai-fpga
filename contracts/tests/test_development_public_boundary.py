"""Public boundary shape only; neither ready-task nor hardware qualification."""

import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
from referencing.exceptions import Unresolvable
from sr2fpga_agent.contract_registry import ContractRegistry, RegisteredContract

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "contracts/episode-pack/development-public-boundary-v1.example.json"


def example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def contract():
    return ContractRegistry().load_schema("development_public_boundary")


def test_registered_boundary_example_reuses_pc_types():
    boundary = contract()
    assert boundary.version == "development-public-boundary-v1"
    assert boundary.validate(example()) == ()
    assert boundary.dependencies[0].key == "project_contract_2_1"
    assert boundary.document["$defs"]["boundary"]["properties"]["signature"] == {
        "$ref": "urn:sr2fpga:pc:2.1#/$defs/signature_fields"
    }
    assert "signature_fields" not in boundary.document["$defs"]


@pytest.mark.parametrize("field", ["rtl_top", "signature", "parameter_values", "abi"])
def test_boundary_requires_each_field(field):
    payload = example()
    del payload["boundary"][field]
    assert contract().validate(payload)


@pytest.mark.parametrize("path", [
    (), ("boundary",), ("boundary", "signature"),
    ("boundary", "abi"), ("boundary", "abi", "domains", "d"),
    ("boundary", "abi", "ports", "rx"),
])
def test_closed_objects_reject_unknown_fields(path):
    payload = example()
    target = payload
    for key in path:
        target = target[key]
    target["unexpected"] = True
    assert contract().validate(payload)


@pytest.mark.parametrize("field", ["payload", "valid", "ready"])
def test_stream_mapping_requires_all_three_signal_names(field):
    payload = example()
    del payload["boundary"]["abi"]["ports"]["rx"][field]
    assert contract().validate(payload)


@pytest.mark.parametrize("value", [-1, True, 1.5, {"param": "W"}])
def test_top_parameter_values_are_concrete_nonnegative_integers(value):
    payload = example()
    payload["boundary"]["parameter_values"]["W"] = value
    assert contract().validate(payload)


def test_inherited_pc_signature_validation_is_active():
    payload = example()
    payload["boundary"]["signature"]["ports"]["rx"]["direction"] = "inout"
    assert contract().validate(payload)


def test_value_ports_and_nonconsuming_domain_pin_shapes():
    payload = example()
    boundary = payload["boundary"]
    boundary["signature"]["domains"]["d"] = {"clock": "none", "reset": {"kind": "none"}}
    boundary["signature"]["ports"] = {
        "x": {"kind": "value", "direction": "input",
              "type": {"kind": "uint", "width": 8}, "domain": "d"},
    }
    boundary["abi"]["domains"]["d"] = {"clock": None, "reset": None}
    boundary["abi"]["ports"] = {"x": {"signal": "input_value"}}
    assert contract().validate(payload) == ()
    boundary["abi"]["ports"]["x"]["valid"] = "invalid_mixed_mapping"
    assert contract().validate(payload)


def test_scope_cannot_claim_task_readiness():
    payload = example()
    payload["validation_scope"] = "ready"
    assert contract().validate(payload)
    payload = example()
    payload["contract_version"] = "episode-pack-v1"
    assert contract().validate(payload)


def test_cross_field_errors_are_explicitly_outside_shape_scope():
    # Preserve the scope limit: a shape-only pass cannot certify these cases.
    payload = example()
    boundary = payload["boundary"]
    boundary["parameter_values"] = {}
    boundary["abi"]["ports"]["tx"]["payload"] = "in_data"
    boundary["signature"]["ports"]["rx"]["domain"] = "MissingDomain"
    assert contract().validate(payload) == ()


def test_unregistered_schema_uri_never_fetches_network(tmp_path, monkeypatch):
    def forbidden_network(*args, **kwargs):
        pytest.fail("schema resolution attempted network access")

    monkeypatch.setattr(socket, "create_connection", forbidden_network)
    document = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": "https://unregistered.invalid/schema"}
    path = tmp_path / "unregistered.schema.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    unregistered = RegisteredContract("probe", "probe", path, document)
    with pytest.raises(Unresolvable):
        unregistered.validate({})


def test_dependency_change_invalidates_parent_validator_cache(tmp_path):
    registry = ContractRegistry()
    original = registry.load_schema("project_contract_2_1")
    document = deepcopy(original.document)
    dep_path = tmp_path / "pc.schema.json"
    parent_path = tmp_path / "parent.schema.json"
    parent_doc = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                  "$ref": "urn:sr2fpga:pc:2.1#/$defs/identifier"}
    parent_path.write_text(json.dumps(parent_doc), encoding="utf-8")
    dep_path.write_text(json.dumps(document), encoding="utf-8")
    dep = RegisteredContract("pc", original.version, dep_path, document)
    parent = RegisteredContract("parent", "probe", parent_path, parent_doc, (dep,))
    assert parent.validate("ValidName") == ()
    changed = deepcopy(document)
    changed["$defs"]["identifier"]["const"] = "OtherName"
    dep_path.write_text(json.dumps(changed), encoding="utf-8")
    dep2 = RegisteredContract("pc", original.version, dep_path, changed)
    parent2 = RegisteredContract("parent", "probe", parent_path, parent_doc, (dep2,))
    assert parent2.validate("ValidName")
