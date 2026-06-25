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

## Issue 19: Checker parser duplication can create oracle drift

**Observation.** The v1.1 project-level L0 checker already had RTL module,
parameter, port, and width parsing helpers. The v1.2 freeze requires HIS↔RTL
cross-checks with the same semantics. If v1.2 reimplemented its own parser, the
same generated project could receive different L0 labels depending on schema
version, even when the underlying RTL is identical.

**Why it matters academically.** The checker is the benchmark oracle. Duplicate
parsers make the oracle itself a source of uncontrolled variation, weakening
claims about model failure distributions and repair progress. A shared
`rtl_introspect` module reduces one form of measurement drift before scaling the
clean v1.2 dataset.

**Evidence so far.**

- Freeze Task 1 extracted RTL introspection helpers into
  `LLM/src/sr2fpga_agent/rtl_introspect.py`.
- The v1.1 checker now imports the shared helper functions while preserving its
  existing behavior.
- Verification after the extraction: `python3 -m unittest discover -s LLM/tests -q`
  ran 173 tests successfully.

**Research use.**

- Treat checker implementation reuse as part of benchmark validity, not merely
  code cleanup.
- When v1.2 cross-checks are added, compare against v1.1 behavior through the
  same parser to isolate schema effects from parser effects.

## Issue 20: Prototype schema suffixes can contaminate clean splits

**Observation.** The v1.2 prototype originally used
`system-his-v1.2-topdown`, while the freeze spec defines the canonical schema as
exactly `system-his-v1.2`. If both strings are accepted as current schemas,
dataset metadata, checker dispatch, and export filters can silently mix
prototype and canonical contracts.

**Why it matters academically.** Schema-version drift changes the benchmark
oracle and can make clean/quarantine split rules ambiguous. A model improvement
claim could otherwise be confounded by accepting a looser prototype contract in
some samples and the frozen contract in others.

**Evidence so far.**

- Freeze Task 2 changed the v1.2 checker constant to `system-his-v1.2`.
- The checker now rejects the retired `system-his-v1.2-topdown` suffix.
- DeepSeek REQ2HIS prompts, parser expectations, runner metadata, and the T4
  example fixture now use the canonical schema string.
- Verification after the rename: `python3 -m unittest discover -s LLM/tests -q`
  ran 175 tests successfully.

**Research use.**

- Treat non-canonical schema versions as legacy/quarantine unless explicitly
  migrated.
- Preserve historical prototype smoke metadata, but do not use it as clean
  v1.2 training evidence.
- Report the schema-version freeze date when describing the clean v1.2 dataset.

## Issue 21: Optional timing metadata still needs semantic bounds

**Observation.** System-HIS v1.2 allows per-flow `data_flow.timing` metadata to
be optional, but once present it must be comparable across samples. Values such
as `initiation_interval = 0`, negative latency, boolean pseudo-integers, or
blank throughput strings would make a generated project look more architected
than it really is while carrying unusable performance claims.

**Why it matters academically.** SR2FPGA is not only evaluating whether RTL
compiles; it is collecting intermediate architecture contracts. Timing metadata
may become a supervision signal or an analysis covariate. If optional timing
fields are accepted without minimum semantics, clean v1.2 data can contain
uncontrolled label noise.

**Evidence so far.**

- Freeze Task 3 added checker validation for optional `data_flow[*].timing`.
- Missing `timing` remains valid, preserving short-prompt flexibility.
- Present timing now requires non-negative integer `latency_cycles`, positive
  integer `initiation_interval`, and non-empty string `throughput` when supplied.
- Verification after the change: `python3 -m unittest discover -s LLM/tests -q`
  ran 176 tests successfully.

**Research use.**

- Distinguish "unknown timing" from "invalid timing" in future dataset exports.
- Treat invalid timing as an L0 contract issue, not as a downstream QoR issue.
- Later compare whether LLMs naturally omit timing, hallucinate timing, or use
  physically plausible values under different prompt styles.

## Issue 22: Free-text control flow blocks measurable L2 behavior

**Observation.** Early System-HIS examples used free-text `condition/effects`
entries. They are readable to humans but hard for tools to use when generating
or checking liveness, stalls, FSM walks, and control/datapath handshakes.
Structured `fsm_transition` and `enable_rule` entries with checked guards make
the control layer machine-verifiable.

