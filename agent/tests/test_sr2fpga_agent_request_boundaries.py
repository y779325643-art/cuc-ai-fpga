import json
from pathlib import Path

import pytest

from sr2fpga_agent import cli
from sr2fpga_agent.agent import DataGenerationAgent, _diagnose_first_failure, _labels
from sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
from sr2fpga_agent.generation import TwoStageProjectGenerator
from sr2fpga_agent.generation.req2his import (
    RequirementCapabilityGapError,
    RequirementClarificationRequired,
)
from sr2fpga_agent.frozen_context import validate_episode_pack
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest, ToolResult
from sr2fpga_agent.requirement_envelope import (
    build_request_requirement_envelope,
    build_requirement_envelope,
)
from sr2fpga_agent.runner import (
    RunnerConfig,
    SourceConnection,
    TaskConfig,
    _count_level_labels,
    _default_requirement,
    _measurement_freeze_sample_record,
    _task_expansion_items,
    load_runner_config,
    planned_samples,
    runner_preflight,
)
from sr2fpga_agent.recorder import _verification_episode_metadata


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "t4_dual_stream_join.system-his-v1.2.json"
)

FAMILY_RECIPE_DECISION_KEYS = {
    "recipe_id",
    "version",
    "sha256",
    "family_id",
    "matched_alias",
    "status",
    "reason",
    "policy_id",
    "policy_version",
    "policy_sha256",
    "policy_status",
    "catalog_version",
}


class PassingCommandRunner:
    def __init__(self) -> None:
        self.stages: list[str] = []

    def run(
        self,
        command: list[str],
        cwd: Path,
        stage: str,
        timeout_seconds: int = 30,
    ) -> ToolResult:
        self.stages.append(stage)
        return ToolResult(stage, command, "passed", 0, "", "", 0.0)


