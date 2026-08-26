from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.method_contract import method_policy_sha256
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.project_contract import build_project_envelope
from sr2fpga_agent.public_evaluator import (
    DevelopmentAttemptPublicEvaluationAuthority,
    PublicEvaluatorResult,
)
from sr2fpga_agent.terminal_selection import (
    TerminalSelectionCandidate,
    TerminalSelectionError,
    read_verified_development_terminal_selection,
    select_development_terminal_candidate,
)


TEST_ROOT = Path(__file__).resolve().parent / ".runner_tmp"


def _test_root() -> Path:
    path = TEST_ROOT / f"terminal-selection-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _project(index: int) -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "counter8",
        "top": {
            "module": "top",
            "source": "rtl/top.v",
            "interface": {"ports": []},
        },
        "sources": [
            {"path": "rtl/top.v", "role": "rtl_source", "language": "verilog"}
        ],
        "artifacts": [],
        "build": {
            "toolchain_id": "open_source",
            "language_standard": "verilog-2005",
        },
    }
    return GeneratedProject(
        "counter8",
        {
            "manifest.json": json.dumps(manifest) + "\n",
            "rtl/top.v": f"module top; localparam INDEX = {index}; endmodule\n",
        },
    )


def _seal_attempt(store: ArtifactStore, index: int):
    project = _project(index)
    attempt_id = f"attempt-{index:03d}"
    candidate_id = f"episode-selection-attempt-{index:03d}"
    envelope = build_project_envelope(
        project,
        episode_id="episode-selection",
        method_condition_id="M1",
        method_policy_sha256=method_policy_sha256("M1"),
        snapshot_id=f"snapshot-{index:03d}",
        file_policies={
            path: {"owner": "model", "origin": "model_generated", "editable": False}
            for path in project.files
        },
    )
    envelope_ref = store.put_validated_json(
        f"envelopes/{candidate_id}",
        envelope,
        contract_key="project_envelope",
    )
    creation_ref = store.append_event(
        "episode-selection",
        "candidate_created",
        {
            "candidate_id": candidate_id,
            "attempt_id": attempt_id,
            "method_condition_id": "M1",
        },
    )
    return store.seal_public_evaluation_candidate(
        candidate_id,
        attempt_id=attempt_id,
        project=project,
        project_envelope_ref=envelope_ref,
        requirement_projection_sha256="a" * 64,
        creation_event_ref=creation_ref,
    )


def _result(accepted: bool) -> PublicEvaluatorResult:
    public_l2 = (
        {"status": "pass", "reason": None}
        if accepted
        else {"status": "not_run", "reason": "needs_oracle"}
    )
    return PublicEvaluatorResult(
        execution_status="completed",
        infrastructure_reason=None,
        stage_outcomes={
            "l0": {"status": "pass", "reason": None},
            "l1": {"status": "pass", "reason": None},
            "public_l2": public_l2,
            "l3": {"status": "pass", "reason": None},
        },
        diagnostic_codes=() if accepted else ("public_l2_needs_oracle",),
        raw_evaluator_record={"private": "not-public"},
        public_l2_harness=(
            {
                "status": "available",
                "harness_id": "trusted-counter8-v1",
                "manifest_sha256": "e" * 64,
                "bundle_sha256": "f" * 64,
                "reason": None,
            }
            if accepted
            else None
        ),
    )


def _evaluated_candidates(
    root: Path,
    accepted: tuple[bool, ...],
) -> tuple[ArtifactStore, list[TerminalSelectionCandidate]]:
    store = ArtifactStore(root / "candidate-store")
    evaluator_store = ArtifactStore(root / "evaluator-store")
    results = iter(_result(value) for value in accepted)
    authority = DevelopmentAttemptPublicEvaluationAuthority(
        store,
        evaluator_store,
        lambda value, evaluation_id: next(results),
        authoritative=True,
    )
    candidates = []
    for index in range(len(accepted)):
        candidate_ref = _seal_attempt(store, index)
        outcome = authority.evaluate_once(
            public_evaluation_candidate_ref=candidate_ref,
            public_contract_sha256="b" * 64,
            public_profile_sha256="a" * 64,
            tool_environment_policy_sha256="d" * 64,
        )
        candidates.append(
            TerminalSelectionCandidate(candidate_ref, outcome.artifact_ref)
        )
    return store, candidates


def test_at_a_selects_earliest_public_acceptance() -> None:
    root = _test_root()
    try:
        store, candidates = _evaluated_candidates(root, (False, True, True))

        selection = select_development_terminal_candidate(
            store,
            episode_id="episode-selection",
            method_condition="M1",
            evaluation_scope="excluded",
            attempt_profile="@A",
            candidates=candidates,
        )
        verified = read_verified_development_terminal_selection(
            store, selection.artifact_ref
        )

        assert verified["selected_attempt_id"] == "attempt-001"
        assert verified["selection_reason"] == "earliest_public_acceptance"
        assert verified["official_authority"] is False
        assert verified["g4b_authorized"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_at_a_selects_last_complete_when_none_is_accepted() -> None:
    root = _test_root()
    try:
        store, candidates = _evaluated_candidates(root, (False, False, False))

        selection = select_development_terminal_candidate(
            store,
            episode_id="episode-selection",
            method_condition="M1",
            evaluation_scope="development",
            attempt_profile="@A",
            candidates=candidates,
        )

        assert selection.payload["selected_attempt_id"] == "attempt-002"
        assert selection.payload["selection_reason"] == "last_complete_budget_exhausted"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_terminal_selection_rejects_wrong_order_and_cross_candidate_outcome() -> None:
    root = _test_root()
    try:
        store, candidates = _evaluated_candidates(root, (False, True))
        with pytest.raises(TerminalSelectionError, match="strictly ordered"):
            select_development_terminal_candidate(
                store,
                episode_id="episode-selection",
                method_condition="M1",
                evaluation_scope="excluded",
                attempt_profile="@A",
                candidates=reversed(candidates),
            )
        mismatched = [
            TerminalSelectionCandidate(
                candidates[0].public_evaluation_candidate_ref,
                candidates[1].public_outcome_ref,
            )
        ]
        with pytest.raises(TerminalSelectionError, match="identity mismatch"):
            select_development_terminal_candidate(
                store,
                episode_id="episode-selection",
                method_condition="M1",
                evaluation_scope="excluded",
                attempt_profile="@1",
                candidates=mismatched,
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)