**Why it matters academically.** Failure repair needs to know whether a model
failed because it built the wrong datapath, the wrong control sequencing, or the
wrong RTL realization of otherwise correct control intent. Free-text control
flow collapses those categories. A bounded guard grammar creates a measurable
bridge from architecture intent to L2 simulation tests.

**Evidence so far.**

- Freeze Task 4 added FSM structure checks for declared state sets,
  `initial`, and `reset_state`.
- Structured `fsm_transition` and `enable_rule` checks now validate guard signal
  references, allowed guard operators, effect targets, and guard nesting depth.
- Verification after the change: `python3 -m unittest discover -s LLM/tests -q`
  ran 180 tests successfully.

**Research use.**

- Keep free-text control descriptions as human commentary only; use structured
  rules for clean v1.2 training and L2 generation.
- Record whether LLM failures occur in FSM declaration, guard reference, guard
  depth/operator, or RTL implementation of a valid rule.
- Use guard-depth violations as evidence that the model is leaking Verilog-like
  expression complexity into the IR layer.

## Issue 23: HIS and RTL can both look plausible while disagreeing

**Observation.** A generated project can contain a valid-looking System-HIS file
and syntactically plausible RTL, yet disagree on component ports, directions,
widths, instance names, source lists, testbench top instantiation, or timing
constraint ports. These cross-file mismatches are different from pure schema
errors and different from Verilog syntax errors.

**Why it matters academically.** Many code-generation evaluations score files
independently. FPGA projects are multi-artifact systems: the architecture
contract, RTL, manifest, constraints, and testbench must cohere. HIS↔RTL
cross-checks expose a system-integration failure mode that is likely common in
LLM-generated engineering packages.

**Evidence so far.**

- Freeze Task 5 added `check_system_his_v12_against_rtl(payload, project)`.
- The checker now catches renamed component ports, direction mismatches, missing
  top instances, invalid data-flow RTL endpoints, manifest/source drift,
  testbench top-instantiation drift, and invalid SDC `get_ports` references.
- Width checking uses semantic normalization, so `[7:0]`, `8`, and resolved
  width values compare by meaning rather than by raw spelling.
- Verification after the change: `python3 -m unittest discover -s LLM/tests -q`
  ran 184 tests successfully.

**Research use.**

- Track HIS↔RTL mismatch as a separate L0 subfamily instead of collapsing it
  into generic artifact contract failure.
- Use semantic width equivalence to avoid overcounting harmless formatting
  differences as model errors.
- Preserve mismatch location (`component_port`, `top_port`, `instance`,
  `data_flow_endpoint`, `manifest`, `testbench`, `constraint`) for repair
  curriculum design.

## Issue 24: Clean splits need schema-derived quarantine labels

**Observation.** After the v1.2 freeze, deterministic generation can emit clean
canonical `system-his-v1.2`, while older DeepSeek baseline runs and prototype
smokes still carry v1.1, legacy, or retired `system-his-v1.2-topdown` metadata.
Without an explicit split label, exports can silently mix these regimes.

**Why it matters academically.** Schema changes alter the oracle, the IR fields
available to the model, and the repair feedback surface. Training or evaluating
on a mixture of v1.1/prototype/v1.2 samples without a split label would confound
model capability with data-contract drift.

**Evidence so far.**

- Freeze Tasks 7a/7b migrated deterministic output for all supported task
  families to canonical `system-his-v1.2`.
- Runner metadata now labels v1.2 samples as `training_split: clean`; non-v1.2
  schema versions are `training_split: quarantine`.
- Recorder exports backfill `training_split` for older metadata when exporting
  JSONL views, without rewriting historical metadata files.
- Verification after the change: `python3 -m unittest discover -s LLM/tests -q`
  ran 190 tests successfully.

**Research use.**

- Filter clean supervised REQ->HIS and HIS->project views by one metadata field.
- Preserve quarantined legacy/prototype samples for ablation and historical
  failure analysis.
- Report schema-derived split policy in any dataset paper or experiment table.

## Issue 25: Simple-prompt v1.2 pilot exposes REQ2HIS IR-reference failures

**Observation.** A small DeepSeek `deepseek-his-v12` pilot on 2026-06-25 used
only simple natural-language prompts for T1/T2/T4 component topologies. The T1
event counter reached L3 after one repair, but T2 stream accumulator and T4
dual-stream join failed during REQ2HIS validation before RTL/project generation.

