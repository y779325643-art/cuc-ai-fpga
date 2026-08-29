import json
import inspect

import pytest

from sr2fpga_agent import cli
from sr2fpga_agent.agent import DataGenerationAgent
import sr2fpga_agent.generation.context_his as context_his_module
from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.episode_executor import EpisodeExecutor, PreCandidateState
from sr2fpga_agent.frozen_context import (
    build_development_episode_pack,
    freeze_ready_requirement_context,
)
from sr2fpga_agent.frozen_context import frozen_project_name
from sr2fpga_agent.generation.context_his import (
    FrozenContextHisGeneratorBridge,
    FrozenContextSystemHisCorrectionFacade,
    FrozenContextSystemHisFacade,
    FrozenContextSystemHisValidationFacade,
)
from sr2fpga_agent.generation.two_stage import TwoStageProjectGenerator
from sr2fpga_agent.his_validation import SystemHisValidationError
from sr2fpga_agent.method_adapters import (
    GenerationServices,
    MethodAdapterRegistry,
    MethodArtifactGateway,
    PairedArtifactCoordinator,
    PairingKey,
    PlanningArtifactKind,
    SharedArtifactRefs,
)
from sr2fpga_agent.model_budget import ModelCallBudget
from sr2fpga_agent.models import (
    GeneratedProject,
    PlatformProfile,
    ProjectRequest,
    ToolResult,
)
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


class _SequenceClient(_Client):
    def __init__(self, responses: list[str]) -> None:
        super().__init__("")
        self.responses = responses

    def stream_chat(self, messages):
        self.calls.append(messages)
        return self.responses[len(self.calls) - 1]


class _FailingClient(_Client):
    def stream_chat(self, messages):
        self.calls.append(messages)
        raise RuntimeError("provider unavailable")


class _StageClient(_Client):
    def __init__(self, response: str, stage_clients: dict[str, _Client]) -> None:
        super().__init__(response)
        self.stage_clients = stage_clients

    def for_stage(self, stage: str):
        return self.stage_clients.get(stage, self)


class _PassingCommandRunner:
    def run(self, command, cwd, stage, timeout_seconds=30):
        return ToolResult(stage, command, "passed", 0, "", "", 0.0)


def _behavior_response() -> str:
    return json.dumps({"behavior_files": {}})


def _two_stage_stub(req2his_client, project_client) -> TwoStageProjectGenerator:
    generator = TwoStageProjectGenerator(_Client("unused"))
    generator.system_his_generator.client = req2his_client
    generator.his_project_generator.client = project_client
    return generator


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
    user_prompt = req_client.calls[0][-1]["content"]
    assert context.public_projection_sha256 in prompt
    assert "evaluator-private-name" not in prompt
    assert '"task_type"' not in prompt
    assert '"family_id"' not in prompt
    assert "Map width facts only to top/component/instance widths" in prompt
    assert "H1 cross-field well-formedness rules (W1-W10)" in prompt
    for rule_id in range(1, 11):
        assert f"- W{rule_id}:" in prompt
    assert "Every instances[].component must match exactly one" in prompt
    assert "data_flow.path endpoint must be literal top.<port>" in prompt
    assert "Use the literal owner top, not top.name" in prompt
    assert "direction must be source to sink" in prompt
    assert "every state owner must be an exact instances[].name" in prompt
    assert "Every clock and reset declared in top.clocks/top.resets must also appear in top.ports" in prompt
    assert "Every instance must include owns_state as a JSON array" in prompt
    assert "Every owns_state entry must resolve to a declared state" in prompt
    assert (
        "Every top.parameters and components[].parameters entry must be an object "
        "with a non-empty name" in user_prompt
    )
    assert '{"name": "DATA_WIDTH", "default": 8}' in user_prompt
    assert (
        'A string such as "DATA_WIDTH" does not declare a parameter'
        in user_prompt
    )
    assert "components[].combinational to true only when" in prompt
    assert "A data flow with cdc=true must cross two declared clock domains" in prompt
    assert "Every declared memory must provide valid positive depth and width" in prompt
    assert "verification.scenarios references must resolve" in prompt
    assert "timing.primary_clock must name a declared top clock" in prompt
    assert "control_flow entry must include related_state and related_flows" in prompt
    assert "control_flow.kind must be one of" in prompt
    assert "artifacts.manifest must be exactly manifest.json" in prompt
    assert "every component source must appear in artifacts.rtl_sources" in prompt
    assert (
        "verification.testbench and artifacts.testbench to be exactly sim/tb_top.v"
        in prompt
    )


