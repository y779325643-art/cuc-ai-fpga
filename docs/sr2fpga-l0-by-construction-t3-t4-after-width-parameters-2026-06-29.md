# SR2FPGA T3/T4 behavior-files rerun after width-parameter hardening - 2026-06-29

Run ID: `l0-by-construction-t3-t4-after-width-parameters`

Config: `configs/sr2fpga_l0_by_construction_t3_t4_after_width_parameters.example.yaml`

Command:

```bash
python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_t3_t4_after_width_parameters.example.yaml --run-id l0-by-construction-t3-t4-after-width-parameters
```

## Why this narrow rerun exists

The previous T3/T4 behavior-files run exposed deterministic skeleton defects:
duplicated `_unused_clock_reset`, missing inherited width parameters such as
`DATA_WIDTH`, and invalid ranges such as `[None-1:0]`. This rerun uses a fresh
sample prefix after those hardening fixes to check whether the same T3/T4 slice
can now clear lint, simulation, and synthesis.

## Run summary

- `total_completed`: 2
- `pass_level_breakdown`: `L3:2`
- `failure_types`: `{}`
- `failure_family_breakdown`: `{}`
- `exports_refreshed`: true

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-width-parameters/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-width-parameters/events.jsonl`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-width-parameters/baseline_report.md`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_width_parameters_t3_stream_fork_8_000001/final/generated_project`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_width_parameters_t4_dual_stream_join_8_000002/final/generated_project`

## Result

| topology | result | note |
|---|---|---|
| T3 `stream_fork` | `L3` | Cleared the full L0-L3 tool path after one REQ2HIS retry. |
| T4 `dual_stream_join` | `L3` | Cleared the full L0-L3 tool path after one REQ2HIS retry. |

The baseline report records:

```text
contract_skeleton_mode | behavior_files | 2 | L3:2 | 100.0% | 0 | 0.0%
```

## Regression checks

The known deterministic skeleton signatures from the previous run did not
reappear:

- no `[None-1:0]` widths in final RTL;
- no missing Verilator parameter errors such as `DATA_WIDTH`, `SAMPLE_WIDTH`,
  or `SUM_WIDTH`;
- no duplicate `_unused_clock_reset` declarations. Each generated component RTL
  file has at most one `_unused_clock_reset` reduction wire, and `top.v` has
  none.

## Remaining observation

Both samples still needed one REQ2HIS retry before project generation:

- T3 first attempt: `system_his.top.clocks[0].target_fmax_mhz must be positive`.
- T4 first attempt: the same non-positive clock target plus several
  `instance '<name>'.owns_state must be a list` schema violations.

These did not prevent L3 completion because the existing retry path corrected
the System-HIS. The next small hardening target is to make the initial REQ2HIS
prompt/schema feedback more explicit about positive `target_fmax_mhz` and
list-valued `owns_state`, reducing retry dependence without changing the
deterministic skeleton path.
