"""Evaluator-owned event channel and downstream interceptor for OASA."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, NoReturn

from sr2fpga_agent.contract_registry import ContractRegistry


AMBIGUITY_AUDIT_EVENTS_VERSION = "ambiguity-audit-events-v1"


class DownstreamEventIntercepted(RuntimeError):
    """Raised before an OASA-forbidden downstream callback can execute."""


class AmbiguityAuditEventInterceptor:
    def __init__(self, *, audit_run_id: str, manifest_sha256: str) -> None:
        self._audit_run_id = audit_run_id
        self._manifest_sha256 = manifest_sha256
        self._events: list[dict[str, Any]] = []

    def phase_a_started(self, ambiguity_case_id: str) -> None:
        self._append(ambiguity_case_id, "phase_a_started")

    def phase_a_completed(
        self,
        ambiguity_case_id: str,
        *,
        execution_status: str,
        counters: dict[str, Any],
        infrastructure_status: str,
        predicted_disposition: str | None = None,
        not_run_reason_id: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {
            "execution_status": execution_status,
            "infrastructure_status": infrastructure_status,
            "counters": dict(counters),
        }
        if predicted_disposition is not None:
            fields["predicted_disposition"] = predicted_disposition
        if not_run_reason_id is not None:
            fields["not_run_reason_id"] = not_run_reason_id
        self._append(ambiguity_case_id, "phase_a_completed", **fields)

    def attempt_downstream(
        self,
        ambiguity_case_id: str,
        downstream_kind: str,
        callback: Callable[[], Any],
    ) -> NoReturn:
        """Record the unsafe attempt and raise without invoking callback."""

        del callback
        self._append(
            ambiguity_case_id,
            "downstream_attempt",
            downstream_kind=downstream_kind,
            enforcement_status="intercepted",
        )
        raise DownstreamEventIntercepted(
            f"OASA intercepted forbidden downstream event: {downstream_kind}"
        )

    def record_escaped_downstream(
        self,
        ambiguity_case_id: str,
        downstream_kind: str,
    ) -> None:
        """Evaluator reconciliation hook for a downstream event that escaped interception."""

        self._append(
            ambiguity_case_id,
            "downstream_attempt",
            downstream_kind=downstream_kind,
            enforcement_status="escaped",
        )

    def build_artifact(self, *, phase_a_audit_sha256: str) -> dict[str, Any]:
        payload = {
            "contract_version": AMBIGUITY_AUDIT_EVENTS_VERSION,
            "audit_run_id": self._audit_run_id,
            "manifest_sha256": self._manifest_sha256,
            "phase_a_audit_sha256": phase_a_audit_sha256,
            "visibility_class": "evaluator_only",
            "events": list(self._events),
        }
        artifact = {**payload, "artifact_sha256": _sha256(payload)}
        validate_ambiguity_audit_events(artifact)
        return artifact

    def _append(
        self,
        ambiguity_case_id: str,
        event_type: str,
        **fields: Any,
    ) -> None:
        self._events.append(
            {
                "sequence": len(self._events),
                "ambiguity_case_id": ambiguity_case_id,
                "event_type": event_type,
                **fields,
            }
        )


def validate_ambiguity_audit_events(artifact: dict[str, Any]) -> None:
    contract = ContractRegistry().load_schema("ambiguity_audit_events")
    errors = contract.validate(artifact)
    if errors:
        raise ValueError("invalid ambiguity audit event artifact: " + "; ".join(errors))
    expected_sequences = list(range(len(artifact["events"])))
    actual_sequences = [item["sequence"] for item in artifact["events"]]
    if actual_sequences != expected_sequences:
        raise ValueError("ambiguity audit event sequence must be contiguous and ordered")
    payload = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    if artifact["artifact_sha256"] != _sha256(payload):
        raise ValueError("ambiguity audit events SHA-256 does not match canonical payload")


def write_ambiguity_audit_events(path: Path, artifact: dict[str, Any]) -> None:
    validate_ambiguity_audit_events(artifact)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
