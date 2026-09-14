import copy
from dataclasses import replace
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore, ArtifactIntegrityError
from sr2fpga_agent.pc_assembly import (
    HOST_BINDINGS, PCDecisionGenerator, _hash, _json_bytes, assemble_pc,
    decision_messages, record_pc_assembly, read_verified_pc_assembly,
)
from test_sr2fpga_agent_context_his import _context_and_his, _platform


def _input():
    """Test-only fixture projection, not an automatic legacy migration API."""
    context, pc = _context_and_his()
    decisions = copy.deepcopy({key: pc[key] for key in (
        "intent", "top", "components", "instances", "state", "data_flow", "control_flow",
        "timing", "resources", "verification",
    )})
    for field in ("user_prompt", "requirement_trace", "target_platform", "declared_task_type"):
        decisions["intent"].pop(field, None)
    for instance in decisions["instances"]:
        instance.pop("owns_state", None)
    decisions["timing"].pop("constraints", None)
    decisions["resources"].pop("target_platform", None)
    for field in ("testbench", "acceptance_obligation", "checks", "expected_behavior", "test_pass_means"):
        decisions["verification"].pop(field, None)
    bindings = {}
    for fact, pointers in pc["intent"]["requirement_trace"]["fact_to_his"].items():
        if fact in HOST_BINDINGS:
            continue
        bindings[fact] = []
        for pointer in pointers:
            parts = pointer.lstrip("/").split("/")
            value = pc
            collection = []
            entry = {}
            for index, part in enumerate(parts):
                if isinstance(value, list):
                    value = value[int(part)]
                    entry = {"collection": ".".join(collection), "name": value["name"], "path": parts[index + 1:]}
                    break
                collection.append(part)
                value = value[part]
            if not entry and isinstance(value, list):
                assert len(value) == 1 and "name" in value[0]
                entry = {"collection": ".".join(parts), "name": value[0]["name"], "path": []}
            if not entry:
                entry = {"collection": parts[0], "path": parts[1:]}
            bindings[fact].append(entry)
    return context, {"decisions": decisions, "fact_bindings": bindings}


def test_assembly_valid_pc_is_deterministic_and_inputs_unchanged():
    context, body = _input()
    before = copy.deepcopy(body)
    first = assemble_pc(context, _platform(), json.dumps(body))
    second = assemble_pc(context, _platform(), json.dumps(body, sort_keys=True))
    assert first.status == "pc_valid", first.diagnostics
    assert first.pc == second.pc
    assert body == before
    assert first.pc["intent"]["user_prompt"] == context.public_text
    assert first.binding_sources["acceptance_criteria"] == "host_copy"
    assert first.binding_sources["data_width_bits"] == "model"
    assert first.field_sources["/schema_version"] == "derived"
    assert first.field_sources["/intent/user_prompt"] == "frozen"
    assert first.field_sources["/top/ports/3/width"] == "model"


@pytest.mark.parametrize("field", ["schema_version", "artifacts", "requirement_trace", "official_outcome"])
def test_controlled_root_fields_are_rejected(field):
    context, body = _input()
    body["decisions"][field] = {}
    result = assemble_pc(context, _platform(), json.dumps(body))
    assert result.status == "decision_schema_failed"
    assert result.pc is None and result.validation_report is None


@pytest.mark.parametrize("raw", ["not json", '{"decisions":{},"decisions":{}}', '{"n":NaN}', b'\xff'])
def test_invalid_input_is_retained_as_failure_not_a_pc(raw, tmp_path):
    context, _ = _input()
    store = ArtifactStore(tmp_path / "store")
    record, ref = record_pc_assembly(store, "attempt", context, _platform(), raw)
    assert record["status"] == "input_parse_failed"
    assert record["pc_ref"] is None
    assert read_verified_pc_assembly(store, ref) == record


def test_unknown_owner_is_not_repaired():
    context, body = _input()
    body["decisions"]["state"]["counters"][0]["owner"] = "ghost"
    result = assemble_pc(context, _platform(), json.dumps(body))
    assert result.status == "assembly_failed" and result.pc is None


def test_missing_or_ambiguous_binding_is_not_inferred():
    context, body = _input()
    body["fact_bindings"]["data_width_bits"] = [{"collection": "top.ports", "name": "missing", "path": ["width"]}]
    assert assemble_pc(context, _platform(), json.dumps(body)).status == "assembly_failed"
    body["fact_bindings"].pop("data_width_bits")
    assert assemble_pc(context, _platform(), json.dumps(body)).status == "assembly_failed"


