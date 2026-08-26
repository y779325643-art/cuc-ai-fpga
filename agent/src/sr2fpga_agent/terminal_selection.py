"""Fail-closed development terminal selection from public-evaluator outcomes."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.public_evaluator import (
    read_verified_development_authoritative_attempt_public_outcome,
)


class TerminalSelectionError(ValueError):
    pass


@dataclass(frozen=True)
class TerminalSelectionCandidate:
    public_evaluation_candidate_ref: ArtifactRef
    public_outcome_ref: ArtifactRef


@dataclass(frozen=True)
class DevelopmentTerminalSelection:
    payload: dict[str, Any]
    artifact_ref: ArtifactRef


def select_development_terminal_candidate(
    store: ArtifactStore,
    *,
    episode_id: str,
    method_condition: str,
    evaluation_scope: str,
    attempt_profile: str,
    candidates: Iterable[TerminalSelectionCandidate],
    registry: ContractRegistry | None = None,
) -> DevelopmentTerminalSelection:
    """Select earliest accepted candidate, otherwise the last complete candidate."""

    if evaluation_scope not in {"development", "excluded"}:
        raise TerminalSelectionError("unsupported development evaluation scope")
    if method_condition not in {"M0", "M1", "M2", "M3", "M4", "M5"}:
        raise TerminalSelectionError("unknown method condition")
    if attempt_profile not in {"@1", "@A"}:
        raise TerminalSelectionError("unknown attempt profile")
    contract_registry = registry or ContractRegistry()
    records = []
    seen_attempts: set[str] = set()
    seen_candidates: set[str] = set()
    last_attempt_number = -1
    for item in tuple(candidates):
        candidate = _read_candidate(
            store,
            item.public_evaluation_candidate_ref,
            contract_registry,
        )
        outcome = read_verified_development_authoritative_attempt_public_outcome(
            store,
            item.public_outcome_ref,
            registry=contract_registry,
        )
        identity = (
            candidate["episode_id"],
            candidate["attempt_id"],
            candidate["method_condition_id"],
        )
        if identity != (
            outcome["episode_id"],
            outcome["attempt_id"],
            outcome["method_condition"],
        ):
            raise TerminalSelectionError("candidate and public outcome identity mismatch")
        if (identity[0], identity[2]) != (episode_id, method_condition):
            raise TerminalSelectionError("terminal selection identity mismatch")
        if (
            outcome["public_evaluation_candidate_sha256"]
            != item.public_evaluation_candidate_ref.sha256
        ):
            raise TerminalSelectionError("public outcome candidate hash mismatch")
        attempt_match = re.fullmatch(r"attempt-(\d{3})", identity[1])
        if attempt_match is None:
            raise TerminalSelectionError("attempt ID must use attempt-NNN form")
        attempt_number = int(attempt_match.group(1))
        if attempt_number <= last_attempt_number:
            raise TerminalSelectionError("candidate attempts must be strictly ordered")
        last_attempt_number = attempt_number
        if identity[1] in seen_attempts or candidate["candidate_id"] in seen_candidates:
            raise TerminalSelectionError("duplicate attempt or candidate identity")
        seen_attempts.add(identity[1])
        seen_candidates.add(candidate["candidate_id"])
        records.append(
            {
                "attempt_id": identity[1],
                "candidate_id": candidate["candidate_id"],
                "public_evaluation_candidate_ref": (
                    item.public_evaluation_candidate_ref.to_dict()
                ),
                "public_outcome_ref": item.public_outcome_ref.to_dict(),
                "complete_project": outcome["complete_project"],
                "public_acceptance": outcome["public_acceptance"],
            }
        )
    if not records:
        raise TerminalSelectionError("terminal selection requires evaluated candidates")
    if attempt_profile == "@1" and len(records) != 1:
        raise TerminalSelectionError("@1 requires exactly one evaluated candidate")
    complete = [record for record in records if record["complete_project"]]
    if not complete:
        raise TerminalSelectionError("no complete project is available for terminal selection")
    accepted = [record for record in complete if record["public_acceptance"]]
    if attempt_profile == "@1":
        selected = complete[0]
        reason = "at1_declared_candidate"
    elif accepted:
        selected = accepted[0]
        reason = "earliest_public_acceptance"
    else:
        selected = complete[-1]
        reason = "last_complete_budget_exhausted"
    without_id = {
        "contract_version": "development-terminal-selection-v1",
        "evaluation_scope": evaluation_scope,
        "episode_id": episode_id,
        "method_condition": method_condition,
        "attempt_profile": attempt_profile,
        "candidate_records": records,
        "selected_attempt_id": selected["attempt_id"],
        "selected_candidate_id": selected["candidate_id"],
        "selected_public_evaluation_candidate_ref": selected[
            "public_evaluation_candidate_ref"
        ],
        "selected_public_outcome_ref": selected["public_outcome_ref"],
        "selection_reason": reason,
        "terminal_selection_authority": True,
        "pass_credit_authority": True,
        "official_authority": False,
        "g4b_authorized": False,
    }
    payload = {
        **without_id,
        "selection_id": "development-terminal-selection-"
        + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
    }
    reference = store.put_validated_json(
        f"terminal-selections/{episode_id}/{method_condition}",
        payload,
        contract_key="development_terminal_selection",
        registry=contract_registry,
    )
    return DevelopmentTerminalSelection(payload, reference)


def read_verified_development_terminal_selection(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    registry: ContractRegistry | None = None,
) -> dict[str, Any]:
    payload = json.loads(store.read_verified(reference))
    contract = (registry or ContractRegistry()).load_schema(
        "development_terminal_selection"
    )
    errors = contract.validate(payload)
    if errors:
        raise TerminalSelectionError(
            "invalid development terminal selection: " + "; ".join(errors)
        )
    without_id = {key: value for key, value in payload.items() if key != "selection_id"}
    expected = "development-terminal-selection-" + hashlib.sha256(
        _canonical_json(without_id)
    ).hexdigest()
    if payload["selection_id"] != expected:
        raise TerminalSelectionError("terminal selection content-derived ID mismatch")
    return payload


def _read_candidate(
    store: ArtifactStore,
    reference: ArtifactRef,
    registry: ContractRegistry,
) -> dict[str, Any]:
    payload = json.loads(store.read_verified(reference))
    contract_key = (
        "public_evaluation_candidate"
        if payload.get("contract_version") == "public-evaluation-candidate-v1"
        else "public_evaluation_candidate_v2"
    )
    errors = registry.load_schema(contract_key).validate(payload)
    if errors:
        raise TerminalSelectionError(
            "invalid public-evaluation candidate: " + "; ".join(errors)
        )
    return payload


def _canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
