"""Boundary port mappings: public schema first, then declared-port relations."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.public_boundary import (
    check_public_boundary_domains,
    check_public_boundary_ports,
)


EXAMPLE = Path(__file__).resolve().parents[2] / (
    "contracts/episode-pack/development-public-boundary-v1.example.json"
)


@pytest.fixture
def payload():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_valid_stream_boundary_passes_without_mutation(payload):
    original = deepcopy(payload)
    assert check_public_boundary_ports(payload) == ()
    assert payload == original


def test_missing_port_mapping_is_rejected_even_when_schema_passes(payload):
    del payload["boundary"]["abi"]["ports"]["rx"]
    assert ContractRegistry().load_schema("development_public_boundary").validate(payload) == ()
    assert check_public_boundary_ports(payload) == (
        "$.boundary.abi.ports: missing port mappings: rx",
    )


def test_unknown_port_mapping_is_rejected(payload):
    payload["boundary"]["abi"]["ports"]["unknown"] = {"signal": "unused"}
    assert check_public_boundary_ports(payload) == (
        "$.boundary.abi.ports: mappings for undeclared ports: unknown",
    )


def test_missing_and_extra_mappings_have_stable_diagnostics(payload):
    payload["boundary"]["abi"]["ports"] = {
        "z": {"signal": "extra_z"}, "a": {"signal": "extra_a"},
    }
    expected = (
        "$.boundary.abi.ports: missing port mappings: rx, tx",
        "$.boundary.abi.ports: mappings for undeclared ports: a, z",
    )
    assert check_public_boundary_ports(payload) == expected
    payload["boundary"]["abi"]["ports"] = dict(
        reversed(list(payload["boundary"]["abi"]["ports"].items()))
    )
    assert check_public_boundary_ports(payload) == expected


@pytest.mark.parametrize("direction", ["input", "output"])
def test_stream_cannot_use_value_mapping(payload, direction):
    payload["boundary"]["signature"]["ports"]["rx"]["direction"] = direction
    payload["boundary"]["abi"]["ports"]["rx"] = {"signal": "in_data"}
    assert check_public_boundary_ports(payload) == (
        "$.boundary.abi.ports.rx: stream port requires payload/valid/ready mapping",
    )


@pytest.mark.parametrize("direction", ["input", "output"])
def test_value_mapping_matches_value_port(payload, direction):
    payload["boundary"]["signature"]["ports"]["rx"] = {
        "kind": "value", "direction": direction,
        "type": {"kind": "uint", "width": 8}, "domain": "d",
    }
    assert check_public_boundary_ports(payload) == (
        "$.boundary.abi.ports.rx: value port requires signal mapping",
    )
    payload["boundary"]["abi"]["ports"]["rx"] = {"signal": "value_data"}
    assert check_public_boundary_ports(payload) == ()


@pytest.mark.parametrize("invalid", [None, [], {}, {"boundary": {}}])
def test_invalid_schema_returns_errors_before_accessing_fields(invalid):
    expected = ContractRegistry().load_schema("development_public_boundary").validate(invalid)
    assert expected
    assert check_public_boundary_ports(invalid) == expected


def test_incomplete_stream_mapping_is_still_a_schema_error(payload):
    del payload["boundary"]["abi"]["ports"]["rx"]["ready"]
    expected = ContractRegistry().load_schema("development_public_boundary").validate(payload)
    assert expected
    assert check_public_boundary_ports(payload) == expected


def test_empty_interface_has_no_mapping_requirement(payload):
    payload["boundary"]["signature"]["ports"] = {}
    payload["boundary"]["abi"]["ports"] = {}
    assert check_public_boundary_ports(payload) == ()


def test_port_check_does_not_claim_pin_uniqueness_or_domain_validation(payload):
    payload["boundary"]["abi"]["ports"]["tx"]["payload"] = "in_data"
    payload["boundary"]["signature"]["ports"]["rx"]["domain"] = "MissingDomain"
    assert check_public_boundary_ports(payload) == ()


@pytest.mark.parametrize("clock,reset,pins", [
    ("rising", {"kind": "sync", "polarity": "active_low"}, {"clock": "clk", "reset": "rst_n"}),
    ("rising", {"kind": "sync", "polarity": "active_high"}, {"clock": "clk", "reset": "rst"}),
    ("rising", {"kind": "none"}, {"clock": "clk", "reset": None}),
    ("none", {"kind": "none"}, {"clock": None, "reset": None}),
    ("rising", {"kind": "async", "polarity": "active_low", "release": "synchronous_to_domain"},
     {"clock": "clk", "reset": "rst_n"}),
])
def test_domain_pin_presence_matches_declaration(payload, clock, reset, pins):
    payload["boundary"]["signature"]["domains"]["d"] = {"clock": clock, "reset": reset}
    payload["boundary"]["abi"]["domains"]["d"] = pins
    original = deepcopy(payload)
    assert check_public_boundary_domains(payload) == ()
    assert payload == original


def test_missing_domain_mapping_is_rejected(payload):
    payload["boundary"]["abi"]["domains"] = {}
    assert check_public_boundary_domains(payload) == (
        "$.boundary.abi.domains: missing domain mappings: d",
    )


def test_extra_domain_mapping_is_rejected(payload):
    payload["boundary"]["abi"]["domains"]["extra"] = {"clock": None, "reset": None}
    assert check_public_boundary_domains(payload) == (
        "$.boundary.abi.domains: mappings for undeclared domains: extra",
    )


def test_domain_mapping_diagnostics_are_stable(payload):
    payload["boundary"]["signature"]["domains"] = {
        "z": {"clock": "none", "reset": {"kind": "none"}},
        "a": {"clock": "none", "reset": {"kind": "none"}},
    }
    expected = (
        "$.boundary.abi.domains: missing domain mappings: a, z",
        "$.boundary.abi.domains: mappings for undeclared domains: d",
    )
    assert check_public_boundary_domains(payload) == expected
    payload["boundary"]["signature"]["domains"] = dict(
        reversed(list(payload["boundary"]["signature"]["domains"].items()))
    )
    assert check_public_boundary_domains(payload) == expected


@pytest.mark.parametrize("signal,kind", [("clock", "rising"), ("reset", "sync")])
def test_consuming_domain_requires_named_pin(payload, signal, kind):
    payload["boundary"]["abi"]["domains"]["d"][signal] = None
    assert check_public_boundary_domains(payload) == (
        f"$.boundary.abi.domains.d.{signal}: expected a pin name for {signal}={kind}",
    )


@pytest.mark.parametrize("signal", ["clock", "reset"])
def test_nonconsuming_domain_requires_null_pin(payload, signal):
    payload["boundary"]["signature"]["domains"]["d"] = {
        "clock": "none", "reset": {"kind": "none"},
    }
    payload["boundary"]["abi"]["domains"]["d"] = {"clock": None, "reset": None}
    payload["boundary"]["abi"]["domains"]["d"][signal] = "unexpected_pin"
    assert check_public_boundary_domains(payload) == (
        f"$.boundary.abi.domains.d.{signal}: expected null for {signal}=none",
    )


def test_domain_without_clock_cannot_consume_reset(payload):
    payload["boundary"]["signature"]["domains"]["d"]["clock"] = "none"
    payload["boundary"]["abi"]["domains"]["d"]["clock"] = None
    assert check_public_boundary_domains(payload) == (
        "$.boundary.signature.domains.d: clock=none requires reset=none",
    )


@pytest.mark.parametrize("invalid", [None, [], {}, {"boundary": {}}])
def test_domain_check_stops_on_schema_failure(invalid):
    expected = ContractRegistry().load_schema("development_public_boundary").validate(invalid)
    assert expected
    assert check_public_boundary_domains(invalid) == expected


def test_domain_mapping_cannot_omit_explicit_null_field(payload):
    del payload["boundary"]["abi"]["domains"]["d"]["reset"]
    expected = ContractRegistry().load_schema("development_public_boundary").validate(payload)
    assert expected
    assert check_public_boundary_domains(payload) == expected


def test_empty_domain_tables_pass_this_scoped_check(payload):
    payload["boundary"]["signature"]["domains"] = {}
    payload["boundary"]["abi"]["domains"] = {}
    assert check_public_boundary_domains(payload) == ()