class FailingProjectGenerator:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def generate(self, request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
        raise self.error


def _platform() -> PlatformProfile:
    return PlatformProfile(
        name="generic_verilog",
        vendor="generic",
        toolchain="open_source",
    )


def _write_project(project: GeneratedProject, project_dir: Path) -> None:
    for relative_path, content in project.files.items():
        target = project_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _runner_config(
    tmp_path: Path,
    *,
    task_type: str,
    source: SourceConnection,
) -> RunnerConfig:
    return RunnerConfig(
        dataset_root=tmp_path / "datasets",
        export_root=tmp_path / "exports",
        run_root=tmp_path / "runs",
        provider=source.name,
        repair_provider="none",
        max_attempts=1,
        refresh_exports=False,
        line_b_targets={"max_samples": 1},
        tasks=[TaskConfig(source=source.name, task_type=task_type, widths=[8], count=1)],
        sources={source.name: source},
    )


def test_missing_oracle_marker_skips_simulation_but_retains_synthesis_evidence(
    tmp_path: Path,
) -> None:
    system_his = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    request = ProjectRequest(
        task_type="unclassified_stream_system",
        width=8,
        project_name="unclassified_stream_system_8",
        description="Generate a stream system outside the benchmark catalog.",
    )
    project = build_contract_skeleton_project(request, _platform(), system_his)
    assert "SR2FPGA_ORACLE_STATUS: needs_oracle" in project.files["sim/tb_top.v"]
    project_dir = tmp_path / "project"
    _write_project(project, project_dir)
    command_runner = PassingCommandRunner()
    agent = DataGenerationAgent(tmp_path / "dataset", command_runner=command_runner)

    results = agent._run_pipeline(project, project_dir, _platform())

    assert results["sim_compile"].status == "not_run"
    assert results["sim_compile"].skip_reason == "needs_oracle"
    assert results["sim_run"].status == "not_run"
    assert results["sim_run"].skip_reason == "needs_oracle"
    assert results["synth"].status == "passed"
    assert command_runner.stages == ["lint", "synth"]
    assert _diagnose_first_failure(results) is None
    labels = _labels(
        results,
        {
            "status": "not_run",
            "skip_reason": "disabled_by_config",
            "tool": "openxc7_nextpnr",
        },
        final_attempt_id=0,
        failure_count=0,
    )
    assert labels["pass_level"] == "L1"
    assert labels["checks"]["l2_sim_pass"] is False
    assert labels["checks"]["l3_synth_pass"] is True
    assert labels["l2_sim_status"] == "not_run"
    assert labels["l2_sim_skip_reason"] == "needs_oracle"
    verification = _verification_episode_metadata(labels, {})
    assert verification["l2_core"]["status"] == "not_run"
    assert verification["l2_core"]["skip_reason"] == "needs_oracle"
    assert verification["l2_core"]["public"]["status"] == "not_run"
    assert verification["l2_core"]["public"]["skip_reason"] == "needs_oracle"
    assert verification["l3"]["status"] == "pass"
    levels = {
        "l0": {"pass": 0, "fail": 0},
        "l1": {"pass": 0, "fail": 0},
        "l2": {"pass": 0, "fail": 0},
        "l3": {"pass": 0, "fail": 0},
        "l4_open": {"pass": 0, "fail": 0, "not_run": 0},
    }
    _count_level_labels(levels, labels)
    assert levels["l2"] == {"pass": 0, "fail": 0, "not_run": 1}


def test_runner_expands_unknown_task_without_fuzzy_catalog_matching() -> None:
    task = TaskConfig(
        source="api",
        task_type="unclassified_dma_bridge",
        widths=[16],
        count=1,
    )

    assert _task_expansion_items(task) == [
        ("", "unclassified_dma_bridge", "", "unclassified", 16)
    ]


def test_two_stage_metadata_records_the_v12_contract(tmp_path: Path) -> None:
    source = SourceConnection(
        name="request-api",
        kind="openai_compat",
        model="test-model",
        base_url="https://example.invalid",
        api_key_env="REQUEST_API_KEY",
        generation_mode="two_stage",
    )
    config = _runner_config(
        tmp_path,
        task_type="alu_control_unit",
        source=source,
    )
    sample = _task_expansion_items(config.tasks[0])
    assert sample[0][1] == "alu_control_unit"
    planned = planned_samples(config)

    metadata = planned[0].metadata(config)

    assert metadata["system_his_schema_version"] == "system-his-v1.2"
    assert metadata["training_split"] == "clean"
    assert "request_mode" not in metadata
    assert validate_episode_pack(metadata["episode_pack"]) == ()
    assert metadata["episode_pack"]["audit_only"]["method_condition_id"] == "M4"
    assert "family_id" not in metadata["episode_pack"]["public_context"]
    decision = metadata["family_recipe_decision"]
    assert FAMILY_RECIPE_DECISION_KEYS <= set(decision)
    assert decision["status"] == "applied"
    assert decision["matched_alias"] == "alu_control_unit"
    assert decision["recipe_id"] == "sr2fpga-family-recipe:alu_control_unit"
    assert json.loads(json.dumps(decision)) == decision
    assert _measurement_freeze_sample_record(planned[0], config)[
        "family_recipe_decision"
    ] == decision


@pytest.mark.parametrize(
    ("kind", "generation_mode"),
    [("deterministic", ""), ("deepseek", "direct")],
)
def test_preflight_allows_generation_method_independent_of_request_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    generation_mode: str,
) -> None:
    monkeypatch.setenv("REQUEST_API_KEY", "test-only-key")
    source = SourceConnection(
        name="method-source",
        kind=kind,
        model="test-model",
        base_url="https://example.invalid",
        api_key_env="REQUEST_API_KEY",
        generation_mode=generation_mode,
    )
    config = _runner_config(
        tmp_path,
        task_type="unclassified_dma_bridge",
        source=source,
    )

    report = runner_preflight(config, validate_provider=False)

    assert report["ok"] is True
    assert report["errors"] == []
    assert report["samples"][0]["task_type"] == "unclassified_dma_bridge"
    assert "family_recipe_decision" not in planned_samples(config)[0].metadata(config)


def test_default_counter_requirement_does_not_add_unrelated_capabilities(
    tmp_path: Path,
) -> None:
    source = SourceConnection(
        name="api",
        kind="openai_compat",
        generation_mode="two_stage",
    )
    config = _runner_config(
        tmp_path,
        task_type="counter",
        source=source,
    )

    sample = planned_samples(config)[0]
    envelope = build_request_requirement_envelope(
        ProjectRequest(
            task_type=sample.task_type,
            width=sample.width,
            project_name=sample.project_name,
            description=sample.requirement,
        ),
        _platform(),
    )

    assert envelope.capability_labels == ("counter",)
    assert all(token not in sample.requirement for token in ("FIFO", "SPI", "UART", "PWM"))


