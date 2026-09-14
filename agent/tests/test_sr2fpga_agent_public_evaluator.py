from __future__ import annotations

import json
from pathlib import Path

import pytest

from sr2fpga_agent.artifact_store import (
    ArtifactIntegrityError,
    ArtifactStore,
    OneShotViolation,
)
from sr2fpga_agent.method_contract import method_policy_sha256
from sr2fpga_agent.models import GeneratedProject, ToolResult
from sr2fpga_agent.project_contract import build_project_envelope
from sr2fpga_agent.public_evaluator import (
    DevelopmentAttemptPublicEvaluationAuthority,
    DevelopmentPublicToolEvaluator,
    DevelopmentTerminalPublicEvaluationAuthority,
    PublicEvaluatorResult,
    read_verified_development_authoritative_attempt_public_outcome,
    read_verified_development_attempt_public_outcome,
    read_verified_development_public_outcome,
)


def _project() -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "counter8",
        "top": {
            "module": "top",
            "source": "rtl/top.v",
            "interface": {
                "ports": [{"name": "count", "direction": "output", "width": 8}]
            },
        },
        "sources": [
            {"path": "rtl/top.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [
            {
                "path": "sim/tb_top.v",
                "role": "candidate_testbench",
                "applicability": "advisory",
            }
        ],
        "build": {
            "toolchain_id": "open_source",
            "language_standard": "verilog-2005",
        },
    }
    return GeneratedProject(
        "counter8",
        {
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "rtl/top.v": (
                "module top(output [7:0] count); assign count = 8'd1; endmodule\n"
            ),
            "sim/tb_top.v": "// candidate-owned TEST_PASS must be ignored\n",
        },
    )


def _sealed_candidate(tmp_path: Path):
    store = ArtifactStore(tmp_path / "candidate-store")
    project = _project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-public-001",
        method_condition_id="M0",
        method_policy_sha256=method_policy_sha256("M0"),
        snapshot_id="snapshot-public-001",
        file_policies={
            path: {"owner": "model", "origin": "model_generated", "editable": False}
            for path in project.files
        },
    )
    envelope_ref = store.put_validated_json(
        "envelopes/public-candidate", envelope, contract_key="project_envelope"
    )
    creation = store.append_event("episode-public-001", "candidate_created", {})
    seal_ref = store.seal_candidate(
        "public-candidate-001",
        project=project,
        project_envelope_ref=envelope_ref,
        requirement_projection_sha256="a" * 64,
        creation_event_ref=creation,
    )
    return store, project, seal_ref


def _sealed_public_evaluation_candidate(tmp_path: Path):
    store = ArtifactStore(tmp_path / "attempt-candidate-store")
    project = _project()
    envelope = build_project_envelope(
        project,
        episode_id="episode-attempt-001",
        method_condition_id="M4",
        method_policy_sha256=method_policy_sha256("M4"),
        snapshot_id="snapshot-attempt-001",
        file_policies={
            path: {"owner": "model", "origin": "model_generated", "editable": False}
            for path in project.files
        },
    )
    envelope_ref = store.put_validated_json(
        "envelopes/attempt-candidate", envelope, contract_key="project_envelope"
    )
    creation = store.append_event(
        "episode-attempt-001",
        "candidate_created",
        {
            "candidate_id": "attempt-candidate-001",
            "attempt_id": "attempt-001",
            "method_condition_id": "M4",
        },
    )
    seal_ref = store.seal_public_evaluation_candidate(
        "attempt-candidate-001",
        attempt_id="attempt-001",
        project=project,
        project_envelope_ref=envelope_ref,
        requirement_projection_sha256="a" * 64,
        creation_event_ref=creation,
    )
    return store, project, seal_ref


def _result(*, raw_secret: str = "private-stdout-secret") -> PublicEvaluatorResult:
    return PublicEvaluatorResult(
        execution_status="completed",
        infrastructure_reason=None,
        stage_outcomes={
            "l0": {"status": "pass", "reason": None},
            "l1": {"status": "pass", "reason": None},
            "public_l2": {"status": "not_run", "reason": "needs_oracle"},
            "l3": {"status": "pass", "reason": None},
        },
        diagnostic_codes=("public_l2_needs_oracle",),
        raw_evaluator_record={"stdout": raw_secret, "workspace": "private/path"},
    )


def _evaluate(authority, seal_ref):
    return authority.evaluate_once(
        terminal_candidate_ref=seal_ref,
        public_contract_sha256="b" * 64,
        public_profile_sha256="c" * 64,
        tool_environment_policy_sha256="d" * 64,
    )


