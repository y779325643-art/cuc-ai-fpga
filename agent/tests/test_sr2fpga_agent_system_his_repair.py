import copy
import json

import pytest

from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
from sr2fpga_agent import deepseek
from sr2fpga_agent.generation import (
    DirectProjectGenerator,
    HisProjectGenerator,
    OracleHisProjectGenerator,
    SystemHisGenerator,
    TwoStageProjectGenerator,
)
from sr2fpga_agent.his_validation import SystemHisValidationError, validate_system_his_h_stages
from sr2fpga_agent.models import (
    GeneratedProject,
    PlatformProfile,
    ProjectRequest,
    RepairResult,
    ToolResult,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.repair import ProjectRepairer, SystemHisRepairer


class SequencedClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.messages_history: list[list[dict[str, str]]] = []

    def stream_chat(self, messages: list[dict[str, str]]) -> str:
        self.messages_history.append(copy.deepcopy(messages))
        return self.responses.pop(0)


class PassingCommandRunner:
    def run(self, command, cwd, stage, timeout_seconds=30):
        stdout = "TEST_PASS\n" if stage in {"sim_run", "candidate_sim_run"} else ""
        if stage == "synth":
            stdout = "Number of cells: 1\n  SB_LUT4 1\n"
        return ToolResult(stage, list(command), "passed", 0, stdout, "", 0.01)


class FailFirstLintCommandRunner(PassingCommandRunner):
    def __init__(self) -> None:
        self.lint_calls = 0

    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage == "lint":
            self.lint_calls += 1
            if self.lint_calls == 1:
                return ToolResult(
                    stage,
                    list(command),
                    "failed",
                    1,
                    "",
                    "syntax error",
                    0.01,
                )
        return super().run(command, cwd, stage, timeout_seconds)


class CommentProjectRepairer:
    def __init__(self) -> None:
        self.calls = 0

    def repair(self, project, diagnosis):
        self.calls += 1
        files = dict(project.files)
        files["rtl/top.v"] = "// repaired\n" + files["rtl/top.v"]
        repaired = GeneratedProject(project_name=project.project_name, files=files)
        return RepairResult(repaired, "rtl/top.v repaired")


def _request(width: int = 8) -> ProjectRequest:
    return ProjectRequest(
        task_type="composed_event_counter",
        width=width,
        project_name=f"event_counter_{width}bit",
        description=f"Build a {width}-bit event counter.",
    )


def _platform() -> PlatformProfile:
    return PlatformProfile(name="generic_verilog", vendor="generic", toolchain="open_source")


def _valid_his(request: ProjectRequest) -> dict:
    project = ProjectGenerator().generate(request, _platform())
    return json.loads(project.files["system_his.json"])


def _invalid_his(stage: str, request: ProjectRequest) -> str:
    if stage == "h0":
        return "not-json"
    if stage == "h3":
        return json.dumps(_valid_his(_request(8)))
    system_his = _valid_his(request)
    if stage == "h1":
        system_his["instances"][0]["component"] = "missing_component"
    elif stage == "h2":
        system_his["components"][1]["semantic_kind"] = "unsupported_future_component"
    return json.dumps(system_his)


@pytest.mark.parametrize(
    ("failed_stage", "width"),
    [("h0", 8), ("h1", 8), ("h2", 8), ("h3", 16)],
)
def test_req2his_repairs_all_h_stages(failed_stage: str, width: int) -> None:
    request = _request(width)
    corrected = _valid_his(request)
    client = SequencedClient([_invalid_his(failed_stage, request), json.dumps(corrected)])
    events: list[dict] = []

    generator = SystemHisGenerator(
        client,
        max_attempts=2,
        event_sink=events.append,
    )
    result = generator.generate(request, _platform())

    assert result == corrected
    assert isinstance(generator.repairer, SystemHisRepairer)
    retry = next(event for event in events if event["event"] == "generation_stage_retry")
    assert retry["stage"] == "req2his"
    assert retry["failed_h_stage"] == failed_stage
    assert retry["repair_layer"] == "system_his"
    assert retry["next_attempt_id"] == 1
    assert retry["diagnostics"]
    assert "previous System-HIS output failed validation" in client.messages_history[1][-1]["content"]


def test_two_stage_rebuilds_complete_project_after_his_repair() -> None:
    request = _request()
    corrected = _valid_his(request)
    invalid = json.loads(json.dumps(corrected))
    invalid["components"][1]["semantic_kind"] = "unsupported_future_component"
    client = SequencedClient([json.dumps(invalid), json.dumps(corrected)])
    generator = TwoStageProjectGenerator(client, max_attempts=2)

    class SkeletonHis2Project:
        def generate(self, request, platform, system_his):
            return build_contract_skeleton_project(request, platform, system_his)

    generator.his_project_generator = SkeletonHis2Project()

    project = generator.generate(request, _platform())

    assert validate_system_his_h_stages(
        request,
        project,
        platform=_platform(),
    )["passed"] is True
    assert {
        "system_his.json",
        "manifest.json",
        "rtl/top.v",
        "constraints/timing.sdc",
        "sim/tb_top.v",
        "reports/predicted_qor.json",
    }.issubset(project.files)


def test_duplicate_component_source_is_repaired_before_his2project() -> None:
    request = _request()
    corrected = _valid_his(request)
    invalid = copy.deepcopy(corrected)
    invalid["components"][1]["source"] = invalid["components"][0]["source"]
    client = SequencedClient([json.dumps(invalid), json.dumps(corrected)])
    events: list[dict] = []
    generator = TwoStageProjectGenerator(client, max_attempts=2, event_sink=events.append)
    lowered_candidates: list[dict] = []

    class RecordingHis2Project:
        def generate(self, request, platform, system_his):
            lowered_candidates.append(copy.deepcopy(system_his))
            return build_contract_skeleton_project(request, platform, system_his)

    generator.his_project_generator = RecordingHis2Project()

    project = generator.generate(request, _platform())

    assert lowered_candidates == [corrected]
    assert validate_system_his_h_stages(request, project, platform=_platform())["passed"] is True
    retry = next(event for event in events if event["event"] == "generation_stage_retry")
    assert retry["failed_h_stage"] == "h2"
    assert "same source path" in "\n".join(retry["diagnostics"])


def test_req2his_budget_exhaustion_preserves_failed_h_stage() -> None:
    request = _request()
    client = SequencedClient([_invalid_his("h0", request)])

    with pytest.raises(SystemHisValidationError) as exc_info:
        SystemHisGenerator(client, max_attempts=1).generate(request, _platform())

    assert exc_info.value.failed_h_stage == "h0"
    assert len(client.messages_history) == 1


def test_agent_records_exhausted_h_stage_instead_of_marking_all_h_gates_not_run(
    tmp_path,
) -> None:
    request = _request()
    dataset_root = tmp_path / "dataset"
    generator = TwoStageProjectGenerator(SequencedClient(["not-json"]), max_attempts=1)
    agent = DataGenerationAgent(dataset_root, project_generator=generator)

    result = agent.run_one(
        sample_id="h0-exhausted",
        requirement=request.description,
        request=request,
        platform=_platform(),
    )

    labels = json.loads(
        (dataset_root / "h0-exhausted" / "eval" / "labels.json").read_text(
            encoding="utf-8"
        )
    )
    diagnosis = json.loads(
        (
            dataset_root
            / "h0-exhausted"
            / "attempts"
            / "attempt_000"
            / "diagnosis.json"
        ).read_text(encoding="utf-8")
    )
    assert result["failure_type"] == "his_validation_failed"
    assert result["failed_h_stage"] == "h0"
    assert labels["h0_status"] == "fail"
    assert labels["h1_status"] == "not_run"
    assert labels["generated_his_pass_credit"] is False
    assert diagnosis["failed_h_stage"] == "h0"
    assert diagnosis["repair_scope"] == "system_his"
    assert diagnosis["his_validation"]["h0"]["status"] == "fail"


@pytest.mark.parametrize(
    ("failed_stage", "width"),
    [("h0", 8), ("h1", 8), ("h2", 8), ("h3", 16)],
)
def test_agent_outer_h_repair_records_candidate_then_lowers(
    tmp_path,
    failed_stage: str,
    width: int,
) -> None:
    request = _request(width)
    corrected = _valid_his(request)
    client = SequencedClient([_invalid_his(failed_stage, request), json.dumps(corrected)])
    generator = TwoStageProjectGenerator(client, max_attempts=1)
    lowered_candidates: list[dict] = []

    class RecordingHis2Project:
        def generate(self, request, platform, system_his):
            lowered_candidates.append(copy.deepcopy(system_his))
            return build_contract_skeleton_project(request, platform, system_his)

    generator.his_project_generator = RecordingHis2Project()
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        command_runner=PassingCommandRunner(),
        project_generator=generator,
        max_attempts=2,
    )

    result = agent.run_one(
        sample_id=f"outer-{failed_stage}",
        requirement=request.description,
        request=request,
        platform=_platform(),
        metadata={"method_condition": "M5"},
    )

    sample_dir = dataset_root / f"outer-{failed_stage}"
    attempt_0_files = list(
        (sample_dir / "attempts/attempt_000/generated_project").rglob("*")
    )
    diagnosis = json.loads(
        (sample_dir / "attempts/attempt_000/diagnosis.json").read_text(
            encoding="utf-8"
        )
    )
    trajectory = json.loads(
        (sample_dir / "eval/trajectory.json").read_text(encoding="utf-8")
    )
    patch = json.loads(
        (sample_dir / "attempts/attempt_000/patch.json").read_text(encoding="utf-8")
    )
    assert result["pass_level"] == "L1"
    assert lowered_candidates == [corrected]
    assert [path.name for path in attempt_0_files if path.is_file()] == ["system_his.json"]
    assert diagnosis["stage"] == "his_validation"
    assert diagnosis["failed_h_stage"] == failed_stage
    assert diagnosis["repair_scope"] == "system_his"
    assert diagnosis["h_stage_diagnostics"]
    assert diagnosis["his_validation"][failed_stage]["status"] == "fail"
    assert (sample_dir / "attempts/attempt_000/patch.diff").read_text(
        encoding="utf-8"
    ).startswith("--- a/system_his.json")
    assert patch["files_touched"] == ["system_his.json"]
    assert patch["tool_result_before"][failed_stage] == "fail"
    assert patch["tool_result_after"][failed_stage] == "pass"
    assert patch["repair_regression"]["repair_scope"] == "system_his"
    assert patch["automatic_pass_credit"] is True
    assert trajectory["attempt_measurements"][0]["repair_scope"] == "system_his"
    assert trajectory["attempt_measurements"][0]["repair_attempted"] is True
    assert trajectory["attempt_measurements"][0]["repair_call_status"] == "succeeded"
    assert trajectory["measurement"]["repair_attempts_used"] == 1
    assert trajectory["his_validation"]["h3"]["status"] == "pass"
    assert len(client.messages_history) == 2


