# SR2FPGA T3/T4 behavior-files rerun after top wiring - 2026-06-28

Run ID: `l0-by-construction-t3-t4-after-top-wiring`

Config: `configs/sr2fpga_l0_by_construction_t3_t4_after_top_wiring.example.yaml`

Command:

```bash
python -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_t3_t4_after_top_wiring.example.yaml --run-id l0-by-construction-t3-t4-after-top-wiring
```

## Why this narrow rerun exists

The previous behavior-retry rerun removed nested module declarations but left
both T3/T4 samples at `L0` because `rtl/top.v` ports and internal wires were
mostly undriven or unused. This rerun tests deterministic skeleton changes that
materialize System-HIS `data_flow` paths into top-level Verilog assignments,
including valid/ready companion wiring where the matching ports exist.

## Run summary

- `total_completed`: 2
- `success_l3`: 0
- `repair_trajectory`: 2
- `rejected`: 0
- `pass_level_breakdown`: `L0:1`, `L1:1`
- `failure_types`: `rtl_reserved_identifier:1`, `port_mismatch:1`
- `failure_family_breakdown`: `rtl_compile_failure:2`
- `exports_refreshed`: true

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-top-wiring/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-top-wiring/baseline_report.md`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-top-wiring/events.jsonl`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_top_wiring_t3_stream_fork_8_000001/attempts/attempt_000/diagnosis.json`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_top_wiring_t4_dual_stream_join_8_000002/attempts/attempt_000/diagnosis.json`

## Result

| topology | previous behavior-retry result | top-wiring result | remaining blocker |
|---|---|---|---|
| T3 `stream_fork` | `L0`, `lint_warning_as_error` from undriven/unused top wiring | `L0`, `rtl_reserved_identifier` | behavior body declares reserved identifier `buf` |
| T4 `dual_stream_join` | `L0`, `lint_warning_as_error` from undriven/unused top wiring | `L1`, `port_mismatch` in sim compile | deterministic testbench omitted `DATA_WIDTH` localparam |

The important movement is that the T4 sample crossed Verilator lint and reached
the simulation compile gate. `contract_skeleton_mode=behavior_files` now shows
`L0:1, L1:1` for this T3/T4 slice, with zero L0 contract failures and zero
cross-file consistency errors.

## Follow-up applied after reading this run

- `sim/tb_top.v` generation now declares top parameters as testbench
  `localparam`s before using parameterized port ranges such as
  `[DATA_WIDTH-1:0]`. Replaying the generated T4 RTL with the fixed testbench
  compiles and prints `TEST_PASS`.
- HIS2PROJECT generation now runs the RTL reserved-identifier checker after
  merging `behavior_files` into the skeleton. A reserved keyword such as `buf`
  in a generated behavior body becomes retry feedback instead of being recorded
  only later as an L0 trajectory.

## Next verification target

Run one more fresh T3/T4 behavior-files slice after the testbench localparam and
reserved-identifier retry fixes. The expected target is to move T4 beyond L1 and
to make T3 retry away from reserved identifiers before recording the attempt.
