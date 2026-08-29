"""Method-neutral, development-only accounting for paired-block preparation."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

from sr2fpga_agent.artifact_store import ArtifactIntegrityError, ArtifactRef, ArtifactStore
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.cost_accounting import (
    COST_AXES,
    COUNT_COST_AXES,
    validate_accounting_failure_origin,
)


CHECKPOINT_IDS = (
    "direct_initial_project",
    "shared_system_his",
    "skeleton_initial_project",
)
_CHECKPOINT_PARENTS = {
    "direct_initial_project": (),
    "shared_system_his": (),
    "skeleton_initial_project": ("shared_system_his",),
}
_CHECKPOINT_STAGES = {
    "direct_initial_project": "block_direct_initial",
    "shared_system_his": "block_req2his",
    "skeleton_initial_project": "block_skeleton_initial",
}


class BlockPreparationCostLedgerError(ValueError):
    pass


@runtime_checkable
class ModelCostLedger(Protocol):
    def reserve(
        self,
        axis: str,
        amount: int | float,
        *,
        stage: str,
        visibility_class: str,
        limit: int | float,
        used_after: int | float,
        started_at: float | None = None,
    ) -> ArtifactRef: ...

    def record_budget_exhausted(
        self,
        axis: str,
        amount: int | float,
        *,
        stage: str,
        visibility_class: str,
        limit: int | float,
        used_after: int | float,
        started_at: float | None = None,
    ) -> ArtifactRef: ...

    def record_cost(
        self,
        *,
        stage: str,
        visibility_class: str,
        cost_delta: Mapping[str, int | float | None],
        status: str = "completed",
        duration_seconds: float | None = None,
        input_artifact_hashes: Iterable[str] = (),
        output_artifact_hashes: Iterable[str] = (),
        unavailable_axes: Mapping[str, str] | None = None,
        started_at: float | None = None,
    ) -> ArtifactRef: ...


@dataclass(frozen=True)
class ReplayedBlockPreparation:
    paired_block_ref: ArtifactRef
    event_refs: tuple[ArtifactRef, ...]
    events: tuple[dict[str, Any], ...]
    checkpoint_axes: dict[str, dict[str, Any]]
    actual_axes: dict[str, Any]
    source_events_sha256: str


class BlockPreparationCostLedger:
    """Append a closed, content-addressed event chain for one paired block."""

    def __init__(
        self,
        store: ArtifactStore,
        *,
        paired_block_ref: ArtifactRef,
        failure_origin: str | None,
    ) -> None:
        store.read_verified(paired_block_ref)
        self.store = store
        self.paired_block_ref = paired_block_ref
        self.failure_origin = validate_accounting_failure_origin(failure_origin)
        self._refs: list[ArtifactRef] = []
        self._values: dict[str, int | float] = {}
        self._unavailable: dict[str, str] = {}
        self._active_checkpoint: str | None = None
        self._closed = False

    @property
    def event_refs(self) -> tuple[ArtifactRef, ...]:
        return tuple(self._refs)

    @property
    def observed_axes(self) -> frozenset[str]:
        return frozenset(set(self._values) | set(self._unavailable))

    def activate_checkpoint(self, checkpoint_id: str) -> None:
        self._require_checkpoint(checkpoint_id)
        if self._closed:
            raise BlockPreparationCostLedgerError("cannot activate after accounting close")
        self._active_checkpoint = checkpoint_id

    def reserve(
        self,
        axis: str,
        amount: int | float,
        *,
        stage: str,
        visibility_class: str,
        limit: int | float,
        used_after: int | float,
        started_at: float | None = None,
    ) -> ArtifactRef:
        _require_axis_value(axis, amount)
        return self._append_cost_event(
            stage=stage,
            visibility_class=visibility_class,
            event_kind="budget_reserved",
            status="reserved",
            cost_delta={axis: amount},
            unavailable_axes={},
            budget_reservation={
                "axis": axis,
                "amount": amount,
                "limit": limit,
                "used_after": used_after,
            },
            duration_seconds=None,
            started_at=started_at,
        )

    def record_budget_exhausted(
        self,
        axis: str,
        amount: int | float,
        *,
        stage: str,
        visibility_class: str,
        limit: int | float,
        used_after: int | float,
        started_at: float | None = None,
    ) -> ArtifactRef:
        _require_axis_value(axis, amount)
        return self._append_cost_event(
            stage=stage,
            visibility_class=visibility_class,
            event_kind="budget_exhausted",
            status="exhausted",
            cost_delta={axis: 0},
            unavailable_axes={},
            budget_reservation={
                "axis": axis,
                "amount": amount,
                "limit": limit,
                "used_after": used_after,
            },
            duration_seconds=None,
            started_at=started_at,
        )

    def record_cost(
        self,
        *,
        stage: str,
        visibility_class: str,
        cost_delta: Mapping[str, int | float | None],
        status: str = "completed",
        duration_seconds: float | None = None,
        input_artifact_hashes: Iterable[str] = (),
        output_artifact_hashes: Iterable[str] = (),
        unavailable_axes: Mapping[str, str] | None = None,
        started_at: float | None = None,
    ) -> ArtifactRef:
        if status not in {"completed", "failed"}:
            raise BlockPreparationCostLedgerError(
                "axis-cost status must be completed or failed"
            )
        delta = dict(cost_delta)
        if duration_seconds is not None and "wall_time" not in delta:
            delta["wall_time"] = duration_seconds
        return self._append_cost_event(
            stage=stage,
            visibility_class=visibility_class,
            event_kind="axis_cost",
            status=status,
            cost_delta=delta,
            unavailable_axes=dict(unavailable_axes or {}),
            budget_reservation=None,
            duration_seconds=duration_seconds,
            started_at=started_at,
            input_artifact_hashes=input_artifact_hashes,
            output_artifact_hashes=output_artifact_hashes,
        )

    def record_checkpoint(
        self,
        *,
        checkpoint_id: str,
        event_kind: str,
        status: str,
        input_refs: Iterable[ArtifactRef] = (),
        output_refs: Iterable[ArtifactRef] = (),
        reason: str | None = None,
    ) -> ArtifactRef:
        self._require_checkpoint(checkpoint_id)
        if checkpoint_id != self._active_checkpoint:
            raise BlockPreparationCostLedgerError("checkpoint is not active")
        expected = {
            "checkpoint_materialized": "completed",
            "checkpoint_failed": "failed",
            "checkpoint_not_run": "not_run",
        }
        if expected.get(event_kind) != status:
            raise BlockPreparationCostLedgerError("invalid checkpoint event status")
        if (status == "completed") != (reason is None):
            raise BlockPreparationCostLedgerError("checkpoint reason does not match status")
        if status != "completed" and (not isinstance(reason, str) or not reason):
            raise BlockPreparationCostLedgerError("checkpoint reason must be non-empty")
        input_references = _verified_references(self.store, input_refs)
        output_references = _verified_references(self.store, output_refs)
        if status == "completed" and not output_references:
            raise BlockPreparationCostLedgerError("materialized checkpoint needs output")
        return self._append(
            checkpoint_id=checkpoint_id,
            stage=_CHECKPOINT_STAGES[checkpoint_id],
            visibility_class="accounting",
            event_kind=event_kind,
            status=status,
            duration_seconds=None,
            input_refs=input_references,
            output_refs=output_references,
            input_artifact_hashes=(),
            output_artifact_hashes=(),
            budget_reservation=None,
            cost_delta={axis: 0 for axis in COST_AXES},
            unavailable_axes={},
            reason=reason,
        )

    def close(
        self,
        *,
        zero_axes: Iterable[str] = (),
        unavailable_axes: Mapping[str, str] | None = None,
    ) -> ArtifactRef:
        if self._closed:
            raise BlockPreparationCostLedgerError("block cost ledger is already closed")
        declared_zero = set(zero_axes)
        declared_unavailable = dict(unavailable_axes or {})
        unknown = (declared_zero | set(declared_unavailable)) - set(COST_AXES)
        if unknown:
            raise BlockPreparationCostLedgerError(
                "unknown close axis: " + ", ".join(sorted(unknown))
            )
        already_observed = set(self._values) | set(self._unavailable)
        overlap = already_observed & (declared_zero | set(declared_unavailable))
        if overlap:
            raise BlockPreparationCostLedgerError(
                "close axis was already observed: " + ", ".join(sorted(overlap))
            )
        missing = set(COST_AXES) - already_observed - declared_zero - set(declared_unavailable)
        if missing:
            raise BlockPreparationCostLedgerError(
                "close must classify every unobserved cost axis: "
                + ", ".join(sorted(missing))
            )
        for axis, reason in declared_unavailable.items():
            if not isinstance(reason, str) or not reason:
                raise BlockPreparationCostLedgerError(
                    f"unavailable reason must be non-empty: {axis}"
                )
        reasons = {**self._unavailable, **declared_unavailable}
        totals = {
            axis: None if axis in reasons else self._values.get(axis, 0)
            for axis in COST_AXES
        }
        reference = self._append(
            checkpoint_id=None,
            stage="accounting_close",
            visibility_class="accounting",
            event_kind="accounting_closed",
            status="closed",
            duration_seconds=None,
            input_refs=(),
            output_refs=(),
            input_artifact_hashes=(),
            output_artifact_hashes=(),
            budget_reservation=None,
            cost_delta=totals,
            unavailable_axes=reasons,
            reason=None,
        )
        self._closed = True
        return reference

    def _append_cost_event(
        self,
        *,
        stage: str,
        visibility_class: str,
        event_kind: str,
        status: str,
        cost_delta: Mapping[str, int | float | None],
        unavailable_axes: Mapping[str, str],
        budget_reservation: Mapping[str, Any] | None,
        duration_seconds: float | None,
        started_at: float | None,
        input_artifact_hashes: Iterable[str] = (),
        output_artifact_hashes: Iterable[str] = (),
    ) -> ArtifactRef:
        checkpoint_id = self._require_active_checkpoint()
        if stage != _CHECKPOINT_STAGES[checkpoint_id]:
            raise BlockPreparationCostLedgerError("stage does not match active checkpoint")
        _validate_delta(cost_delta, unavailable_axes)
        reference = self._append(
            checkpoint_id=checkpoint_id,
            stage=stage,
            visibility_class=visibility_class,
            event_kind=event_kind,
            status=status,
            duration_seconds=duration_seconds,
            input_refs=(),
            output_refs=(),
            input_artifact_hashes=_sorted_hashes(input_artifact_hashes),
            output_artifact_hashes=_sorted_hashes(output_artifact_hashes),
            budget_reservation=budget_reservation,
            cost_delta=cost_delta,
            unavailable_axes=unavailable_axes,
            reason=None,
            started_at=started_at,
        )
        _accumulate_delta(self._values, self._unavailable, cost_delta, unavailable_axes)
        return reference

    def _append(
        self,
        *,
        checkpoint_id: str | None,
        stage: str,
        visibility_class: str,
        event_kind: str,
        status: str,
        duration_seconds: float | None,
        input_refs: tuple[ArtifactRef, ...],
        output_refs: tuple[ArtifactRef, ...],
        input_artifact_hashes: tuple[str, ...],
        output_artifact_hashes: tuple[str, ...],
        budget_reservation: Mapping[str, Any] | None,
        cost_delta: Mapping[str, int | float | None],
        unavailable_axes: Mapping[str, str],
        reason: str | None,
        started_at: float | None = None,
    ) -> ArtifactRef:
        if self._closed:
            raise BlockPreparationCostLedgerError("cannot append after accounting close")
        sequence = len(self._refs)
        event = {
            "contract_version": "development-block-preparation-event-v1",
            "evaluation_scope": "excluded_development_conformance_only",
            "parent_event_id": _event_id_from_ref(self.store, self._refs[-1]) if self._refs else None,
            "sequence": sequence,
            "paired_block_ref": self.paired_block_ref.to_dict(),
            "checkpoint_id": checkpoint_id,
            "parent_checkpoint_ids": list(_CHECKPOINT_PARENTS.get(checkpoint_id, ())),
            "stage": stage,
            "event_kind": event_kind,
            "status": status,
            "reason": reason,
            "started_at": time.time() if started_at is None else started_at,
            "duration_seconds": duration_seconds,
            "input_artifact_refs": [reference.to_dict() for reference in input_refs],
            "output_artifact_refs": [reference.to_dict() for reference in output_refs],
            "input_artifact_hashes": list(input_artifact_hashes),
            "output_artifact_hashes": list(output_artifact_hashes),
            "budget_reservation": dict(budget_reservation) if budget_reservation else None,
            "cost_delta": dict(cost_delta),
            "unavailable_axes": dict(unavailable_axes),
            "model_gateway_provenance_ref": None,
            "failure_origin": self.failure_origin,
            "official_outcome": False,
            "official_authority": False,
            "pass_credit_authority": False,
            "rq1_evidence": False,
            "rq2_evidence": False,
            "g3_accepted": False,
            "g4b_authorized": False,
        }
        event["event_id"] = "block-preparation-event-" + hashlib.sha256(
            _canonical_json(event)
        ).hexdigest()
        reference = self.store.put_validated_json(
            f"block-preparation-events/{self.paired_block_ref.sha256}/"
            f"{sequence:06d}-{event['event_id']}",
            event,
            contract_key="development_block_preparation_event",
        )
        self._refs.append(reference)
        return reference

    def _require_checkpoint(self, checkpoint_id: str) -> None:
        if checkpoint_id not in CHECKPOINT_IDS:
            raise BlockPreparationCostLedgerError(f"unknown checkpoint: {checkpoint_id}")

    def _require_active_checkpoint(self) -> str:
        if self._active_checkpoint is None:
            raise BlockPreparationCostLedgerError("no active checkpoint")
        return self._active_checkpoint


def replay_development_block_preparation(
    store: ArtifactStore,
    event_refs: Iterable[ArtifactRef],
    *,
    registry: ContractRegistry | None = None,
) -> ReplayedBlockPreparation:
    """Recompute closed block accounting from content-verified raw events."""

    references = tuple(event_refs)
    if not references:
        raise BlockPreparationCostLedgerError("block preparation replay requires events")
    contract = (registry or ContractRegistry()).load_schema(
        "development_block_preparation_event"
    )
    events: list[dict[str, Any]] = []
    for reference in references:
        try:
            event = json.loads(store.read_verified(reference))
        except json.JSONDecodeError as exc:
            raise BlockPreparationCostLedgerError("block event is not valid JSON") from exc
        errors = contract.validate(event)
        if errors:
            raise BlockPreparationCostLedgerError("invalid block event: " + "; ".join(errors))
        expected_id = "block-preparation-event-" + hashlib.sha256(
            _canonical_json({key: value for key, value in event.items() if key != "event_id"})
        ).hexdigest()
        if event["event_id"] != expected_id:
            raise BlockPreparationCostLedgerError("block event ID does not match its content")
        _verify_event_references(store, event)
        events.append(event)

    paired_block_ref = _artifact_ref(events[0]["paired_block_ref"])
    store.read_verified(paired_block_ref)
    values: dict[str, int | float] = {}
    unavailable: dict[str, str] = {}
    checkpoint_values = {checkpoint: {} for checkpoint in CHECKPOINT_IDS}
    checkpoint_unavailable = {checkpoint: {} for checkpoint in CHECKPOINT_IDS}
    close_event: dict[str, Any] | None = None
    previous_id = None
    for sequence, event in enumerate(events):
        if event["paired_block_ref"] != paired_block_ref.to_dict():
            raise BlockPreparationCostLedgerError("paired-block identity mismatch")
        if event["sequence"] != sequence or event["parent_event_id"] != previous_id:
            raise BlockPreparationCostLedgerError("block event sequence or parent chain mismatch")
        expected_key = (
            f"block-preparation-events/{paired_block_ref.sha256}/"
            f"{sequence:06d}-{event['event_id']}"
        )
        if references[sequence].key != expected_key:
            raise BlockPreparationCostLedgerError("block event reference key mismatch")
        previous_id = event["event_id"]
        if event["event_kind"] == "accounting_closed":
            if sequence != len(events) - 1 or close_event is not None:
                raise BlockPreparationCostLedgerError("accounting close must be the unique final event")
            close_event = event
            continue
        _validate_delta(event["cost_delta"], event["unavailable_axes"])
        _accumulate_delta(values, unavailable, event["cost_delta"], event["unavailable_axes"])
        checkpoint_id = event["checkpoint_id"]
        if checkpoint_id not in CHECKPOINT_IDS:
            raise BlockPreparationCostLedgerError("cost event has invalid checkpoint")
        _accumulate_delta(
            checkpoint_values[checkpoint_id],
            checkpoint_unavailable[checkpoint_id],
            event["cost_delta"],
            event["unavailable_axes"],
        )
    if close_event is None:
        raise BlockPreparationCostLedgerError("block cost stream is not closed")

    declared = close_event["cost_delta"]
    declared_unavailable = close_event["unavailable_axes"]
    for axis, reason in unavailable.items():
        if declared_unavailable.get(axis) != reason:
            raise BlockPreparationCostLedgerError(
                f"declared {axis} unavailable reason does not match raw events"
            )
    resolved_unavailable = {**unavailable, **declared_unavailable}
    actual_axes = _axis_results(values, resolved_unavailable, declared)
    checkpoint_axes = {
        checkpoint: _axis_results(
            checkpoint_values[checkpoint], checkpoint_unavailable[checkpoint], None
        )
        for checkpoint in CHECKPOINT_IDS
    }
    event_ids = [event["event_id"] for event in events]
    return ReplayedBlockPreparation(
        paired_block_ref=paired_block_ref,
        event_refs=references,
        events=tuple(events),
        checkpoint_axes=checkpoint_axes,
        actual_axes=actual_axes,
        source_events_sha256=hashlib.sha256(_canonical_json(event_ids)).hexdigest(),
    )


def _axis_results(
    values: Mapping[str, int | float],
    unavailable: Mapping[str, str],
    declared: Mapping[str, int | float | None] | None,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for axis in COST_AXES:
        expected = None if axis in unavailable else values.get(axis, 0)
        if declared is not None and declared[axis] != expected:
            raise BlockPreparationCostLedgerError(
                f"declared {axis} close totals do not match raw events"
            )
        results[axis] = (
            {"status": "unavailable", "value": None, "reason": unavailable[axis]}
            if axis in unavailable
            else {"status": "measured", "value": expected, "reason": None}
        )
    return results


def _verified_references(store: ArtifactStore, refs: Iterable[ArtifactRef]) -> tuple[ArtifactRef, ...]:
    references = tuple(refs)
    for reference in references:
        store.read_verified(reference)
    return references


def _verify_event_references(store: ArtifactStore, event: Mapping[str, Any]) -> None:
    for field in ("input_artifact_refs", "output_artifact_refs"):
        for payload in event[field]:
            reference = _artifact_ref(payload)
            if store.read_verified(reference) is None:
                raise BlockPreparationCostLedgerError("event artifact reference is unreadable")
    for field in ("input_artifact_hashes", "output_artifact_hashes"):
        if any(not isinstance(digest, str) or len(digest) != 64 for digest in event[field]):
            raise BlockPreparationCostLedgerError("event artifact hash is invalid")
    provenance = event["model_gateway_provenance_ref"]
    if provenance is not None:
        try:
            store.read_verified(_artifact_ref(provenance))
        except (ArtifactIntegrityError, KeyError, TypeError, ValueError) as exc:
            raise BlockPreparationCostLedgerError(
                "model gateway provenance reference is unreadable"
            ) from exc


def _artifact_ref(payload: Mapping[str, Any]) -> ArtifactRef:
    return ArtifactRef(
        key=payload["key"],
        sha256=payload["sha256"],
        size_bytes=payload["size_bytes"],
        media_type=payload["media_type"],
    )


def _event_id_from_ref(store: ArtifactStore, reference: ArtifactRef) -> str:
    payload = json.loads(store.read_verified(reference))
    event_id = payload.get("event_id") if isinstance(payload, dict) else None
    if not isinstance(event_id, str):
        raise BlockPreparationCostLedgerError("previous block event has no event ID")
    return event_id


def _validate_delta(
    cost_delta: Mapping[str, int | float | None], unavailable_axes: Mapping[str, str]
) -> None:
    if not cost_delta:
        raise BlockPreparationCostLedgerError("cost delta must be non-empty")
    unknown = set(cost_delta) - set(COST_AXES)
    if unknown:
        raise BlockPreparationCostLedgerError("unknown cost axis: " + ", ".join(sorted(unknown)))
    null_axes = {axis for axis, value in cost_delta.items() if value is None}
    if null_axes != set(unavailable_axes):
        raise BlockPreparationCostLedgerError(
            "null cost axes and unavailable reasons must match exactly"
        )
    for axis, value in cost_delta.items():
        if value is None:
            if not isinstance(unavailable_axes[axis], str) or not unavailable_axes[axis]:
                raise BlockPreparationCostLedgerError(
                    f"unavailable reason must be non-empty: {axis}"
                )
        else:
            _require_axis_value(axis, value, allow_zero=True)


def _require_axis_value(axis: str, value: int | float, *, allow_zero: bool = False) -> None:
    if axis not in COST_AXES:
        raise BlockPreparationCostLedgerError(f"unknown cost axis: {axis}")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BlockPreparationCostLedgerError(f"cost value must be numeric: {axis}")
    if value < 0 or (not allow_zero and value == 0):
        raise BlockPreparationCostLedgerError(f"cost value must be non-negative: {axis}")
    if axis in COUNT_COST_AXES and not isinstance(value, int):
        raise BlockPreparationCostLedgerError(f"count cost must be an integer: {axis}")


def _accumulate_delta(
    values: dict[str, int | float],
    unavailable: dict[str, str],
    cost_delta: Mapping[str, int | float | None],
    unavailable_axes: Mapping[str, str],
) -> None:
    for axis, value in cost_delta.items():
        if value is None:
            reason = unavailable_axes[axis]
            existing = unavailable.get(axis)
            if existing is not None and existing != reason:
                raise BlockPreparationCostLedgerError(
                    f"conflicting unavailable reasons for {axis}"
                )
            unavailable[axis] = reason
        elif axis not in unavailable:
            values[axis] = values.get(axis, 0) + value


def _sorted_hashes(values: Iterable[str]) -> tuple[str, ...]:
    hashes = tuple(sorted(set(values)))
    for digest in hashes:
        if not isinstance(digest, str) or len(digest) != 64:
            raise BlockPreparationCostLedgerError("artifact hash must be SHA-256")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise BlockPreparationCostLedgerError("artifact hash must be SHA-256") from exc
    return hashes


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
