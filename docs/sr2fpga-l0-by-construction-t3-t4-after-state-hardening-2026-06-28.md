# SR2FPGA T3/T4 behavior-files rerun after state hardening - 2026-06-28

Run ID: `l0-by-construction-t3-t4-after-state-hardening`

Config: `configs/sr2fpga_l0_by_construction_t3_t4_after_state_hardening.example.yaml`

Command:

```bash
python -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_t3_t4_after_state_hardening.example.yaml --run-id l0-by-construction-t3-t4-after-state-hardening
```

## Why this narrow rerun exists

The full after-hardening rerun left the `behavior_files` arm with one T3
`GEN_FAIL` and one T4 `L0` sample. The T3 failure was still in REQ2HIS
state/control-flow validation, while T4 reached RTL lint but failed on duplicate
FSM localparams. After hardening state-name prompt guidance and duplicate
localparam merge behavior, this narrow rerun spends only on the remaining T3/T4
behavior-files path.

## Run summary

- `total_completed`: 2
- `success_l3`: 0
- `repair_trajectory`: 2
- `rejected`: 0
- `pass_level_breakdown`: `L0:2`
- `failure_family_breakdown`: `rtl_compile_failure:2`
- `exports_refreshed`: true

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-state-hardening/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-state-hardening/baseline_report.md`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-state-hardening/events.jsonl`

## Result

| topology | previous after-hardening result | narrow rerun result | remaining blocker |
|---|---|---|---|
| T3 `stream_fork` | `GEN_FAIL` in REQ2HIS | `L0` | generated behavior returned nested module/endmodule text |
| T4 `dual_stream_join` | `L0`, duplicate FSM localparams | `L0` | generated behavior returned nested module/endmodule text |

The important movement is that both T3 and T4 now cross the System-HIS v1.2
contract gate. T3's previous duplicate/invalid state-control failure surface is
gone in this run; T4's duplicate `IDLE`/`WAIT`/`JOINED` localparam failure is
also gone.

## New blocker

Both samples now fail at RTL compile/lint because HIS2PROJECT returned complete
module bodies inside `behavior_files` values. The deterministic skeleton already
wraps each behavior hole in a module, so this creates nested module declarations:

- T3: Verilator reports module declarations within module declarations in
  `rtl/skid_buffer.v`, `rtl/stream_fork.v`, and `rtl/stream_stage.v`.
- T4: Verilator reports the same class in `rtl/skid_buffer.v`,
  `rtl/stream_join.v`, `rtl/accumulator_core.v`, and `rtl/stream_stage.v`.

## Follow-up applied

After reading this run, `merge_behavior_files()` was hardened to reject behavior
text containing module declarations or `endmodule`, and HIS2PROJECT now appends
retry feedback that asks the model to return only behavior-body replacements.
That should move this blocker from RTL lint into the HIS2PROJECT retry loop in
the next narrow rerun.