@pytest.mark.parametrize(
    ("max_attempts", "expected_project_repairs", "expected_pass_level"),
    [(2, 0, "L0"), (3, 1, "L1")],
)
def test_h_and_project_repairs_share_one_attempt_budget(
    tmp_path,
    max_attempts: int,
    expected_project_repairs: int,
    expected_pass_level: str,
) -> None:
    request = _request()
    corrected = _valid_his(request)
    client = SequencedClient([_invalid_his("h2", request), json.dumps(corrected)])
    generator = TwoStageProjectGenerator(client, max_attempts=1)

    class SkeletonHis2Project:
        def generate(self, request, platform, system_his):
            return build_contract_skeleton_project(request, platform, system_his)

    generator.his_project_generator = SkeletonHis2Project()
    project_repairer = CommentProjectRepairer()
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        command_runner=FailFirstLintCommandRunner(),
        project_generator=generator,
        repairer=project_repairer,
        max_attempts=max_attempts,
    )

    result = agent.run_one(
        sample_id=f"shared-budget-{max_attempts}",
        requirement=request.description,
        request=request,
        platform=_platform(),
        metadata={"method_condition": "M5"},
    )

    attempt_dirs = sorted(
        (dataset_root / f"shared-budget-{max_attempts}" / "attempts").iterdir()
    )
    trajectory = json.loads(
        (
            dataset_root
            / f"shared-budget-{max_attempts}"
            / "eval/trajectory.json"
        ).read_text(encoding="utf-8")
    )
    assert result["pass_level"] == expected_pass_level
    assert project_repairer.calls == expected_project_repairs
    assert len(attempt_dirs) == max_attempts
    project_attempt = trajectory["attempt_measurements"][1]
    assert project_attempt["repair_scope"] == "project"
    assert project_attempt["repair_attempted"] is bool(expected_project_repairs)
    assert project_attempt["repair_call_status"] == (
        "succeeded" if expected_project_repairs else "not_run"
    )


