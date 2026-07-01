# SR2FPGA T7 Policy/Value Shell Design

Date: 2026-06-29

Status note (2026-06-30): this file keeps the legacy topology ID/name used by
the implementation (`t7_policy_value_shell`). For public reporting, dataset
splits, and paper-facing discussion, it maps to compressed tier **T3: datapath
and memory shells**.

## Purpose

T7 is the next component-topology step after T5 and T6 toward the
reinforcement-learning accelerator flagship. T5 added an RL-shaped inference
datapath through a vector-MAC feature pipeline. T6 added a temporal-difference
update datapath. T7 should introduce the first accelerator-shaped shell: a small
policy/value datapath with configuration registers, score comparison, action
selection, and valid-ready boundaries.

The implementation target is a new deterministic task:

- `composed_policy_value_shell`
- topology id: `t7_policy_value_shell`
- difficulty tier: `T7`

T7 remains synthetic. Its job is to test whether SR2FPGA can generate a larger
multi-component project with configuration/control boundaries that resemble an
RL accelerator shell. It is not yet the full AC820-ZYNQ RL accelerator.

## Current Baseline

The component-topology ladder is now:

- T1 `composed_event_counter`
- T2 `composed_stream_accumulator`
- T3 `composed_stream_fork`
- T4 `composed_dual_stream_join`
- T5 `composed_vector_mac_pipeline`
- T6 `composed_td_update_core`

T7 should combine the shape of inference and update without literally composing
the full T5/T6 RTL. The deterministic template should stay small enough for
unit-test and simulation coverage while adding the next architectural concepts:
configuration, action selection, and fabric/software boundary signals.

## Scope

T7 should accept a compact observation/value input tuple and produce a selected
action plus value estimate:

```text
policy_score_0 = obs0 * weight0 + bias0
policy_score_1 = obs1 * weight1 + bias1
selected_action = policy_score_1 > policy_score_0
value_estimate = (policy_score_0 + policy_score_1) >> 1
```

The task should also expose simple configuration writes for weights, biases, and
an enable bit. This is intentionally a tiny shell, not a full neural network.

The generated task should:

- accept `obs0`, `obs1`, and `obs_valid` under valid-ready flow control;
- expose a small configuration interface for `cfg_valid`, `cfg_addr`,
  `cfg_data`, and `cfg_ready`;
- store two weights, two biases, and an enable bit;
- compute two policy scores and one value estimate;
- emit `action_valid`, `action_ready`, `selected_action`, and `value_estimate`;
- use fixed-width integer arithmetic;
- avoid replay memory, AXI, ARM software, board shell, floating point, and
  multi-layer policy networks.

## Architecture

The new topology should use five reusable submodules:

- `config_reg_bank`: accepts simple configuration writes and owns weights,
  biases, and enable state.
- `observation_stage`: captures the two-observation input tuple.
- `policy_score_core`: computes two scores from observations and configured
  weights/biases.
- `action_select_core`: compares scores and computes `selected_action` plus
  `value_estimate`.
- `stream_stage`: stages the output action/value tuple.

The top-level interface should expose:

- `clk`, `rst_n`
- config input: `cfg_valid`, `cfg_addr`, `cfg_data`, `cfg_ready`
- observation input: `obs_valid`, `obs_ready`, `obs0`, `obs1`
- output: `action_valid`, `action_ready`, `selected_action`, `value_estimate`

Suggested widths:

- `obs0`, `obs1`, `cfg_data`, weights, biases, policy scores, and value estimate
  use `DATA_WIDTH`.
- `cfg_addr` can be 3 bits.
- `selected_action` is 1 bit.
- intermediate products may use `2*DATA_WIDTH` internally, truncated back to
  `DATA_WIDTH` for the deterministic template.

## Data Flow

Required component edges:

- `top.cfg_valid` -> `config_reg_bank.cfg_valid`
- `top.cfg_addr` -> `config_reg_bank.cfg_addr`
- `top.cfg_data` -> `config_reg_bank.cfg_data`
- `config_reg_bank.cfg_ready` -> `top.cfg_ready`
- `top.obs_valid` -> `observation_stage.in_valid`
- `top.obs0` -> `observation_stage.obs0`
- `top.obs1` -> `observation_stage.obs1`
- `observation_stage.in_ready` -> `top.obs_ready`
- `observation_stage.out_valid` -> `policy_score_core.in_valid`
- `observation_stage.obs0_out` -> `policy_score_core.obs0`
- `observation_stage.obs1_out` -> `policy_score_core.obs1`
- `config_reg_bank.weight0` -> `policy_score_core.weight0`
- `config_reg_bank.weight1` -> `policy_score_core.weight1`
- `config_reg_bank.bias0` -> `policy_score_core.bias0`
- `config_reg_bank.bias1` -> `policy_score_core.bias1`
- `config_reg_bank.enable` -> `policy_score_core.enable`
- `policy_score_core.out_valid` -> `action_select_core.in_valid`
- `policy_score_core.score0` -> `action_select_core.score0`
- `policy_score_core.score1` -> `action_select_core.score1`
- `action_select_core.out_valid` -> `stream_stage.in_valid`
- `action_select_core.selected_action` -> `stream_stage.selected_action`
- `action_select_core.value_estimate` -> `stream_stage.value_estimate`
- `stream_stage.out_valid` -> `top.action_valid`
- `top.action_ready` -> `stream_stage.out_ready`
- `stream_stage.selected_action_out` -> `top.selected_action`
- `stream_stage.value_estimate_out` -> `top.value_estimate`

