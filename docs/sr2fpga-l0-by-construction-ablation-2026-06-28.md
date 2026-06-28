# SR2FPGA L0-by-construction ablation run - 2026-06-28

Run ID: `l0-by-construction-ablation`

Config: `configs/sr2fpga_l0_by_construction_ablation.example.yaml`

Command:

```bash
python -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_ablation.example.yaml --run-id l0-by-construction-ablation
```

## Run summary

The run completed all 8 planned samples:

- `total_completed`: 8
- `success_l3`: 0
- `repair_trajectory`: 5
- `rejected`: 3
- `pass_level_breakdown`: `L0_FAIL:4`, `GEN_FAIL:3`, `L0:1`

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-ablation/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-ablation/baseline_report.md`
- `tmp/sr2fpga_runs/l0-by-construction-ablation/events.jsonl`

## Ablation result

| mode | total | pass levels | L0 contract failures | cross-file error rate | L3 pass rate |
|---|---:|---|---:|---:|---:|
| `legacy_full_project` | 4 | `L0_FAIL:4` | 4 | 100.0% | 0.0% |
| `behavior_files` | 4 | `GEN_FAIL:3`, `L0:1` | 3 | 75.0% | 0.0% |

Observed delta (`behavior_files - legacy_full_project`):

- L0 contract failures: `-1`
- L3 pass rate: `+0.0 pp`

Interpretation: Tier A contract-preserving skeleton generation reduced structural
L0 failures in this small paired run and produced one sample that crossed L0
(`t3_stream_fork`), but it did not yet reach L1/L2/L3 reliability. The dominant
remaining blockers are in REQ2HIS validity and HIS2PROJECT lowerability, not in
runner wiring.

## Failure pattern

Legacy direct full-project generation:

- T1-T4 all failed at L0 with incomplete/non-canonical `system_his.json` and
  manifest structures.

`behavior_files` skeleton generation:

- T1 `event_counter`: `GEN_FAIL`; HIS2PROJECT failed v1.2 cross-check due to
  single-bit width expression mismatches such as `1` versus `[1-1:0]`.
- T2 `stream_accumulator`: `GEN_FAIL`; REQ2HIS repeatedly failed reset
  `kind`/`polarity` validation.
- T3 `stream_fork`: crossed L0 and failed lint; generated RTL omitted module
  `DATA_WIDTH` parameter declarations while top tried to override them.
- T4 `dual_stream_join`: `GEN_FAIL`; HIS2PROJECT failed v1.2 cross-check because
  FSM states declared in System-HIS were not found in RTL.

## Next fix targets

1. Fixed after this run: RTL width normalization now treats concrete
   minus-one ranges like `[1-1:0]` and `[8-1:0]` as integer widths for future
   HIS↔RTL cross-checks. This does not change the recorded run result; rerun the
   ablation to measure the effect.
2. Fixed after this run: REQ2HIS initial and retry prompts now spell out reset
   enum values and the current `rst_n` active-low sync contract. This targets
   the T2 reset `kind`/`polarity` failure; rerun the ablation to measure the
   effect.
3. Fixed after this run: System-HIS v1.2 now rejects instance parameter
   overrides unless the target component declares that parameter, and REQ2HIS
   prompt/retry guidance explains the rule. This targets the T3 missing
   `DATA_WIDTH` component-parameter failure; rerun the ablation to measure the
   effect.
4. Fixed after this run: contract skeleton generation now infers FSM owners from
   instance-prefixed names such as `join_core.arb_fsm`, preserving those state
   localparams in the target component module; HIS2PROJECT prompt guidance also
   tells the model to keep declared `state.fsms` names visible in RTL. This
   targets the T4 FSM-state lowerability failure; rerun the ablation to measure
   the effect.
