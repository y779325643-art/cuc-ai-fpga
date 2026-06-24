# SR2FPGA Failure Repair Research Issue Log - 2026-06-24

This note records research-significant issues discovered while building and
running the SR2FPGA natural LLM failure and repair pipeline. It is not a bug
tracker. The goal is to preserve observations that may become paper motivation,
benchmark design choices, ablations, or threats to validity.

## Context

The current research framing is:

```text
requirement
-> System-HIS
-> multi-file RTL project package
-> tool labels L0-L5
-> diagnosis / patch trajectory
-> trainable JSONL views
```

The most relevant recent runs are:

- `deepseek-baseline-a`: first-attempt, no tool repair, T1-T4.
- `deepseek-baseline-b`: first tool-loop repair run, T1-T4.
- `deepseek-baseline-b-smoke`: tightened repair prompt, T1/T2.
- `deepseek-baseline-b-tightened`: tightened repair prompt, T1-T4.
- `deepseek-baseline-b-t3-t4-smoke`: narrow repair-knee run, T3/T4.

The current important empirical pattern is:

- First-attempt DeepSeek project generation naturally fails at L0 on all T1-T4.
- Early tool-loop repair also stays at L0 when the repair prompt does not encode
  the project contract precisely enough.
- With a tighter repair prompt, T1/T2 repair to L3, but T3/T4 remain difficult.
- T3/T4 expose the transition from project-package errors to RTL compile and
  simulation-semantic errors.

## Issue 1: Project-package failure is a first-class failure mode

**Observation.** DeepSeek often emits some plausible RTL files but fails the
complete project artifact contract: incomplete or non-v1.1 `system_his.json`,
manifest drift, missing timing constraints, missing verification fields,
misaligned QoR records, or inconsistent source lists.

**Why it matters academically.** Most RTL-LLM work treats "generated Verilog" as
the artifact. SR2FPGA's unit is a verifiable project package. This makes L0
contract validity a meaningful research object rather than pre-processing
noise. A model that can write a single RTL module but cannot produce the files,
metadata, testbench, constraints, and project manifest needed by an FPGA tool
flow has not solved system-level RTL generation.

**Evidence so far.**

- `deepseek-baseline-a`: 4/4 samples ended at L0 with
  `artifact_contract_failure`.
- `deepseek-baseline-b`: 4/4 samples still ended at L0 before prompt tightening.
- `cross_file_consistency_error_rate = 1.0` in both early runs.

**Research use.**

- Motivation: project-level generation is not simply "more lines of code".
- Benchmark: L0 should remain a real label, not an ignored formatting failure.
- Training: `failure_to_diagnosis` and `failure_to_patch` should include
  artifact-repair targets.

## Issue 2: Natural LLM errors are broader than RTL syntax errors

**Observation.** The user's revised direction is correct: the useful natural
failure distribution is not limited to "RTL naturally contains a bug". It also
includes errors in generated project files, interface contracts, manifests,
constraints, reports, and intermediate representations.

**Why it matters academically.** A project-generation model must satisfy several
coupled contracts: natural-language requirement, System-HIS, RTL module
boundaries, testbench behavior, timing constraints, manifest, and tool logs. The
failure space is therefore multi-artifact and multi-level. This is closer to a
real hardware engineering workflow than single-file code generation.

**Evidence so far.**

- Baseline (a) produced natural L0 failures even on simple T1/T2 topologies.
- Tightened baseline (b) repaired T1/T2 to L3, showing these failures are
  repairable and trainable rather than meaningless noise.
- T3/T4 then exposed deeper RTL failures after some project-package errors were
  fixed.

**Research use.**

- Failure taxonomy should include artifact, RTL compile, RTL simulation,
  synthesis, timing, and board-level families.
- Main data collection should use natural LLM/project failures; synthetic
  injection should stay as controlled ablation and pipeline testing.

## Issue 3: The L0 checker is both an oracle and a moving specification

**Observation.** Several residual failures were caused by checker-level
contract details: exact module roles, `clock` versus `clock_domain`, matching
`parameters` and `params`, allowed connection protocols, non-negative QoR
integers, required verification fields, and exact width strings.