def test_outer_h_repair_records_invalid_next_candidate_as_its_own_attempt(
    tmp_path,
) -> None:
    request = _request()
    client = SequencedClient(
        [_invalid_his("h0", request), _invalid_his("h1", request)]
    )
    generator = TwoStageProjectGenerator(client, max_attempts=1)
    dataset_root = tmp_path / "dataset"
    agent = DataGenerationAgent(
        dataset_root,
        project_generator=generator,
        max_attempts=2,
    )

    result = agent.run_one(
        sample_id="invalid-h-repair",
        requirement=request.description,
        request=request,
        platform=_platform(),
        metadata={"method_condition": "M5"},
    )

    sample_dir = dataset_root / "invalid-h-repair"
    trajectory = json.loads(
        (sample_dir / "eval/trajectory.json").read_text(encoding="utf-8")
    )
    first_patch = json.loads(
        (sample_dir / "attempts/attempt_000/patch.json").read_text(encoding="utf-8")
    )
    second_diagnosis = json.loads(
        (sample_dir / "attempts/attempt_001/diagnosis.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["pass_level"] == "H1_FAIL"
    assert result["failed_h_stage"] == "h1"
    assert first_patch["tool_result_before"]["h0"] == "fail"
    assert first_patch["tool_result_after"]["h0"] == "pass"
    assert first_patch["tool_result_after"]["h1"] == "fail"
    assert trajectory["attempt_measurements"][0]["repair_call_status"] == (
        "candidate_failed_validation"
    )
    assert second_diagnosis["failed_h_stage"] == "h1"
    assert list(
        path.name
        for path in (sample_dir / "attempts/attempt_001/generated_project").rglob("*")
        if path.is_file()
    ) == ["system_his.json"]


def test_generate_from_system_his_revalidates_before_lowering() -> None:
    request = _request()
    invalid = _valid_his(request)
    invalid["components"][1]["semantic_kind"] = "unsupported_future_component"
    generator = TwoStageProjectGenerator(SequencedClient([]), max_attempts=1)

    class MustNotRunHis2Project:
        def generate(self, request, platform, system_his):
            raise AssertionError("HIS2PROJECT ran before H0-H3 passed")

    generator.his_project_generator = MustNotRunHis2Project()

    with pytest.raises(SystemHisValidationError) as exc_info:
        generator.generate_from_system_his(request, _platform(), invalid)

    assert exc_info.value.failed_h_stage == "h2"


def test_provider_specific_names_are_compatibility_aliases_only() -> None:
    assert DirectProjectGenerator.__name__ == "DirectProjectGenerator"
    assert HisProjectGenerator.__name__ == "HisProjectGenerator"
    assert OracleHisProjectGenerator.__name__ == "OracleHisProjectGenerator"
    assert SystemHisGenerator.__name__ == "SystemHisGenerator"
    assert TwoStageProjectGenerator.__name__ == "TwoStageProjectGenerator"
    assert ProjectRepairer.__name__ == "ProjectRepairer"
    assert deepseek.DeepSeekProjectGenerator is DirectProjectGenerator
    assert deepseek.DeepSeekSystemHisGenerator is SystemHisGenerator
    assert deepseek.DeepSeekTwoStageProjectGenerator is TwoStageProjectGenerator
    assert deepseek.DeepSeekRepairer is ProjectRepairer
