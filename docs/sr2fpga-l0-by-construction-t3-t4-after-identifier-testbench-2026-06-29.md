# SR2FPGA T3/T4 behavior-files rerun after identifier and testbench hardening - 2026-06-29

Run ID: `l0-by-construction-t3-t4-after-identifier-testbench`

Config: `configs/sr2fpga_l0_by_construction_t3_t4_after_identifier_testbench.example.yaml`

Command:

```bash
python -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_t3_t4_after_identifier_testbench.example.yaml --run-id l0-by-construction-t3-t4-after-identifier-testbench
```

## Why this narrow rerun exists

The previous top-wiring rerun moved T4 from L0 to L1, then exposed two
deterministic hardening targets: generated behavior could still use reserved
identifiers such as `buf`, and the deterministic testbench did not declare
top-level parameters such as `DATA_WIDTH`. This rerun checks the fresh T3/T4
slice after those fixes.

## Run summary

- `total_completed`: 2
- `success_l3`: 0
- `repair_trajectory`: 2
- `rejected`: 0
- `pass_level_breakdown`: `L0:2`
- `failure_types`: `reset_behavior_error:1`, `unknown:1`
- `failure_family_breakdown`: `rtl_compile_failure:2`
- `exports_refreshed`: true

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-identifier-testbench/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-identifier-testbench/events.jsonl`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_identifier_testbench_t3_stream_fork_8_000001/attempts/attempt_000/diagnosis.json`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_identifier_testbench_t4_dual_stream_join_8_000002/attempts/attempt_000/diagnosis.json`

## Result

| topology | result | observed blocker |
|---|---|---|
| T3 `stream_fork` | `L0` | duplicate `_unused_clock_reset` and missing top-level `DATA_WIDTH` |
| T4 `dual_stream_join` | `L0` | `[None-1:0]` width emission plus missing top-level width parameters |

This run did not improve the aggregate pass level over the previous slice. It
did, however, identify deterministic skeleton defects rather than natural model
logic defects. Those defects should not be recorded as model behavior quality.

## Follow-up applied after reading this run

- Missing or null width metadata now defaults to scalar width instead of
  emitting invalid ranges such as `[None-1:0]`.
- `rtl/top.v` and `sim/tb_top.v` inherit component parameters used by internal
  wires when the top contract omits them, so `DATA_WIDTH`, `SAMPLE_WIDTH`, or
  `SUM_WIDTH` references are declared before use.
- `merge_behavior_files()` now drops duplicate model-returned
  `_unused_clock_reset` lines when the deterministic skeleton already inserted
  one.

Replay evidence after those fixes:

- T3 replay with the same generated behavior becomes Verilator lint-clean.
- T4 replay no longer has `[None-1:0]` or missing width-parameter errors; the
  remaining failures are model behavior lint warnings such as unused `state`
  registers and unused payload inputs.

## Next verification target

Run another fresh T3/T4 slice after these skeleton fixes. If the deterministic
errors stay gone, the next blocker is behavior-body lint cleanliness, which
should be addressed through HIS2PROJECT prompt constraints or lint-aware retry
rather than more top/skeleton wiring work.
