"""Development-only sealed-candidate boundary for evaluator-owned execution."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping

from sr2fpga_agent.models import GeneratedProject, canonical_json_bytes as _canonical_json
from sr2fpga_agent.artifact_store import ArtifactIntegrityError, ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry


_OPAQUE_HIDDEN_OUTCOME_RE = re.compile(r"^hidden-outcome-([0-9a-f]{64})$")


@dataclass(frozen=True)
class HiddenEvaluatorInput:
    """Private evaluator input; never returned to generation or repair."""

    terminal_project: GeneratedProject
    terminal_candidate_sha256: str
    public_contract_sha256: str
    public_profile_sha256: str
    private_commitment: bytes
    private_commitment_sha256: str
    tool_environment_policy_sha256: str
    hidden_case_seed: int = 0


@dataclass(frozen=True)
class OpaqueHiddenOutcomeRef:
    """The only value allowed to cross back from evaluator-owned storage."""

    outcome_id: str
    contract_id: str = "development-hidden-outcome-v1"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class DevelopmentHiddenEvaluationAuthority:
    """Exercise the final-only boundary without minting an official outcome.

    Official Paper-1 execution remains locked until a signed campaign authority
    and evaluator-owned CLI/process are implemented. This class deliberately
    returns no status, score, diagnostics, or private identifier.
    """

    def __init__(
        self,
        candidate_store: ArtifactStore,
        evaluator_store: ArtifactStore,
        evaluator: Callable[[HiddenEvaluatorInput], Mapping[str, Any]],
    ) -> None:
        if candidate_store.root.resolve() == evaluator_store.root.resolve():
            raise ValueError("candidate and evaluator stores must be physically separate")
        self._candidate_store = candidate_store
        self._evaluator_store = evaluator_store
        self._evaluator = evaluator

    def evaluate_once(
        self,
        *,
        terminal_candidate_ref: ArtifactRef,
        private_commitment_ref: ArtifactRef,
        public_contract_sha256: str,
        public_profile_sha256: str,
        tool_environment_policy_sha256: str,
        decoding_seed: int,
        max_infrastructure_retries: int = 0,
    ) -> OpaqueHiddenOutcomeRef:
        for label, value in (
            ("public_contract_sha256", public_contract_sha256),
            ("public_profile_sha256", public_profile_sha256),
            ("tool_environment_policy_sha256", tool_environment_policy_sha256),
        ):
            _require_sha256(label, value)
        if not isinstance(decoding_seed, int) or isinstance(decoding_seed, bool) or decoding_seed < 0:
            raise ValueError("decoding_seed must be a non-negative integer")
        if isinstance(max_infrastructure_retries, bool) or not isinstance(max_infrastructure_retries, int) or max_infrastructure_retries < 0:
            raise ValueError("infrastructure retry ceiling must be a non-negative integer")

        terminal_bytes = self._candidate_store.read_verified(terminal_candidate_ref)
        try:
            terminal = json.loads(terminal_bytes)
        except json.JSONDecodeError as exc:
            raise ValueError("terminal candidate artifact is not valid JSON") from exc
        if not isinstance(terminal, dict) or terminal.get("contract_version") != "terminal-candidate-v1":
            raise ValueError("hidden evaluator requires terminal-candidate-v1")
        project = self._candidate_store.read_sealed_project(terminal_candidate_ref)
        private_commitment = self._evaluator_store.read_verified(private_commitment_ref)
        ledger_payload = {
            "episode_id": terminal["episode_id"],
            "method_condition": terminal["method_condition_id"],
            "decoding_seed": decoding_seed,
            "terminal_candidate_sha256": terminal_candidate_ref.sha256,
            "hidden_evaluator_commitment_sha256": private_commitment_ref.sha256,
            "max_infrastructure_retries": max_infrastructure_retries,
        }
        ledger_digest = hashlib.sha256(_canonical_json(ledger_payload)).hexdigest()
        subject_digest = hashlib.sha256(_canonical_json({
            "episode_id": terminal["episode_id"], "method_condition": terminal["method_condition_id"],
        })).hexdigest()
        self._evaluator_store.consume_once(f"hidden-subject-{subject_digest}", terminal_candidate_ref.sha256)
        ledger_ref = self._evaluator_store.consume_once(
            f"hidden-{ledger_digest}",
            terminal_candidate_ref.sha256,
        )
        execution_refs = []
        semantic_commit_ref = None
        stream_id = f"hidden-{ledger_digest}"
        for ordinal in range(max_infrastructure_retries + 1):
            semantic_status = None
            try:
                project = self._candidate_store.read_sealed_project(terminal_candidate_ref)
                private_commitment = self._evaluator_store.read_verified(private_commitment_ref)
                evaluator_input = HiddenEvaluatorInput(
                    terminal_project=project,
                    terminal_candidate_sha256=terminal_candidate_ref.sha256,
                    public_contract_sha256=public_contract_sha256,
                    public_profile_sha256=public_profile_sha256,
                    private_commitment=private_commitment,
                    private_commitment_sha256=private_commitment_ref.sha256,
                    tool_environment_policy_sha256=tool_environment_policy_sha256,
                    hidden_case_seed=decoding_seed,
                )
                raw_outcome = dict(self._evaluator(evaluator_input))
                if self._candidate_store.read_sealed_project(terminal_candidate_ref) != project:
                    raise ArtifactIntegrityError("evaluator mutated the sealed input view")
                self._evaluator_store.read_verified(private_commitment_ref)
                result = raw_outcome.get("outcome")
                if isinstance(result, str) and result in {"pass", "fail"}:
                    semantic_status = result
                    hidden_execution_status = "completed"
                    infrastructure_reason = None
                else:
                    hidden_execution_status = "infrastructure_error"
                    infrastructure_reason = "invalid_evaluator_outcome"
            except ArtifactIntegrityError as exc:
                raw_outcome = {"private_exception_type": type(exc).__name__, "private_message": str(exc)}
                hidden_execution_status = "integrity_error"
                infrastructure_reason = "artifact_integrity_error"
            except Exception as exc:  # evaluator details stay private
                raw_outcome = {"private_exception_type": type(exc).__name__, "private_message": str(exc)}
                hidden_execution_status = "infrastructure_error"
                infrastructure_reason = "evaluator_exception"
            execution_ref = self._evaluator_store.append_event(stream_id, "hidden_execution", {
                "ordinal": ordinal, "terminal_candidate_sha256": terminal_candidate_ref.sha256,
                "private_commitment_sha256": private_commitment_ref.sha256,
                "hidden_case_seed": decoding_seed,
                "previous_execution_ref": execution_refs[-1].to_dict() if execution_refs else None,
                "hidden_execution_status": hidden_execution_status,
                "hidden_semantic_status": semantic_status,
                "infrastructure_reason": infrastructure_reason,
                "raw_evaluator_outcome": raw_outcome,
            })
            execution_refs.append(execution_ref)
            if semantic_status is not None:
                self._evaluator_store.consume_once(f"hidden-semantic-{subject_digest}", terminal_candidate_ref.sha256)
                semantic_commit_ref = self._evaluator_store.append_event(stream_id, "hidden_semantic_committed", {
                    "execution_ref": execution_ref.to_dict(),
                    "terminal_candidate_sha256": terminal_candidate_ref.sha256,
                    "hidden_semantic_status": semantic_status,
                })
                break
            if hidden_execution_status == "integrity_error":
                break
        execution_status = "completed" if semantic_status is not None else "not_run"
        private_record = {
            "record_version": "development-hidden-outcome-v1",
            "evaluation_scope": "development_conformance_only",
            "ledger": ledger_payload,
            "one_shot_ledger_ref": ledger_ref.key,
            "public_contract_sha256": public_contract_sha256,
            "public_profile_sha256": public_profile_sha256,
            "tool_environment_policy_sha256": tool_environment_policy_sha256,
            "execution_status": execution_status,
            "infrastructure_reason": infrastructure_reason,
            "raw_evaluator_outcome": raw_outcome,
            "execution_event_refs": [ref.to_dict() for ref in execution_refs],
            "semantic_commit_ref": semantic_commit_ref.to_dict() if semantic_commit_ref else None,
            "max_infrastructure_retries": max_infrastructure_retries,
        }
        self._evaluator_store.put_blob(
            f"private-outcomes/{ledger_digest}",
            _canonical_json(private_record),
            media_type="application/json",
        )
        return OpaqueHiddenOutcomeRef(
            outcome_id="hidden-outcome-" + ledger_digest,
        )

    @property
    def candidate_store(self) -> ArtifactStore:
        return self._candidate_store

    @property
    def evaluator_store(self) -> ArtifactStore:
        return self._evaluator_store

    def store_private_commitment(
        self,
        key: str,
        private_commitment: bytes,
    ) -> ArtifactRef:
        if not isinstance(key, str) or not key:
            raise ValueError("private commitment key must be non-empty")
        if not isinstance(private_commitment, (bytes, bytearray)):
            raise TypeError("private commitment must be bytes")
        return self._evaluator_store.put_blob(
            f"private-commitments/{key}",
            bytes(private_commitment),
            media_type="application/octet-stream",
        )

    def publish_sanitized_outcome(
        self,
        opaque_ref: OpaqueHiddenOutcomeRef,
        *,
        registry: ContractRegistry | None = None,
    ) -> ArtifactRef:
        """Publish reducer-only status while retaining every private datum."""

        if not isinstance(opaque_ref, OpaqueHiddenOutcomeRef):
            raise TypeError("opaque hidden outcome reference is required")
        if opaque_ref.contract_id != "development-hidden-outcome-v1":
            raise ValueError("unknown opaque hidden outcome contract")
        match = _OPAQUE_HIDDEN_OUTCOME_RE.fullmatch(opaque_ref.outcome_id)
        if match is None:
            raise ValueError("invalid opaque hidden outcome ID")
        ledger_digest = match.group(1)
        private_record = _read_json_object(
            self._evaluator_store,
            f"private-outcomes/{ledger_digest}",
            "private hidden outcome",
        )
        if private_record.get("record_version") != "development-hidden-outcome-v1":
            raise ValueError("private hidden outcome version mismatch")
        if private_record.get("evaluation_scope") != "development_conformance_only":
            raise ValueError("private hidden outcome scope mismatch")
        ledger = private_record.get("ledger")
        if not isinstance(ledger, dict):
            raise ValueError("private hidden outcome ledger is missing")
        if hashlib.sha256(_canonical_json(ledger)).hexdigest() != ledger_digest:
            raise ValueError("opaque hidden outcome does not match its private ledger")
        for label in (
            "terminal_candidate_sha256",
            "hidden_evaluator_commitment_sha256",
        ):
            _require_sha256(label, ledger.get(label))
        for label in (
            "public_contract_sha256",
            "public_profile_sha256",
            "tool_environment_policy_sha256",
        ):
            value = private_record.get(label)
            _require_sha256(label, value)

        execution_status = private_record.get("execution_status")
        raw_outcome = private_record.get("raw_evaluator_outcome")
        if execution_status == "completed" and isinstance(raw_outcome, dict):
            hidden_status = raw_outcome.get("outcome")
        else:
            hidden_status = None
        if hidden_status in {"pass", "fail"}:
            sanitized_execution_status = "completed"
            hidden_l2 = {"status": hidden_status, "reason": None}
        else:
            sanitized_execution_status = "not_run"
            reason = private_record.get("infrastructure_reason")
            if not isinstance(reason, str) or not reason:
                reason = "invalid_evaluator_outcome"
            hidden_l2 = {"status": "not_run", "reason": reason}

        without_id = {
            "contract_version": "development-hidden-conformance-outcome-v1",
            "evaluation_scope": "excluded_development_conformance_only",
            "episode_id": ledger.get("episode_id"),
            "method_condition": ledger.get("method_condition"),
            "decoding_seed": ledger.get("decoding_seed"),
            "terminal_candidate_sha256": ledger["terminal_candidate_sha256"],
            "hidden_evaluator_commitment_sha256": ledger[
                "hidden_evaluator_commitment_sha256"
            ],
            "public_contract_sha256": private_record["public_contract_sha256"],
            "public_profile_sha256": private_record["public_profile_sha256"],
            "tool_environment_policy_sha256": private_record[
                "tool_environment_policy_sha256"
            ],
            "opaque_outcome_ref": opaque_ref.to_dict(),
            "one_shot_ledger_ref": private_record.get("one_shot_ledger_ref"),
            "execution_status": sanitized_execution_status,
            "hidden_l2": hidden_l2,
            "reducer_visible": True,
            "generation_visible": False,
            "repair_visible": False,
            "official_outcome": False,
            "g4b_authorized": False,
        }
        payload = {
            **without_id,
            "outcome_id": "hidden-conformance-outcome-"
            + hashlib.sha256(_canonical_json(without_id)).hexdigest(),
        }
        reference = self._candidate_store.put_validated_json(
            f"hidden-conformance-outcomes/{ledger_digest}",
            payload,
            contract_key="development_hidden_conformance_outcome",
            registry=registry,
        )
        if "execution_event_refs" in private_record:
            from sr2fpga_agent.hidden_execution_state import reconcile_hidden_execution_state

            reconcile_hidden_execution_state(self._candidate_store, self._evaluator_store,
                                             legacy_outcome_ref=reference)
        return reference


def development_hidden_case_seed(metadata: Mapping[str, Any] | None, sample_id: str) -> int:
    """Share the development case seed across methods in one explicit replicate."""
    metadata = metadata or {}
    semantic = metadata.get("semantic_instance_id")
    replicate = metadata.get("replicate_id")
    identity = ({"semantic_instance_id": semantic, "replicate_id": replicate}
                if isinstance(semantic, str) and semantic and isinstance(replicate, str) and replicate
                else {"legacy_sample_id": sample_id})
    return int.from_bytes(hashlib.sha256(_canonical_json({
        "domain": "excluded-development-hidden-case-seed-v1", **identity,
    })).digest()[:8], "big")


def _require_sha256(label: str, value: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be lowercase SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be lowercase SHA-256") from exc
    if value.lower() != value:
        raise ValueError(f"{label} must be lowercase SHA-256")


def read_verified_development_hidden_conformance_outcome(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    registry: ContractRegistry | None = None,
) -> dict[str, Any]:
    payload = _read_json_object(store, reference, "hidden conformance outcome")
    errors = (registry or ContractRegistry()).load_schema(
        "development_hidden_conformance_outcome"
    ).validate(payload)
    if errors:
        raise ValueError("invalid hidden conformance outcome: " + "; ".join(errors))
    outcome_id = payload.pop("outcome_id")
    expected = "hidden-conformance-outcome-" + hashlib.sha256(
        _canonical_json(payload)
    ).hexdigest()
    payload["outcome_id"] = outcome_id
    if outcome_id != expected:
        raise ValueError("hidden conformance outcome ID mismatch")
    return payload


def _read_json_object(
    store: ArtifactStore,
    key_or_ref: str | ArtifactRef,
    label: str,
) -> dict[str, Any]:
    try:
        payload = json.loads(store.read_verified(key_or_ref))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")
    return payload


