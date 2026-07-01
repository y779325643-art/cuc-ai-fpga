# SR2FPGA T12 Replay Arbiter Shell Design

Date: 2026-06-29

Status note (2026-06-30): this file keeps the legacy topology ID/name used by
the implementation (`t12_replay_arbiter_shell`). For public reporting, dataset
splits, and paper-facing discussion, it maps to compressed tier **T4: integrated
host-facing system shells**.

## Purpose

T12 is the next component-topology step after T11 toward the reinforcement-
learning accelerator flagship. T11 added two-lane batch compute. T12 should add
the next synthetic complexity axis: replay-memory host packetization and
fabric-side sample read arbitration.

The implementation target is a new deterministic task:

- `composed_replay_arbiter_shell`
- topology id: `t12_replay_arbiter_shell`
- difficulty tier: `T12`

T12 remains synthetic. Its job is to test whether SR2FPGA can generate and
verify a replay-buffer-style subsystem with host transition packet writes,
indexed fabric sample requests, deterministic read/write arbitration, sample
packet output, occupancy reporting, and irq reporting. It is not yet random
replay sampling, prioritized replay, DMA, DDR, AC820-ZYNQ software, or a
realistic RL training memory subsystem.

## Current Baseline

The late ladder is now:

- T8 `composed_replay_sample_shell`: FIFO-like replay sample boundary.
- T10 `composed_rl_accelerator_shell`: one-sample integrated RL shell.
- T11 `composed_batch_rl_accelerator_shell`: two-lane batch compute shell.

T12 should extend replay realism without taking on true stochastic sampling.
It should model the host/fabric contention shape that a real replay path needs:
host writes transition packets, fabric asks for a sample by index, and an
arbiter controls memory access and output packet staging.

## Scope

T12 should expose:

- host write packet input: `host_valid`, `host_ready`, `host_state`,
  `host_action`, `host_reward`, `host_next_state`, `host_done`
- fabric indexed read request: `sample_req_valid`, `sample_req_ready`,
  `sample_index`
- sample packet output: `sample_valid`, `sample_ready`, `sample_state`,
  `sample_action`, `sample_reward`, `sample_next_state`, `sample_done`
- status: `occupancy`, `write_index`, `irq`

The generated task should:

- pack host transition fields into one replay write transaction;
- write each host packet into a depth-4 replay memory at `write_index`;
- increment `write_index` modulo 4;
- saturate `occupancy` at 4;
- accept a fabric read request only when `sample_index < occupancy`;
- read the requested entry and stage it as a valid-ready sample packet;
- prioritize host writes over read requests when both arrive in the same cycle;
- assert `irq` when a requested sample packet is accepted by the fabric;
- avoid random sampling, prioritized replay trees, multi-port memory, DMA, DDR,
  host software, board shell, and real RL workload fidelity.

## Architecture

The new topology should use five reusable submodules:

- `host_transition_packetizer`: captures host transition fields and emits a
  packed write command.
- `replay_index_allocator`: owns `write_index` and `occupancy`.
- `replay_request_arbiter`: prioritizes host writes over sample read requests
  and emits memory write/read commands.
- `replay_memory_bank`: owns the depth-4 transition memory and read data.
- `sample_packet_stage`: stages read data as a valid-ready sample output and
  owns `irq`.

The top-level interface should expose:

- `clk`, `rst_n`
- host packet input: `host_valid`, `host_ready`, `host_state`, `host_action`,
  `host_reward`, `host_next_state`, `host_done`
- sample request input: `sample_req_valid`, `sample_req_ready`,
  `sample_index`
- sample output: `sample_valid`, `sample_ready`, `sample_state`,
  `sample_action`, `sample_reward`, `sample_next_state`, `sample_done`
- status output: `occupancy`, `write_index`, `irq`

## Data Flow

Required component edges:

- host top ports -> `host_transition_packetizer`
- `host_transition_packetizer.packet_valid` -> `replay_request_arbiter.write_valid`
- `host_transition_packetizer` packet fields -> `replay_request_arbiter`
- `replay_index_allocator.write_index` -> `replay_request_arbiter.write_index`
- `replay_index_allocator.occupancy` -> `replay_request_arbiter.occupancy`
- `top.sample_req_valid` -> `replay_request_arbiter.read_req_valid`
- `top.sample_index` -> `replay_request_arbiter.sample_index`
- `replay_request_arbiter.sample_req_ready` -> `top.sample_req_ready`
- `replay_request_arbiter.mem_write_valid` -> `replay_memory_bank.write_valid`
- `replay_request_arbiter.mem_read_valid` -> `replay_memory_bank.read_valid`
- `replay_request_arbiter` write/read addresses and payload fields ->
  `replay_memory_bank`
