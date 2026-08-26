import json

import pytest

from sr2fpga_agent.artifact_store import (
    ArtifactIntegrityError,
    ArtifactStore,
    OneShotViolation,
)
from sr2fpga_agent.evaluator_dispatch import (
    DevelopmentHiddenEvaluationAuthority,
    read_verified_development_hidden_conformance_outcome,
)
from sr2fpga_agent.method_contract import method_policy_sha256
from sr2fpga_agent.models import GeneratedProject
from sr2fpga_agent.project_contract import build_project_envelope


def _project() -> GeneratedProject:
    manifest = {
        "contract_version": "project-package-v1",
        "project_name": "counter8",
        "top": {
            "module": "top",
            "source": "rtl/top.v",
            "interface": {"ports": [{"name": "count", "direction": "output", "width": 8}]},
        },
        "sources": [{"path": "rtl/top.v", "role": "rtl_source", "language": "verilog"}],
        "artifacts": [
            {"path": "sim/tb_top.v", "role": "candidate_testbench", "applicability": "advisory"}
        ],
        "build": {"toolchain_id": "open_source", "language_standard": "verilog-2005"},
    }
    return GeneratedProject(
        "counter8",
        {
            "manifest.json": json.dumps(manifest, sort_keys=True) + "\n",
            "rtl/top.v": "module top(output [7:0] count); assign count = 8'd1; endmodule\n",
            "sim/tb_top.v": "// malicious candidate claims TEST_PASS\n",
        },
    )


def _sealed_candidate(tmp_path):
    store = ArtifactStore(tmp_path / "candidate-store")
    project = _project()
    policies = {
        path: {"owner": "model", "origin": "model_generated", "editable": False}
        for path in project.files
    }
    envelope = build_project_envelope(
        project,
        episode_id="episode-001",
        method_condition_id="M0",
        method_policy_sha256=method_policy_sha256("M0"),
        snapshot_id="snapshot-000",
        file_policies=policies,
    )
    envelope_ref = store.put_validated_json(
        "envelopes/candidate-001", envelope, contract_key="project_envelope"
    )
    creation = store.append_event("episode-001", "candidate_created", {})
    seal_ref = store.seal_candidate(
        "candidate-001",
        project=project,
        project_envelope_ref=envelope_ref,
        requirement_projection_sha256="a" * 64,
        creation_event_ref=creation,
    )
    return store, project, seal_ref


def test_hidden_dispatch_reads_only_sealed_candidate_and_returns_opaque_ref(tmp_path) -> None:
    candidate_store, mutable_project, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    commitment = evaluator_store.put_blob("private/commitment", b"expected-count=1")
    seen = {}

    def evaluator(value):
        seen["rtl"] = value.terminal_project.files["rtl/top.v"]
        seen["private"] = value.private_commitment
        return {
            "outcome": "pass" if "8'd1" in seen["rtl"] and seen["private"] == b"expected-count=1" else "fail",
            "private_case": "case-secret-001",
        }

    authority = DevelopmentHiddenEvaluationAuthority(
        candidate_store, evaluator_store, evaluator
    )
    mutable_project.files["rtl/top.v"] = "module top; endmodule\n"
    outcome_ref = authority.evaluate_once(
        terminal_candidate_ref=seal_ref,
        private_commitment_ref=commitment,
        public_contract_sha256="b" * 64,
        public_profile_sha256="c" * 64,
        tool_environment_policy_sha256="d" * 64,
        decoding_seed=7,
    )

    assert "8'd1" in seen["rtl"]
    assert seen["private"] == b"expected-count=1"
    public_value = outcome_ref.to_dict()
    assert set(public_value) == {"outcome_id", "contract_id"}
    assert "pass" not in json.dumps(public_value)
    assert "case-secret-001" not in json.dumps(public_value)

    sanitized_ref = authority.publish_sanitized_outcome(outcome_ref)
    sanitized = read_verified_development_hidden_conformance_outcome(
        candidate_store, sanitized_ref
    )
    assert sanitized["hidden_l2"] == {"status": "pass", "reason": None}
    assert sanitized["terminal_candidate_sha256"] == seal_ref.sha256
    assert sanitized["opaque_outcome_ref"] == public_value
    assert sanitized["reducer_visible"] is True
    assert sanitized["generation_visible"] is False
    assert sanitized["repair_visible"] is False
    assert sanitized["official_outcome"] is False
    assert sanitized["g4b_authorized"] is False
    assert "case-secret-001" not in json.dumps(sanitized)