**Why it matters academically.** This is a different failure surface from
classic RTL syntax or simulation failure. The model can understand the task
semantically but still violate the intermediate architecture language: instance
identity, endpoint namespaces, legal control effects, and FSM state completeness.
That makes System-HIS itself a useful benchmark target rather than only a hidden
prompt scaffold.

**Evidence so far.**

- Run: `tmp/sr2fpga_runs/pilot-his-v12-repair-20260625`.
- Config: `tmp/sr2fpga_runs/pilot_his_v12_repair_20260625.yaml`.
- Inputs were simple prompts:
  - T1: "Generate an 8-bit FPGA RTL project that counts incoming event pulses."
  - T2: "Generate an 8-bit FPGA RTL project that accepts a valid-ready input
    stream and accumulates samples."
  - T4: "Generate an 8-bit FPGA RTL project that joins two input streams,
    accumulates joined samples, and exposes one output stream."
- Result: 3 planned / 3 completed; pass levels `L3: 1`, `GEN_FAIL: 2`.
- T1 first attempt failed L0 because System-HIS instances named `event_gate` and
  `counter` did not match top RTL instantiations; DeepSeek repair produced an L3
  final package.
- T2 generation failures included missing `instances[].name`, data-flow
  endpoints using component-like names instead of valid top/instance ports, and
  structured control effects targeting undeclared endpoints such as
  `input_buffer.in_ready` and `top.out_valid`.
- T4 generation failure included incomplete FSM metadata (`initial` and
  `reset_state` empty) and global reset effects targeting undeclared symbols
  such as `all`.
- Runner now records generation-stage failures as `pass_level: GEN_FAIL`,
  `failure_type: generation_failed`, and `failure_family: generation_failure`
  instead of crashing mid-run.
- Verification after the infrastructure fix: `python3 -m unittest discover -s
  LLM/tests -q` ran 198 tests successfully.
- Follow-up run after adding richer REQ2HIS retry feedback:
  `tmp/sr2fpga_runs/pilot-his-v12-retry-feedback-20260625`.
- The follow-up run emitted explicit `generation_stage_retry` events. T2 first
  failed REQ2HIS on `owns_state`, missing state references, and illegal effect
  targets, then repaired the System-HIS enough to enter HIS2PROJECT and produce
  a repair trajectory (`pass_level: L0`) instead of `GEN_FAIL`.
- T4 still failed REQ2HIS after two retry events, converging to a narrower
  reset-reference error: `control_flow 'reset_accum'.when signal 'top.rst_n' is
  not declared`. This suggests a specific next design question: whether reset
  names declared in `top.resets` should also be legal control guard signals, or
  whether the prompt/checker should require every clock/reset to be duplicated
  in `top.ports`.
- Verification after the retry-feedback change: `python3 -m unittest discover
  -s LLM/tests -q` ran 200 tests successfully.
- Follow-up reset-guard run:
  `tmp/sr2fpga_runs/pilot-his-v12-reset-guard-20260625`.
- After accepting declared top clocks/resets as legal control guard signals and
  prompting that clocks/resets should also appear in `top.ports`, T4 no longer
  failed at REQ2HIS. It passed REQ2HIS after one retry, completed HIS2PROJECT,
  and ended as a project-level `L0_FAIL` repair trajectory rather than
  `GEN_FAIL`.
- The remaining T4 failures are now HIS↔RTL contract mismatches: RTL ports are
  missing names expected by System-HIS (`in_valid`, `out_valid`, etc.) and width
  spelling/equivalence mismatches remain for parameterized `DATA_WIDTH` ports.
  This moves the research focus from IR validity to contract-preserving
  HIS2PROJECT generation and repair.
- Subsequent checker audit showed that part of this T4 `L0_FAIL` was a
  measurement false positive, not a model/project error. The RTL port parser was
  reading ANSI-port line comments such as `// input stream` as port names, and
  the width checker compared System-HIS width dictionaries against RTL
  parameterized ranges too literally. After stripping line comments during RTL
  introspection and normalizing dictionary `expr` widths such as `DATA_WIDTH`
  against `[DATA_WIDTH-1:0]`, the same T4 attempt passes offline L0 recheck.
- Manual tool side-evaluation of that same T4 attempt after the checker fixes:
  Verilator lint passed (`exit 0`), Yosys synthesis/stat passed (`exit 0`), but
  Icarus Verilog testbench compilation failed before simulation because
  `sim/tb_top.v` initializes unpacked arrays with aggregate literals such as
  `{8'd1, 8'd2, 8'd3}`. This is a useful boundary case: the generated RTL can be
  lint/synthesis-valid while the generated verification harness is not portable
  across the chosen simulator.
