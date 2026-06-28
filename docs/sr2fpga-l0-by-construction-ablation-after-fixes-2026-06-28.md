# SR2FPGA L0-by-construction ablation after-fixes rerun - 2026-06-28

Run ID: `l0-by-construction-ablation-after-fixes`

Config: `configs/sr2fpga_l0_by_construction_ablation_after_fixes.example.yaml`

Command:

```bash
python -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_ablation_after_fixes.example.yaml --run-id l0-by-construction-ablation-after-fixes
```

## Why this rerun exists

The first `l0-by-construction-ablation` run exposed four concrete blockers in
the `behavior_files` arm: concrete minus-one RTL widths, reset enum fidelity,
undeclared component parameters, and FSM state lowerability. Those fixes were
implemented after the first run. This rerun uses a new sample prefix,
`l0_by_construction_ablation_after_fixes`, so the runner cannot reuse the old
sample directories.

## Run summary

The run completed all 8 planned samples and refreshed the JSONL exports:

- `total_completed`: 8
- `success_l3`: 0
- `repair_trajectory`: 5
- `rejected`: 3
- `pass_level_breakdown`: `L0_FAIL:4`, `L0:1`, `GEN_FAIL:3`
- `exports_refreshed`: true

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-ablation-after-fixes/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-ablation-after-fixes/baseline_report.md`
- `tmp/sr2fpga_runs/l0-by-construction-ablation-after-fixes/events.jsonl`

## Ablation result

| mode | total | pass levels | L0 contract failures | cross-file error rate | L3 pass rate |
|---|---:|---|---:|---:|---:|
| `legacy_full_project` | 4 | `L0_FAIL:4` | 4 | 100.0% | 0.0% |
| `behavior_files` | 4 | `GEN_FAIL:3`, `L0:1` | 3 | 75.0% | 0.0% |

Observed delta (`behavior_files - legacy_full_project`):

- L0 contract failures: `-1`
- L3 pass rate: `+0.0 pp`

The aggregate result is unchanged from the first run, but the single
`behavior_files` sample that crosses L0 moved from T3 to T1. This is a useful
diagnostic signal: the implemented fixes changed the failure surface, but T2-T4
still expose lowerability and RTL range-generation failures before L3.

## Failure pattern

Legacy direct full-project generation:

- T1-T4 remained `L0_FAIL`, matching the first run's direct-generation arm.

`behavior_files` skeleton generation:

- T1 `event_counter`: crossed L0 and was recorded as a repair trajectory. This
  confirms the previous concrete minus-one width mismatch no longer blocks this
  sample at the v1.2 HIS↔RTL cross-check.
- T2 `stream_accumulator`: `GEN_FAIL`; HIS2PROJECT cross-check rejected
  component sources such as `source: "library"` because they were not present in
  `artifacts.rtl_sources`. The same sample also exposed FSM states being checked
  against RTL module `top`.
- T3 `stream_fork`: `GEN_FAIL`; FSM states such as `skid_buffer_fsm.EMPTY` and
  `out0_stage_fsm.IDLE` were still searched in RTL module `top`, which means the
  generated HIS/RTL pair did not preserve an explicit FSM owner.
- T4 `dual_stream_join`: `GEN_FAIL`; generated RTL produced repeated range
  expressions such as `[7:0-1:0]` and `[DATA_WIDTH-1:0-1:0]`, which fail the
  v1.2 width cross-check.

## Next fix targets

1. Normalize or prevent repeated RTL range construction where a complete range
   expression is treated as a scalar width and receives an extra `-1:0` suffix.
   The T4 errors show this as `[7:0-1:0]` and `[DATA_WIDTH-1:0-1:0]`.
2. Tighten REQ2HIS/HIS2PROJECT guidance so component `source` values must name
   files listed in `artifacts.rtl_sources`; placeholder sources such as
   `library` are not lowerable.
3. Require generated FSMs to carry an explicit owner, or use
   `<instance>.<fsm>` naming, so checker and skeleton generation do not map
   component FSM states back to `top`.
