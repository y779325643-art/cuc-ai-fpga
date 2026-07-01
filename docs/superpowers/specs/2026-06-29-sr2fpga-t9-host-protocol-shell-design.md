# SR2FPGA T9 Host Protocol Shell Design

Date: 2026-06-29

Status note (2026-06-30): this file keeps the legacy topology ID/name used by
the implementation (`t9_host_protocol_shell`). For public reporting, dataset
splits, and paper-facing discussion, it maps to compressed tier **T4: integrated
host-facing system shells**.

## Purpose

T9 is the next component-topology step after T8 toward the reinforcement-learning
accelerator flagship. T7 introduced a policy/value accelerator shell, and T8
introduced a replay/sample host-fabric memory boundary. T9 should introduce the
first protocol-shaped host/fabric wrapper: a small AXI-lite-style control/status
register interface plus an AXI-stream-style sample output interface.

The implementation target is a new deterministic task:

- `composed_host_protocol_shell`
- topology id: `t9_host_protocol_shell`
- difficulty tier: `T9`

T9 remains synthetic. Its job is to test whether SR2FPGA can generate a larger
multi-component project with protocol-shaped host control, status reads, command
decoding, streaming data output, and an interrupt/status signal. It is not yet a
full ARM-connected AC820-ZYNQ subsystem, DMA engine, or board shell.

## Current Baseline

The component-topology ladder is now:

- T1 `composed_event_counter`
- T2 `composed_stream_accumulator`
- T3 `composed_stream_fork`
- T4 `composed_dual_stream_join`
- T5 `composed_vector_mac_pipeline`
- T6 `composed_td_update_core`
- T7 `composed_policy_value_shell`
- T8 `composed_replay_sample_shell`

T9 should not try to combine all prior RTL blocks. Instead, it should add the
next missing complexity axis: protocol-shaped host/fabric integration. The
template must stay small enough for unit-test and Icarus simulation coverage.

## Scope

T9 should expose a minimal single-beat AXI-lite-style control/status interface
and a minimal AXI-stream-style sample output:

```text
write CTRL at addr 0x00: bit0=start, bit1=clear_irq
write SAMPLE0 at addr 0x04: stream payload low byte
write SAMPLE1 at addr 0x08: stream payload high byte
read STATUS at addr 0x0c: bit0=busy, bit1=done, bit2=irq
stream payload = {sample1, sample0}
irq = done until clear_irq is written
```

The generated task should:

- accept AXI-lite-style single-beat writes through `s_axi_awvalid`,
  `s_axi_awready`, `s_axi_awaddr`, `s_axi_wvalid`, `s_axi_wready`,
  `s_axi_wdata`, `s_axi_wstrb`, `s_axi_bvalid`, and `s_axi_bready`;
- accept AXI-lite-style single-beat reads through `s_axi_arvalid`,
  `s_axi_arready`, `s_axi_araddr`, `s_axi_rvalid`, `s_axi_rready`, and
  `s_axi_rdata`;
- emit AXI-stream-style payload through `m_axis_tvalid`, `m_axis_tready`,
  `m_axis_tdata`, and `m_axis_tlast`;
- expose `irq`;
- store two 8-bit sample registers and one control/status register block;
- emit one stream beat after `start`;
- set `done` and `irq` after the beat is accepted;
- clear `irq` when `clear_irq` is written;
- avoid burst AXI, outstanding transactions, byte-lane corner cases, DMA,
  external DDR, ARM software, board shell, and real RL workload semantics.

## Architecture

The new topology should use five reusable submodules:

- `axi_lite_write_ctrl`: accepts one write address/data handshake, emits decoded
  write enable, address, data, and response valid.
- `axi_lite_read_ctrl`: accepts one read address handshake, emits decoded read
  address and read valid.
- `control_reg_bank`: owns `ctrl`, `sample0`, `sample1`, `busy`, `done`, and
  `irq` state; decodes writes and forms `status_rdata`.
- `sample_stream_adapter`: emits one `{sample1, sample0}` AXI-stream beat after
  start and asserts `stream_done` when the beat is accepted.
- `irq_status`: exposes the registered interrupt line.

The top-level interface should expose:

- `clk`, `rst_n`
- AXI-lite write subset: `s_axi_awvalid`, `s_axi_awready`, `s_axi_awaddr`,
  `s_axi_wvalid`, `s_axi_wready`, `s_axi_wdata`, `s_axi_wstrb`,
  `s_axi_bvalid`, `s_axi_bready`
- AXI-lite read subset: `s_axi_arvalid`, `s_axi_arready`, `s_axi_araddr`,
  `s_axi_rvalid`, `s_axi_rready`, `s_axi_rdata`
- AXI-stream output subset: `m_axis_tvalid`, `m_axis_tready`, `m_axis_tdata`,
  `m_axis_tlast`
- interrupt output: `irq`

Suggested widths:

- `DATA_WIDTH` is the control data width and defaults to 8 in tests.
- `s_axi_awaddr` and `s_axi_araddr` can be 4 bits.
- `s_axi_wstrb` can be 1 bit for an 8-bit control data width.
- `m_axis_tdata` is `2*DATA_WIDTH` so it can carry `{sample1, sample0}`.

## Data Flow

Required component edges:

- `top.s_axi_awvalid` -> `axi_lite_write_ctrl.awvalid`
- `top.s_axi_awaddr` -> `axi_lite_write_ctrl.awaddr`
- `top.s_axi_wvalid` -> `axi_lite_write_ctrl.wvalid`
- `top.s_axi_wdata` -> `axi_lite_write_ctrl.wdata`
- `top.s_axi_wstrb` -> `axi_lite_write_ctrl.wstrb`
- `axi_lite_write_ctrl.awready` -> `top.s_axi_awready`
- `axi_lite_write_ctrl.wready` -> `top.s_axi_wready`
- `axi_lite_write_ctrl.bvalid` -> `top.s_axi_bvalid`
- `top.s_axi_bready` -> `axi_lite_write_ctrl.bready`
- `axi_lite_write_ctrl.write_valid` -> `control_reg_bank.write_valid`
- `axi_lite_write_ctrl.write_addr` -> `control_reg_bank.write_addr`
- `axi_lite_write_ctrl.write_data` -> `control_reg_bank.write_data`
- `top.s_axi_arvalid` -> `axi_lite_read_ctrl.arvalid`
- `top.s_axi_araddr` -> `axi_lite_read_ctrl.araddr`
- `axi_lite_read_ctrl.arready` -> `top.s_axi_arready`
- `axi_lite_read_ctrl.read_valid` -> `control_reg_bank.read_valid`
- `axi_lite_read_ctrl.read_addr` -> `control_reg_bank.read_addr`
- `control_reg_bank.read_data` -> `top.s_axi_rdata`
- `axi_lite_read_ctrl.rvalid` -> `top.s_axi_rvalid`
- `top.s_axi_rready` -> `axi_lite_read_ctrl.rready`
- `control_reg_bank.start_pulse` -> `sample_stream_adapter.start`
- `control_reg_bank.sample0` -> `sample_stream_adapter.sample0`
- `control_reg_bank.sample1` -> `sample_stream_adapter.sample1`
- `sample_stream_adapter.tvalid` -> `top.m_axis_tvalid`
- `top.m_axis_tready` -> `sample_stream_adapter.tready`
- `sample_stream_adapter.tdata` -> `top.m_axis_tdata`
- `sample_stream_adapter.tlast` -> `top.m_axis_tlast`
- `sample_stream_adapter.stream_done` -> `control_reg_bank.stream_done`
- `control_reg_bank.irq_state` -> `irq_status.irq_in`
- `irq_status.irq_out` -> `top.irq`

The deterministic template should accept only one write or one read transaction
at a time. It does not need to support concurrent outstanding reads/writes or
true AXI timing corner cases.

## System-HIS Requirements

The generated `system_his.json` should continue using `system-his-v1.2` and the
current aspect layout. T9 must exercise:

- `components`: include `top`, `axi_lite_write_ctrl`, `axi_lite_read_ctrl`,
  `control_reg_bank`, `sample_stream_adapter`, and `irq_status`.
- `instances`: include one instance of each non-top component.
- `interfaces`: include AXI-lite write subset, AXI-lite read subset, AXI-stream
  output subset, interrupt, clock, and reset ports.
- `data_flow`: describe write address/data capture, control/status register
  update, readback, stream payload output, stream done feedback, and irq output.