**Why it matters academically.** If the tool oracle defines the label, then the
oracle specification must be explicit, stable, and defensible. Otherwise the
dataset risks measuring conformance to a private checker instead of real
project correctness.

**Evidence so far.**

- Repair quality improved sharply when the prompt enumerated L0 checker
  requirements.
- Numeric width normalization was added after T3 failed on notation differences
  such as `[7:0]` versus `8`.
- Parameterized widths such as `[DATA_WIDTH-1:0]` still require stricter
  treatment because they preserve design intent.

**Research use.**

- Include the L0 contract as a public benchmark spec.
- Separate semantic errors from representational equivalence errors.
- Report checker normalizations as part of the reproducibility story.

## Issue 4: Prompt tightening can become hidden benchmark leakage

**Observation.** Repair prompt changes moved the model from repeated L0 failure
to T1/T2 L3 success. This is good engineering, but it also shows that prompt
specificity strongly changes measured repair performance.

**Why it matters academically.** A repair loop can appear to improve because the
human prompt increasingly encodes the evaluator. This creates a possible
confound between model repair ability and prompt-engineered compliance with the
checker.

**Evidence so far.**

- Early baseline (b): T1-T4 remained L0.
- Tightened T1/T2 smoke: both reached L3.
- Full tightened baseline: T1/T2 reached L3, T3/T4 did not.

**Research use.**

- Freeze prompts before benchmark-scale runs.
- Version prompts and include prompt hash/config fingerprints in run metadata.
- Add a deterministic L0 schema-normalizer baseline to compare against LLM
  repair.
- Evaluate on held-out topology variants not used during prompt iteration.

## Issue 5: L0 can mask deeper RTL failures

**Observation.** When a project fails L0, the normal pipeline may never reach
lint, simulation, synthesis, or timing, even if RTL files exist and could expose
additional failures.

**Why it matters academically.** A single final pass level is useful for
benchmark scoring but insufficient for understanding natural project failures.
A generated package may have both artifact-contract errors and RTL semantic
errors. Training only on the first blocking label may hide useful supervision.

**Evidence so far.**

- Manual side evaluation found deeper signals inside generated projects:
  T1 compiles and prints `TEST_PASS`; T2 compiles but reports `TEST_FAIL`;
  T3 compiles but reports many data mismatches and `TEST_FAIL`; T4 has a Verilog
  compile failure in `stream_stage.v`.
- The main pipeline correctly keeps the raw L0 label, but side labels would make
  the sample more useful.

**Research use.**

- Add optional diagnostic sidecar labels: preserve raw L0 as the official
  blocking label, then record best-effort L1/L2/L3 side results when possible.
- Train separate models for "first blocking failure" and "latent downstream
  failure prediction".

## Issue 6: Cross-file consistency is the repair knee

**Observation.** T1/T2 are repairable after prompt alignment, while T3/T4 remain
hard. The failures shift from simple schema fields to cross-module endpoint
identity, instance/module naming, width equivalence, valid-ready behavior, and
multi-stream simulation semantics.

**Why it matters academically.** This is a concrete difficulty knee for
project-level RTL generation. It supports the reframe claim that the open
problem is not small RTL syntax, but multi-file, cross-module, physically
checkable project consistency.

**Evidence so far.**

- Full tightened baseline: T1/T2 reached L3; T3/T4 did not.
- T3 failed on reserved keyword `fork` as an instance name in one run, then on
  width/top-port mismatch in the narrow smoke run.
- T4 moved from L0 to L1, then failed simulation with unknown output data.

**Research use.**

- Treat T3/T4 as the current calibration knee.
- Build more T3/T4-like topology variants before scaling.
- Report pass-rate by topology, not only aggregate pass-rate.

## Issue 7: Repair trajectories need attempt-level semantics, not only final labels

**Observation.** A sample may move from L0 to L1 without reaching L3. That
partial progress is scientifically meaningful because it reveals which contract
layers the repair loop can internalize.

**Why it matters academically.** A binary success metric undercounts repair
learning. For tool distillation, the trajectory itself is the data: each attempt
is an interaction with a non-differentiable oracle.

