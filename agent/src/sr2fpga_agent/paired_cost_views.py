"""Verified development-only actual, standalone, and incremental cost views."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from sr2fpga_agent.artifact_store import (
    ArtifactConflictError,
    ArtifactIntegrityError,
    ArtifactRef,
    ArtifactStore,
)
from sr2fpga_agent.block_cost_accounting import replay_development_block_preparation
from sr2fpga_agent.block_preparation import read_development_shared_checkpoint_manifest
from sr2fpga_agent.contract_registry import ContractRegistry
from sr2fpga_agent.cost_accounting import COST_AXES, reconcile_cost_events
from sr2fpga_agent.paired_block import load_development_paired_block


_METHODS = ("M0", "M1", "M2", "M3", "M4", "M5")
_METHOD_PREREQUISITES = {
    "M0": ("direct_initial_project",),
    "M1": ("direct_initial_project",),
    "M2": (),
    "M3": ("shared_system_his",),
    "M4": ("shared_system_his", "skeleton_initial_project"),
    "M5": ("shared_system_his", "skeleton_initial_project"),
}
_CONTRASTS = {
    "M1-M0": ("direct_initial_project", "M1", "M0"),
    "M4-M3": ("shared_system_his", "M4", "M3"),
    "M5-M4": ("skeleton_initial_project", "M5", "M4"),
}
_CONTRAST_COMPONENTS = {
    "M1-M0": (("exclusive:M1",), ("exclusive:M0",)),
    "M4-M3": (
        ("checkpoint:skeleton_initial_project", "exclusive:M4"),
        ("exclusive:M3",),
    ),
    "M5-M4": (("exclusive:M5",), ("exclusive:M4",)),
}


class PairedCostReconciliationError(ValueError):
    pass


@dataclass(frozen=True)
class MethodCostSource:
    method_condition: str
    terminal_status: str
    trajectory_ref: ArtifactRef | None
    blocked_checkpoint_id: str | None = None


@dataclass(frozen=True)
class _VerifiedMethodCost:
    source: MethodCostSource
    trajectory: dict[str, Any] | None
    cost_summary_refs: tuple[ArtifactRef, ...]
    attempt_event_refs: tuple[ArtifactRef, ...]
    event_ids: tuple[str, ...]
    exclusive_axes: dict[str, dict[str, Any]]


def reconcile_development_paired_block_costs(
    store: ArtifactStore,
    *,
    paired_block_ref: ArtifactRef,
    checkpoint_manifest_ref: ArtifactRef,
    block_event_refs: Iterable[ArtifactRef],
    methods: Iterable[MethodCostSource],
    source_full_pack_runner_ref: ArtifactRef | None,
    reducer_policy_sha256: str,
) -> tuple[dict[str, Any], ArtifactRef]:
    """Derive the three registered views solely from verified raw sources."""

    _require_sha256(reducer_policy_sha256, "reducer policy")
    paired_block = _read_paired_block(store, paired_block_ref)
    manifest = _read_manifest(store, checkpoint_manifest_ref)
    if manifest["paired_block_ref"] != paired_block_ref.to_dict():
        raise PairedCostReconciliationError(
            "checkpoint manifest belongs to another paired block"
        )

    event_refs = tuple(block_event_refs)
    try:
        replay = replay_development_block_preparation(store, event_refs)
    except (
        ArtifactConflictError,
        ArtifactIntegrityError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise PairedCostReconciliationError(
            "block preparation source cannot be replayed"
        ) from exc
    if replay.paired_block_ref != paired_block_ref:
        raise PairedCostReconciliationError(
            "block preparation events belong to another paired block"
        )
    if [reference.to_dict() for reference in replay.event_refs] != manifest[
        "block_event_refs"
    ]:
        raise PairedCostReconciliationError(
            "block event references do not match the checkpoint manifest"
        )

    nodes = {node["checkpoint_id"]: node for node in manifest["nodes"]}
    sources = _normalize_method_sources(methods)
    required_lineage = {
        paired_block_ref.sha256,
        checkpoint_manifest_ref.sha256,
        *(reference.sha256 for reference in event_refs),
    }
    verified_methods: dict[str, _VerifiedMethodCost] = {}
    episode_ids: set[str] = set()
    for method in _METHODS:
        source = sources[method]
        _validate_method_availability(source, nodes)
        if source.trajectory_ref is None:
            verified_methods[method] = _blocked_method(source)
            continue
        checkpoint_hashes = {
            nodes[checkpoint]["artifact_ref"]["sha256"]
            for checkpoint in _METHOD_PREREQUISITES[method]
        }
        verified = _load_verified_method_cost(
            store,
            source,
            required_input_hashes=required_lineage | checkpoint_hashes,
        )
        episode_id = verified.trajectory["episode_id"]
        if episode_id in episode_ids:
            raise PairedCostReconciliationError(
                "method trajectories must use distinct episodes"
            )
        episode_ids.add(episode_id)
        verified_methods[method] = verified

    _require_disjoint_source_partition(replay, verified_methods)
    structurally_complete = (
        manifest["manifest_status"] == "complete"
        and all(
            item.source.terminal_status == "completed"
            and item.source.trajectory_ref is not None
            for item in verified_methods.values()
        )
    )
    if structurally_complete:
        if source_full_pack_runner_ref is None:
            raise PairedCostReconciliationError(
                "complete reconciliation requires a full-pack-runner-v2 source"
            )
        _validate_full_pack_lineage(
            store,
            source_full_pack_runner_ref,
            paired_block_ref=paired_block_ref,
            paired_block=paired_block,
            methods=verified_methods,
        )
    elif source_full_pack_runner_ref is not None:
        raise PairedCostReconciliationError(
            "incomplete reconciliation cannot name a full-pack source"
        )

    component_axes = {
        **{
            f"checkpoint:{checkpoint}": replay.checkpoint_axes[checkpoint]
            for checkpoint in nodes
        },
        **{
            f"exclusive:{method}": verified_methods[method].exclusive_axes
            for method in _METHODS
        },
    }
    actual_axes = _aggregate_axes(
        [
            ("block_preparation", replay.actual_axes),
            *(
                (f"exclusive:{method}", verified_methods[method].exclusive_axes)
                for method in _METHODS
            ),
        ]
    )
    method_records = [
        _method_record(method, verified_methods[method], replay, nodes)
        for method in _METHODS
    ]
    contrasts = [
        _contrast_record(contrast_id, component_axes, verified_methods, nodes)
        for contrast_id in _CONTRASTS
    ]
    block_event_ids = [event["event_id"] for event in replay.events]
    method_event_ids = {
        method: list(verified_methods[method].event_ids) for method in _METHODS
    }
    source_partition = {
        "block_event_ids": block_event_ids,
        "block_events_sha256": replay.source_events_sha256,
        "method_event_ids": method_event_ids,
    }
    source_partition["source_events_sha256"] = _sha256_json(
        {
            "block_event_ids": block_event_ids,
            "method_event_ids": method_event_ids,
        }
    )
    incomplete_reasons = _incomplete_reasons(manifest, verified_methods)
    payload = {
        "contract_version": "development-paired-block-cost-reconciliation-v1",
        "evaluation_scope": "excluded_development_conformance_only",
        "reconciliation_status": "complete" if structurally_complete else "incomplete",
        "incomplete_reasons": incomplete_reasons,
        "paired_block_ref": paired_block_ref.to_dict(),
        "checkpoint_manifest_ref": checkpoint_manifest_ref.to_dict(),
        "block_event_refs": [reference.to_dict() for reference in replay.event_refs],
        "source_full_pack_runner_ref": (
            source_full_pack_runner_ref.to_dict()
            if source_full_pack_runner_ref is not None
            else None
        ),
        "reducer_policy_sha256": reducer_policy_sha256,
        "actual_block_axes": actual_axes,
        "method_records": method_records,
        "incremental_contrasts": contrasts,
        "source_event_partition": source_partition,
        "reconciliation": {
            "method_set": list(_METHODS),
            "checkpoint_manifest_verified": True,
            "all_source_artifacts_verified": True,
            "all_available_trajectories_verified": True,
            "source_event_partition_disjoint": True,
            "all_required_axes_classified": True,
            "full_pack_lineage_verified": structurally_complete,
            "all_authority_fields_false": True,
        },
        "official_outcome": False,
        "official_authority": False,
        "pass_credit_authority": False,
        "rq1_evidence": False,
        "rq2_evidence": False,
        "g3_accepted": False,
        "g4b_authorized": False,
    }
    try:
        reference = store.put_validated_json(
            f"paired-cost-reconciliations/{paired_block_ref.sha256}/"
            f"{reducer_policy_sha256}",
            payload,
            contract_key="development_paired_block_cost_reconciliation",
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PairedCostReconciliationError(
            "paired-block cost reconciliation failed contract validation"
        ) from exc
    return payload, reference


def read_development_paired_block_cost_reconciliation(
    store: ArtifactStore, reference: ArtifactRef
) -> dict[str, Any]:
    """Read a companion and reproduce it from its verified raw sources."""

    try:
        payload = json.loads(store.read_verified(reference))
    except (
        ArtifactConflictError,
        ArtifactIntegrityError,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise PairedCostReconciliationError(
            "paired-block cost reconciliation is not valid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise PairedCostReconciliationError(
            "paired-block cost reconciliation must be a JSON object"
        )
    errors = ContractRegistry().load_schema(
        "development_paired_block_cost_reconciliation"
    ).validate(payload)
    if errors:
        raise PairedCostReconciliationError(
            "invalid paired-block cost reconciliation: " + "; ".join(errors)
        )
    methods = tuple(
        MethodCostSource(
            item["method_condition"],
            item["terminal_status"],
            _optional_ref(item["trajectory_ref"]),
            item["blocked_checkpoint_id"],
        )
        for item in payload["method_records"]
    )
    rebuilt, rebuilt_ref = reconcile_development_paired_block_costs(
        store,
        paired_block_ref=_artifact_ref(payload["paired_block_ref"]),
        checkpoint_manifest_ref=_artifact_ref(payload["checkpoint_manifest_ref"]),
        block_event_refs=tuple(
            _artifact_ref(item) for item in payload["block_event_refs"]
        ),
        methods=methods,
        source_full_pack_runner_ref=_optional_ref(
            payload["source_full_pack_runner_ref"]
        ),
        reducer_policy_sha256=payload["reducer_policy_sha256"],
    )
    if rebuilt != payload or rebuilt_ref != reference:
        raise PairedCostReconciliationError(
            "paired-block cost reconciliation does not match verified sources"
        )
    return payload


def _read_paired_block(store: ArtifactStore, reference: ArtifactRef) -> dict[str, Any]:
    try:
        _require_exact_reference(store, reference, "paired block")
        return load_development_paired_block(store, reference)
    except (ArtifactIntegrityError, KeyError, TypeError, ValueError) as exc:
        raise PairedCostReconciliationError("paired-block source is invalid") from exc


def _read_manifest(store: ArtifactStore, reference: ArtifactRef) -> dict[str, Any]:
    try:
        _require_exact_reference(store, reference, "checkpoint manifest")
        return read_development_shared_checkpoint_manifest(store, reference)
    except (ArtifactIntegrityError, KeyError, TypeError, ValueError) as exc:
        raise PairedCostReconciliationError(
            "checkpoint-manifest source is invalid"
        ) from exc


def _normalize_method_sources(
    methods: Iterable[MethodCostSource],
) -> dict[str, MethodCostSource]:
    records = tuple(methods)
    if any(not isinstance(record, MethodCostSource) for record in records):
        raise PairedCostReconciliationError(
            "method cost sources must be MethodCostSource records"
        )
    by_method = {record.method_condition: record for record in records}
    if len(records) != len(_METHODS) or set(by_method) != set(_METHODS):
        raise PairedCostReconciliationError(
            "cost reconciliation requires exactly one M0-M5 method source"
        )
    return by_method


def _validate_method_availability(
    source: MethodCostSource, nodes: Mapping[str, Mapping[str, Any]]
) -> None:
    blocked = source.terminal_status == "blocked_by_shared_checkpoint"
    if blocked != (source.trajectory_ref is None):
        raise PairedCostReconciliationError(
            f"{source.method_condition} blocked status and trajectory disagree"
        )
    if blocked:
        checkpoint = source.blocked_checkpoint_id
        if checkpoint not in _METHOD_PREREQUISITES[source.method_condition]:
            raise PairedCostReconciliationError(
                f"{source.method_condition} names an unrelated blocked checkpoint"
            )
        if nodes[checkpoint]["status"] == "completed":
            raise PairedCostReconciliationError(
                f"{source.method_condition} is blocked by a completed checkpoint"
            )
        return
    if source.blocked_checkpoint_id is not None:
        raise PairedCostReconciliationError(
            f"{source.method_condition} has an unexpected blocked checkpoint"
        )
    if source.terminal_status not in {"completed", "failed", "not_run"}:
        raise PairedCostReconciliationError(
            f"{source.method_condition} has an unknown terminal status"
        )
    incomplete = [
        checkpoint
        for checkpoint in _METHOD_PREREQUISITES[source.method_condition]
        if nodes[checkpoint]["status"] != "completed"
    ]
    if incomplete:
        raise PairedCostReconciliationError(
            f"{source.method_condition} ran without completed prerequisites"
        )


def _blocked_method(source: MethodCostSource) -> _VerifiedMethodCost:
    return _VerifiedMethodCost(
        source=source,
        trajectory=None,
        cost_summary_refs=(),
        attempt_event_refs=(),
        event_ids=(),
        exclusive_axes=_zero_axes(),
    )


def _load_verified_method_cost(
    store: ArtifactStore,
    source: MethodCostSource,
    *,
    required_input_hashes: set[str],
) -> _VerifiedMethodCost:
    reference = source.trajectory_ref
    if reference is None:
        raise PairedCostReconciliationError("available method has no trajectory")
    try:
        _require_exact_reference(store, reference, "trajectory")
        trajectory = json.loads(store.read_verified(reference))
    except (
        ArtifactIntegrityError,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise PairedCostReconciliationError(
            f"{source.method_condition} trajectory is invalid"
        ) from exc
    errors = ContractRegistry().load_schema("trajectory_v2").validate(trajectory)
    if errors:
        raise PairedCostReconciliationError(
            f"invalid {source.method_condition} trajectory: " + "; ".join(errors)
        )
    without_id = {key: value for key, value in trajectory.items() if key != "trajectory_id"}
    if trajectory["trajectory_id"] != "trajectory-v2-" + _sha256_json(without_id):
        raise PairedCostReconciliationError(
            f"{source.method_condition} trajectory ID does not match its content"
        )
    if trajectory["method_condition"] != source.method_condition:
        raise PairedCostReconciliationError(
            f"{source.method_condition} trajectory method mismatch"
        )
    expected_key = f"trajectories/{trajectory['episode_id']}/{source.method_condition}"
    if reference.key != expected_key:
        raise PairedCostReconciliationError(
            f"{source.method_condition} trajectory key mismatch"
        )

    summaries: list[ArtifactRef] = []
    event_refs: list[ArtifactRef] = []
    event_ids: list[str] = []
    summary_axes: list[tuple[str, Mapping[str, Any]]] = []
    seen_attempts: set[str] = set()
    for attempt in trajectory["attempts"]:
        attempt_id = attempt["attempt_id"]
        if attempt_id in seen_attempts:
            raise PairedCostReconciliationError(
                f"{source.method_condition} repeats an attempt"
            )
        seen_attempts.add(attempt_id)
        if not required_input_hashes.issubset(set(attempt["input_artifact_hashes"])):
            raise PairedCostReconciliationError(
                f"{source.method_condition} trajectory omits checkpoint lineage"
            )
        attempt_refs = tuple(
            _artifact_ref(item) for item in attempt["attempt_event_refs"]
        )
        summary_ref = _artifact_ref(attempt["cost_summary_ref"])
        expected_summary_key = (
            f"cost-summaries/{trajectory['episode_id']}/{attempt_id}"
        )
        if summary_ref.key != expected_summary_key:
            raise PairedCostReconciliationError(
                f"{source.method_condition} cost-summary key mismatch"
            )
        try:
            _require_exact_reference(store, summary_ref, "cost summary")
            declared_summary = json.loads(store.read_verified(summary_ref))
            rebuilt = reconcile_cost_events(
                store, attempt_refs, summary_key=summary_ref.key
            )
        except (
            ArtifactConflictError,
            ArtifactIntegrityError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise PairedCostReconciliationError(
                f"{source.method_condition} raw attempt cost cannot be reconciled"
            ) from exc
        if rebuilt.artifact_ref != summary_ref or rebuilt.payload != declared_summary:
            raise PairedCostReconciliationError(
                f"{source.method_condition} cost summary does not match raw events"
            )
        expected_summary_identity = (
            trajectory["episode_id"],
            source.method_condition,
            attempt_id,
        )
        for summary in (declared_summary, rebuilt.payload):
            if (
                summary["episode_id"],
                summary["method_condition"],
                summary["attempt_id"],
            ) != expected_summary_identity:
                raise PairedCostReconciliationError(
                    f"{source.method_condition} raw summary identity mismatch"
                )
        raw_events = [
            json.loads(store.read_verified(event_ref)) for event_ref in attempt_refs
        ]
        expected_event_identity = (
            trajectory["episode_id"],
            source.method_condition,
            attempt_id,
        )
        if any(
            (
                event["episode_id"],
                event["method_condition"],
                event["attempt_id"],
            )
            != expected_event_identity
            for event in raw_events
        ):
            raise PairedCostReconciliationError(
                f"{source.method_condition} raw attempt identity mismatch"
            )
        if any(
            event["candidate_id"] != attempt["candidate_id"] for event in raw_events
        ):
            raise PairedCostReconciliationError(
                f"{source.method_condition} raw attempt candidate identity mismatch"
            )
        raw_input_hashes = sorted(
            {
                digest
                for event in raw_events
                for digest in event["input_artifact_hashes"]
            }
        )
        if raw_input_hashes != attempt["input_artifact_hashes"]:
            raise PairedCostReconciliationError(
                f"{source.method_condition} raw input artifact hashes mismatch"
            )
        raw_output_hashes = sorted(
            {
                digest
                for event in raw_events
                for digest in event["output_artifact_hashes"]
            }
        )
        if raw_output_hashes != attempt["output_artifact_hashes"]:
            raise PairedCostReconciliationError(
                f"{source.method_condition} raw output artifact hashes mismatch"
            )
        current_ids = [event["event_id"] for event in raw_events]
        if attempt["source_events_sha256"] != _sha256_json(current_ids):
            raise PairedCostReconciliationError(
                f"{source.method_condition} trajectory event digest mismatch"
            )
        if declared_summary["source_event_ids"] != current_ids:
            raise PairedCostReconciliationError(
                f"{source.method_condition} summary event IDs mismatch"
            )
        summaries.append(summary_ref)
        event_refs.extend(attempt_refs)
        event_ids.extend(current_ids)
        summary_axes.append((f"attempt:{attempt_id}", declared_summary["axes"]))
    if len(event_refs) != len(set(event_refs)) or len(event_ids) != len(set(event_ids)):
        raise PairedCostReconciliationError(
            f"{source.method_condition} repeats raw attempt events"
        )
    terminal_ref = _optional_ref(trajectory["terminal_candidate_ref"])
    if terminal_ref is not None:
        try:
            _require_exact_reference(store, terminal_ref, "terminal candidate")
        except (ArtifactIntegrityError, KeyError, TypeError, ValueError) as exc:
            raise PairedCostReconciliationError(
                f"{source.method_condition} terminal reference is invalid"
            ) from exc
    return _VerifiedMethodCost(
        source=source,
        trajectory=trajectory,
        cost_summary_refs=tuple(summaries),
        attempt_event_refs=tuple(event_refs),
        event_ids=tuple(event_ids),
        exclusive_axes=_aggregate_axes(summary_axes),
    )


def _require_disjoint_source_partition(replay, methods: Mapping[str, _VerifiedMethodCost]) -> None:
    seen_refs = set(replay.event_refs)
    seen_ids = {event["event_id"] for event in replay.events}
    if len(seen_refs) != len(replay.event_refs) or len(seen_ids) != len(replay.events):
        raise PairedCostReconciliationError("block source partition contains duplicates")
    for method in _METHODS:
        record = methods[method]
        refs = set(record.attempt_event_refs)
        ids = set(record.event_ids)
        if seen_refs & refs or seen_ids & ids:
            raise PairedCostReconciliationError(
                "block and method source-event partitions overlap"
            )
        seen_refs.update(refs)
        seen_ids.update(ids)


def _validate_full_pack_lineage(
    store: ArtifactStore,
    reference: ArtifactRef,
    *,
    paired_block_ref: ArtifactRef,
    paired_block: Mapping[str, Any],
    methods: Mapping[str, _VerifiedMethodCost],
) -> None:
    try:
        _require_exact_reference(store, reference, "full-pack reconciliation")
        payload = json.loads(store.read_verified(reference))
    except (
        ArtifactIntegrityError,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise PairedCostReconciliationError("full-pack source is invalid") from exc
    errors = ContractRegistry().load_schema(
        "full_pack_runner_reconciliation_v2"
    ).validate(payload)
    if errors:
        raise PairedCostReconciliationError(
            "invalid full-pack source: " + "; ".join(errors)
        )
    if payload.get("paired_block_ref") != paired_block_ref.to_dict():
        raise PairedCostReconciliationError(
            "full-pack source belongs to another paired block"
        )
    if (
        payload.get("method_order") != paired_block["method_order"]
        or payload.get("actual_method_order") != paired_block["method_order"]
        or payload["public_projection_sha256"]
        != paired_block["public_projection_sha256"]
    ):
        raise PairedCostReconciliationError("full-pack paired-block lineage disagrees")
    by_method = {item["method_condition"]: item for item in payload["method_records"]}
    if set(by_method) != set(_METHODS):
        raise PairedCostReconciliationError("full-pack method set disagrees")
    for method in _METHODS:
        verified = methods[method]
        full_pack_method = by_method[method]
        if full_pack_method["trajectory_ref"] != verified.source.trajectory_ref.to_dict():
            raise PairedCostReconciliationError(
                f"full-pack {method} trajectory reference disagrees"
            )
        if full_pack_method["episode_id"] != verified.trajectory["episode_id"]:
            raise PairedCostReconciliationError(
                f"full-pack {method} episode identity disagrees"
            )
        if full_pack_method["cost_summary_refs"] != [
            item.to_dict() for item in verified.cost_summary_refs
        ]:
            raise PairedCostReconciliationError(
                f"full-pack {method} cost-summary references disagree"
            )
        if full_pack_method["terminal_candidate_ref"] != verified.trajectory[
            "terminal_candidate_ref"
        ]:
            raise PairedCostReconciliationError(
                f"full-pack {method} terminal reference disagrees"
            )
    try:
        _require_exact_reference(
            store,
            _artifact_ref(payload["source_smoke_report_ref"]),
            "full-pack source report",
        )
    except (ArtifactIntegrityError, KeyError, TypeError, ValueError) as exc:
        raise PairedCostReconciliationError(
            "full-pack source report reference is invalid"
        ) from exc


def _method_record(
    method: str,
    verified: _VerifiedMethodCost,
    replay,
    nodes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    prerequisite_axes = [
        (f"checkpoint:{checkpoint}", replay.checkpoint_axes[checkpoint])
        for checkpoint in _METHOD_PREREQUISITES[method]
    ]
    standalone = _aggregate_axes(
        [*prerequisite_axes, (f"exclusive:{method}", verified.exclusive_axes)]
    )
    checkpoint = verified.source.blocked_checkpoint_id
    blocked_reason = None
    if checkpoint is not None:
        blocked_reason = f"{nodes[checkpoint]['reason']}:{checkpoint}"
    return {
        "method_condition": method,
        "terminal_status": verified.source.terminal_status,
        "blocked_checkpoint_id": checkpoint,
        "blocked_reason": blocked_reason,
        "trajectory_ref": (
            verified.source.trajectory_ref.to_dict()
            if verified.source.trajectory_ref is not None
            else None
        ),
        "cost_summary_refs": [item.to_dict() for item in verified.cost_summary_refs],
        "attempt_event_refs": [item.to_dict() for item in verified.attempt_event_refs],
        "source_events_sha256": _sha256_json(list(verified.event_ids)),
        "exclusive_axes": verified.exclusive_axes,
        "standalone_attributed_axes": standalone,
    }


def _contrast_record(
    contrast_id: str,
    component_axes: Mapping[str, Mapping[str, Any]],
    methods: Mapping[str, _VerifiedMethodCost],
    nodes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    checkpoint, treatment, baseline = _CONTRASTS[contrast_id]
    treatment_components, baseline_components = _CONTRAST_COMPONENTS[contrast_id]
    treatment_axes = _aggregate_axes(
        [(component, component_axes[component]) for component in treatment_components]
    )
    baseline_axes = _aggregate_axes(
        [(component, component_axes[component]) for component in baseline_components]
    )
    blocked_checkpoints = [
        methods[method].source.blocked_checkpoint_id
        for method in (treatment, baseline)
        if methods[method].source.blocked_checkpoint_id is not None
    ]
    forced_reason = None
    if blocked_checkpoints:
        forced_reason = "blocked_by_shared_checkpoint:" + blocked_checkpoints[0]
    elif nodes[checkpoint]["status"] != "completed":
        forced_reason = (
            f"checkpoint_{nodes[checkpoint]['status']}:{checkpoint}:"
            f"{nodes[checkpoint]['reason']}"
        )
    signed = _signed_delta_axes(
        treatment_axes, baseline_axes, forced_reason=forced_reason
    )
    unavailable = next(
        (value["reason"] for value in signed.values() if value["status"] == "unavailable"),
        None,
    )
    return {
        "contrast_id": contrast_id,
        "checkpoint_id": checkpoint,
        "treatment_method": treatment,
        "baseline_method": baseline,
        "status": "unavailable" if unavailable is not None else "measured",
        "reason": unavailable,
        "arms": [
            {
                "role": "treatment",
                "method_condition": treatment,
                "axes": treatment_axes,
            },
            {
                "role": "baseline",
                "method_condition": baseline,
                "axes": baseline_axes,
            },
        ],
        "signed_delta_axes": signed,
    }


def _aggregate_axes(
    components: Iterable[tuple[str, Mapping[str, Mapping[str, Any]]]],
) -> dict[str, dict[str, Any]]:
    sources = tuple(components)
    results: dict[str, dict[str, Any]] = {}
    for axis in COST_AXES:
        unavailable = [
            f"{label}:{axes[axis]['reason']}"
            for label, axes in sources
            if axes[axis]["status"] == "unavailable"
        ]
        if unavailable:
            results[axis] = {
                "status": "unavailable",
                "value": None,
                "reason": "source_unavailable:" + "|".join(unavailable),
            }
        else:
            results[axis] = {
                "status": "measured",
                "value": sum(axes[axis]["value"] for _, axes in sources),
                "reason": None,
            }
    return results


def _signed_delta_axes(
    treatment: Mapping[str, Mapping[str, Any]],
    baseline: Mapping[str, Mapping[str, Any]],
    *,
    forced_reason: str | None,
) -> dict[str, dict[str, Any]]:
    results = {}
    for axis in COST_AXES:
        reason = forced_reason
        if reason is None and (
            treatment[axis]["status"] == "unavailable"
            or baseline[axis]["status"] == "unavailable"
        ):
            reason = (
                f"contrast_arm_unavailable:{axis}:"
                f"treatment={treatment[axis]['reason']}:baseline={baseline[axis]['reason']}"
            )
        results[axis] = (
            {"status": "unavailable", "value": None, "reason": reason}
            if reason is not None
            else {
                "status": "measured",
                "value": treatment[axis]["value"] - baseline[axis]["value"],
                "reason": None,
            }
        )
    return results


def _zero_axes() -> dict[str, dict[str, Any]]:
    return {
        axis: {"status": "measured", "value": 0, "reason": None}
        for axis in COST_AXES
    }


def _incomplete_reasons(
    manifest: Mapping[str, Any], methods: Mapping[str, _VerifiedMethodCost]
) -> list[str]:
    reasons = {
        f"checkpoint_{node['status']}:{node['checkpoint_id']}:{node['reason']}"
        for node in manifest["nodes"]
        if node["status"] != "completed"
    }
    reasons.update(
        f"blocked_by_shared_checkpoint:{record.source.blocked_checkpoint_id}"
        for record in methods.values()
        if record.source.blocked_checkpoint_id is not None
    )
    reasons.update(
        f"method_terminal_status:{method}:{record.source.terminal_status}"
        for method, record in methods.items()
        if record.source.terminal_status not in {
            "completed",
            "blocked_by_shared_checkpoint",
        }
    )
    return sorted(reasons)


def _artifact_ref(payload: Mapping[str, Any]) -> ArtifactRef:
    return ArtifactRef(
        key=payload["key"],
        sha256=payload["sha256"],
        size_bytes=payload["size_bytes"],
        media_type=payload["media_type"],
    )


def _optional_ref(payload: Mapping[str, Any] | None) -> ArtifactRef | None:
    return None if payload is None else _artifact_ref(payload)


def _require_exact_reference(
    store: ArtifactStore, reference: ArtifactRef, label: str
) -> None:
    if store.reference(reference.key) != reference:
        raise PairedCostReconciliationError(
            f"{label} reference does not match its immutable key"
        )
    store.read_verified(reference)


def _require_sha256(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise PairedCostReconciliationError(f"{label} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise PairedCostReconciliationError(f"{label} must be SHA-256") from exc


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
