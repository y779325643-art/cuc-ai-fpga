# SR2FPGA T10 RL Accelerator Shell Design

Date: 2026-06-29

Status note (2026-06-30): this file keeps the legacy topology ID/name used by
the implementation (`t10_rl_accelerator_shell`). For public reporting, dataset
splits, and paper-facing discussion, it maps to compressed tier **T4: integrated
host-facing system shells**.

## Purpose

T10 is the next component-topology step after T9 toward the reinforcement-
learning accelerator flagship. T7 introduced a policy/value shell, T8
introduced a replay/sample host-fabric boundary, and T9 introduced a
protocol-shaped host control and stream wrapper. T10 should combine those
axes into one deterministic synthetic accelerator shell.

The implementation target is a new deterministic task:

- `composed_rl_accelerator_shell`
- topology id: `t10_rl_accelerator_shell`
- difficulty tier: `T10`

T10 remains synthetic. Its job is to test whether SR2FPGA can generate a larger
multi-component project that accepts host configuration, consumes a sample-like
observation tuple, computes policy/value/update outputs, emits a result stream,
and reports completion through an interrupt. It is not yet a realistic DQN,
actor-critic, PPO, SAC, AC820-ZYNQ, DMA, or board-level accelerator.

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
- T9 `composed_host_protocol_shell`

T10 should combine the relevant behavior from T7, T8, and T9 without copying
all prior RTL. It should add the next missing complexity axis: a complete
sample-to-result path shaped like a small RL accelerator transaction.

## Scope

T10 should expose a bounded host configuration interface, a sample input
interface, a result stream interface, and an interrupt:

```text
cfg addr 0: weight0
cfg addr 1: bias0
cfg addr 2: weight1
cfg addr 3: bias1
cfg addr 4: alpha
cfg addr 5: enable

sample = obs0, obs1, reward, next_value, done
score0 = obs0 * weight0 + bias0
score1 = obs1 * weight1 + bias1
selected_action = score1 > score0
value_estimate = (score0 + score1) >> 1
td_error = reward + next_value - value_estimate
updated_value = value_estimate + ((alpha * td_error) >> 4)
result stream = selected_action, value_estimate, updated_value, episode_done
irq = result accepted and episode_done
```

The deterministic test values should avoid negative `td_error` so the first
template can stay unsigned and compact. Signed arithmetic, saturation, rounding
policy, and algorithm-specific fixed-point semantics are deferred until a real
workload reference is available.

The generated task should:

- accept configuration writes through `cfg_valid`, `cfg_ready`, `cfg_addr`, and
  `cfg_data`;
- accept one sample transaction through `sample_valid`, `sample_ready`,
  `obs0`, `obs1`, `reward`, `next_value`, and `done_in`;
- compute policy scores, selected action, value estimate, TD error, and updated
  value;
- emit one result transaction through `result_valid`, `result_ready`,
  `selected_action`, `value_estimate`, `updated_value`, and `episode_done`;
- expose `irq`;
- support backpressure on the result stream;
- avoid replay batches, multi-action arrays, real neural-network layers, DMA,
  external DDR, host software, board shell, and real RL algorithm fidelity.

## Architecture

The new topology should use five reusable submodules:

- `host_config_bank`: owns weights, biases, alpha, and enable configuration.
- `sample_capture_stage`: accepts one sample tuple and holds it while the
  result path is busy.
- `policy_value_core`: computes `score0`, `score1`, `selected_action`, and
  `value_estimate`.
- `td_update_core`: computes `td_error` and `updated_value`.
- `result_stream_stage`: owns result-valid backpressure, output registers,
  `episode_done`, and `irq`.

The top-level interface should expose:

- `clk`, `rst_n`
- config write subset: `cfg_valid`, `cfg_ready`, `cfg_addr`, `cfg_data`
- sample input: `sample_valid`, `sample_ready`, `obs0`, `obs1`, `reward`,
  `next_value`, `done_in`
- result output: `result_valid`, `result_ready`, `selected_action`,
  `value_estimate`, `updated_value`, `episode_done`
