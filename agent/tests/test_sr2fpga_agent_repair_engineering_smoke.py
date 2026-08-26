from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from sr2fpga_agent.artifact_store import (
    ArtifactIntegrityError,
    ArtifactRef,
    ArtifactStore,
    OneShotViolation,
)
from sr2fpga_agent.agent import DataGenerationAgent as RealDataGenerationAgent
from sr2fpga_agent.episode_outcome import (
    EpisodeOutcomeError,
    read_verified_development_episode_outcome,
    reconcile_development_episode_outcome,
)
from sr2fpga_agent.evaluator_dispatch import (
    DevelopmentHiddenEvaluationAuthority,
    read_verified_development_hidden_conformance_outcome,
)
from sr2fpga_agent.frozen_context import (
    context_from_validated_episode_pack,
    frozen_project_name,
)
from sr2fpga_agent.generation.direct_project import DirectProjectGenerator
from sr2fpga_agent.models import (
    GeneratedProject,
    PlatformProfile,
    ProjectRequest,
    RepairResult,
    ToolResult,
)
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.runner import (
    RunnerConfig,
    SourceConnection,
    TaskConfig,
    planned_samples,
    run_batch,
)


class _StaticClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def stream_chat(self, _messages):
        return self.response

    def chat(self, _messages):
        return self.response


class _PassingCommandRunner:
    def run(self, command, cwd, stage, timeout_seconds=30):
        if stage in {"lint", "public_l1_lint"} and "missing_count" in (
            Path(cwd) / "rtl/top.v"
        ).read_text(encoding="utf-8"):
            return ToolResult(
                stage=stage,
                command=list(command),
                status="failed",
                exit_code=1,
                stdout="",
                stderr="Signal missing_count is not declared\n",
                duration_seconds=0.001,
            )
        stdout = "TEST_PASS\n" if stage == "candidate_sim_run" else ""
        return ToolResult(
            stage=stage,
            command=list(command),
            status="passed",
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_seconds=0.001,
        )


