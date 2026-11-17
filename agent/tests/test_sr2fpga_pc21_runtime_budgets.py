"""Protocol-derived resource and recovery tests; no providers or EDA tools."""

from dataclasses import replace
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sr2fpga_agent.artifact_store import ArtifactIntegrityError, ArtifactStore
from sr2fpga_agent.execution.budgets import (
    B4_MODEL_CALLS, BudgetBusy, BudgetError, BudgetExceeded, BudgetLedger, BudgetLimits,
)


def limits(method="M1", **changes):
    values = dict(max_total_input_tokens=1000, max_total_output_tokens=400,
                  max_single_output_tokens=100, max_context_tokens=300,
                  max_public_tool_calls=20, max_active_seconds=120,
                  max_eda_seconds=60, max_cpu_seconds=120, max_memory_bytes=1024)
    values.update(changes)
    return BudgetLimits.for_method(method, **values)


def ledger(tmp_path, methods=("M1",), **changes):
    return BudgetLedger(ArtifactStore(tmp_path / "store"), "paired-block-1",
                        {method: limits(method, **changes) for method in methods})


def model_call(authority, operation, consumers, *, input_tokens=10, output_tokens=20, outcome="completed"):
    reservation = authority.reserve(operation, consumers, model_calls=1, input_tokens=input_tokens,
                                    output_tokens=output_tokens, context_tokens=input_tokens+output_tokens,
                                    active_seconds=2, token_reservation_kind="exact")
    authority.dispatch(reservation.reservation_id)
    authority.reconcile(reservation.reservation_id, outcome=outcome,
                        observed={"input_tokens": input_tokens, "output_tokens": output_tokens,
                                  "context_tokens": input_tokens+output_tokens, "active_seconds": 1})
    return reservation


@pytest.mark.parametrize("field,value", [
    ("max_model_calls", True), ("max_total_input_tokens", 1.5),
    ("max_total_output_tokens", -1), ("max_active_seconds", float("nan")),
    ("max_eda_seconds", float("inf")), ("max_cpu_seconds", True),
    ("max_memory_bytes", -1), ("max_context_tokens", False),
])
def test_invalid_axes_fail_before_an_allocation_can_exist(field, value):
    with pytest.raises(ValueError):
        replace(limits(), **{field: value})


def test_limits_require_every_resource_axis_and_exact_b4_allocation(tmp_path):
    with pytest.raises(ValueError, match="every registered"):
        BudgetLimits.from_dict({"max_model_calls": 4})
    with pytest.raises(ValueError, match="B4"):
        BudgetLedger(ArtifactStore(tmp_path), "x", {"M1": replace(limits(), max_model_calls=3)})
    with pytest.raises(ValueError, match="public-cycle"):
        BudgetLedger(ArtifactStore(tmp_path), "y", {"M0": replace(limits("M0"), max_public_cycles=4)})


def test_failed_calls_spend_calls_and_reopening_does_not_reset_them(tmp_path):
    authority = ledger(tmp_path, ("M0",))
    model_call(authority, "initial-direct", ["M0"], outcome="failed")
    reopened = ledger(tmp_path, ("M0",))
    assert reopened.remaining("M0", "model_calls") == 0
    assert reopened.snapshot()["budget_status"] == "compliant"
    with pytest.raises(BudgetExceeded, match="model_calls"):
        reopened.reserve("retry", ["M0"], model_calls=1)


def test_shared_dag_is_six_actual_ten_attributed_then_eleven_fifteen(tmp_path):
    authority = ledger(tmp_path, tuple(B4_MODEL_CALLS))
    for name, consumers in (("direct", ["M0", "M1"]), ("pc", ["M3", "M4", "M5"]),
                            ("m3-free", ["M3"]), ("body", ["M4", "M5"]),
                            ("untyped", ["M2"]), ("m2-free", ["M2"])):
        model_call(authority, name, consumers)
    initial = authority.snapshot()
    assert initial["actual"]["used"]["model_calls"] == 6
    assert sum(item["used"]["model_calls"] for item in initial["methods"].values()) == 10
    assert authority.remaining("M1", "model_calls") == 3
    assert authority.remaining("M5", "model_calls") == 2
    for method, count in (("M1", 3), ("M5", 2)):
        for index in range(count):
            model_call(authority, method+"-repair-"+str(index), [method])
    terminal = authority.snapshot()
    assert terminal["actual"]["used"]["model_calls"] == 11
    assert sum(item["used"]["model_calls"] for item in terminal["methods"].values()) == 15
    assert terminal["budget_status"] == "compliant"
    assert all(item["remaining"]["model_calls"] == 0 for item in terminal["methods"].values())


