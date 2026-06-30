# OpenXC7 Handoff: llm17 T6 TD Update Core

This handoff contains the latest SR2FPGA sample that reached local L3 on macOS.
The next validation boundary is L4 implementation/timing on Windows with
OpenXC7 or Vivado.

## Sample

- Sample id: `sample_official_eval_gap_closure_llm17_t6_td_update_core_8_000001`
- Task: `composed_td_update_core`
- Topology: `t6_td_update_core`
- Source: `deepseek-oracle-his-v12`
- Contract mode: `behavior_files`
- Local pass level: `L3`

## Local Evidence

Evidence files are under `evidence/`.

- `summary.json`: run-level bucket summary, with this sample in `success_l3`
- `trajectory.json`: per-stage tool trajectory
- `labels.json`: final labels; `l1_lint_pass`, `l2_sim_pass`, and `l3_synth_pass` are true
- `measured_qor.json`: Yosys resource statistics
- `lint.log`: Verilator `-Wall` lint log
- `sim_run.log`: Icarus/VVP simulation output
- `synth.log`: Yosys synthesis log

## Project Input

Use `generated_project/` as the OpenXC7/Vivado input package.

Important files:

- `generated_project/manifest.json`
- `generated_project/system_his.json`
- `generated_project/rtl/top.v`
- `generated_project/rtl/td_input_stage.v`
- `generated_project/rtl/discount_core.v`
- `generated_project/rtl/td_update_core.v`
- `generated_project/rtl/stream_stage.v`
- `generated_project/constraints/timing.sdc`
- `generated_project/sim/tb_top.v`

## Windows L4 Work

Run implementation/timing on the Windows machine.

Recommended checks:

- OpenXC7 or Vivado synthesis/implementation for the target XC7 device.
- Timing report at the clock period in `constraints/timing.sdc`.
- Utilization report for LUT/FF/BRAM/DSP.
- DRC/check_timing report.

Record results back as structured L4 evidence:

- `l4_open_tool`: `openxc7_nextpnr` or equivalent
- `l4_open_pass`: true/false
- `wns_ns`, `tns_ns`, `fmax_mhz`
- utilization fields for LUT/FF/BRAM/DSP
- raw timing/utilization log paths