def test_hidden_dispatch_is_one_shot_for_exact_ledger_key(tmp_path) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    commitment = evaluator_store.put_blob("private/commitment", b"secret")
    calls = []
    authority = DevelopmentHiddenEvaluationAuthority(
        candidate_store,
        evaluator_store,
        lambda value: calls.append(value) or {"outcome": "fail"},
    )
    kwargs = {
        "terminal_candidate_ref": seal_ref,
        "private_commitment_ref": commitment,
        "public_contract_sha256": "b" * 64,
        "public_profile_sha256": "c" * 64,
        "tool_environment_policy_sha256": "d" * 64,
        "decoding_seed": 7,
    }

    authority.evaluate_once(**kwargs)
    with pytest.raises(OneShotViolation, match="already consumed"):
        authority.evaluate_once(**kwargs)
    assert len(calls) == 1


def test_hidden_dispatch_rejects_tampered_terminal_artifact_before_evaluator(tmp_path) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    commitment = evaluator_store.put_blob("private/commitment", b"secret")
    calls = []
    authority = DevelopmentHiddenEvaluationAuthority(
        candidate_store,
        evaluator_store,
        lambda value: calls.append(value) or {"outcome": "pass"},
    )
    blob = candidate_store.root / "blobs" / seal_ref.sha256[:2] / seal_ref.sha256
    blob.write_bytes(b"tampered")

    with pytest.raises(ArtifactIntegrityError):
        authority.evaluate_once(
            terminal_candidate_ref=seal_ref,
            private_commitment_ref=commitment,
            public_contract_sha256="b" * 64,
            public_profile_sha256="c" * 64,
            tool_environment_policy_sha256="d" * 64,
            decoding_seed=7,
        )
    assert calls == []


def test_hidden_dispatch_requires_separate_candidate_and_evaluator_stores(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "shared")
    with pytest.raises(ValueError, match="physically separate"):
        DevelopmentHiddenEvaluationAuthority(store, store, lambda value: {})


def test_hidden_sanitizer_maps_invalid_private_result_to_not_run(tmp_path) -> None:
    candidate_store, _, seal_ref = _sealed_candidate(tmp_path)
    evaluator_store = ArtifactStore(tmp_path / "evaluator-store")
    commitment = evaluator_store.put_blob("private/commitment", b"secret")
    authority = DevelopmentHiddenEvaluationAuthority(
        candidate_store,
        evaluator_store,
        lambda _value: {
            "outcome": "opaque",
            "private_case": "must-never-cross-boundary",
        },
    )
    opaque_ref = authority.evaluate_once(
        terminal_candidate_ref=seal_ref,
        private_commitment_ref=commitment,
        public_contract_sha256="b" * 64,
        public_profile_sha256="c" * 64,
        tool_environment_policy_sha256="d" * 64,
        decoding_seed=7,
    )

    sanitized_ref = authority.publish_sanitized_outcome(opaque_ref)
    sanitized = read_verified_development_hidden_conformance_outcome(
        candidate_store, sanitized_ref
    )

    assert sanitized["execution_status"] == "not_run"
    assert sanitized["hidden_l2"] == {
        "status": "not_run",
        "reason": "invalid_evaluator_outcome",
    }
    assert "must-never-cross-boundary" not in json.dumps(sanitized)