def test_public_authority_reads_sealed_candidate_and_sanitizes_raw_output(
    tmp_path: Path,
) -> None:
    candidate_store, mutable_project, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    seen = {}

    def evaluator(value, evaluation_id):
        seen["rtl"] = value.terminal_project.files["rtl/top.v"]
        seen["id"] = evaluation_id
        return _result()

    authority = DevelopmentTerminalPublicEvaluationAuthority(
        candidate_store, evaluator_store, evaluator
    )
    mutable_project.files["rtl/top.v"] = "module top; endmodule\n"
    outcome = _evaluate(authority, seal_ref)
    verified = read_verified_development_public_outcome(
        candidate_store, outcome.artifact_ref
    )

    assert "8'd1" in seen["rtl"]
    assert len(seen["id"]) == 64
    assert verified == outcome.payload
    assert verified["public_acceptance"] is False
    assert verified["repair_visible"] is False
    assert verified["pass_credit_authority"] is False
    assert verified["official_outcome"] is False
    assert verified["vpp_l3"] is None
    assert "private-stdout-secret" not in json.dumps(verified)
    assert "private/path" not in json.dumps(verified)
    private_blobs = b"\n".join(
        path.read_bytes()
        for path in (evaluator_store.root / "blobs").rglob("*")
        if path.is_file()
    )
    assert b"private-stdout-secret" in private_blobs


def test_public_authority_is_one_shot_and_rejects_shared_store(tmp_path: Path) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    calls = []
    authority = DevelopmentTerminalPublicEvaluationAuthority(
        candidate_store,
        evaluator_store,
        lambda value, evaluation_id: calls.append((value, evaluation_id)) or _result(),
    )

    _evaluate(authority, seal_ref)
    with pytest.raises(OneShotViolation, match="already consumed"):
        _evaluate(authority, seal_ref)
    assert len(calls) == 1
    with pytest.raises(ValueError, match="stores must be separate"):
        DevelopmentTerminalPublicEvaluationAuthority(
            candidate_store, candidate_store, lambda value, evaluation_id: _result()
        )


def test_attempt_public_authority_is_one_shot_and_has_no_terminal_or_pass_credit(
    tmp_path: Path,
) -> None:
    candidate_store, mutable_project, seal_ref = _sealed_public_evaluation_candidate(
        tmp_path
    )
    evaluator_store = ArtifactStore(tmp_path / "attempt-evaluator-store")
    seen = {}

    def evaluator(value, evaluation_id):
        seen["rtl"] = value.terminal_project.files["rtl/top.v"]
        seen["candidate_sha256"] = value.public_evaluation_candidate_sha256
        seen["evaluation_id"] = evaluation_id
        return _result()

    authority = DevelopmentAttemptPublicEvaluationAuthority(
        candidate_store, evaluator_store, evaluator
    )
    mutable_project.files["rtl/top.v"] = "module top; endmodule\n"
    outcome = authority.evaluate_once(
        public_evaluation_candidate_ref=seal_ref,
        public_contract_sha256="b" * 64,
        public_profile_sha256="c" * 64,
        tool_environment_policy_sha256="d" * 64,
    )
    verified = read_verified_development_attempt_public_outcome(
        candidate_store, outcome.artifact_ref
    )

    assert "8'd1" in seen["rtl"]
    assert seen["candidate_sha256"] == seal_ref.sha256
    assert len(seen["evaluation_id"]) == 64
    assert verified["evaluation_scope"] == "development_attempt_shadow_only"
    assert verified["attempt_id"] == "attempt-001"
    assert verified["repair_visible"] is False
    assert verified["pass_credit_authority"] is False
    assert verified["official_outcome"] is False
    assert verified["vpp_l3"] is None
    with pytest.raises(OneShotViolation, match="already consumed"):
        authority.evaluate_once(
            public_evaluation_candidate_ref=seal_ref,
            public_contract_sha256="b" * 64,
            public_profile_sha256="c" * 64,
            tool_environment_policy_sha256="d" * 64,
        )