def test_unknown_task_uses_clean_generic_requirement(
    tmp_path: Path,
) -> None:
    source = SourceConnection(
        name="api",
        kind="openai_compat",
        generation_mode="two_stage",
    )
    config = _runner_config(
        tmp_path,
        task_type="customer_custom_block",
        source=source,
    )

    sample = planned_samples(config)[0]

    assert sample.requirement == "Generate an 8-bit customer_custom_block FPGA RTL project."
    assert all(token not in sample.requirement for token in ("FIFO", "SPI", "UART", "PWM"))


def test_contract_requirement_does_not_inject_unrelated_task_families() -> None:
    requirement = _default_requirement("counter", 8, requirement_style="contract")

    assert "Use an appropriate multi-file RTL structure" in requirement
    assert all(token not in requirement for token in ("FIFO", "SPI", "UART", "PWM"))


def test_runner_config_preserves_explicit_task_requirement(tmp_path: Path) -> None:
    config_path = tmp_path / "runner.json"
    requirement = "Build an 8-bit counter exposed through a Wishbone bus."
    config_path.write_text(
        json.dumps(
            {
                "dataset_root": str(tmp_path / "datasets"),
                "export_root": str(tmp_path / "exports"),
                "run_root": str(tmp_path / "runs"),
                "line_b_targets": {"max_samples": 1},
                "tasks": [
                    {
                        "source": "api",
                        "task_type": "counter",
                        "widths": [8],
                        "count": 1,
                        "requirement": requirement,
                    }
                ],
                "sources": {
                    "api": {
                        "kind": "openai_compat",
                        "generation_mode": "two_stage",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_runner_config(config_path)

    assert config.tasks[0].requirement == requirement
    assert planned_samples(config)[0].requirement == requirement


def test_runner_config_rejects_removed_request_mode(tmp_path: Path) -> None:
    config_path = tmp_path / "legacy.json"
    config_path.write_text(
        json.dumps(
            {
                "dataset_root": str(tmp_path / "datasets"),
                "export_root": str(tmp_path / "exports"),
                "run_root": str(tmp_path / "runs"),
                "request_mode": "product",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="request_mode has been removed"):
        load_runner_config(config_path)


def test_runner_config_rejects_removed_family_recipe_switch(tmp_path: Path) -> None:
    config_path = tmp_path / "legacy.json"
    config_path.write_text(
        json.dumps(
            {
                "dataset_root": str(tmp_path / "datasets"),
                "export_root": str(tmp_path / "exports"),
                "run_root": str(tmp_path / "runs"),
                "family_recipe": True,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="family_recipe has been removed.*automatic policy"):
        load_runner_config(config_path)


def test_runner_task_rejects_removed_family_recipe_switch(tmp_path: Path) -> None:
    config_path = tmp_path / "legacy-task.json"
    config_path.write_text(
        json.dumps(
            {
                "dataset_root": str(tmp_path / "datasets"),
                "export_root": str(tmp_path / "exports"),
                "run_root": str(tmp_path / "runs"),
                "tasks": [
                    {
                        "task_type": "counter",
                        "widths": [8],
                        "count": 1,
                        "family_recipe": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="task family_recipe has been removed.*automatic policy"):
        load_runner_config(config_path)


def test_cli_rejects_removed_request_mode(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            [
                "--dataset-root",
                str(tmp_path / "dataset"),
                "--sample-id",
                "sample-1",
                "--project-name",
                "unified-project",
                "--request-mode",
                "product",
            ]
        )
    assert exc_info.value.code == 2


def test_cli_rejects_removed_family_recipe_switch(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            [
                "--dataset-root",
                str(tmp_path / "dataset"),
                "--sample-id",
                "sample-1",
                "--project-name",
                "unified-project",
                "--family-recipe",
            ]
        )
    assert exc_info.value.code == 2


def test_cli_deterministic_provider_requires_explicit_task_type(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="--task-type is required"):
        cli.main(
            [
                "--dataset-root",
                str(tmp_path / "dataset"),
                "--sample-id",
                "sample-1",
                "--project-name",
                "unified-project",
                "--provider",
                "deterministic",
            ]
        )


def test_cli_accepts_real_two_stage_provider_without_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_one(self, **kwargs):
        captured["project_generator"] = self.project_generator
        captured.update(kwargs)
        return {"sample_dir": str(tmp_path / "dataset" / "sample-1"), "pass_level": "H3"}

    monkeypatch.setenv("REQUEST_API_KEY", "test-only-key")
    monkeypatch.setattr(DataGenerationAgent, "run_one", fake_run_one)

    cli.main(
        [
            "--dataset-root",
            str(tmp_path / "dataset"),
            "--sample-id",
            "sample-1",
            "--project-name",
            "unified-project",
            "--task-type",
            "alu_control_unit",
            "--requirement",
            "Build an 8-bit ALU control unit with add, subtract, and, or, and status flags.",
            "--provider",
            "openai_compat",
            "--model",
            "test-model",
            "--base-url",
            "https://example.invalid",
            "--api-key-env",
            "REQUEST_API_KEY",
        ]
    )

    assert isinstance(captured["project_generator"], TwoStageProjectGenerator)
    request = captured["request"]
    assert isinstance(request, ProjectRequest)
    assert request.task_type == "alu_control_unit"
    assert not hasattr(request, "request_mode")
    assert not hasattr(request, "family_recipe")
    decision = captured["metadata"]["family_recipe_decision"]
    assert FAMILY_RECIPE_DECISION_KEYS <= set(decision)
    assert json.loads(json.dumps(decision)) == decision


@pytest.mark.parametrize("provider", ["deterministic", "deepseek"])
def test_cli_non_two_stage_method_omits_family_recipe_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_one(self, **kwargs):
        captured.update(kwargs)
        return {"sample_dir": str(tmp_path / "dataset" / "sample-1"), "pass_level": "L1"}

    monkeypatch.setenv("REQUEST_API_KEY", "test-only-key")
    monkeypatch.setattr(DataGenerationAgent, "run_one", fake_run_one)
    cli.main(
        [
            "--dataset-root",
            str(tmp_path / "dataset"),
            "--sample-id",
            "sample-1",
            "--project-name",
            "unified-project",
            "--task-type",
            "counter",
            "--provider",
            provider,
            "--api-key-env",
            "REQUEST_API_KEY",
        ]
    )

    metadata = captured["metadata"]
    assert metadata["requirement_boundary"]["disposition"] == "ready"
    assert metadata["method_condition"] in {"M0", "reference_deterministic"}
    assert "family_recipe_decision" not in metadata


def test_requirement_clarification_is_recorded_as_not_run_and_returned_to_caller(
    tmp_path: Path,
) -> None:
    envelope = build_requirement_envelope(
        "Build a custom hardware system.",
        defaults={
            "data_width_bits": 8,
            "clock_frequencies_hz": (100_000_000,),
            "reset_polarity": "active_low",
            "target_platform": "generic_verilog",
            "acceptance_criteria": "independent verification",
        },
    )
    error = RequirementClarificationRequired(envelope, ("functional_decomposition",))
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        project_generator=FailingProjectGenerator(error),
    )

    result = agent.run_one(
        sample_id="clarification-sample",
        requirement=envelope.raw_requirement,
        request=ProjectRequest(
            task_type="custom_system",
            width=8,
            project_name="custom_system",
            description=envelope.raw_requirement,
        ),
        platform=_platform(),
    )

    labels = json.loads(
        (dataset_root / "clarification-sample" / "eval" / "labels.json").read_text(
            encoding="utf-8"
        )
    )
    attempt = json.loads(
        (dataset_root / "clarification-sample" / "attempts" / "attempt_000" / "eval" / "generation.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["failure_type"] == "requirement_clarification_required"
    assert result["questions"] == [
        "Which independently verifiable hardware capabilities make up the system?"
    ]
    assert labels["failure_origin"] == "requirement_boundary"
    assert labels["automatic_pass_credit"] is False
    assert attempt["status"] == "not_run"
    assert attempt["skip_reason"] == "requirement_clarification_required"


def test_requirement_capability_gap_is_not_recorded_as_design_failure(tmp_path: Path) -> None:
    error = RequirementCapabilityGapError("req-test", ("dma", "external_memory"))
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        project_generator=FailingProjectGenerator(error),
    )

    result = agent.run_one(
        sample_id="capability-gap-sample",
        requirement="Build a DMA bridge to DDR memory.",
        request=ProjectRequest(
            task_type="custom_dma_bridge",
            width=32,
            project_name="custom_dma_bridge",
            description="Build a DMA bridge to DDR memory.",
        ),
        platform=_platform(),
    )

    labels = json.loads(
        (dataset_root / "capability-gap-sample" / "eval" / "labels.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["failure_type"] == "capability_gap"
    assert result["capability_gaps"] == ["dma", "external_memory"]
    assert labels["failure_origin"] == "backend_capability_gap"
    assert labels["automatic_pass_credit"] is False