- Verification after the checker/parser fixes:
  `python3 -m unittest discover -s LLM/tests -q` ran 205 tests successfully;
  `python3 -m compileall -q LLM/src` and `git diff --check` also passed.
- Follow-up implementation added a dedicated
  `testbench_simulator_compatibility` classifier for Icarus elaboration failures
  on aggregate literals and added explicit Icarus portability rules to
  DeepSeek project generation, HIS2PROJECT, and repair prompts. Verification:
  `python3 -m unittest discover -s LLM/tests -q` ran 208 tests successfully, and
  the old T4 `sim_compile` log now classifies as
  `testbench_simulator_compatibility`.
- A one-step DeepSeek repair experiment on the old T4 attempt wrote
  `tmp/sr2fpga_runs/t4_sim_compile_repair_20260625`. The repair changed
  `sim/tb_top.v` from aggregate array initialization to explicit `initial`
  assignments. The repaired package passes L0, Verilator lint, Icarus compile,
  and Yosys synthesis, then reaches simulation and fails with `TEST_FAIL:
  mismatch at 1, expected 12, got 10`, which classifies as
  `functional_mismatch`. This is exactly the desired trajectory distinction:
  testbench dialect repair exposed a deeper stream/accumulation semantic
  mismatch.
- A second functional repair prompt added an anti-cheating rule: do not make a
  functional mismatch pass by changing expected values unless the diagnosis
  explicitly says the testbench expectation is wrong. The next DeepSeek repair
  kept expected values `5, 12, 21`, but changed the stimulus to avoid duplicate
  valid-ready acceptance. That exposed another verification-harness failure:
  the testbench could deassert valid in the same simulation timestep and hang
  without a bounded timeout.
- A third repair prompt added a bounded-wait rule for all generated testbenches.
  The resulting run `tmp/sr2fpga_runs/t4_timeout_repair_20260625` passes L0,
  Verilator lint, Icarus compile, vvp simulation (`TEST_PASS`), and Yosys
  synthesis/stat. This moves the same T4 trajectory to L3 without changing the
  expected cumulative outputs. Verification after these prompt/classifier
  changes: `python3 -m unittest discover -s LLM/tests -q` ran 209 tests
  successfully; `python3 -m compileall -q LLM/src` and `git diff --check` also
  passed.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3-20260625` did not reach L3. It
  revealed another evaluator-equivalence gap: System-HIS width objects such as
  `{"expr": "DATA_WIDTH", "resolved": 8}` should match concrete RTL width `8`
  when the resolved value agrees. The checker now compares width candidate sets
  instead of a single preferred spelling, so both symbolic RTL
  `[DATA_WIDTH-1:0]` and concrete RTL `[7:0]` can be accepted when justified by
  the System-HIS width object.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3b-20260625` then skipped the old
  L0 width false positive and reached L1. Its repair trajectory was:
  `lint_warning_as_error` on an implicit undeclared signal, then a remaining
  width warning, then a testbench syntax error, then a bounded simulation
  timeout. A classifier fix now labels Verilator implicit-signal logs as
  `undeclared_signal` and avoids misclassifying `Simulation reported TEST_FAIL`
  as `port_mismatch`.