**Evidence so far.**

- T4 in the T3/T4 smoke crossed L0 and lint but failed simulation.
- Earlier repairs expanded tiny legacy System-HIS files into larger v1.1-like
  structures, even when final labels stayed L0.

**Research use.**

- Add attempt-level event logging and trajectory summaries.
- Report monotonic/non-monotonic movement across L0/L1/L2/L3.
- Train `LOG2DIAG`, `FAILURE2PATCH`, and `PATCH2VERIFY` views separately.

## Issue 8: The model can repair format before function

**Observation.** Tool-loop repair first learns to satisfy package/schema
contracts, then exposes RTL compile and simulation issues. This ordering may be
natural because L0 is the earliest blocking gate.

**Why it matters academically.** It suggests a curriculum: first project
contract validity, then RTL compile, then simulation semantics, then synthesis
and physical closure. It also argues against collapsing all failures into one
generic "incorrect" label.

**Evidence so far.**

- T1/T2 reached L3 after schema-aware prompt tightening.
- T4 moved from L0 to L1 but failed simulation, showing format repair did not
  imply functional repair.

**Research use.**

- Design training curricula by evaluation depth.
- Measure whether fixing earlier layers increases exposure to later layers.
- Compare direct project generation against staged System-HIS-to-project
  generation.

## Issue 9: Tool-side normalization is a baseline, not merely engineering glue

**Observation.** Numeric width normalization changed the meaning of T3 residual
failures: `[7:0]` and `8` should be equivalent for concrete ports, while
parameterized widths need more careful symbolic handling.

**Why it matters academically.** Some apparent model failures are artifacts of
representation. A benchmark must decide what equivalences are allowed. The
normalizer itself is therefore part of the measurement method and a baseline
for deterministic repair.

**Evidence so far.**

- T3 narrow smoke exposed numeric width notation mismatch.
- The checker now normalizes concrete numeric ranges while preserving stricter
  parameterized comparisons.

**Research use.**

- Report normalized and unnormalized L0 results as an ablation if feasible.
- Add a deterministic contract-normalizer baseline.
- Keep normalization rules public and versioned.

## Issue 10: The benchmark must distinguish source of failure

**Observation.** The dataset now has fields such as `source`,
`failure_origin`, `measurement_point`, `requirement_style`, and
`difficulty_tier`. These are necessary because natural LLM failures, synthetic
mutations, deterministic component generation, and future fine-tuned outputs
are different distributions.

**Why it matters academically.** Mixing failure origins without labeling them
would make the dataset hard to interpret. A model that repairs injected errors
may not repair natural project-generation errors. A model that repairs DeepSeek
outputs may not generalize to another generator.

**Evidence so far.**

- Current DeepSeek runs use `source=deepseek`, `failure_origin=natural_llm`,
  `requirement_style=natural_component`.
- Synthetic failure injection exists but is intentionally not the main data
  source.

**Research use.**

- Report results by failure origin and source model.
- Use synthetic failures for controlled ablation, not as the primary headline.
- Add multi-source inputs later to support the "tool distillation, not LLM
  distillation" claim.

## Issue 11: Baseline (a) and baseline (b) need careful naming

**Observation.** Baseline (a) is the frontier-model first-attempt/no-tool
measurement point. Baseline (b) is the same frontier model with tool-loop
repair. These are not external competitors; they are internal measurement points
in the SR2FPGA chain.

**Why it matters academically.** Misnaming these baselines could make the paper
sound like it claims to beat frontier models with a small local model. The
correct claim is different: quantify how much tool feedback and tool-verified
training add over first-attempt generation.

**Evidence so far.**

- `a_first_attempt_no_tools`: 4/4 L0.
- `b_tool_in_loop_repair`: after prompt tightening, T1/T2 reached L3 while
  T3/T4 remained failure trajectories.

**Research use.**

- In the paper, call frontier first-attempt generation the "first-half
  baseline".
- Reserve model-vs-model claims for later fine-tuned measurement point (c).

## Issue 12: Small sample counts are useful for discovery but not yet evidence

