"""PC prompt scaffolding never silently repairs candidate structure."""
import copy
import json

import pytest
from jsonschema import Draft202012Validator

from sr2fpga_agent.generation.context_his import FrozenContextSystemHisFacade
from sr2fpga_agent.his_validation import validate_frozen_system_his_payload_h_stages
from sr2fpga_agent.prompts import (
    _frozen_system_his_correction_messages,
    _frozen_system_his_messages,
    _pc_state_ownership_example,
)
from sr2fpga_agent.system_his_schema import load_registered_system_his_schema
from sr2fpga_agent.system_his_v12_checker import _state_names, _validate_instance_state_ownership
from test_sr2fpga_agent_context_his import _context_and_his, _platform


@pytest.mark.parametrize("repair", [False, True])
def test_initial_and_correction_prompts_show_nested_trace_and_actual_root_keys(repair):
    context, payload = _context_and_his()
    messages = (
        _frozen_system_his_correction_messages(context, payload, failed_h_stage="h0", diagnostics=["unexpected root field"])
        if repair else _frozen_system_his_messages(context)
    )
    content = messages[-1]["content"]
    marker = "Merge the following PARTIAL object"
    scaffold = content[content.index(marker):]
    fragment, _ = json.JSONDecoder().raw_decode(scaffold[scaffold.index("{"):])
    assert set(fragment) == {"intent"}
    assert set(fragment["intent"]) == {"requirement_trace"}
    trace = fragment["intent"]["requirement_trace"]
    assert trace["requirement_id"] == payload["intent"]["requirement_trace"]["requirement_id"]
    assert trace["required_facts"] == payload["intent"]["requirement_trace"]["required_facts"]
    schema = load_registered_system_his_schema()
    assert "Allowed root keys: " + ", ".join(sorted(schema["properties"])) in content
    assert "never /requirement_trace" in content
    assert "Do not add fictitious state" in content


def test_ownership_example_is_resolvable_and_reproduces_wrong_owner_failure():
    fragment = _pc_state_ownership_example()
    schema = load_registered_system_his_schema()
    Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/state"}).validate(fragment["state"])
    errors = []
    _validate_instance_state_ownership(fragment["instances"], _state_names(fragment["state"], errors), errors, state=fragment["state"])
    assert errors == []
    fragment["state"]["registers"][0]["owner"] = "top"
    _validate_instance_state_ownership(fragment["instances"], _state_names(fragment["state"], errors), errors, state=fragment["state"])
    assert errors == ["instance 'u_state' owns missing state 'u_state.state_q'"]


def test_generation_preserves_misnested_trace_for_h0_rejection():
    context, payload = _context_and_his()
    malformed = copy.deepcopy(payload)
    malformed["requirement_trace"] = malformed["intent"].pop("requirement_trace")

    class Client:
        calls = 0

        def stream_chat(self, messages):
            self.calls += 1
            return json.dumps(malformed)

    client = Client()
    emitted = FrozenContextSystemHisFacade(client, None, _platform()).emit_his(context)
    assert client.calls == 1
    assert "requirement_trace" in emitted
    assert "requirement_trace" not in emitted["intent"]
    report = validate_frozen_system_his_payload_h_stages(context, emitted, platform=_platform())
    assert report["h0"]["status"] == "fail"
    assert report["h1"]["status"] == "not_run"