- A side repair on the L1 final package,
  `tmp/sr2fpga_runs/t4_fresh_l3b_timeout_side_repair_20260625`, passes L0,
  Verilator lint, Icarus compile, vvp simulation (`TEST_PASS`), and Yosys
  synthesis/stat. This shows the fresh official sample is still repairable to
  L3, but the current official `max_attempts: 4` budget is one repair step too
  small for this natural T4 trajectory. Verification after the width/classifier
  changes: `python3 -m unittest discover -s LLM/tests -q` ran 211 tests
  successfully; `python3 -m compileall -q LLM/src` and `git diff --check` also
  passed.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3c-20260625` used
  `max_attempts: 5` and still ended at L1. Its trajectory was L0 FSM-state
  mismatch, Verilator width-truncation warnings in `skid_buffer`, Icarus
  testbench syntax errors, and two bounded simulation timeouts. A side repair
  on the L1 final package,
  `tmp/sr2fpga_runs/t4_fresh_l3c_timeout_side_repair_20260625`, also remained
  at simulation timeout even though L0, lint, compile, and synthesis passed.
  Follow-up handshake diagnosis in
  `tmp/sr2fpga_runs/handshake_debug_l3c_20260625` showed the final RTL was not
  necessarily the failing artifact: the generated testbench asserted
  `in0_valid/in1_valid`, waited on `@(posedge clk)`, then deasserted valid with
  blocking assignments in the same simulator timestep. The DUT and testbench
  therefore raced in the active event region, and the skid buffers never
  captured the inputs. A protocol-stable testbench that drives/deasserts on
  `negedge clk` passes the same RTL with `TEST_PASS`. This reclassifies the
  l3c timeout as a verification-harness/sampling-race failure candidate, not
  confirmed RTL functional failure. A new classifier label,
  `testbench_handshake_timeout`, now separates logs like `TEST_FAIL: timeout
  waiting for output at iteration 0` from generic timeouts.

**Research use.**

- Treat REQ2HIS as its own supervised target and evaluation stage.
- Add IR-specific error subfamilies: namespace error, missing instance identity,
  illegal effect target, incomplete FSM declaration, and reset abstraction
  mismatch.
- Consider a repair path for invalid HIS before HIS2PROJECT, separate from RTL
  repair.
- Compare simple prompts vs. natural-component prompts to measure how much
  topology scaffolding reduces IR-reference errors.
- Track oracle/toolchain false positives separately from model failures,
  especially parser limitations, width-equivalence policy, and simulator
  dialect support in generated testbenches.
- Treat generated testbenches as first-class artifacts in failure repair:
  waveform-visible valid-ready races can make a correct or near-correct RTL
  package look like an RTL timeout failure.
- Treat repair-provider validity as part of the trajectory, not as runner
  infrastructure noise. A fresh run
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3d-20260625` exposed that a DeepSeek
  repair response with an invalid `system_his.json` could previously raise a
  `ValueError` and abort the whole batch before labels were written. The agent
  now records this class as `failure_type=repair_failed`, `stage=repair`, with
  the upstream diagnosis preserved.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3e-20260625` completed after the
  testbench sampling prompt and repair-failure handling changes. It ended at
  L1, not L3, but every attempt passed L0, Verilator lint, and Icarus compile.
  The trajectory was one valid-ready input-handshake timeout followed by four
  functional mismatches (`Expected 165`, observed `0`, `162`, then `132`).
  This is a cleaner T4 signal than l3c: the project package is structurally
  valid and portable enough to simulate, while the remaining failure is stream
  join/accumulation semantics under the generated test scenario. Future logs
  containing `Timeout waiting for input handshake` classify as
  `testbench_handshake_timeout` rather than generic timeout.
- A local semantic trace of l3e attempt 004 in
  `tmp/sr2fpga_runs/semantic_debug_l3e_attempt4_20260625` confirmed the final
  `Expected 165 but got 132` mismatch is a real RTL data-loss bug, not a wrong
  expected value. The joined samples accepted by the accumulator were
  `11, 22, 44, 55`; the `33` sample was lost during back-to-back valid-ready
  traffic through the skid buffers and join. DeepSeek prompts now require
  back-to-back valid-ready verification and per-output transaction checking, so
  a final-value-only test cannot hide a lost or duplicated stream transfer.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3f-20260625` completed with one
  T4 simple-prompt sample and ended at L0 after five failed attempts. The
  trajectory is valuable because the repair loop made partial progress across
  failure strata: attempts 000 and 001 failed L0 consistency because
  `system_his.json`/`manifest.json` referenced `stream_join.in1_data` while
  the generated RTL module did not declare it; attempt 002 crossed L0 and the
  RTL identifier check, then failed Verilator lint on `UNUSEDPARAM` and
  `UNUSEDSIGNAL`; attempt 003 tried to remove the unused `DEPTH` parameter but
  left `.DEPTH(2)` overrides in `top.v`, creating a Verilator `PINNOTFOUND`
  parameter-interface error; attempt 004 reintroduced `DEPTH` but still failed
  as `lint_warning_as_error`. This shows repair can move an artifact-contract
  failure into a cleaner RTL-lint failure, but may also introduce a new
  cross-file parameter contract inconsistency. The log parser now classifies
  Verilator `PINNOTFOUND` parameter errors as `parameter_mismatch`, and the
  repair prompt now tells the model that unused-parameter fixes must keep the
  module declaration and all instantiations consistent. The runner summary now
  includes `attempt_stage_transition_breakdown`, so trajectories such as
  `l0_consistency->lint` and `lint->sim_run` are measurable without manually
  inspecting each `trajectory.json`. On the l3f sample the new derived counts
  are `l0_consistency->l0_consistency: 1`, `l0_consistency->lint: 1`, and
  `lint->lint: 2`.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3g-20260625` used the same T4
  simple-prompt topology with corrected `difficulty_tier: T4` metadata. It
  ended at L1 after five failed attempts, but the repair trajectory crossed
  every early package boundary: `l0_consistency->l0_consistency: 1`,
  `l0_consistency->lint: 1`, `lint->sim_compile: 1`, and
  `sim_compile->sim_run: 1`. The final summary stored these counts in
  `attempt_stage_transition_breakdown`, proving that the new summary field is
  useful on real generated samples, not only unit fixtures. The failure
  sequence was two System-HIS/RTL width-contract mismatches, one Verilator
  lint warning-as-error for unused `stage_ready`, one Icarus testbench syntax
  error, and one simulation mismatch.
- The l3g final mismatch (`expected 3, got 6`) appears to be a generated
  testbench observation bug rather than a clear RTL functional bug. The
  testbench does `wait(out_valid); @(posedge clk) #1;` before checking
  `out_data`, which can skip the current valid transaction and observe the
  next accumulated value. DeepSeek prompts now explicitly say that after
  `wait(out_valid)`, the testbench must check the current transaction before
  advancing to another active clock edge. The agent now also runs a
  `testbench_static_check` before `sim_compile`; on the l3g final testbench it
  reports `testbench_observation_race` at line 44, separating this oracle bug
  from true RTL functional mismatch.
