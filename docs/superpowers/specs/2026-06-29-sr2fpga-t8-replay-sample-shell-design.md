# SR2FPGA T8 Replay Sample Shell Design

Date: 2026-06-29

Status note (2026-06-30): this file keeps the legacy topology ID/name used by
the implementation (`t8_replay_sample_shell`). For public reporting, dataset
splits, and paper-facing discussion, it maps to compressed tier **T3: datapath
and memory shells**.

## Purpose

T8 is the next component-topology step after T7 toward the reinforcement-learning
accelerator flagship. T5 covered an RL-shaped vector-MAC inference datapath, T6
covered a temporal-difference update datapath, and T7 introduced a small
policy/value shell with configuration state and action/value output. T8 should
introduce the first host/fabric memory boundary: a replay/sample shell that lets
host-side logic write compact transition samples and lets fabric-side logic read
those samples through a valid-ready output.

The implementation target is a new deterministic task:

- `composed_replay_sample_shell`
- topology id: `t8_replay_sample_shell`
- difficulty tier: `T8`

T8 remains synthetic. Its job is to test whether SR2FPGA can generate a larger
multi-component project with a small memory, write-side host interface, read-side
fabric interface, occupancy tracking, and deterministic sample packing. It is
not yet a full AC820-ZYNQ RL accelerator, replay buffer, or AXI-connected system.

## Current Baseline

The component-topology ladder is now:

- T1 `composed_event_counter`
- T2 `composed_stream_accumulator`
- T3 `composed_stream_fork`
- T4 `composed_dual_stream_join`
- T5 `composed_vector_mac_pipeline`
- T6 `composed_td_update_core`
- T7 `composed_policy_value_shell`

T8 should build on the T7 host/fabric boundary idea without depending on the T7
RTL. The deterministic template should remain small enough for unit-test and
Icarus simulation coverage while adding the next architectural concepts:
sample-store memory, host writes, fabric reads, replay occupancy, and packed
transition outputs.

## Scope

T8 should accept compact replay samples from a host-style write interface and
emit packed samples to a fabric-style read interface:

```text
sample = {state, action, reward, next_state, done}
packed_sample = {state, next_state, reward, action, done}
occupancy = number of stored samples
sample_valid = read request accepted and memory contains a sample
```

The exact sample is intentionally tiny:

- `state`: `DATA_WIDTH`
- `next_state`: `DATA_WIDTH`
- `reward`: `DATA_WIDTH`
- `action`: 1 bit
- `done`: 1 bit

The generated task should:

- expose a host write side: `host_valid`, `host_ready`, `host_state`,
  `host_action`, `host_reward`, `host_next_state`, and `host_done`;
- expose a fabric read side: `sample_ready`, `sample_valid`, `sample_state`,
  `sample_action`, `sample_reward`, `sample_next_state`, and `sample_done`;
- track replay occupancy with `occupancy`;
- store at least four samples in a deterministic circular buffer;
- reject writes when full and hold reads when empty;
- emit samples in FIFO order for deterministic verification;
- use fixed-width integer fields;
- avoid random sampling, priorities, AXI, DMA, external DDR, ARM software,
  board shell, floating point, and a full training loop.

## Architecture

The new topology should use five reusable submodules:

- `host_sample_stage`: accepts host-side valid-ready sample writes and stages the
  incoming transition tuple.
- `replay_store`: owns a small circular replay memory, write pointer, read
  pointer, and occupancy counter.
- `sample_read_stage`: accepts fabric-side ready, requests a sample when the
  store is non-empty, and stages output valid/data.
- `sample_pack_core`: presents the stored sample fields in a stable packed-order
  payload and keeps field-level outputs.
- `occupancy_counter`: exposes the replay occupancy as a top-level status signal.

The top-level interface should expose:

- `clk`, `rst_n`
- host write input: `host_valid`, `host_ready`, `host_state`, `host_action`,
  `host_reward`, `host_next_state`, `host_done`