- `replay_memory_bank.read_valid` -> `sample_packet_stage.in_valid`
- `replay_memory_bank` read fields -> `sample_packet_stage`
- `sample_packet_stage` sample outputs -> top sample outputs
- `sample_packet_stage.sample_accepted` -> `top.irq`
- `replay_request_arbiter.write_accepted` -> `replay_index_allocator.write_accepted`
- `replay_index_allocator.occupancy` -> `top.occupancy`
- `replay_index_allocator.write_index` -> `top.write_index`

The template should use deterministic single-cycle memory read semantics. Host
writes have priority over reads. A read request that conflicts with a host write
stalls until the next cycle.

## System-HIS Requirements

The generated `system_his.json` should continue using `system-his-v1.2` and the
current aspect layout. T12 must exercise:

- `components`: include `top`, `host_transition_packetizer`,
  `replay_index_allocator`, `replay_request_arbiter`, `replay_memory_bank`, and
  `sample_packet_stage`.
- `instances`: include one instance of each non-top component.
- `interfaces`: include host transition packet input, indexed sample request,
  sample packet output, status, interrupt, clock, and reset ports.
- `data_flow`: describe host packetization, write index allocation, replay
  memory write/read, sample packet staging, and irq output.
- `control_flow`: describe reset, host-write priority, read request gating by
  `sample_index < occupancy`, output backpressure, and irq-on-accept behavior.
- `state`: mark `write_index` and `occupancy` as owned by
  `replay_index_allocator`; replay entry memory as owned by
  `replay_memory_bank`; staged sample packet and irq as owned by
  `sample_packet_stage`.
- `verification`: state that the bounded testbench writes two host packets,
  reads index 0 and index 1, checks sample payloads, occupancy, write index,
  and irq, and prints `TEST_PASS` only when all checks match.

## Testing Strategy

Implementation should use TDD:

1. Add a failing generator test for `composed_replay_arbiter_shell` that checks
   topology id, submodules, replay-arbiter top ports, state ownership, manifest
   sources, and deterministic testbench checks.
2. Add the T12 case to supported-task manifest coverage and Icarus multimodule
   simulation coverage.
3. Add a failing runner test showing `component_topology` expansion includes
   `t12_replay_arbiter_shell`.
4. Add a failing fidelity test that rejects missing T12 host, request, sample,
   status, and irq ports.
5. Add a failing DeepSeek prompt test that requires T12 architecture guidance
   and expected RTL files.
6. Implement the minimal generator, runner, fidelity, and prompt changes.
7. Run focused tests, full `LLM/tests`, `compileall`, and `git diff --check`.

The deterministic testbench should:

```text
write packet 0: state=0x12, action=0, reward=0x03, next_state=0x21, done=0
write packet 1: state=0x34, action=1, reward=0x05, next_state=0x43, done=1
expect occupancy=2 and write_index=2
request sample_index=0; expect packet 0
request sample_index=1; expect packet 1 and irq=1 after accepted output
```

## Non-Goals

T12 is not the final realistic replay subsystem. These are intentionally
deferred:

- random replay sampling or prioritized replay;
- multi-port memory or concurrent true read/write;
- batch sample output;
- AXI, DMA, DDR, ARM software, or board shell;
- real replay schema from a target RL algorithm;
- measured QoR on a real target device.

## Human Input Needed

T12 can still be implemented synthetically without user-provided reference
material. It improves complex-project generation coverage by adding replay
packetization and deterministic read/write arbitration.

Before the project claims a realistic RL accelerator, user or external reference
input is required: algorithm family, observation/action schema, replay sample
schema, batch size, host register/stream packet format, fixed-point policy,
fabric/software split on AC820-ZYNQ, and target clock/resource constraints.

Without those inputs, T12 remains a valid synthetic replay-arbiter shell but
should not be described as application-realistic.

## Self-Review

- No placeholders remain in this document.
- The task is scoped to one deterministic topology and its existing integration
  points.
- The host packetization, replay arbitration, memory readback, sample staging,
  and irq behavior are concrete enough for a TDD implementation plan.
- The design advances complex-project generation beyond T11 while preserving a
  clear boundary before real RL accelerator claims.
