import json

import pytest

from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.cost_accounting import AttemptCostLedger, AttemptCostLedgerRouter
from sr2fpga_agent.evaluator_dispatch import DevelopmentHiddenEvaluationAuthority
from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest, ToolResult
from sr2fpga_agent.parsers import parse_project_files
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.repair import ProjectRepairer


class DirectProjectWithoutHisGenerator:
    def generate(self, request, platform):
        return _direct_project(request, platform)


class BrokenDirectProjectWithoutHisGenerator:
    def generate(self, request, platform):
        project = _direct_project(request, platform)
        files = dict(project.files)
        manifest = json.loads(files["manifest.json"])
        manifest["top_module"] = "missing_top"
        files["manifest.json"] = json.dumps(manifest) + "\n"
        return GeneratedProject(project_name=project.project_name, files=files)


class MinimalRoleBasedDirectGenerator:
    def generate(self, request, platform):
        manifest = {
            "project_name": request.project_name,
            "top_module": "direct_top",
            "sources": ["src/design.v"],
        }
        return GeneratedProject(
            project_name=request.project_name,
            files={
                "manifest.json": json.dumps(manifest) + "\n",
                "src/design.v": (
                    "module direct_top(input wire clk, output reg [7:0] count);\n"
                    "  always @(posedge clk) count <= count + 1'b1;\n"
                    "endmodule\n"
                ),
            },
        )


class MultipleCandidateTestbenchGenerator:
    def generate(self, request, platform):
        manifest = {
            "contract_version": "project-package-v1",
            "project_name": request.project_name,
            "top": {
                "module": "direct_top",
                "source": "src/design.v",
                "interface": {
                    "ports": [{"name": "clk", "direction": "input", "width": 1}]
                },
            },
            "sources": [
                {
                    "path": "src/design.v",
                    "role": "rtl_source",
                    "language": "verilog",
                }
            ],
            "artifacts": [
                {
                    "path": path,
                    "role": "candidate_testbench",
                    "applicability": "advisory",
                }
                for path in ("sim/tb_a.v", "sim/tb_b.v")
            ],
            "build": {
                "toolchain_id": "open_source",
                "language_standard": "verilog-2005",
            },
        }
        testbench = (
            "module tb; reg clk = 0; direct_top dut(.clk(clk)); "
            "initial begin $display(\"TEST_PASS\"); $finish; end endmodule\n"
        )
        return GeneratedProject(
            project_name=request.project_name,
            files={
                "manifest.json": json.dumps(manifest) + "\n",
                "src/design.v": "module direct_top(input wire clk); endmodule\n",
                "sim/tb_a.v": testbench,
                "sim/tb_b.v": testbench,
            },
        )


class ProjectPackageDirectProjectWithoutHisGenerator:
    def generate(self, request, platform):
        manifest = {
            "contract_version": "project-package-v1",
            "project_name": request.project_name,
            "top": {
                "module": "top",
                "source": "rtl/top.v",
                "interface": {
                    "ports": [
                        {
                            "name": "clk",
                            "direction": "input",
                            "width": 1,
                        }
                    ],
                },
            },
            "sources": [
                {
                    "path": "rtl/top.v",
                    "role": "rtl_source",
                    "language": "verilog",
                }
            ],
            "artifacts": [],
            "build": {
                "toolchain_id": "open_source",
                "language_standard": "verilog-2005",
            },
        }
        return GeneratedProject(
            project_name=request.project_name,
            files={
                "manifest.json": json.dumps(manifest) + "\n",
                "rtl/top.v": "module top(input wire clk); reg [7:0] count; always @(posedge clk) count <= count + 1'b1; endmodule\n",
            },
        )