def test_semantically_wrong_binding_reaches_unchanged_h3():
    context, body = _input()
    body["fact_bindings"]["data_width_bits"] = [{"collection": "state.counters", "name": "count", "path": ["width"]}]
    result = assemble_pc(context, _platform(), json.dumps(body))
    assert result.status == "pc_validation_failed" and result.failure_stage == "h3"


def test_record_replays_and_summary_tampering_is_rejected(tmp_path):
    context, body = _input()
    store = ArtifactStore(tmp_path / "store")
    record, ref = record_pc_assembly(store, "attempt", context, _platform(), json.dumps(body))
    assert record["status"] == "pc_valid", record["diagnostics"]
    assert read_verified_pc_assembly(store, ref) == record
    forged = copy.deepcopy(record)
    forged["logical_model_calls"] = 1
    forged["record_id"] = "pc-assembly-" + _hash(_json_bytes({k: v for k, v in forged.items() if k != "record_id"}))
    forged_ref = store.put_validated_json("tampered", forged, contract_key="pc_assembly_record")
    with pytest.raises(ValueError, match="replay"):
        read_verified_pc_assembly(store, forged_ref)
    raw_ref = record["raw_response_ref"]
    (store.root / "blobs" / raw_ref["sha256"][:2] / raw_ref["sha256"]).write_bytes(b"tampered")
    with pytest.raises(ArtifactIntegrityError):
        read_verified_pc_assembly(store, ref)


def test_generator_is_one_call_and_repeated_attempt_cannot_dispatch(tmp_path):
    context, body = _input()
    class Client:
        calls = 0
        def stream_chat(self, messages):
            self.calls += 1
            return json.dumps(body)
    client = Client()
    generator = PCDecisionGenerator(client, _platform(), ArtifactStore(tmp_path / "store"))
    record, _ = generator.generate(context, "attempt")
    assert record["status"] == "pc_valid"
    assert client.calls == record["logical_model_calls"] == 1
    with pytest.raises(FileExistsError):
        generator.generate(context, "attempt")
    assert client.calls == 1


def test_provider_failure_is_not_parsed_as_a_success(tmp_path):
    context, _ = _input()
    class Client:
        def stream_chat(self, messages):
            raise RuntimeError("private credential must not enter artifacts")
    store = ArtifactStore(tmp_path / "store")
    record, ref = PCDecisionGenerator(Client(), _platform(), store).generate(context, "attempt")
    assert record["status"] == "provider_failed" and record["pc_ref"] is None
    assert "private credential" not in json.dumps(record)
    assert read_verified_pc_assembly(store, ref) == record


def test_corrupt_frozen_context_is_rejected_before_prompt_or_assembly():
    context, body = _input()
    context = replace(context, public_projection_sha256="0" * 64)
    with pytest.raises(ValueError, match="digest"):
        decision_messages(context, _platform())
    with pytest.raises(ValueError, match="digest"):
        assemble_pc(context, _platform(), json.dumps(body))


@pytest.mark.parametrize("owner", ["top", "u_counter"])
def test_derived_ownership_never_reassigns_the_model_owner(owner):
    context, body = _input()
    d = body["decisions"]
    core = copy.deepcopy(d["components"][0])
    core.update(name="counter_core", source="rtl/counter_core.v", semantic_kind="counter", combinational=False)
    d["components"].append(core)
    d["instances"] = [{"name": "u_counter", "component": "counter_core", "clock": "clk", "reset": "rst_n", "parameter_values": {}}]
    d["state"]["counters"][0]["owner"] = owner
    result = assemble_pc(context, _platform(), json.dumps(body))
    assert result.pc is not None, result.diagnostics
    assert result.pc["state"]["counters"][0]["owner"] == owner
    assert result.pc["instances"][0]["owns_state"] == ([] if owner == "top" else ["u_counter.count"])
    assert result.field_sources["/instances/0/owns_state"] == "derived"


