# SR2FPGA Phase D Frozen Multi-Teacher Pilot Design

Date: 2026-07-17
Status: approved design, implementation not started
Base commit: `b1f7b926` (`codex/phase-c-c5-evidence`)
Target branch: `codex/phase-d-frozen-multiteacher-pilot`

## 1. Purpose

Phase C established that the trusted task generators, System-HIS contracts,
independent oracles, mutation gates, and L0-L4 evidence pipeline are auditable.
Phase D moves from deterministic reference evidence to the first frozen,
multi-teacher, natural-LLM Line-B pilot.

The purpose is not to obtain a favorable model score. The purpose is to produce
a small but defensible dataset that measures:

1. first-attempt project generation without tool feedback, `(a)`;
2. same-model tool-in-the-loop repair, `(b)`;
3. per-model and per-family failure structure;
4. the quality and completeness of exported training trajectories; and
5. representative OpenXC7 L4 behavior for LLM-generated FIR projects.

The pilot is the gate before larger Line-B collection and the first SFT `(c)`
experiment.

## 2. Fixed Decisions

The following decisions are frozen for this phase.

### 2.1 Sample matrix

The official pilot contains exactly 24 scoreable LLM episodes:

```text
6 task families x 4 teacher models x 1 fixed requirement instance = 24
```

The six families are:

| Family ID | Runner task mapping | Main semantic coverage |
| --- | --- | --- |
| `sync_fifo` | `task_type: fifo` | occupancy, full/empty, simultaneous push/pop |
| `valid_ready_stream_accumulator` | `component_topology: t2_stream_accumulator` | backpressure and payload stability |
| `stream_fork_join` | `component_topology: t4_dual_stream_join` | multi-module ordering, drop/duplication |
| `fir_filter` | `task_type: fir_filter` | signed arithmetic, width growth, DSP-style datapath |
| `sobel_threshold` | `task_type: sobel_threshold` | image pipeline and boundary cases |
| `qtable_update_core` | `component_topology: t6_td_update_core` | fixed-point RL update semantics |

The four teachers are configured by local, ignored configuration:

| Source ID | Gateway-reported model ID | Protocol kind |
| --- | --- | --- |
| `claude` | `claude-opus-4-8` | `anthropic_compat` |
| `gpt` | `gpt-5.5` | `openai_compat` |
| `qwen` | `qwen3-coder-plus` | `openai_compat` |
| `deepseek` | `deepseek-v4-pro` | `deepseek-his-v12` |

Model names are recorded as gateway-reported IDs. The dataset and paper must
not imply that a proxy-served model is identical to an official vendor endpoint
unless that provenance is independently established.

### 2.2 Deterministic control

Each family must have one deterministic `B_ref` control that passes its declared
oracle and L0-L3 before the LLM pilot starts. These six controls are not counted
among the 24 LLM episodes and are not reported as model baselines.

### 2.3 Requirement style

The pilot uses one frozen `simple_prompt` requirement per family. The prompt may
state externally observable behavior, interfaces, parameters, and artifact
requirements. It must not contain:

- RTL implementation code;
- internal register names;
- hidden test vectors or hidden seeds;
- mutation descriptions;
- line-level repair instructions; or
- the deterministic reference implementation.

The exact rendered requirement text is identical across all four teachers for a
family and is identified by SHA-256.

### 2.4 Generation and repair budget

All teachers use two-stage generation:

```text
REQ2HIS -> H0/H1/H2/H3 -> deterministic skeleton -> HIS2PROJECT
```

Every episode has at most three project attempts:

```text
attempt 0: first generation, no tool feedback, measurement (a)
attempt 1: same-model repair using structured tool feedback
attempt 2: same-model repair using structured tool feedback
```

The final accepted or exhausted state is measurement `(b)`. Transport retries
are not project repair attempts.

### 2.5 L4 policy

All 24 episodes run through L0-L3. OpenXC7 L4 is enabled only when:

1. the family is `fir_filter`;
2. the final project passes L3;
3. the OpenXC7 environment passes preflight; and
4. the configured timeout has not been exhausted.