class VhdlDirectGenerator:
    def generate(self, request, platform):
        manifest = {
            "contract_version": "project-package-v1",
            "project_name": request.project_name,
            "top": {
                "module": "direct_top",
                "source": "src/design.vhd",
                "interface": {"ports": []},
            },
            "sources": [
                {
                    "path": "src/design.vhd",
                    "role": "rtl_source",
                    "language": "vhdl",
                }
            ],
            "artifacts": [],
            "build": {
                "toolchain_id": "open_source",
                "language_standard": "vhdl-2008",
            },
        }
        return GeneratedProject(
            project_name=request.project_name,
            files={
                "manifest.json": json.dumps(manifest) + "\n",
                "src/design.vhd": (
                    "entity direct_top is end entity;\n"
                    "architecture rtl of direct_top is begin end architecture;\n"
                ),
            },
        )


class CountingDirectProjectWithoutHisGenerator:
    def __init__(self, error=None):
        self.calls = 0
        self.error = error

    def generate(self, request, platform):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return _direct_project(request, platform)


class PassingRunner:
    def __init__(self):
        self.stages = []

    def run(self, command, cwd, stage, timeout_seconds=30):
        self.stages.append(stage)
        stdout = "TEST_PASS\n" if stage in {"sim_run", "candidate_sim_run"} else ""
        if stage == "synth":
            stdout = "Number of cells: 1\n  SB_LUT4 1\n"
        return ToolResult(
            stage=stage,
            command=list(command),
            status="passed",
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_seconds=0.01,
        )


class MissingCoreToolRunner(PassingRunner):
    def __init__(self, missing_stage):
        super().__init__()
        self.missing_stage = missing_stage

    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == self.missing_stage:
            self.stages.append(stage)
            return ToolResult(
                stage=stage,
                command=list(command),
                status="missing_tool",
                exit_code=None,
                stdout="",
                stderr=f"Missing executable: {command[0]}",
                duration_seconds=0.01,
            )
        return super().run(command, cwd, stage, timeout_seconds)