def test_frozen_his_skeleton_preflight_rejects_static_contract_before_project_call() -> None:
    context, payload = _context_and_his()
    payload["top"]["ports"] = [
        port
        for port in payload["top"]["ports"]
        if port["name"] not in {"clk", "rst_n"}
    ]
    project_client = _Client(_behavior_response())
    facade = FrozenContextSystemHisFacade(
        _Client(json.dumps(payload)),
        project_client,
        _platform(),
    )

    with pytest.raises(ValueError, match="static deterministic skeleton is inconsistent"):
        facade.emit_skeleton_project_output(context, payload)

    assert project_client.calls == []


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


def test_cli_m4_binds_frozen_context_executor_before_project_call(
    tmp_path, monkeypatch
) -> None:
    context, payload = _context_and_his()
    raw_req = _Client(json.dumps(payload))
    raw_project = _Client(_behavior_response())
    captured = {}

    monkeypatch.setattr(
        cli,
        "build_project_generator",
        lambda **_kwargs: _two_stage_stub(raw_req, raw_project),
    )

    def fake_run_one(self, **kwargs):
        generator = self.project_generator
        captured["generator"] = generator
        captured["project"] = generator.generate(
            kwargs["request"], kwargs["platform"]
        )
        captured["metadata"] = kwargs["metadata"]
        return {"sample_dir": "unused", "pass_level": "H3"}

    monkeypatch.setattr(DataGenerationAgent, "run_one", fake_run_one)

    cli.main(
        [
            "--dataset-root",
            str(tmp_path / "dataset"),
            "--sample-id",
            "cli-m4-valid",
            "--task-type",
            "counter",
            "--project-name",
            "evaluator-private-name",
            "--requirement",
            "Build an 8-bit synchronous counter with active-low reset.",
            "--provider",
            "openai_compat",
            "--api-key-env",
            "UNUSED_API_KEY",
        ]
    )

    generator = captured["generator"]
    assert isinstance(generator, FrozenContextHisGeneratorBridge)
    assert [state.value for state in generator.last_outcome.state_trace] == [
        "method_prepared",
        "planning_artifact_emitted",
        "h_validated",
        "candidate_emitted",
    ]
    assert generator.last_outcome.h_report["h3"]["status"] == "pass"
    assert len(raw_req.calls) == 1
    assert len(raw_project.calls) == 1
    prompt = json.dumps(raw_req.calls, ensure_ascii=False)
    assert context.public_projection_sha256 in prompt
    assert '"task_type"' not in prompt
    assert '"family_id"' not in prompt
    assert "evaluator-private-name" not in prompt
    assert "BEHAVIOR_HOLE" not in captured["project"].files["rtl/top.v"]


def test_cli_m4_h3_failure_stops_before_project_call(tmp_path, monkeypatch) -> None:
    _context, payload = _context_and_his()
    payload["intent"]["requirement_trace"]["requirement_id"] = "wrong"
    raw_req = _Client(json.dumps(payload))
    raw_project = _Client(_behavior_response())

    monkeypatch.setattr(
        cli,
        "build_project_generator",
        lambda **_kwargs: _two_stage_stub(raw_req, raw_project),
    )

    def fake_run_one(self, **kwargs):
        return self.project_generator.generate(kwargs["request"], kwargs["platform"])

    monkeypatch.setattr(DataGenerationAgent, "run_one", fake_run_one)

    with pytest.raises(SystemHisValidationError):
        cli.main(
            [
                "--dataset-root",
                str(tmp_path / "dataset"),
                "--sample-id",
                "cli-m4-invalid",
                "--task-type",
                "counter",
                "--project-name",
                "evaluator-private-name",
                "--requirement",
                "Build an 8-bit synchronous counter with active-low reset.",
                "--provider",
                "openai_compat",
                "--api-key-env",
                "UNUSED_API_KEY",
            ]
        )

    assert len(raw_req.calls) == 1
    assert raw_project.calls == []