**Observation.** The current runs are intentionally small: T1-T4, with smoke
subsets. They are excellent for finding failure families and hardening the
pipeline, but not sufficient for statistical claims.

**Why it matters academically.** The current numbers should be used as
calibration and qualitative evidence, not final performance claims.

**Evidence so far.**

- The observed T3/T4 knee is compelling but based on very few samples.
- Prompt changes were made between runs, so direct quantitative comparison is
  not yet clean.

**Research use.**

- Freeze configs/prompts before larger runs.
- Expand topology variants around the T3/T4 knee.
- Report confidence intervals or at least sample counts in tables.

## Issue 13: System-HIS itself is not yet a stable canonical IR

**Observation.** Existing `system_his.json` files are not field-compatible
across dataset generations. Historical deterministic samples use fields such as
`project_name`, `task_type`, `system`, `interface`, `verification`; some LLM
samples use ad hoc fields such as `design`, `task`, `clock`, `baud_rate`,
`history`, `components`, or `version`; newer repaired samples use
`schema_version: system-his-v1.1` with `project`, `clocks`, `resets`,
`modules`, `connections`, `top_ports`, `verification`, and `qor_intent`.

There is also an internal spec drift: the research reframe describes `role` as
a semantic module role such as `fifo`, `arbiter`, `pipeline`, or `alu`, while
the current L0 checker and prompt require `role` to be exactly `top` or
`submodule`.

**Why it matters academically.** System-HIS is supposed to be both the
intermediate supervision target and the L0 contract oracle. If its fields drift,
then the model is not learning a clean intermediate representation. It is
learning a mixture of historical JSON shapes, prompt artifacts, and checker
quirks. This weakens the core claim that System-HIS is an explicit, learnable,
evaluable requirement-level IR.

**Evidence so far.**

- Some final samples have no `schema_version` and use legacy top-level keys:
  `interface`, `platform`, `project_name`, `system`, `task_type`,
  `verification`.
- Some LLM samples have nearly free-form keys such as `design`, `task`,
  `baud_rate`, `history`, `components`, or `version`.
- Newer baseline (b) repaired samples use `system-his-v1.1`, but still include
  legacy compatibility fields such as `project_name`, `system`, and
  `interface` beside the v1.1 fields.
- The current prompt/checker resolves module `role` as structural
  `top|submodule`, while the higher-level research text still suggests
  semantic roles.

**Research use.**

- Freeze a canonical `system-his-v1.2` before larger data generation.
- Split ambiguous fields into separate concepts, e.g. structural role
  (`top|submodule`) versus semantic kind (`skid_buffer`, `accumulator`,
  `stream_join`, `counter_core`).
- Keep legacy samples, but mark them as `system_his_schema_version: legacy` and
  exclude them from clean REQ-to-HIS training unless migrated.
- Add a migration/normalization view so the dataset can support both historical
  traceability and clean model training.

## Issue 14: IR-valid architecture can still lower to illegal Verilog

**Observation.** The `his-v12-smoke-6` run accepted a
`system-his-v1.2-topdown` contract at L0 and reached Verilator lint, but the
generated `rtl/top.v` failed because the `stream_join` instance was named
`join`, a Verilog reserved keyword:
`%Error: rtl/top.v:52:7: syntax error, unexpected join`.

**Why it matters academically.** This separates IR self-consistency from
target-language realizability. A high-level architecture contract can be
well-formed, top-down, and internally connected while still containing
identifier choices that are illegal after RTL lowering. For SR2FPGA, this means
REQ-to-HIS validation should include lowering-aware constraints, not only
abstract architecture checks.

**Evidence so far.**

- `tmp/sr2fpga_runs/his-v12-smoke-6/summary.json` reports
  `pass_level_breakdown.L0 = 1`, `contract_metrics.l0_contract_failures = 0`,
  and `failure_family_breakdown.rtl_compile_failure = 1`.
- `datasets/sr2fpga_rtl_v1/sample_his_v12_smoke_v2_t4_dual_stream_join_8_000001/eval/labels.json`
  marks `l0_complete: true` and `l1_lint_pass: false`.
