from __future__ import annotations

import copy
import hashlib
import json
from types import SimpleNamespace

import pytest

from sr2fpga_agent.agent import DataGenerationAgent as RealDataGenerationAgent
from sr2fpga_agent.artifact_store import (
    ArtifactIntegrityError,
    ArtifactRef,
    ArtifactStore,
)
from sr2fpga_agent.contract_skeleton import build_contract_skeleton_project
from sr2fpga_agent.pre_candidate_outcome import (
    PreCandidateOutcomeError,
    read_verified_development_pre_candidate_stop_outcome,
    reconcile_development_pre_candidate_stop_outcome,
)
from sr2fpga_agent.frozen_context import (
    freeze_ready_requirement_context,
    frozen_project_name,
)
from sr2fpga_agent.his_correction_outcome import (
    HisCorrectionOutcomeError,
    read_verified_development_his_correction_outcome,
    reconcile_development_his_correction_outcome,
)
from sr2fpga_agent.models import PlatformProfile, ProjectRequest
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.requirement_boundary import evaluate_requirement_boundary
from sr2fpga_agent.runner import (
    RunnerConfig,
    SourceConnection,
    TaskConfig,
    planned_samples,
    run_batch,
)
from sr2fpga_agent.system_his_fidelity import build_frozen_requirement_trace
from sr2fpga_agent.tool_runner import ToolResult


class _StaticClient:
    def __init__(self, response: str, *, fail_if_called: bool = False) -> None:
        self.response = response
        self.fail_if_called = fail_if_called
        self.calls: list[list[dict[str, str]]] = []

    def stream_chat(self, messages):
        if self.fail_if_called:
            raise AssertionError("downstream project generation must not run")
        self.calls.append(messages)
        return self.response

    def chat(self, messages):
        return self.stream_chat(messages)


class _SequenceClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls: list[list[dict[str, str]]] = []

    def stream_chat(self, messages):
        self.calls.append(messages)
        return self.responses.pop(0)

    def chat(self, messages):
        return self.stream_chat(messages)


class _TwoStageGeneratorStub:
    def __init__(self, req2his_client, project_client) -> None:
        self.system_his_generator = SimpleNamespace(client=req2his_client)
        self.his_project_generator = SimpleNamespace(client=project_client)


class _FailIfCalledCommandRunner:
    def run(self, *args, **kwargs):
        raise AssertionError("public or EDA tool execution must not run")


class _PassingCommandRunner:
    def run(self, command, cwd, stage, timeout_seconds=30):
        stdout = "TEST_PASS\n" if stage == "candidate_sim_run" else ""
        if stage == "synth":
            stdout = "Number of cells: 1\n  SB_LUT4 1\n"
        return ToolResult(
            stage=stage,
            command=list(command),
            status="passed",
            exit_code=0,
            stdout=stdout,
            stderr="",
            duration_seconds=0.001,
        )