The deterministic template may be one-observation-at-a-time. It does not need to
support simultaneous config writes and observation transfers in the same cycle.

## System-HIS Requirements

The generated `system_his.json` should continue using `system-his-v1.2` and the
current aspect layout. T7 must exercise:

- `components`: include `top`, `config_reg_bank`, `observation_stage`,
  `policy_score_core`, `action_select_core`, and `stream_stage`.
- `instances`: include one instance of each non-top component.
- `interfaces`: include config, observation, action/value output, clock, and
  reset ports.
- `data_flow`: describe configuration movement, observation capture, score
  computation, action selection, and output staging.
- `control_flow`: describe config writes, enable gating, valid-ready transfer,
  and output backpressure.
- `state`: mark weights, biases, and enable as owned by `config_reg_bank`;
  captured observation registers as owned by `observation_stage`; output
  registers as owned by `stream_stage`.
- `timing`: retain positive `target_fmax_mhz` and include latency /
  initiation-interval metadata for the score/select path.
- `verification`: state that the bounded testbench configures weights/biases,
  sends at least two observations, checks selected action and value estimate, and
  prints `TEST_PASS` only when all checks match.

## Runner And Prompt Integration

The implementation should extend the current `component_topology` path:

- add the topology to `COMPONENT_TOPOLOGIES`;
- add `composed_policy_value_shell` to `SUPPORTED_TASK_TYPES`;
- make runner `component_topology` expansion accept `t7_policy_value_shell`;
- add natural and contract requirement text for T7;
- add REQ->HIS fidelity top-port requirements for T7;
- extend DeepSeek two-stage guidance and multimodule source expectations for T7.

## Testing Strategy

Implementation should use TDD:

1. Add a failing generator test for `composed_policy_value_shell` that checks
   task type, topology id, submodules, top ports, state ownership, and manifest
   sources.
2. Add a failing runner test showing `component_topology` expansion includes
   `t7_policy_value_shell`.
3. Add a failing fidelity test that rejects missing T7 config/observation/action
   ports.
4. Add a failing DeepSeek prompt test that requires the T7 architecture guidance
   and expected RTL files.
5. Implement the minimal generator, runner, fidelity, and prompt changes to pass
   those tests.
6. Run focused tests, then the full `LLM/tests` suite.

The deterministic testbench should configure at least two weights and two biases
and verify at least two observations. Example:

```text
weight0=2, bias0=1, weight1=3, bias1=0
obs0=4, obs1=2
score0=9, score1=6, selected_action=0, value_estimate=7

obs0=1, obs1=5
score0=3, score1=15, selected_action=1, value_estimate=9
```

## Non-Goals

T7 is not the full reinforcement-learning accelerator. These are intentionally
deferred:

- real DQN, actor-critic, or policy-gradient workload fidelity;
- observation vectors wider than the deterministic two-element shell;
- replay memory, sample batching, or memory arbitration;
- ARM/environment handshake;
- AXI-lite or AXI-stream protocol-complete interfaces;
- board-level shell or OpenXC7/Vivado physical closure;
- floating-point support;
- multi-layer neural-network inference.

T8 or later should introduce replay/sample batching, host/fabric boundary
details, and board-facing integration.

## Human Input Needed

T7 can still be implemented synthetically without user-provided reference
material. It will improve complex-project generation coverage by adding config
state, score comparison, action selection, and a clearer shell boundary.

Before the project claims a realistic RL accelerator, user or external reference
input becomes required. The minimum reference package should include:

- RL algorithm family, such as DQN, actor-critic, or policy-gradient inference;
- observation vector length and element format;
- action count and action-selection rule;
- fixed-point scale, signedness, rounding, and saturation policy;
- whether FPGA fabric owns inference only, update only, or replay/sample logic;
- FPGA/ARM boundary on AC820-ZYNQ;
- clock target, DSP budget, BRAM budget, and I/O expectations;
- any Python, HLS, RTL, or paper reference for the intended workload.

Without those inputs, T7 remains a valid synthetic shell but should not be
described as application-realistic.

## Self-Review

- No placeholders remain in this document.
- The task is scoped to one deterministic topology and its existing integration
  points.
- The config/register, observation, score, action, and output behaviors are
  concrete enough for a TDD implementation plan.
- The design advances accelerator-shell complexity beyond T5/T6 without taking
  on full RL accelerator scope.
