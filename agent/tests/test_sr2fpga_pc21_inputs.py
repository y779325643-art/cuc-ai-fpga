"""Input tests from plan §4.1 and architecture §6.1–6.2 / V02–V03.

The deliberately empty structural fixture tests serialization only. It is not
an AI task, a semantically checked PC, or a buildable reference project.
"""

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.pc import (
    BindingError, ParseLimits, PcParseError, PcSchemaError, PcSemanticError, TrustedContext,
    TrustedSource, assemble_project_contract, parse_design_proposal,
    parse_project_contract,
)


LIMITS = ParseLimits(max_bytes=100_000, max_depth=64)
DESIGN = {
    "entry": "Top",
    "modules": {"Top": {
        "signature": {"source": "requirement_boundary"},
        "implementation": {"kind": "structural", "instances": {}, "nets": {}},
    }},
    "requirement_map": [],
}
CONTEXT = TrustedContext(
    TrustedSource("requirements-dev", b'{"public": true}\n'),
    TrustedSource("target-dev", b'{"target": "development"}'),
    TrustedSource("capability-dev", b'{"capability": "development"}'),
)


def encoded(payload):
    return json.dumps(payload).encode("utf-8")


def assembled():
    return assemble_project_contract(encoded(DESIGN), CONTEXT, limits=LIMITS)


def design_with_worker_instance(target="Worker"):
    design = deepcopy(DESIGN)
    design["modules"]["Top"]["implementation"]["instances"]["u_worker"] = {
        "module": target,
        "parameters": {},
        "domains": {},
    }
    design["modules"]["Worker"] = {
        "signature": {
            "source": "declared",
            "parameters": {},
            "domains": {},
            "ports": {},
        },
        "implementation": {
            "kind": "behavioral",
            "execution": "combinational",
            "intent": "Schema fixture for instance-reference tests.",
        },
    }
    return design


def declared_structural_module(instances=None):
    return {
        "signature": {
            "source": "declared",
            "parameters": {},
            "domains": {},
            "ports": {},
        },
        "implementation": {
            "kind": "structural",
            "instances": instances or {},
            "nets": {},
        },
    }


def instance_of(module):
    return {"module": module, "parameters": {}, "domains": {}}


def test_design_and_controller_bound_roundtrip():
    assert parse_design_proposal(encoded(DESIGN), limits=LIMITS) == DESIGN
    pc = assembled()
    assert pc["bindings"]["requirements"]["sha256"] == hashlib.sha256(
        CONTEXT.requirements.content
    ).hexdigest()
    assert parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS) == pc


def test_public_smoke_fixture_is_a_valid_design_proposal():
    fixture = Path(__file__).parent / "fixtures" / "pc21_input_smoke" / "design.json"
    assert parse_design_proposal(fixture.read_bytes(), limits=LIMITS) == DESIGN


def test_registered_schema_design_definitions_are_identical():
    registry = ContractRegistry()
    full = registry.load_schema("project_contract_2_1").document
    proposal = registry.load_schema("design_proposal_2_1").document
    assert proposal["$defs"] == full["$defs"]
    assert proposal["$ref"] == full["properties"]["design"]["$ref"]


@pytest.mark.parametrize("raw", [
    b'{"entry":"A","entry":"B"}',
    b'{"nested":{"key":1,"key":2}}',
    b'{"key":1,"\\u006bey":2}',
    b'{"value":NaN}', b'{"value":Infinity}', b'{"value":-Infinity}',
    b'{"value":1.0}', b'{"value":1e0}', b'{"value":1e999}',
    b'{"value":"\\ud800"}', b'{"\\udfff":0}',
    b'{"value":"\\ud800x\\udc00"}',
    b'{"value":}', b'[]', b'null', b'\xff',
])
def test_strict_json_rejects_before_schema(raw):
    with pytest.raises(PcParseError):
        parse_design_proposal(raw, limits=LIMITS)