def test_pc_failure_leaves_only_actually_spent_calls_charged(tmp_path):
    authority = ledger(tmp_path, ("M3", "M4", "M5"))
    model_call(authority, "invalid-pc", ["M3", "M4", "M5"], outcome="failed")
    assert authority.remaining("M5", "model_calls") == 3
    assert authority.snapshot()["actual"]["used"]["model_calls"] == 1


def test_shared_reservation_checks_all_consumers_atomically(tmp_path):
    store = ArtifactStore(tmp_path)
    authority = BudgetLedger(store, "shared", {"M0": limits("M0"), "M1": limits("M1", max_total_input_tokens=5)})
    before = len(store.event_refs(authority._event_stream))
    with pytest.raises(BudgetExceeded, match="M1 input_tokens"):
        authority.reserve("direct", ["M0", "M1"], model_calls=1, input_tokens=6,
                          output_tokens=10, context_tokens=16,
                          metadata={"token_bound_source": "fixture_transport_limit"})
    assert len(store.event_refs(authority._event_stream)) == before
    assert authority.remaining("M0", "model_calls") == 1


def test_token_bounds_and_context_are_checked_before_dispatch(tmp_path):
    authority = ledger(tmp_path)
    with pytest.raises(BudgetExceeded, match="single output"):
        authority.reserve("too-long", ["M1"], model_calls=1, output_tokens=101, context_tokens=101,
                          metadata={"token_bound_source": "fixture_transport_limit"})
    with pytest.raises(BudgetExceeded, match="context_tokens"):
        authority.reserve("context", ["M1"], model_calls=1, input_tokens=250, output_tokens=60, context_tokens=310,
                          metadata={"token_bound_source": "fixture_transport_limit"})
    with pytest.raises(ValueError, match="include reserved"):
        authority.reserve("bad-context", ["M1"], model_calls=1, input_tokens=10, output_tokens=10, context_tokens=10)
    assert authority.remaining("M1", "model_calls") == 4


def test_upper_bounds_are_not_measured_tokens_and_unknown_retains_reservation(tmp_path):
    authority = ledger(tmp_path)
    reservation = authority.reserve("uncertain", ["M1"], model_calls=1, input_tokens=50,
                                    output_tokens=100, context_tokens=150,
                                    metadata={"token_bound_source": "fixture_transport_limit"})
    authority.dispatch(reservation.reservation_id)
    authority.reconcile(reservation.reservation_id, outcome="unknown", observed={},
                        unavailable_reasons={"input_tokens": "provider_usage_unavailable"})
    reopened = ledger(tmp_path)
    summary = reopened.snapshot()
    assert summary["actual"]["observed"]["input_tokens"] == 0
    assert summary["actual"]["used"]["input_tokens"] == 50
    assert summary["actual"]["used"]["output_tokens"] == 100
    assert summary["budget_status"] == "unverifiable"
    assert reopened.remaining("M1", "model_calls") == 3
    with pytest.raises(BudgetError, match="already dispatched"):
        reopened.dispatch(reservation.reservation_id)
    # A later provider receipt settles the original request, without a second call.
    reopened.reconcile(reservation.reservation_id,
                       observed={"input_tokens": 40, "output_tokens": 20, "context_tokens": 60})
    assert reopened.snapshot()["budget_status"] == "compliant"
    assert reopened.remaining("M1", "model_calls") == 3
    assert reopened.remaining("M1", "output_tokens") == 380