class FailingCandidateSmokeRunner(PassingRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage != "candidate_sim_run":
            return super().run(command, cwd, stage, timeout_seconds)
        self.stages.append(stage)
        return ToolResult(
            stage=stage,
            command=list(command),
            status="failed",
            exit_code=1,
            stdout="TEST_FAIL mismatch\n",
            stderr="",
            duration_seconds=0.01,
        )


class UnexpectedRepairer:
    def __init__(self):
        self.calls = 0

    def repair(self, project, diagnosis):
        self.calls += 1
        raise AssertionError("infrastructure and capability gaps must not trigger repair")


class StaticChatClient:
    def __init__(self, payload):
        self.payload = payload

    def chat(self, messages):
        return self.payload


def _request() -> ProjectRequest:
    return ProjectRequest(task_type="counter", width=8, project_name="direct_counter")


def _platform() -> PlatformProfile:
    return PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")


def _direct_project(request: ProjectRequest, platform: PlatformProfile) -> GeneratedProject:
    project = ProjectGenerator().generate(request, platform)
    files = dict(project.files)
    files.pop("system_his.json")
    return GeneratedProject(project_name=project.project_name, files=files)


def _requirement_boundary(disposition: str) -> dict:
    boundary = {
        "boundary_version": "requirement-boundary-v1",
        "requirement_id": "req-direct-counter",
        "disposition": disposition,
        "clarification_fact_ids": [],
        "clarification_questions": [],
        "capability_gap_ids": [],
    }
    if disposition == "needs_clarification":
        boundary["clarification_fact_ids"] = ["interface_protocols"]
        boundary["clarification_questions"] = ["Which interface protocol applies?"]
    elif disposition == "capability_gap":
        boundary["capability_gap_ids"] = ["pcie"]
    return boundary


def test_direct_project_parser_accepts_complete_project_without_system_his() -> None:
    project = _direct_project(_request(), _platform())

    files = parse_project_files(json.dumps({"files": project.files}))

    assert "system_his.json" not in files
    assert files["manifest.json"] == project.files["manifest.json"]


def test_direct_project_repair_does_not_require_system_his() -> None:
    project = _direct_project(_request(), _platform())
    repaired_files = dict(project.files)
    repaired_files["rtl/top.v"] = repaired_files["rtl/top.v"].replace(
        "module top",
        "// repaired\nmodule top",
        1,
    )
    repairer = ProjectRepairer(
        StaticChatClient(json.dumps({"files": repaired_files})),
        max_attempts=1,
    )

    repaired = repairer.repair(
        project,
        {
            "stage": "lint",
            "failure_type": "syntax_error",
            "root_cause": "syntax error",
            "affected_files": ["rtl/top.v"],
        },
    )

    assert "system_his.json" not in repaired.generated_project.files
    assert "// repaired" in repaired.generated_project.files["rtl/top.v"]


@pytest.mark.parametrize("method_condition", ["M0", "M1", "M2"])
def test_non_his_method_candidate_smoke_has_no_formal_l2_credit(
    tmp_path,
    method_condition,
) -> None:
    runner = PassingRunner()
    agent = DataGenerationAgent(
        tmp_path / "dataset",
        command_runner=runner,
        project_generator=DirectProjectWithoutHisGenerator(),
    )

    result = agent.run_one(
        f"sample_{method_condition.lower()}",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={
            "method_condition": method_condition,
            "requirement_boundary": _requirement_boundary("ready"),
        },
    )

    sample_dir = tmp_path / "dataset" / f"sample_{method_condition.lower()}"
    labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
    trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
    sim_compile = json.loads(
        (sample_dir / "attempts/attempt_000/eval/sim_compile.json").read_text(
            encoding="utf-8"
        )
    )
    candidate_sim_run = json.loads(
        (sample_dir / "attempts/attempt_000/eval/candidate_sim_run.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["pass_level"] == "L1"
    assert labels["checks"]["l0_complete"] is True
    assert labels["checks"]["l1_lint_pass"] is True
    assert labels["l2_sim_status"] == "not_run"
    assert labels["l2_sim_skip_reason"] == "needs_oracle"
    assert labels["checks"]["l2_sim_pass"] is False
    assert labels["checks"]["l3_synth_pass"] is True
    assert sim_compile["status"] == "not_run"
    assert sim_compile["skip_reason"] == "needs_oracle"
    assert candidate_sim_run["status"] == "passed"
    assert labels["generated_his_pass_level"] == "NOT_APPLICABLE"
    for stage in ("h0", "h1", "h2", "h3"):
        assert labels[f"{stage}_status"] == "not_applicable"
        assert trajectory["his_validation"][stage]["status"] == "not_applicable"
    assert trajectory["generated_his"] is None
    assert runner.stages == ["lint", "candidate_sim_compile", "candidate_sim_run", "synth"]


def test_development_hidden_evaluation_records_opaque_outcome(tmp_path) -> None:
    runner = PassingRunner()
    evaluator_calls: list[object] = []
    candidate_store = ArtifactStore(tmp_path / "candidate-store")
    cost_router = AttemptCostLedgerRouter()

    def cost_ledger_factory(attempt_id: int) -> AttemptCostLedger:
        return AttemptCostLedger(
            candidate_store,
            episode_id="sample_hidden_development",
            attempt_id=f"attempt-{attempt_id:03d}",
            method_condition="M1",
            failure_origin="natural_llm",
            candidate_id=f"sample_hidden_development-attempt-{attempt_id:03d}",
            input_artifact_hashes=("a" * 64,),
        )

    def evaluator(value):
        evaluator_calls.append(value)
        return {
            "outcome": "pass",
            "private_case": value.private_commitment_sha256,
        }

    authority = DevelopmentHiddenEvaluationAuthority(
        candidate_store,
        ArtifactStore(tmp_path / "evaluator-store"),
        evaluator,
    )
    sample_dir_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        sample_dir_root,
        command_runner=runner,
        project_generator=ProjectPackageDirectProjectWithoutHisGenerator(),
        development_hidden_evaluation_authority=authority,
        development_hidden_private_commitment=b"opaque-commitment",
        attempt_cost_ledger_factory=cost_ledger_factory,
        attempt_cost_router=cost_router,
    )

    result = agent.run_one(
        "sample_hidden_development",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={
            "method_condition": "M1",
            "analysis_population": "development",
            "requirement_boundary": _requirement_boundary("ready"),
        },
    )

    sample_dir = sample_dir_root / "sample_hidden_development"
    trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
    labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
    assert result["pass_level"] == "L1"
    assert labels["checks"]["l2_hidden_pass"] is False
    assert trajectory["development_hidden_outcome"] == {
        "outcome_id": trajectory["development_hidden_outcome"]["outcome_id"],
        "contract_id": "development-hidden-outcome-v1",
    }
    assert evaluator_calls
    assert "outcome" not in trajectory["development_hidden_outcome"]
    canonical = agent.last_canonical_trajectory
    assert canonical is not None
    assert canonical.payload["lineage_complete"] is True
    assert canonical.payload["development_hidden_outcome_ref"] == trajectory[
        "development_hidden_outcome"
    ]
    assert (
        evaluator_calls[0].terminal_candidate_sha256
        == canonical.payload["terminal_candidate_ref"]["sha256"]
    )
    hidden_cost = agent.last_cost_summaries[0].payload["axes"][
        "hidden_evaluator_tool_calls"
    ]
    assert hidden_cost["status"] == "measured"
    assert hidden_cost["value"] == 1


def test_development_hidden_evaluation_refuses_a_second_candidate_store(tmp_path) -> None:
    runner = PassingRunner()
    evaluator_calls: list[object] = []
    cost_store = ArtifactStore(tmp_path / "cost-store")
    cost_router = AttemptCostLedgerRouter()

    def cost_ledger_factory(attempt_id: int) -> AttemptCostLedger:
        return AttemptCostLedger(
            cost_store,
            episode_id="sample_hidden_store_mismatch",
            attempt_id=f"attempt-{attempt_id:03d}",
            method_condition="M1",
            failure_origin="natural_llm",
            candidate_id=f"sample_hidden_store_mismatch-attempt-{attempt_id:03d}",
        )

    authority = DevelopmentHiddenEvaluationAuthority(
        ArtifactStore(tmp_path / "second-candidate-store"),
        ArtifactStore(tmp_path / "evaluator-store"),
        lambda value: evaluator_calls.append(value) or {"outcome": "pass"},
    )
    sample_dir_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        sample_dir_root,
        command_runner=runner,
        project_generator=ProjectPackageDirectProjectWithoutHisGenerator(),
        development_hidden_evaluation_authority=authority,
        development_hidden_private_commitment=b"opaque-commitment",
        attempt_cost_ledger_factory=cost_ledger_factory,
        attempt_cost_router=cost_router,
    )

    agent.run_one(
        "sample_hidden_store_mismatch",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={
            "method_condition": "M1",
            "analysis_population": "development",
            "requirement_boundary": _requirement_boundary("ready"),
        },
    )

    trajectory = json.loads(
        (sample_dir_root / "sample_hidden_store_mismatch/eval/trajectory.json").read_text(
            encoding="utf-8"
        )
    )
    assert evaluator_calls == []
    assert "development_hidden_outcome" not in trajectory
    assert agent.last_canonical_trajectory is not None
    assert (
        agent.last_canonical_trajectory.payload["development_hidden_outcome_ref"]
        is None
    )
    assert not (authority.candidate_store.root / "refs").exists()


def test_non_development_population_skips_development_hidden_evaluation(tmp_path) -> None:
    runner = PassingRunner()
    evaluator_calls: list[object] = []

    def evaluator(value):
        evaluator_calls.append(value)
        return {"outcome": "pass"}

    authority = DevelopmentHiddenEvaluationAuthority(
        ArtifactStore(tmp_path / "candidate-store"),
        ArtifactStore(tmp_path / "evaluator-store"),
        evaluator,
    )
    sample_dir_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        sample_dir_root,
        command_runner=runner,
        project_generator=DirectProjectWithoutHisGenerator(),
        development_hidden_evaluation_authority=authority,
        development_hidden_private_commitment=b"opaque-commitment",
    )

    result = agent.run_one(
        "sample_hidden_official_vpp",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={
            "method_condition": "M1",
            "analysis_population": "official_vpp",
            "requirement_boundary": _requirement_boundary("ready"),
        },
    )

    sample_dir = sample_dir_root / "sample_hidden_official_vpp"
    trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
    labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
    assert result["pass_level"] == "L1"
    assert labels["checks"]["l2_hidden_pass"] is False
    assert "development_hidden_outcome" not in trajectory
    assert evaluator_calls == []


