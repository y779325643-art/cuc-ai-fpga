import json
import inspect

import pytest

import sr2fpga_agent.generation.context_his as context_his_module
from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.episode_executor import EpisodeExecutor, PreCandidateState
from sr2fpga_agent.frozen_context import freeze_ready_requirement_context
from sr2fpga_agent.frozen_context import frozen_project_name
from sr2fpga_agent.generation.context_his import (
    FrozenContextSystemHisCorrectionFacade,
    FrozenContextSystemHisFacade,
    FrozenContextSystemHisValidationFacade,
)
from sr2fpga_agent.method_adapters import (
    GenerationServices,
    MethodAdapterRegistry,
    MethodArtifactGateway,
    PairedArtifactCoordinator,
    PairingKey,
    SharedArtifactRefs,
)
from sr2fpga_agent.model_budget import ModelCallBudget
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.parsers import parse_system_his_v12
from sr2fpga_agent.project_contract import (
    build_composite_project_envelope,
    project_package_sha256,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary
from sr2fpga_agent.system_his_fidelity import build_frozen_requirement_trace


def _platform() -> PlatformProfile:
    return PlatformProfile("generic_verilog", "generic", "open_source")


def _context_and_his():
    platform = _platform()
    request = ProjectRequest(
        "counter",
        8,
        "evaluator-private-name",
        "Build an 8-bit synchronous counter with active-low reset.",
    )
    context = freeze_ready_requirement_context(
        evaluate_requirement_boundary(request, platform), platform
    )
    project = ProjectGenerator().generate(
        ProjectRequest(
            "counter",
            8,
            frozen_project_name(context),
            request.description,
        ),
        platform,
    )
    payload = parse_system_his_v12(project.files["system_his.json"])
    payload["intent"]["requirement_trace"] = build_frozen_requirement_trace(
        context, payload
    )
    return context, payload


class _Client:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = []

    def stream_chat(self, messages):
        self.calls.append(messages)
        return self.response

    def chat(self, messages):
        self.calls.append(messages)
        return self.response


class _FailingClient(_Client):
    def stream_chat(self, messages):
        self.calls.append(messages)
        raise RuntimeError("provider unavailable")


def _behavior_response() -> str:
    return json.dumps({"behavior_files": {}})


def _free_project_response(project_name: str) -> str:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": project_name,
        "top": {
            "module": "top",
            "source": "rtl/top.v",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "rst_n", "direction": "input", "width": 1},
                    {"name": "en", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {"path": "rtl/top.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [
            {
                "path": "constraints/timing.sdc",
                "role": "constraint",
                "applicability": "advisory",
            },
            {
                "path": "sim/tb_top.v",
                "role": "candidate_testbench",
                "applicability": "advisory",
            },
            {
                "path": "reports/predicted_qor.json",
                "role": "predicted_qor",
                "applicability": "advisory",
            },
        ],
        "build": {
            "toolchain_id": "open_source",
            "language_standard": "verilog-2005",
        },
    }
    rtl = """module top(
  input wire clk,
  input wire rst_n,
  input wire en,
  output reg [7:0] count
);
always @(posedge clk) begin
  if (!rst_n) count <= 8'd0;
  else if (en) count <= count + 8'd1;
end
endmodule
"""
    return json.dumps(
        {
            "project_name": project_name,
            "files": {
                "manifest.json": json.dumps(manifest),
                "rtl/top.v": rtl,
                "constraints/timing.sdc": "create_clock -period 10 [get_ports clk]\n",
                "sim/tb_top.v": "module tb_top; top dut(); endmodule\n",
                "reports/predicted_qor.json": "{}\n",
            },
        }
    )


def _repairable_project(context, payload) -> GeneratedProject:
    project_name = frozen_project_name(context)
    response = json.loads(_free_project_response(project_name))
    files = dict(response["files"])
    manifest = json.loads(files["manifest.json"])
    manifest["artifacts"].append(
        {
            "path": "system_his.json",
            "role": "system_his",
            "applicability": "required",
        }
    )
    files["manifest.json"] = json.dumps(manifest, sort_keys=True) + "\n"
    files["system_his.json"] = json.dumps(payload, sort_keys=True) + "\n"
    files["sim/tb_top.v"] = "// TRUSTED-TB-CANARY\nmodule tb_top; endmodule\n"
    files["constraints/timing.sdc"] = "# TRUSTED-CONSTRAINT-CANARY\n"
    files["rtl/top.v"] = files["rtl/top.v"].replace(
        "always @(posedge clk) begin\n",
        "// SR2FPGA_BEHAVIOR_BEGIN\nalways @(posedge clk) begin\n",
    ).replace(
        "end\nendmodule\n",
        "end\n// SR2FPGA_BEHAVIOR_END\nendmodule\n",
    )
    return GeneratedProject(project_name, files)


def _trusted_repair_envelope(tmp_path, project: GeneratedProject):
    store = ArtifactStore(tmp_path / "repair-store")
    trusted_ref = store.append_event("episode-m5", "skeleton_built", {})
    model_ref = store.append_event("episode-m5", "behavior_generated", {})
    trusted_event_id = json.loads(store.read_verified(trusted_ref))["event_id"]
    model_event_id = json.loads(store.read_verified(model_ref))["event_id"]
    envelope = build_composite_project_envelope(
        project,
        episode_id="episode-m5",
        method_condition_id="M5",
        snapshot_id="snapshot-000",
        trusted_builder_event_id=trusted_event_id,
        model_generation_event_id=model_event_id,
        event_ref_resolver=store.has_event_id,
    )
    return store, envelope


def test_frozen_his_validator_runs_all_h_stages_without_request_routing() -> None:
    context, payload = _context_and_his()

    report = FrozenContextSystemHisValidationFacade(_platform()).validate_his(
        context, payload
    )

    assert report["passed"] is True
    assert [report[name]["status"] for name in ("h0", "h1", "h2", "h3")] == [
        "pass",
        "pass",
        "pass",
        "pass",
    ]


def test_frozen_his_validator_rejects_platform_not_bound_to_context() -> None:
    context, payload = _context_and_his()
    different = PlatformProfile("other", "generic", "open_source")

    with pytest.raises(ValueError, match="does not match frozen"):
        FrozenContextSystemHisValidationFacade(different).validate_his(
            context, payload
        )


def test_frozen_his_h3_is_value_aware() -> None:
    context, payload = _context_and_his()
    payload["top"]["ports"][3]["width"] = 999

    report = FrozenContextSystemHisValidationFacade(_platform()).validate_his(
        context, payload
    )

    assert report["passed"] is False
    assert report["h3"]["status"] == "fail"
    assert any("data_width_bits" in item for item in report["h3"]["diagnostics"])


def test_frozen_his_rejects_nonfrozen_project_identity() -> None:
    context, payload = _context_and_his()
    payload["project_name"] = "evaluator-private-name"

    report = FrozenContextSystemHisValidationFacade(_platform()).validate_his(
        context, payload
    )

    assert report["passed"] is False
    assert report["h1"]["status"] == "fail"
    assert any("frozen identity" in item for item in report["h1"]["diagnostics"])


def test_frozen_req2his_prompt_excludes_evaluator_family_metadata() -> None:
    context, payload = _context_and_his()
    req_client = _Client(json.dumps(payload))
    facade = FrozenContextSystemHisFacade(
        req_client, _Client(_behavior_response()), _platform()
    )

    assert facade.emit_his(context)["schema_version"] == "system-his-v1.2"
    prompt = json.dumps(req_client.calls, ensure_ascii=False)
    assert context.public_projection_sha256 in prompt
    assert "evaluator-private-name" not in prompt
    assert '"task_type"' not in prompt
    assert '"family_id"' not in prompt


def test_m4_context_native_req2his_validation_and_skeleton_lowering(tmp_path) -> None:
    context, payload = _context_and_his()
    raw_req = _Client(json.dumps(payload))
    raw_project = _Client(_behavior_response())
    budget = ModelCallBudget(max_calls=2)
    facade = FrozenContextSystemHisFacade(
        budget.client(raw_req, "req2his"),
        budget.client(raw_project, "his2project"),
        _platform(),
    )
    services = GenerationServices(
        artifacts=MethodArtifactGateway(ArtifactStore(tmp_path / "store")),
        episode_id="episode-001",
        system_his=facade,
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
    )

    outcome = EpisodeExecutor().emit_candidate(
        MethodAdapterRegistry().create("M4"), context, services
    )

    assert outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert outcome.candidate is not None
    assert budget.calls_used == 2
    assert [record["stage"] for record in budget.call_records] == [
        "req2his",
        "his2project",
    ]
    project = services.artifacts.read_project(outcome.candidate)
    assert json.loads(project.files["manifest.json"])["contract_version"] == "project-package-v1"
    assert project_package_sha256(project) == outcome.candidate.project_package_sha256


def test_m3_free_from_his_does_not_call_skeleton_or_behavior_filler(
    tmp_path, monkeypatch
) -> None:
    context, payload = _context_and_his()
    project_name = f"frozen_{context.requirement_id.replace('req-', '')[:24]}"
    raw_req = _Client(json.dumps(payload))
    raw_project = _Client(_free_project_response(project_name))
    budget = ModelCallBudget(max_calls=2)

    def forbidden(*args, **kwargs):
        raise AssertionError("M3 invoked deterministic skeleton machinery")

    monkeypatch.setattr(
        context_his_module, "build_contract_skeleton_project", forbidden
    )
    monkeypatch.setattr(context_his_module, "merge_behavior_files", forbidden)
    assert "ProjectGenerator" not in inspect.getsource(context_his_module)
    facade = FrozenContextSystemHisFacade(
        budget.client(raw_req, "req2his"),
        budget.client(raw_project, "his2project_free"),
        _platform(),
    )
    services = GenerationServices(
        artifacts=MethodArtifactGateway(ArtifactStore(tmp_path / "store")),
        episode_id="episode-m3",
        system_his=facade,
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
    )

    outcome = EpisodeExecutor().emit_candidate(
        MethodAdapterRegistry().create("M3"), context, services
    )

    assert outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert budget.calls_used == 2
    project = services.artifacts.read_project(outcome.candidate)
    assert json.loads(project.files["system_his.json"]) == payload
    assert "BEHAVIOR_HOLE" not in project.files["rtl/top.v"]


def test_m3_m4_consume_same_materialized_frozen_his(tmp_path) -> None:
    context, payload = _context_and_his()
    project_name = f"frozen_{context.requirement_id.replace('req-', '')[:24]}"
    raw_req = _Client(json.dumps(payload))
    store = ArtifactStore(tmp_path / "store")
    coordinator = PairedArtifactCoordinator(store)
    req_facade = FrozenContextSystemHisFacade(
        raw_req, _Client(_behavior_response()), _platform()
    )
    pairing = PairingKey(
        paired_block_id="pair-m3-m4",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="counter-instance",
        decoding_seed=7,
        model_provenance_sha256="a" * 64,
    )
    shared_his = coordinator.materialize_system_his(
        pairing, lambda: req_facade.emit_his(context)
    )
    shared = SharedArtifactRefs(system_his=shared_his)
    validation = FrozenContextSystemHisValidationFacade(_platform())
    gateway = MethodArtifactGateway(store)

    m3_services = GenerationServices(
        artifacts=gateway,
        episode_id="episode-m3",
        system_his=FrozenContextSystemHisFacade(
            _Client("unused"), _Client(_free_project_response(project_name)), _platform()
        ),
        his_validation=validation,
    )
    m4_services = GenerationServices(
        artifacts=gateway,
        episode_id="episode-m4",
        system_his=FrozenContextSystemHisFacade(
            _Client("unused"), _Client(_behavior_response()), _platform()
        ),
        his_validation=validation,
    )

    m3 = EpisodeExecutor().emit_candidate(
        MethodAdapterRegistry().create("M3"), context, m3_services, shared
    )
    m4 = EpisodeExecutor().emit_candidate(
        MethodAdapterRegistry().create("M4"), context, m4_services, shared
    )

    assert m3.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert m4.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert m3.planning_artifact.artifact_ref.sha256 == shared_his.artifact_ref.sha256
    assert m4.planning_artifact.artifact_ref.sha256 == shared_his.artifact_ref.sha256
    assert len(raw_req.calls) == 1


def test_m3_rejects_model_control_of_frozen_project_name() -> None:
    context, payload = _context_and_his()
    facade = FrozenContextSystemHisFacade(
        _Client("unused"), _Client(_free_project_response("model-private-name")), _platform()
    )

    with pytest.raises(ValueError, match="frozen project name"):
        facade.emit_free_project(context, payload)


def test_m3_rejects_behavior_hole_marker() -> None:
    context, payload = _context_and_his()
    project_name = f"frozen_{context.requirement_id.replace('req-', '')[:24]}"
    response = json.loads(_free_project_response(project_name))
    response["files"]["rtl/top.v"] += "// BEHAVIOR_HOLE\n"
    facade = FrozenContextSystemHisFacade(
        _Client("unused"), _Client(json.dumps(response)), _platform()
    )

    with pytest.raises(ValueError, match="must not contain BEHAVIOR_HOLE"):
        facade.emit_free_project(context, payload)


def test_h_failure_stops_before_his2project_call(tmp_path) -> None:
    context, payload = _context_and_his()
    payload["intent"]["requirement_trace"]["requirement_id"] = "wrong"
    raw_req = _Client(json.dumps(payload))
    raw_project = _Client(_behavior_response())
    budget = ModelCallBudget(max_calls=2)
    facade = FrozenContextSystemHisFacade(
        budget.client(raw_req, "req2his"),
        budget.client(raw_project, "his2project"),
        _platform(),
    )
    services = GenerationServices(
        artifacts=MethodArtifactGateway(ArtifactStore(tmp_path / "store")),
        episode_id="episode-001",
        system_his=facade,
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
    )

    outcome = EpisodeExecutor().emit_candidate(
        MethodAdapterRegistry().create("M4"), context, services
    )

    assert outcome.final_state is PreCandidateState.NO_COMPLETE_CANDIDATE
    assert outcome.failure is not None
    assert outcome.failure.stage == "h3"
    assert budget.calls_used == 1
    assert raw_project.calls == []


def test_m5_context_native_correction_reruns_all_h_before_lowering(tmp_path) -> None:
    context, valid_payload = _context_and_his()
    invalid_payload = json.loads(json.dumps(valid_payload))
    invalid_payload["intent"]["requirement_trace"]["requirement_id"] = "wrong"
    raw_req = _Client(json.dumps(invalid_payload))
    raw_repair = _Client(json.dumps(valid_payload))
    raw_project = _Client(_behavior_response())
    budget = ModelCallBudget(max_calls=3)
    services = GenerationServices(
        artifacts=MethodArtifactGateway(ArtifactStore(tmp_path / "store")),
        episode_id="episode-m5",
        system_his=FrozenContextSystemHisFacade(
            budget.client(raw_req, "req2his"),
            budget.client(raw_project, "his2project"),
            _platform(),
        ),
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        repair=FrozenContextSystemHisCorrectionFacade(
            budget.client(raw_repair, "system_his_repair"), _platform()
        ),
    )

    outcome = EpisodeExecutor(max_his_corrections=1).emit_candidate(
        MethodAdapterRegistry().create("M5"), context, services
    )

    assert outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert outcome.his_corrections_used == 1
    assert outcome.h_report["passed"] is True
    assert [record["stage"] for record in budget.call_records] == [
        "req2his",
        "system_his_repair",
        "his2project",
    ]
    repair_prompt = json.dumps(raw_repair.calls, ensure_ascii=False)
    assert '"failed_h_stage": "h3"' not in repair_prompt
    assert "failed_h_stage: h3" in repair_prompt
    assert '"h_report"' not in repair_prompt
    assert '"task_type"' not in repair_prompt
    assert '"family_id"' not in repair_prompt
    assert "evaluator-private-name" not in repair_prompt


def test_m4_never_calls_context_native_his_correction(tmp_path) -> None:
    context, payload = _context_and_his()
    payload["intent"]["requirement_trace"]["requirement_id"] = "wrong"
    raw_req = _Client(json.dumps(payload))
    raw_repair = _Client("unused")
    raw_project = _Client(_behavior_response())
    services = GenerationServices(
        artifacts=MethodArtifactGateway(ArtifactStore(tmp_path / "store")),
        episode_id="episode-m4",
        system_his=FrozenContextSystemHisFacade(raw_req, raw_project, _platform()),
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        repair=FrozenContextSystemHisCorrectionFacade(raw_repair, _platform()),
    )

    outcome = EpisodeExecutor(max_his_corrections=1).emit_candidate(
        MethodAdapterRegistry().create("M4"), context, services
    )

    assert outcome.final_state is PreCandidateState.NO_COMPLETE_CANDIDATE
    assert outcome.his_corrections_used == 0
    assert raw_repair.calls == []
    assert raw_project.calls == []


def test_failed_m5_correction_call_is_budgeted_and_stops_before_lowering(
    tmp_path,
) -> None:
    context, payload = _context_and_his()
    payload["intent"]["requirement_trace"]["requirement_id"] = "wrong"
    raw_req = _Client(json.dumps(payload))
    raw_repair = _FailingClient("")
    raw_project = _Client(_behavior_response())
    budget = ModelCallBudget(max_calls=2)
    services = GenerationServices(
        artifacts=MethodArtifactGateway(ArtifactStore(tmp_path / "store")),
        episode_id="episode-m5",
        system_his=FrozenContextSystemHisFacade(
            budget.client(raw_req, "req2his"), raw_project, _platform()
        ),
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        repair=FrozenContextSystemHisCorrectionFacade(
            budget.client(raw_repair, "system_his_repair"), _platform()
        ),
    )

    outcome = EpisodeExecutor(max_his_corrections=1).emit_candidate(
        MethodAdapterRegistry().create("M5"), context, services
    )

    assert outcome.final_state is PreCandidateState.NO_COMPLETE_CANDIDATE
    assert outcome.failure.stage == "his_correction"
    assert budget.calls_used == 2
    assert budget.failed_calls == 1
    assert budget.call_records[-1]["status"] == "failed"
    assert raw_project.calls == []


def test_m5_project_repair_edits_only_behavior_region_and_hides_trusted_content(tmp_path) -> None:
    context, payload = _context_and_his()
    project = _repairable_project(context, payload)
    repaired_rtl = project.files["rtl/top.v"].replace(
        "count + 8'd1", "count + 8'd2"
    )
    raw_project_repair = _Client(
        json.dumps({"rtl_files": {"rtl/top.v": repaired_rtl}})
    )
    budget = ModelCallBudget(max_calls=1)
    store, envelope = _trusted_repair_envelope(tmp_path, project)
    facade = FrozenContextSystemHisCorrectionFacade(
        _Client("unused"),
        _platform(),
        project_client=budget.client(raw_project_repair, "project_repair"),
        project_envelope=envelope,
        event_ref_resolver=store.has_event_id,
    )

    repaired = facade.repair_project(
        context,
        project,
        {"stage": "lint", "diagnostics": ["counter increment width mismatch"]},
    )

    assert repaired.files["rtl/top.v"] == repaired_rtl
    assert repaired.files["system_his.json"] == project.files["system_his.json"]
    assert repaired.files["manifest.json"] == project.files["manifest.json"]
    assert repaired.files["sim/tb_top.v"] == project.files["sim/tb_top.v"]
    assert budget.calls_used == 1
    prompt = json.dumps(raw_project_repair.calls, ensure_ascii=False)
    assert "TRUSTED-TB-CANARY" not in prompt
    assert "TRUSTED-CONSTRAINT-CANARY" not in prompt
    assert '"task_type"' not in prompt
    assert '"family_id"' not in prompt
    assert "evaluator-private-name" not in prompt


def test_m5_project_repair_rejects_edit_outside_behavior_region(tmp_path) -> None:
    context, payload = _context_and_his()
    project = _repairable_project(context, payload)
    invalid_rtl = project.files["rtl/top.v"].replace("module top", "module changed")
    store, envelope = _trusted_repair_envelope(tmp_path, project)
    facade = FrozenContextSystemHisCorrectionFacade(
        _Client("unused"),
        _platform(),
        project_client=_Client(
            json.dumps({"rtl_files": {"rtl/top.v": invalid_rtl}})
        ),
        project_envelope=envelope,
        event_ref_resolver=store.has_event_id,
    )

    with pytest.raises(ValueError, match="violated the model edit surface"):
        facade.repair_project(
            context,
            project,
            {"stage": "lint", "diagnostics": ["bad RTL"]},
        )


def test_m5_project_repair_rejects_trusted_path_target(tmp_path) -> None:
    context, payload = _context_and_his()
    project = _repairable_project(context, payload)
    store, envelope = _trusted_repair_envelope(tmp_path, project)
    facade = FrozenContextSystemHisCorrectionFacade(
        _Client("unused"),
        _platform(),
        project_client=_Client(
            json.dumps({"rtl_files": {"system_his.json": "{}"}})
        ),
        project_envelope=envelope,
        event_ref_resolver=store.has_event_id,
    )

    with pytest.raises(ValueError, match="non-editable path"):
        facade.repair_project(
            context,
            project,
            {"stage": "lint", "diagnostics": ["bad RTL"]},
        )


def test_m5_project_repair_requires_envelope_before_model_call() -> None:
    context, payload = _context_and_his()
    project = _repairable_project(context, payload)
    raw = _Client("unused")
    facade = FrozenContextSystemHisCorrectionFacade(
        _Client("unused"),
        _platform(),
        project_client=raw,
    )

    with pytest.raises(RuntimeError, match="trusted project envelope"):
        facade.repair_project(
            context,
            project,
            {"stage": "lint", "diagnostics": ["bad RTL"]},
        )
    assert raw.calls == []


def test_m5_project_repair_rejects_candidate_tampered_after_envelope(tmp_path) -> None:
    context, payload = _context_and_his()
    project = _repairable_project(context, payload)
    store, envelope = _trusted_repair_envelope(tmp_path, project)
    files = dict(project.files)
    files["rtl/top.v"] = files["rtl/top.v"].replace("count + 8'd1", "count + 8'd9")
    tampered = GeneratedProject(project.project_name, files)
    raw = _Client("unused")
    facade = FrozenContextSystemHisCorrectionFacade(
        _Client("unused"),
        _platform(),
        project_client=raw,
        project_envelope=envelope,
        event_ref_resolver=store.has_event_id,
    )

    with pytest.raises(ValueError, match="does not match the current candidate"):
        facade.repair_project(
            context,
            tampered,
            {"stage": "lint", "diagnostics": ["bad RTL"]},
        )
    assert raw.calls == []
