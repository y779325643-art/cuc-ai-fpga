# Training-Data-Quality Issues — 2026-06-24

Findings from a review pass over the training-data contract (`recorder.py`,
`log_parser.py`, and actual exported samples). These affect the quality of the
JSONL training views, so they should be fixed before the first clean training
split. Code changes are codex's to make.

## Positive baseline (no action)

The `predicted_qor` / `measured_qor` separation holds in both code and data:
`export_training_views` reads predicted QoR from
`final/.../reports/predicted_qor.json` (model-generated) and measured QoR from
`eval/measured_qor.json` (tool-parsed), and never mixes them
(`recorder.py:132-150`). Verified in a real sample (predicted LUT 8 / FF 8 vs
measured lut 0 / ff 8). Keep this invariant intact.

## High priority

### F. `classify_failure` broad single-word patterns produce noisy labels

`log_parser.py:26-27` classify on super-common single words:

```python
("reset_behavior_error", ["reset"]),
("clocking_error",       ["clock"]),
```

Nearly every Verilog tool log mentions `clk`/`rst`/reset/clock, so these two
first-match-wins patterns swallow most synth-stage failures **before** the more
specific later categories (`synthesis_error`, `resource_overuse`, `timing_risk`)
are ever reached — making those effectively unreachable and mislabeling many
failures. This corrupts `failure_type` in `failure_to_diagnosis.jsonl`, so
LOG2DIAG/FAILURE2PATCH would train on noisy labels.

**Fix direction:** narrow `reset_behavior_error` / `clocking_error` to require an
error-context token (e.g. "reset" *and* an error verb, or a specific message
shape), or drop them; re-order so genuinely specific categories win; add a unit
test that a synth/timing log mentioning "clock" still classifies as
`synthesis_error`/`timing_risk`, not `clocking_error`.

### E. Failure-taxonomy names drift between spec and code

The hardware-semantic taxonomy added to the reframe spec
(`2026-06-22-sr2fpga-research-reframe-design.md`) does not match the names already
emitted by `classify_failure`:

| Spec name | Code name (`log_parser.py`) |
|---|---|
| `multi_driven_net` | `multiple_driver` |
| `latch_inference` | `latch_inferred` |
| `blocking_in_sequential` | (missing) |
| `cdc_missing_sync` | (missing) |
| backpressure / `bram_inference_miss` | (missing) |

**Fix direction:** reconcile before implementing the hardware-semantic taxonomy.
Preferred: the **spec adopts the existing code names** (`multiple_driver`,
`latch_inferred` — already producing data) and **adds the three missing
categories** (`blocking_in_sequential`, `cdc_missing_sync`, plus the L2/L3
classes), to avoid renaming already-emitted labels. Update the spec table to
match, then extend `classify_failure` with the missing classes + tests.

## Medium priority (QoR-prediction prerequisites)

### G. L3 measured LUT is always 0 under the generic Yosys flow

`parse_yosys_stats` (`log_parser.py:71`) maps cell names to `lut` by matching
"LUT", but the default Yosys flow emits generic gates (`$_AND_`, `$_XOR_`,
`$_DFFE_`), not LUTs — LUTs appear only after FPGA techmapping (`synth_xilinx`).
So measured `lut` is currently always 0, and predicted-vs-measured LUT is not a
real comparison (only `cell_count` and `ff` are meaningful). A QOR_PRED task on
this would train against a vacuous LUT signal.

**Fix direction:** for the L3 QoR signal, run Yosys with an FPGA target
(`synth_xilinx`) so LUT/FF/BRAM/DSP are real, or defer the authoritative LUT
number to L4 (OpenXC7/Vivado) and stop treating the generic-flow `lut` as a QoR
label. Decide before QOR_PRED data is collected.

### C. `project_to_measured_qor` is not filtered by pass level

`recorder.py:142` exports a measured-QoR row whenever `measured_qor.json` exists,
regardless of whether the sample reached L3. Samples that failed at L0/L1 have
empty/partial measured QoR (synth never ran), yet still appear in
`project_to_measured_qor.jsonl`, and the row's `metadata` carries
`measurement_point` but **not** `pass_level` — so partial rows cannot be filtered
out. QOR_PRED could train on empty QoR.

**Fix direction:** add `pass_level` to QoR export rows (and ideally to all view
rows), or only export measured-QoR rows for L3-passing samples.

## Low priority

### B. Export silently filters samples without provenance

`export_training_views` (`recorder.py:92-102`) includes a sample in a view only
if the required files exist, silently skipping the rest. There is no manifest of
"N scanned, M included, K excluded and why," which is a data-provenance gap for
reproducibility.

**Fix direction:** emit an `export_manifest.json` alongside the JSONL views
recording per-view counts and excluded sample IDs with reasons.

### (Confirmed pending, not a new bug) `training_split` label

Sample `metadata.json` carries `system_his_schema_version` but no
`training_split` field yet — this is freeze-plan Task 9 (quarantine labeling),
already tracked, not yet implemented.
