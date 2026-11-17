"""Execute the public, task-independent PC declaration tutorials without EDA."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.pc.context import check_task_design, load_public_task
from sr2fpga_agent.pc.inputs import ParseLimits, TrustedContext, TrustedSource
from sr2fpga_agent.pc.semantics import PcSemanticError


EXAMPLES = Path(__file__).parent / "fixtures" / "pc21_public_rules"


def _read(name):
    return json.loads((EXAMPLES / name).read_bytes())


def _task(kind, *, requirements=None):
    name = f"public-context-{kind}.json"
    content = ((EXAMPLES / name).read_bytes() if requirements is None
               else json.dumps(requirements).encode("utf-8"))
    sources = TrustedContext(
        TrustedSource("public-rules-requirements", content),
        TrustedSource("public-rules-target", (EXAMPLES / "target-profile.json").read_bytes()),
        TrustedSource("public-rules-capability", (EXAMPLES / "capability-profile.json").read_bytes()),
    )
    return load_public_task(sources, asset_root=None, limits=ParseLimits(200_000, 64))


def _schema_valid(design):
    errors = ContractRegistry().load_schema("design_proposal_2_1").validate(design)
    assert not errors, errors


@pytest.mark.parametrize(("kind", "filename", "instances"), [
    ("compute", "compute-multioutput.design.json", 1),
    ("fifo", "fifo.design.json", 1),
    ("fifo", "fifo-renamed-child.design.json", 2),
])
def test_public_examples_pass_registered_admission(kind, filename, instances):
    task = _task(kind)
    design = _read(filename)
    original = deepcopy(design)
    _schema_valid(design)
    checked = check_task_design(design, task)
    assert len(checked.instances) == instances
    assert set(checked.instances["self"].port_widths.values()) == {18}
    assert checked.scope == "schema_and_listed_static_checks_only"
    assert "algorithm_correctness" in checked.deferred_checks
    assert all(item["status"] == "not_evaluated" for item in checked.verification_obligations)
    assert design == original


@pytest.mark.parametrize("reference", ["Vector", "sample_data"])
def test_main_relation_uses_logical_ports_not_tensor_or_abi_names(reference):
    design = _read("compute-multioutput.design.json")
    design["modules"]["Work"]["implementation"]["tensor_rules"]["operation"]["inputs"] = [reference]
    _schema_valid(design)
    with pytest.raises(PcSemanticError, match=f"unknown tensor port {reference}"):
        check_task_design(design, _task("compute"))


@pytest.mark.parametrize(("damage", "message"), [
    ("reused_input", "tensor port belongs to more than one main relation"),
    ("missing_output", "every tensor port must belong to exactly one main relation; missing: result_b"),
])
def test_main_relations_are_a_unique_complete_port_partition(damage, message):
    design = _read("compute-multioutput.design.json")
    rules = design["modules"]["Work"]["implementation"]["tensor_rules"]
    if damage == "reused_input":
        # Sharing the mathematical input does not mean listing the same local
        # port in two primary declaration relations. One multi-output relation
        # in the positive example accounts for both outputs without duplication.
        rules.clear()
        rules.update({
            name: {"kind": "compute", "fact": "Relation", "inputs": ["sample"], "outputs": [output]}
            for name, output in (("first", "result_a"), ("second", "result_b"))
        })
    else:
        rules["operation"]["outputs"] = ["result_a"]
    _schema_valid(design)
    with pytest.raises(PcSemanticError, match=message):
        check_task_design(design, _task("compute"))


def test_a_relation_cannot_repeat_a_local_port_within_its_lists():
    design = _read("compute-multioutput.design.json")
    design["modules"]["Work"]["implementation"]["tensor_rules"]["operation"]["inputs"] *= 2
    _schema_valid(design)
    with pytest.raises(PcSemanticError, match="duplicate tensor relation port"):
        check_task_design(design, _task("compute"))


def test_a_buffer_input_must_be_a_local_input_not_the_output_it_buffers():
    design = _read("fifo.design.json")
    design["modules"]["Queue"]["implementation"]["buffer_rules"]["storage"]["input"] = "egress"
    _schema_valid(design)
    with pytest.raises(PcSemanticError, match="wrong direction for egress"):
        check_task_design(design, _task("fifo"))


def test_removing_the_binding_does_not_remove_the_tensor_fifo_obligation():
    design = _read("fifo.design.json")
    del design["modules"]["Queue"]["implementation"]["buffer_rules"]
    _schema_valid(design)
    with pytest.raises(PcSemanticError, match="tensor FIFO requires a buffer binding"):
        check_task_design(design, _task("fifo"))


def test_fifo_storage_must_match_the_complete_beat_not_only_its_width():
    design = _read("fifo.design.json")
    design["modules"]["Queue"]["implementation"]["states"]["queue"]["element_type"] = {
        "kind": "uint", "width": 18,
    }
    _schema_valid(design)
    with pytest.raises(PcSemanticError, match="buffer FIFO and both ports must carry identical complete tensor beats"):
        check_task_design(design, _task("fifo"))


def test_fifo_storage_and_streams_must_have_the_same_bound_domain():
    requirements = _read("public-context-fifo.json")
    requirements["boundary"]["signature"]["domains"]["other_domain"] = deepcopy(
        requirements["boundary"]["signature"]["domains"]["clock_domain"]
    )
    requirements["boundary"]["abi"]["domains"]["other_domain"] = {
        "clock": "other_clk", "reset": "other_rst_n",
    }
    design = _read("fifo.design.json")
    design["modules"]["Queue"]["implementation"]["states"]["queue"]["domain"] = "other_domain"
    _schema_valid(design)
    with pytest.raises(PcSemanticError, match="buffer must stay in one domain"):
        check_task_design(design, _task("fifo", requirements=requirements))


@pytest.mark.parametrize(("depth", "read_mode"), [(1, "registered"), (4, "fallthrough")])
def test_fifo_names_depth_and_read_mode_are_not_a_reference_architecture(depth, read_mode):
    design = _read("fifo.design.json")
    module = design["modules"].pop("Queue")
    design["entry"] = "AnotherLegalModule"
    design["modules"][design["entry"]] = module
    body = module["implementation"]
    state = body["states"].pop("queue")
    state.update(depth=depth, read_mode=read_mode)
    body["states"]["another_state"] = state
    binding = body["buffer_rules"].pop("storage")
    binding["state"] = "another_state"
    body["buffer_rules"]["another_binding"] = binding
    for mapping in design["requirement_map"]:
        mapping["targets"][0]["module"] = design["entry"]
    _schema_valid(design)
    checked = check_task_design(design, _task("fifo"))
    assert checked.instances["self"].states["another_state"]["depth"] == depth
    assert checked.scope == "schema_and_listed_static_checks_only"