def test_size_and_depth_limits_are_enforced_before_schema():
    raw = encoded(DESIGN)
    with pytest.raises(PcParseError, match="max_bytes"):
        parse_design_proposal(raw, limits=ParseLimits(len(raw) - 1, 64))
    with pytest.raises(PcParseError, match="max_depth"):
        parse_design_proposal(b'{"nested":' + b'[' * 1000 + b'0' + b']' * 1000 + b'}',
                              limits=ParseLimits(10_000, 16))
    assert parse_design_proposal(raw, limits=ParseLimits(len(raw), 5)) == DESIGN


def test_brackets_and_escaped_quotes_in_notes_do_not_count_as_depth():
    design = {**DESIGN, "notes": '[\\\"' * 100}
    assert parse_design_proposal(encoded(design), limits=ParseLimits(10_000, 5)) == design


def test_valid_escaped_unicode_surrogate_pair_is_accepted():
    design = {**DESIGN, "notes": "\U0001f600"}
    assert parse_design_proposal(encoded(design), limits=LIMITS) == design


@pytest.mark.parametrize("extra", [{"bindings": {}}, {"schema_version": "sr2fpga-pc-2.1"}])
def test_model_cannot_supply_controller_fields(extra):
    with pytest.raises(PcSchemaError):
        assemble_project_contract(encoded({**DESIGN, **extra}), CONTEXT, limits=LIMITS)


def test_wrapped_design_is_not_model_format():
    with pytest.raises(PcSchemaError):
        parse_design_proposal(encoded({"design": DESIGN}), limits=LIMITS)


@pytest.mark.parametrize("entry", ["MissingTop", "top"])
def test_entry_must_name_an_exact_defined_module(entry):
    design = {**DESIGN, "entry": entry}

    with pytest.raises(PcSemanticError, match=f"entry module is not defined: {entry}"):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_saved_pc_rechecks_entry_module_reference():
    pc = assembled()
    pc["design"]["entry"] = "MissingTop"

    with pytest.raises(PcSemanticError, match="entry module is not defined: MissingTop"):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


def test_structural_instance_may_reference_a_defined_behavioral_module():
    design = design_with_worker_instance()

    assert assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)["design"] == design


def test_structural_instance_module_must_be_defined():
    design = design_with_worker_instance("MissingWorker")

    with pytest.raises(
        PcSemanticError,
        match=r"instance module is not defined: Top\.u_worker -> MissingWorker",
    ):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_saved_pc_rechecks_instance_module_reference():
    pc = assemble_project_contract(
        encoded(design_with_worker_instance()), CONTEXT, limits=LIMITS
    )
    pc["design"]["modules"]["Top"]["implementation"]["instances"]["u_worker"][
        "module"
    ] = "MissingWorker"

    with pytest.raises(PcSemanticError, match="MissingWorker"):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


def test_module_cannot_instantiate_itself():
    design = deepcopy(DESIGN)
    design["modules"]["Top"]["implementation"]["instances"]["u_self"] = instance_of(
        "Top"
    )

    with pytest.raises(PcSemanticError, match="recursive module hierarchy: Top -> Top"):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_mutually_recursive_modules_report_the_cycle_path():
    design = deepcopy(DESIGN)
    design["modules"]["Top"]["implementation"]["instances"]["u_worker"] = instance_of(
        "Worker"
    )
    design["modules"]["Worker"] = declared_structural_module(
        {"u_top": instance_of("Top")}
    )

    with pytest.raises(
        PcSemanticError,
        match="recursive module hierarchy: Top -> Worker -> Top",
    ):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_multiple_paths_may_share_one_completed_module():
    design = deepcopy(DESIGN)
    top_instances = design["modules"]["Top"]["implementation"]["instances"]
    top_instances.update({
        "u_left": instance_of("Left"),
        "u_right": instance_of("Right"),
    })
    design["modules"]["Left"] = declared_structural_module(
        {"u_shared": instance_of("Shared")}
    )
    design["modules"]["Right"] = declared_structural_module(
        {"u_shared": instance_of("Shared")}
    )
    design["modules"]["Shared"] = declared_structural_module()

    assert assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)["design"] == design


