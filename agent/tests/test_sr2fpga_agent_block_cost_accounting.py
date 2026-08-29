from __future__ import annotations

import hashlib
import json

import pytest

from sr2fpga_agent.artifact_store import ArtifactRef, ArtifactStore
from sr2fpga_agent.block_cost_accounting import (
    BlockPreparationCostLedger,
    BlockPreparationCostLedgerError,
    replay_development_block_preparation,
)
from sr2fpga_agent.cost_accounting import COST_AXES
from sr2fpga_agent.model_budget import ModelCallBudget


def _ref(store: ArtifactStore, key: str) -> ArtifactRef:
    return store.put_blob(key, b"{}", media_type="application/json")


def _provider_cost(*, transport: int, wall_time: float) -> dict[str, int | float]:
    return {
        "input_tokens": 3,
        "output_tokens": 2,
        "cached_tokens": 0,
        "provider_transport_attempts": transport,
        "wall_time": wall_time,
    }


def _remaining_zero_axes(ledger: BlockPreparationCostLedger) -> set[str]:
    return set(COST_AXES) - set(ledger.observed_axes)


def test_replay_counts_shared_call_once_and_excludes_close_delta(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    paired_ref = _ref(store, "paired/a/paired-block")
    ledger = BlockPreparationCostLedger(
        store, paired_block_ref=paired_ref, failure_origin="natural_llm"
    )
    ledger.activate_checkpoint("direct_initial_project")
    ledger.reserve(
        "logical_model_calls",
        1,
        stage="block_direct_initial",
        visibility_class="accounting",
        limit=3,
        used_after=1,
        started_at=1.0,
    )
    ledger.record_cost(
        stage="block_direct_initial",
        visibility_class="accounting",
        cost_delta=_provider_cost(transport=1, wall_time=0.25),
        started_at=1.0,
    )
    ledger.record_checkpoint(
        checkpoint_id="direct_initial_project",
        event_kind="checkpoint_materialized",
        status="completed",
        output_refs=(_ref(store, "paired/a/direct-project"),),
    )
    ledger.close(zero_axes=_remaining_zero_axes(ledger))

    replay = replay_development_block_preparation(store, ledger.event_refs)

    assert replay.actual_axes["logical_model_calls"] == {
        "status": "measured",
        "value": 1,
        "reason": None,
    }
    assert replay.actual_axes["wall_time"] == {
        "status": "measured",
        "value": 0.25,
        "reason": None,
    }
    assert replay.checkpoint_axes["direct_initial_project"]["wall_time"]["value"] == 0.25
    assert len(replay.event_refs) == 4
    assert all(store.read_verified(reference) for reference in replay.event_refs)


def test_model_budget_charges_finish_duration_once_to_block_ledger(monkeypatch, tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    ledger = BlockPreparationCostLedger(
        store,
        paired_block_ref=_ref(store, "paired/b/paired-block"),
        failure_origin=None,
    )
    ledger.activate_checkpoint("shared_system_his")
    times = iter((2.0, 2.25))
    monkeypatch.setattr(
        "sr2fpga_agent.model_budget.time.monotonic", lambda: next(times)
    )
    budget = ModelCallBudget(1, attempt_cost_ledger=ledger)
    call_id, started = budget.reserve("block_req2his", "chat", 0)
    budget.finish(
        call_id,
        "block_req2his",
        "chat",
        started,
        provider_transport_attempts=1,
        provider_token_usage={"input_tokens": 1, "output_tokens": 1, "cached_tokens": 0},
    )
    ledger.close(zero_axes=_remaining_zero_axes(ledger))

    replay = replay_development_block_preparation(store, ledger.event_refs)

    assert replay.actual_axes["logical_model_calls"]["value"] == 1
    assert replay.actual_axes["wall_time"]["value"] == 0.25


def test_replay_rejects_tampered_chain_and_close_total(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "store")
    ledger = BlockPreparationCostLedger(
        store,
        paired_block_ref=_ref(store, "paired/c/paired-block"),
        failure_origin=None,
    )
    ledger.activate_checkpoint("shared_system_his")
    ledger.record_cost(
        stage="block_req2his",
        visibility_class="accounting",
        cost_delta={"logical_model_calls": 1, "wall_time": 1.0},
    )
    ledger.close(zero_axes=_remaining_zero_axes(ledger))

    tampered_store = ArtifactStore(tmp_path / "tampered")
    _ref(tampered_store, "paired/c/paired-block")
    first = json.loads(store.read_verified(ledger.event_refs[0]))
    first_ref = tampered_store.put_validated_json(
        "block-preparation-events/"
        + ledger.paired_block_ref.sha256
        + "/000000-"
        + first["event_id"],
        first,
        contract_key="development_block_preparation_event",
    )
    close = json.loads(store.read_verified(ledger.event_refs[-1]))
    close["cost_delta"]["logical_model_calls"] = 2
    unsigned = {key: value for key, value in close.items() if key != "event_id"}
    close["event_id"] = "block-preparation-event-" + hashlib.sha256(
        json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    close_ref = tampered_store.put_validated_json(
        "block-preparation-events/"
        + ledger.paired_block_ref.sha256
        + "/000001-"
        + close["event_id"],
        close,
        contract_key="development_block_preparation_event",
    )

    with pytest.raises(BlockPreparationCostLedgerError, match="close totals"):
        replay_development_block_preparation(tampered_store, (first_ref, close_ref))
