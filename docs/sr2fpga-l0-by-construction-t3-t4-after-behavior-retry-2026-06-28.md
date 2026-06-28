# SR2FPGA T3/T4 behavior-files rerun after behavior-body retry - 2026-06-28

Run ID: `l0-by-construction-t3-t4-after-behavior-retry`

Config: `configs/sr2fpga_l0_by_construction_t3_t4_after_behavior_retry.example.yaml`

Command:

```bash
python -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_t3_t4_after_behavior_retry.example.yaml --run-id l0-by-construction-t3-t4-after-behavior-retry
```

## Why this narrow rerun exists

The previous T3/T4 state-hardening rerun showed that both samples crossed the
System-HIS v1.2 contract gate, but failed RTL lint because the model returned
complete `module ... endmodule` text inside `behavior_files`. The deterministic
skeleton already provides module wrappers, so those responses became nested
module declarations. After hardening `merge_behavior_files()` to reject module
declarations and adding HIS2PROJECT retry feedback, this rerun checks whether
that blocker disappears.

## Run summary

- `total_completed`: 2
- `success_l3`: 0
- `repair_trajectory`: 2
- `rejected`: 0
- `pass_level_breakdown`: `L0:2`
- `failure_type`: `lint_warning_as_error:2`
- `failure_family_breakdown`: `rtl_compile_failure:2`
- `exports_refreshed`: true

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-behavior-retry/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-behavior-retry/events.jsonl`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_behavior_retry_t3_stream_fork_8_000001/attempts/attempt_000/diagnosis.json`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_behavior_retry_t4_dual_stream_join_8_000002/attempts/attempt_000/diagnosis.json`

## Result

| topology | previous blocker | rerun result | remaining blocker |
|---|---|---|---|
| T3 `stream_fork` | nested module declarations in behavior bodies | `L0` | `top.v` ports and internal wires are mostly undriven/unused |
| T4 `dual_stream_join` | nested module declarations in behavior bodies | `L0` | `top.v` ports and internal wires are mostly undriven/unused |

The nested-module failure signature is gone. Both samples still stop at L0
because Verilator treats many `UNUSEDSIGNAL` and `UNDRIVEN` warnings as fatal.
The remaining issue is now the deterministic top/skeleton integration path:
generated component instances and top-level ports are present, but the
connection assignments are not being materialized into driven nets.

## Follow-up target

The next highest-leverage step is to harden the skeleton top-level wiring
emitter against System-HIS `data_flow` connections. The expected verifier target
is to move T3/T4 from warning-as-error L0 failures to lint-clean L1/L2 failures,
then let the repair trajectory focus on functional simulation rather than
structural connectivity.