def test_saved_pc_rechecks_recursive_module_hierarchy():
    pc = assembled()
    pc["design"]["modules"]["Top"]["implementation"]["instances"]["u_self"] = (
        instance_of("Top")
    )

    with pytest.raises(PcSemanticError, match="Top -> Top"):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


def test_same_module_definition_may_be_instantiated_multiple_times():
    design = design_with_worker_instance()
    design["modules"]["Top"]["implementation"]["instances"]["u_worker_2"] = (
        instance_of("Worker")
    )

    assert assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)["design"] == design


def test_isolated_module_is_rejected_as_unreachable():
    design = deepcopy(DESIGN)
    design["modules"]["UnusedRamWrapper"] = declared_structural_module()

    with pytest.raises(
        PcSemanticError,
        match="module definitions are unreachable from entry Top: UnusedRamWrapper",
    ):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_unreachable_subtree_reports_all_modules_in_stable_order():
    design = deepcopy(DESIGN)
    design["modules"]["UnusedB"] = declared_structural_module()
    design["modules"]["UnusedA"] = declared_structural_module(
        {"u_b": instance_of("UnusedB")}
    )

    with pytest.raises(
        PcSemanticError,
        match="module definitions are unreachable from entry Top: UnusedA, UnusedB",
    ):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_saved_pc_rechecks_module_reachability():
    pc = assembled()
    pc["design"]["modules"]["Unused"] = declared_structural_module()

    with pytest.raises(PcSemanticError, match="unreachable from entry Top: Unused"):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


def test_entry_signature_must_come_from_requirement_boundary():
    design = deepcopy(DESIGN)
    design["modules"]["Top"]["signature"] = {
        "source": "declared",
        "parameters": {},
        "domains": {},
        "ports": {},
    }

    with pytest.raises(
        PcSemanticError,
        match=(
            "module signature source mismatch: Top expected "
            "requirement_boundary, got declared"
        ),
    ):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_internal_signature_must_be_declared():
    design = design_with_worker_instance()
    design["modules"]["Worker"]["signature"] = {"source": "requirement_boundary"}

    with pytest.raises(
        PcSemanticError,
        match=(
            "module signature source mismatch: Worker expected declared, "
            "got requirement_boundary"
        ),
    ):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_saved_pc_rechecks_signature_sources():
    pc = assemble_project_contract(
        encoded(design_with_worker_instance()), CONTEXT, limits=LIMITS
    )
    pc["design"]["modules"]["Worker"]["signature"] = {
        "source": "requirement_boundary"
    }

    with pytest.raises(PcSemanticError, match="Worker expected declared"):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


def design_with_parameterized_worker(parameter_bindings):
    design = design_with_worker_instance()
    design["modules"]["Worker"]["signature"]["parameters"] = {
        "DEPTH": {"minimum": 1, "maximum": 4096}
    }
    design["modules"]["Top"]["implementation"]["instances"]["u_worker"][
        "parameters"
    ] = parameter_bindings
    return design


def test_instance_parameter_name_may_match_target_declaration():
    design = design_with_parameterized_worker({"DEPTH": 1024})

    assert assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)["design"] == design


@pytest.mark.parametrize("bindings,missing", [
    ({"DEPTH": 1024}, "WIDTH"),
    ({}, "DEPTH, WIDTH"),
])
def test_instance_must_bind_all_declared_parameters(bindings, missing):
    design = design_with_parameterized_worker(bindings)
    # Reverse declaration order: diagnostics must still be stable by name.
    design["modules"]["Worker"]["signature"]["parameters"] = {
        "WIDTH": {"minimum": 1, "maximum": 64},
        "DEPTH": {"minimum": 1, "maximum": 4096},
    }
    with pytest.raises(PcSemanticError) as error:
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)
    assert str(error.value) == (
        "instance parameter bindings are missing: Top.u_worker -> Worker: " + missing
    )


