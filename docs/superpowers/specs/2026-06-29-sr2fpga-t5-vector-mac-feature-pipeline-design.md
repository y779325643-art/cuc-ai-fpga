# SR2FPGA T5 Vector MAC Feature Pipeline Design

Date: 2026-06-29

Status note (2026-06-30): this file keeps the legacy topology ID/name used by
the implementation (`t5_vector_mac_pipeline`). For public reporting, dataset
splits, and paper-facing discussion, it maps to compressed tier **T3: datapath
and memory shells**.

## Purpose

T5 is the first explicit bridge from the existing T1-T4 component-topology ladder
toward the reinforcement-learning accelerator flagship. It should add a
deterministic, multi-component streaming datapath that resembles the feature
extraction / Q-value inference core of an RL accelerator without taking on replay
memory, ARM/environment handshakes, epsilon-greedy control, or full Bellman-update
logic yet.

The implementation target is a new task type:

- `composed_vector_mac_pipeline`
- topology id: `t5_vector_mac_pipeline`
- difficulty tier: `T5`

## Current Baseline

The current codebase already supports a compositional ladder through
`component_topology`:

- T1 `composed_event_counter`: event gate plus counter core.
- T2 `composed_stream_accumulator`: skid buffer plus accumulator core.
- T3 `composed_stream_fork`: skid buffer, stream fork, and stream stages.
- T4 `composed_dual_stream_join`: two skid buffers, stream join, accumulator, and
  stream stage.

The System-HIS v1.2 freeze document names an RL accelerator as the forward-compat
stress case. It identifies two needs that T5 should start exercising: streaming
MAC datapaths via `data_flow.timing`, and later control-heavy RL loops via
`control_flow`.

## Scope

T5 should be a deterministic SR2FPGA task that accepts a stream of feature values
and a matching stream of weights, performs a bounded vector dot-product, adds an
optional bias, and emits one valid-ready score stream.

The task must remain small enough for the current deterministic generator and
testbench style:

- parameterized by `DATA_WIDTH` from the existing request width;
- fixed vector length in the generated template, represented as a parameter such
  as `VECTOR_LEN`;
- no external memory interface;
- no AXI or board shell;
- no floating point;
- no RL policy-selection branch;
- no replay buffer.

## Architecture

The new topology should use four reusable submodules:

- `skid_buffer`: existing valid-ready input buffering for the feature stream.
- `skid_buffer`: a second instance for the weight stream.
- `vector_mac_core`: new stateful core that consumes paired feature/weight
  samples and accumulates `feature * weight` over `VECTOR_LEN` beats.
- `stream_stage`: existing output staging for the completed score.

The top-level interface should expose:

- `clk`, `rst_n`
- `feature_valid`, `feature_data`, `feature_ready`
- `weight_valid`, `weight_data`, `weight_ready`
- `bias`
- `score_valid`, `score_data`, `score_ready`

`score_data` should be wider than the inputs. The deterministic template should
make this explicit with an expression such as `2*DATA_WIDTH`, matching the
recent width-equivalence hardening work.

## Data Flow

Required component edges:

- `top.feature_valid` -> `skid_buffer.feature.in_valid`
- `top.feature_data` -> `skid_buffer.feature.in_data`
- `top.weight_valid` -> `skid_buffer.weight.in_valid`
- `top.weight_data` -> `skid_buffer.weight.in_data`
- `skid_buffer.feature.out_valid` -> `vector_mac_core.feature_valid`
- `skid_buffer.feature.out_data` -> `vector_mac_core.feature_data`
- `skid_buffer.weight.out_valid` -> `vector_mac_core.weight_valid`
- `skid_buffer.weight.out_data` -> `vector_mac_core.weight_data`
- `vector_mac_core.feature_ready` -> `skid_buffer.feature.out_ready`
- `vector_mac_core.weight_ready` -> `skid_buffer.weight.out_ready`
- `top.bias` -> `vector_mac_core.bias`
- `vector_mac_core.score_valid` -> `stream_stage.in_valid`
- `vector_mac_core.score_data` -> `stream_stage.in_data`
- `stream_stage.in_ready` -> `vector_mac_core.score_ready`
- `stream_stage.out_valid` -> `top.score_valid`
- `stream_stage.out_data` -> `top.score_data`
- `top.score_ready` -> `stream_stage.out_ready`