class _BudgetedSyntheticRepairer:
    def __init__(self, model_budget, *, touch_trusted_surface: bool) -> None:
        self._model_budget = model_budget
        self._touch_trusted_surface = touch_trusted_surface

    def repair(self, project, diagnosis):
        call_id, started = self._model_budget.reserve(
            "project_repair",
            "synthetic_engineering_smoke",
            len(json.dumps(diagnosis, sort_keys=True)),
        )
        files = dict(project.files)
        if self._touch_trusted_surface:
            files["sim/tb_top.v"] += "\n// forbidden synthetic edit\n"
            patch_diff = "diff --git a/sim/tb_top.v b/sim/tb_top.v\n"
        else:
            files["rtl/top.v"] = files["rtl/top.v"].replace(
                "count <= missing_count +",
                "count <= count +",
                1,
            )
            patch_diff = "diff --git a/rtl/top.v b/rtl/top.v\n"
        self._model_budget.finish(
            call_id,
            "project_repair",
            "synthetic_engineering_smoke",
            started,
            output_chars=sum(len(value) for value in files.values()),
        )
        return RepairResult(
            generated_project=GeneratedProject(
                project_name=project.project_name,
                files=files,
            ),
            patch_diff=patch_diff,
        )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _direct_project_response(metadata: dict, requirement: str) -> str:
    context = context_from_validated_episode_pack(metadata["episode_pack"])
    request = ProjectRequest(
        "counter",
        4,
        frozen_project_name(context),
        requirement,
    )
    project = ProjectGenerator().generate(
        request,
        PlatformProfile("generic_verilog", "generic", "open_source"),
    )
    system_his = json.loads(project.files["system_his.json"])
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": project.project_name,
        "top": {
            "module": system_his["artifacts"]["top_module"],
            "source": system_his["artifacts"]["rtl_sources"][0],
            "interface": {
                "ports": [
                    {
                        "name": port["name"],
                        "direction": port["dir"],
                        "width": port["width"],
                    }
                    for port in system_his["top"]["ports"]
                ]
            },
        },
        "sources": [
            {"path": path, "role": "rtl_source", "language": "verilog"}
            for path in system_his["artifacts"]["rtl_sources"]
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
    files = {
        path: content
        for path, content in project.files.items()
        if path not in {"manifest.json", "system_his.json"}
    }
    files["manifest.json"] = json.dumps(manifest, sort_keys=True) + "\n"
    return json.dumps({"project_name": project.project_name, "files": files})


def _write_trusted_public_l2_harness(root: Path) -> Path:
    root.mkdir(parents=True)
    testbench = (
        "module trusted_tb;\n"
        "  reg clk = 0; reg rst_n = 0; reg en = 0; wire [3:0] count;\n"
        "  top dut(.clk(clk), .rst_n(rst_n), .en(en), .count(count));\n"
        "  initial begin #1; $finish; end\n"
        "endmodule\n"
    )
    (root / "trusted_tb.v").write_text(
        testbench,
        encoding="utf-8",
        newline="\n",
    )
    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "contract_version": "development-public-l2-harness-v1",
                "harness_id": "excluded-m1-repair-public-l2-v1",
                "evaluation_scope": "development_excluded_public_l2",
                "testbench_top": "trusted_tb",
                "language_standard": "verilog-2005",
                "files": [
                    {
                        "path": "trusted_tb.v",
                        "sha256": hashlib.sha256(testbench.encode("utf-8")).hexdigest(),
                    }
                ],
                "timeout_seconds": 20,
                "pass_rule": "simulator_exit_zero",
                "official_authority": False,
                "g4b_authorized": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest_path


def test_runner_repair_engineering_smoke_is_budgeted_and_fail_closed(
    tmp_path,
    monkeypatch,
) -> None:
    dataset_root = tmp_path / "datasets"
    run_root = tmp_path / "runs"
    requirement = "Build a 4-bit synchronous counter with enable and active-low reset."
    harness_manifest = _write_trusted_public_l2_harness(
        tmp_path / "trusted-public-l2"
    )
    source = SourceConnection(
        name="fake-direct",
        kind="openai_compat",
        model="fake-model",
        generation_mode="direct",
    )
    repair = SourceConnection(
        name="fake-repair",
        kind="openai_compat",
        model="fake-repair-model",
        generation_mode="direct",
    )
    config = RunnerConfig(
        dataset_root=dataset_root,
        export_root=tmp_path / "exports",
        run_root=run_root,
        provider="fake-direct",
        repair_provider="fake-repair",
        max_attempts=2,
        refresh_exports=False,
        max_model_calls=2,
        sources={"fake-direct": source, "fake-repair": repair},
        line_b_targets={"max_samples": 2},
        tasks=[
            TaskConfig(
                source="fake-direct",
                task_type="counter",
                widths=[4],
                count=1,
                failure_injectors=["undefined_signal_reference"],
                failure_origin="synthetic_injected",
                measurement_point="b_tool_in_loop_repair",
                evaluation_line="line_b",
                requirement=requirement,
                method_condition="M1",
                analysis_population="excluded",
                semantic_instance_id=f"semantic-counter-m1-repair-{index:03d}",
                decoding_seed=17,
                paired_block_id=f"pair-counter-m1-repair-{index:03d}-seed-17",
                public_l2_harness_manifest=str(harness_manifest),
            )
            for index in (1, 2)
        ],
    )
    metadata = planned_samples(config)[0].metadata(config)
    direct_response = _direct_project_response(metadata, requirement)

    monkeypatch.setattr(
        "sr2fpga_agent.runner.build_project_generator_for_connection",
        lambda connection, **kwargs: DirectProjectGenerator(
            _StaticClient(direct_response)
        ),
    )

    def build_repairer(repairers, config, sample, model_budget=None):
        return _BudgetedSyntheticRepairer(
            model_budget,
            touch_trusted_surface=sample.sample_id.endswith("000002"),
        )

    monkeypatch.setattr("sr2fpga_agent.runner._repairer_for_sample", build_repairer)

    def build_agent(dataset_root, **kwargs):
        return RealDataGenerationAgent(
            dataset_root,
            command_runner=_PassingCommandRunner(),
            **kwargs,
        )

    monkeypatch.setattr("sr2fpga_agent.runner.DataGenerationAgent", build_agent)
    monkeypatch.setattr(
        "sr2fpga_agent.runner._development_hidden_evaluator",
        lambda _value: {
            "outcome": "pass",
            "private_case": "excluded-repair-hidden-secret",
        },
    )

    summary = run_batch(config, run_id="repair-engineering-smoke")

    successful_id = "sample_runner_counter_4_000001"
    rejected_id = "sample_runner_counter_4_000002"
    successful_dir = dataset_root / successful_id
    rejected_dir = dataset_root / rejected_id
    successful_labels = _read_json(successful_dir / "eval/labels.json")
    successful_trajectory = _read_json(successful_dir / "eval/trajectory.json")
    successful_patch = _read_json(
        successful_dir / "attempts/attempt_000/patch.json"
    )
    rejected_labels = _read_json(rejected_dir / "eval/labels.json")
    rejected_trajectory = _read_json(rejected_dir / "eval/trajectory.json")
    rejected_patch = _read_json(rejected_dir / "attempts/attempt_000/patch.json")
    successful_metadata = _read_json(successful_dir / "metadata.json")
    rejected_metadata = _read_json(rejected_dir / "metadata.json")
    events = [
        json.loads(line)
        for line in (run_root / "repair-engineering-smoke/events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    completed = [event for event in events if event["event"] == "sample_completed"]
    successful_completion = next(
        event for event in completed if event["sample_id"] == successful_id
    )
    rejected_completion = next(
        event for event in completed if event["sample_id"] == rejected_id
    )
    artifact_store = ArtifactStore(
        run_root / "repair-engineering-smoke" / "method_artifacts"
    )
    canonical_trajectory = json.loads(
        artifact_store.read_verified(
            ArtifactRef(**successful_completion["canonical_trajectory_ref"])
        )
    )
    selection = json.loads(
        artifact_store.read_verified(
            ArtifactRef(**successful_completion["development_terminal_selection_ref"])
        )
    )
    outcome, outcome_ref = reconcile_development_episode_outcome(
        artifact_store,
        public_evaluation_ref=ArtifactRef(
            **successful_completion["development_public_evaluation_ref"]
        ),
        trajectory_ref=ArtifactRef(
            **successful_completion["canonical_trajectory_ref"]
        ),
    )

    assert summary["total_completed"] == 2
    assert successful_metadata["failure_origin"] == "synthetic_injected"
    assert rejected_metadata["failure_origin"] == "synthetic_injected"
    assert successful_metadata["model_call_budget"]["model_calls_used"] == 1
    assert rejected_metadata["model_call_budget"]["model_calls_used"] == 1
    assert successful_trajectory["measurement"]["initial"]["pass_level"] == "L0"
    assert successful_trajectory["measurement"]["final"]["pass_level"] == "L1"
    assert successful_trajectory["measurement"]["repair_calls_attempted"] == 1
    assert successful_trajectory["measurement"]["repair_transitions"] == 1
    assert successful_trajectory["measurement"]["repair_success"] is True
    assert successful_patch["repair_regression"]["fixed_target"] is True
    assert successful_patch["repair_regression"]["regressed_levels"] == []
    assert successful_patch["touched_trusted_artifacts"] is False
    assert successful_patch["automatic_pass_credit"] is True
    assert successful_labels["automatic_pass_credit"] is True
    assert successful_labels["development_public_acceptance"] is True
    assert successful_labels["official_outcome"] is False
    assert len(canonical_trajectory["attempts"]) == 2
    assert selection["selected_attempt_id"] == "attempt-001"
    assert outcome["repair"] == {
        "reconciliation_status": "complete",
        "calls_attempted": 1,
        "transitions": 1,
        "successes": 1,
        "diagnosis_count": 1,
        "valid_patch_count": 1,
        "rerun_count": 1,
        "by_scope": {
            "system_his": {"calls_attempted": 0, "transitions": 0},
            "project": {"calls_attempted": 1, "transitions": 1},
        },
        "issues": [],
    }
    assert outcome["development_vpp_l3_status"] == "evaluated"
    assert outcome["development_vpp_l3"] is True
    assert outcome["vpp_l3_status"] == "not_evaluated"
    assert outcome["vpp_l3"] is None
    assert outcome["official_outcome"] is False
    assert json.loads(artifact_store.read_verified(outcome_ref)) == outcome
    assert successful_completion["development_episode_outcome_ref"] == (
        outcome_ref.to_dict()
    )
    assert "development_episode_outcome_ref" not in rejected_completion
    outer_repair_attempts = 0
    for reference in outcome["cost_summary_refs"]:
        summary_payload = json.loads(
            artifact_store.read_verified(ArtifactRef(**reference))
        )
        outer_repair_attempts += summary_payload["axes"]["outer_repair_attempts"][
            "value"
        ]
    assert outer_repair_attempts == 1

    assert rejected_patch["status"] == "invalid_edit_surface"
    assert rejected_patch["touched_trusted_artifacts"] is True
    assert rejected_patch["automatic_pass_credit"] is False
    assert rejected_labels["automatic_pass_credit"] is False
    assert rejected_trajectory["measurement"]["repair_transitions"] == 0
    assert not (rejected_dir / "attempts/attempt_001").exists()
    assert "forbidden synthetic edit" not in (
        rejected_dir / "final/generated_project/sim/tb_top.v"
    ).read_text(encoding="utf-8")

    started = [event for event in events if event["event"] == "model_call_started"]
    finished = [event for event in events if event["event"] == "model_call_finished"]
    assert len(started) == len(finished) == len(completed) == 2
    assert {event["stage"] for event in started} == {"project_repair"}
    assert {event["failure_origin"] for event in completed} == {
        "synthetic_injected"
    }


def test_runner_hidden_fail_is_terminal_one_shot_and_never_repairs(
    tmp_path,
    monkeypatch,
) -> None:
    dataset_root = tmp_path / "datasets"
    run_root = tmp_path / "runs"
    requirement = "Build a 4-bit synchronous counter with enable and active-low reset."
    harness_manifest = _write_trusted_public_l2_harness(
        tmp_path / "trusted-public-l2"
    )
    source = SourceConnection(
        name="fake-direct",
        kind="openai_compat",
        model="fake-model",
        generation_mode="direct",
    )
    repair_source = SourceConnection(
        name="fake-repair",
        kind="openai_compat",
        model="fake-repair-model",
        generation_mode="direct",
    )
    config = RunnerConfig(
        dataset_root=dataset_root,
        export_root=tmp_path / "exports",
        run_root=run_root,
        provider="fake-direct",
        repair_provider="fake-repair",
        max_attempts=2,
        refresh_exports=False,
        max_model_calls=2,
        sources={"fake-direct": source, "fake-repair": repair_source},
        line_b_targets={"max_samples": 1},
        tasks=[
            TaskConfig(
                source="fake-direct",
                task_type="counter",
                widths=[4],
                count=1,
                requirement=requirement,
                method_condition="M1",
                analysis_population="excluded",
                semantic_instance_id="semantic-counter-m1-hidden-fail-001",
                decoding_seed=17,
                paired_block_id="pair-counter-m1-hidden-fail-001-seed-17",
                public_l2_harness_manifest=str(harness_manifest),
            )
        ],
    )
    sample = planned_samples(config)[0]
    direct_response = _direct_project_response(sample.metadata(config), requirement)
    direct_client = _StaticClient(direct_response)
    monkeypatch.setattr(
        "sr2fpga_agent.runner.build_project_generator_for_connection",
        lambda _connection, **_kwargs: DirectProjectGenerator(direct_client),
    )

    repair_calls: list[dict] = []

    class _RepairSpy:
        def repair(self, _project, diagnosis):
            repair_calls.append(dict(diagnosis))
            raise AssertionError("hidden outcome must never trigger repair")

    repair_spy = _RepairSpy()
    monkeypatch.setattr(
        "sr2fpga_agent.runner._repairer_for_sample",
        lambda *_args, **_kwargs: repair_spy,
    )

    built_repairers: list[object] = []

    def build_agent(dataset_root, **kwargs):
        built_repairers.append(kwargs.get("repairer"))
        return RealDataGenerationAgent(
            dataset_root,
            command_runner=_PassingCommandRunner(),
            **kwargs,
        )

    monkeypatch.setattr("sr2fpga_agent.runner.DataGenerationAgent", build_agent)
    hidden_inputs = []
    private_canary = "excluded-hidden-fail-canary"

    def hidden_fail(evaluator_input):
        hidden_inputs.append(evaluator_input)
        return {"outcome": "fail", "private_case": private_canary}

    monkeypatch.setattr(
        "sr2fpga_agent.runner._development_hidden_evaluator",
        hidden_fail,
    )

    summary = run_batch(config, run_id="hidden-fail-engineering-smoke")
    run_dir = run_root / "hidden-fail-engineering-smoke"
    store = ArtifactStore(run_dir / "method_artifacts")
    completion = next(
        event
        for event in (
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        if event.get("event") == "sample_completed"
    )
    trajectory_ref = ArtifactRef(**completion["canonical_trajectory_ref"])
    trajectory = json.loads(store.read_verified(trajectory_ref))
    terminal_ref = ArtifactRef(**trajectory["terminal_candidate_ref"])
    hidden_ref = ArtifactRef(
        **completion["development_hidden_conformance_outcome_ref"]
    )
    hidden = read_verified_development_hidden_conformance_outcome(
        store,
        hidden_ref,
    )
    outcome_ref = ArtifactRef(**completion["development_episode_outcome_ref"])
    outcome = read_verified_development_episode_outcome(store, outcome_ref)

    assert summary["total_completed"] == 1
    assert built_repairers == [repair_spy]
    assert repair_calls == []
    assert len(hidden_inputs) == 1
    assert hidden_inputs[0].terminal_candidate_sha256 == terminal_ref.sha256
    assert hidden["terminal_candidate_sha256"] == terminal_ref.sha256
    assert hidden["execution_status"] == "completed"
    assert hidden["hidden_l2"] == {"status": "fail", "reason": None}
    assert hidden["generation_visible"] is False
    assert hidden["repair_visible"] is False
    assert hidden["official_outcome"] is False
    assert hidden["g4b_authorized"] is False
    assert outcome["stage_outcomes"]["l0"]["status"] == "pass"
    assert outcome["stage_outcomes"]["l1"]["status"] == "pass"
    assert outcome["stage_outcomes"]["public_l2"]["status"] == "pass"
    assert outcome["stage_outcomes"]["l3"]["status"] == "pass"
    assert outcome["repair"]["calls_attempted"] == 0
    assert outcome["repair"]["transitions"] == 0
    assert outcome["repair"]["successes"] == 0
    assert outcome["development_vpp_l3_status"] == "evaluated"
    assert outcome["development_vpp_l3"] is False
    assert outcome["development_vpp_l3_reasons"] == ["hidden_l2_failed"]
    assert outcome["vpp_l3_status"] == "not_evaluated"
    assert outcome["vpp_l3"] is None
    assert outcome["official_outcome"] is False
    assert outcome["rq1_evidence"] is False
    assert outcome["rq2_evidence"] is False
    assert outcome["denominator"] == {
        "population": "excluded",
        "retained": True,
        "replacement_allowed": False,
    }

    assert len(trajectory["attempts"]) == 1
    events = [
        json.loads(store.read_verified(ArtifactRef(**reference)))
        for reference in trajectory["attempts"][0]["attempt_event_refs"]
    ]
    hidden_event_index = next(
        index
        for index, event in enumerate(events)
        if event["stage"] == "development_hidden_evaluator"
    )
    assert [
        event["stage"] for event in events[hidden_event_index + 1 :]
    ] == ["attempt_lifecycle", "accounting_close"]
    assert not any(event["stage"] == "outer_repair" for event in events)
    cost_summary = json.loads(
        store.read_verified(
            ArtifactRef(**trajectory["attempts"][0]["cost_summary_ref"])
        )
    )
    assert cost_summary["axes"]["outer_repair_attempts"]["value"] == 0
    assert cost_summary["axes"]["hidden_evaluator_tool_calls"]["value"] == 1
    assert cost_summary["axes"]["hidden_infrastructure_retries"]["value"] == 0
    assert cost_summary["axes"]["hidden_evaluator_runtime"]["status"] == "measured"

    evaluator_store = ArtifactStore(
        run_dir / "development_hidden_authority" / "evaluator_store"
    )
    commitment_ref = evaluator_store.reference(
        f"private-commitments/{sample.sample_id}"
    )
    assert commitment_ref is not None
    retry_calls = []
    retry_authority = DevelopmentHiddenEvaluationAuthority(
        store,
        evaluator_store,
        lambda value: retry_calls.append(value) or {"outcome": "pass"},
    )
    with pytest.raises(OneShotViolation, match="already consumed"):
        retry_authority.evaluate_once(
            terminal_candidate_ref=terminal_ref,
            private_commitment_ref=commitment_ref,
            public_contract_sha256=hidden["public_contract_sha256"],
            public_profile_sha256=hidden["public_profile_sha256"],
            tool_environment_policy_sha256=hidden[
                "tool_environment_policy_sha256"
            ],
            decoding_seed=hidden["decoding_seed"],
        )
    assert retry_calls == []

    public_material = json.dumps(completion, sort_keys=True) + json.dumps(
        outcome, sort_keys=True
    ) + json.dumps(hidden, sort_keys=True)
    assert private_canary not in public_material
    for blob in (store.root / "blobs").rglob("*"):
        if blob.is_file():
            assert private_canary.encode("utf-8") not in blob.read_bytes()

    forged_outcome = json.loads(json.dumps(outcome))
    forged_outcome["development_vpp_l3"] = True
    forged_outcome["development_vpp_l3_reasons"] = []
    forged_without_id = {
        key: value
        for key, value in forged_outcome.items()
        if key != "outcome_id"
    }
    forged_outcome["outcome_id"] = "episode-outcome-" + hashlib.sha256(
        (
            json.dumps(
                forged_without_id,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    ).hexdigest()
    forged_outcome_ref = store.put_validated_json(
        "tamper/forged-hidden-pass-credit",
        forged_outcome,
        contract_key="development_episode_outcome",
    )
    with pytest.raises(EpisodeOutcomeError, match="does not rebuild"):
        read_verified_development_episode_outcome(store, forged_outcome_ref)

    reordered_trajectory = json.loads(json.dumps(trajectory))
    event_refs = reordered_trajectory["attempts"][0]["attempt_event_refs"]
    event_refs[0], event_refs[1] = event_refs[1], event_refs[0]
    reordered_without_id = {
        key: value
        for key, value in reordered_trajectory.items()
        if key != "trajectory_id"
    }
    reordered_trajectory["trajectory_id"] = "trajectory-v2-" + hashlib.sha256(
        json.dumps(
            reordered_without_id,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    reordered_ref = store.put_validated_json(
        "tamper/reordered-hidden-events",
        reordered_trajectory,
        contract_key="trajectory_v2",
    )
    with pytest.raises(EpisodeOutcomeError, match="trajectory does not rebuild"):
        reconcile_development_episode_outcome(
            store,
            public_evaluation_ref=ArtifactRef(
                **completion["development_public_evaluation_ref"]
            ),
            trajectory_ref=reordered_ref,
        )

    cross_episode_trajectory = json.loads(json.dumps(trajectory))
    cross_episode_trajectory["episode_id"] = "foreign-episode"
    cross_without_id = {
        key: value
        for key, value in cross_episode_trajectory.items()
        if key != "trajectory_id"
    }
    cross_episode_trajectory["trajectory_id"] = "trajectory-v2-" + hashlib.sha256(
        json.dumps(
            cross_without_id,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    cross_episode_ref = store.put_validated_json(
        "tamper/cross-episode-hidden-trajectory",
        cross_episode_trajectory,
        contract_key="trajectory_v2",
    )
    with pytest.raises(EpisodeOutcomeError, match="identity mismatch"):
        reconcile_development_episode_outcome(
            store,
            public_evaluation_ref=ArtifactRef(
                **completion["development_public_evaluation_ref"]
            ),
            trajectory_ref=cross_episode_ref,
        )

    hidden_blob = store.root / "blobs" / hidden_ref.sha256[:2] / hidden_ref.sha256
    hidden_blob.write_bytes(b"{}\n")
    with pytest.raises(ArtifactIntegrityError, match="artifact size mismatch"):
        read_verified_development_episode_outcome(store, outcome_ref)