- interrupt output: `irq`

Suggested widths:

- `DATA_WIDTH` defaults to 8 in tests.
- `cfg_addr` can be 3 bits.
- `selected_action`, `done_in`, `episode_done`, and `irq` are 1 bit.
- Intermediate score/update math may wrap to `DATA_WIDTH` in the first
  deterministic template.

## Data Flow

Required component edges:

- `top.cfg_valid` -> `host_config_bank.cfg_valid`
- `top.cfg_addr` -> `host_config_bank.cfg_addr`
- `top.cfg_data` -> `host_config_bank.cfg_data`
- `host_config_bank.cfg_ready` -> `top.cfg_ready`
- `top.sample_valid` -> `sample_capture_stage.in_valid`
- `sample_capture_stage.in_ready` -> `top.sample_ready`
- `top.obs0` -> `sample_capture_stage.obs0`
- `top.obs1` -> `sample_capture_stage.obs1`
- `top.reward` -> `sample_capture_stage.reward`
- `top.next_value` -> `sample_capture_stage.next_value`
- `top.done_in` -> `sample_capture_stage.done_in`
- `sample_capture_stage.out_valid` -> `policy_value_core.in_valid`
- `host_config_bank.weight0` -> `policy_value_core.weight0`
- `host_config_bank.bias0` -> `policy_value_core.bias0`
- `host_config_bank.weight1` -> `policy_value_core.weight1`
- `host_config_bank.bias1` -> `policy_value_core.bias1`
- `host_config_bank.enable` -> `policy_value_core.enable`
- `policy_value_core.out_valid` -> `td_update_core.in_valid`
- `policy_value_core.value_estimate` -> `td_update_core.value_estimate`
- `sample_capture_stage.reward_out` -> `td_update_core.reward`
- `sample_capture_stage.next_value_out` -> `td_update_core.next_value`
- `host_config_bank.alpha` -> `td_update_core.alpha`
- `td_update_core.out_valid` -> `result_stream_stage.in_valid`
- `policy_value_core.selected_action` -> `result_stream_stage.selected_action`
- `policy_value_core.value_estimate` -> `result_stream_stage.value_estimate`
- `td_update_core.updated_value` -> `result_stream_stage.updated_value`
- `sample_capture_stage.done_out` -> `result_stream_stage.done_in`
- `result_stream_stage.out_ready` -> `sample_capture_stage.consume_ready`
- `result_stream_stage.result_valid` -> `top.result_valid`
- `top.result_ready` -> `result_stream_stage.result_ready`
- `result_stream_stage.selected_action_out` -> `top.selected_action`
- `result_stream_stage.value_estimate_out` -> `top.value_estimate`
- `result_stream_stage.updated_value_out` -> `top.updated_value`
- `result_stream_stage.episode_done_out` -> `top.episode_done`
- `result_stream_stage.irq` -> `top.irq`

The template should accept one sample at a time. While a result is pending and
`result_ready` is low, `sample_ready` should remain low.

## System-HIS Requirements

The generated `system_his.json` should continue using `system-his-v1.2` and the
current aspect layout. T10 must exercise:

- `components`: include `top`, `host_config_bank`, `sample_capture_stage`,
  `policy_value_core`, `td_update_core`, and `result_stream_stage`.
- `instances`: include one instance of each non-top component.
- `interfaces`: include config write, sample input, result stream output,
  interrupt, clock, and reset ports.
- `data_flow`: describe config loading, sample capture, score/value compute,
  TD update compute, result staging, and irq output.
- `control_flow`: describe reset, config writes, enable gating, sample
  valid-ready capture, result backpressure, result acceptance, and irq behavior.
- `state`: mark weights, biases, alpha, and enable as owned by
  `host_config_bank`; sample tuple registers as owned by
  `sample_capture_stage`; result registers and irq as owned by
  `result_stream_stage`.
- `timing`: retain positive `target_fmax_mhz` and include latency /
  initiation-interval metadata for config-to-sample and sample-to-result paths.