def test_cli_m5_corrects_h_failure_before_project_call(tmp_path, monkeypatch) -> None:
    _context, valid_payload = _context_and_his()
    invalid_payload = json.loads(json.dumps(valid_payload))
    invalid_payload["intent"]["requirement_trace"]["requirement_id"] = "wrong"
    raw_repair = _Client(json.dumps(valid_payload))
    raw_req = _StageClient(
        json.dumps(invalid_payload),
        {"system_his_repair": raw_repair},
    )
    raw_project = _Client(_behavior_response())
    captured = {}

    monkeypatch.setattr(
        cli,
        "build_project_generator",
        lambda **_kwargs: _two_stage_stub(raw_req, raw_project),
    )
    monkeypatch.setattr(cli, "build_repairer", lambda **_kwargs: None)

    def fake_run_one(self, **kwargs):
        generator = self.project_generator
        captured["generator"] = generator
        captured["project"] = generator.generate(
            kwargs["request"], kwargs["platform"]
        )
        return {"sample_dir": "unused", "pass_level": "H3"}

    monkeypatch.setattr(DataGenerationAgent, "run_one", fake_run_one)

    cli.main(
        [
            "--dataset-root",
            str(tmp_path / "dataset"),
            "--sample-id",
            "cli-m5-corrected",
            "--task-type",
            "counter",
            "--project-name",
            "evaluator-private-name",
            "--requirement",
            "Build an 8-bit synchronous counter with active-low reset.",
            "--provider",
            "openai_compat",
            "--api-key-env",
            "UNUSED_API_KEY",
            "--repair-provider",
            "deepseek",
            "--max-attempts",
            "2",
            "--max-model-calls",
            "3",
        ]
    )

    generator = captured["generator"]
    assert isinstance(generator, FrozenContextHisGeneratorBridge)
    assert generator.last_outcome.his_corrections_used == 1
    assert generator.last_outcome.h_report["passed"] is True
    assert len(raw_req.calls) == 1
    assert len(raw_repair.calls) == 1
    assert len(raw_project.calls) == 1
    repair_prompt = json.dumps(raw_repair.calls, ensure_ascii=False)
    assert "failed_h_stage: h3" in repair_prompt
    assert '"task_type"' not in repair_prompt
    assert '"family_id"' not in repair_prompt
    assert "evaluator-private-name" not in repair_prompt
    assert "BEHAVIOR_HOLE" not in captured["project"].files["rtl/top.v"]


def test_frozen_m4_bridge_and_agent_share_h3_authority(tmp_path) -> None:
    context, payload = _context_and_his()
    request = ProjectRequest(
        "counter",
        8,
        "evaluator-private-name",
        "Build an 8-bit synchronous counter with active-low reset.",
    )
    platform = _platform()
    boundary = evaluate_requirement_boundary(request, platform)
    system_his = FrozenContextSystemHisFacade(
        _Client(json.dumps(payload)),
        _Client(_behavior_response()),
        platform,
    )
    services = GenerationServices(
        artifacts=MethodArtifactGateway(ArtifactStore(tmp_path / "method-store")),
        episode_id="agent-m4-valid",
        system_his=system_his,
        his_validation=FrozenContextSystemHisValidationFacade(platform),
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition="M4",
        context=context,
        services=services,
        system_his=system_his,
    )
    metadata = {
        "analysis_population": "development",
        "method_condition": "M4",
        "requirement_boundary": boundary.to_dict(),
        "episode_pack": build_development_episode_pack(
            context,
            episode_id="agent-m4-valid",
            analysis_population="development",
            method_condition="M4",
            evaluator_metadata={"task_type": "counter"},
        ).to_dict(),
    }

    result = DataGenerationAgent(
        tmp_path / "dataset",
        command_runner=_PassingCommandRunner(),
        project_generator=bridge,
    ).run_one(
        sample_id="agent-m4-valid",
        requirement=request.description,
        request=request,
        platform=platform,
        metadata=metadata,
    )

    labels = json.loads(
        (tmp_path / "dataset" / "agent-m4-valid" / "eval" / "labels.json").read_text(
            encoding="utf-8"
        )
    )
    assert result.get("failure_type") is None
    assert bridge.last_outcome.h_report["h3"]["status"] == "pass"
    assert labels["h3_status"] == "pass"


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