def test_candidate_smoke_failure_does_not_block_synth_or_trigger_repair(tmp_path) -> None:
    runner = FailingCandidateSmokeRunner()
    repairer = UnexpectedRepairer()
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        command_runner=runner,
        project_generator=DirectProjectWithoutHisGenerator(),
        repairer=repairer,
        max_attempts=2,
    )

    result = agent.run_one(
        "sample_candidate_smoke_fail",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={"method_condition": "M2"},
    )

    sample_dir = dataset_root / "sample_candidate_smoke_fail"
    labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
    candidate_sim_run = json.loads(
        (sample_dir / "attempts/attempt_000/eval/candidate_sim_run.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["pass_level"] == "L1"
    assert candidate_sim_run["status"] == "failed"
    assert labels["l2_sim_status"] == "not_run"
    assert labels["checks"]["l3_synth_pass"] is True
    assert repairer.calls == 0
    assert runner.stages == ["lint", "candidate_sim_compile", "candidate_sim_run", "synth"]


def test_direct_method_still_fails_method_neutral_l0(tmp_path) -> None:
    runner = PassingRunner()
    agent = DataGenerationAgent(
        tmp_path / "dataset",
        command_runner=runner,
        project_generator=BrokenDirectProjectWithoutHisGenerator(),
    )

    result = agent.run_one(
        "sample_direct_l0_fail",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={"method_condition": "M0"},
    )

    labels = json.loads(
        (tmp_path / "dataset/sample_direct_l0_fail/eval/labels.json").read_text(encoding="utf-8")
    )
    diagnosis = json.loads(
        (
            tmp_path
            / "dataset/sample_direct_l0_fail/attempts/attempt_000/diagnosis.json"
        ).read_text(encoding="utf-8")
    )
    assert result["pass_level"] == "L0_FAIL"
    assert labels["h0_status"] == "not_applicable"
    assert labels["checks"]["l0_complete"] is False
    assert diagnosis["stage"] == "l0_consistency"
    assert diagnosis["affected_files"] == ["manifest.json"]
    assert runner.stages == []


def test_direct_minimal_package_without_candidate_tb_qor_or_sdc_runs_lint_and_synth(
    tmp_path,
) -> None:
    runner = PassingRunner()
    agent = DataGenerationAgent(
        tmp_path / "dataset",
        command_runner=runner,
        project_generator=MinimalRoleBasedDirectGenerator(),
    )

    result = agent.run_one(
        "sample_direct_minimal_package",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={"method_condition": "M0"},
    )

    labels = json.loads(
        (
            tmp_path
            / "dataset/sample_direct_minimal_package/eval/labels.json"
        ).read_text(encoding="utf-8")
    )
    assert result["pass_level"] == "L1"
    assert labels["checks"]["l0_complete"] is True
    assert labels["checks"]["l1_lint_pass"] is True
    assert labels["l2_sim_status"] == "not_run"
    assert labels["l2_sim_skip_reason"] == "needs_oracle"
    assert labels["checks"]["l3_synth_pass"] is True
    assert runner.stages == ["lint", "synth"]


def test_multiple_candidate_testbenches_are_diagnostic_not_formal_l2(tmp_path) -> None:
    runner = PassingRunner()
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        command_runner=runner,
        project_generator=MultipleCandidateTestbenchGenerator(),
    )

    result = agent.run_one(
        "sample_multiple_candidate_tbs",
        "Design a direct hardware block.",
        _request(),
        _platform(),
        metadata={"method_condition": "M2"},
    )

    sample_dir = dataset_root / "sample_multiple_candidate_tbs"
    labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
    candidate_compile = json.loads(
        (
            sample_dir
            / "attempts/attempt_000/eval/candidate_sim_compile.json"
        ).read_text(encoding="utf-8")
    )
    assert result["pass_level"] == "L1"
    assert labels["l2_sim_status"] == "not_run"
    assert labels["l2_sim_skip_reason"] == "needs_oracle"
    assert labels["checks"]["l3_synth_pass"] is True
    assert candidate_compile["status"] == "not_run"
    assert candidate_compile["skip_reason"] == "multiple_candidate_testbenches"
    assert labels["h0_status"] == "not_applicable"
    assert runner.stages == ["lint", "synth"]


@pytest.mark.parametrize(
    ("missing_stage", "expected_pass_level", "expected_stages"),
    [
        ("lint", "L0", ["lint"]),
        ("synth", "L1", ["lint", "synth"]),
    ],
)
def test_missing_core_tool_is_infrastructure_not_run_without_repair(
    tmp_path,
    missing_stage,
    expected_pass_level,
    expected_stages,
) -> None:
    runner = MissingCoreToolRunner(missing_stage)
    repairer = UnexpectedRepairer()
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        command_runner=runner,
        project_generator=MinimalRoleBasedDirectGenerator(),
        repairer=repairer,
        max_attempts=2,
    )

    result = agent.run_one(
        f"sample_missing_{missing_stage}_tool",
        "Design a direct hardware block.",
        _request(),
        _platform(),
        metadata={"method_condition": "M2"},
    )

    sample_dir = dataset_root / f"sample_missing_{missing_stage}_tool"
    labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
    trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
    tool_result = json.loads(
        (
            sample_dir / f"attempts/attempt_000/eval/{missing_stage}.json"
        ).read_text(encoding="utf-8")
    )
    measurement = trajectory["attempt_measurements"][0]
    assert result["pass_level"] == expected_pass_level
    assert tool_result["status"] == "not_run"
    assert tool_result["skip_reason"] == "missing_tool"
    assert labels["automatic_pass_credit"] is False
    assert labels["automatic_pass_credit_reason"] == "missing_tool"
    assert labels["failure_origin"] == "toolchain_environment_failure"
    assert measurement["repair_eligible"] is False
    assert measurement["repair_skip_reason"] == "infrastructure_failure"
    assert measurement["infrastructure_reason"] == "missing_tool"
    assert repairer.calls == 0
    assert runner.stages == expected_stages