def test_authoritative_attempt_public_outcome_is_repair_visible_but_not_official(
    tmp_path: Path,
) -> None:
    candidate_store, _, seal_ref = _sealed_public_evaluation_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "authoritative-evaluator-store")
    result = PublicEvaluatorResult(
        execution_status="completed",
        infrastructure_reason=None,
        stage_outcomes={
            "l0": {"status": "pass", "reason": None},
            "l1": {"status": "fail", "reason": "lint_failed"},
            "public_l2": {"status": "not_run", "reason": "upstream_stage_not_pass"},
            "l3": {"status": "not_run", "reason": "upstream_stage_not_pass"},
        },
        diagnostic_codes=("lint_failed",),
        raw_evaluator_record={"stdout": "private-public-log"},
    )
    authority = DevelopmentAttemptPublicEvaluationAuthority(
        candidate_store,
        evaluator_store,
        lambda value, evaluation_id: result,
        authoritative=True,
    )

    outcome = authority.evaluate_once(
        public_evaluation_candidate_ref=seal_ref,
        public_contract_sha256="b" * 64,
        public_profile_sha256="c" * 64,
        tool_environment_policy_sha256="d" * 64,
    )
    verified = read_verified_development_authoritative_attempt_public_outcome(
        candidate_store,
        outcome.artifact_ref,
    )

    assert authority.authoritative is True
    assert verified["complete_project"] is True
    assert verified["public_acceptance"] is False
    assert verified["repair_diagnosis"] == {
        "stage": "l1",
        "failure_type": "lint_failed",
        "diagnostic_codes": ["lint_failed"],
    }
    assert verified["repair_visible"] is True
    assert verified["terminal_selection_authority"] is True
    assert verified["pass_credit_authority"] is True
    assert verified["official_outcome"] is False
    assert "private-public-log" not in json.dumps(verified)


def test_authoritative_public_evaluator_preserves_unverified_l0_candidate(
    tmp_path: Path,
) -> None:
    candidate_store = ArtifactStore(tmp_path / "unverified-candidate-store")
    evaluator_store = ArtifactStore(tmp_path / "unverified-evaluator-store")
    project = GeneratedProject(
        "broken_project",
        {"rtl/top.v": "module top; endmodule\n"},
    )
    creation_ref = candidate_store.append_event(
        "episode-unverified",
        "candidate_created",
        {
            "candidate_id": "candidate-unverified",
            "attempt_id": "attempt-000",
            "method_condition_id": "M1",
        },
    )
    seal_ref = candidate_store.seal_unverified_public_evaluation_candidate(
        "candidate-unverified",
        episode_id="episode-unverified",
        attempt_id="attempt-000",
        method_condition_id="M1",
        project=project,
        project_envelope_reason="project_manifest_invalid",
        requirement_projection_sha256="a" * 64,
        creation_event_ref=creation_ref,
    )
    seen = {}

    def evaluator(value, evaluation_id):
        seen["project"] = value.terminal_project
        return PublicEvaluatorResult(
            execution_status="completed",
            infrastructure_reason=None,
            stage_outcomes={
                "l0": {"status": "fail", "reason": "public_l0_failed"},
                "l1": {"status": "not_run", "reason": "upstream_stage_not_pass"},
                "public_l2": {
                    "status": "not_run",
                    "reason": "upstream_stage_not_pass",
                },
                "l3": {"status": "not_run", "reason": "upstream_stage_not_pass"},
            },
            diagnostic_codes=("project_manifest_invalid",),
            raw_evaluator_record={},
        )

    authority = DevelopmentAttemptPublicEvaluationAuthority(
        candidate_store,
        evaluator_store,
        evaluator,
        authoritative=True,
    )

    outcome = authority.evaluate_once(
        public_evaluation_candidate_ref=seal_ref,
        public_contract_sha256="b" * 64,
        public_profile_sha256="a" * 64,
        tool_environment_policy_sha256="d" * 64,
    )

    assert seen["project"].files == project.files
    assert outcome.payload["complete_project"] is False
    assert outcome.payload["public_acceptance"] is False
    assert outcome.payload["repair_diagnosis"]["failure_type"] == (
        "project_envelope_unavailable"
    )


def test_public_authority_rejects_tampered_terminal_before_evaluator(
    tmp_path: Path,
) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    calls = []
    authority = DevelopmentTerminalPublicEvaluationAuthority(
        candidate_store,
        evaluator_store,
        lambda value, evaluation_id: calls.append((value, evaluation_id)) or _result(),
    )
    blob = candidate_store.root / "blobs" / seal_ref.sha256[:2] / seal_ref.sha256
    blob.write_bytes(b"tampered")

    with pytest.raises(ArtifactIntegrityError):
        _evaluate(authority, seal_ref)
    assert calls == []