- `control_flow`: describe reset, write response, read response, start command,
  stream backpressure, done/irq set, and irq clear.
- `state`: mark `ctrl`, `sample0`, `sample1`, `busy`, `done`, and `irq_state`
  as owned by `control_reg_bank`; any protocol pending flags as owned by the
  AXI-lite controller instances.
- `timing`: retain positive `target_fmax_mhz` and include latency /
  initiation-interval metadata for write-to-stream and readback paths.
- `verification`: state that the bounded testbench writes sample registers,
  writes start, observes one stream beat, reads status, clears irq, and prints
  `TEST_PASS` only when all checks match.

## Runner And Prompt Integration

The implementation should extend the current `component_topology` path:

- add the topology to `COMPONENT_TOPOLOGIES`;
- add `composed_host_protocol_shell` to `SUPPORTED_TASK_TYPES`;
- make runner `component_topology` expansion accept `t9_host_protocol_shell`;
- add natural and contract requirement text for T9;
- add REQ->HIS fidelity top-port requirements for T9;
- extend DeepSeek two-stage guidance and multimodule source expectations for T9.

## Testing Strategy

Implementation should use TDD:

1. Add a failing generator test for `composed_host_protocol_shell` that checks
   task type, topology id, submodules, protocol-shaped top ports, state
   ownership, manifest sources, and deterministic testbench content.
2. Add the T9 case to supported-task manifest coverage and Icarus multimodule
   simulation coverage.
3. Add a failing runner test showing `component_topology` expansion includes
   `t9_host_protocol_shell`.
4. Add a failing fidelity test that rejects missing T9 AXI-lite/stream/irq
   ports.
5. Add a failing DeepSeek prompt test that requires the T9 architecture guidance
   and expected RTL files.
6. Implement the minimal generator, runner, fidelity, and prompt changes to pass
   those tests.
7. Run focused tests, then the full `LLM/tests` suite, `compileall`, and
   `git diff --check`.

The deterministic testbench should:

```text
write SAMPLE0 addr 0x04 = 0x12
write SAMPLE1 addr 0x08 = 0x34
write CTRL addr 0x00 = 0x01
expect m_axis_tvalid, m_axis_tdata = 0x3412, m_axis_tlast = 1
read STATUS addr 0x0c and expect done=1, irq=1
write CTRL addr 0x00 = 0x02
read STATUS addr 0x0c and expect irq=0
```

## Non-Goals

T9 is not the full reinforcement-learning accelerator. These are intentionally
deferred:

- full AXI4-Lite compliance including independent outstanding channels;
- AXI-stream packets longer than one beat;
- DMA, external DDR, cache coherency, or ARM software drivers;
- real DQN, actor-critic, or policy-gradient workload fidelity;
- combining T7/T8 datapaths into one realistic accelerator;
- board-level shell, OpenXC7/Vivado physical closure, or AC820 pin constraints.

T10 or later should either combine T7 policy/value and T8 replay storage under
the T9 protocol shell, or switch from synthetic tasks to a real algorithm
reference supplied by the user.

## Human Input Needed

T9 can still be implemented synthetically without user-provided reference
material. It improves complex-project generation coverage by adding
protocol-shaped host control and stream output.

Before the project claims a realistic RL accelerator, user or external reference
input becomes required. The minimum reference package should include:

- RL algorithm family, such as DQN, actor-critic, or policy-gradient inference;
- observation vector length and element format;
- action count and action-selection rule;
- replay sample schema and batch size;
- host register map and stream packet format;
- fixed-point scale, signedness, rounding, and saturation policy;
- whether FPGA fabric owns inference only, update only, replay/sample logic, or
  all three;
- FPGA/ARM boundary on AC820-ZYNQ;
- clock target, DSP budget, BRAM budget, and I/O expectations;
- any Python, HLS, RTL, or paper reference for the intended workload.

Without those inputs, T9 remains a valid synthetic protocol shell but should not
be described as application-realistic.

## Self-Review

- No placeholders remain in this document.
- The task is scoped to one deterministic topology and its existing integration
  points.
- The AXI-lite-style write/read subset, AXI-stream-style output, status/irq
  behavior, and verification expectations are concrete enough for a TDD
  implementation plan.
- The design advances host/fabric protocol complexity beyond T8 without taking
  on full RL accelerator scope.
