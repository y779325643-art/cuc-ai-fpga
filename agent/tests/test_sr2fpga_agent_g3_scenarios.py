"""Cross-boundary G3 fixtures using the real Runner and registered reducers."""

import json
from types import SimpleNamespace

import pytest

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.checkpoint_stop_outcome import read_verified_checkpoint_stop_outcome
from sr2fpga_agent.episode_outcome import read_verified_development_episode_outcome
from sr2fpga_agent.models import GeneratedProject, RepairResult, ToolResult
from sr2fpga_agent.paired_block import build_balanced_method_orders

from test_sr2fpga_agent_full_pack_smoke import _PassingCommandRunner, _run_fake_complete_full_pack


class _FailingInitialCommandRunner(_PassingCommandRunner):
    def run(self, command, cwd, stage, timeout_seconds=30):
        from pathlib import Path

        if stage in {"lint", "public_l1_lint"} and any(
            "g3_missing_signal" in path.read_text(encoding="utf-8")
            for path in (Path(cwd) / "rtl").rglob("*.v")
        ):
            return ToolResult(stage=stage, command=list(command), status="failed", exit_code=1,
                              stdout="", stderr="Signal g3_missing_signal is not declared",
                              duration_seconds=0.001)
        return super().run(command, cwd, stage, timeout_seconds)


class _M5Repairer:
    def __init__(self, budget):
        self.budget = budget

    def repair(self, project, diagnosis):
        assert diagnosis["failure_type"] == "lint_failed"
        assert diagnosis["diagnostic_codes"] == ["lint_failed"]
        call, started = self.budget.reserve("project_repair", "synthetic_g3", len(str(diagnosis)))
        files = dict(project.files)
        paths = [path for path, text in files.items() if path.endswith(".v") and "g3_missing_signal" in text]
        assert paths
        for path in paths:
            files[path] = files[path].replace("g3_missing_signal", "1'b0")
        self.budget.finish(call, "project_repair", "synthetic_g3", started,
                           output_chars=sum(map(len, files.values())))
        return RepairResult(GeneratedProject(project.project_name, files),
                            "\n".join(f"diff --git a/{path} b/{path}" for path in paths))


def test_m5_public_failure_repair_closes(monkeypatch):
    fixture = SimpleNamespace(
        command_runner=_FailingInitialCommandRunner(),
        build_repairer=lambda repairers, config, sample, model_budget=None: _M5Repairer(model_budget),
    )
    run = _run_fake_complete_full_pack(
        monkeypatch, method_order=build_balanced_method_orders(909991)[0],
        public_repair_fixture=fixture, assemble_companions=False,
    )
    event = next(item for item in run.completion_events if item["method_condition"] == "M5")
    outcome = read_verified_development_episode_outcome(
        run.store, ArtifactRef(**event["development_episode_outcome_ref"]),
    )
    assert outcome["repair"]["transitions"] == 1
    trajectory = json.loads(run.store.read_verified(ArtifactRef(**outcome["trajectory_ref"])))
    assert trajectory["failure_origin"] == "synthetic_injected"
    assert outcome["repair"]["diagnosis_count"] == 1
    assert outcome["repair"]["valid_patch_count"] == 1
    assert outcome["repair"]["rerun_count"] == 1
    assert outcome["repair"]["by_scope"]["system_his"]["transitions"] == 0
    assert outcome["official_outcome"] is False


def test_provider_failure_closes_without_candidate(monkeypatch):
    run = _run_fake_complete_full_pack(
        monkeypatch, method_order=build_balanced_method_orders(909991)[0],
        failed_stage="block_req2his", assemble_companions=False,
    )
    blocked = [item for item in run.run_events if item["event"] == "sample_blocked_by_shared_checkpoint"]
    assert {item["method_condition"] for item in blocked} == {"M3", "M4", "M5"}
    for event in blocked:
        ref = ArtifactRef(**event["development_checkpoint_stop_outcome_ref"])
        outcome = read_verified_checkpoint_stop_outcome(run.store, ref)
        assert outcome["execution_status"] == "not_run"
        assert outcome["semantic_status"] == "not_evaluated"
        assert outcome["terminal_candidate_ref"] is None
        assert outcome["denominator"] == {"retained": True, "replacement_allowed": False}
        assert "synthetic System-HIS checkpoint failure" not in json.dumps(outcome)
        forged = dict(outcome, semantic_instance_id="another-instance")
        forged_ref = run.store.put_validated_json(
            "g3/forged-stop/" + outcome["method_condition"], forged,
            contract_key="development_checkpoint_stop_outcome",
        )
        with pytest.raises(ValueError, match="replayed sources"):
            read_verified_checkpoint_stop_outcome(run.store, forged_ref)


def test_l3_infrastructure_closes_registered_outcome(monkeypatch):
    class MissingSynthesis(_PassingCommandRunner):
        def run(self, command, cwd, stage, timeout_seconds=30):
            if stage in {"synth", "public_l3_synth"}:
                return ToolResult(stage=stage, command=list(command), status="missing_tool",
                                  exit_code=None, stdout="", stderr="", duration_seconds=0.0,
                                  skip_reason="missing_tool")
            return super().run(command, cwd, stage, timeout_seconds)

    run = _run_fake_complete_full_pack(
        monkeypatch, method_order=build_balanced_method_orders(909991)[0],
        command_runner=MissingSynthesis(), assemble_companions=False,
    )
    for event in run.completion_events:
        outcome = read_verified_development_episode_outcome(
            run.store, ArtifactRef(**event["development_episode_outcome_ref"]),
        )
        assert outcome["stage_outcomes"]["l3"]["status"] == "not_run"
        assert outcome["repair"]["calls_attempted"] == 0
        assert outcome["development_vpp_l3_status"] == "not_evaluated"
        assert outcome["denominator"]["retained"] is True