- `verification`: state that the bounded testbench configures weights, sends
  two samples, observes two deterministic results, checks irq behavior, and
  prints `TEST_PASS` only when all checks match.

## Runner And Prompt Integration

The implementation should extend the current `component_topology` path:

- add the topology to `COMPONENT_TOPOLOGIES`;
- add `composed_rl_accelerator_shell` to `SUPPORTED_TASK_TYPES`;
- make runner `component_topology` expansion accept `t10_rl_accelerator_shell`;
- add natural and contract requirement text for T10;
- add REQ->HIS fidelity top-port requirements for T10;
- extend DeepSeek two-stage guidance and multimodule source expectations for
  T10.

## Testing Strategy

Implementation should use TDD:

1. Add a failing generator test for `composed_rl_accelerator_shell` that checks
   task type, topology id, submodules, RL-shaped top ports, state ownership,
   manifest sources, deterministic simulation coverage, and expected result
   checks.
2. Add the T10 case to supported-task manifest coverage and Icarus multimodule
   simulation coverage.
3. Add a failing runner test showing `component_topology` expansion includes
   `t10_rl_accelerator_shell`.
4. Add a failing fidelity test that rejects missing T10 config, sample, result,
   and irq ports.
5. Add a failing DeepSeek prompt test that requires the T10 architecture
   guidance and expected RTL files.
6. Implement the minimal generator, runner, fidelity, and prompt changes to
   pass those tests.
7. Run focused tests, then the full `LLM/tests` suite, `compileall`, and
   `git diff --check`.

The deterministic testbench should:

```text
write cfg weight0=2, bias0=1, weight1=3, bias1=0, alpha=4, enable=1
sample 1: obs0=4, obs1=2, reward=1, next_value=8, done=0
expect selected_action=0, value_estimate=7, updated_value=7, episode_done=0
sample 2: obs0=1, obs1=5, reward=2, next_value=15, done=1
expect selected_action=1, value_estimate=9, updated_value=11, episode_done=1
expect irq=1 after the second result is accepted
```

## Non-Goals

T10 is not the final realistic reinforcement-learning accelerator. These are
intentionally deferred:

- real DQN, actor-critic, PPO, SAC, or policy-gradient workload fidelity;
- replay memory batches or stochastic sampling;
- neural-network layers beyond a two-score deterministic policy/value shell;
- signed fixed-point calibration, saturation, rounding, and overflow policy;
- AXI4-Lite, AXI-stream packet framing, DMA, external DDR, cache coherency, or
  ARM software drivers;
- board-level shell, OpenXC7/Vivado physical closure, or AC820 pin constraints;
- measured QoR on a real target device.

## Human Input Needed

T10 can still be implemented synthetically without user-provided reference
material. It improves complex-project generation coverage by combining the
policy/value, sample/update, host/config, result/backpressure, and irq pieces.

Before the project claims a realistic RL accelerator, user or external reference
input becomes required. The minimum reference package should include:

- RL algorithm family, such as DQN, actor-critic, PPO, SAC, or inference-only
  policy evaluation;
- observation vector length, action count, batch size, and data schema;
- fixed-point width, signedness, scale, rounding, and saturation policy;
- replay sample schema, if replay/sample logic remains in fabric;
- host register map, command lifecycle, stream packet format, and interrupt
  semantics;
- whether FPGA fabric owns inference only, update only, replay/sample logic, or
  all three;
- target board/toolchain constraints, including AC820-ZYNQ boundary, clock,
  DSP, BRAM, and I/O expectations;
- any Python, HLS, RTL, or paper reference for the intended workload.

Without those inputs, T10 remains a valid synthetic integrated shell but should
not be described as application-realistic.

## Self-Review

- No placeholders remain in this document.
- The task is scoped to one deterministic topology and its existing integration
  points.
- The config, sample, compute, result, and irq behavior is concrete enough for a
  TDD implementation plan.
- The design advances complex-project generation beyond T9 while preserving a
  clear boundary before real RL accelerator claims.