- A retrospective scan with the new `testbench_static_check` found
  `testbench_observation_race` in 9 of 155 generated attempt testbenches. The
  hits are concentrated in two T4 dual-stream-join samples:
  `sample_baseline_b_tightened_t4_dual_stream_join_8_000004` attempts 000-003
  and `sample_pilot_his_v12_t4_fresh_l3g_20260625_t4_dual_stream_join_8_000001`
  attempts 000-004. The baseline sample never reached simulation because all
  four attempts failed L0, so this pattern is a latent oracle bug hidden behind
  artifact-contract failures. This supports keeping side diagnostics for
  generated testbenches even when the official pass level stops earlier. Runner
  summaries now include `latent_testbench_issue_breakdown`; recomputing the
  l3g summary from its run state reports `{"testbench_observation_race": 5}`.
  The l3g run artifact was refreshed in-place with runner resume, so
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3g-20260625/summary.json` now
  contains the latent-testbench count on disk. The corresponding
  `baseline_report.md` now renders a "Latent Testbench Issues" table so the
  oracle-bug count is visible without opening raw JSON.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3h-20260625` completed one T4
  simple-prompt sample after adding the generated-testbench static check. This
  sample ended at `L0_FAIL` after five failed attempts, with three
  `lint_warning_as_error` failures and two `l0_contract_violation` failures.
  The trajectory did not reach `sim_compile`, so the new
  `testbench_static_check` did not have an official-stage opportunity to fire;
  the runner summary also reports an empty `latent_testbench_issue_breakdown`.
  The useful research signal is repair oscillation: attempts 000 and 001
  exposed an unused `stream_join.in1_data` path, attempts 002 and 004 tried to
  remove or rewrite that interface and broke the System-HIS/manifest/RTL
  contract, while attempt 003 returned to the same Verilator unused-signal
  failure. The derived transition counts are `lint->lint: 1`,
  `lint->l0_consistency: 2`, and `l0_consistency->lint: 1`. This is a clean
  example of local lint-oriented repair damaging the architecture contract
  instead of resolving the underlying dataflow design: the correct repair
  should either implement the second input stream semantically or update the
  whole top-down contract consistently, not silence a warning by deleting
  interface obligations. DeepSeek repair acceptance now runs a System-HIS L0
  gate for v1.2 projects when the upstream failure was not already
  `l0_consistency`; invalid lint/compile/sim repairs are rejected before they
  become the next attempt. The agent labels this class as
  `repair_contract_regression`, separating repair-induced contract damage from
  generic `repair_failed` API or JSON failures.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3i-20260625` was launched after
  adding the repair contract gate. It did not exercise that gate because the
  first official failure was already `l0_consistency`; the subsequent L0 repair
  failed as `repair_failed` with an invalid repaired `system_his.json`.
  However, the run exposed another evaluator/IR boundary issue. The generated
  RTL contained a `stream_join` FSM with states `IDLE`, `SEND_0`, and `SEND_1`,
  and System-HIS named the FSM `join_core.arb_fsm` without an explicit `owner`
  field. The checker interpreted the missing owner as `top`, then falsely
  reported that the FSM states were missing from RTL module `top`. The checker
  now infers the owner from instance-prefixed state/FSM names such as
  `join_core.arb_fsm`, so the same l3i attempt 000 passes offline L0 recheck.
  This is another example of why the benchmark needs to track evaluator
  false positives separately from model failures: a valid instance-level FSM
  can be mislabeled as an architecture-contract failure if IR ownership
  conventions are underspecified.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3j-20260625` was run after the FSM
  owner-inference checker fix. The result moved from l3i's false L0 failure to
  a cleaner L1 repair trajectory: one Verilator `lint_warning_as_error` on an
  unused `accumulator_reg`, followed by four `functional_mismatch` failures at
  `sim_run`. The stage-transition summary is `lint->sim_run: 1` and
  `sim_run->sim_run: 3`; `l0_contract_failures` and
  `cross_file_consistency_error_rate` are both 0.0 for this sample. This is the
  desired effect of improving evaluator fidelity: after removing an ownership
  false positive, the same T4 simple-prompt measurement regime exposes the
  deeper valid-ready/accumulation semantics instead of spending the whole
  budget on contract repair. The mismatch sequence also shows repair movement
  without convergence: expected packets `5, 12, 21` remained stable, while the
  observed values shifted across attempts (`10/22`, `15/22`, `15/24`,
  `15/20`) and backpressure outputs remained wrong. This is a good candidate
  for the next semantic trace tool: classify whether the RTL is accepting extra
  samples, dropping one stream, or whether the generated testbench's expected
  cumulative sequence assumes a different join policy.
