from dataclasses import replace
import copy
import hashlib
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.cost_accounting import AttemptCostLedger, COST_AXES, reconcile_cost_events
from sr2fpga_agent.his_correction_outcome import (
    _reconcile_cost, HisCorrectionOutcomeError, read_verified_development_his_correction_outcome,
)
from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.models import ProjectRequest
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.requirement_envelope import build_request_requirement_envelope
from sr2fpga_agent.system_his_fidelity import check_system_his_req_fidelity
from sr2fpga_agent.system_his_v12_checker import check_system_his_v12
from test_sr2fpga_agent_context_his import _platform
from test_sr2fpga_agent_requirement_h3 import _extended_requirement_fixture
from test_sr2fpga_agent_pre_candidate_stop_outcome import (
    test_real_runner_m5_h_correction_acceptance_is_artifact_derived_and_fail_closed as _m5_fixture,
    test_real_runner_m5_h_correction_uses_distinct_budget_stage as _post_correction_fixture,
)


@pytest.mark.parametrize("qualified", [False, True])
@pytest.mark.parametrize("wrong_owner", [False, True])
def test_h1_checks_owner_for_bare_and_qualified_references(qualified, wrong_owner):
    project = ProjectGenerator().generate(ProjectRequest("fir_filter", 8, "ownership"), _platform())
    payload = json.loads(project.files["system_his.json"])
    assert check_system_his_v12(payload).passed
    component = copy.deepcopy(payload["components"][0])
    component.update(name="owned_unit", source="rtl/owned_unit.v", combinational=False)
    payload["components"].append(component)
    payload["artifacts"]["rtl_sources"].append("rtl/owned_unit.v")
    instance = {"name": "u_unit", "component": "owned_unit", "parameter_values": {},
                "clock": "clk", "reset": "rst_n", "owns_state": []}
    payload["instances"].append(instance)
    state = {"name": "owned_state", "owner": "u_unit", "width": 1}
    payload["state"]["registers"].append(state)
    instance["owns_state"] = [f"{instance['name']}.{state['name']}" if qualified else state["name"]]
    if wrong_owner:
        state["owner"] = "top"
    result = check_system_his_v12(payload)
    assert result.passed is (not wrong_owner)
    if wrong_owner:
        assert any("state" in error and "own" in error for error in result.errors)


@pytest.mark.parametrize("unit", ["mW", "MW"])
def test_custom_acceptance_preserves_case_sensitive_units_in_full_h3(unit):
    request, platform, payload = _extended_requirement_fixture()
    request = replace(request, description=request.description.split("Acceptance:")[0]
                      + "Acceptance: peak power must not exceed 5 mW")
    trace = build_request_requirement_envelope(request, platform).requirement_trace_template()
    trace["fact_to_his"] = payload["intent"]["requirement_trace"]["fact_to_his"]
    trace["unresolved_facts"] = []
    payload["intent"]["requirement_trace"] = trace
    payload["verification"]["pass_condition"] = "peak power must not exceed 5 " + unit
    result = check_system_his_req_fidelity(request, payload, platform)
    assert result.passed is (unit == "mW")


def _raw_costs(tmp_path, stages, outer):
    store = ArtifactStore(tmp_path / "cost-store")
    ledger = AttemptCostLedger(store, episode_id="e", attempt_id="attempt-000",
                               method_condition="M5", failure_origin="synthetic_injected")
    for index, stage in enumerate(stages):
        ledger.reserve("logical_model_calls", 1, stage=stage, visibility_class="accounting",
                       limit=len(stages), used_after=index + 1)
    ledger.record_cost(stage="repair", visibility_class="accounting", status="completed",
                       cost_delta={"outer_repair_attempts": outer})
    ledger.close(zero_axes=set(COST_AXES) - ledger.observed_axes)
    summary = reconcile_cost_events(store, ledger.event_refs, summary_key="cost")
    return _reconcile_cost(store, (summary.artifact_ref,),
                           [{"attempt_event_refs": [ref.to_dict() for ref in ledger.event_refs]}],
                           ContractRegistry())


@pytest.mark.parametrize(("stages", "outer"), [
    (["system_his_repair", "his2project"], 0),
    (["req2his", "system_his_repair", "his2project"], 0),
    (["system_his_repair", "his2project", "project_repair"], 1),
])
def test_correction_costs_rebuild_shared_and_repair_calls(tmp_path, stages, outer):
    cost = _raw_costs(tmp_path, stages, outer)
    assert cost["logical_model_calls"] == len(stages)
    assert cost["project_repairs"] == outer


@pytest.mark.parametrize(("stages", "outer"), [
    (["system_his_repair", "system_his_repair", "his2project"], 0),
    (["system_his_repair", "his2project", "project_repair"], 0),
    (["system_his_repair", "his2project", "unknown"], 0),
])
def test_correction_costs_reject_extra_pc_repair_and_misattribution(tmp_path, stages, outer):
    with pytest.raises(HisCorrectionOutcomeError):
        _raw_costs(tmp_path, stages, outer)


def test_paired_m3_m5_shared_pc_correction_closes_and_replays(tmp_path, monkeypatch):
    store, ref, outcome = _m5_fixture(tmp_path, monkeypatch, "h1", shared_initial=True)
    assert outcome["cost"]["logical_model_calls"] == 2
    forged = copy.deepcopy(outcome)
    forged["cost"]["logical_model_calls"] = 3
    unsigned = {key: value for key, value in forged.items() if key != "outcome_id"}
    encoded = (json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    forged["outcome_id"] = "his-correction-outcome-" + hashlib.sha256(encoded).hexdigest()
    forged_ref = store.put_validated_json("tampered/shared-cost", forged,
                                         contract_key="development_his_correction_outcome_v2")
    with pytest.raises(HisCorrectionOutcomeError, match="does not rebuild"):
        read_verified_development_his_correction_outcome(store, forged_ref)
    assert read_verified_development_his_correction_outcome(store, ref) == outcome


def test_pc_correction_followed_by_invalid_fpp_is_retained(tmp_path, monkeypatch):
    _post_correction_fixture(tmp_path, monkeypatch, invalid_project=True)


def test_missing_trajectory_is_not_silently_treated_as_a_normal_stop(tmp_path, monkeypatch):
    original = DataGenerationAgent.run_one

    def without_trajectory(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        result.pop("canonical_trajectory_ref", None)
        return result

    monkeypatch.setattr(DataGenerationAgent, "run_one", without_trajectory)
    with pytest.raises(RuntimeError, match="missing artifact-derived acceptance lineage"):
        _post_correction_fixture(tmp_path, monkeypatch, invalid_project=True)