def test_m4_m5_bridges_consume_prepared_project_and_keep_method_events_distinct(
    tmp_path,
) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    pairing = PairingKey(
        paired_block_id="pair-prepared-bridge",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="counter-instance",
        decoding_seed=7,
        model_provenance_sha256="a" * 64,
    )
    paired_prefix = f"paired/{pairing.digest()}"
    prepared_his = gateway.put_planning(
        "prepared/system-his", PlanningArtifactKind.SYSTEM_HIS, payload
    )
    prepared_project = gateway.put_project(
        f"{paired_prefix}/skeleton-initial-project",
        _repairable_project(context, payload),
    )
    prepared_trusted = gateway.put_project(
        f"{paired_prefix}/trusted-skeleton", _repairable_project(context, payload)
    )
    prepared = SharedArtifactRefs(
        initial_project=prepared_project,
        system_his=prepared_his,
    )
    behavior_client = _Client(_behavior_response())
    system_his = FrozenContextSystemHisFacade(
        _Client("must not be called"), behavior_client, _platform()
    )
    coordinator = PairedArtifactCoordinator(store)
    bridges = []

    for method in ("M4", "M5"):
        services = GenerationServices(
            artifacts=gateway,
            episode_id=f"prepared-{method.lower()}",
            system_his=system_his,
            his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        )
        bridge = FrozenContextHisGeneratorBridge(
            method_condition=method,
            context=context,
            services=services,
            system_his=system_his,
            coordinator=coordinator,
            pairing=pairing,
            prepared_shared_artifacts=prepared,
            prepared_trusted_skeleton=prepared_trusted,
        )
        bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())
        bridges.append(bridge)

    assert behavior_client.calls == []
    assert {
        bridge.last_outcome.candidate.artifact_ref for bridge in bridges
    } == {prepared_project.artifact_ref}
    assert {bridge.last_skeleton_artifact for bridge in bridges} == {prepared_trusted}
    candidate_methods = []
    for bridge in bridges:
        candidate_event = next(
            json.loads(store.read_verified(reference))
            for reference in bridge.last_method_event_refs
            if json.loads(store.read_verified(reference))["payload"].get("state")
            == "candidate_emitted"
        )
        candidate_methods.append(candidate_event["payload"]["method_condition_id"])
    assert candidate_methods == ["M4", "M5"]


def test_m3_prepared_his_runs_one_free_project_call_without_shared_project(
    tmp_path,
) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    prepared_his = gateway.put_planning(
        "prepared/m3-system-his", PlanningArtifactKind.SYSTEM_HIS, payload
    )
    req_client = _Client("must not be called")
    project_client = _Client(_free_project_response(frozen_project_name(context)))
    system_his = FrozenContextSystemHisFacade(
        req_client, project_client, _platform()
    )
    services = GenerationServices(
        artifacts=gateway,
        episode_id="prepared-m3",
        system_his=system_his,
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition="M3",
        context=context,
        services=services,
        system_his=system_his,
        prepared_shared_artifacts=SharedArtifactRefs(system_his=prepared_his),
    )

    bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())

    assert req_client.calls == []
    assert len(project_client.calls) == 1
    assert bridge.last_outcome.planning_artifact == prepared_his
    assert bridge.last_outcome.candidate is not None


