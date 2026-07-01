# SR2FPGA Official Eval Set Gap Closure Design

## Purpose

Close the task-coverage gap identified after comparing the current SR2FPGA task
families with common RTL-generation benchmarks. The goal is not to create a
large standalone benchmark. The goal is to define a publication-ready official
evaluation set that is broad enough to answer reviewer concerns about task
diversity while staying aligned with SR2FPGA's main contribution:
project-level, tool-verified RTL project generation and repair trajectories.

This design records the approved Plan B:

- reorganize existing task families into a literature-aligned official eval set;
- stop extending the synthetic RL ladder by default;
- add only two missing task families for processor-like and data-integrity
  coverage;
- keep integrated T4 shell tasks as supplemental complexity evidence rather than
  primary aggregate metrics.

Status note (2026-06-30): the accompanying config is a **gap-closure scaffold**,
not the final frozen official aggregate. The public/reporting curriculum is
compressed to T0-T4; legacy topology IDs t5-t12 remain implementation IDs. The
scaffold may include integrated T4 shell tasks so their supplemental results can
be generated in the same dry run, but paper-facing primary aggregates must either
exclude them or report them in a separate supplemental table until real workload
references exist.

## Background

SR2FPGA already supports a wider task surface than the current baseline configs
exercise. The implementation includes simple RTL blocks, multi-module blocks,
component topologies, and an RL-shaped synthetic ladder. The publication risk is
that official experiments currently concentrate on the legacy t1-t4 topology IDs,
which can look narrow when compared with HDLBits-derived, RTLLM-style, VerilogEval-style,
AutoChip-style, ResBench-style, and repository-level RTL benchmarks.

The fix should not be another open-ended synthetic ladder. The reframe protocol
already separates:

- Line A: benchmark eval set, quality-first, modest scale;
- Line B: training and trajectory data, scale-first, automated L0-L3 collection.

This document defines the Line A task-family coverage that should be frozen
before scaled official experiments.

## Design Principles

1. **Coverage before scale.** First freeze a balanced official set, then scale
   samples per family.
2. **Project-level first.** Prefer tasks that exercise System-HIS, manifest,
   multi-file RTL, constraints, testbench, and cross-file L0 checking.
3. **Minimal new implementation.** Reuse existing families where they cover a
   literature category; add only categories that are genuinely missing.
4. **No benchmark sprawl.** Do not compete with HDLBits/VerilogEval on number of
   small problems. SR2FPGA's differentiator is tool-verified project
   trajectories.
5. **Clear reporting boundary.** Integrated T4 shell tasks are useful
   supplemental complexity examples, but not the primary aggregate evaluation set
   until real workload references exist.
6. **Prompt-information boundary.** Official `simple_prompt` baselines may state
   externally checkable obligations, interfaces, and acceptance behavior, but must
   not encode module-level implementation recipes. Contract-rich/System-HIS views
   may expose structure because that is the evaluated treatment; report those
   separately from the simple-prompt baseline.

## Literature-Aligned Coverage Categories

The official eval set should cover these RTL-generation categories:

| Category | Why it matters |
| --- | --- |
| Control / FSM | Common in HDLBits, VerilogEval, RTLLM, and repair benchmarks. |
| Stream / handshake | Exposes backpressure and temporal protocol failures often missed by simple tests. |
| Arithmetic / datapath | Covers DSP-style datapaths, accumulation, and bit-width failure modes. |
| Memory / buffering | Covers FIFO/RAM state, ordering, and resource-inference behavior. |
| Protocol / host interface | Covers serial/control interfaces and software-visible boundary behavior. |
| Hierarchy / composition | Exercises cross-file consistency, submodule integration, and manifest correctness. |
| Processor-like control | Covers ALU/control style tasks found in many RTL benchmark suites. |
| Checksum / data integrity | Covers shift/XOR feedback, stream framing, and protocol-adjacent logic. |

## Official Eval Set

Use the following task families as the primary official eval set after the two
new families are implemented.

