"""Attempt-level and paired-run measurements for Paper-1 episodes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_LEVEL_RANK = {
    "GEN_FAIL": -2,
    "H0_FAIL": -1,
    "H1_FAIL": -1,
    "H2_FAIL": -1,
    "H3_FAIL": -1,
    "L0_FAIL": -1,
    "L0": 0,
    "L1": 1,
    "L2": 2,
    "L3": 3,
    "L4": 4,
}

_REPAIR_SCOPES = ("system_his", "project")
_REPAIR_CALL_STATUSES = {
    "succeeded",
    "candidate_failed_validation",
    "failed",
    "not_run",
}
_REPAIR_TRANSITION_STATUSES = {"succeeded", "candidate_failed_validation"}


def build_episode_measurement(
    *,
    attempts: list[dict[str, Any]],
    patches: list[dict[str, Any]],
    l4_open: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the additive (a)/(b) measurement block for one episode."""
    if not attempts:
        raise ValueError("episode measurement requires at least one attempt")
    ordered = sorted((dict(item) for item in attempts), key=lambda item: int(item.get("attempt_id", 0)))
    repair_accounting = _repair_accounting(ordered, patches)
    repair_transitions = int(repair_accounting["repair_transitions"])
    initial = _measurement_point(ordered[0], "a_first_attempt_no_tools")
    final_point = "b_tool_in_loop_repair" if repair_transitions > 0 else "a_first_attempt_no_tools"
    final = _measurement_point(ordered[-1], final_point)
    regressions = sorted(
        {
            str(regression)
            for patch in patches
            if isinstance(patch, dict)
            for regression in patch.get("regressions", [])
            if isinstance(regression, str) and regression
        }
    )
    infrastructure_reason = _infrastructure_reason(ordered)
    repair_eligible = bool(ordered[0].get("repair_eligible", repair_transitions > 0))
    repair_skip_reason = ordered[0].get("repair_skip_reason")
    return {
        "initial": initial,
        "final": final,
        # Backward-compatible field: it now means an evidenced
        # diagnosis -> valid patch -> rerun transition, never an attempt-id gap.
        "repair_attempts_used": repair_transitions,
        "repair_calls_attempted": repair_accounting["repair_calls_attempted"],
        "repair_transitions": repair_transitions,
        "repair_accounting": repair_accounting,
        "repair_success": (
            repair_transitions > 0
            and infrastructure_reason is None
            and _level_rank(final["pass_level"]) > _level_rank(initial["pass_level"])
        ),
        "repair_eligible": repair_eligible,
        "repair_skip_reason": str(repair_skip_reason) if repair_skip_reason else None,
        "regressions": regressions,
        "scoreable": infrastructure_reason is None,
        "infrastructure_status": infrastructure_reason or "scoreable",
        "l4_open": _l4_measurement(l4_open),
    }


def collect_paired_results(dataset_root: Path, sample_ids: list[str]) -> dict[str, Any]:
    """Aggregate only the explicitly completed samples into paired results."""
    episodes = [_read_episode_result(dataset_root / sample_id, sample_id) for sample_id in sample_ids]
    pairs_by_id: dict[str, list[dict[str, Any]]] = {}
    for episode in episodes:
        pairs_by_id.setdefault(episode["paired_requirement_id"], []).append(episode)

    pairs: list[dict[str, Any]] = []
    for paired_id in sorted(pairs_by_id):
        members = pairs_by_id[paired_id]
        hashes = {member["requirement_sha256"] for member in members}
        if len(hashes) != 1:
            raise ValueError(f"requirement hash mismatch in pair {paired_id}")
        by_source: dict[str, dict[str, Any]] = {}
        for member in members:
            source = member["source"]
            if source in by_source:
                raise ValueError(f"duplicate source {source} in pair {paired_id}")
            by_source[source] = member
        pairs.append(
            {
                "paired_requirement_id": paired_id,
                "family_id": members[0]["family_id"],
                "requirement_sha256": next(iter(hashes)),
                "complete": len(by_source) == 4,
                "source_outcomes": by_source,
            }
        )

    scoreable = [episode for episode in episodes if episode["measurement"].get("scoreable") is True]
    infrastructure = _count_values(
        str(episode["measurement"].get("infrastructure_status", "unknown"))
        for episode in episodes
        if episode["measurement"].get("scoreable") is not True
    )
    return {
        "schema_version": "sr2fpga-phase-d-paired-v1",
        "episode_count": len(episodes),
        "scoreable_episode_count": len(scoreable),
        "pair_count": len(pairs),
        "complete_pairs": sum(int(pair["complete"]) for pair in pairs),
        "infrastructure_outcomes": infrastructure,
        "pairs": pairs,
        "by_source": _aggregate_groups(scoreable, "source"),
        "by_family": _aggregate_groups(scoreable, "family_id"),
        "initial_vs_final": _initial_vs_final(scoreable),
    }