@pytest.mark.parametrize("method", ["M4", "M5"])
def test_skeleton_bridge_accepts_prepared_his_only_and_generates_project(
    tmp_path, method
) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    prepared_his = gateway.put_planning(
        f"prepared/{method.lower()}-system-his",
        PlanningArtifactKind.SYSTEM_HIS,
        payload,
    )
    req_client = _Client("must not be called")
    behavior_client = _Client(_behavior_response())
    system_his = FrozenContextSystemHisFacade(
        req_client, behavior_client, _platform()
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition=method,
        context=context,
        services=GenerationServices(
            artifacts=gateway,
            episode_id=f"prepared-his-only-{method.lower()}",
            system_his=system_his,
            his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        ),
        system_his=system_his,
        prepared_shared_artifacts=SharedArtifactRefs(system_his=prepared_his),
    )

    bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())

    assert req_client.calls == []
    assert len(behavior_client.calls) == 1
    assert bridge.last_outcome.candidate is not None
    assert bridge.last_skeleton_artifact is not None


def test_m3_rejects_full_prepared_set_before_any_model_call(tmp_path) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    pairing = PairingKey(
        paired_block_id="pair-invalid-m3",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="counter-instance",
        decoding_seed=7,
        model_provenance_sha256="a" * 64,
    )
    prefix = f"paired/{pairing.digest()}"
    prepared_his = gateway.put_planning(
        f"{prefix}/system-his", PlanningArtifactKind.SYSTEM_HIS, payload
    )
    prepared_project = gateway.put_project(
        f"{prefix}/skeleton-initial-project", _repairable_project(context, payload)
    )
    prepared_trusted = gateway.put_project(
        f"{prefix}/trusted-skeleton", _repairable_project(context, payload)
    )
    req_client = _Client("must not be called")
    project_client = _Client("must not be called")
    system_his = FrozenContextSystemHisFacade(
        req_client, project_client, _platform()
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition="M3",
        context=context,
        services=GenerationServices(
            artifacts=gateway,
            episode_id="invalid-m3",
            system_his=system_his,
            his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        ),
        system_his=system_his,
        coordinator=PairedArtifactCoordinator(store),
        pairing=pairing,
        prepared_shared_artifacts=SharedArtifactRefs(
            initial_project=prepared_project,
            system_his=prepared_his,
        ),
        prepared_trusted_skeleton=prepared_trusted,
    )

    with pytest.raises(ValueError, match="M3.*prepared project"):
        bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())

    assert req_client.calls == project_client.calls == []


def test_prepared_project_without_his_rejects_before_coordinator_call(tmp_path) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    pairing = PairingKey(
        paired_block_id="pair-project-without-his",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="counter-instance",
        decoding_seed=7,
        model_provenance_sha256="a" * 64,
    )
    prefix = f"paired/{pairing.digest()}"
    prepared_project = gateway.put_project(
        f"{prefix}/skeleton-initial-project", _repairable_project(context, payload)
    )
    prepared_trusted = gateway.put_project(
        f"{prefix}/trusted-skeleton", _repairable_project(context, payload)
    )
    req_client = _Client("must not be called")
    system_his = FrozenContextSystemHisFacade(
        req_client, _Client("must not be called"), _platform()
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition="M4",
        context=context,
        services=GenerationServices(
            artifacts=gateway,
            episode_id="project-without-his",
            system_his=system_his,
            his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        ),
        system_his=system_his,
        coordinator=PairedArtifactCoordinator(store),
        pairing=pairing,
        prepared_shared_artifacts=SharedArtifactRefs(initial_project=prepared_project),
        prepared_trusted_skeleton=prepared_trusted,
    )

    with pytest.raises(ValueError, match="prepared project requires prepared System-HIS"):
        bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())

    assert req_client.calls == []


def test_prepared_trusted_skeleton_without_project_rejects(tmp_path) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    pairing = PairingKey(
        paired_block_id="pair-skeleton-without-project",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="counter-instance",
        decoding_seed=7,
        model_provenance_sha256="a" * 64,
    )
    prefix = f"paired/{pairing.digest()}"
    prepared_his = gateway.put_planning(
        f"{prefix}/system-his", PlanningArtifactKind.SYSTEM_HIS, payload
    )
    prepared_trusted = gateway.put_project(
        f"{prefix}/trusted-skeleton", _repairable_project(context, payload)
    )
    system_his = FrozenContextSystemHisFacade(
        _Client("must not be called"), _Client("must not be called"), _platform()
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition="M4",
        context=context,
        services=GenerationServices(
            artifacts=gateway,
            episode_id="skeleton-without-project",
            system_his=system_his,
            his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        ),
        system_his=system_his,
        coordinator=PairedArtifactCoordinator(store),
        pairing=pairing,
        prepared_shared_artifacts=SharedArtifactRefs(system_his=prepared_his),
        prepared_trusted_skeleton=prepared_trusted,
    )

    with pytest.raises(ValueError, match="trusted skeleton requires prepared project"):
        bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())