def test_duplicate_names_and_reserved_sources_are_rejected():
    context, body = _input()
    body["decisions"]["top"]["ports"].append(copy.deepcopy(body["decisions"]["top"]["ports"][0]))
    result = assemble_pc(context, _platform(), json.dumps(body))
    assert result.failure_stage == "uniqueness"
    context, body = _input()
    body["decisions"]["components"][0]["source"] = "manifest.json"
    assert assemble_pc(context, _platform(), json.dumps(body)).failure_stage == "path"


def test_model_cannot_supply_derived_ownership_or_host_bindings():
    context, body = _input()
    body["decisions"]["instances"] = [{"name": "u", "component": "top", "clock": "clk", "reset": "rst_n", "parameter_values": {}, "owns_state": []}]
    assert assemble_pc(context, _platform(), json.dumps(body)).status == "decision_schema_failed"
    context, body = _input()
    body["fact_bindings"]["acceptance_criteria"] = [{"collection": "verification", "path": ["pass_condition"]}]
    assert assemble_pc(context, _platform(), json.dumps(body)).failure_stage == "binding_keys"


def test_missing_assessment_is_not_a_semantic_failure(monkeypatch):
    context, body = _input()
    import sr2fpga_agent.pc_assembly as module
    report = {key: {"status": "pass", "diagnostics": []} for key in ("h0", "h1", "h2", "h3")}
    report["h3"]["status"] = "not_applicable"
    report["passed"] = False
    monkeypatch.setattr(module, "validate_frozen_system_his_payload_h_stages", lambda *a, **k: report)
    result = assemble_pc(context, _platform(), json.dumps(body))
    assert result.status == "pc_unverified" and result.failure_stage == "h3"


@pytest.mark.parametrize("valid", [True, False])
def test_offline_cli_and_independent_record_replay(tmp_path, valid):
    from dataclasses import asdict
    from sr2fpga_agent.frozen_context import build_development_episode_pack
    from sr2fpga_agent.pc_assembly import main
    context, body = _input()
    pack = build_development_episode_pack(context, episode_id="offline", method_condition="M3", analysis_population="excluded", evaluator_metadata={"canary": "PRIVATE_NOT_FOR_MODEL"}, private_ref_ids=("PRIVATE_NOT_FOR_MODEL",))
    pack_path, platform_path, response_path = (tmp_path / name for name in ("pack.json", "platform.json", "response.json"))
    pack_path.write_text(json.dumps(pack.to_dict()), encoding="utf-8")
    platform_path.write_text(json.dumps(asdict(_platform())), encoding="utf-8")
    response_path.write_text(json.dumps(body) if valid else "not-json", encoding="utf-8")
    root = tmp_path / "offline"
    assert "PRIVATE_NOT_FOR_MODEL" not in json.dumps(decision_messages(context, _platform()))
    assert main(["--episode-pack", str(pack_path), "--platform", str(platform_path), "--response", str(response_path), "--output-root", str(root)]) == (0 if valid else 1)
    assert main(["--output-root", str(root), "--verify", "pc-interface/attempt-000/record"]) == 0
    with pytest.raises(SystemExit):
        main(["--episode-pack", str(pack_path), "--platform", str(platform_path), "--response", str(response_path), "--output-root", str(root)])


def test_source_drift_during_call_retains_raw_but_cannot_commit_a_result(tmp_path, monkeypatch):
    import sr2fpga_agent.pc_assembly as module
    context, body = _input()
    class Client:
        def stream_chat(self, messages):
            monkeypatch.setattr(module, "_runtime_stamp", lambda: "changed")
            return json.dumps(body)
    store = ArtifactStore(tmp_path / "store")
    with pytest.raises(ValueError, match="changed during model invocation"):
        PCDecisionGenerator(Client(), _platform(), store).generate(context, "attempt")
    assert store.reference("pc-interface/attempt/raw") is not None
    assert store.reference("pc-interface/attempt/context") is not None
    assert store.reference("pc-interface/attempt/record") is None


def test_interface_version_drift_is_a_pre_call_integrity_error(monkeypatch):
    import sr2fpga_agent.pc_assembly as module
    registry = module.ContractRegistry()
    class ChangedRegistry:
        def load_schema(self, key):
            schema = registry.load_schema(key)
            return replace(schema, version="pc-decisions-v2") if key == "pc_decisions" else schema
    monkeypatch.setattr(module, "ContractRegistry", ChangedRegistry)
    context, _ = _input()
    with pytest.raises(ValueError, match="requires pc_decisions"):
        decision_messages(context, _platform())
