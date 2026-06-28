# SR2FPGA Autonomous Trajectory Runner Design

## Status

Delivered and implemented (2026-06-23; runner merged to main). Two post-delivery
corrections applied: (1) System-HIS schema references updated from `v1.1` to
`v1.2` following the freeze ratified in
`docs/superpowers/specs/2026-06-24-sr2fpga-system-his-v1.2-freeze-design.md`;
(2) training-view name `HIS2FILES` corrected to `HIS2PROJECT` to match the
canonical name established in the reframe spec. Design decisions and component
lists are historical — see `docs/current-status.md` for the current runner state.

This document synchronizes the next engineering step with:

- `docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`
- `docs/superpowers/decisions/2026-06-22-sr2fpga-reframe-decision-log.md`

The goal is to turn the existing SR2FPGA data-generation agent from a
Codex-driven one-sample CLI into an autonomous, reproducible trajectory
production system aligned with the TCAD/TRETS research framing.

## Core Decision

Build a **Compositional Multi-Module Component Library plus Autonomous
Trajectory Runner**.

The runner must not be framed as a DeepSeek batch script. DeepSeek is one
candidate generator and one frontier-model baseline. The research objective is
to **distill the EDA tool oracle, not the LLM**. Therefore the runner must
support multiple input sources and preserve all tool-generated labels:

```text
requirement / System-HIS / candidate project
-> Verilator / Icarus / Yosys / later OpenXC7 or Vivado
-> labels, diagnosis, patches, measured QoR
-> trainable trajectory dataset
```

## Research Alignment

This design follows the reframe decisions:

- Paper 1 needs a project-level benchmark and trajectory dataset, not a
  prompt-engineering demo.
- The generated artifact is a variable-topology, multi-module RTL project,
  not a fixed single-file Verilog snippet.
- System-HIS is both an intermediate supervision target and the contract used
  by L0 consistency checking.
- Frontier models are the first-attempt, no-tool baseline, not the final
  competitor.
- Data must be multi-source so the project does not become simple DeepSeek
  distillation.
- Large-scale trajectory production should run through L0-L3; L4/L5 are
  reserved for benchmark/evaluation subsets and later OpenXC7/Vivado work.

## Two Production Lines

### Line A: Benchmark Eval Set

Line A creates a smaller, high-quality benchmark set.

Purpose:

- Measure first-attempt model capability per difficulty tier.
- Provide stable acceptance tests for System-HIS, cross-file consistency, and
  tool pass rates.
- Later select representative designs for L4 timing closure and L5 board runs.

Inputs and outputs:

```text
compositional generator
-> requirement
-> System-HIS v1.2
-> contract
-> reference multi-file RTL implementation
-> black-box self-checking testbench
-> constraints
-> difficulty tier
```

Line A items should be quality-controlled. Each reference implementation and
testbench pair must be machine-checked so the benchmark is self-consistent.

### Line B: Training And Repair Trajectories

Line B creates larger-scale training data.

Purpose:

- Produce successful L3 samples.
- Produce real failure, diagnosis, repair, and retry trajectories.
- Feed `REQ2HIS`, `HIS2PROJECT`, `REQ2PROJECT`, `LOG2DIAG`,
  `FAILURE2PATCH`, `PROJECT_CRITIC`, and `QOR_PRED` views.

Default target mix for Line B:

```yaml
targets:
  l3_success_ratio: 0.4
  repair_trajectory_ratio: 0.6
```

This ratio is a starting policy, not a research claim. The runner should record
actual achieved counts because task difficulty and model behavior may change
the observed distribution.

## Component-Library MVP

The first new generator should be a compositional program generator, not a
larger set of handwritten fixed templates.

### Components

Initial components may include:

- register stage
- valid-ready stage
- skid buffer
- FIFO-like queue
- arbiter
- mux/demux
- ALU slice
- counter/timer
- MAC unit
- small ROM
- protocol adapter

The existing deterministic task families are seeds, not the final library:

- `counter`
- `fifo`
- `simple_fsm`
- `ram_read_write`
- `uart_tx`
- `spi_master`
- `pwm_controller`
- `fir_filter`
- `streaming_valid_ready`
- `matrix_vector_mac`

### Topology Generator

The topology generator should combine components into variable multi-module
projects:

- linear chains
- producer-consumer pipelines
- trees/reductions
- bus-like fanout/fanin patterns
- small controller plus datapath designs
- later CDC-marked designs

The point is not "many files" by itself. The point is cross-file contracts:
ports, widths, parameters, reset polarity, protocol timing, and module
connections must be consistent across System-HIS, manifest, RTL, constraints,
and testbench.

### System-HIS v1.2 Output

Each generated item should emit System-HIS at the structure-contract level:

- project name and top module
- clocks and target Fmax
- resets and polarity
- modules with roles, ports, params, clock/reset domain, and intent tag
- connections with protocol and width
- top ports
- verification contract
- QoR intent

Functional detail remains in the black-box testbench, not in System-HIS.

### Testbench Discipline

Testbenches must:

- test only the black-box interface contract;
- avoid internal signal names;
- initialize all inputs;
- include bounded watchdog timeouts;
- print `TEST_PASS` only on success;
- print `TEST_FAIL` with useful expected/actual context on failure;
- be verified against the generated reference implementation before being used
  as benchmark evidence.

This is important because LLM-written testbenches are not inherently certified.
Program-generated reference RTL plus testbench gives a machine-checked
self-consistency anchor.

## Difficulty Tiers

The runner and component generator should annotate each task with a provisional
difficulty tier:

- T1 Easy
- T2 Medium
- T3 Hard
- T4 Stress

The exact thresholds are not fixed yet. They should be calibrated during
baseline measurement. Candidate axes:

1. cross-file consistency load: number of modules, ports, parameters, and
   connections;
2. timing pressure: target Fmax and estimated critical-path depth;
3. protocol/control complexity: register, valid-ready, backpressure,
   AXI-lite/stream later;
4. structural scale and hierarchy depth;
5. CDC presence later.

The purpose is to find and report the frontier-model pass-rate knee rather than
only aggregate pass rates.

## Autonomous Runner

The runner should provide one primary control entry:

```bash
python3 -m LLM.src.sr2fpga_agent.runner --config configs/sr2fpga_agent.yaml
```

The existing one-sample CLI remains useful for debugging:

```bash
python3 -m LLM.src.sr2fpga_agent.cli ...
```

The runner owns batch orchestration, state, resume behavior, exports, and run
summaries. Codex should only start runs, inspect summaries, and adjust config.

## Runner Configuration

Example first config:

```yaml
dataset_root: datasets/sr2fpga_rtl_v1
export_root: datasets/sr2fpga_rtl_v1_exports
run_root: tmp/sr2fpga_runs
provider: deepseek
repair_provider: deepseek
max_attempts: 4
refresh_exports: true

line_b_targets:
  l3_success_ratio: 0.4
  repair_trajectory_ratio: 0.6
  max_samples: 20

tasks:
  - source: deepseek
    task_type: uart_tx
    widths: [8]
    count: 3
  - source: deepseek
    task_type: spi_master
    widths: [8]
    count: 3
  - source: compositional
    family: valid_ready_pipeline
    tiers: [T1, T2]
    count: 6
```

The exact YAML parser dependency is an implementation decision. If PyYAML is
already available, use it. If not, a JSON config fallback is acceptable for the
first implementation.

## Runner State And Resume

Each run should write:

```text
tmp/sr2fpga_runs/<run_id>/
  config.yaml
  run_state.json
  summary.json
  events.jsonl
  logs/
```

`run_state.json` should record:

- run id and config fingerprint;
- next sample id;
- completed samples;
- failed/rejected samples;
- per-task success counts;
- per-task repair trajectory counts;
- failure type histogram;
- last completed action;
- whether exports were refreshed.