| Literature category | SR2FPGA family | Status | Primary role |
| --- | --- | --- | --- |
| Control / FSM | `simple_fsm` | existing | Single-module FSM baseline and Tier-2 control-flow ratification. |
| Control / FSM | `composed_event_counter` | existing | Multi-module event gating plus counter state. |
| Stream / handshake | `composed_stream_accumulator` | existing | Valid-ready stream accumulation and backpressure. |
| Stream / handshake | `composed_stream_fork` | existing | One input stream, two output streams, cross-file flow wiring. |
| Stream / handshake | `composed_dual_stream_join` | existing | Dual input synchronization, FSM/control-flow stress. |
| Arithmetic / datapath | `fir_filter` | existing | MAC helper composition and fixed pipeline behavior. |
| Arithmetic / datapath | `matrix_vector_mac` | existing | Fixed dot-product compute and accumulation. |
| Arithmetic / datapath | `composed_vector_mac_pipeline` | existing | RL-shaped feature pipeline without real workload claims. |
| Memory / buffering | `fifo` | existing | Ordering, state, empty/full behavior. |
| Memory / buffering | `ram_read_write` | existing | RAM read/write semantics and synthesis resource behavior. |
| Memory / buffering | `composed_replay_sample_shell` | existing | Host/fabric sample buffering as supplemental memory boundary. |
| Protocol / host interface | `uart_tx` | existing | Serial protocol control and timed output. |
| Protocol / host interface | `spi_master` | existing | Serial master control and sampled input. |
| Protocol / host interface | `composed_host_protocol_shell` | existing | Software-visible control/status and stream shell. |
| Processor-like control | `alu_control_unit` | new | ALU operation select, flags, and simple control decode. |
| Checksum / data integrity | `crc_stream_checker` | new | Streaming CRC/checksum update with frame-valid result. |

The first official frozen set should contain one canonical configuration per
family plus parameter-heldout variants. That gives 16 families before parameter
variants. If runtime or API cost is high, the TRETS-safe minimum can use a
12-family subset by keeping one representative from each category and moving
the remaining entries to supplemental per-family tables.

The frozen aggregate should be derived from this table, not directly from any
gap-closure scaffold config that also runs supplemental integrated-shell samples.

## New Task Family: `alu_control_unit`

### Intent

Add a small processor-like task without turning SR2FPGA into a CPU benchmark.
This covers ALU/control categories common in RTL-generation literature while
remaining easy to verify through L0-L3.

### Project Shape

Suggested RTL files:

- `rtl/top.v`
- `rtl/alu_core.v`
- `rtl/control_decode.v`
- `rtl/status_flags.v`

### Interface

Use a single-clock, active-low reset interface:

- inputs: `clk`, `rst_n`, `valid`, `op[2:0]`, `lhs[WIDTH-1:0]`,
  `rhs[WIDTH-1:0]`
- outputs: `ready`, `result[WIDTH-1:0]`, `zero`, `carry`, `negative`,
  `result_valid`

### Behavior

Support a fixed operation set:

- `000`: add
- `001`: subtract
- `010`: bitwise and
- `011`: bitwise or
- `100`: bitwise xor
- `101`: logical shift left by `rhs[2:0]`
- `110`: logical shift right by `rhs[2:0]`
- `111`: pass `lhs`

The testbench should check every operation, at least one carry case, at least
one zero case, and at least one negative-MSB case. The task should be
single-cycle or one registered output stage; the chosen latency must be recorded
in System-HIS and tested consistently.

## New Task Family: `crc_stream_checker`

### Intent

Add a data-integrity and protocol-adjacent streaming task. This closes a gap
between simple stream movement and more realistic communication logic without
introducing vendor IP, external buses, or large protocol stacks.

### Project Shape

Suggested RTL files:

- `rtl/top.v`
- `rtl/crc8_update.v`
- `rtl/stream_frame_accumulator.v`
- `rtl/crc_status.v`

### Interface

Use a valid-ready byte stream:

- inputs: `clk`, `rst_n`, `in_valid`, `in_data[7:0]`, `frame_start`,
  `frame_end`, `expected_crc[7:0]`, `out_ready`
- outputs: `in_ready`, `crc_value[7:0]`, `crc_match`, `crc_valid`

### Behavior

Use CRC-8 with polynomial `0x07`, initial value `0x00`, and byte-serial updates.
The implementation does not need to support reflected input/output. The
testbench should verify:

- reset clears the CRC accumulator;
- a known byte sequence produces the expected CRC;
- `crc_valid` asserts on `frame_end`;
- `crc_match` compares against `expected_crc`;
- backpressure on `out_ready` does not drop the final CRC result.

## Supplemental Complexity Ladder

Integrated T4 shell tasks remain useful, but they should not define the official
aggregate result until real RL workload references exist.

| Family | Reporting role |
| --- | --- |
| `composed_rl_accelerator_shell` | Supplemental integrated synthetic shell. |
| `composed_batch_rl_accelerator_shell` | Supplemental multi-lane synthetic shell. |
| `composed_replay_arbiter_shell` | Supplemental replay arbitration and packetization shell. |

Do not add a new synthetic tier by default. Any future post-T4 curriculum
extension requires an explicit real workload reference or a separate approved
design that shows why the missing axis affects publication evidence.

## Split And Measurement Policy

All official `(a)/(b)/(c)` comparisons must use the same task set, split,
hidden tests, repair budget, timeout, tool versions, and prompt family. The
official eval set should support the reframe split policy:

- S1 parameter-heldout: unseen width, depth, latency, or parallelism values
  inside the same family;
- S2 topology-heldout: unseen wiring or topology variants;
- S3 component-combination-heldout: unseen combinations of known components;
- S4 family-heldout: one or more families held out from training;
- S5 real-IP external: real open-source IP only for external validation, never
  for training.

The initial frozen Line A set should define:

- canonical family list;
- canonical width/depth/latency variants;
- hidden/stress L2 scenarios per family;
- deterministic reference requirement for B_ref and B_template;
- release-tier markers for generated artifacts and tool logs.

## TRETS-Safe Reporting

For a TRETS-safe paper, this gap closure supports:

- System-HIS and L0-L5 benchmark definition;
- tool-verified trajectory factory;
- L0-L3 scaled results over a balanced official task set;
- tool-in-loop repair delta `b - a`;
- failure taxonomy and semantic-gap heatmap by category;
- optional OpenXC7 L4 representative evidence if available.

The TRETS-safe result does not require the new SFT point `(c)`, but the official
task set must be frozen before scaling `(a)` and `(b)`.

## TCAD-Strong Reporting

For a TCAD-strong paper, this gap closure is necessary but not sufficient. TCAD
still requires:

- System-HIS-constrained / contract-preserving generation ablation;
- trained model point `(c)`;
- System-HIS ablation;
- structured diagnosis-to-patch ablation;
- OpenXC7 plus Vivado commercial-reference validation on a representative L4
  subset;
- at least one verified L4 or L5-min physical result.

The new `alu_control_unit` and `crc_stream_checker` families should be included
in L4 candidate screening only after their deterministic B_ref samples pass
L0-L3 consistently.

## Non-Goals

This design does not:

- create a general HDLBits replacement;
- add CPU, RISC-V, DDR, PCIe, Ethernet, AES, or vendor-IP tasks;
- claim realistic RL accelerator coverage from synthetic integrated-shell tasks;
- change the System-HIS v1.2 schema;
- change the official L0-L5 definitions;
- start model fine-tuning;
- commit generated datasets or run logs.

## Implementation Boundary

The follow-up implementation plan should modify only the pieces needed to make
the two new task families first-class:

- `LLM/src/sr2fpga_agent/project_generator.py`;
- runner topology/task expansion only if required;
- unit tests for generator, runner expansion, L0/HIS fidelity, and DeepSeek
  prompt guidance where applicable;
- docs/current-status and README task lists;
- optional official eval config templates after deterministic B_ref passes.

Do not mix implementation of the new task families with scaled official
experiment runs. First land deterministic support and tests; then freeze eval
configs; then run scaled Line A and Line B experiments.

## Acceptance Criteria

The design is ready to hand off to implementation when:

1. the official eval set table above is accepted as the frozen coverage target;
2. `alu_control_unit` and `crc_stream_checker` are the only new V1 task
   families;
3. integrated T4 shell tasks are reported as supplemental complexity evidence;
4. no post-T4 synthetic tier starts without a new approved design;
5. implementation is planned as deterministic support first, scaled experiment
   execution second.