def _measurement_point(attempt: dict[str, Any], measurement_point: str) -> dict[str, Any]:
    pass_level = str(attempt.get("pass_level") or attempt.get("highest_level") or "GEN_FAIL")
    failure_type = str(attempt.get("failure_type") or attempt.get("failure_class") or "none")
    return {
        "measurement_point": measurement_point,
        "attempt_id": int(attempt.get("attempt_id", 0)),
        "pass_level": pass_level,
        "highest_level": pass_level,
        "failure_type": failure_type,
        "failure_class": None if failure_type == "none" else failure_type,
        "automatic_pass_credit": bool(attempt.get("automatic_pass_credit", True)),
    }


def _infrastructure_reason(attempts: list[dict[str, Any]]) -> str | None:
    for attempt in attempts:
        reason = attempt.get("infrastructure_reason")
        if reason:
            return str(reason)
        if attempt.get("automatic_pass_credit") is False:
            return "automatic_pass_credit_denied"
    return None


def _l4_measurement(value: dict[str, Any] | None) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    return {
        "status": str(raw.get("status", "not_run")),
        "skip_reason": raw.get("skip_reason"),
    }


def _read_episode_result(sample_dir: Path, sample_id: str) -> dict[str, Any]:
    metadata = _read_json(sample_dir / "metadata.json")
    trajectory = _read_json(sample_dir / "eval" / "trajectory.json")
    measurement = trajectory.get("measurement")
    if not isinstance(measurement, dict):
        raise ValueError(f"sample {sample_id} is missing trajectory.measurement")
    required = {
        "source": metadata.get("source"),
        "paired_requirement_id": metadata.get("paired_requirement_id"),
        "requirement_sha256": metadata.get("requirement_sha256"),
    }
    missing = [key for key, value in required.items() if not isinstance(value, str) or not value]
    if missing:
        raise ValueError(f"sample {sample_id} is missing paired metadata: {', '.join(missing)}")
    return {
        "sample_id": sample_id,
        "family_id": str(metadata.get("family_id") or "unclassified"),
        **required,
        "freeze_fingerprint": metadata.get("freeze_fingerprint"),
        "measurement": measurement,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"required paired artifact is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"paired artifact must be an object: {path}")
    return value


def _aggregate_groups(episodes: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for episode in episodes:
        groups.setdefault(str(episode[key]), []).append(episode)
    return {name: _aggregate_episodes(members) for name, members in sorted(groups.items())}


def _aggregate_episodes(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    repair = _aggregate_repair(episodes)
    return {
        "episodes": len(episodes),
        "initial": _survival(episodes, "initial"),
        "final": _survival(episodes, "final"),
        "repair_attempts_used": repair["repair_transitions"],
        "repair_calls_attempted": repair["repair_calls_attempted"],
        "repair_transitions": repair["repair_transitions"],
        "repair_accounting": repair["repair_accounting"],
        "repair_success": _repair_success_count(episodes),
        "regressions": sum(len(episode["measurement"].get("regressions", [])) for episode in episodes),
        "l4_open": _count_values(
            str(episode["measurement"].get("l4_open", {}).get("status", "not_run")) for episode in episodes
        ),
    }


def _survival(episodes: list[dict[str, Any]], point: str) -> dict[str, int]:
    levels = [
        str(episode["measurement"].get(point, {}).get("pass_level", "GEN_FAIL")) for episode in episodes
    ]
    return {
        "denominator": len(levels),
        "l0_pass": sum(int(_level_rank(level) >= 0) for level in levels),
        "l1_pass": sum(int(_level_rank(level) >= 1) for level in levels),
        "l2_pass": sum(int(_level_rank(level) >= 2) for level in levels),
        "l3_pass": sum(int(_level_rank(level) >= 3) for level in levels),
    }


def _initial_vs_final(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    initial = _survival(episodes, "initial")
    final = _survival(episodes, "final")
    repair = _aggregate_repair(episodes)
    return {
        "scoreable_denominator": len(episodes),
        "initial": initial,
        "final": final,
        "l0_pass_delta": final["l0_pass"] - initial["l0_pass"],
        "l1_pass_delta": final["l1_pass"] - initial["l1_pass"],
        "l2_pass_delta": final["l2_pass"] - initial["l2_pass"],
        "l3_pass_delta": final["l3_pass"] - initial["l3_pass"],
        "repair_attempts_used": repair["repair_transitions"],
        "repair_calls_attempted": repair["repair_calls_attempted"],
        "repair_transitions": repair["repair_transitions"],
        "repair_accounting": repair["repair_accounting"],
        "repair_success": _repair_success_count(episodes),
        "regressions": sum(len(episode["measurement"].get("regressions", [])) for episode in episodes),
    }


def _repair_accounting(
    attempts: list[dict[str, Any]], patches: list[dict[str, Any]]
) -> dict[str, Any]:
    """Reconcile repair calls with concrete patch-and-rerun transitions.

    Missing legacy fields never fall back to attempt-id arithmetic. A repair
    transition requires an annotated call, a matching valid patch record, and
    the immediately following attempt record.
    """
    by_scope = {
        scope: {"calls_attempted": 0, "transitions": 0, "call_status_counts": {}}
        for scope in _REPAIR_SCOPES
    }
    issues: list[str] = []
    attempt_ids = [int(attempt.get("attempt_id", 0)) for attempt in attempts]
    if len(set(attempt_ids)) != len(attempt_ids):
        issues.append("duplicate_attempt_id")
    attempt_id_set = set(attempt_ids)

    patches_by_diagnosis: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for patch_index, patch in enumerate(patches):
        if not isinstance(patch, dict):
            issues.append(f"patch_{patch_index}:not_an_object")
            continue
        diagnosis_id = patch.get("diagnosis_id")
        if not isinstance(diagnosis_id, str) or not diagnosis_id:
            issues.append(f"patch_{patch_index}:missing_diagnosis_id")
            continue
        patches_by_diagnosis.setdefault(diagnosis_id, []).append((patch_index, patch))

    matched_patch_indexes: set[int] = set()
    calls_attempted = 0
    transitions = 0
    event_fields = ("repair_scope", "repair_attempted", "repair_call_status")
    for attempt in attempts:
        attempt_id = int(attempt.get("attempt_id", 0))
        event_present = [field in attempt for field in event_fields]
        diagnosis_id = f"d{attempt_id + 1:03d}"
        matching_patches = patches_by_diagnosis.get(diagnosis_id, [])
        failure_type = str(attempt.get("failure_type") or attempt.get("failure_class") or "none")
        legacy_repair_evidence = (
            any(event_present)
            or bool(matching_patches)
            or (
                failure_type != "none"
                and ("repair_eligible" in attempt or attempt_id + 1 in attempt_id_set)
            )
        )
        if not any(event_present):
            if legacy_repair_evidence:
                issues.append(f"attempt_{attempt_id}:missing_repair_event_fields")
            continue
        if not all(event_present):
            issues.append(f"attempt_{attempt_id}:partial_repair_event_fields")
            continue

        scope = attempt.get("repair_scope")
        attempted = attempt.get("repair_attempted")
        call_status = attempt.get("repair_call_status")
        if scope not in _REPAIR_SCOPES:
            issues.append(f"attempt_{attempt_id}:invalid_repair_scope")
            continue
        if not isinstance(attempted, bool):
            issues.append(f"attempt_{attempt_id}:invalid_repair_attempted")
            continue
        if call_status not in _REPAIR_CALL_STATUSES:
            issues.append(f"attempt_{attempt_id}:invalid_repair_call_status")
            continue
        if not attempted:
            if call_status != "not_run":
                issues.append(f"attempt_{attempt_id}:not_attempted_status_mismatch")
            continue
        if call_status == "not_run":
            issues.append(f"attempt_{attempt_id}:attempted_status_mismatch")
            continue

        calls_attempted += 1
        scope_accounting = by_scope[str(scope)]
        scope_accounting["calls_attempted"] += 1
        status_counts = scope_accounting["call_status_counts"]
        status_counts[str(call_status)] = status_counts.get(str(call_status), 0) + 1

        if failure_type == "none":
            issues.append(f"attempt_{attempt_id}:missing_diagnosis")
            continue
        if call_status == "failed":
            if matching_patches:
                issues.append(f"attempt_{attempt_id}:failed_call_has_patch")
            continue

        if len(matching_patches) != 1:
            issue = "missing_patch" if not matching_patches else "ambiguous_patch"
            issues.append(f"attempt_{attempt_id}:{issue}")
            continue
        patch_index, patch = matching_patches[0]
        matched_patch_indexes.add(patch_index)
        if not _valid_patch_record(patch):
            continue
        if attempt_id + 1 not in attempt_id_set:
            issues.append(f"attempt_{attempt_id}:missing_rerun")
            continue
        if call_status not in _REPAIR_TRANSITION_STATUSES:
            continue
        transitions += 1
        scope_accounting["transitions"] += 1

    for patch_index, _patch in enumerate(patches):
        if patch_index not in matched_patch_indexes:
            issues.append(f"patch_{patch_index}:unmatched_repair_event")

    return {
        "status": "complete" if not issues else "incomplete",
        "repair_calls_attempted": calls_attempted,
        "repair_transitions": transitions,
        "by_scope": by_scope,
        "issues": sorted(set(issues)),
    }


def _valid_patch_record(patch: dict[str, Any]) -> bool:
    files_touched = patch.get("files_touched")
    return (
        patch.get("status") == "valid"
        and patch.get("allowed_edit_regions_respected") is True
        and patch.get("touched_trusted_artifacts") is False
        and isinstance(files_touched, list)
        and bool(files_touched)
        and all(isinstance(path, str) and path for path in files_touched)
    )


def _aggregate_repair(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    by_scope = {
        scope: {"calls_attempted": 0, "transitions": 0, "call_status_counts": {}}
        for scope in _REPAIR_SCOPES
    }
    status_values: list[str] = []
    calls_attempted = 0
    transitions = 0
    for episode in episodes:
        measurement = episode["measurement"]
        accounting = measurement.get("repair_accounting")
        if not isinstance(accounting, dict):
            status_values.append("incomplete")
            continue
        status_values.append(str(accounting.get("status", "incomplete")))
        calls_attempted += int(measurement.get("repair_calls_attempted", 0) or 0)
        transitions += int(measurement.get("repair_transitions", 0) or 0)
        episode_scopes = accounting.get("by_scope")
        if not isinstance(episode_scopes, dict):
            continue
        for scope in _REPAIR_SCOPES:
            values = episode_scopes.get(scope)
            if not isinstance(values, dict):
                continue
            target = by_scope[scope]
            target["calls_attempted"] += int(values.get("calls_attempted", 0) or 0)
            target["transitions"] += int(values.get("transitions", 0) or 0)
            status_counts = values.get("call_status_counts")
            if isinstance(status_counts, dict):
                for status, count in status_counts.items():
                    name = str(status)
                    target["call_status_counts"][name] = (
                        target["call_status_counts"].get(name, 0) + int(count or 0)
                    )
    return {
        "repair_calls_attempted": calls_attempted,
        "repair_transitions": transitions,
        "repair_accounting": {
            "status_counts": _count_values(status_values),
            "by_scope": by_scope,
        },
    }


def _repair_success_count(episodes: list[dict[str, Any]]) -> int:
    return sum(
        int(
            episode["measurement"].get("repair_success") is True
            and episode["measurement"].get("repair_transitions", 0) > 0
            and isinstance(episode["measurement"].get("repair_accounting"), dict)
            and episode["measurement"]["repair_accounting"].get("status") == "complete"
        )
        for episode in episodes
    )


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _level_rank(level: Any) -> int:
    return _LEVEL_RANK.get(str(level), -2)