- A first semantic trace harness on l3j attempt 004 wrote
  `tmp/sr2fpga_runs/semantic_trace_l3j_attempt4_20260625`. The trace parser
  reports 22 input accepts, 9 join outputs, 8 accumulator outputs, and 6 final
  outputs; the first output mismatch is `idx=1 expected=12 actual=10`. The
  primary diagnosis is `stimulus_reaccepted_while_valid_held`: the generated
  testbench holds `in0_valid` and `in1_valid` high until `out_valid`, while the
  DUT keeps `in*_ready` high, so the same `(1,4)` packet is accepted repeatedly
  across cycles 5-8 before the first output is checked. This shifts the l3j
  functional mismatch from "RTL arithmetic is wrong" toward a generated
  testbench stimulus/oracle bug: the expected sequence assumes one handshake
  per packet, but the stimulus permits multiple valid-ready handshakes for the
  same packet.
- The l3j semantic finding has been converted into a static testbench checker.
  Generated testbenches now report `testbench_stimulus_reaccept_risk` when an
  input `*_valid` signal is asserted and the code waits for `out_valid` before
  withdrawing that input valid, because the same packet can be accepted multiple
  times if the DUT keeps `*_ready` high. The agent runs this rule in
  `testbench_static_check` before `sim_compile`, and the runner's latent
  testbench scan uses the same combined checker. A retrospective scan of the
  l3j sample reports 10 latent hits: two risky stimulus blocks per attempt
  across five attempts. This closes a useful loop: waveform/semantic trace
  evidence produced a deterministic oracle-quality rule that can prevent false
  RTL functional-mismatch labels in future generated samples. The DeepSeek
  project, HIS2PROJECT, and repair prompts now also state the upstream rule:
  do not hold input valid high until `out_valid`; deassert or advance each input
  valid after its own input-ready handshake so one packet cannot be accepted
  repeatedly while the testbench waits for output.
- Fresh official runner experiment
  `tmp/sr2fpga_runs/pilot-his-v12-t4-fresh-l3k-20260625` was run after adding
  the input-valid withdrawal prompt rule and the `testbench_stimulus_reaccept_risk`
  checker. It ended at L1 with one `lint_warning_as_error` followed by four
  `functional_mismatch` failures at `sim_run`; the transition summary is again
  `lint->sim_run: 1` and `sim_run->sim_run: 3`. Unlike l3j, the latent testbench
  issue scan is empty, and every post-lint attempt passed
  `testbench_static_check` before simulation. This is encouraging: the oracle
  bug found by semantic trace is no longer present in this fresh sample, so the
  remaining failures are cleaner candidates for RTL/protocol semantic analysis.
  The repair loop made partial progress on the basic sequence, moving the first
  mismatch from transfer 0 to transfer 2 by attempt 002/003, but attempt 004
  regressed to broad mismatches. This suggests the next repair bottleneck is not
  testbench sampling, but stable preservation of valid-ready join/accumulator
  semantics under repair.