def test_prepared_project_without_trusted_skeleton_rejects(tmp_path) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    pairing = PairingKey(
        paired_block_id="pair-project-without-skeleton",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="counter-instance",
        decoding_seed=7,
        model_provenance_sha256="a" * 64,
    )
    prefix = f"paired/{pairing.digest()}"
    prepared_his = gateway.put_planning(
        f"{prefix}/system-his", PlanningArtifactKind.SYSTEM_HIS, payload
    )
    prepared_project = gateway.put_project(
        f"{prefix}/skeleton-initial-project", _repairable_project(context, payload)
    )
    system_his = FrozenContextSystemHisFacade(
        _Client("must not be called"), _Client("must not be called"), _platform()
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition="M5",
        context=context,
        services=GenerationServices(
            artifacts=gateway,
            episode_id="project-without-skeleton",
            system_his=system_his,
            his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        ),
        system_his=system_his,
        coordinator=PairedArtifactCoordinator(store),
        pairing=pairing,
        prepared_shared_artifacts=SharedArtifactRefs(
            initial_project=prepared_project,
            system_his=prepared_his,
        ),
    )

    with pytest.raises(ValueError, match="prepared project requires prepared trusted skeleton"):
        bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())


def test_prepared_project_and_skeleton_must_share_pairing_prefix(tmp_path) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    pairing = PairingKey(
        paired_block_id="pair-prefix-binding",
        requirement_revision_id=context.revision_id,
        semantic_instance_id="counter-instance",
        decoding_seed=7,
        model_provenance_sha256="a" * 64,
    )
    prefix = f"paired/{pairing.digest()}"
    prepared_his = gateway.put_planning(
        f"{prefix}/system-his", PlanningArtifactKind.SYSTEM_HIS, payload
    )
    prepared_project = gateway.put_project(
        f"{prefix}/skeleton-initial-project", _repairable_project(context, payload)
    )
    prepared_trusted = gateway.put_project(
        "paired/wrong-prefix/trusted-skeleton", _repairable_project(context, payload)
    )
    system_his = FrozenContextSystemHisFacade(
        _Client("must not be called"), _Client("must not be called"), _platform()
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition="M5",
        context=context,
        services=GenerationServices(
            artifacts=gateway,
            episode_id="prefix-binding",
            system_his=system_his,
            his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        ),
        system_his=system_his,
        coordinator=PairedArtifactCoordinator(store),
        pairing=pairing,
        prepared_shared_artifacts=SharedArtifactRefs(
            initial_project=prepared_project,
            system_his=prepared_his,
        ),
        prepared_trusted_skeleton=prepared_trusted,
    )

    with pytest.raises(ValueError, match="prepared trusted skeleton key"):
        bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())


@pytest.mark.parametrize("method", ["M0", "M1", "M2"])
def test_non_his_bridge_rejects_prepared_artifacts_before_calls(tmp_path, method) -> None:
    context, payload = _context_and_his()
    store = ArtifactStore(tmp_path / "store")
    gateway = MethodArtifactGateway(store)
    prepared_his = gateway.put_planning(
        "prepared/non-his-system-his", PlanningArtifactKind.SYSTEM_HIS, payload
    )
    req_client = _Client("must not be called")
    system_his = FrozenContextSystemHisFacade(
        req_client, _Client("must not be called"), _platform()
    )
    bridge = FrozenContextHisGeneratorBridge(
        method_condition=method,
        context=context,
        services=GenerationServices(
            artifacts=gateway,
            episode_id=f"invalid-{method.lower()}",
            system_his=system_his,
        ),
        system_his=system_his,
        prepared_shared_artifacts=SharedArtifactRefs(system_his=prepared_his),
    )

    with pytest.raises(ValueError, match="does not accept prepared HIS artifacts"):
        bridge.generate(ProjectRequest("counter", 8, "ignored", "ignored"), _platform())

    assert req_client.calls == []


