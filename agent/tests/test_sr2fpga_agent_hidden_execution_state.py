import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore, OneShotViolation
from sr2fpga_agent.evaluator_dispatch import DevelopmentHiddenEvaluationAuthority, development_hidden_case_seed
from sr2fpga_agent.hidden_execution_state import read_verified_hidden_execution_state
from test_sr2fpga_agent_evaluator_dispatch import _sealed_candidate


def _fixture(tmp_path, evaluator):
    candidate, project, seal = _sealed_candidate(tmp_path)
    private = ArtifactStore(tmp_path / "private")
    authority = DevelopmentHiddenEvaluationAuthority(candidate, private, evaluator)
    kwargs = dict(terminal_candidate_ref=seal,
                  private_commitment_ref=private.put_blob("private/commitment", b"fixed-cases"),
                  public_contract_sha256="b" * 64, public_profile_sha256="c" * 64,
                  tool_environment_policy_sha256="d" * 64, decoding_seed=17,
                  max_infrastructure_retries=1)
    return authority, kwargs, project


def _publish(authority, opaque):
    legacy_ref = authority.publish_sanitized_outcome(opaque)
    ref = authority.candidate_store.reference("hidden-execution-states/" + opaque.outcome_id.removeprefix("hidden-outcome-"))
    assert ref is not None
    state = read_verified_hidden_execution_state(authority.candidate_store, authority.evaluator_store, ref)
    assert state["legacy_outcome_ref"] == legacy_ref.to_dict()
    return state, ref


@pytest.mark.parametrize("semantic", ["pass", "fail"])
def test_hidden_precommit_retry_is_same_terminal_and_single_commit(tmp_path, semantic):
    calls = []
    def evaluator(value):
        calls.append((value.terminal_candidate_sha256, value.hidden_case_seed, dict(value.terminal_project.files)))
        if len(calls) == 1:
            raise TimeoutError("PRIVATE-INFRA-CANARY https://private.invalid/key")
        return {"outcome": semantic, "private_case": "PRIVATE-CASE-CANARY"}
    authority, kwargs, _ = _fixture(tmp_path, evaluator)
    opaque = authority.evaluate_once(**kwargs)
    state, _ = _publish(authority, opaque)
    assert calls[0] == calls[1]
    assert state["hidden_execution_status"] == "completed"
    assert state["hidden_semantic_status"] == semantic
    assert state["semantic_commit_count"] == 1
    assert state["execution_count"] == 2
    assert state["infrastructure_retry_count"] == 1
    assert "PRIVATE-" not in json.dumps(state)
    with pytest.raises(OneShotViolation):
        authority.evaluate_once(**kwargs)
    assert len(calls) == 2


@pytest.mark.parametrize("mutation", ["seed", "commitment", "terminal"])
def test_hidden_subject_cannot_be_rescored_by_changing_identity(tmp_path, mutation):
    authority, kwargs, project = _fixture(tmp_path, lambda value: {"outcome": "fail"})
    authority.evaluate_once(**kwargs)
    if mutation == "seed":
        kwargs["decoding_seed"] += 1
    elif mutation == "commitment":
        kwargs["private_commitment_ref"] = authority.evaluator_store.put_blob("private/alternate", b"other-cases")
    else:
        store = authority.candidate_store
        kwargs["terminal_candidate_ref"] = store.seal_candidate(
            "candidate-002", project=project, project_envelope_ref=store.reference("envelopes/candidate-001"),
            requirement_projection_sha256="a" * 64,
            creation_event_ref=store.append_event("episode-001", "candidate_created", {}),
        )
    with pytest.raises(OneShotViolation):
        authority.evaluate_once(**kwargs)


def test_hidden_exhausted_infrastructure_has_no_semantic_commit(tmp_path):
    def evaluator(value):
        raise TimeoutError("private unavailable")
    authority, kwargs, _ = _fixture(tmp_path, evaluator)
    state, _ = _publish(authority, authority.evaluate_once(**kwargs))
    assert state["hidden_execution_status"] == "infrastructure_error"
    assert state["hidden_semantic_status"] is None
    assert state["semantic_commit_count"] == 0
    assert state["execution_count"] == 2


def test_hidden_integrity_error_never_retries_or_commits(tmp_path):
    def evaluator(value):
        value.terminal_project.files["rtl/top.v"] = "mutated by evaluator"
        return {"outcome": "pass"}
    authority, kwargs, _ = _fixture(tmp_path, evaluator)
    state, _ = _publish(authority, authority.evaluate_once(**kwargs))
    assert state["hidden_execution_status"] == "integrity_error"
    assert state["hidden_semantic_status"] is None
    assert state["semantic_commit_count"] == 0
    assert state["execution_count"] == 1


def test_hidden_companion_rejects_forged_counts_and_extra_events(tmp_path):
    authority, kwargs, _ = _fixture(tmp_path, lambda value: {"outcome": "pass"})
    opaque = authority.evaluate_once(**kwargs)
    state, ref = _publish(authority, opaque)
    forged = dict(state, execution_count=99)
    forged_ref = authority.candidate_store.put_validated_json("forged", forged,
                                                            contract_key="development_hidden_execution_state")
    with pytest.raises(ValueError, match="private event replay"):
        read_verified_hidden_execution_state(authority.candidate_store, authority.evaluator_store, forged_ref)
    digest = opaque.outcome_id.removeprefix("hidden-outcome-")
    authority.evaluator_store.append_event("hidden-" + digest, "hidden_execution", {})
    with pytest.raises(ValueError, match="extra or missing"):
        read_verified_hidden_execution_state(authority.candidate_store, authority.evaluator_store, ref)


def test_hidden_case_seed_is_shared_by_paired_methods_not_sample_ids():
    common = dict(semantic_instance_id="semantic-1", replicate_id="replicate-0")
    seeds = {development_hidden_case_seed(dict(common, method_condition=f"M{i}", decoding_seed=i), f"sample-{i}") for i in range(6)}
    assert len(seeds) == 1
    assert development_hidden_case_seed(dict(common, replicate_id="replicate-1"), "sample-0") not in seeds
