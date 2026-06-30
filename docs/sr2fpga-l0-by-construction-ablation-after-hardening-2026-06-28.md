# SR2FPGA L0-by-construction ablation after-hardening rerun - 2026-06-28

Run ID: `l0-by-construction-ablation-after-hardening`

Config: `configs/sr2fpga_l0_by_construction_ablation_after_hardening.example.yaml`

Command:

```bash
python -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_ablation_after_hardening.example.yaml --run-id l0-by-construction-ablation-after-hardening
```

## Why this rerun exists

The previous after-fixes rerun still exposed three lowerability blockers in the
`behavior_files` arm: non-lowerable component sources such as `library`,
unowned FSMs that were later checked against RTL module `top`, and repeated RTL
range construction such as `[7:0-1:0]`. Those were hardened in the v1.2 checker,
REQ2HIS prompts, and contract skeleton width rendering. This rerun uses a fresh
sample prefix, `l0_by_construction_ablation_after_hardening`, so the runner
cannot reuse earlier sample directories.

## Run summary

The run completed all 8 planned samples and refreshed the JSONL exports:

- `total_completed`: 8
- `success_l3`: 0
- `repair_trajectory`: 7
- `rejected`: 1
- `pass_level_breakdown`: `L0_FAIL:4`, `L0:3`, `GEN_FAIL:1`
- `exports_refreshed`: true

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-ablation-after-hardening/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-ablation-after-hardening/baseline_report.md`
- `tmp/sr2fpga_runs/l0-by-construction-ablation-after-hardening/events.jsonl`

## Ablation result

| mode | total | pass levels | L0 contract failures | cross-file error rate | L3 pass rate |
|---|---:|---|---:|---:|---:|
| `legacy_full_project` | 4 | `L0_FAIL:4` | 4 | 100.0% | 0.0% |
| `behavior_files` | 4 | `GEN_FAIL:1`, `L0:3` | 1 | 25.0% | 0.0% |

Observed delta (`behavior_files - legacy_full_project`):

- L0 contract failures: `-3`
- L3 pass rate: `+0.0 pp`

Compared with the after-fixes rerun, the `behavior_files` arm moved from
`GEN_FAIL:3, L0:1` to `GEN_FAIL:1, L0:3`. The useful signal is now much
cleaner: skeleton-based generation is usually crossing L0, while deeper RTL
compile/simulation behavior remains the next bottleneck.

## Failure pattern

Legacy direct full-project generation:

- T1-T4 remained `L0_FAIL`, matching the previous direct-generation arm.

`behavior_files` skeleton generation:

- T1 `event_counter`: crossed L0 and was recorded as a repair trajectory.
- T2 `stream_accumulator`: crossed L0; this is the main improvement over the
  after-fixes rerun, where T2 stopped at `GEN_FAIL`.
- T3 `stream_fork`: remained `GEN_FAIL` during REQ2HIS. The retry sequence
  exposed state ownership, undeclared in-ready control targets, duplicated
  state names, and a final positive-`target_fmax_mhz` validation failure.
- T4 `dual_stream_join`: crossed L0; this is the second major improvement over
  the after-fixes rerun. It then failed at RTL lint/compile because
  `rtl/stream_join.v` declared duplicate localparams `IDLE`, `WAIT`, and
  `JOINED`.

## Next fix targets

1. Tighten REQ2HIS guidance for T3-style streaming fork topologies so owned
   state names are unique per instance/FSM and generated control-flow targets
   reference declared ports or state fields.
2. Prevent contract skeleton FSM localparams from colliding with generated RTL
   localparams when behavior files already declare the same state names.
3. Keep the next rerun small: T3/T4 behavior-files only is enough to validate
   the remaining blocker before spending another full paired ablation run.
