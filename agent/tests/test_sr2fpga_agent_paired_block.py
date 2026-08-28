import copy
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.paired_block import (
    METHODS,
    build_balanced_method_orders,
    build_development_paired_block,
    development_paired_block_reference,
    load_development_paired_block,
    write_development_paired_block,
)


def _write_block(store: ArtifactStore, **overrides):
    schedule_seed = overrides.pop("execution_schedule_seed", 991)
    method_order = overrides.pop(
        "method_order", build_balanced_method_orders(schedule_seed)[0]
    )
    arguments = {
        "paired_block_id": "pair-fir-001-replicate-000",
        "semantic_instance_id": "semantic-fir-001",
        "replicate_id": "replicate-000",
        "public_projection_sha256": "1" * 64,
        "model_provenance_sha256": "2" * 64,
        "decoding_control_mode": "documented_seed_control",
        "requested_decoding_seed": 17,
        "execution_schedule_seed": schedule_seed,
        "method_order": method_order,
    }
    arguments.update(overrides)
    return write_development_paired_block(store, **arguments)


def test_balanced_method_orders_are_seeded_permutations() -> None:
    first = build_balanced_method_orders(991)
    repeated = build_balanced_method_orders(991)
    different = build_balanced_method_orders(992)

    assert first == repeated
    assert first != different
    assert len(first) == len(METHODS) == 6
    assert len(set(first)) == 6
    assert all(set(order) == set(METHODS) for order in first)


def test_balanced_method_orders_balance_positions_and_predecessors() -> None:
    orders = build_balanced_method_orders(991)

    for position in range(len(METHODS)):
        assert {order[position] for order in orders} == set(METHODS)

    predecessor_pairs = {
        (order[position], order[position + 1])
        for order in orders
        for position in range(len(METHODS) - 1)
    }
    assert len(predecessor_pairs) == len(METHODS) * (len(METHODS) - 1)


@pytest.mark.parametrize("seed", (-1, True, 1.5, "991"))
def test_balanced_method_orders_reject_invalid_schedule_seed(seed) -> None:
    with pytest.raises(ValueError, match="execution_schedule_seed"):
        build_balanced_method_orders(seed)


@pytest.mark.parametrize("schedule_seed", (991, 992))
def test_development_paired_block_round_trips_through_artifact_store(
    tmp_path, schedule_seed
) -> None:
    store = ArtifactStore(tmp_path / "store")

    reference = _write_block(store, execution_schedule_seed=schedule_seed)
    payload = load_development_paired_block(store, reference)

    assert reference.key.startswith("paired-blocks/")
    assert payload["method_order"] == list(
        build_balanced_method_orders(schedule_seed)[0]
    )
    assert payload["requested_decoding_seed"] == 17
    assert payload["official_outcome"] is False
    assert payload["official_authority"] is False
    assert payload["pass_credit_authority"] is False
    assert payload["g3_accepted"] is False
    assert payload["g4b_authorized"] is False


def test_pure_planned_reference_matches_materialized_reference(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    arguments = {
        "paired_block_id": "pair-fir-planned-001",
        "semantic_instance_id": "semantic-fir-001",
        "replicate_id": "replicate-000",
        "public_projection_sha256": "1" * 64,
        "model_provenance_sha256": "2" * 64,
        "decoding_control_mode": "documented_seed_control",
        "requested_decoding_seed": 17,
        "execution_schedule_seed": 991,
        "method_order": build_balanced_method_orders(991)[0],
    }

    payload = build_development_paired_block(**arguments)
    planned = development_paired_block_reference(payload)
    materialized = write_development_paired_block(store, **arguments)

    assert planned == materialized


def test_writer_uses_filesystem_safe_key_for_contract_legal_colon_id(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")

    reference = _write_block(store, paired_block_id="pair:fir:001")
    payload = load_development_paired_block(store, reference)

    assert reference.key.startswith("paired-blocks/")
    assert ":" not in reference.key.removeprefix("paired-blocks/")
    assert payload["paired_block_id"] == "pair:fir:001"


def test_stochastic_blocked_mode_accepts_null_requested_seed(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")

    reference = _write_block(
        store,
        decoding_control_mode="stochastic_blocked",
        requested_decoding_seed=None,
    )

    assert load_development_paired_block(store, reference)[
        "requested_decoding_seed"
    ] is None


def test_writer_rejects_schema_valid_order_not_derived_from_schedule_seed(
    tmp_path,
) -> None:
    store = ArtifactStore(tmp_path / "store")
    allowed = set(build_balanced_method_orders(991))
    arbitrary = tuple(METHODS)
    if arbitrary in allowed:
        arbitrary = tuple(reversed(METHODS))
    assert arbitrary not in allowed

    with pytest.raises(ValueError, match="balanced order"):
        _write_block(store, method_order=arbitrary)


def test_writer_rejects_invalid_decoding_control_pair(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")

    with pytest.raises(ValueError, match="invalid development paired block"):
        _write_block(store, requested_decoding_seed=None)


def test_loader_revalidates_schedule_order_cross_field_rule(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    reference = _write_block(store)
    payload = json.loads(store.read_verified(reference))
    tampered = copy.deepcopy(payload)
    allowed = set(build_balanced_method_orders(991))
    arbitrary = tuple(METHODS)
    if arbitrary in allowed:
        arbitrary = tuple(reversed(METHODS))
    tampered["method_order"] = list(arbitrary)
    raw_reference = store.put_blob(
        "paired-blocks/raw-tampered",
        json.dumps(tampered, sort_keys=True, separators=(",", ":")).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError, match="balanced order"):
        load_development_paired_block(store, raw_reference)


def test_loader_rejects_schedule_seed_changed_without_matching_order(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    reference = _write_block(store)
    payload = json.loads(store.read_verified(reference))
    original_order = tuple(payload["method_order"])
    changed_seed = next(
        seed
        for seed in range(992, 1100)
        if original_order not in build_balanced_method_orders(seed)
    )
    payload["execution_schedule_seed"] = changed_seed
    raw_reference = store.put_blob(
        "paired-blocks/schedule-tampered",
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError, match="balanced order"):
        load_development_paired_block(store, raw_reference)


def test_loader_rejects_authority_escalation(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    reference = _write_block(store)
    payload = json.loads(store.read_verified(reference))
    payload["g3_accepted"] = True
    raw_reference = store.put_blob(
        "paired-blocks/authority-tampered",
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
        media_type="application/json",
    )

    with pytest.raises(ValueError, match="invalid development paired block"):
        load_development_paired_block(store, raw_reference)


def test_loader_rejects_non_object_json(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    reference = store.put_blob(
        "paired-blocks/not-an-object",
        b"[]",
        media_type="application/json",
    )

    with pytest.raises(ValueError, match="JSON object"):
        load_development_paired_block(store, reference)