- The first lint diagnosis points to instance name `join` in `rtl/top.v`.

**Research use.**

- Treat target-language identifier legality as part of the IR checker for
  clean REQ-to-HIS supervision.
- Keep this as a distinct failure family from malformed JSON, missing files,
  and cross-file endpoint mismatch.
- Prefer canonical instance names that are semantic but legal, e.g.
  `join_core` instead of `join`.

## Issue 15: Reserved-keyword failures are not limited to architecture names

**Observation.** The `his-v12-smoke-8` run avoided the previous `join`
instance-name failure and correctly kept `join_core`, but Verilator lint still
failed because the generated `skid_buffer.v` used `buf` as an internal array
name. Verilog treats `buf` as a primitive keyword, so this produced syntax
errors even though the System-HIS contract was valid and the instance topology
was legal.

**Why it matters academically.** A REQ-to-HIS checker can prevent illegal
architecture-level identifiers, but HIS-to-RTL generation still needs
language-aware lexical constraints for every lowered RTL identifier: modules,
instances, regs, wires, arrays, named blocks, and parameters. This is a useful
example of a failure that is below architecture design but above functional
semantics.

**Evidence so far.**

- `tmp/sr2fpga_runs/his-v12-smoke-8/summary.json` reports
  `pass_level_breakdown.L0 = 1`, `contract_metrics.l0_contract_failures = 0`,
  and `failure_types.syntax_error = 1`.
- `datasets/sr2fpga_rtl_v1/sample_his_v12_smoke_v4_t4_dual_stream_join_8_000001/attempts/attempt_000/diagnosis.json`
  points to `reg [WIDTH-1:0] buf [0:DEPTH-1];` and later `buf[...]` uses in
  `rtl/skid_buffer.v`.

**Research use.**

- Distinguish architecture-identifier legality from RTL-internal identifier
  legality.
- Add reserved-keyword constraints to both REQ2HIS and HIS2PROJECT prompts.
- Consider a deterministic RTL lexical sanitizer as a tool-side baseline.

## Issue 16: Metadata can drift even when generated artifacts are correct

**Observation.** The `his-v12-smoke-7` sample generated a valid
`system-his-v1.2-topdown` file, but `metadata.json` still recorded
`system_his_schema_version: system-his-v1.1` because the runner metadata path
was hard-coded.

**Why it matters academically.** Training and evaluation views depend on
metadata as much as file contents. If metadata schema labels drift, clean
REQ-to-HIS data can be misbucketed as v1.1, contaminating schema-specific
analysis and model training.

**Evidence so far.**

- `datasets/sr2fpga_rtl_v1/sample_his_v12_smoke_v3_t4_dual_stream_join_8_000001/final/generated_project/system_his.json`
  has `schema_version: system-his-v1.2-topdown`.
- The same sample's `metadata.json` was written before the fix and labels it as
  `system-his-v1.1`.
- `his-v12-smoke-8` verifies the fix: the v4 sample metadata now records
  `system_his_schema_version: system-his-v1.2-topdown`.

**Research use.**

- Treat metadata generation as part of the benchmark contract, not only a
  recorder detail.
- Add schema-version checks to exported JSONL validation before using data for
  training.

## Issue 17: Long LLM generation stages need stage-level observability

**Observation.** The v3 and v4 two-stage smoke runs spent several minutes with
`run_state.next_index = 0` and no sample artifact yet written. The runs
eventually completed, but during generation it was not visible whether the
pipeline was in REQ2HIS, HIS2PROJECT, validation retry, or network wait.
After adding stage events, `his-v12-smoke-10` recorded `req2his` and
`his2project` start/finish events while the run was still active.

**Why it matters academically.** Repair trajectories are tool-interaction data.
If long LLM stages are opaque, then timeout, retry, and malformed-output events
are under-recorded. This weakens both engineering debuggability and the
scientific trace of how samples were produced.

**Research use.**

- Add stage event logging before and after REQ2HIS, HIS2PROJECT, validation,
  and local EDA calls.
- Record generation latency and retry count as sample metadata or run events.
- Keep API/network failures separate from model artifact failures.

**Implementation progress.**