def test_real_runner_m5_h_correction_uses_distinct_budget_stage(
    tmp_path, monkeypatch
) -> None:
    source = SourceConnection(
        name="his",
        kind="openai_compat",
        model="fake-model",
        generation_mode="two_stage",
        system_his_schema_version="system-his-v1.2",
    )
    config = RunnerConfig(
        dataset_root=tmp_path / "datasets",
        export_root=tmp_path / "exports",
        run_root=tmp_path / "runs",
        provider="his",
        repair_provider="his",
        max_attempts=2,
        refresh_exports=False,
        sources={"his": source},
        line_b_targets={"max_samples": 1},
        tasks=[
            TaskConfig(
                source="his",
                task_type="counter",
                widths=[8],
                count=1,
                requirement=(
                    "Build an 8-bit synchronous counter with active-low reset."
                ),
                method_condition="M5",
                analysis_population="excluded",
                semantic_instance_id="semantic-counter-m5-budget-001",
                decoding_seed=17,
                paired_block_id="pair-counter-m5-budget-001-seed-17",
                failure_origin="synthetic_injected",
                measurement_point="b_tool_in_loop_repair",
            )
        ],
    )
    sample = planned_samples(config)[0]
    req2his_client = _SequenceClient(
        [
            _system_his_response_for_failed_stage(config, sample, "h0"),
            _system_his_response_for_failed_stage(config, sample, None),
        ]
    )
    project_client = _StaticClient(json.dumps({"behavior_files": {}}))

    def build_generator(_connection, **kwargs):
        budget = kwargs["model_budget"]
        return _TwoStageGeneratorStub(
            budget.client(req2his_client, "req2his"),
            budget.client(project_client, "his2project"),
        )

    def build_agent(dataset_root, **kwargs):
        return RealDataGenerationAgent(
            dataset_root,
            command_runner=_PassingCommandRunner(),
            **kwargs,
        )

    monkeypatch.setattr(
        "sr2fpga_agent.runner.build_project_generator_for_connection",
        build_generator,
    )
    monkeypatch.setattr(
        "sr2fpga_agent.runner.build_repairer_for_connection",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr("sr2fpga_agent.runner.DataGenerationAgent", build_agent)
    monkeypatch.setattr(
        "sr2fpga_agent.runner._development_hidden_evaluator",
        lambda _value: {"outcome": "pass"},
    )

    with pytest.raises(
        RuntimeError,
        match="missing artifact-derived acceptance lineage",
    ):
        run_batch(config, run_id="m5-h0-correction-stage", resume=False)
    events = [
        json.loads(line)
        for line in (
            config.run_root / "m5-h0-correction-stage" / "events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]

    assert [
        event["stage"]
        for event in events
        if event.get("event") == "model_call_finished"
    ] == ["req2his", "system_his_repair", "his2project"]


@pytest.mark.parametrize("failed_stage", ("h0", "h1", "h2", "h3"))
def test_real_runner_m5_h_correction_acceptance_is_artifact_derived_and_fail_closed(
    tmp_path, monkeypatch, failed_stage: str
) -> None:
    source = SourceConnection(
        name="his",
        kind="openai_compat",
        model="fake-model",
        generation_mode="two_stage",
        system_his_schema_version="system-his-v1.2",
    )
    harness_root = tmp_path / "trusted-public-l2"
    harness_root.mkdir()
    trusted_canary = f"trusted-evaluator-{failed_stage}-canary"
    trusted_tb = (
        f"// {trusted_canary}\n"
        "module trusted_tb; initial begin #1; $finish; end endmodule\n"
    )
    trusted_tb_path = harness_root / "trusted_tb.v"
    trusted_tb_path.write_text(trusted_tb, encoding="utf-8", newline="\n")
    harness_manifest_path = harness_root / "manifest.json"
    harness_manifest_path.write_text(
        json.dumps(
            {
                "contract_version": "development-public-l2-harness-v1",
                "harness_id": f"m5-{failed_stage}-public-l2-v1",
                "evaluation_scope": "development_excluded_public_l2",
                "testbench_top": "trusted_tb",
                "language_standard": "verilog-2005",
                "files": [
                    {
                        "path": "trusted_tb.v",
                        "sha256": hashlib.sha256(trusted_tb.encode()).hexdigest(),
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
    config = RunnerConfig(
        dataset_root=tmp_path / "datasets",
        export_root=tmp_path / "exports",
        run_root=tmp_path / "runs",
        provider="his",
        repair_provider="his",
        max_attempts=2,
        refresh_exports=False,
        sources={"his": source},
        line_b_targets={"max_samples": 1},
        tasks=[
            TaskConfig(
                source="his",
                task_type="fir_filter",
                widths=[8],
                count=1,
                requirement=(
                    "Build an 8-bit signed integer streaming FIR filter with active-low reset."
                ),
                method_condition="M5",
                analysis_population="excluded",
                semantic_instance_id=f"semantic-fir-m5-{failed_stage}-001",
                decoding_seed=17,
                paired_block_id=f"pair-fir-m5-{failed_stage}-001-seed-17",
                failure_origin="synthetic_injected",
                measurement_point="b_tool_in_loop_repair",
                public_l2_harness_manifest=str(harness_manifest_path),
            )
        ],
    )
    sample = planned_samples(config)[0]
    initial_response = _system_his_response_for_failed_stage(
        config, sample, failed_stage
    )
    corrected_response = _system_his_response_for_failed_stage(config, sample, None)
    req2his_client = _SequenceClient([initial_response, corrected_response])
    platform = PlatformProfile(
        name=config.platform,
        vendor="generic",
        toolchain="open_source",
    )
    request = ProjectRequest(
        task_type=sample.task_type,
        width=sample.width,
        project_name=sample.project_name,
        description=sample.requirement,
    )
    context = freeze_ready_requirement_context(
        evaluate_requirement_boundary(request, platform), platform
    )
    skeleton = build_contract_skeleton_project(
        ProjectRequest(
            task_type=sample.task_type,
            width=sample.width,
            project_name=frozen_project_name(context),
            description=sample.requirement,
        ),
        platform,
        json.loads(corrected_response),
    )
    project_client = _StaticClient(
        json.dumps(
            {
                "behavior_files": {
                    path: "// deterministic fake-provider behavior body"
                    for path, content in skeleton.files.items()
                    if "BEHAVIOR_HOLE" in content
                }
            }
        )
    )

    def build_generator(_connection, **kwargs):
        budget = kwargs["model_budget"]
        return _TwoStageGeneratorStub(
            budget.client(req2his_client, "req2his"),
            budget.client(project_client, "his2project"),
        )

    monkeypatch.setattr(
        "sr2fpga_agent.runner.build_project_generator_for_connection",
        build_generator,
    )
    monkeypatch.setattr(
        "sr2fpga_agent.runner.build_repairer_for_connection",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "sr2fpga_agent.runner.DataGenerationAgent",
        lambda dataset_root, **kwargs: RealDataGenerationAgent(
            dataset_root, command_runner=_PassingCommandRunner(), **kwargs
        ),
    )
    private_canary = f"private-hidden-{failed_stage}-canary"
    monkeypatch.setattr(
        "sr2fpga_agent.runner._development_hidden_evaluator",
        lambda _value: {"outcome": "pass", "private_case": private_canary},
    )

    summary = run_batch(config, run_id=f"m5-{failed_stage}-correction", resume=False)
    run_dir = config.run_root / f"m5-{failed_stage}-correction"
    events = [
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    completion = next(event for event in events if event.get("event") == "sample_completed")
    store = ArtifactStore(run_dir / "method_artifacts")
    outcome_ref = ArtifactRef(**completion["development_his_correction_outcome_ref"])
    outcome = read_verified_development_his_correction_outcome(store, outcome_ref)

    assert summary["total_completed"] == 1
    assert outcome["h_validation"]["initial_failed_stage"] == failed_stage
    assert outcome["h_validation"]["corrected_stage_statuses"] == {
        "h0": "pass", "h1": "pass", "h2": "pass", "h3": "pass"
    }
    assert outcome["initial_his_ref"] != outcome["corrected_his_ref"]
    assert outcome["correction_lineage"]["correction_count"] == 1
    assert outcome["cost"]["logical_model_stages"] == {
        "req2his": 1, "system_his_repair": 1, "his2project": 1
    }
    assert outcome["cost"]["project_repairs"] == 0
    assert outcome["official_outcome"] is False
    assert outcome["rq1_evidence"] is False
    assert outcome["rq2_evidence"] is False
    assert outcome["g3_accepted"] is False
    assert outcome["g4b_authorized"] is False
    serialized_prompts = json.dumps(
        req2his_client.calls + project_client.calls, sort_keys=True
    )
    assert private_canary not in serialized_prompts
    assert trusted_canary not in serialized_prompts
    assert private_canary not in json.dumps(outcome, sort_keys=True)
    assert private_canary not in store.read_verified(
        ArtifactRef(**outcome["candidate_artifact_ref"])
    ).decode()
    assert private_canary not in json.dumps(
        [
            json.loads(store.read_verified(ArtifactRef(**item)))
            for item in outcome["method_event_refs"]
        ],
        sort_keys=True,
    )

    if failed_stage == "h2":
        initial_ref = ArtifactRef(**outcome["initial_his_ref"])
        initial_blob = (
            store.root / "blobs" / initial_ref.sha256[:2] / initial_ref.sha256
        )
        initial_blob.write_bytes(b"{\"tampered\":true}\n")
        with pytest.raises(ArtifactIntegrityError):
            read_verified_development_his_correction_outcome(store, outcome_ref)

    if failed_stage == "h3":
        common = {
            "episode_pack_ref": ArtifactRef(**outcome["episode_pack_ref"]),
            "initial_his_ref": ArtifactRef(**outcome["initial_his_ref"]),
            "corrected_his_ref": ArtifactRef(**outcome["corrected_his_ref"]),
            "method_event_refs": tuple(
                ArtifactRef(**item) for item in outcome["method_event_refs"]
            ),
            "candidate_artifact_ref": ArtifactRef(
                **outcome["candidate_artifact_ref"]
            ),
            "trajectory_ref": ArtifactRef(**outcome["trajectory_ref"]),
            "development_episode_outcome_ref": ArtifactRef(
                **outcome["development_episode_outcome_ref"]
            ),
            "platform": PlatformProfile(**outcome["platform_profile"]),
        }
        reordered = dict(common)
        reordered["method_event_refs"] = tuple(reversed(common["method_event_refs"]))
        with pytest.raises(HisCorrectionOutcomeError, match="sequence mismatch"):
            reconcile_development_his_correction_outcome(store, **reordered)
        missing = dict(common)
        missing["method_event_refs"] = common["method_event_refs"][:-1]
        with pytest.raises(HisCorrectionOutcomeError, match="eight distinct"):
            reconcile_development_his_correction_outcome(store, **missing)
        swapped = dict(common)
        swapped["initial_his_ref"] = common["corrected_his_ref"]
        swapped["corrected_his_ref"] = common["initial_his_ref"]
        with pytest.raises(HisCorrectionOutcomeError):
            reconcile_development_his_correction_outcome(store, **swapped)
        drifted = dict(common)
        drifted["platform"] = PlatformProfile(
            **{**outcome["platform_profile"], "name": "drifted-platform"}
        )
        with pytest.raises(HisCorrectionOutcomeError, match="platform profile"):
            reconcile_development_his_correction_outcome(store, **drifted)
        extra_event = store.append_event(
            sample.sample_id,
            "episode_state_transition",
            {
                "state": "his_correction_requested",
                "method_condition_id": "M5",
                "failed_h_stage": "h3",
            },
        )
        inserted = dict(common)
        inserted["method_event_refs"] = (
            *common["method_event_refs"][:5],
            extra_event,
            *common["method_event_refs"][5:],
        )
        with pytest.raises(HisCorrectionOutcomeError, match="eight distinct"):
            reconcile_development_his_correction_outcome(store, **inserted)
        wrong_candidate = dict(common)
        wrong_candidate["candidate_artifact_ref"] = common["initial_his_ref"]
        with pytest.raises(HisCorrectionOutcomeError, match="candidate"):
            reconcile_development_his_correction_outcome(store, **wrong_candidate)
        wrong_trajectory = dict(common)
        wrong_trajectory["trajectory_ref"] = common["candidate_artifact_ref"]
        with pytest.raises(HisCorrectionOutcomeError, match="trajectory mismatch"):
            reconcile_development_his_correction_outcome(store, **wrong_trajectory)
        forged_report = copy.deepcopy(outcome)
        forged_report["h_validation"]["corrected_report_sha256"] = "f" * 64
        without_id = {
            key: value for key, value in forged_report.items() if key != "outcome_id"
        }
        forged_report["outcome_id"] = "his-correction-outcome-" + hashlib.sha256(
            _canonical_json(without_id)
        ).hexdigest()
        forged_report_ref = store.put_validated_json(
            "tampered/his-correction-report",
            forged_report,
            contract_key="development_his_correction_outcome",
        )
        with pytest.raises(HisCorrectionOutcomeError, match="does not rebuild"):
            read_verified_development_his_correction_outcome(
                store, forged_report_ref
            )
        with monkeypatch.context() as capability_drift:
            capability_drift.setattr(
                "sr2fpga_agent.his_correction_outcome.capability_profile_sha256",
                lambda _backend: "0" * 64,
            )
            with pytest.raises(
                HisCorrectionOutcomeError, match="capability profile"
            ):
                read_verified_development_his_correction_outcome(store, outcome_ref)
        trajectory = json.loads(
            store.read_verified(ArtifactRef(**outcome["trajectory_ref"]))
        )
        cost_event_ref = ArtifactRef(
            **trajectory["attempts"][0]["attempt_event_refs"][0]
        )
        cost_event_blob = (
            store.root
            / "blobs"
            / cost_event_ref.sha256[:2]
            / cost_event_ref.sha256
        )
        cost_event = json.loads(cost_event_blob.read_bytes())
        cost_event["stage"] = "forged_model_stage"
        cost_event_blob.write_bytes(_canonical_json(cost_event))
        with pytest.raises(ArtifactIntegrityError):
            read_verified_development_his_correction_outcome(store, outcome_ref)


@pytest.mark.parametrize("failed_stage", ("h0", "h1", "h2", "h3"))
def test_real_runner_m4_h_stage_stop_is_rebuilt_and_tamper_closed(
    tmp_path, monkeypatch, failed_stage: str
) -> None:
    source = SourceConnection(
        name="his",
        kind="openai_compat",
        model="fake-model",
        generation_mode="two_stage",
        system_his_schema_version="system-his-v1.2",
    )
    config = RunnerConfig(
        dataset_root=tmp_path / "datasets",
        export_root=tmp_path / "exports",
        run_root=tmp_path / "runs",
        provider="his",
        repair_provider="none",
        max_attempts=3,
        refresh_exports=False,
        sources={"his": source},
        line_b_targets={"max_samples": 1},
        tasks=[
            TaskConfig(
                source="his",
                task_type="counter",
                widths=[8],
                count=1,
                requirement=(
                    "Build an 8-bit synchronous counter with active-low reset."
                ),
                method_condition="M4",
                analysis_population="excluded",
                semantic_instance_id=f"semantic-counter-m4-{failed_stage}-001",
                decoding_seed=17,
                paired_block_id=f"pair-counter-m4-{failed_stage}-001-seed-17",
                failure_origin="synthetic_injected",
                measurement_point="b_tool_in_loop_repair",
            )
        ],
    )
    sample = planned_samples(config)[0]
    req2his_client = _StaticClient(
        _system_his_response_for_failed_stage(config, sample, failed_stage)
    )
    project_client = _StaticClient("", fail_if_called=True)
    generators_remaining = [True]

    def build_generator(_connection, **_kwargs):
        generators_remaining.pop(0)
        budget = _kwargs["model_budget"]
        return _TwoStageGeneratorStub(
            budget.client(req2his_client, "req2his"),
            budget.client(project_client, "his2project"),
        )

    def build_agent(dataset_root, **kwargs):
        return RealDataGenerationAgent(
            dataset_root,
            command_runner=_FailIfCalledCommandRunner(),
            **kwargs,
        )

    def hidden_must_not_run(_value):
        raise AssertionError("hidden evaluator must not run")

    monkeypatch.setattr(
        "sr2fpga_agent.runner.build_project_generator_for_connection",
        build_generator,
    )
    monkeypatch.setattr("sr2fpga_agent.runner.DataGenerationAgent", build_agent)
    monkeypatch.setattr(
        "sr2fpga_agent.runner._development_hidden_evaluator",
        hidden_must_not_run,
    )

    summary = run_batch(config, run_id=f"m4-{failed_stage}-stop", resume=False)
    run_dir = config.run_root / f"m4-{failed_stage}-stop"
    store = ArtifactStore(run_dir / "method_artifacts")
    completion = next(
        json.loads(line)
        for line in (run_dir / "events.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if json.loads(line).get("event") == "sample_completed"
    )
    labels = json.loads(
        (config.dataset_root / sample.sample_id / "eval" / "labels.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["total_completed"] == 1
    assert generators_remaining == []
    assert len(req2his_client.calls) == 1
    assert project_client.calls == []
    assert completion["pass_level"] == "GEN_FAIL"
    assert completion["method_artifacts"]["candidate_artifact_ref"] is None
    assert completion["method_artifacts"]["state_trace"] == [
        "method_prepared",
        "planning_artifact_emitted",
        "h_validated",
        "no_complete_candidate",
    ]
    assert completion["method_artifacts"]["his_corrections_used"] == 0
    assert completion["method_artifacts"]["failure"]["stage"] == failed_stage
    assert labels["failure_type"] == "his_validation_failed"
    expected_statuses = _expected_h_statuses(failed_stage)
    assert [labels[f"h{index}_status"] for index in range(4)] == list(
        expected_statuses.values()
    )
    for forbidden in (
        "development_public_evaluation_ref",
        "development_terminal_selection_ref",
        "development_terminal_public_outcome_ref",
        "development_hidden_outcome_ref",
        "development_hidden_conformance_outcome_ref",
        "development_episode_outcome_ref",
    ):
        assert forbidden not in completion

    outcome_ref = ArtifactRef(
        **completion["development_pre_candidate_stop_outcome_ref"]
    )
    outcome = read_verified_development_pre_candidate_stop_outcome(
        store, outcome_ref
    )
    assert outcome["contract_version"] == (
        "development-pre-candidate-stop-outcome-v2"
    )
    assert outcome["method_condition"] == "M4"
    assert outcome["failure"]["stage"] == failed_stage
    assert outcome["h_validation"]["failed_stage"] == failed_stage
    assert outcome["h_validation"]["stage_statuses"] == expected_statuses
    for stage, status in expected_statuses.items():
        assert outcome["stage_outcomes"][stage]["status"] == status
    assert outcome["stage_outcomes"]["project_emission"] == {
        "status": "not_run",
        "reason": f"upstream_{failed_stage}_failed",
    }
    assert outcome["repair"]["calls_attempted"] == 0
    assert outcome["missingness"]["classification"] == "design_outcome"
    assert outcome["missingness"]["reason"] == (
        f"{failed_stage}_failed_before_complete_candidate"
    )
    assert outcome["development_vpp_l3"] is False
    assert outcome["development_vpp_l3_reasons"] == [
        f"{failed_stage}_failed",
        "no_complete_candidate",
    ]
    assert outcome["vpp_l3"] is None
    assert outcome["official_outcome"] is False
    assert outcome["g3_accepted"] is False
    assert outcome["g4b_authorized"] is False
    trajectory_ref = ArtifactRef(**outcome["trajectory_ref"])
    trajectory = json.loads(store.read_verified(trajectory_ref))
    attempt_inputs = set(trajectory["attempts"][0]["input_artifact_hashes"])
    assert outcome["episode_pack_ref"]["sha256"] in attempt_inputs
    assert outcome["public_projection_sha256"] in attempt_inputs

    forged = copy.deepcopy(outcome)
    forged["method_event_refs"][2], forged["method_event_refs"][3] = (
        forged["method_event_refs"][3],
        forged["method_event_refs"][2],
    )
    without_id = {key: value for key, value in forged.items() if key != "outcome_id"}
    forged["outcome_id"] = "pre-candidate-stop-outcome-" + hashlib.sha256(
        _canonical_json(without_id)
    ).hexdigest()
    forged_ref = store.put_validated_json(
        "tampered/pre-candidate-stop-outcome",
        forged,
        contract_key="development_pre_candidate_stop_outcome_v2",
    )
    with pytest.raises(PreCandidateOutcomeError, match="order mismatch"):
        read_verified_development_pre_candidate_stop_outcome(store, forged_ref)

    forged_digest = copy.deepcopy(outcome)
    forged_digest["h_validation"]["report_sha256"] = "f" * 64
    without_id = {
        key: value for key, value in forged_digest.items() if key != "outcome_id"
    }
    forged_digest["outcome_id"] = "pre-candidate-stop-outcome-" + hashlib.sha256(
        _canonical_json(without_id)
    ).hexdigest()
    forged_digest_ref = store.put_validated_json(
        "tampered/pre-candidate-stop-outcome-report-digest",
        forged_digest,
        contract_key="development_pre_candidate_stop_outcome_v2",
    )
    with pytest.raises(PreCandidateOutcomeError, match="does not rebuild"):
        read_verified_development_pre_candidate_stop_outcome(
            store, forged_digest_ref
        )

    forged_platform = copy.deepcopy(outcome)
    forged_platform["platform_profile"]["name"] = "other-platform"
    without_id = {
        key: value for key, value in forged_platform.items() if key != "outcome_id"
    }
    forged_platform["outcome_id"] = "pre-candidate-stop-outcome-" + hashlib.sha256(
        _canonical_json(without_id)
    ).hexdigest()
    forged_platform_ref = store.put_validated_json(
        "tampered/pre-candidate-stop-outcome-platform",
        forged_platform,
        contract_key="development_pre_candidate_stop_outcome_v2",
    )
    with pytest.raises(PreCandidateOutcomeError, match="platform profile"):
        read_verified_development_pre_candidate_stop_outcome(
            store, forged_platform_ref
        )

    with monkeypatch.context() as capability_drift:
        capability_drift.setattr(
            "sr2fpga_agent.pre_candidate_outcome.capability_profile_sha256",
            lambda _backend: "0" * 64,
        )
        with pytest.raises(PreCandidateOutcomeError, match="capability profile"):
            read_verified_development_pre_candidate_stop_outcome(
                store, outcome_ref
            )

    if failed_stage == "h3":
        foreign_trajectory = copy.deepcopy(trajectory)
        foreign_trajectory["episode_id"] = "foreign-episode"
        without_trajectory_id = {
            key: value
            for key, value in foreign_trajectory.items()
            if key != "trajectory_id"
        }
        foreign_trajectory["trajectory_id"] = "trajectory-v2-" + hashlib.sha256(
            _canonical_json(without_trajectory_id)
        ).hexdigest()
        foreign_trajectory_ref = store.put_validated_json(
            "tampered/foreign-episode-trajectory",
            foreign_trajectory,
            contract_key="trajectory_v2",
        )
        forged_episode = copy.deepcopy(outcome)
        forged_episode["trajectory_ref"] = foreign_trajectory_ref.to_dict()
        without_id = {
            key: value for key, value in forged_episode.items() if key != "outcome_id"
        }
        forged_episode["outcome_id"] = (
            "pre-candidate-stop-outcome-"
            + hashlib.sha256(_canonical_json(without_id)).hexdigest()
        )
        forged_episode_ref = store.put_validated_json(
            "tampered/pre-candidate-stop-outcome-foreign-episode",
            forged_episode,
            contract_key="development_pre_candidate_stop_outcome_v2",
        )
        with pytest.raises(PreCandidateOutcomeError, match="trajectory identity"):
            read_verified_development_pre_candidate_stop_outcome(
                store, forged_episode_ref
            )

    if failed_stage == "h0":
        legacy_outcome, legacy_ref = (
            reconcile_development_pre_candidate_stop_outcome(
                store,
                episode_pack_ref=ArtifactRef(**outcome["episode_pack_ref"]),
                planning_artifact_ref=ArtifactRef(
                    **outcome["planning_artifact_ref"]
                ),
                method_event_refs=(
                    ArtifactRef(**payload)
                    for payload in outcome["method_event_refs"]
                ),
                trajectory_ref=trajectory_ref,
            )
        )
        assert legacy_outcome["contract_version"] == (
            "development-pre-candidate-stop-outcome-v1"
        )
        assert read_verified_development_pre_candidate_stop_outcome(
            store, legacy_ref
        ) == legacy_outcome

    store.append_event(
        sample.sample_id,
        "episode_state_transition",
        {"state": "unexpected_post_stop_transition"},
    )
    with pytest.raises(PreCandidateOutcomeError, match="complete episode stream"):
        read_verified_development_pre_candidate_stop_outcome(store, outcome_ref)

    planning_ref = ArtifactRef(**outcome["planning_artifact_ref"])
    planning_blob = (
        store.root / "blobs" / planning_ref.sha256[:2] / planning_ref.sha256
    )
    planning_blob.write_bytes(b"{\"tampered\":true}\n")
    with pytest.raises(ArtifactIntegrityError):
        read_verified_development_pre_candidate_stop_outcome(store, outcome_ref)


def _system_his_response_for_failed_stage(
    config: RunnerConfig,
    sample,
    failed_stage: str | None,
) -> str:
    if failed_stage == "h0":
        return "{}"
    platform = PlatformProfile(
        name=config.platform,
        vendor="generic",
        toolchain="open_source",
    )
    request = ProjectRequest(
        task_type=sample.task_type,
        width=sample.width,
        project_name=sample.project_name,
        description=sample.requirement,
    )
    context = freeze_ready_requirement_context(
        evaluate_requirement_boundary(request, platform), platform
    )
    generated = ProjectGenerator().generate(
        ProjectRequest(
            task_type=sample.task_type,
            width=sample.width,
            project_name=frozen_project_name(context),
            description=sample.requirement,
        ),
        platform,
    )
    payload = json.loads(generated.files["system_his.json"])
    payload["intent"]["requirement_trace"] = build_frozen_requirement_trace(
        context, payload
    )
    if failed_stage == "h1":
        payload["artifacts"]["top_module"] = "wrong_top"
    elif failed_stage == "h2":
        payload["components"][0]["semantic_kind"] = (
            "unsupported_future_component"
        )
    elif failed_stage == "h3":
        payload["intent"]["requirement_trace"]["requirement_id"] = "wrong"
    elif failed_stage is not None:
        raise AssertionError(f"unsupported test H stage: {failed_stage}")
    return json.dumps(payload)


def _expected_h_statuses(failed_stage: str) -> dict[str, str]:
    stages = ("h0", "h1", "h2", "h3")
    failure_index = stages.index(failed_stage)
    return {
        stage: (
            "pass"
            if index < failure_index
            else "fail"
            if index == failure_index
            else "not_run"
        )
        for index, stage in enumerate(stages)
    }


def _canonical_json(payload) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