This gives at most four new LLM-generated L4 verdicts. Vivado is not run in this
pilot. Existing Phase C dual-tool reference evidence remains separate.

## 3. Scope

### 3.1 In scope

- frozen 24-episode multi-teacher matrix;
- `repair_provider: same_as_source`;
- attempt-level `(a)` and final `(b)` measurement records;
- deterministic preflight controls;
- measurement-freeze manifest and hashes;
- per-source and per-family reports;
- infrastructure/model-failure separation;
- FIR-only OpenXC7 L4 selection;
- trainable REQ2HIS, HIS2PROJECT, LOG2DIAG, and FAILURE2PATCH exports;
- leakage and trusted-artifact audits;
- independent review of code and run evidence.

### 3.2 Out of scope

- first SFT `(c)` training;
- full Line-B scale collection;
- prompt-style ablation;
- cross-model repair;
- Vivado runs for LLM-generated projects;
- L5 board execution;
- new task families;
- changes that weaken trusted testbenches or reference models; and
- tuning prompts after seeing official pilot outcomes.

## 4. Architecture

Phase D reuses the existing runner, source connections, generators, repairer,
recorder, oracle, and report components. It adds only the controls required for
a frozen paired experiment.

```text
Phase D config
  -> runner preflight
  -> deterministic B_ref gate (6 families)
  -> measurement_freeze.json
  -> planned_samples() == 24
  -> per-sample source generator
  -> per-sample same-source repairer
  -> DataGenerationAgent attempts 0..2
  -> L0-L3, plus FIR-only L4
  -> trajectory / labels / QoR
  -> paired_results.json
  -> baseline_report.md
  -> training exports
  -> evidence audit
```

### 4.1 Same-source repair resolution

The runner accepts the sentinel:

```yaml
repair_provider: same_as_source
```

For each sample, the runner resolves the repair connection from
`sample.source`. Repairers are cached by source connection. A repairer for one
source must never be reused for another source.

Rules:

- `claude` generation uses the `claude` repairer;
- `gpt` generation uses the `gpt` repairer;
- `qwen` generation uses the `qwen` repairer;
- `deepseek` generation uses the `deepseek` repairer;
- deterministic controls do not use an LLM repairer; and
- the resolved source and model are recorded in every attempt.

Preflight must treat `same_as_source` as a policy, not as a provider name.

### 4.2 Attempt measurements

An episode must preserve both the initial and final verdicts. It is insufficient
to store only the highest final level.

The trajectory gains an additive block equivalent to:

```json
{
  "measurement": {
    "initial": {
      "measurement_point": "a_first_attempt_no_tools",
      "attempt_id": 0,
      "highest_level": "L1",
      "failure_class": "rtl_compile_failure"
    },
    "final": {
      "measurement_point": "b_tool_in_loop_repair",
      "attempt_id": 2,
      "highest_level": "L3",
      "failure_class": null
    },
    "repair_attempts_used": 2,
    "repair_success": true,
    "regressions": []
  }
}
```

Existing trajectory readers must remain compatible when this block is absent.

### 4.3 Measurement-freeze manifest

After successful preflight and before the first LLM generation call, the runner
writes `measurement_freeze.json`. The manifest contains:

```json
{
  "schema_version": "sr2fpga-measurement-freeze-v1",
  "run_id": "...",
  "task_matrix": [],
  "source_models": [],
  "requirement_sha256": {},
  "prompt_template_sha256": {},
  "hidden_profile_sha256": {},
  "random_seeds": {},
  "max_attempts": 3,
  "timeouts": {},
  "tool_versions": {},
  "config_fingerprint": "...",
  "l4_policy": {
    "family_ids": ["fir_filter"],
    "run_after_final_l3_pass": true
  }
}
```

The manifest must not contain API keys, raw authorization headers, hidden vectors,
or unrestricted local file paths.

Resume is allowed only when the current freeze fingerprint exactly matches the
stored manifest.

### 4.4 Paired results

