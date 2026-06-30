# SR2FPGA T11 Batch RL Accelerator Shell Design

Date: 2026-06-29

## Purpose

T11 is the next component-topology step after T10 toward the reinforcement-
learning accelerator flagship. T10 combined host config, sample capture,
policy/value scoring, TD update, result streaming, and irq reporting for one
sample at a time. T11 should add the next synthetic complexity axis: a
two-sample batch datapath with lane-level policy/value/update outputs.

The implementation target is a new deterministic task:

- `composed_batch_rl_accelerator_shell`
- topology id: `t11_batch_rl_accelerator_shell`
- difficulty tier: `T11`

T11 remains synthetic. Its job is to test whether SR2FPGA can generate and
verify a wider multi-lane accelerator shell with shared configuration, batched
sample capture, per-lane policy/value/update compute, vectorized result output,
and irq reporting. It is not yet a realistic DQN, actor-critic, PPO, SAC, DMA,
AC820-ZYNQ, or board-level accelerator.

## Current Baseline

The component-topology ladder is now:

- T7 `composed_policy_value_shell`
- T8 `composed_replay_sample_shell`
- T9 `composed_host_protocol_shell`
- T10 `composed_rl_accelerator_shell`

T11 should extend T10 instead of replacing it. T10 proves a one-sample
sample-to-result path. T11 should prove that the generator can express a small
batch with duplicated lane datapaths and deterministic result packing.

## Scope

T11 should expose shared host configuration, a two-lane batch input, a
two-lane result output, and an interrupt:

```text
cfg addr 0: weight0
cfg addr 1: bias0
cfg addr 2: weight1
cfg addr 3: bias1
cfg addr 4: alpha
cfg addr 5: enable

lane A sample = obs0_a, obs1_a, reward_a, next_value_a, done_a
lane B sample = obs0_b, obs1_b, reward_b, next_value_b, done_b

score0_x = obs0_x * weight0 + bias0
score1_x = obs1_x * weight1 + bias1
selected_action_x = score1_x > score0_x
value_estimate_x = (score0_x + score1_x) >> 1
td_error_x = reward_x + next_value_x - value_estimate_x
updated_value_x = value_estimate_x + ((alpha * td_error_x) >> 4)
batch_done = done_a | done_b
irq = result accepted and batch_done
```

The generated task should:

- accept configuration writes through `cfg_valid`, `cfg_ready`, `cfg_addr`, and
  `cfg_data`;
- accept a two-lane batch through `batch_valid`, `batch_ready`, lane A sample
  ports, and lane B sample ports;
- compute lane A and lane B selected actions, value estimates, and updated
  values;
- emit one result transaction through `result_valid`, `result_ready`, lane A
  result ports, lane B result ports, `batch_done`, and `irq`;
- support backpressure on the result stream;
- keep the arithmetic deterministic and unsigned for the first template;
- avoid stochastic replay sampling, real neural-network layers, true batch
  memory arbitration, DMA, host software, board shell, and real RL algorithm
  fidelity.

## Architecture

The new topology should use five reusable submodules:

- `batch_config_bank`: owns shared weights, biases, alpha, and enable.
- `batch_sample_buffer`: captures both sample lanes and holds them while the
  result path is busy.
- `dual_policy_value_core`: computes selected action and value estimate for
  both lanes using shared config.
- `dual_td_update_core`: computes updated value for both lanes.
- `batch_result_stage`: owns result-valid backpressure, lane result registers,
  `batch_done`, and `irq`.

The top-level interface should expose:

- `clk`, `rst_n`
- config write subset: `cfg_valid`, `cfg_ready`, `cfg_addr`, `cfg_data`
- batch input: `batch_valid`, `batch_ready`, `obs0_a`, `obs1_a`, `reward_a`,
  `next_value_a`, `done_a`, `obs0_b`, `obs1_b`, `reward_b`, `next_value_b`,
  `done_b`
- result output: `result_valid`, `result_ready`, `selected_action_a`,
  `value_estimate_a`, `updated_value_a`, `selected_action_b`,
  `value_estimate_b`, `updated_value_b`, `batch_done`
- interrupt output: `irq`

## Data Flow

Required component edges:

- `top.cfg_valid` -> `batch_config_bank.cfg_valid`
- `top.cfg_addr` -> `batch_config_bank.cfg_addr`
- `top.cfg_data` -> `batch_config_bank.cfg_data`
- `batch_config_bank.cfg_ready` -> `top.cfg_ready`
- `top.batch_valid` -> `batch_sample_buffer.in_valid`
- `batch_sample_buffer.in_ready` -> `top.batch_ready`
- lane A and lane B sample top ports -> `batch_sample_buffer`
- `batch_sample_buffer.out_valid` -> `dual_policy_value_core.in_valid`
- `batch_config_bank` weights, biases, and enable -> `dual_policy_value_core`
- `dual_policy_value_core.out_valid` -> `dual_td_update_core.in_valid`
- lane rewards and next values -> `dual_td_update_core`
- `batch_config_bank.alpha` -> `dual_td_update_core.alpha`
- `dual_td_update_core.out_valid` -> `batch_result_stage.in_valid`
- lane selected actions and values -> `batch_result_stage`
- lane updated values -> `batch_result_stage`
- lane done flags -> `batch_result_stage`
- `batch_result_stage.out_ready` -> `batch_sample_buffer.consume_ready`
- `batch_result_stage` result ports -> top result ports
- `batch_result_stage.irq` -> `top.irq`

The template should accept one two-lane batch at a time. While a result is
pending and `result_ready` is low, `batch_ready` should remain low.

## System-HIS Requirements

The generated `system_his.json` should continue using `system-his-v1.2` and the
current aspect layout. T11 must exercise:

- `components`: include `top`, `batch_config_bank`, `batch_sample_buffer`,
  `dual_policy_value_core`, `dual_td_update_core`, and `batch_result_stage`.
- `instances`: include one instance of each non-top component.
- `interfaces`: include config write, two-lane batch input, two-lane result
  output, interrupt, clock, and reset ports.
- `data_flow`: describe config loading, batch capture, dual-lane score/value
  compute, dual-lane TD update, result staging, and irq output.
- `control_flow`: describe reset, config writes, enable gating, batch
  valid-ready capture, result backpressure, result acceptance, and irq behavior.
- `state`: mark shared config registers as owned by `batch_config_bank`; lane
  sample tuple registers as owned by `batch_sample_buffer`; lane result
  registers and irq as owned by `batch_result_stage`.
- `verification`: state that the bounded testbench configures weights, sends
  one two-lane batch, observes deterministic lane results, checks irq behavior,
  and prints `TEST_PASS` only when all checks match.

## Testing Strategy

Implementation should use TDD:

1. Add a failing generator test for `composed_batch_rl_accelerator_shell` that
   checks topology id, submodules, batch-shaped top ports, state ownership,
   manifest sources, and deterministic testbench checks.
2. Add the T11 case to supported-task manifest coverage and Icarus multimodule
   simulation coverage.
3. Add a failing runner test showing `component_topology` expansion includes
   `t11_batch_rl_accelerator_shell`.
4. Add a failing fidelity test that rejects missing T11 config, batch, lane
   result, and irq ports.
5. Add a failing DeepSeek prompt test that requires T11 architecture guidance
   and expected RTL files.
6. Implement the minimal generator, runner, fidelity, and prompt changes.
7. Run focused tests, full `LLM/tests`, `compileall`, and `git diff --check`.

The deterministic testbench should:

```text
write cfg weight0=2, bias0=1, weight1=3, bias1=0, alpha=4, enable=1
batch lane A: obs0=4, obs1=2, reward=1, next_value=8, done=0
expect lane A: selected_action=0, value_estimate=7, updated_value=7
batch lane B: obs0=1, obs1=5, reward=2, next_value=15, done=1
expect lane B: selected_action=1, value_estimate=9, updated_value=11
expect batch_done=1 and irq=1 after result acceptance
```

## Non-Goals

T11 is not the final realistic reinforcement-learning accelerator. These are
intentionally deferred:

- real DQN, actor-critic, PPO, SAC, or policy-gradient workload fidelity;
- stochastic replay sampling or true replay memory arbitration;
- batch sizes beyond two lanes;
- neural-network layers beyond deterministic two-score lane logic;
- signed fixed-point calibration, saturation, rounding, and overflow policy;
- AXI4-Lite, AXI-stream packet framing, DMA, external DDR, ARM software, or
  board shell;
- measured QoR on a real target device.

## Human Input Needed

T11 can still be implemented synthetically without user-provided reference
material. It improves complex-project generation coverage by adding shared
config, duplicated lane compute, wider batch ports, and vectorized result
staging.

Before the project claims a realistic RL accelerator, user or external reference
input is required. The minimum reference package remains:

- RL algorithm family;
- observation vector length, action count, batch size, and data schema;
- fixed-point width, signedness, scale, rounding, and saturation policy;
- replay sample schema and host register/stream packet format;
- fabric/software split on AC820-ZYNQ;
- clock, DSP, BRAM, and I/O expectations;
- Python, HLS, RTL, or paper reference for the intended workload.

Without those inputs, T11 remains a valid synthetic batch shell but should not
be described as application-realistic.

## Self-Review

- No placeholders remain in this document.
- The task is scoped to one deterministic topology and its existing integration
  points.
- The batch input, dual-lane compute, result staging, and irq behavior are
  concrete enough for a TDD implementation plan.
- The design advances complex-project generation beyond T10 while preserving a
  clear boundary before real RL accelerator claims.