def test_unsupported_synthesis_language_is_capability_gap_without_repair(
    tmp_path,
) -> None:
    runner = PassingRunner()
    repairer = UnexpectedRepairer()
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        command_runner=runner,
        project_generator=VhdlDirectGenerator(),
        repairer=repairer,
        max_attempts=2,
    )
    result = agent.run_one(
        "sample_unsupported_synth_language",
        "Design a direct hardware block.",
        _request(),
        _platform(),
        metadata={"method_condition": "M2"},
    )

    sample_dir = dataset_root / "sample_unsupported_synth_language"
    trajectory = json.loads((sample_dir / "eval/trajectory.json").read_text(encoding="utf-8"))
    synth = json.loads(
        (sample_dir / "attempts/attempt_000/eval/synth.json").read_text(encoding="utf-8")
    )
    measurement = trajectory["attempt_measurements"][0]
    assert result["pass_level"] == "L0"
    assert synth["status"] == "not_run"
    assert synth["skip_reason"] == "capability_gap"
    assert measurement["repair_eligible"] is False
    assert measurement["repair_skip_reason"] == "capability_gap"
    assert repairer.calls == 0
    assert runner.stages == []


@pytest.mark.parametrize(
    ("disposition", "method_condition", "failure_type", "result_key", "expected", "h_status"),
    [
        (
            "needs_clarification",
            "M0",
            "requirement_clarification_required",
            "questions",
            ["Which interface protocol applies?"],
            "not_applicable",
        ),
        ("capability_gap", "M4", "capability_gap", "capability_gaps", ["pcie"], "not_run"),
    ],
)
def test_nonready_requirement_boundary_stops_before_project_generator_call(
    tmp_path,
    disposition,
    method_condition,
    failure_type,
    result_key,
    expected,
    h_status,
) -> None:
    generator = CountingDirectProjectWithoutHisGenerator()
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(dataset_root, project_generator=generator)

    result = agent.run_one(
        f"sample_{disposition}",
        "Design a hardware block.",
        _request(),
        _platform(),
        metadata={
            "method_condition": method_condition,
            "requirement_boundary": _requirement_boundary(disposition),
        },
    )

    sample_dir = dataset_root / f"sample_{disposition}"
    generation = json.loads(
        (sample_dir / "attempts/attempt_000/eval/generation.json").read_text(
            encoding="utf-8"
        )
    )
    labels = json.loads((sample_dir / "eval/labels.json").read_text(encoding="utf-8"))
    assert generator.calls == 0
    assert result["failure_type"] == failure_type
    assert result[result_key] == expected
    assert generation["status"] == "not_run"
    assert generation["skip_reason"] == failure_type
    assert labels["automatic_pass_credit"] is False
    assert labels["h0_status"] == h_status