The report layer emits `paired_results.json` and a Markdown table with one row
per `(family_id, source)` pair. Required fields include:

```text
family_id
source
gateway_reported_model_id
requirement_sha256
initial_highest_level
initial_failure_class
final_highest_level
final_failure_class
repair_attempts_used
repair_success
regression_count
l4_open_status
infrastructure_status
```

Aggregates are reported per source, per family, and per verification level.
Initial-to-final changes use paired counts; L0-L5 ordinal levels are not averaged
into one score.

## 5. Data Flow And Ownership

### 5.1 Requirement pairing

The runner materializes one canonical `ProjectRequest` and rendered requirement
per family before expanding the four sources. All four source samples reference
the same `paired_requirement_id` and `requirement_sha256`.

Source identity may affect only model invocation and resulting generated
artifacts. It must not affect requirement wording, parameters, hidden scenarios,
or expected behavior.

### 5.2 Trusted artifacts

The following remain trusted and non-model-editable:

- hidden scenarios and seeds;
- Python and embedded-SystemVerilog golden models;
- scoreboards and protocol checkers;
- deterministic skeleton ownership regions;
- board and tool profiles;
- measurement-freeze metadata; and
- data-release metadata.

Any repair that touches a trusted artifact is invalid and receives no automatic
pass credit.

### 5.3 Training views

Only verified episode data is exported. Each exported row carries:

```text
source_episode_id
family_id
source
gateway_reported_model_id
paired_requirement_id
requirement_sha256
attempt_id
measurement_point
failure_origin
verification level or diagnosis source
```

Hidden vectors, hidden seeds, hidden `.memh` paths, and trusted oracle contents
must not appear in public training views.

## 6. Configuration

### 6.1 Committed example

A committed example config documents the matrix and environment variable names
without real endpoints or credentials. It must be runnable after users supply a
local source table.

### 6.2 Local config

The official local run uses an ignored file under `configs/local/` and the
ignored root `.env`. Expected environment variables are:

```text
ANTHROPIC_API_KEY
OPENAI_API_KEY
DASHSCOPE_API_KEY
DEEPSEEK_API_KEY
```

No credential may be copied into committed YAML, JSON, Markdown, logs, reports,
or dataset exports.

## 7. Failure Semantics

### 7.1 Model failures

The following are scoreable model outcomes:

- invalid or unfaithful generated System-HIS;
- malformed project packages;
- L0 cross-file inconsistency;
- RTL identifier, lint, compile, or simulation failure;
- synthesis failure;
- failed or regressive repair; and
- L4 implementation failure after L3 pass.

### 7.2 Infrastructure outcomes

The following are not model failures:

- missing credentials;
- provider authentication failure;
- HTTP 429/5xx after transport retries;
- response transport truncation or timeout;
- missing EDA executable;
- toolchain environment failure; and
- missing OpenXC7 board/tool data.

Infrastructure outcomes are recorded separately and must not enter the model
pass/fail denominator.

### 7.3 Transport retries versus repair attempts

Transport retries happen inside a provider call and do not advance `attempt_id`.
Repair attempts happen only after a generated project receives structured tool
feedback. Every attempt transition must be visible in `events.jsonl`.

### 7.4 Completion policy

The final pilot requires 24 scoreable LLM episodes. A transient infrastructure
failure is resumed under the same freeze manifest and sample ID. It must not be
replaced by another model, another requirement, or a changed prompt. A persistent
provider outage blocks Phase D completion rather than silently reducing the
denominator.

## 8. Reporting And Claim Discipline

The Phase D report must state:

- this is a 24-episode pilot, not a statistically conclusive benchmark;
- model IDs are gateway-reported;
- deterministic controls validate the experiment and are not LLM baselines;
- `(a)` is attempt 0 without tool feedback;
- `(b)` is the final state after at most two same-model repairs;
- low pass rates remain valid findings; and
- only FIR final L3-pass projects are eligible for new OpenXC7 L4 labels.

The report must not call generated projects "correct" or "fully verified". Use
"tool-accepted under the declared contract" and explicit H/L levels.

