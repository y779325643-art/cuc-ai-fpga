# OpenXC7 Handoff: llm17 T6 TD Update Core with Functional Testbench

This handoff supersedes the earlier `openxc7-handoff-llm17-t6-20260630`
package. The project here uses a task-specific independent functional
testbench, not a skeleton testbench that unconditionally prints `TEST_PASS`.

## Sample

- Source sample: `sample_official_eval_gap_closure_llm17_t6_td_update_core_8_000001`
- Task: `composed_td_update_core`
- Topology: `t6_td_update_core`
- Source mode: `deepseek-oracle-his-v12`
- Local recheck pass level: `L3`

## Functional Testbench Policy

- `generated_project/sim/tb_top.v` drives TD-update input transactions.
- It checks `td_error` and `updated_value` against expected values.
- It emits `TEST_FAIL` on timeout or mismatch.
- `TEST_PASS` is emitted only after the functional checks complete.

## Local Evidence

Evidence files are under `evidence/`.

- `verification_summary.json`: local recheck summary
- `lint.json` / `lint.log`: Verilator `-Wall`
- `sim_compile.json` / `sim_compile.log`: Icarus compile
- `sim_run.json` / `sim_run.log`: simulation; expected output includes `TEST_PASS`
- `synth.json` / `synth.log`: Yosys synthesis and resource stats

## Windows L4 Work

Use `generated_project/` as the OpenXC7/Vivado input package.

Recommended Windows checks:

- OpenXC7 or Vivado synthesis/implementation for the target XC7 device.
- Timing report at the clock period in `constraints/timing.sdc`.
- Utilization report for LUT/FF/BRAM/DSP.
- DRC/check_timing report.

Record L4 fields:

- `l4_open_tool`
- `l4_open_pass`
- `wns_ns`, `tns_ns`, `fmax_mhz`
- utilization fields for LUT/FF/BRAM/DSP
- raw timing/utilization log paths
