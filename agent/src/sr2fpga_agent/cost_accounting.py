"""Write-once attempt-cost events and deterministic cost reconciliation."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from sr2fpga_agent.models import compact_json_bytes as _canonical_json
from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.evaluator_dispatch import (
    read_verified_development_hidden_conformance_outcome,
)
from sr2fpga_agent.method_contract import method_policy_sha256
from sr2fpga_agent.public_evaluator import (
    read_verified_development_authoritative_attempt_public_outcome,
    read_verified_development_public_outcome,
)
from sr2fpga_agent.terminal_selection import (
    read_verified_development_terminal_selection,
)
from sr2fpga_agent.contract_registry import ContractRegistry


COUNT_COST_AXES = (
    "logical_model_calls",
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "provider_transport_attempts",
    "planner_parser_schema_retries",
    "outer_repair_attempts",
    "public_tool_calls",
    "hidden_evaluator_tool_calls",
    "hidden_infrastructure_retries",
)
DURATION_COST_AXES = (
    "wall_time",
    "eda_time",
    "hidden_evaluator_runtime",
)
COST_AXES = COUNT_COST_AXES + DURATION_COST_AXES
ACCOUNTING_FAILURE_ORIGINS = frozenset(
    {
        "natural_llm",
        "synthetic_injected",
        "deterministic",
        "deterministic_template",
        "compositional_assembly",
    }
)


class CostAccountingError(ValueError):
    pass


@dataclass(frozen=True)
class ReconciledCostSummary:
    payload: dict[str, Any]
    artifact_ref: ArtifactRef


@dataclass(frozen=True)
class ReconciledTrajectory:
    payload: dict[str, Any]
    artifact_ref: ArtifactRef


class AttemptCostLedger:
    """Append registered cost events for one episode attempt."""

    def __init__(
        self,
        store: ArtifactStore,
        *,
        episode_id: str,
        attempt_id: str,
        method_condition: str,
        failure_origin: str | None,
        candidate_id: str | None = None,
        input_artifact_hashes: Iterable[str] = (),
    ) -> None:
        self.store = store
        self.episode_id = episode_id
        self.attempt_id = attempt_id
        self.method_condition = method_condition
        self.failure_origin = validate_accounting_failure_origin(failure_origin)
        self.candidate_id = candidate_id
        self.input_artifact_hashes = tuple(sorted(set(input_artifact_hashes)))
        self._refs: list[ArtifactRef] = []
        self._values: dict[str, int | float] = {}
        self._unavailable: dict[str, str] = {}
        self._closed = False

    @property
    def event_refs(self) -> tuple[ArtifactRef, ...]:
        return tuple(self._refs)

    @property
    def observed_axes(self) -> frozenset[str]:
        return frozenset(set(self._values) | set(self._unavailable))

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
        return self._append(
            stage=stage,
            visibility_class=visibility_class,
            event_type="budget_reserved",
            status="reserved",
            started_at=started_at,
            duration_seconds=None,
            budget_reservation={
                "axis": axis,
                "amount": amount,
                "limit": limit,
                "used_after": used_after,
            },
            cost_delta={axis: amount},
            unavailable_axes={},
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
        return self._append(
            stage=stage,
            visibility_class=visibility_class,
            event_type="budget_exhausted",
            status="exhausted",
            started_at=started_at,
            duration_seconds=None,
            budget_reservation={
                "axis": axis,
                "amount": amount,
                "limit": limit,
                "used_after": used_after,
            },
            cost_delta={axis: 0},
            unavailable_axes={},
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
            raise CostAccountingError("axis-cost status must be completed or failed")
        return self._append(
            stage=stage,
            visibility_class=visibility_class,
            event_type="axis_cost",
            status=status,
            started_at=started_at,
            duration_seconds=duration_seconds,
            budget_reservation=None,
            cost_delta=dict(cost_delta),
            unavailable_axes=dict(unavailable_axes or {}),
            input_artifact_hashes=tuple(input_artifact_hashes),
            output_artifact_hashes=tuple(output_artifact_hashes),
        )

    def close(
        self,
        *,
        zero_axes: Iterable[str] = (),
        unavailable_axes: Mapping[str, str] | None = None,
        started_at: float | None = None,
    ) -> ArtifactRef:
        if self._closed:
            raise CostAccountingError("attempt cost ledger is already closed")
        declared_zero = set(zero_axes)
        declared_unavailable = dict(unavailable_axes or {})
        unknown = (declared_zero | set(declared_unavailable)) - set(COST_AXES)
        if unknown:
            raise CostAccountingError(
                "unknown close axis: " + ", ".join(sorted(unknown))
            )
        already_observed = set(self._values) | set(self._unavailable)
        overlap = already_observed & (declared_zero | set(declared_unavailable))
        if overlap:
            raise CostAccountingError(
                "close axis was already observed: " + ", ".join(sorted(overlap))
            )
        missing = set(COST_AXES) - already_observed - declared_zero - set(declared_unavailable)
        if missing:
            raise CostAccountingError(
                "close must classify every unobserved cost axis: "
                + ", ".join(sorted(missing))
            )
        for axis, reason in declared_unavailable.items():
            if not isinstance(reason, str) or not reason:
                raise CostAccountingError(f"unavailable reason must be non-empty: {axis}")
        totals: dict[str, int | float | None] = {}
        reasons = {**self._unavailable, **declared_unavailable}
        for axis in COST_AXES:
            totals[axis] = None if axis in reasons else self._values.get(axis, 0)
        reference = self._append(
            stage="accounting_close",
            visibility_class="accounting",
            event_type="accounting_closed",
            status="closed",
            started_at=started_at,
            duration_seconds=None,
            budget_reservation=None,
            cost_delta=totals,
            unavailable_axes=reasons,
        )
        self._closed = True
        return reference

    def _append(
        self,
        *,
        stage: str,
        visibility_class: str,
        event_type: str,
        status: str,
        started_at: float | None,
        duration_seconds: float | None,
        budget_reservation: Mapping[str, Any] | None,
        cost_delta: Mapping[str, int | float | None],
        unavailable_axes: Mapping[str, str],
        input_artifact_hashes: tuple[str, ...] = (),
        output_artifact_hashes: tuple[str, ...] = (),
    ) -> ArtifactRef:
        if self._closed:
            raise CostAccountingError("cannot append after accounting close")
        _validate_delta(cost_delta, unavailable_axes)
        sequence = len(self._refs)
        event: dict[str, Any] = {
            "contract_version": "attempt-event-v1",
            "parent_event_id": (
                _event_id_from_ref(self.store, self._refs[-1]) if self._refs else None
            ),
            "sequence": sequence,
            "episode_id": self.episode_id,
            "candidate_id": self.candidate_id,
            "attempt_id": self.attempt_id,
            "method_condition": self.method_condition,
            "stage": stage,
            "visibility_class": visibility_class,
            "event_type": event_type,
            "status": status,
            "started_at": time.time() if started_at is None else started_at,
            "duration_seconds": duration_seconds,
            "input_artifact_hashes": sorted(
                set(self.input_artifact_hashes) | set(input_artifact_hashes)
            ),
            "output_artifact_hashes": sorted(set(output_artifact_hashes)),
            "budget_reservation": (
                dict(budget_reservation) if budget_reservation is not None else None
            ),
            "cost_delta": dict(cost_delta),
            "unavailable_axes": dict(unavailable_axes),
            "failure_origin": self.failure_origin,
        }
        event["event_id"] = "attempt-event-" + hashlib.sha256(
            _canonical_json(event)
        ).hexdigest()
        reference = self.store.put_validated_json(
            f"attempt-events/{self.episode_id}/{self.attempt_id}/{sequence:06d}",
            event,
            contract_key="attempt_event",
        )
        self._refs.append(reference)
        if event_type != "accounting_closed":
            _accumulate_delta(self._values, self._unavailable, cost_delta, unavailable_axes)
        return reference


class AttemptCostLedgerRouter:
    """Route shared model/tool wrappers to the currently active attempt."""

    def __init__(self) -> None:
        self._active: AttemptCostLedger | None = None

    def activate(self, ledger: AttemptCostLedger) -> None:
        if self._active is not None:
            raise CostAccountingError("an attempt cost ledger is already active")
        self._active = ledger

    def current(self) -> AttemptCostLedger | None:
        return self._active

    def deactivate(self, ledger: AttemptCostLedger) -> None:
        if self._active is not ledger:
            raise CostAccountingError("attempt cost ledger router ownership mismatch")
        self._active = None


class AccountingCommandRunner:
    """Count every delegated external tool invocation on the active attempt."""

    def __init__(self, delegate: Any, router: AttemptCostLedgerRouter) -> None:
        self._delegate = delegate
        self._router = router

    def run(
        self,
        command: list[str],
        cwd: Any,
        stage: str,
        timeout_seconds: int = 30,
    ) -> Any:
        started = time.monotonic()
        try:
            result = self._delegate.run(
                command,
                cwd,
                stage,
                timeout_seconds=timeout_seconds,
            )
        except Exception:
            self._record(stage, time.monotonic() - started, status="failed")
            raise
        duration = getattr(result, "duration_seconds", time.monotonic() - started)
        status = "completed" if getattr(result, "status", None) == "passed" else "failed"
        self._record(stage, duration, status=status)
        return result

    def _record(self, stage: str, duration: float, *, status: str) -> None:
        ledger = self._router.current()
        if ledger is None:
            return
        ledger.record_cost(
            stage=stage,
            visibility_class="public",
            status=status,
            duration_seconds=max(0.0, float(duration)),
            cost_delta={
                "public_tool_calls": 1,
                "eda_time": max(0.0, float(duration)),
            },
        )


def validate_accounting_failure_origin(value: str | None) -> str | None:
    """Validate the closed candidate-source taxonomy used by cost lineage."""

    if value is not None and value not in ACCOUNTING_FAILURE_ORIGINS:
        raise CostAccountingError(f"unknown accounting failure origin: {value}")
    return value

def reconcile_cost_events(
    store: ArtifactStore,
    event_refs: Iterable[ArtifactRef],
    *,
    summary_key: str | None = None,
    registry: ContractRegistry | None = None,
) -> ReconciledCostSummary:
    """Rebuild one cost summary solely from verified attempt events."""

    references = tuple(event_refs)
    if not references:
        raise CostAccountingError("cost reconciliation requires attempt events")
    contract_registry = registry or ContractRegistry()
    event_contract = contract_registry.load_schema("attempt_event")
    events: list[dict[str, Any]] = []
    for reference in references:
        try:
            event = json.loads(store.read_verified(reference))
        except json.JSONDecodeError as exc:
            raise CostAccountingError("attempt event is not valid JSON") from exc
        errors = event_contract.validate(event)
        if errors:
            raise CostAccountingError("invalid attempt event: " + "; ".join(errors))
        expected_id = "attempt-event-" + hashlib.sha256(
            _canonical_json({key: value for key, value in event.items() if key != "event_id"})
        ).hexdigest()
        if event["event_id"] != expected_id:
            raise CostAccountingError("attempt event ID does not match its content")
        events.append(event)

    first = events[0]
    identity = (
        first["episode_id"],
        first["attempt_id"],
        first["method_condition"],
    )
    previous_id = None
    values: dict[str, int | float] = {}
    unavailable: dict[str, str] = {}
    close_event: dict[str, Any] | None = None
    for sequence, event in enumerate(events):
        if (
            event["episode_id"],
            event["attempt_id"],
            event["method_condition"],
        ) != identity:
            raise CostAccountingError("attempt event identity mismatch")
        if event["sequence"] != sequence or event["parent_event_id"] != previous_id:
            raise CostAccountingError("attempt event sequence or parent chain mismatch")
        expected_key = f"attempt-events/{identity[0]}/{identity[1]}/{sequence:06d}"
        if references[sequence].key != expected_key:
            raise CostAccountingError("attempt event reference key mismatch")
        previous_id = event["event_id"]
        if event["event_type"] == "accounting_closed":
            if sequence != len(events) - 1 or close_event is not None:
                raise CostAccountingError("accounting close must be the unique final event")
            close_event = event
            continue
        _validate_delta(event["cost_delta"], event["unavailable_axes"])
        _accumulate_delta(
            values,
            unavailable,
            event["cost_delta"],
            event["unavailable_axes"],
        )
    if close_event is None:
        raise CostAccountingError("attempt cost stream is not closed")

    declared = close_event["cost_delta"]
    declared_unavailable = close_event["unavailable_axes"]
    for axis, reason in unavailable.items():
        if declared_unavailable.get(axis) != reason:
            raise CostAccountingError(
                f"declared {axis} unavailable reason does not match raw events"
            )
    reconciled_unavailable = {**unavailable, **declared_unavailable}
    axes: dict[str, dict[str, Any]] = {}
    for axis in COST_AXES:
        expected = None if axis in reconciled_unavailable else values.get(axis, 0)
        if declared[axis] != expected:
            raise CostAccountingError(f"declared {axis} total does not match raw events")
        if axis in reconciled_unavailable:
            axes[axis] = {
                "status": "unavailable",
                "value": None,
                "reason": reconciled_unavailable[axis],
            }
        else:
            axes[axis] = {"status": "measured", "value": expected, "reason": None}

    event_ids = [event["event_id"] for event in events]
    payload = {
        "contract_version": "cost-summary-v1",
        "episode_id": identity[0],
        "attempt_id": identity[1],
        "method_condition": identity[2],
        "source_event_ids": event_ids,
        "source_events_sha256": hashlib.sha256(_canonical_json(event_ids)).hexdigest(),
        "event_count": len(events),
        "failure_count": sum(event["status"] == "failed" for event in events),
        "budget_exhaustion_count": sum(
            event["event_type"] == "budget_exhausted" for event in events
        ),
        "accounting_closed": True,
        "all_required_axes_reconciled": not reconciled_unavailable,
        "axes": axes,
    }
    key = summary_key or f"cost-summaries/{identity[0]}/{identity[1]}"
    reference = store.put_validated_json(
        key,
        payload,
        contract_key="cost_summary",
        registry=contract_registry,
    )
    return ReconciledCostSummary(payload, reference)


def reconcile_attempt_trajectory(
    store: ArtifactStore,
    cost_summary_refs: Iterable[ArtifactRef],
    *,
    terminal_candidate_ref: ArtifactRef | None = None,
    terminal_candidate_missing_reason: str = "terminal_candidate_ref_missing",
    development_hidden_outcome_ref: Mapping[str, str] | None = None,
    development_hidden_conformance_outcome_ref: ArtifactRef | None = None,
    development_terminal_selection_ref: ArtifactRef | None = None,
    development_selected_public_outcome_ref: ArtifactRef | None = None,
    development_terminal_public_outcome_ref: ArtifactRef | None = None,
    registry: ContractRegistry | None = None,
) -> ReconciledTrajectory:
    """Build trajectory-v2 only from verified events, summaries, and an optional seal."""

    references = tuple(cost_summary_refs)
    if not references:
        raise CostAccountingError("trajectory reconciliation requires cost summaries")
    contract_registry = registry or ContractRegistry()
    summary_contract = contract_registry.load_schema("cost_summary")
    trajectory_contract = contract_registry.load_schema("trajectory_v2")
    summaries: list[tuple[ArtifactRef, dict[str, Any]]] = []
    for reference in references:
        try:
            summary = json.loads(store.read_verified(reference))
        except json.JSONDecodeError as exc:
            raise CostAccountingError("cost summary is not valid JSON") from exc
        errors = summary_contract.validate(summary)
        if errors:
            raise CostAccountingError("invalid cost summary: " + "; ".join(errors))
        summaries.append((reference, summary))
    summaries.sort(key=lambda item: item[1]["attempt_id"])

    first = summaries[0][1]
    identity = (first["episode_id"], first["method_condition"])
    attempts: list[dict[str, Any]] = []
    failure_origins: set[str | None] = set()
    missing: list[str] = []
    seen_attempt_ids: set[str] = set()
    for summary_ref, summary in summaries:
        if (summary["episode_id"], summary["method_condition"]) != identity:
            raise CostAccountingError("trajectory cost-summary identity mismatch")
        attempt_id = summary["attempt_id"]
        if attempt_id in seen_attempt_ids:
            raise CostAccountingError("trajectory contains duplicate attempt summary")
        seen_attempt_ids.add(attempt_id)
        expected_summary_key = f"cost-summaries/{identity[0]}/{attempt_id}"
        if summary_ref.key != expected_summary_key:
            raise CostAccountingError("trajectory cost-summary reference key mismatch")

        event_refs: list[ArtifactRef] = []
        for sequence in range(summary["event_count"]):
            key = f"attempt-events/{identity[0]}/{attempt_id}/{sequence:06d}"
            event_ref = store.reference(key)
            if event_ref is None:
                raise CostAccountingError(f"trajectory source event is missing: {key}")
            event_refs.append(event_ref)
        rebuilt = reconcile_cost_events(
            store,
            event_refs,
            summary_key=summary_ref.key,
            registry=contract_registry,
        )
        if rebuilt.artifact_ref != summary_ref or rebuilt.payload != summary:
            raise CostAccountingError("trajectory cost summary does not match raw events")

        events = [json.loads(store.read_verified(reference)) for reference in event_refs]
        if [event["event_id"] for event in events] != summary["source_event_ids"]:
            raise CostAccountingError("trajectory event IDs do not match cost summary")
        candidate_ids = {event["candidate_id"] for event in events}
        if len(candidate_ids) != 1:
            raise CostAccountingError("trajectory attempt candidate identity mismatch")
        attempt_failure_origins = {event["failure_origin"] for event in events}
        if len(attempt_failure_origins) != 1:
            raise CostAccountingError("trajectory attempt failure-origin mismatch")
        candidate_id = next(iter(candidate_ids))
        failure_origins.update(attempt_failure_origins)
        input_hashes = sorted(
            {value for event in events for value in event["input_artifact_hashes"]}
        )
        output_hashes = sorted(
            {value for event in events for value in event["output_artifact_hashes"]}
        )
        if candidate_id is None:
            missing.append(f"{attempt_id}:candidate_id_missing")
        if not output_hashes:
            missing.append(f"{attempt_id}:candidate_output_hash_missing")
        attempts.append(
            {
                "attempt_id": attempt_id,
                "candidate_id": candidate_id,
                "input_artifact_hashes": input_hashes,
                "output_artifact_hashes": output_hashes,
                "attempt_event_refs": [reference.to_dict() for reference in event_refs],
                "cost_summary_ref": summary_ref.to_dict(),
                "source_events_sha256": summary["source_events_sha256"],
                "accounting_closed": True,
            }
        )

    if len(failure_origins) != 1:
        raise CostAccountingError("trajectory failure-origin mismatch across attempts")
    terminal_ref_payload = None
    if terminal_candidate_ref is None:
        if not terminal_candidate_missing_reason:
            raise CostAccountingError("terminal candidate missing reason must be non-empty")
        missing.append(terminal_candidate_missing_reason)
    else:
        try:
            terminal_candidate = json.loads(store.read_verified(terminal_candidate_ref))
        except json.JSONDecodeError as exc:
            raise CostAccountingError("terminal candidate is not valid JSON") from exc
        errors = contract_registry.load_schema("terminal_candidate").validate(
            terminal_candidate
        )
        if errors:
            raise CostAccountingError("invalid terminal candidate: " + "; ".join(errors))
        if (
            terminal_candidate["episode_id"],
            terminal_candidate["method_condition_id"],
        ) != identity:
            raise CostAccountingError("terminal candidate trajectory identity mismatch")
        if development_terminal_selection_ref is None:
            final_candidate_id = attempts[-1]["candidate_id"]
            if final_candidate_id != terminal_candidate["candidate_id"]:
                raise CostAccountingError("terminal candidate does not match final attempt")
        terminal_ref_payload = terminal_candidate_ref.to_dict()

    selection_ref_payload = None
    selected_public_ref_payload = None
    terminal_public_ref_payload = None
    terminal_public = None
    if development_terminal_selection_ref is not None:
        if terminal_candidate_ref is None or development_selected_public_outcome_ref is None:
            raise CostAccountingError(
                "development terminal selection requires terminal and selected public refs"
            )
        try:
            selection = read_verified_development_terminal_selection(
                store, development_terminal_selection_ref, registry=contract_registry
            )
            selected_public = (
                read_verified_development_authoritative_attempt_public_outcome(
                    store,
                    development_selected_public_outcome_ref,
                    registry=contract_registry,
                )
            )
            terminal_candidate = json.loads(store.read_verified(terminal_candidate_ref))
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise CostAccountingError("invalid development terminal selection lineage") from exc
        if (selection["episode_id"], selection["method_condition"]) != identity:
            raise CostAccountingError("development terminal selection identity mismatch")
        if selection["selected_candidate_id"] != terminal_candidate["candidate_id"]:
            raise CostAccountingError("terminal candidate does not match development selection")
        selected_attempt = next(
            (
                attempt
                for attempt in attempts
                if attempt["attempt_id"] == selection["selected_attempt_id"]
            ),
            None,
        )
        if selected_attempt is None or selected_attempt["candidate_id"] != selection[
            "selected_candidate_id"
        ]:
            raise CostAccountingError("selected terminal is absent from trajectory attempts")
        if selection["selected_public_outcome_ref"] != (
            development_selected_public_outcome_ref.to_dict()
        ):
            raise CostAccountingError("selected public outcome reference mismatch")
        if selected_public["outcome_id"] != json.loads(
            store.read_verified(development_selected_public_outcome_ref)
        )["outcome_id"]:
            raise CostAccountingError("selected public outcome content mismatch")
        selection_ref_payload = development_terminal_selection_ref.to_dict()
        selected_public_ref_payload = development_selected_public_outcome_ref.to_dict()
    elif development_selected_public_outcome_ref is not None:
        raise CostAccountingError("selected public outcome requires terminal selection")

    if development_terminal_public_outcome_ref is not None:
        if (
            terminal_candidate_ref is None
            or development_selected_public_outcome_ref is None
        ):
            raise CostAccountingError(
                "terminal public outcome requires terminal candidate and selected public outcome"
            )
        try:
            terminal_public = read_verified_development_public_outcome(
                store,
                development_terminal_public_outcome_ref,
                registry=contract_registry,
            )
        except (KeyError, ValueError) as exc:
            raise CostAccountingError("invalid terminal public outcome lineage") from exc
        if terminal_public["terminal_candidate_sha256"] != terminal_candidate_ref.sha256:
            raise CostAccountingError("terminal public outcome candidate hash mismatch")
        if (terminal_public["episode_id"], terminal_public["method_condition"]) != identity:
            raise CostAccountingError("terminal public outcome identity mismatch")
        if terminal_public["stage_outcomes"] != selected_public["stage_outcomes"]:
            raise CostAccountingError(
                "selected and terminal public stage outcomes disagree"
            )
        if terminal_public.get("public_l2_harness") != selected_public.get(
            "public_l2_harness"
        ):
            raise CostAccountingError(
                "selected and terminal public L2 harness commitments disagree"
            )
        if terminal_public["public_acceptance"] != selected_public["public_acceptance"]:
            raise CostAccountingError(
                "selected and terminal public acceptance disagree"
            )
        terminal_public_ref_payload = development_terminal_public_outcome_ref.to_dict()

    hidden_conformance_ref_payload = None
    if development_hidden_conformance_outcome_ref is not None:
        if development_hidden_outcome_ref is None or terminal_candidate_ref is None:
            raise CostAccountingError(
                "hidden conformance outcome requires opaque hidden and terminal refs"
            )
        try:
            hidden_conformance = (
                read_verified_development_hidden_conformance_outcome(
                    store,
                    development_hidden_conformance_outcome_ref,
                    registry=contract_registry,
                )
            )
        except (KeyError, ValueError) as exc:
            raise CostAccountingError("invalid hidden conformance outcome lineage") from exc
        if (
            hidden_conformance["episode_id"],
            hidden_conformance["method_condition"],
        ) != identity:
            raise CostAccountingError("hidden conformance outcome identity mismatch")
        if hidden_conformance["terminal_candidate_sha256"] != terminal_candidate_ref.sha256:
            raise CostAccountingError("hidden conformance terminal candidate mismatch")
        if hidden_conformance["opaque_outcome_ref"] != dict(
            development_hidden_outcome_ref
        ):
            raise CostAccountingError("hidden conformance opaque reference mismatch")
        if hidden_conformance["public_contract_sha256"] != method_policy_sha256(
            identity[1]
        ):
            raise CostAccountingError("hidden conformance method contract mismatch")
        if hidden_conformance["public_profile_sha256"] != terminal_candidate[
            "requirement_projection_sha256"
        ]:
            raise CostAccountingError("hidden conformance requirement profile mismatch")
        if terminal_public is not None and (
            hidden_conformance["public_contract_sha256"],
            hidden_conformance["public_profile_sha256"],
            hidden_conformance["tool_environment_policy_sha256"],
        ) != (
            terminal_public["public_contract_sha256"],
            terminal_public["public_profile_sha256"],
            terminal_public["tool_environment_policy_sha256"],
        ):
            raise CostAccountingError("public and hidden conformance commitments disagree")
        hidden_conformance_ref_payload = (
            development_hidden_conformance_outcome_ref.to_dict()
        )

    without_id = {
        "contract_version": "trajectory-v2",
        "episode_id": identity[0],
        "method_condition": identity[1],
        "failure_origin": next(iter(failure_origins)),
        "attempts": attempts,
        "terminal_candidate_ref": terminal_ref_payload,
        "development_hidden_outcome_ref": (
            dict(development_hidden_outcome_ref)
            if development_hidden_outcome_ref is not None
            else None
        ),
        "development_terminal_selection_ref": selection_ref_payload,
        "development_selected_public_outcome_ref": selected_public_ref_payload,
        "development_terminal_public_outcome_ref": terminal_public_ref_payload,
        "lineage_complete": not missing,
        "missing_lineage_reasons": sorted(missing),
    }
    if hidden_conformance_ref_payload is not None:
        without_id["development_hidden_conformance_outcome_ref"] = (
            hidden_conformance_ref_payload
        )
    payload = {
        **without_id,
        "trajectory_id": "trajectory-v2-" + hashlib.sha256(
            _canonical_json(without_id)
        ).hexdigest(),
    }
    errors = trajectory_contract.validate(payload)
    if errors:
        raise CostAccountingError("invalid trajectory-v2: " + "; ".join(errors))
    reference = store.put_validated_json(
        f"trajectories/{identity[0]}/{identity[1]}",
        payload,
        contract_key="trajectory_v2",
        registry=contract_registry,
    )
    return ReconciledTrajectory(payload, reference)


def _event_id_from_ref(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    error: type[ValueError] = CostAccountingError,
    label: str = "previous attempt event",
) -> str:
    payload = json.loads(store.read_verified(reference))
    event_id = payload.get("event_id") if isinstance(payload, dict) else None
    if not isinstance(event_id, str):
        raise error(f"{label} has no event ID")
    return event_id


def _validate_delta(
    cost_delta: Mapping[str, int | float | None],
    unavailable_axes: Mapping[str, str],
    *,
    error: type[ValueError] = CostAccountingError,
) -> None:
    if not cost_delta:
        raise error("cost delta must be non-empty")
    unknown = set(cost_delta) - set(COST_AXES)
    if unknown:
        raise error("unknown cost axis: " + ", ".join(sorted(unknown)))
    null_axes = {axis for axis, value in cost_delta.items() if value is None}
    if null_axes != set(unavailable_axes):
        raise error("null cost axes and unavailable reasons must match exactly")
    for axis, value in cost_delta.items():
        if value is None:
            reason = unavailable_axes.get(axis)
            if not isinstance(reason, str) or not reason:
                raise error(f"unavailable reason must be non-empty: {axis}")
            continue
        _require_axis_value(axis, value, allow_zero=True, error=error)


def _require_axis_value(
    axis: str,
    value: int | float,
    *,
    allow_zero: bool = False,
    error: type[ValueError] = CostAccountingError,
) -> None:
    if axis not in COST_AXES:
        raise error(f"unknown cost axis: {axis}")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise error(f"cost value must be numeric: {axis}")
    if value < 0 or (not allow_zero and value == 0):
        raise error(f"cost value must be non-negative: {axis}")
    if axis in COUNT_COST_AXES and not isinstance(value, int):
        raise error(f"count cost must be an integer: {axis}")


def _accumulate_delta(
    values: dict[str, int | float],
    unavailable: dict[str, str],
    cost_delta: Mapping[str, int | float | None],
    unavailable_axes: Mapping[str, str],
    *,
    error: type[ValueError] = CostAccountingError,
) -> None:
    for axis, value in cost_delta.items():
        if value is None:
            reason = unavailable_axes[axis]
            existing = unavailable.get(axis)
            if existing is not None and existing != reason:
                raise error(f"conflicting unavailable reasons for {axis}")
            unavailable[axis] = reason
        elif axis not in unavailable:
            values[axis] = values.get(axis, 0) + value