## 9. Testing Strategy

### 9.1 Unit tests

Tests must cover:

1. parsing `repair_provider: same_as_source`;
2. per-sample repairer resolution for all four source kinds;
3. no repairer sharing across different sources;
4. deterministic controls receiving no LLM repairer;
5. provider preflight ignoring the policy sentinel as a provider name;
6. attempt-0 and final measurement extraction;
7. backwards-compatible trajectory loading;
8. transport failure classification outside the model denominator;
9. freeze-manifest hashing and secret redaction;
10. resume rejection on freeze mismatch;
11. 24-sample Cartesian expansion with six paired requirements;
12. identical requirement hashes across four sources;
13. FIR-only L4 selection after final L3 pass; and
14. hidden-data leakage audit over all exports.

### 9.2 Integration tests

Integration tests use mocked providers and tool runners to prove:

- one source can generate and repair its own failed project;
- a second source uses a distinct repairer;
- attempt 0 remains unchanged when later attempts run;
- `paired_results.json` contains both initial and final verdicts;
- infrastructure failure does not become a model failure; and
- no secret appears in generated artifacts.

### 9.3 Live preflight

Before the official pilot:

```text
6/6 deterministic controls pass L0-L3
6/6 task oracles remain mutation-qualified
4/4 provider authentication probes pass
planned_samples == 24
paired_requirement_ids == 6
each paired requirement has exactly four sources
OpenXC7 preflight passes or produces an explicit infrastructure blocker
```

## 10. Acceptance Criteria

Phase D is complete only when all of the following are true:

### 10.1 Implementation gates

- all repository tests pass;
- the 24-sample matrix expands deterministically;
- `same_as_source` is enforced and auditable;
- attempt `(a)` and final `(b)` records are both preserved;
- freeze mismatch prevents resume;
- FIR-only L4 policy is enforced; and
- old runner configs and trajectory readers remain compatible.

### 10.2 Live-run gates

- 24/24 scoreable LLM episodes exist;
- all four teachers and all six families are represented;
- every episode uses the frozen requirement hash;
- every repair is performed by the originating teacher;
- every episode has complete initial/final paired data;
- no unresolved infrastructure outcome remains;
- every eligible FIR project has an OpenXC7 pass/fail verdict or a documented
  infrastructure skip reason; and
- summary, paired report, trajectories, QoR, events, and training exports are
  mutually consistent.

### 10.3 Integrity gates

- zero hidden-vector, hidden-seed, or hidden-path leakage;
- zero trusted-artifact modifications receiving pass credit;
- zero credentials in tracked files or run artifacts;
- zero unclassified failure origins;
- deterministic controls remain separate from model denominators; and
- an independent code-and-artifact review returns `APPROVED`.

There is deliberately no minimum model pass-rate gate. Model failure is a valid
result when the measurement is frozen and the oracle is trusted.

## 11. Deliverables

The phase produces:

```text
docs/superpowers/specs/2026-07-17-sr2fpga-phase-d-frozen-multiteacher-pilot-design.md
docs/superpowers/plans/2026-07-17-sr2fpga-phase-d-frozen-multiteacher-pilot.md
configs/current/sr2fpga_phase_d_multiteacher_pilot.example.yaml
configs/local/sr2fpga_phase_d_multiteacher_pilot.local.yaml   # ignored
<run>/measurement_freeze.json
<run>/provider_auth.json
<run>/summary.json
<run>/paired_results.json
<run>/baseline_report.md
<exports>/*.jsonl
docs/sr2fpga-phase-d-multiteacher-pilot-evidence-2026-07-17.md
```

## 12. Follow-On Gate

After Phase D is approved:

1. inspect failure and repair distributions;
2. decide whether prompt ambiguity is too dominant;
3. freeze the larger Line-B split and sample budget;
4. scale trajectory collection without changing the Phase D measurement protocol;
5. build the first SFT dataset; and
6. train and evaluate the first `(c)` model.

Phase D does not authorize SFT until its evidence and leakage audits pass.