def test_late_usage_can_fill_unknown_costs_but_cannot_rewrite_measured_costs(tmp_path):
    authority = ledger(tmp_path)
    reservation = authority.reserve("missing-cost", ["M1"], model_calls=1, input_tokens=10,
                                    output_tokens=100, context_tokens=110,
                                    metadata={"token_bound_source": "fixture_transport_limit"})
    authority.dispatch(reservation.reservation_id)
    authority.reconcile(reservation.reservation_id, observed={"input_tokens": 10})
    assert authority.snapshot()["budget_status"] == "unverifiable"
    authority.reconcile(reservation.reservation_id, observed={"output_tokens": 20, "context_tokens": 30})
    assert ledger(tmp_path).snapshot()["budget_status"] == "compliant"
    with pytest.raises(BudgetError, match="conflicting final"):
        authority.reconcile(reservation.reservation_id, observed={"input_tokens": 9})


def test_cancel_only_before_dispatch_and_final_receipts_are_idempotent(tmp_path):
    authority = ledger(tmp_path)
    reservation = authority.reserve("cancelled", ["M1"], model_calls=1)
    authority.cancel(reservation.reservation_id, reason="not_sent")
    assert authority.remaining("M1", "model_calls") == 4
    reservation = model_call(authority, "sent", ["M1"])
    with pytest.raises(BudgetError, match="cannot be refunded"):
        authority.cancel(reservation.reservation_id, reason="pretend_unused")
    before = len(authority.store.event_refs(authority._event_stream))
    authority.reconcile(reservation.reservation_id, observed={"input_tokens": 10, "output_tokens": 20,
                        "context_tokens": 30, "active_seconds": 1})
    assert len(authority.store.event_refs(authority._event_stream)) == before
    with pytest.raises(BudgetError, match="conflicting final"):
        authority.reconcile(reservation.reservation_id, observed={"input_tokens": 10, "output_tokens": 21})


def test_actual_overages_are_preserved_and_block_future_side_effects(tmp_path):
    authority = ledger(tmp_path)
    reservation = authority.reserve("overshoot", ["M1"], model_calls=1, input_tokens=10,
                                    output_tokens=100, context_tokens=110,
                                    metadata={"token_bound_source": "fixture_transport_limit"})
    authority.dispatch(reservation.reservation_id)
    authority.reconcile(reservation.reservation_id, observed={"input_tokens": 10, "output_tokens": 120,
                                                            "context_tokens": 130})
    summary = authority.snapshot()
    assert summary["actual"]["observed"]["output_tokens"] == 120
    assert summary["budget_status"] == "exceeded"
    assert "single_output_tokens" in summary["methods"]["M1"]["overages"]
    with pytest.raises(BudgetExceeded, match="already exceeded"):
        authority.reserve("next", ["M1"], model_calls=1)


def test_peak_axes_are_not_summed_and_times_are_summed(tmp_path):
    authority = ledger(tmp_path)
    for index in range(2):
        reservation = authority.reserve(str(index), ["M1"], public_tool_calls=1,
                                        active_seconds=10, eda_seconds=5, cpu_seconds=7, memory_bytes=1000)
        authority.dispatch(reservation.reservation_id)
        authority.reconcile(reservation.reservation_id, observed={"active_seconds": 2.5,
                            "eda_seconds": 1.5, "cpu_seconds": 2, "memory_bytes": 900})
    state = authority.snapshot()["methods"]["M1"]
    assert state["used"]["active_seconds"] == 5
    assert state["used"]["eda_seconds"] == 3
    assert state["used"]["cpu_seconds"] == 4
    assert state["used"]["memory_bytes"] == 900
    assert state["used"]["public_tool_calls"] == 2


def test_public_cycle_budget_is_not_reset_by_reopen(tmp_path):
    authority = ledger(tmp_path)
    for index in range(4):
        reservation = authority.reserve("cycle"+str(index), ["M1"], public_cycles=1)
        authority.dispatch(reservation.reservation_id)
        authority.reconcile(reservation.reservation_id, observed={})
    reopened = ledger(tmp_path)
    with pytest.raises(BudgetExceeded, match="public_cycles"):
        reopened.reserve("cycle4", ["M1"], public_cycles=1)