- fabric sample output: `sample_valid`, `sample_ready`, `sample_state`,
  `sample_action`, `sample_reward`, `sample_next_state`, `sample_done`
- status output: `occupancy`

Suggested widths:

- `host_state`, `host_reward`, `host_next_state`, `sample_state`,
  `sample_reward`, and `sample_next_state` use `DATA_WIDTH`.
- `host_action`, `host_done`, `sample_action`, and `sample_done` are 1 bit.
- `occupancy` can be 3 bits for a depth-4 store, so values 0-4 are representable.
- The store depth is fixed at 4 in the deterministic template.

## Data Flow

Required component edges:

- `top.host_valid` -> `host_sample_stage.in_valid`
- `top.host_state` -> `host_sample_stage.state`
- `top.host_action` -> `host_sample_stage.action`
- `top.host_reward` -> `host_sample_stage.reward`
- `top.host_next_state` -> `host_sample_stage.next_state`
- `top.host_done` -> `host_sample_stage.done`
- `host_sample_stage.in_ready` -> `top.host_ready`
- `host_sample_stage.out_valid` -> `replay_store.write_valid`
- `host_sample_stage.state_out` -> `replay_store.write_state`
- `host_sample_stage.action_out` -> `replay_store.write_action`
- `host_sample_stage.reward_out` -> `replay_store.write_reward`
- `host_sample_stage.next_state_out` -> `replay_store.write_next_state`
- `host_sample_stage.done_out` -> `replay_store.write_done`
- `replay_store.write_ready` -> `host_sample_stage.out_ready`
- `top.sample_ready` -> `sample_read_stage.out_ready`
- `sample_read_stage.read_ready` -> `replay_store.read_ready`
- `replay_store.read_valid` -> `sample_read_stage.in_valid`
- `replay_store.read_state` -> `sample_pack_core.state`
- `replay_store.read_action` -> `sample_pack_core.action`
- `replay_store.read_reward` -> `sample_pack_core.reward`
- `replay_store.read_next_state` -> `sample_pack_core.next_state`
- `replay_store.read_done` -> `sample_pack_core.done`
- `sample_pack_core.sample_state` -> `sample_read_stage.sample_state`
- `sample_pack_core.sample_action` -> `sample_read_stage.sample_action`
- `sample_pack_core.sample_reward` -> `sample_read_stage.sample_reward`
- `sample_pack_core.sample_next_state` -> `sample_read_stage.sample_next_state`
- `sample_pack_core.sample_done` -> `sample_read_stage.sample_done`
- `sample_read_stage.out_valid` -> `top.sample_valid`
- `sample_read_stage.sample_state_out` -> `top.sample_state`
- `sample_read_stage.sample_action_out` -> `top.sample_action`
- `sample_read_stage.sample_reward_out` -> `top.sample_reward`
- `sample_read_stage.sample_next_state_out` -> `top.sample_next_state`
- `sample_read_stage.sample_done_out` -> `top.sample_done`
- `replay_store.occupancy` -> `occupancy_counter.occupancy_in`
- `occupancy_counter.occupancy_out` -> `top.occupancy`

The deterministic template may serialize writes and reads. It does not need to
support simultaneous write and read pointer updates in the same cycle if that
would complicate the first T8 implementation. If simultaneous write/read is
supported, occupancy must remain correct.

## System-HIS Requirements

The generated `system_his.json` should continue using `system-his-v1.2` and the
current aspect layout. T8 must exercise:

- `components`: include `top`, `host_sample_stage`, `replay_store`,
  `sample_read_stage`, `sample_pack_core`, and `occupancy_counter`.
- `instances`: include one instance of each non-top component.
- `interfaces`: include host write, fabric sample output, status, clock, and
  reset ports.
- `data_flow`: describe host sample staging, replay memory write, replay memory
  read, sample packing, sample output staging, and occupancy reporting.
- `control_flow`: describe reset, host backpressure when full, read stall when
  empty, valid-ready sample transfers, write-pointer update, read-pointer
  update, and occupancy update.
