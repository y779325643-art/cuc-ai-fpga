# SR2FPGA T6 TD-Update Core Design

Date: 2026-06-29

## Purpose

T6 is the next component-topology step after T5 toward the reinforcement-learning
accelerator flagship. T5 introduced an RL-shaped inference datapath by computing
a vector-MAC score. T6 should introduce the first explicit RL update datapath:
temporal-difference error and value update.

The implementation target is a new deterministic task:

- `composed_td_update_core`
- topology id: `t6_td_update_core`
- difficulty tier: `T6`

T6 remains a synthetic intermediate task. It should exercise RL update semantics,
multi-input valid-ready coordination, state/control-flow metadata, and wider
fixed-point arithmetic without claiming to be a complete accelerator.

## Current Baseline

The current component-topology ladder is:

- T1 `composed_event_counter`
- T2 `composed_stream_accumulator`
- T3 `composed_stream_fork`
- T4 `composed_dual_stream_join`
- T5 `composed_vector_mac_pipeline`

T5 covers `feature * weight` accumulation and score output. T6 should cover the
other half of a small value-based RL datapath: update a value estimate using a
reward, current value, next value, discount factor, and learning rate.

## Scope

T6 computes a fixed-point integer approximation of:

```text
td_error = reward + ((gamma * next_value) >> SCALE_SHIFT) - value
updated_value = value + ((alpha * td_error) >> SCALE_SHIFT)
```

The generated task should:

- accept one valid-ready bundle containing `reward`, `value`, `next_value`,
  `gamma`, and `alpha`;
- emit one valid-ready bundle containing `td_error` and `updated_value`;
- use signed arithmetic for reward, value, td error, and updated value;
- use unsigned fixed-point scale factors for `gamma` and `alpha`;
- use a fixed `SCALE_SHIFT`, such as 4, in the deterministic template;
- avoid floating point, external memory, replay buffers, AXI, board shell, and
  policy/action selection.

## Architecture

The new topology should use four reusable submodules:

- `td_input_stage`: captures the input update tuple under valid-ready flow
  control.
- `discount_core`: computes `reward + ((gamma * next_value) >> SCALE_SHIFT)`.
- `td_update_core`: computes `td_error` and `updated_value`.
- `stream_stage`: stages the output tuple.

The top-level interface should expose:

- `clk`, `rst_n`
- `in_valid`, `in_ready`
- `reward`, `value`, `next_value`
- `gamma`, `alpha`
- `out_valid`, `out_ready`
- `td_error`, `updated_value`

Suggested widths:

- `reward`, `value`, `next_value`, `td_error`, and `updated_value` use
  `DATA_WIDTH`.
- `gamma` and `alpha` use `DATA_WIDTH`.
- intermediate products use `2*DATA_WIDTH`.

The deterministic implementation can use signed two's-complement arithmetic.
The bounded testbench should choose small positive values to avoid ambiguity
around saturation. Saturation is out of scope for T6.

## Data Flow

Required component edges:

- `top.in_valid` -> `td_input_stage.in_valid`
- `top.reward` -> `td_input_stage.reward`
- `top.value` -> `td_input_stage.value`
- `top.next_value` -> `td_input_stage.next_value`
- `top.gamma` -> `td_input_stage.gamma`
- `top.alpha` -> `td_input_stage.alpha`
- `td_input_stage.out_valid` -> `discount_core.in_valid`
- `td_input_stage.reward_out` -> `discount_core.reward`
- `td_input_stage.next_value_out` -> `discount_core.next_value`
- `td_input_stage.gamma_out` -> `discount_core.gamma`
- `discount_core.out_valid` -> `td_update_core.in_valid`
- `discount_core.discounted_return` -> `td_update_core.discounted_return`
- `td_input_stage.value_out` -> `td_update_core.value`
- `td_input_stage.alpha_out` -> `td_update_core.alpha`
- `td_update_core.out_valid` -> `stream_stage.in_valid`
- `td_update_core.td_error` -> `stream_stage.td_error`
- `td_update_core.updated_value` -> `stream_stage.updated_value`
- `stream_stage.out_valid` -> `top.out_valid`
- `stream_stage.td_error_out` -> `top.td_error`
- `stream_stage.updated_value_out` -> `top.updated_value`
- `top.out_ready` -> `stream_stage.out_ready`