def test_invalid_requirement_boundary_stops_before_generation(tmp_path) -> None:
    generator = CountingDirectProjectWithoutHisGenerator()
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(dataset_root, project_generator=generator)

    result = agent.run_one(
        "sample_invalid_boundary",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={
            "method_condition": "M0",
            "requirement_boundary": {
                **_requirement_boundary("ready"),
                "boundary_version": "unknown-boundary-version",
            },
        },
    )

    generation = json.loads(
        (
            dataset_root
            / "sample_invalid_boundary/attempts/attempt_000/eval/generation.json"
        ).read_text(encoding="utf-8")
    )
    assert generator.calls == 0
    assert result["failure_type"] == "invalid_requirement_boundary_metadata"
    assert generation["status"] == "not_run"


def test_direct_generation_failure_keeps_h_stages_not_applicable(tmp_path) -> None:
    generator = CountingDirectProjectWithoutHisGenerator(ValueError("invalid project response"))
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(dataset_root, project_generator=generator)

    result = agent.run_one(
        "sample_direct_generation_fail",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={"method_condition": "M0"},
    )

    labels = json.loads(
        (dataset_root / "sample_direct_generation_fail/eval/labels.json").read_text(
            encoding="utf-8"
        )
    )
    assert generator.calls == 1
    assert result["failure_type"] == "generation_failed"
    for stage in ("h0", "h1", "h2", "h3"):
        assert labels[f"{stage}_status"] == "not_applicable"


def test_his_method_without_system_his_still_fails_h0(tmp_path) -> None:
    runner = PassingRunner()
    agent = DataGenerationAgent(
        tmp_path / "dataset",
        command_runner=runner,
        project_generator=DirectProjectWithoutHisGenerator(),
    )

    result = agent.run_one(
        "sample_his_missing",
        "Design an 8-bit counter.",
        _request(),
        _platform(),
        metadata={"method_condition": "M4"},
    )

    labels = json.loads(
        (tmp_path / "dataset/sample_his_missing/eval/labels.json").read_text(encoding="utf-8")
    )
    assert result["pass_level"] == "H0_FAIL"
    assert labels["h0_status"] == "fail"
    assert labels["h1_status"] == "not_run"
    assert runner.stages == []
