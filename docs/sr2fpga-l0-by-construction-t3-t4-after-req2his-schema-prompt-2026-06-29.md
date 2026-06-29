# SR2FPGA T3/T4 behavior-files rerun after REQ2HIS schema prompt hardening - 2026-06-29

Run ID: `l0-by-construction-t3-t4-after-req2his-schema-prompt`

Config: `configs/sr2fpga_l0_by_construction_t3_t4_after_req2his_schema_prompt.example.yaml`

Command:

```bash
python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_l0_by_construction_t3_t4_after_req2his_schema_prompt.example.yaml --run-id l0-by-construction-t3-t4-after-req2his-schema-prompt
```

## Why this narrow rerun exists

The previous width-parameter rerun reached `L3:2`, but both samples needed a
REQ2HIS retry for schema details: non-positive `target_fmax_mhz` and non-list
`owns_state`. This pass makes the initial REQ2HIS prompt and retry checklist
explicit about positive clock targets and list-valued `owns_state`, then runs a
fresh T3/T4 slice to see what remains.

## Run summary

- `total_completed`: 2
- `pass_level_breakdown`: `L3:1, GEN_FAIL:1`
- `failure_types`: `generation_failed:1`
- `failure_family_breakdown`: `generation_failure:1`
- `exports_refreshed`: true

Primary evidence:

- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-req2his-schema-prompt/summary.json`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-req2his-schema-prompt/events.jsonl`
- `tmp/sr2fpga_runs/l0-by-construction-t3-t4-after-req2his-schema-prompt/baseline_report.md`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_req2his_schema_prompt_t3_stream_fork_8_000001`
- `datasets/sr2fpga_rtl_v1/sample_l0_by_construction_t3_t4_after_req2his_schema_prompt_t4_dual_stream_join_8_000002`

## Result

| topology | result | observed blocker |
|---|---|---|
| T3 `stream_fork` | `L3` | First REQ2HIS attempt retried on `control_flow 'global_reset'.effect must be an object`, then completed through L3. |
| T4 `dual_stream_join` | `GEN_FAIL` | HIS2PROJECT cross-check rejected equivalent arithmetic width spelling: System-HIS `2*DATA_WIDTH` versus RTL `[2*DATA_WIDTH-1:0]`. |

The specific `target_fmax_mhz` and list-valued `owns_state` errors from the
previous run did not reappear in either fresh sample. The remaining REQ2HIS
retry surface moved to structured `control_flow` and FSM reset-state details.

## Follow-up applied after reading this run

- REQ2HIS prompt and retry checklist now explicitly state:
  - `top.clocks[].target_fmax_mhz` and `timing.target_fmax_mhz` must be positive
    numbers;
  - `instances[].owns_state` must be a JSON array, using `[]` when no state is
    owned.
- `rtl_introspect.normalize_width()` now treats arithmetic RTL ranges such as
  `[2*DATA_WIDTH-1:0]` as the width expression `2*DATA_WIDTH`, so
  `widths_equivalent({"expr": "2*DATA_WIDTH", "resolved": 16},
  "[2*DATA_WIDTH-1:0]")` succeeds.

## Next verification target

Run another fresh T3/T4 slice after the arithmetic width-equivalence fix. If T4
crosses this GEN_FAIL, the next prompt hardening target is structured
`control_flow` shape: `effect` must be an object whose `target` names declared
state or data-flow entries, and FSM `reset_state` must be non-empty and drawn
from the FSM's `states`.
