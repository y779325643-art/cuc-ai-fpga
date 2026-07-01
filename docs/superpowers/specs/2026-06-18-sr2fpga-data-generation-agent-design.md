# SR2FPGA Data Generation Agent V1 Design

## Status

Delivered (2026-06-18). V1 architecture is implemented and stable.

**Post-delivery notes (do not rewrite — see current-status.md for live state):**
- Task families have expanded beyond the original V1 set to include 6 additional
  single-module families (`uart_tx`, `spi_master`, `pwm_controller`, `fir_filter`,
  `streaming_valid_ready`, `matrix_vector_mac`) and 4 composed topology families
  (`composed_event_counter`, `composed_stream_accumulator`, `composed_stream_fork`,
  `composed_dual_stream_join`). See `2026-06-22-sr2fpga-multimodule-task-families-design.md`.
- Training task names are now standardized in the reframe spec as: `REQ2HIS`,
  `HIS2PROJECT` (not `HIS2FILES`), `LOG2DIAG`, `FAILURE2PATCH`, `ARCH_MUTATE`
  (actor) and `PROJECT2RISK`, `PROJECT2LEVEL`, `PROJECT2QOR` (critic).
- System-HIS schema is now canonical `system-his-v1.2` (frozen). See
  `2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`.

## Decision

This document records the V1 design for the SR2FPGA data generation agent.

The agent is a tool-calling verified dataset generator. It is not the final no-tool inference model. Its job is to produce high-quality FPGA RTL project samples, preserve failures, repair projects with tool feedback, and record measured evaluation labels for later model training.

Core objective:

> Build a lightweight, command-line-friendly data factory that generates Verilog RTL project packages, runs open-source EDA checks, repairs failures, and records final projects, tool logs, QoR labels, and repair trajectories.

## Relationship To The Final Model

The project has two separate roles:

- Data generation agent: may call tools, read logs, debug code, rerun checks, and record attempts.
- Final generation model: should generate project packages without online EDA tool calls.

The data generation agent creates training data for the final model. Tool calls are allowed only in the dataset construction process, not in the final no-tool generation boundary.

The intended learning loop is:

```text
tool-calling data factory
-> verified project dataset
-> repair and QoR supervision
-> no-tool generation model
```

## V1 Scope

V1 focuses on open-source, lightweight, deployable tooling.

Included:

- Generate natural-language requirements.
- Generate `system_his.json`.
- Generate `manifest.json`.
- Generate pure Verilog RTL.
- Generate timing and physical constraints when the platform profile supports them.
- Generate Verilog testbench.
- Generate `reports/predicted_qor.json` before running synthesis.
- Run lint, simulation, and synthesis.
- Repair failed projects using tool logs.
- Save every failed attempt, diagnosis, patch, and next result.
- Parse measured resource usage from synthesis results.
- Export training JSONL views.

Excluded from V1:

- Vivado or Quartus as required dependencies.
- HLS generation.
- Vendor IP generation.
- Bitstream as a required output.
- Board-level testing.
- Mandatory power analysis.
- Mandatory full place-and-route.

## V1 Toolchain

The first implementation should use tools that are easy to install, run from scripts, and automate in batch mode.

Required tools:

- Verilator for lint and strict static checks.
- Icarus Verilog for lightweight Verilog simulation.
- Yosys for synthesis and resource statistics.

Optional tools:

- nextpnr for lightweight place-and-route on supported Lattice targets.
- OpenSTA for timing analysis when a suitable netlist, liberty file, and constraints are available.

Recommended first platform profiles:

- `generic_verilog`
- `lattice_ice40`
- `lattice_ecp5`

Commercial toolchains can be added later as separate evaluation backends.

## Agent Components

### Task Generator

Creates or selects requirements for simple RTL design tasks.

V1 task families:

- Counter
- Adder and subtractor
- Multiplexer and demultiplexer
- Shift register
- FIFO
- Simple FSM
- Small UART RX or TX
- ALU
- RAM read/write block
- Valid-ready pipeline

The task generator should vary width, depth, reset polarity, clocking assumptions, expected latency, and corner cases.

### Project Generator

Generates the project package from the requirement and platform profile.

Required generated files:

```text
generated_project/
  system_his.json
  manifest.json
  rtl/top.v
  constraints/timing.sdc
  sim/tb_top.v
  reports/predicted_qor.json
```

If a board-specific platform profile exists, the generator may also produce a physical constraint file:

```text
constraints/physical.pcf
```

For larger tasks, the project may include additional RTL modules under:

```text
rtl/modules/*.v
```

### Tool Runner

Runs checks in a fixed order:

```text
L0 completeness and consistency checks
-> Verilator lint
-> Icarus Verilog simulation
-> Yosys synthesis and resource statistics
-> optional nextpnr or OpenSTA timing/P&R
```

Example commands:

```bash
verilator --lint-only -Wall rtl/*.v rtl/modules/*.v
iverilog -g2012 -o sim.out rtl/*.v rtl/modules/*.v sim/tb_top.v
vvp sim.out
yosys -p "read_verilog rtl/*.v rtl/modules/*.v; synth -top top; stat"
```

The final implementation should build these commands from `manifest.json` rather than relying on hard-coded file globs.

### Log Parser

Converts raw logs into structured records.

It should extract:

- Stage name.
- Tool name.
- Command.
- Exit code.
- Error summary.
- Warning summary.
- Failure type.
- Relevant file and line references when available.
- Resource statistics from Yosys.
- Optional timing estimates from nextpnr or OpenSTA.

### Repair Agent

When a stage fails, the repair agent receives:

- Requirement.
- Platform profile.
- `system_his.json`.
- `manifest.json`.
- Relevant project files.
- Tool command.
- Tool log.
- Parsed failure summary.