The design should only accept a new update tuple when all downstream stages can
eventually accept it. It is acceptable for the deterministic T6 template to be a
one-sample-at-a-time pipeline with backpressure rather than a fully overlapped
multi-sample pipeline.

## System-HIS Requirements

The generated `system_his.json` should continue using `system-his-v1.2` and the
current aspect layout. T6 must exercise:

- `components`: include `top`, `td_input_stage`, `discount_core`,
  `td_update_core`, and `stream_stage`.
- `instances`: include one instance of each non-top component.
- `interfaces`: include the input tuple, output tuple, clock, and reset ports.
- `data_flow`: describe tuple capture, discount calculation, TD update, and
  output staging.
- `control_flow`: describe valid-ready transfer, one-sample-at-a-time hold, and
  output backpressure.
- `state`: mark captured input registers as owned by `td_input_stage` and output
  registers as owned by `stream_stage`; `td_update_core` may own registered
  `td_error` and `updated_value` if the implementation registers them there.
- `timing`: retain positive `target_fmax_mhz` and include a small latency /
  initiation-interval statement for the TD update path.
- `verification`: state that the bounded testbench checks at least two updates
  and prints `TEST_PASS` only when both `td_error` and `updated_value` match.

## Runner And Prompt Integration

The implementation should extend the current `component_topology` path:

- add the topology to `COMPONENT_TOPOLOGIES`;
- add `composed_td_update_core` to `SUPPORTED_TASK_TYPES`;
- make runner `component_topology` expansion accept `t6_td_update_core`;
- add natural and contract requirement text for T6;
- add REQ->HIS fidelity top-port requirements for T6;
- extend DeepSeek two-stage guidance and multimodule source expectations for T6.

## Testing Strategy

Implementation should use TDD:

1. Add a failing generator test for `composed_td_update_core` that checks task
   type, topology id, submodules, top ports, state ownership, and manifest
   sources.
2. Add a failing runner test showing `component_topology` expansion includes
   `t6_td_update_core`.
3. Add a failing fidelity test that rejects missing T6 reward/value/output ports.
4. Add a failing DeepSeek prompt test that requires the T6 architecture guidance
   and expected RTL files.
5. Implement the minimal generator, runner, fidelity, and prompt changes to pass
   those tests.
6. Run focused tests, then the full `LLM/tests` suite.

The deterministic testbench should verify at least these fixed-point examples
with `SCALE_SHIFT = 4`:

```text
reward=4, value=10, next_value=20, gamma=8, alpha=4
discounted_return = 4 + ((8*20)>>4) = 14
td_error = 14 - 10 = 4
updated_value = 10 + ((4*4)>>4) = 11

reward=2, value=6, next_value=16, gamma=8, alpha=8
discounted_return = 2 + ((8*16)>>4) = 10
td_error = 10 - 6 = 4
updated_value = 6 + ((8*4)>>4) = 8
```

## Non-Goals

T6 is not the full reinforcement-learning accelerator. These are intentionally
deferred:

- action selection or epsilon-greedy branching;
- replay memory, sample batching, or memory arbitration;
- ARM/environment handshake;
- AXI-lite configuration registers;
- board-level shell or OpenXC7/Vivado physical closure;
- floating-point support;
- saturation/rounding policy beyond deterministic truncating right shift.

T7 should introduce the policy/value accelerator shell and configuration
registers. T8 or later should introduce replay/sample batching and board-facing
integration.

## Human Input Needed

T6 does not require a user-provided real reference project. It is a synthetic
task that tests whether the generator can express and implement the arithmetic
shape of a TD update.

Human input becomes important before T7 or the full flagship case. Useful inputs
at that point are:

- RL algorithm family, such as DQN-style value update or actor-critic;
- observation vector width and action count;
- fixed-point scale, signedness, and saturation policy;
- whether FPGA fabric computes only inference/update kernels or also owns replay
  sampling;
- FPGA/ARM boundary on AC820-ZYNQ;
- target clock, DSP budget, BRAM budget, and I/O expectations;
- any Python, HLS, or RTL reference for the intended workload.

Without those inputs, T5 and T6 remain valid synthetic ladder tasks, but the full
RL accelerator should not be described as application-realistic.

## Self-Review

- No placeholders remain in this document.
- The task is scoped to one deterministic topology and its existing integration
  points.
- The formula, widths, and testbench examples are concrete.
- The design advances RL semantics beyond T5 without taking on T7/T8 scope.
