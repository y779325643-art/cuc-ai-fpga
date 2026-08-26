import copy
import hashlib
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.target_profile_pairs import (
    build_development_target_profile_pair_outcome,
    build_pilot_target_profile_pair_manifest,
    validate_development_target_profile_pair_outcome,
    validate_pilot_target_profile_pair_manifest,
)


def _pair() -> dict:
    return {
        "profile_pair_id": "pilot-pair-001",
        "semantic_instance_id": "semantic-001",
        "family_id": "fir_filter",
        "semantic_obligation_sha256": "a" * 64,
        "hidden_oracle_commitment_sha256": "b" * 64,
        "change_axes": ["clock_target"],
        "functional_invariant_ids": ["same_cycle_accurate_function"],
        "required_change_ids": ["clock_period_constraint"],
        "allowed_change_ids": ["clock_period_constraint", "timing_exception"],
        "forbidden_change_ids": ["rtl_function_change", "hidden_oracle_change"],
        "profile_compliance_commitment_sha256": "c" * 64,
        "endpoints": {
            "l3": "independent_synthesis",
            "l4": "openxc7_post_route",
        },
        "members": [
            {
                "member_role": "baseline",
                "profile_member_id": "pilot-pair-001-baseline",
                "target_profile_id": "artix7-100mhz",
                "target_profile_sha256": "d" * 64,
            },
            {
                "member_role": "variant",
                "profile_member_id": "pilot-pair-001-variant",
                "target_profile_id": "artix7-125mhz",
                "target_profile_sha256": "e" * 64,
            },
        ],
        "objective_exclusion_ids": ["official_target_profile_population"],
        "paired_cost_rule": "full_pair_all_outcomes",
        "tpa_l4_rule": "both_members_complete_and_compliant",
    }


def _manifest() -> dict:
    return build_pilot_target_profile_pair_manifest(
        "pilot-profile-pairs-001", "f" * 64, [_pair()]
    )


def _axis(value: float = 1.0) -> dict:
    return {"status": "measured", "value": value, "reason": None}


def _cost_summary(method: str, attempt_id: str, value: float) -> dict:
    return {
        "contract_version": "cost-summary-v1",
        "episode_id": f"episode-{attempt_id}",
        "attempt_id": attempt_id,
        "method_condition": method,
        "source_event_ids": ["attempt-event-" + ("1" if value == 1 else "2") * 64],
        "source_events_sha256": ("3" if value == 1 else "4") * 64,
        "event_count": 1,
        "failure_count": 0,
        "budget_exhaustion_count": 0,
        "accounting_closed": True,
        "all_required_axes_reconciled": True,
        "axes": {
            "logical_model_calls": _axis(value),
            "input_tokens": _axis(value),
            "output_tokens": _axis(value),
            "cached_tokens": _axis(value),
            "provider_transport_attempts": _axis(value),
            "planner_parser_schema_retries": _axis(value),
            "outer_repair_attempts": _axis(value),
            "public_tool_calls": _axis(value),
            "hidden_evaluator_tool_calls": _axis(value),
            "hidden_infrastructure_retries": _axis(value),
            "wall_time": _axis(value),
            "eda_time": _axis(value),
            "hidden_evaluator_runtime": _axis(value),
        },
    }


def _observations(store: ArtifactStore, method: str = "M4") -> list[dict]:
    records = []
    for index, member in enumerate(_pair()["members"], start=1):
        candidate_ref = store.put_blob(
            f"candidates/{member['member_role']}",
            json.dumps({"member": member["member_role"]}).encode(),
            media_type="application/json",
        )
        cost_ref = store.put_validated_json(
            f"cost/{member['member_role']}",
            _cost_summary(method, f"attempt-{index}", float(index)),
            contract_key="cost_summary",
        )
        records.append(
            {
                **member,
                "execution_status": "completed",
                "candidate_ref": candidate_ref.to_dict(),
                "invariant_status": "pass",
                "required_changes_status": "pass",
                "forbidden_changes_status": "pass",
                "profile_compliance_status": "pass",
                "l3_status": "pass",
                "l4_status": "pass",
                "violation_ids": [],
                "cost_summary_ref": cost_ref.to_dict(),
            }
        )
    return records


def _rehash(artifact: dict) -> None:
    payload = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    artifact["artifact_sha256"] = hashlib.sha256(raw.encode()).hexdigest()


def test_pilot_manifest_is_closed_excluded_and_hash_bound() -> None:
    manifest = _manifest()

    assert manifest["population_role"] == "pilot_only_excluded"
    assert manifest["official_population"] is False
    assert manifest["g4b_authorized"] is False
    assert manifest["official_authority"] is False
    validate_pilot_target_profile_pair_manifest(manifest)

    tampered = copy.deepcopy(manifest)
    tampered["pairs"][0]["change_axes"] = ["device_part"]
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        validate_pilot_target_profile_pair_manifest(tampered)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("required_change_ids", ["not_allowed"], "subset"),
        ("forbidden_change_ids", ["clock_period_constraint"], "disjoint"),
        ("change_axes", ["clock_target", "device_part"], "compound_profile"),
        ("objective_exclusion_ids", ["some_other_exclusion"], "official"),
    ),
)
def test_manifest_cross_field_rules_fail_closed(field, value, message) -> None:
    pair = _pair()
    pair[field] = value
    with pytest.raises(ValueError, match=message):
        build_pilot_target_profile_pair_manifest("invalid-pairs", "f" * 64, [pair])