def test_invalid_shared_output_is_design_failure_not_infrastructure(monkeypatch):
    run = _run_fake_complete_full_pack(
        monkeypatch, method_order=build_balanced_method_orders(909991)[0],
        failed_stage="block_req2his_invalid", assemble_companions=False,
    )
    blocked = [item for item in run.run_events if item["event"] == "sample_blocked_by_shared_checkpoint"]
    assert {item["method_condition"] for item in blocked} == {"M3", "M4", "M5"}
    for event in blocked:
        outcome = read_verified_checkpoint_stop_outcome(
            run.store, ArtifactRef(**event["development_checkpoint_stop_outcome_ref"]),
        )
        assert outcome["semantic_status"] == "design_failure"
        assert outcome["development_vpp_l3"] is False
        assert outcome["hidden_execution_status"] == "not_run"
        assert outcome["hidden_semantic_status"] is None


def test_public_l2_failure_closes_registered_outcome(monkeypatch):
    class FailingPublicL2(_PassingCommandRunner):
        def run(self, command, cwd, stage, timeout_seconds=30):
            if stage == "public_l2_sim":
                return ToolResult(stage=stage, command=list(command), status="failed",
                                  exit_code=1, stdout="", stderr="synthetic assertion failure",
                                  duration_seconds=0.001)
            return super().run(command, cwd, stage, timeout_seconds)

    run = _run_fake_complete_full_pack(
        monkeypatch, method_order=build_balanced_method_orders(909991)[0],
        command_runner=FailingPublicL2(), assemble_companions=False,
    )
    for event in run.completion_events:
        outcome = read_verified_development_episode_outcome(
            run.store, ArtifactRef(**event["development_episode_outcome_ref"]),
        )
        assert outcome["stage_outcomes"]["public_l2"]["status"] == "fail"
        assert outcome["development_vpp_l3"] is False
        assert outcome["official_outcome"] is False


def test_hidden_retry_cost_closes_without_new_model_or_repair_call(monkeypatch):
    from collections import Counter
    from sr2fpga_agent.evaluator_dispatch import DevelopmentHiddenEvaluationAuthority
    from sr2fpga_agent.hidden_execution_state import read_verified_hidden_execution_state
    from sr2fpga_agent.runner import DEVELOPMENT_HIDDEN_AUTHORITY_DIR

    calls = Counter()
    seeds = set()
    original = DevelopmentHiddenEvaluationAuthority.evaluate_once
    def with_frozen_retry(self, **kwargs):
        return original(self, **kwargs, max_infrastructure_retries=1)
    monkeypatch.setattr(DevelopmentHiddenEvaluationAuthority, "evaluate_once", with_frozen_retry)
    def evaluator(value):
        calls[value.terminal_candidate_sha256] += 1
        seeds.add(value.hidden_case_seed)
        if calls[value.terminal_candidate_sha256] == 1:
            raise TimeoutError("PRIVATE-RETRY-CANARY")
        return {"outcome": "pass"}
    run = _run_fake_complete_full_pack(
        monkeypatch, method_order=build_balanced_method_orders(909991)[0],
        hidden_evaluator=evaluator, assemble_companions=False,
    )
    assert len(seeds) == 1
    assert len(calls) == 6 and set(calls.values()) == {2}
    private_store = ArtifactStore(run.run_dir / DEVELOPMENT_HIDDEN_AUTHORITY_DIR / "evaluator_store")
    for event in run.completion_events:
        outcome = read_verified_development_episode_outcome(
            run.store, ArtifactRef(**event["development_episode_outcome_ref"]),
        )
        assert outcome["repair"]["calls_attempted"] == 0
        summaries = [json.loads(run.store.read_verified(ArtifactRef(**ref)))
                     for ref in outcome["cost_summary_refs"]]
        assert sum(item["axes"]["hidden_evaluator_tool_calls"]["value"] for item in summaries) == 1
        assert sum(item["axes"]["hidden_infrastructure_retries"]["value"] for item in summaries) == 1
        state = read_verified_hidden_execution_state(run.store, private_store,
                    ArtifactRef(**event["development_hidden_execution_state_ref"]))
        assert state["execution_count"] == 2
        assert state["semantic_commit_count"] == 1


def test_ambiguity_four_strata_replay_is_artifact_derived(tmp_path):
    from test_sr2fpga_agent_ambiguity_outcome import _phase_and_replay
    from sr2fpga_agent.ambiguity_outcome import AmbiguityAuditObservation, build_ambiguity_outcome

    manifest, witness, phase, events, replay = _phase_and_replay(tmp_path)
    store = ArtifactStore(tmp_path / "audit-evidence")
    for key, contract, payload in (
        ("manifest", "ambiguity_case_manifest", manifest),
        ("witness", "ambiguity_witness", witness),
        ("phase", "requirement_audit", phase),
        ("events", "ambiguity_audit_events", events),
        ("replay", "clarification_replay", replay),
    ):
        store.put_validated_json("ambiguity/" + key, payload, contract_key=contract)
    result = build_ambiguity_outcome(manifest, witness, [AmbiguityAuditObservation("g3", phase, events, replay)])
    ref = store.put_validated_json("ambiguity/outcome", result, contract_key="ambiguity_outcome")
    assert json.loads(store.read_verified(ref)) == result
    assert result["summary"]["case_observation_count"] == 4
    assert result["summary"]["cluster_primary_safety_failure"]["value"] == 0.0
    assert result["summary"]["one_replay_closure"]["value"] == 1.0