def test_public_authority_preserves_evaluator_exception_as_not_run(
    tmp_path: Path,
) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")

    def fail(_value, _evaluation_id):
        raise RuntimeError("private evaluator path C:/secret")

    outcome = _evaluate(
        DevelopmentTerminalPublicEvaluationAuthority(
            candidate_store, evaluator_store, fail
        ),
        seal_ref,
    )

    assert outcome.payload["execution_status"] == "not_run"
    assert outcome.payload["infrastructure_reason"] == "evaluator_exception"
    assert set(outcome.payload["stage_outcomes"]) == {
        "l0",
        "l1",
        "public_l2",
        "l3",
    }
    assert all(
        value["status"] == "not_run"
        for value in outcome.payload["stage_outcomes"].values()
    )
    assert "C:/secret" not in json.dumps(outcome.payload)


def test_public_l2_pass_without_trusted_harness_commitment_fails_closed(
    tmp_path: Path,
) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    unsafe_pass = PublicEvaluatorResult(
        execution_status="completed",
        infrastructure_reason=None,
        stage_outcomes={
            "l0": {"status": "pass", "reason": None},
            "l1": {"status": "pass", "reason": None},
            "public_l2": {"status": "pass", "reason": None},
            "l3": {"status": "pass", "reason": None},
        },
        diagnostic_codes=(),
        raw_evaluator_record={"stdout": "unbound pass"},
    )

    outcome = _evaluate(
        DevelopmentTerminalPublicEvaluationAuthority(
            candidate_store,
            evaluator_store,
            lambda _value, _evaluation_id: unsafe_pass,
        ),
        seal_ref,
    )

    assert outcome.payload["execution_status"] == "not_run"
    assert outcome.payload["infrastructure_reason"] == "evaluator_exception"
    assert outcome.payload["public_acceptance"] is False


def test_public_authority_rejects_unsanitized_reason_and_content_id_tamper(
    tmp_path: Path,
) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    unsafe = PublicEvaluatorResult(
        execution_status="completed",
        infrastructure_reason=None,
        stage_outcomes={
            "l0": {"status": "fail", "reason": "C:/private path"},
            "l1": {"status": "not_run", "reason": "upstream_stage_not_pass"},
            "public_l2": {"status": "not_run", "reason": "upstream_stage_not_pass"},
            "l3": {"status": "not_run", "reason": "upstream_stage_not_pass"},
        },
        diagnostic_codes=("l0_failed",),
        raw_evaluator_record={"path": "C:/private path"},
    )
    outcome = _evaluate(
        DevelopmentTerminalPublicEvaluationAuthority(
            candidate_store,
            evaluator_store,
            lambda _value, _evaluation_id: unsafe,
        ),
        seal_ref,
    )
    assert outcome.payload["execution_status"] == "not_run"
    assert "C:/private" not in json.dumps(outcome.payload)

    tampered = json.loads(json.dumps(outcome.payload))
    tampered["diagnostic_codes"] = ["different_public_code"]
    tampered_ref = candidate_store.put_blob(
        "public-authority-outcomes/tampered",
        (json.dumps(tampered, sort_keys=True, separators=(",", ":")) + "\n").encode(),
        media_type="application/json",
    )
    with pytest.raises(ValueError, match="content-derived ID mismatch"):
        read_verified_development_public_outcome(candidate_store, tampered_ref)


class _PassingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path, str]] = []

    def run(self, command, cwd, stage, timeout_seconds=30):
        self.calls.append((list(command), Path(cwd), stage))
        return ToolResult(stage, list(command), "passed", 0, "PRIVATE LOG", "", 0.1)


def test_public_tool_evaluator_ignores_candidate_testbench_and_keeps_logs_private(
    tmp_path: Path,
) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    runner = _PassingRunner()
    tool_evaluator = DevelopmentPublicToolEvaluator(
        tmp_path / "evaluator-workspaces", command_runner=runner
    )
    outcome = _evaluate(
        DevelopmentTerminalPublicEvaluationAuthority(
            candidate_store, evaluator_store, tool_evaluator
        ),
        seal_ref,
    )

    assert [call[2] for call in runner.calls] == ["public_l1_lint", "public_l3_synth"]
    assert all(call[0][0] not in {"iverilog", "vvp"} for call in runner.calls)
    assert outcome.payload["stage_outcomes"] == {
        "l0": {"status": "pass", "reason": None},
        "l1": {"status": "pass", "reason": None},
        "public_l2": {"status": "not_run", "reason": "needs_oracle"},
        "l3": {"status": "pass", "reason": None},
    }
    assert "PRIVATE LOG" not in json.dumps(outcome.payload)
    workspaces = list((tmp_path / "evaluator-workspaces").iterdir())
    assert len(workspaces) == 1
    assert len(workspaces[0].name) == 16
    assert (workspaces[0] / "rtl" / "top.v").is_file()
    assert (workspaces[0] / "sim" / "tb_top.v").is_file()