def test_missing_his_merge_preserves_existing_shared_fields() -> None:
    marker = object()
    shared = SharedArtifactRefs(initial_project=marker)
    his = object()

    merged = context_his_module._merge_shared_system_his(shared, his)

    assert merged.initial_project is marker
    assert merged.system_his is his


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
    repair_user_prompt = raw_repair.calls[0][-1]["content"]
    assert '"failed_h_stage": "h3"' not in repair_prompt
    assert "failed_h_stage: h3" in repair_prompt
    assert '"h_report"' not in repair_prompt
    assert '"task_type"' not in repair_prompt
    assert '"family_id"' not in repair_prompt
    assert "evaluator-private-name" not in repair_prompt
    assert "Do not create top-level fact-name shortcuts" in repair_user_prompt
    assert "target facts to intent, artifacts, or resources" in repair_user_prompt
    assert (
        "Every top.parameters and components[].parameters entry must be an object "
        "with a non-empty name" in repair_user_prompt
    )
    assert '{"name": "DATA_WIDTH", "default": 8}' in repair_user_prompt
    assert (
        'A string such as "DATA_WIDTH" does not declare a parameter'
        in repair_user_prompt
    )
    assert "Every clock and reset declared in top.clocks/top.resets must also appear in top.ports" in repair_user_prompt
    assert '"additionalProperties": false' in repair_user_prompt


def test_excluded_m5_variant_uses_two_his2project_repairs_with_full_accounting(
    tmp_path,
) -> None:
    context, payload = _context_and_his()
    rtl_path = payload["artifacts"]["rtl_sources"][0]
    raw_req = _Client(json.dumps(payload))
    raw_project = _Client(
        json.dumps(
            {
                "behavior_files": {
                    rtl_path: "module top; endmodule",
                }
            }
        )
    )
    second_invalid = json.dumps(
        {
            "behavior_files": {
                rtl_path: "module retry; endmodule",
            }
        }
    )
    raw_output_repair = _SequenceClient([second_invalid, _behavior_response()])
    budget = ModelCallBudget(max_calls=4)
    facade = FrozenContextSystemHisFacade(
        budget.client(raw_req, "req2his"),
        budget.client(raw_project, "his2project"),
        _platform(),
        project_output_repair_client=budget.client(
            raw_output_repair,
            "his2project_output_repair",
        ),
    )
    store = ArtifactStore(tmp_path / "store")
    services = GenerationServices(
        artifacts=MethodArtifactGateway(store),
        episode_id="episode-output-repair",
        system_his=facade,
        his_validation=FrozenContextSystemHisValidationFacade(_platform()),
        project_output_repair=facade,
    )

    outcome = EpisodeExecutor(
        max_his_corrections=1,
        max_project_output_repairs=2,
        max_shared_pre_candidate_repairs=2,
    ).emit_candidate(MethodAdapterRegistry().create("M5"), context, services)

    assert outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert outcome.his_corrections_used == 0
    assert outcome.project_output_repairs_used == 2
    assert [record["stage"] for record in budget.call_records] == [
        "req2his",
        "his2project",
        "his2project_output_repair",
        "his2project_output_repair",
    ]
    repair_prompt = json.dumps(raw_output_repair.calls, ensure_ascii=False)
    assert "module top; endmodule" in repair_prompt
    assert "module retry; endmodule" in repair_prompt
    assert "Do not include module declarations" in repair_prompt
    assert "Return behavior_files only" in repair_prompt
    assert "evaluator-private-name" not in repair_prompt
    events = [
        json.loads(store.read_verified(reference))
        for reference in services.artifacts.event_refs("episode-output-repair")
    ]
    assert [event["payload"]["state"] for event in events] == [
        "method_prepared",
        "planning_artifact_emitted",
        "h_validated",
        "project_output_rejected",
        "project_output_repair_requested",
        "project_output_rejected",
        "project_output_repair_requested",
        "candidate_emitted",
    ]


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