def test_each_instance_must_supply_its_own_parameter_bindings():
    design = design_with_parameterized_worker({"DEPTH": 1024})
    design["modules"]["Top"]["implementation"]["instances"]["u_worker_2"] = (
        instance_of("Worker")
    )
    with pytest.raises(PcSemanticError, match="Top.u_worker_2 -> Worker: DEPTH"):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)
    design["modules"]["Top"]["implementation"]["instances"]["u_worker_2"][
        "parameters"
    ] = {"DEPTH": 2048}
    assert assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)["design"] == design


def test_saved_pc_rejects_removed_parameter_binding():
    pc = assemble_project_contract(
        encoded(design_with_parameterized_worker({"DEPTH": 1024})), CONTEXT, limits=LIMITS
    )
    pc["design"]["modules"]["Top"]["implementation"]["instances"]["u_worker"][
        "parameters"
    ].clear()
    with pytest.raises(PcSemanticError, match="bindings are missing: Top.u_worker -> Worker: DEPTH"):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


def test_instance_parameter_name_must_be_declared_by_target_module():
    design = design_with_parameterized_worker({"DEPTH": 1024, "UNKNOWN": 3})

    with pytest.raises(
        PcSemanticError,
        match=(
            "instance parameters are not declared by target module: "
            "Top.u_worker -> Worker: UNKNOWN"
        ),
    ):
        assemble_project_contract(encoded(design), CONTEXT, limits=LIMITS)


def test_saved_pc_rechecks_instance_parameter_names():
    pc = assemble_project_contract(
        encoded(design_with_parameterized_worker({"DEPTH": 1024})),
        CONTEXT,
        limits=LIMITS,
    )
    pc["design"]["modules"]["Top"]["implementation"]["instances"]["u_worker"][
        "parameters"
    ]["UNKNOWN"] = 3

    with pytest.raises(PcSemanticError, match="Worker: UNKNOWN"):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


@pytest.mark.parametrize("version", ["sr2fpga-pc-2.0", "system-his-v1.2", "sr2fpga-pc-2.2", ""])
def test_old_unknown_and_empty_versions_are_rejected(version):
    pc = assembled()
    pc["schema_version"] = version
    with pytest.raises(PcSchemaError):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


@pytest.mark.parametrize("name", ["requirements", "target_profile", "capability_profile"])
@pytest.mark.parametrize("field,value", [("id", "candidate-selected"), ("sha256", "0" * 64)])
def test_each_binding_identity_and_hash_is_checked(name, field, value):
    pc = assembled()
    pc["bindings"][name][field] = value
    with pytest.raises(BindingError, match=name):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


@pytest.mark.parametrize("name", ["requirements", "target_profile", "capability_profile"])
def test_source_byte_changes_invalidate_saved_pc_even_when_json_meaning_is_same(name):
    source = getattr(CONTEXT, name)
    changed = replace(CONTEXT, **{name: replace(source, content=source.content + b' ')})
    with pytest.raises(BindingError, match=name):
        parse_project_contract(encoded(assembled()), changed, limits=LIMITS)


def test_full_pc_schema_is_rechecked_after_loading():
    pc = assembled()
    pc["design"]["modules"]["Top"]["signature"]["source"] = "candidate_boundary"
    with pytest.raises(PcSchemaError):
        parse_project_contract(encoded(pc), CONTEXT, limits=LIMITS)


def test_parsed_result_does_not_mutate_controller_context():
    pc = assembled()
    pc["bindings"]["requirements"]["id"] = "changed"
    assert assembled()["bindings"]["requirements"]["id"] == CONTEXT.requirements.id


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_resource_policy_requires_explicit_positive_integers(value):
    with pytest.raises(ValueError):
        ParseLimits(value, 64)
    with pytest.raises(ValueError):
        ParseLimits(10_000, value)


def test_trusted_content_requires_immutable_original_bytes():
    with pytest.raises(TypeError):
        TrustedSource("public", {"not": "original bytes"})