The runner should be resumable. If interrupted, it should not overwrite
completed sample directories unless an explicit `--overwrite` option is given.

## Sample Buckets

Every completed sample should be categorized:

- `success_l3`: final label is L3 or higher.
- `repair_trajectory`: sample has meaningful failed attempts, diagnoses, or
  patches, even if final level is L1 or L2.
- `rejected`: invalid or unusable sample, such as unparseable LLM output,
  missing required files after retries, provider failure before an attempt can
  be written, or completely empty tool evidence.

`rejected` items should be summarized in run logs but excluded from standard
training exports unless a future experiment explicitly studies provider
failure behavior.

## Candidate Sources

The runner should eventually support multiple sources:

1. compositional generator;
2. deterministic generator;
3. DeepSeek;
4. local served model;
5. deliberately mutated/broken reference projects;
6. small real open-source IP anchors.

This is required by the reframe: data must be multi-source to support
tool-distillation claims and avoid pure LLM distillation.

## Repair Policy

V1 repair policy should remain bounded:

- preserve multi-file structure;
- preserve `manifest.json` unless the failure references it;
- generate local `patch.diff` by comparing files;
- retry until L3 or `max_attempts`;
- record every failed attempt.

For simulation failures, improve prompts and repair context to distinguish:

- `testbench_timeout`
- `functional_mismatch`
- `TEST_FAIL`
- missing `TEST_PASS`
- uninitialized testbench input
- unrealistic slow clock divider in simulation

The runner should collect these cases; it does not need to solve all of them in
the first implementation.

## L0 Consistency Checker

The reframe makes L0 a named component, not a side effect.

The current agent mostly validates manifest-level completeness and then relies
on tools. The next design should add a first-class L0 checker that validates
System-HIS against generated files:

- top module exists and matches manifest;
- declared submodules are instantiated;
- top ports match System-HIS names, directions, and widths;
- cross-module connections match port widths;
- reset names and polarity match;
- constraints reference real ports;
- testbench instantiates the real top module.

The first implementation can start with a narrow parser/checker for generated
Verilog patterns and expand later.

## Export Behavior

After each run or at configured intervals, the runner should refresh:

- `requirement_to_his.jsonl`
- `his_to_project.jsonl`
- `requirement_to_project.jsonl`
- `failure_to_diagnosis.jsonl`
- `failure_to_patch.jsonl`
- `project_to_predicted_qor.jsonl`
- `project_to_measured_qor.jsonl`

The runner should also write a compact run summary with counts and failure
histograms so humans do not need to inspect every sample manually.

## Out Of Scope For This First Slice

- OpenXC7 or Vivado execution.
- L4/L5 board flow.
- Training or fine-tuning a model.
- GA/RL QoR optimization.
- Full CIRCT lowering.
- Deep method-novelty implementation such as constrained decoding.
- A web UI.
- Any secret committed to Git.

## Success Criteria

The first implementation slice is successful when:

1. A single command starts a batch run from a config file.
2. The run can produce at least one DeepSeek multi-file trajectory sample
   without Codex manually invoking per-sample CLI commands.
3. The run records `run_state.json`, `events.jsonl`, and `summary.json`.
4. The run can resume without overwriting completed samples.
5. The run refreshes training exports.
6. The run classifies samples into `success_l3`, `repair_trajectory`, and
   `rejected`.
7. Unit tests cover config loading, sample-id generation, bucket classification,
   resume behavior, and export refresh.

The component-library MVP may be implemented as the following slice if keeping
the first runner slice small is necessary. However, the runner design must keep
the component-library source as a first-class future input, not as an
afterthought.

## Open Questions For User Confirmation

1. Should the first implementation prioritize the runner shell around existing
   DeepSeek/deterministic sources, or build the compositional component-library
   source first?
2. Should generated datasets continue to be committed as small research
   snapshots, or should future runs remain local artifacts with only summaries
   committed?
3. Should `run_root` live under ignored `tmp/`, or should selected run summaries
   be committed under `docs/runs/` for research traceability?