def test_complete_development_pair_reconciles_full_cost_without_official_credit(
    tmp_path,
) -> None:
    store = ArtifactStore(tmp_path / "store")
    manifest = _manifest()

    outcome = build_development_target_profile_pair_outcome(
        manifest,
        "pilot-pair-001",
        "M4",
        _observations(store),
        store=store,
    )

    assert outcome["pair_completeness"] == "complete"
    assert outcome["tpa_l4_status"] == "pass"
    assert outcome["tpa_l4_reasons"] == []
    assert outcome["paired_cost"]["status"] == "complete"
    assert outcome["paired_cost"]["axes"]["logical_model_calls"]["value"] == 3.0
    assert outcome["terminal_binding"] is False
    assert outcome["pass_credit_authority"] is False
    assert outcome["official_authority"] is False


def test_forbidden_change_failure_retains_complete_pair_and_fails_development_tpa(
    tmp_path,
) -> None:
    store = ArtifactStore(tmp_path / "store")
    observations = _observations(store)
    observations[1]["forbidden_changes_status"] = "fail"
    observations[1]["violation_ids"] = ["rtl_function_change"]

    outcome = build_development_target_profile_pair_outcome(
        _manifest(), "pilot-pair-001", "M4", observations, store=store
    )

    assert outcome["pair_completeness"] == "complete"
    assert outcome["tpa_l4_status"] == "fail"
    assert outcome["tpa_l4_reasons"] == ["forbidden_change_detected"]


def test_failed_compliance_requires_a_named_violation(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    observations = _observations(store)
    observations[1]["profile_compliance_status"] = "fail"

    with pytest.raises(ValueError, match="requires at least one violation_id"):
        build_development_target_profile_pair_outcome(
            _manifest(), "pilot-pair-001", "M4", observations, store=store
        )


def test_missing_member_cost_is_not_replaced_and_makes_pair_not_run(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    observations = _observations(store)
    observations[1]["cost_summary_ref"] = None

    outcome = build_development_target_profile_pair_outcome(
        _manifest(), "pilot-pair-001", "M4", observations, store=store
    )

    assert outcome["pair_completeness"] == "incomplete"
    assert outcome["tpa_l4_status"] == "not_run"
    assert outcome["tpa_l4_reasons"] == ["paired_cost_incomplete"]
    axis = outcome["paired_cost"]["axes"]["logical_model_calls"]
    assert axis == {
        "status": "unavailable",
        "value": None,
        "reason": "member_axis_unavailable",
    }


def test_member_identity_and_cost_method_mismatch_are_rejected(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    observations = _observations(store)
    observations[1]["target_profile_sha256"] = "9" * 64
    with pytest.raises(ValueError, match="target_profile_sha256 mismatch"):
        build_development_target_profile_pair_outcome(
            _manifest(), "pilot-pair-001", "M4", observations, store=store
        )

    with pytest.raises(ValueError, match="method_condition mismatch"):
        build_development_target_profile_pair_outcome(
            _manifest(), "pilot-pair-001", "M5", _observations(store), store=store
        )


def test_noncompleted_member_cannot_claim_stage_results(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    observations = _observations(store)
    observations[1]["execution_status"] = "infrastructure_error"

    with pytest.raises(ValueError, match="all evaluation stages not_run"):
        build_development_target_profile_pair_outcome(
            _manifest(), "pilot-pair-001", "M4", observations, store=store
        )


def test_member_observation_rejects_raw_or_private_output_field(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    observations = _observations(store)
    observations[0]["raw_compliance_output"] = "PRIVATE-CONTENT"

    with pytest.raises(ValueError, match="extra=.*raw_compliance_output"):
        build_development_target_profile_pair_outcome(
            _manifest(), "pilot-pair-001", "M4", observations, store=store
        )


@pytest.mark.parametrize(
    "field", ("terminal_binding", "pass_credit_authority", "official_authority")
)
def test_development_outcome_rejects_authority_escalation(tmp_path, field) -> None:
    store = ArtifactStore(tmp_path / "store")
    outcome = build_development_target_profile_pair_outcome(
        _manifest(), "pilot-pair-001", "M4", _observations(store), store=store
    )
    outcome[field] = True

    with pytest.raises(ValueError, match="invalid development"):
        validate_development_target_profile_pair_outcome(outcome)


@pytest.mark.parametrize(
    ("mutator", "message"),
    (
        (
            lambda outcome: outcome.update(
                {"tpa_l4_status": "fail", "tpa_l4_reasons": ["l4_failure"]}
            ),
            "reasons do not match",
        ),
        (
            lambda outcome: outcome["paired_cost"]["axes"][
                "logical_model_calls"
            ].update({"value": 999.0}),
            "axes do not match",
        ),
        (
            lambda outcome: outcome["paired_cost"]["member_cost_summary_refs"].reverse(),
            "references do not match",
        ),
    ),
)
def test_recomputed_artifact_hash_cannot_hide_reducer_tamper(
    tmp_path, mutator, message
) -> None:
    store = ArtifactStore(tmp_path / "store")
    outcome = build_development_target_profile_pair_outcome(
        _manifest(), "pilot-pair-001", "M4", _observations(store), store=store
    )
    mutator(outcome)
    _rehash(outcome)

    with pytest.raises(ValueError, match=message):
        validate_development_target_profile_pair_outcome(outcome)