It outputs:

- `diagnosis.json`
- `patch.diff`
- A repaired project for the next attempt.

The patch should be minimal where possible. The agent should not rewrite the entire project when a local fix is enough.

### Dataset Recorder

Persists the full sample, including every attempt and final labels.

It should record:

- Original requirement.
- Platform profile.
- All attempts.
- All logs.
- Diagnoses.
- Patches.
- Final verified project.
- Measured QoR labels.
- Tool versions.
- Trajectory metadata.

## Dataset Directory Structure

Each sample should be stored as:

```text
datasets/sr2fpga_rtl_v1/sample_000001/
  requirement.txt
  platform_profile.json

  attempts/
    attempt_000/
      generated_project/
        system_his.json
        manifest.json
        rtl/
        constraints/
        sim/
        reports/predicted_qor.json
      eval/
        lint.log
        sim.log
        synth.log
      diagnosis.json
      patch.diff

    attempt_001/
      generated_project/
      eval/
      diagnosis.json
      patch.diff

  final/
    generated_project/
      system_his.json
      manifest.json
      rtl/
      constraints/
      sim/
      reports/predicted_qor.json

  eval/
    labels.json
    measured_qor.json
    tool_versions.json
    trajectory.json
```

The final project should be copied from the last successful attempt. Failed attempts must remain available for repair training.

## Repair Trajectory Format

The trajectory must preserve the causal chain:

```text
failed project
-> tool command and log
-> structured diagnosis
-> patch.diff
-> repaired project
-> next tool result
```

Example attempt entry:

```json
{
  "attempt_id": 0,
  "stage": "simulation",
  "status": "failed",
  "tool": "iverilog",
  "exit_code": 1,
  "failure_type": "port_mismatch",
  "log_path": "attempts/attempt_000/eval/sim.log",
  "diagnosis_path": "attempts/attempt_000/diagnosis.json",
  "patch_path": "attempts/attempt_000/patch.diff",
  "next_attempt_id": 1
}
```

`patch.diff` is required for failed attempts that are repaired. It is more useful for repair training than storing only the repaired full files.

## Failure Type Taxonomy

V1 should use a fixed failure taxonomy:

- `syntax_error`
- `module_not_found`
- `port_mismatch`
- `width_mismatch`
- `multiple_driver`
- `latch_inferred`
- `non_synthesizable_construct`
- `testbench_timeout`
- `functional_mismatch`
- `reset_behavior_error`
- `clocking_error`
- `constraint_port_missing`
- `synthesis_error`
- `resource_overuse`
- `timing_risk`
- `unknown`

The taxonomy should be stored in `diagnosis.json` and summarized in `trajectory.json`.

## Measured QoR Labels

`predicted_qor.json` is generated before tool execution. Measured labels are saved separately after synthesis or timing evaluation.

`eval/measured_qor.json` may include:

- LUT or logic cell count.
- FF count.
- Memory cell count or inferred memory summary.
- DSP or multiplier-related cell count when available.
- Yosys cell breakdown.
- Estimated maximum frequency when timing tools are available.
- Timing pass/fail when timing tools are available.
- Optional power estimate when supported by a later backend.

The dataset must clearly separate:

- Predicted QoR: generated by the model before tool execution.
- Measured QoR: parsed from external tool outputs.

## Labels

`eval/labels.json` should record the highest passed level:

- L0: files are complete and internally consistent.
- L1: lint passes.
- L2: simulation passes.
- L3: synthesis passes and resource statistics are parsed.
- L4-lite: optional timing or P&R passes.
- L5: out of scope for V1.

Example:

```json
{
  "pass_level": "L3",
  "checks": {
    "l0_complete": true,
    "l1_lint_pass": true,
    "l2_sim_pass": true,
    "l3_synth_pass": true,
    "l4_lite_timing_pass": false
  },
  "final_attempt_id": 2,
  "failure_count": 2,
  "toolchain": ["verilator", "iverilog", "yosys"]
}
```

## Training Exports

The recorder should export multiple JSONL views from the same dataset:

- `requirement_to_his.jsonl`
- `his_to_project.jsonl`
- `requirement_to_project.jsonl`
- `requirement_to_file.jsonl`
- `failure_to_diagnosis.jsonl`
- `failure_to_patch.jsonl`
- `project_to_predicted_qor.jsonl`
- `project_to_measured_qor.jsonl`

These views support staged training instead of forcing the model to learn one large end-to-end task immediately.

## V1 Success Criteria

V1 is successful when it can:

- Generate at least one complete sample from a requirement.
- Run L0-L3 checks through command-line tools.
- Repair at least one intentionally or naturally failed attempt.
- Save `trajectory.json`, `diagnosis.json`, and `patch.diff`.
- Parse Yosys resource statistics into `measured_qor.json`.
- Export at least one JSONL training view.

The first milestone should prioritize correctness and traceability over dataset size.

## Risks And Mitigations

Risk: the agent rewrites entire projects instead of producing small repairs.

Mitigation: require `patch.diff`, cap changed files per repair where practical, and record repair scope.

Risk: logs are too noisy for training.

Mitigation: store raw logs and structured summaries. Train on summaries first, with raw logs available for richer models.

Risk: predicted QoR leaks measured tool results.

Mitigation: generate and timestamp `predicted_qor.json` before running synthesis. Store measured labels only under `eval/`.

Risk: physical constraints are impossible without a board profile.

Mitigation: make physical constraints optional for `generic_verilog` and required only for platform profiles that define pins.

Risk: power estimates are not reliable in the open-source V1 flow.

Mitigation: treat power as optional in V1 and add vendor-tool power evaluation later.
