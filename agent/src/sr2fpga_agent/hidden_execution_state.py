"""Two-axis hidden execution closure rebuilt from evaluator-private events."""

from __future__ import annotations

import hashlib
import json

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.evaluator_dispatch import (
    _canonical_json, read_verified_development_hidden_conformance_outcome,
)


def reconcile_hidden_execution_state(
    candidate_store: ArtifactStore, evaluator_store: ArtifactStore, *, legacy_outcome_ref: ArtifactRef,
) -> tuple[dict, ArtifactRef]:
    if candidate_store.root.resolve() == evaluator_store.root.resolve():
        raise ValueError("hidden execution evidence requires separate stores")
    legacy = read_verified_development_hidden_conformance_outcome(candidate_store, legacy_outcome_ref)
    digest = legacy["opaque_outcome_ref"]["outcome_id"].removeprefix("hidden-outcome-")
    private = json.loads(evaluator_store.read_verified(f"private-outcomes/{digest}"))
    ledger = private["ledger"]
    if hashlib.sha256(_canonical_json(ledger)).hexdigest() != digest:
        raise ValueError("hidden private ledger identity mismatch")
    for field in ("episode_id", "method_condition", "decoding_seed", "terminal_candidate_sha256",
                  "hidden_evaluator_commitment_sha256"):
        if ledger[field] != legacy[field]:
            raise ValueError("hidden legacy outcome and private ledger disagree")
    refs = [ArtifactRef(**raw) for raw in private["execution_event_refs"]]
    ceiling = private["max_infrastructure_retries"]
    if ceiling != ledger["max_infrastructure_retries"]:
        raise ValueError("hidden retry ceiling differs from frozen execution identity")
    if isinstance(ceiling, bool) or not isinstance(ceiling, int) or ceiling < 0 or not 1 <= len(refs) <= ceiling + 1:
        raise ValueError("hidden execution retry ceiling violated")
    events = []
    stream_id = f"hidden-{digest}"
    for index, ref in enumerate(refs):
        event = _read_event(evaluator_store, ref, stream_id, index, "hidden_execution")
        payload = event["payload"]
        if payload["ordinal"] != index or payload["previous_execution_ref"] != (refs[index - 1].to_dict() if index else None):
            raise ValueError("hidden retry lineage is not contiguous")
        if (payload["terminal_candidate_sha256"] != ledger["terminal_candidate_sha256"]
                or payload["private_commitment_sha256"] != ledger["hidden_evaluator_commitment_sha256"]
                or payload["hidden_case_seed"] != ledger["decoding_seed"]):
            raise ValueError("hidden retry changed terminal, commitment, or case seed")
        if index and events[-1]["hidden_execution_status"] != "infrastructure_error":
            raise ValueError("hidden retry after semantic commit or integrity error")
        status = payload["hidden_execution_status"]
        semantic = payload["hidden_semantic_status"]
        if status == "completed":
            if semantic not in {"pass", "fail"} or payload["raw_evaluator_outcome"].get("outcome") != semantic:
                raise ValueError("completed hidden execution lacks raw semantic evidence")
        elif status not in {"infrastructure_error", "integrity_error"} or semantic is not None:
            raise ValueError("invalid hidden execution/semantic state")
        events.append(payload)
    final = events[-1]
    if final["hidden_execution_status"] == "infrastructure_error" and len(refs) != ceiling + 1:
        raise ValueError("hidden infrastructure execution stopped before frozen retry exhaustion")
    commit_raw = private["semantic_commit_ref"]
    commit_ref = ArtifactRef(**commit_raw) if commit_raw is not None else None
    if final["hidden_execution_status"] == "completed":
        if commit_ref is None:
            raise ValueError("completed hidden result has no semantic commit")
        commit = _read_event(evaluator_store, commit_ref, stream_id, len(refs), "hidden_semantic_committed")
        if commit["payload"] != {
            "execution_ref": refs[-1].to_dict(),
            "terminal_candidate_sha256": ledger["terminal_candidate_sha256"],
            "hidden_semantic_status": final["hidden_semantic_status"],
        }:
            raise ValueError("hidden semantic commit does not match final execution")
        if legacy["hidden_l2"]["status"] != final["hidden_semantic_status"]:
            raise ValueError("legacy hidden semantic status mismatch")
    elif commit_ref is not None or legacy["hidden_l2"]["status"] != "not_run":
        raise ValueError("uncommitted hidden execution cannot carry a semantic result")
    expected_refs = tuple(refs + ([commit_ref] if commit_ref else []))
    if evaluator_store.event_refs(stream_id) != expected_refs:
        raise ValueError("hidden execution event stream has extra or missing events")
    subject = {"episode_id": ledger["episode_id"], "method_condition": ledger["method_condition"]}
    subject_digest = hashlib.sha256(_canonical_json(subject)).hexdigest()
    if (evaluator_store.reference(f"one-shot/hidden-semantic-{subject_digest}") is not None) != (commit_ref is not None):
        raise ValueError("hidden semantic ledger and commit event disagree")
    for key in (f"hidden-subject-{subject_digest}", f"hidden-{digest}") + (
        (f"hidden-semantic-{subject_digest}",) if commit_ref else ()
    ):
        consumed = json.loads(evaluator_store.read_verified(f"one-shot/{key}"))
        if consumed["subject_sha256"] != ledger["terminal_candidate_sha256"] or consumed["operation_id"] != key:
            raise ValueError("hidden one-shot ledger subject mismatch")
    if private["raw_evaluator_outcome"] != final["raw_evaluator_outcome"]:
        raise ValueError("hidden private summary does not match final execution")
    if private["execution_status"] != ("completed" if commit_ref else "not_run") or private["infrastructure_reason"] != final["infrastructure_reason"]:
        raise ValueError("hidden private execution summary disagrees with events")
    if not commit_ref and legacy["hidden_l2"]["reason"] != final["infrastructure_reason"]:
        raise ValueError("legacy hidden infrastructure reason mismatch")
    payload = {
        "contract_version": "development-hidden-execution-state-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "legacy_outcome_ref": legacy_outcome_ref.to_dict(),
        "episode_id": ledger["episode_id"], "method_condition": ledger["method_condition"],
        "terminal_candidate_sha256": ledger["terminal_candidate_sha256"],
        "hidden_execution_status": final["hidden_execution_status"],
        "hidden_semantic_status": final["hidden_semantic_status"],
        "semantic_commit_count": int(commit_ref is not None),
        "execution_count": len(refs), "infrastructure_retry_count": len(refs) - 1,
        "max_infrastructure_retries": ceiling,
        "private_event_chain_sha256": hashlib.sha256(_canonical_json([ref.to_dict() for ref in expected_refs])).hexdigest(),
        "reducer_visible": True, "generation_visible": False, "repair_visible": False,
        "official_outcome": False, "official_authority": False, "pass_credit_authority": False,
        "g3_accepted": False, "g4b_authorized": False,
    }
    payload["outcome_id"] = "hidden-execution-" + hashlib.sha256(_canonical_json(payload)).hexdigest()
    ref = candidate_store.put_validated_json(f"hidden-execution-states/{digest}", payload,
                                            contract_key="development_hidden_execution_state")
    return payload, ref


def read_verified_hidden_execution_state(candidate_store, evaluator_store, reference):
    payload = json.loads(candidate_store.read_verified(reference))
    errors = ContractRegistry().load_schema("development_hidden_execution_state").validate(payload)
    if errors:
        raise ValueError("invalid hidden execution state: " + "; ".join(errors))
    rebuilt, ref = reconcile_hidden_execution_state(candidate_store, evaluator_store,
                                                    legacy_outcome_ref=ArtifactRef(**payload["legacy_outcome_ref"]))
    if rebuilt != payload or ref != reference:
        raise ValueError("hidden execution state does not match private event replay")
    return payload


def _read_event(store, ref, stream_id, sequence, event_type):
    event = json.loads(store.read_verified(ref))
    without_id = {key: value for key, value in event.items() if key != "event_id"}
    expected = "event-" + hashlib.sha256(_canonical_json(without_id)).hexdigest()
    if (event.get("event_id") != expected or event.get("episode_id") != stream_id
            or event.get("sequence") != sequence or event.get("event_type") != event_type
            or event.get("event_version") != "trusted-core-event-v1"):
        raise ValueError("hidden execution event identity or ordering mismatch")
    return event