## Current Snapshot - 2026-06-25

The current best status is not "T4 solved"; it is more useful than that. The
pipeline has moved from noisy L0/schema/testbench artifacts toward cleaner T4
L1 semantic failures. The l3h-l3k sequence shows the research stack doing what
it is supposed to do:

- l3h exposed repair-induced architecture-contract damage, leading to a repair
  contract gate and the `repair_contract_regression` distinction.
- l3i exposed a checker false positive around instance-owned FSM names, leading
  to owner inference for names such as `join_core.arb_fsm`.
- l3j reached simulation but semantic tracing showed a generated-testbench
  stimulus/oracle bug: valid stayed high until `out_valid`, so the same packet
  could be accepted repeatedly.
- l3k was run after the prompt and checker changes for that bug; it still ends
  at L1, but latent testbench issues are empty and every post-lint attempt
  passes `testbench_static_check`.

This makes l3k the current cleanest failure specimen: a simple natural-language
T4 prompt produces a structurally valid, simulator-portable project that reaches
`sim_run`, but the repair loop does not yet preserve valid-ready
join/accumulator semantics robustly. That is a better benchmark signal than
early L0-only failures or false functional mismatches caused by the generated
testbench.

## Immediate Research Actions

1. Freeze the current T4 prompt/checker configuration and run a small fresh
   T3/T4 batch to see whether l3k's cleaner L1 pattern repeats.
2. Add automatic semantic side diagnostics for valid-ready
   `functional_mismatch` attempts, using trace summaries of input accepts, join
   outputs, accumulator outputs, and final outputs.
3. Preserve generated-testbench failures as first-class labels, not just
   infrastructure noise, because they are natural project-generation failures.
4. Keep L0 project-package failures as official labels and first-class repair
   targets.
5. Add optional side-diagnostic labels for generated RTL hidden behind L0
   failures.
6. Re-run T3 after the current v1.2 checker and prompt fixes to see whether it
   now crosses L0.
7. Add deterministic L0 normalization/repair as a baseline against LLM repair.
8. Expand T3/T4-like topology variants before scaling T1/T2.
9. Preserve `source`, `failure_origin`, `measurement_point`,
   `requirement_style`, `difficulty_tier`, and `topology_id` in every exported
   training view.
10. Freeze and document a canonical System-HIS schema before generating the next
   clean training split.
11. Extend lexical reserved-keyword checks or sanitization for all generated
    RTL identifiers, not only System-HIS instance names.
12. Add stage-level generation events and latency metrics for REQ2HIS and
    HIS2PROJECT.
13. Re-run a fresh T4 sample through the normal agent loop with the new
    testbench portability, anti-cheating, and bounded-wait prompt rules so the
    official dataset label catches up with the side repair experiment.
14. Add a generated-testbench lint/repair rule for clocked stimulus: drive and
    withdraw valid-ready inputs away from the sampling edge, or use
    nonblocking assignments and explicit post-edge observation points.
15. Add repair-provider failure telemetry to the run summary and paper taxonomy:
    invalid repair artifacts are natural LLM failures and must not crash the
    batch runner.
16. Add an automated side diagnostic for valid-ready streams that reports the
    accepted input/join/output transaction sequence when simulation mismatches
    occur, because this is the fastest way to distinguish testbench expectation
    errors from RTL data-loss bugs.
17. Track parameter-interface mismatches separately from port mismatches in the
    failure taxonomy. The l3f attempt 003 trace shows unused-parameter repair
    can create a distinct cross-file parameter contract bug that should not be
    hidden under generic `unknown` or ordinary port mismatch.
18. Expand generated-testbench semantic checks beyond the implemented
    `wait(out_valid)` then `@(posedge clk)` detector. The l3g trace shows this
    class of oracle bug can produce false functional mismatches by sampling the
    next output transaction.
19. Treat repair contract preservation as an explicit metric: local lint repair
    should not silently rewrite or delete top-down architecture obligations.

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
