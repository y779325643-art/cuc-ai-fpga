import json

from sr2fpga_agent import cli
from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.episode_executor import EpisodeExecutor, PreCandidateState
from sr2fpga_agent.frozen_context import (
    build_development_episode_pack,
    freeze_ready_requirement_context,
)
from sr2fpga_agent.generation.context_direct import (
    FrozenContextDirectProjectFacade,
    FrozenContextDirectProjectGenerator,
)
from sr2fpga_agent.generation.direct_project import DirectProjectGenerator
from sr2fpga_agent.method_adapters import (
    GenerationServices,
    MethodAdapterRegistry,
    MethodArtifactGateway,
    MethodStageFailure,
)
from sr2fpga_agent.model_budget import ModelCallBudget
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary
from sr2fpga_agent.runner import _bind_frozen_direct_generator


def _platform() -> PlatformProfile:
    return PlatformProfile("generic_verilog", "generic", "open_source")


def _context():
    request = ProjectRequest(
        task_type="counter",
        width=8,
        project_name="evaluator-private-name",
        description="Build an 8-bit synchronous counter with active-low reset.",
    )
    boundary = evaluate_requirement_boundary(request, _platform())
    return freeze_ready_requirement_context(boundary, _platform())


def _response(project_name: str = "model-name") -> str:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": project_name,
        "top": {
            "module": "top",
            "source": "rtl/design.v",
            "interface": {
                "ports": [
                    {"name": "clk", "direction": "input", "width": 1},
                    {"name": "count", "direction": "output", "width": 8},
                ]
            },
        },
        "sources": [
            {"path": "rtl/design.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [],
        "build": {"toolchain_id": "open_source", "language_standard": "verilog-2005"},
    }
    return json.dumps(
        {
            "project_name": project_name,
            "files": {
                "manifest.json": json.dumps(manifest),
                "rtl/design.v": "module top(input clk, output [7:0] count); endmodule\n",
            },
        }
    )


class _Client:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = []

    def chat(self, messages):
        self.calls.append(messages)
        return self.response


def test_frozen_direct_prompt_contains_only_public_context_not_audit_metadata() -> None:
    context = _context()
    canary = "EVALUATOR-ONLY-CANARY"
    pack = build_development_episode_pack(
        context,
        episode_id="episode-001",
        analysis_population="development",
        method_condition="M0",
        evaluator_metadata={
            "family_id": "private-counter-family",
            "task_type": "counter",
            "project_name": "evaluator-private-name",
            "canary": canary,
        },
    )
    client = _Client(_response())

    project = FrozenContextDirectProjectFacade(client).emit_project(pack.context)
    serialized_prompt = json.dumps(client.calls, ensure_ascii=False)

    assert len(client.calls) == 1
    assert project.project_name.startswith("frozen_")
    assert context.public_projection_sha256 in serialized_prompt
    assert canary not in serialized_prompt
    assert "private-counter-family" not in serialized_prompt
    assert "evaluator-private-name" not in serialized_prompt
    assert '"task_type"' not in serialized_prompt
    assert '"family_id"' not in serialized_prompt


def test_frozen_direct_facade_uses_one_budgeted_call_and_real_canonical_parser(
    tmp_path,
) -> None:
    context = _context()
    raw_client = _Client(_response())
    budget = ModelCallBudget(max_calls=1)
    facade = FrozenContextDirectProjectFacade(
        budget.client(raw_client, "direct_project")
    )
    store = ArtifactStore(tmp_path / "store")
    services = GenerationServices(
        artifacts=MethodArtifactGateway(store),
        episode_id="episode-001",
        direct=facade,
    )

    outcome = EpisodeExecutor().emit_candidate(
        MethodAdapterRegistry().create("M0"), context, services
    )

    assert outcome.final_state is PreCandidateState.CANDIDATE_EMITTED
    assert outcome.candidate is not None
    assert budget.calls_used == 1
    assert budget.failed_calls == 0
    assert budget.call_records[0]["stage"] == "direct_project"


def test_invalid_direct_response_is_a_first_class_method_failure(tmp_path) -> None:
    context = _context()
    raw_client = _Client("not json")
    budget = ModelCallBudget(max_calls=1)
    store = ArtifactStore(tmp_path / "store")
    services = GenerationServices(
        artifacts=MethodArtifactGateway(store),
        episode_id="episode-001",
        direct=FrozenContextDirectProjectFacade(
            budget.client(raw_client, "direct_project")
        ),
    )

    outcome = EpisodeExecutor().emit_candidate(
        MethodAdapterRegistry().create("M0"), context, services
    )

    assert outcome.final_state is PreCandidateState.NO_COMPLETE_CANDIDATE
    assert isinstance(outcome.failure, MethodStageFailure)
    assert outcome.failure.stage == "direct_generation"
    assert outcome.failure.error_type == "ValueError"
    assert budget.calls_used == 1
    assert len(raw_client.calls) == 1


def test_cli_m0_runtime_wraps_legacy_generator_with_frozen_context(
    tmp_path, monkeypatch, capsys
) -> None:
    client = _Client(_response())
    captured = {}

    class _Agent:
        def __init__(self, dataset_root, **kwargs):
            captured["generator"] = kwargs["project_generator"]

        def run_one(self, **kwargs):
            captured["metadata"] = kwargs["metadata"]
            return {"sample_dir": str(tmp_path / "sample"), "pass_level": "L0"}

    monkeypatch.setattr(
        cli,
        "build_project_generator",
        lambda **kwargs: DirectProjectGenerator(client, max_attempts=1),
    )
    monkeypatch.setattr(cli, "DataGenerationAgent", _Agent)

    cli.main(
        [
            "--dataset-root",
            str(tmp_path / "dataset"),
            "--sample-id",
            "sample-001",
            "--project-name",
            "evaluator-private-name",
            "--task-type",
            "counter",
            "--requirement",
            "Build an 8-bit synchronous counter with active-low reset.",
            "--provider",
            "deepseek",
        ]
    )

    assert isinstance(captured["generator"], FrozenContextDirectProjectGenerator)
    assert captured["metadata"]["method_condition"] == "M0"
    captured["generator"].generate(
        ProjectRequest("PRIVATE-TASK-CANARY", 999, "PRIVATE-NAME", "PRIVATE-DESC"),
        PlatformProfile("PRIVATE-PLATFORM", "PRIVATE-VENDOR", "PRIVATE-TOOL"),
    )
    prompt = json.dumps(client.calls, ensure_ascii=False)
    assert "PRIVATE-TASK-CANARY" not in prompt
    assert "PRIVATE-NAME" not in prompt
    assert "PRIVATE-DESC" not in prompt
    assert "PRIVATE-PLATFORM" not in prompt
    assert capsys.readouterr().out.startswith("sample_dir=")


def test_runner_binding_requires_and_consumes_validated_episode_pack() -> None:
    context = _context()
    pack = build_development_episode_pack(
        context,
        episode_id="episode-001",
        analysis_population="development",
        method_condition="M0",
        evaluator_metadata={"task_type": "PRIVATE"},
    ).to_dict()
    generator = DirectProjectGenerator(_Client(_response()), max_attempts=1)

    bound = _bind_frozen_direct_generator(
        generator,
        {"method_condition": "M0", "episode_pack": pack},
    )

    assert isinstance(bound, FrozenContextDirectProjectGenerator)


def test_runner_binding_fails_closed_without_m0_episode_pack() -> None:
    generator = DirectProjectGenerator(_Client(_response()), max_attempts=1)

    try:
        _bind_frozen_direct_generator(generator, {"method_condition": "M0"})
    except SystemExit as exc:
        assert "requires a validated episode_pack" in str(exc)
    else:
        raise AssertionError("M0 binding accepted missing episode_pack")