The core should only accept a pair when both feature and weight streams are valid
and it can accept the beat. After `VECTOR_LEN` accepted pairs, it should emit
`bias + sum(feature_i * weight_i)` once, then reset the accumulation state for the
next vector.

## System-HIS Requirements

The generated `system_his.json` should continue using `system-his-v1.2` and the
current aspect layout. T5 must exercise these fields:

- `components`: include `top`, `skid_buffer`, `vector_mac_core`, and
  `stream_stage`.
- `instances`: include two skid-buffer instances, one vector-MAC instance, and
  one output-stage instance.
- `interfaces`: include feature, weight, bias, score, clock, and reset ports.
- `data_flow`: describe paired feature/weight movement into the MAC core and the
  score output path.
- `control_flow`: describe the bounded accumulation counter and the transition
  from accumulate to output-valid.
- `state`: mark vector index, accumulator, and pending-score state as owned by
  `vector_mac_core`.
- `timing`: retain a positive `target_fmax_mhz` and include a simple latency /
  initiation-interval statement for the MAC core.
- `verification`: state that the bounded testbench checks at least two vectors
  and prints `TEST_PASS` only when both scores match.

## Runner And Prompt Integration

The implementation should extend the existing path rather than add a new runner
mode:

- add the topology to `COMPONENT_TOPOLOGIES`;
- add `composed_vector_mac_pipeline` to `SUPPORTED_TASK_TYPES`;
- make runner `component_topology` expansion accept `t5_vector_mac_pipeline`;
- add natural and contract requirement text for T5;
- add REQ->HIS fidelity top-port requirements for T5;
- extend DeepSeek two-stage guidance and multimodule source expectations for T5.

## Testing Strategy

Implementation should use TDD:

1. Add a failing generator test that requests
   `composed_vector_mac_pipeline` and checks task type, topology id, submodules,
   top ports, state ownership, and manifest sources.
2. Add a failing runner test showing `component_topology` expansion includes
   `t5_vector_mac_pipeline`.
3. Add a failing fidelity test that rejects missing T5 feature/weight/score
   ports.
4. Add a failing DeepSeek prompt test that requires the T5 architecture guidance
   and expected RTL files.
5. Implement the minimal generator, runner, fidelity, and prompt changes to pass
   those tests.
6. Run the focused unit tests, then the full `LLM/tests` suite.

If local Verilog tooling is available, the deterministic T5 testbench should also
be compile/run checked through the existing project-generator simulation tests.

## Non-Goals

T5 is not the full reinforcement-learning accelerator. These are intentionally
deferred to later topologies:

- T6: TD-error / value-update core.
- T7: policy/value accelerator shell with configuration registers.
- T8 or later: replay/sample batching, ARM/environment handshake, board-oriented
  shell, and open-flow timing/resource evaluation.

## Human Input Needed

T5 does not require a real reference project. It is a synthetic but RL-shaped
intermediate task whose job is to harden the current generation pipeline around a
vector-MAC datapath.

Human-provided reference material becomes important before T7 or the full RL
accelerator case. At that point, the useful inputs are:

- a real or target RL workload shape, such as DQN-style Q-value inference,
  policy-gradient inference, or value-function update;
- expected observation vector width, action count, batch size, numeric format,
  and whether fixed-point scaling is required;
- the intended boundary between FPGA fabric and ARM/software on the AC820-ZYNQ;
- any existing RTL/HLS/Python reference, even if incomplete;
- target board constraints, clock target, DSP budget, BRAM budget, and I/O
  expectations.

If no real reference is available, the already approved legacy t5-t12 bridge
tasks map into compressed T3/T4 reporting tiers, but that ladder is supplemental
complexity evidence rather than the paper's primary official aggregate. After
compressed T4, do not add a new synthetic tier by default; a new step needs an
approved design and should preferably be grounded in a real workload reference.
The full flagship case should not claim application realism until at least the
workload shape and fabric/software boundary are grounded in user-provided or
cited reference material.

## Self-Review

- No placeholders remain in this document.
- The task is scoped to one new deterministic component topology and its existing
  integration points.
- The design follows the current T1-T4 component-topology pattern.
- The RL accelerator path is explicit but not overclaimed as complete.