def test_reopening_cannot_rewrite_limits_or_rebind_operation(tmp_path):
    authority = ledger(tmp_path)
    first = authority.reserve("same", ["M1"], model_calls=1)
    assert authority.reserve("same", ["M1"], model_calls=1).reservation_id == first.reservation_id
    with pytest.raises(BudgetError, match="different reservation"):
        authority.reserve("same", ["M1"], model_calls=1, input_tokens=1, context_tokens=1,
                          metadata={"token_bound_source": "fixture_transport_limit"})
    with pytest.raises(BudgetError, match="cannot change"):
        ledger(tmp_path, max_total_input_tokens=2000)


def test_budget_blob_tampering_fails_closed(tmp_path):
    authority = ledger(tmp_path)
    authority.reserve("one", ["M1"], model_calls=1)
    reference = authority.store.event_refs(authority._event_stream)[0]
    blob = authority.store.root / "blobs" / reference.sha256[:2] / reference.sha256
    blob.write_bytes(b"{}")
    with pytest.raises(ArtifactIntegrityError):
        authority.snapshot()


@pytest.mark.parametrize("source", [None, "", " ", False])
def test_token_upper_bounds_require_recorded_provenance(tmp_path, source):
    authority = ledger(tmp_path)
    with pytest.raises(ValueError, match="token_bound_source"):
        authority.reserve("unproven", ["M1"], model_calls=1, input_tokens=10,
                          output_tokens=20, context_tokens=30, metadata={"token_bound_source": source})
    assert authority.remaining("M1", "model_calls") == 4


def test_nonfinite_metadata_cannot_create_an_invalid_json_event(tmp_path):
    authority = ledger(tmp_path)
    with pytest.raises(ValueError):
        authority.reserve("bad-json", ["M1"], public_cycles=1, metadata={"nested": [float("nan")]})
    assert authority.remaining("M1", "public_cycles") == 4


def test_file_lock_protects_independent_controllers(tmp_path):
    authority = ledger(tmp_path)
    with authority._locked():
        with pytest.raises(BudgetBusy):
            authority.reserve("racing", ["M1"], model_calls=1)
    assert authority.remaining("M1", "model_calls") == 4


def test_second_process_observes_existing_consumption(tmp_path):
    authority = ledger(tmp_path, ("M0",))
    model_call(authority, "once", ["M0"])
    script = """import json,sys
from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.execution.budgets import BudgetLimits,BudgetLedger
config=json.loads(sys.argv[2])
ledger=BudgetLedger(ArtifactStore(sys.argv[1]),'paired-block-1',{'M0':BudgetLimits.from_dict(config)})
assert ledger.remaining('M0','model_calls')==0
print('persisted')
"""
    completed = subprocess.run([sys.executable, "-B", "-c", script, str(authority.store.root),
                                json.dumps(limits("M0").to_dict())], capture_output=True, text=True,
                               timeout=15, cwd=Path(__file__).resolve().parents[2],
                               env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")})
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "persisted"


def test_os_lock_blocks_a_different_process_without_spending_a_call(tmp_path):
    authority = ledger(tmp_path)
    script = """import json,sys
from sr2fpga_agent.artifact_store import ArtifactStore
from sr2fpga_agent.execution.budgets import BudgetLimits,BudgetLedger,BudgetBusy
try:
 BudgetLedger(ArtifactStore(sys.argv[1]),'paired-block-1',{'M1':BudgetLimits.from_dict(json.loads(sys.argv[2]))})
except BudgetBusy:
 print('blocked')
else:
 raise SystemExit('cross-process lock was bypassed')
"""
    with authority._locked():
        completed = subprocess.run([sys.executable, "-B", "-c", script, str(authority.store.root),
                                    json.dumps(limits().to_dict())], capture_output=True, text=True,
                                   timeout=15, cwd=Path(__file__).resolve().parents[2],
                                   env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")})
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "blocked"
    assert authority.remaining("M1", "model_calls") == 4