- `DeepSeekTwoStageProjectGenerator` now emits `generation_stage_started`,
  `generation_stage_finished`, and `generation_stage_failed` events.
- Runner injects a sample-aware event sink for `deepseek-his-v12` and writes
  these events to `events.jsonl`.
- `his-v12-smoke-10` measured `req2his` at about 62.2 seconds and
  `his2project` at about 70.7 seconds for the T4 simple-prompt smoke.

## Issue 18: Precheck stages can shift failure attribution without changing pass level

**Observation.** After adding the RTL identifier precheck, `his-v12-smoke-9`
recorded a new `rtl_identifier_check` trajectory stage before Verilator. The
v5 sample passed that stage and then failed Verilator with
`failure_type: lint_warning_as_error` because `rtl/top.v` declared an unused and
undriven `out_ready_out` wire. `his-v12-smoke-10` repeated the same pattern
with an unused/undriven `staged_ready` wire.

**Why it matters academically.** The pass level remained L0 because lint did
not pass, but the failure attribution became more precise: lexical legality was
separated from strict lint hygiene. This makes the trajectory more useful for
training and analysis because the absence of one failure class becomes evidence
that the model advanced to the next engineering constraint.

**Evidence so far.**

- `tmp/sr2fpga_runs/his-v12-smoke-9/summary.json` reports
  `failure_types.lint_warning_as_error = 1`,
  `failure_family_breakdown.rtl_compile_failure = 1`, and
  `contract_metrics.l0_contract_failures = 0`.
- `datasets/sr2fpga_rtl_v1/sample_his_v12_smoke_v5_t4_dual_stream_join_8_000001/eval/trajectory.json`
  records `rtl_identifier_check` as passed before the failed `lint` stage.
- The diagnosis points to `rtl/top.v` wire `out_ready_out`, which is declared
  but unused/undriven.
- `tmp/sr2fpga_runs/his-v12-smoke-10/summary.json` again reports
  `failure_types.lint_warning_as_error = 1`, while
  `datasets/sr2fpga_rtl_v1/sample_his_v12_smoke_v6_t4_dual_stream_join_8_000001/eval/trajectory.json`
  records `rtl_identifier_check` as passed.

**Research use.**

- Report both pass level and first failing stage, not only pass level.
- Treat newly inserted deterministic prechecks as measurement instruments; they
  can improve label precision even when aggregate L0/L1 pass rates do not move.
- Add stage-latency and stage-outcome logs so future prechecks can be studied
  as part of the repair curriculum.

## Immediate Research Actions

1. Keep L0 project-package failures as official labels and first-class repair
   targets.
2. Add optional side-diagnostic labels for generated RTL hidden behind L0
   failures.
3. Re-run T3 after numeric-width normalization to see whether it crosses L0.
4. Freeze a prompt/config version before the next larger baseline run.
5. Add attempt-level event summaries so partial repair progress can be measured.
6. Add deterministic L0 normalization/repair as a baseline against LLM repair.
7. Expand T3/T4-like topology variants before scaling T1/T2.
8. Preserve `source`, `failure_origin`, `measurement_point`,
   `requirement_style`, `difficulty_tier`, and `topology_id` in every exported
   training view.
9. Freeze and document a canonical System-HIS schema before generating the next
   clean training split.
10. Extend lexical reserved-keyword checks or sanitization for all generated
    RTL identifiers, not only System-HIS instance names.
11. Add stage-level generation events and latency metrics for REQ2HIS and
    HIS2PROJECT.

## Paper Hooks

- **Motivation:** real frontier LLM failures are project-package and
  cross-file-consistency failures, not only bad Verilog syntax.
- **Benchmark contribution:** L0-L5 must start at artifact contract validity and
  end at physical/board validation.
- **Dataset contribution:** the unit is a tool-verified trajectory with a
  versioned intermediate contract, not a standalone code sample.
- **Method contribution:** tool feedback can be distilled only if the dataset
  preserves diagnosis, patch, and attempt-level movement.
- **Threats to validity:** prompt iteration, checker strictness, small sample
  count, System-HIS schema drift, and source-model dependence must be made
  explicit.
