"""Persistent PC 2.1 resource reservations and shared-method cost attribution.

The controller must reserve before a side effect, durably dispatch, then
reconcile measured usage. Reservations are bounds, never measured token usage.
All consumers of a shared operation are charged its full standalone cost while
the actual view counts that operation once. Limits do not authorize execution.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields
import hashlib
import json
import math
from pathlib import Path
import threading
from types import MappingProxyType
from typing import Any, Iterator, Mapping, Sequence

from sr2fpga_agent.artifact_store import ArtifactIntegrityError, ArtifactStore
from sr2fpga_agent.models import canonical_json_bytes


B4_MODEL_CALLS = {"M0": 1, "M1": 4, "M2": 2, "M3": 2, "M4": 2, "M5": 4}
B4_PUBLIC_CYCLES = {method: 4 if method in {"M1", "M5"} else 1 for method in B4_MODEL_CALLS}
RESOURCE_LIMITS = {
    "model_calls": "max_model_calls",
    "input_tokens": "max_total_input_tokens",
    "output_tokens": "max_total_output_tokens",
    "context_tokens": "max_context_tokens",
    "public_tool_calls": "max_public_tool_calls",
    "public_cycles": "max_public_cycles",
    "final_public_tool_calls": "max_final_public_tool_calls",
    "hidden_tool_calls": "max_hidden_tool_calls",
    "active_seconds": "max_active_seconds",
    "eda_seconds": "max_eda_seconds",
    "cpu_seconds": "max_cpu_seconds",
    "memory_bytes": "max_memory_bytes",
}
PEAK_AXES = frozenset({"context_tokens", "memory_bytes"})
TIME_AXES = frozenset({"active_seconds", "eda_seconds", "cpu_seconds"})
FINAL_OUTCOMES = frozenset({"completed", "failed"})
_THREAD_LOCKS: dict[str, threading.Lock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()


class BudgetError(RuntimeError):
    """Invalid budget operation; it does not grant a retry or new allowance."""


class BudgetExceeded(BudgetError):
    """An operation was rejected before dispatch because a limit would be crossed."""


class BudgetBusy(BudgetError):
    """A concurrent transaction owns the ledger; caller may retry before dispatch."""


def _number(value: Any, axis: str) -> int | float:
    if axis in TIME_AXES:
        if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
            raise ValueError(f"{axis} must be a finite nonnegative number")
    elif type(value) is not int or value < 0:
        raise ValueError(f"{axis} must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class BudgetLimits:
    max_model_calls: int
    max_total_input_tokens: int
    max_total_output_tokens: int
    max_single_output_tokens: int
    max_context_tokens: int
    max_public_tool_calls: int
    max_public_cycles: int
    max_active_seconds: float
    max_eda_seconds: float
    max_cpu_seconds: float
    max_memory_bytes: int
    max_final_public_tool_calls: int = 0
    max_hidden_tool_calls: int = 0

    def __post_init__(self) -> None:
        reverse = {limit: axis for axis, limit in RESOURCE_LIMITS.items()}
        for field in fields(self):
            axis = reverse.get(field.name, "output_tokens")
            _number(getattr(self, field.name), axis)
        if self.max_model_calls and (not self.max_single_output_tokens or not self.max_context_tokens):
            raise ValueError("model calls require explicit positive single-output and context limits")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BudgetLimits":
        if set(payload) != {field.name for field in fields(cls)}:
            raise ValueError("budget limits must explicitly cover every registered resource axis")
        return cls(**dict(payload))

    @classmethod
    def for_method(cls, method: str, **limits: Any) -> "BudgetLimits":
        if method not in B4_MODEL_CALLS:
            raise ValueError("unknown method condition")
        if "max_model_calls" in limits:
            raise ValueError("for_method owns the B4 model-call ceiling")
        limits.setdefault("max_public_cycles", B4_PUBLIC_CYCLES[method])
        return cls(max_model_calls=B4_MODEL_CALLS[method], **limits)

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    operation_id: str
    consumers: tuple[str, ...]
    resources: Mapping[str, int | float]
    token_reservation_kind: str
    metadata: Mapping[str, Any]
    state: str

    def to_dict(self) -> dict[str, Any]:
        return {"reservation_id": self.reservation_id, "operation_id": self.operation_id,
                "consumers": list(self.consumers), "resources": dict(self.resources),
                "token_reservation_kind": self.token_reservation_kind,
                "metadata": dict(self.metadata), "state": self.state}


class BudgetLedger:
    """Append-only budget authority for one paired block or standalone episode.

    A file lock and an in-process lock cover check-and-append for every consumer.
    OS locks are released on process exit; no stale-lock deletion is necessary.
    Calls already marked dispatched cannot be cancelled or refunded as unused.
    The supplied worker must enforce CPU/memory and wall-time quotas externally.
    """

    def __init__(self, store: ArtifactStore, stream_id: str,
                 limits: Mapping[str, BudgetLimits], *, budget_policy_id: str = "paper1-b4-v1") -> None:
        if not isinstance(stream_id, str) or not stream_id:
            raise ValueError("budget stream identity must be nonempty")
        if budget_policy_id != "paper1-b4-v1":
            raise ValueError("unregistered budget policy")
        if not limits or any(method not in B4_MODEL_CALLS for method in limits):
            raise ValueError("budget limits require explicit M0-M5 consumers")
        normalized = {}
        for method, item in limits.items():
            if not isinstance(item, BudgetLimits):
                raise TypeError("every consumer requires BudgetLimits")
            if item.max_model_calls != B4_MODEL_CALLS[method]:
                raise ValueError(f"{method} does not match its registered B4 call allocation")
            if item.max_public_cycles > B4_PUBLIC_CYCLES[method]:
                raise ValueError(f"{method} exceeds its public-cycle allocation")
            normalized[method] = item
        self.store = store
        self.stream_id = stream_id
        self.limits = MappingProxyType(normalized)
        digest = hashlib.sha256(stream_id.encode("utf-8")).hexdigest()
        self._event_stream = "pc21-budget-" + digest
        self._configuration_key = f"pc21-budgets/{digest}/configuration"
        self._lock_path = Path(store.root) / "pc21-budget-locks" / (digest + ".lock")
        self._configuration = {
            "budget_version": "pc21-runtime-budget-v1", "stream_id": stream_id,
            "budget_policy_id": budget_policy_id,
            "limits": {name: item.to_dict() for name, item in sorted(normalized.items())},
        }
        with self._locked():
            reference = store.reference(self._configuration_key)
            encoded = canonical_json_bytes(self._configuration)
            if reference is None:
                store.put_blob(self._configuration_key, encoded, media_type="application/json")
            elif store.read_verified(reference) != encoded:
                raise BudgetError("reopening cannot change budget identity or limits")
            self._replay()

    @contextmanager
    def _locked(self) -> Iterator[None]:
        key = str(self._lock_path.resolve()).casefold()
        with _THREAD_LOCKS_GUARD:
            lock = _THREAD_LOCKS.setdefault(key, threading.Lock())
        if not lock.acquire(blocking=False):
            raise BudgetBusy("another controller transaction owns this budget ledger")
        handle = None
        acquired = False
        try:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            handle = self._lock_path.open("a+b")
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if __import__("os").name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise BudgetBusy("another controller process owns this budget ledger") from error
            acquired = True
            yield
        finally:
            if handle is not None:
                if acquired:
                    handle.seek(0)
                    if __import__("os").name == "nt":
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                handle.close()
            lock.release()

    def _replay(self) -> dict[str, dict[str, Any]]:
        reference = self.store.reference(self._configuration_key)
        if reference is None or self.store.read_verified(reference) != canonical_json_bytes(self._configuration):
            raise ArtifactIntegrityError("budget configuration changed or disappeared")
        reservations: dict[str, dict[str, Any]] = {}
        for sequence, reference in enumerate(self.store.event_refs(self._event_stream)):
            event = json.loads(self.store.read_verified(reference))
            expected_hash = "event-" + hashlib.sha256(canonical_json_bytes(
                {key: value for key, value in event.items() if key != "event_id"})).hexdigest()
            if (event.get("sequence") != sequence or event.get("episode_id") != self._event_stream
                    or event.get("event_id") != expected_hash):
                raise ArtifactIntegrityError("budget event sequence or identity is corrupt")
            payload = event.get("payload", {})
            reservation_id = payload.get("reservation_id")
            kind = event.get("event_type")
            if kind == "budget_reserved":
                if reservation_id in reservations:
                    raise ArtifactIntegrityError("duplicate budget reservation")
                reservations[reservation_id] = {**payload, "state": "reserved", "observed": {},
                                                "unavailable_reasons": {}}
            elif reservation_id not in reservations:
                raise ArtifactIntegrityError("budget event precedes its reservation")
            else:
                item = reservations[reservation_id]
                if kind == "budget_dispatched" and item["state"] == "reserved":
                    item["state"] = "dispatched"
                    item["observed"] = {axis: item["resources"][axis]
                                        for axis in ("model_calls", "public_tool_calls", "public_cycles",
                                                     "final_public_tool_calls", "hidden_tool_calls")}
                elif kind == "budget_cancelled" and item["state"] == "reserved":
                    item["state"] = "cancelled"
                    item["cancel_reason"] = payload["reason"]
                elif kind == "budget_reconciled" and (
                    item["state"] in {"dispatched", "unknown"}
                    or self._is_usage_refinement(item, payload)
                ):
                    item["state"] = payload["outcome"]
                    item["observed"] = payload["observed"]
                    item["unavailable_reasons"] = payload["unavailable_reasons"]
                else:
                    raise ArtifactIntegrityError("invalid budget lifecycle event")
        return reservations

    def _event(self, kind: str, payload: dict[str, Any]) -> None:
        self.store.append_event(self._event_stream, kind, payload)

    def _reservation_id(self, operation_id: str) -> str:
        if not isinstance(operation_id, str) or not operation_id:
            raise ValueError("operation identity must be nonempty")
        return "reservation-" + hashlib.sha256(canonical_json_bytes([self.stream_id, operation_id])).hexdigest()

    @staticmethod
    def _view(item: dict[str, Any]) -> Reservation:
        return Reservation(item["reservation_id"], item["operation_id"], tuple(item["consumers"]),
                           MappingProxyType(dict(item["resources"])), item["token_reservation_kind"],
                           MappingProxyType(dict(item["metadata"])), item["state"])

    @staticmethod
    def _is_usage_refinement(item: Mapping[str, Any], payload: Mapping[str, Any]) -> bool:
        """Late telemetry may fill unknown costs, never replace known facts."""
        if item["state"] not in FINAL_OUTCOMES or item["state"] != payload.get("outcome"):
            return False
        before, after = item["observed"], payload.get("observed", {})
        if set(before) != set(after):
            return False
        return (any(before[axis] is None and after[axis] is not None for axis in before)
                and all(value is None or after[axis] == value for axis, value in before.items()))

    def reserve(self, operation_id: str, consumers: Sequence[str], *, model_calls: int = 0,
                input_tokens: int = 0, output_tokens: int = 0, context_tokens: int = 0,
                public_tool_calls: int = 0, public_cycles: int = 0,
                final_public_tool_calls: int = 0, hidden_tool_calls: int = 0,
                active_seconds: float = 0, eda_seconds: float = 0, cpu_seconds: float = 0,
                memory_bytes: int = 0, token_reservation_kind: str = "upper_bound",
                metadata: Mapping[str, Any] | None = None) -> Reservation:
        reservation_id = self._reservation_id(operation_id)
        if isinstance(consumers, str) or not consumers or len(consumers) != len(set(consumers)):
            raise ValueError("shared consumers must be a nonempty unique sequence")
        if any(consumer not in self.limits for consumer in consumers):
            raise ValueError("operation names an unconfigured method consumer")
        if token_reservation_kind not in {"exact", "upper_bound"}:
            raise ValueError("token reservation kind must identify exact counts or an explicit upper bound")
        resources = {"model_calls": model_calls, "input_tokens": input_tokens,
                     "output_tokens": output_tokens, "context_tokens": context_tokens,
                     "public_tool_calls": public_tool_calls, "public_cycles": public_cycles,
                     "final_public_tool_calls": final_public_tool_calls, "hidden_tool_calls": hidden_tool_calls,
                     "active_seconds": active_seconds, "eda_seconds": eda_seconds,
                     "cpu_seconds": cpu_seconds, "memory_bytes": memory_bytes}
        for axis, value in resources.items():
            _number(value, axis)
        if model_calls not in {0, 1}:
            raise ValueError("each model reservation represents exactly one logical call")
        if model_calls and context_tokens < input_tokens + output_tokens:
            raise ValueError("context reservation must include reserved input and output tokens")
        if not any(resources.values()):
            raise ValueError("empty resource reservations are not budget operations")
        record = {"reservation_id": reservation_id, "operation_id": operation_id,
                  "consumers": sorted(consumers), "resources": resources,
                  "token_reservation_kind": token_reservation_kind,
                  "metadata": json.loads(json.dumps(dict(metadata or {}), allow_nan=False))}
        if model_calls and token_reservation_kind == "upper_bound" and any(
                resources[axis] for axis in ("input_tokens", "output_tokens", "context_tokens")):
            source = record["metadata"].get("token_bound_source")
            if not isinstance(source, str) or not source.strip():
                raise ValueError("token upper-bound reservations require metadata.token_bound_source")
        # Check serializability before reserving anything.
        json.dumps(record, allow_nan=False)
        canonical_json_bytes(record)
        with self._locked():
            existing = self._replay()
            if reservation_id in existing:
                previous = existing[reservation_id]
                if any(previous[key] != value for key, value in record.items()):
                    raise BudgetError("operation identity already binds a different reservation")
                return self._view(previous)
            snapshot = self._summarize(existing)
            for consumer in record["consumers"]:
                state = snapshot["methods"][consumer]
                limit = self.limits[consumer]
                if state["status"] == "exceeded":
                    raise BudgetExceeded(f"{consumer} has already exceeded a resource bound")
                if model_calls and output_tokens > limit.max_single_output_tokens:
                    raise BudgetExceeded(f"{consumer} single output token bound exceeded before dispatch")
                for axis, value in resources.items():
                    current = state["used"][axis]
                    projected = max(current, value) if axis in PEAK_AXES else current + value
                    ceiling = getattr(limit, RESOURCE_LIMITS[axis])
                    if projected > ceiling:
                        raise BudgetExceeded(f"{consumer} {axis}: {projected}>{ceiling} before dispatch")
            self._event("budget_reserved", record)
            return self._view(self._replay()[reservation_id])

    def dispatch(self, reservation_id: str) -> Reservation:
        """Durably mark execution before calling a provider or tool."""
        with self._locked():
            items = self._replay()
            item = self._item(items, reservation_id)
            if item["state"] != "reserved":
                raise BudgetError("reservation was already dispatched, reconciled or cancelled")
            self._event("budget_dispatched", {"reservation_id": reservation_id})
            return self._view(self._replay()[reservation_id])

    def cancel(self, reservation_id: str, *, reason: str) -> Reservation:
        """Release only a reservation known not to have been dispatched."""
        if not isinstance(reason, str) or not reason:
            raise ValueError("cancellation requires a reason")
        with self._locked():
            item = self._item(self._replay(), reservation_id)
            if item["state"] == "cancelled" and item.get("cancel_reason") == reason:
                return self._view(item)
            if item["state"] != "reserved":
                raise BudgetError("dispatched/uncertain operations cannot be refunded as unused")
            self._event("budget_cancelled", {"reservation_id": reservation_id, "reason": reason})
            return self._view(self._replay()[reservation_id])

    def reconcile(self, reservation_id: str, *, observed: Mapping[str, int | float | None],
                  outcome: str = "completed", unavailable_reasons: Mapping[str, str] | None = None) -> Reservation:
        """Record actual usage, including overages, without rewriting an old event.

        Unknown measurements retain their full reserved bounds. An unknown remote
        operation may later be reconciled under the same identity, never dispatched
        again. Final identical receipts are idempotent; conflicting receipts fail.
        """
        if outcome not in FINAL_OUTCOMES | {"unknown"}:
            raise ValueError("unknown budget outcome")
        if set(observed) - set(RESOURCE_LIMITS):
            raise ValueError("unregistered observed resource axis")
        reasons = dict(unavailable_reasons or {})
        if set(reasons) - set(RESOURCE_LIMITS) or any(not isinstance(v, str) or not v for v in reasons.values()):
            raise ValueError("unavailable resource reasons must identify registered axes")
        for axis, value in observed.items():
            if value is not None:
                _number(value, axis)
        with self._locked():
            item = self._item(self._replay(), reservation_id)
            normalized: dict[str, int | float | None] = {}
            for axis, amount in item["resources"].items():
                if axis == "model_calls":
                    if axis in observed and observed[axis] != amount:
                        raise BudgetError("a dispatched logical model call cannot be refunded or multiplied")
                    normalized[axis] = amount
                elif axis in observed:
                    normalized[axis] = observed[axis]
                elif axis in item["observed"]:
                    normalized[axis] = item["observed"][axis]
                elif axis in {"public_tool_calls", "public_cycles", "final_public_tool_calls", "hidden_tool_calls"} or amount == 0:
                    normalized[axis] = amount
                else:
                    normalized[axis] = None
                if normalized[axis] is None:
                    reasons.setdefault(axis, "remote_execution_unknown" if outcome == "unknown" else "usage_unavailable")
                else:
                    reasons.pop(axis, None)
            payload = {"reservation_id": reservation_id, "outcome": outcome,
                       "observed": normalized, "unavailable_reasons": reasons}
            if item["state"] in FINAL_OUTCOMES:
                if (item["state"] == outcome and item["observed"] == normalized
                        and item["unavailable_reasons"] == reasons):
                    return self._view(item)
                if not self._is_usage_refinement(item, payload):
                    raise BudgetError("conflicting final budget observation")
            if (item["state"] == "unknown" and outcome == "unknown"
                    and item["observed"] == normalized and item["unavailable_reasons"] == reasons):
                return self._view(item)
            if item["state"] not in {"dispatched", "unknown"} | FINAL_OUTCOMES:
                raise BudgetError("only dispatched or uncertain operations can be reconciled")
            self._event("budget_reconciled", payload)
            return self._view(self._replay()[reservation_id])

    @staticmethod
    def _item(items: Mapping[str, Any], reservation_id: str) -> dict[str, Any]:
        if reservation_id not in items:
            raise BudgetError("unknown budget reservation identity")
        return items[reservation_id]

    def _summarize(self, items: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        def empty() -> dict[str, Any]:
            return {"used": {axis: 0 for axis in RESOURCE_LIMITS},
                    "observed": {axis: 0 for axis in RESOURCE_LIMITS},
                    "unavailable_axes": {}, "status": "compliant", "overages": []}
        actual = empty()
        methods = {method: empty() for method in self.limits}
        for item in items.values():
            if item["state"] == "cancelled":
                continue
            for target in [actual, *(methods[name] for name in item["consumers"])]:
                for axis, reserved in item["resources"].items():
                    measured = item["observed"].get(axis)
                    charged = reserved if measured is None else measured
                    if axis in PEAK_AXES:
                        target["used"][axis] = max(target["used"][axis], charged)
                        if measured is not None:
                            target["observed"][axis] = max(target["observed"][axis], measured)
                    else:
                        target["used"][axis] += charged
                        if measured is not None:
                            target["observed"][axis] += measured
                    if (item["state"] != "reserved" and measured is None
                            and (reserved or axis in item["unavailable_reasons"])):
                        target["unavailable_axes"].setdefault(axis, []).append({
                            "reservation_id": item["reservation_id"],
                            "reason": item["unavailable_reasons"].get(axis, "operation_not_reconciled"),
                        })
                if item["state"] in {"dispatched", "unknown"}:
                    target["status"] = "unverifiable"
        for method, summary in methods.items():
            limit = self.limits[method]
            for axis, field in RESOURCE_LIMITS.items():
                if summary["used"][axis] > getattr(limit, field):
                    summary["overages"].append(axis)
            for item in items.values():
                if method not in item["consumers"] or item["state"] == "cancelled" or not item["resources"]["model_calls"]:
                    continue
                output = item["observed"].get("output_tokens", item["resources"]["output_tokens"])
                if output is not None and output > limit.max_single_output_tokens:
                    summary["overages"].append("single_output_tokens")
            summary["status"] = ("exceeded" if summary["overages"] else
                                 "unverifiable" if summary["unavailable_axes"] or summary["status"] == "unverifiable"
                                 else "compliant")
            summary["remaining"] = {
                axis: max(0, getattr(limit, field) - summary["used"][axis])
                for axis, field in RESOURCE_LIMITS.items()
            }
            summary["limits"] = limit.to_dict()
        statuses = {item["status"] for item in methods.values()}
        actual["status"] = ("exceeded" if "exceeded" in statuses else
                            "unverifiable" if "unverifiable" in statuses else "compliant")
        return {"budget_version": "pc21-runtime-budget-v1", "stream_id": self.stream_id,
                "budget_status": actual["status"], "actual": actual, "methods": methods,
                "reservations": {key: dict(item) for key, item in items.items()}}

    def snapshot(self) -> dict[str, Any]:
        with self._locked():
            return self._summarize(self._replay())

    def remaining(self, method: str, axis: str) -> int | float:
        if method not in self.limits or axis not in RESOURCE_LIMITS:
            raise ValueError("unknown budget consumer or axis")
        return self.snapshot()["methods"][method]["remaining"][axis]