- `state`: mark replay memories, write pointer, read pointer, and occupancy as
  owned by `replay_store`; staged input sample registers as owned by
  `host_sample_stage`; staged output sample registers as owned by
  `sample_read_stage`.
- `timing`: retain positive `target_fmax_mhz` and include latency /
  initiation-interval metadata for the write-to-read sample path.
- `verification`: state that the bounded testbench writes at least three samples,
  checks occupancy, reads samples back in FIFO order, verifies all fields, and
  prints `TEST_PASS` only when all checks match.

## Runner And Prompt Integration

The implementation should extend the current `component_topology` path:

- add the topology to `COMPONENT_TOPOLOGIES`;
- add `composed_replay_sample_shell` to `SUPPORTED_TASK_TYPES`;
- make runner `component_topology` expansion accept `t8_replay_sample_shell`;
- add natural and contract requirement text for T8;
- add REQ->HIS fidelity top-port requirements for T8;
- extend DeepSeek two-stage guidance and multimodule source expectations for T8.

## Testing Strategy

Implementation should use TDD:

1. Add a failing generator test for `composed_replay_sample_shell` that checks
   task type, topology id, submodules, top ports, state ownership, manifest
   sources, and deterministic testbench content.
2. Add the T8 case to supported-task manifest coverage and Icarus multimodule
   simulation coverage.
3. Add a failing runner test showing `component_topology` expansion includes
   `t8_replay_sample_shell`.
4. Add a failing fidelity test that rejects missing T8 host/sample/occupancy
   ports.
5. Add a failing DeepSeek prompt test that requires the T8 architecture guidance
   and expected RTL files.
6. Implement the minimal generator, runner, fidelity, and prompt changes to pass
   those tests.
7. Run focused tests, then the full `LLM/tests` suite, `compileall`, and
   `git diff --check`.

The deterministic testbench should write and read at least these samples:

```text
sample0: state=3, action=1, reward=4, next_state=5, done=0
sample1: state=8, action=0, reward=2, next_state=9, done=1
sample2: state=1, action=1, reward=7, next_state=6, done=0
```

Expected readback is FIFO order with identical fields. Occupancy should be 3
after three writes and 0 after three successful reads.

## Non-Goals

T8 is not the full reinforcement-learning accelerator. These are intentionally
deferred:

- random replay sampling or prioritized replay;
- batch-size greater than one sample per output transfer;
- external DDR or DMA;
- AXI-lite or AXI-stream protocol-complete interfaces;
- ARM software driver or environment loop;
- real DQN, actor-critic, or policy-gradient workload fidelity;
- floating-point support;
- board-level shell, OpenXC7/Vivado physical closure, or AC820 pin constraints.

T9 or later should either add a protocol-complete host/fabric wrapper or combine
T7 policy/value output with T8 sample storage under a realistic algorithm
reference.

## Human Input Needed

T8 can still be implemented synthetically without user-provided reference
material. It improves complex-project generation coverage by adding memory,
occupancy, and host/fabric boundary behavior.

Before the project claims a realistic RL accelerator, user or external reference
input becomes required. The minimum reference package should include:

- RL algorithm family, such as DQN, actor-critic, or policy-gradient inference;
- observation vector length and element format;
- action count and action-selection rule;
- replay sample schema and batch size;
- fixed-point scale, signedness, rounding, and saturation policy;
- whether FPGA fabric owns inference only, update only, replay/sample logic, or
  all three;
- FPGA/ARM boundary on AC820-ZYNQ;
- clock target, DSP budget, BRAM budget, and I/O expectations;
- any Python, HLS, RTL, or paper reference for the intended workload.

Without those inputs, T8 remains a valid synthetic replay shell but should not be
described as application-realistic.

## Self-Review

- No placeholders remain in this document.
- The task is scoped to one deterministic topology and its existing integration
  points.
- The host write, replay store, read output, occupancy, and verification
  behaviors are concrete enough for a TDD implementation plan.
- The design advances host/fabric and replay/sample complexity beyond T7 without
  taking on full RL accelerator scope.
