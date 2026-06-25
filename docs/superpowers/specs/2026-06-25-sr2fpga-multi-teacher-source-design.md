# SR2FPGA Multi-Teacher Source Design

## Status

Proposed for user confirmation on 2026-06-25.

This document synchronizes with:

- `docs/superpowers/specs/2026-06-22-sr2fpga-research-reframe-design.md`
- `docs/superpowers/specs/2026-06-23-sr2fpga-autonomous-trajectory-runner-design.md`
- `docs/research-objective-sr2fpga-tcad.md`

The goal is to let one runner batch draw candidate projects from **several
independent teacher models**, with per-teacher connection settings, so the
SR2FPGA trajectory dataset is not an artifact of any single generator.

## Motivation

The teacher model that proposes candidate projects shapes the **difficulty and
diversity of the failures** we collect. It does *not* shape label correctness —
labels come from the EDA tool oracle (Verilator / Icarus / Yosys / later
OpenXC7 / Vivado), not from the teacher. The reviewer-facing validity threats a
single teacher creates are therefore:

1. **Single-teacher bias** — the failure distribution and taxonomy reflect one
   model's quirks rather than a real engineering distribution.
2. **Reproducibility** — a closed API teacher drifts over time; nobody can
   regenerate the dataset.
3. **Sparse repair data** — a teacher that rarely fails yields few repair
   trajectories.

Multi-teacher generation turns the teacher into a **measured variable** rather
than a hidden confound, and lets us anchor reproducibility with an open-weight
teacher. The runner already groups every summary metric by `source` (see
`_calibration_breakdown` in `runner.py`), so per-teacher failure distribution
reporting is **already available**; this design only supplies the missing
plumbing to actually run more than one teacher family in a batch.

## Core Decision

Add **per-source teacher connection configuration** plus a generalized
**OpenAI-compatible project generator**, so any OpenAI-API-shaped endpoint can
be attached as a teacher source by configuration alone.

The target teacher matrix (capability x lineage spread):

| Role | Teacher | Purpose |
|------|---------|---------|
| Frontier A | Claude (Anthropic) | high-quality proposals, decorrelated failures |
| Frontier B | GPT-5.5 (OpenAI) | second lineage, decorrelated failures |
| Mid + reproducibility anchor | DeepSeek (open-weight build) | already wired; open weights = reproducible |
| Weak / failure generator | Qwen-7B (API, OpenAI-compatible endpoint) | many natural failures; open weights = reproducible |
| Control | deterministic generator | trusted baseline anchor |

**Gemini is explicitly out of scope for the first cut.** A third frontier point
adds marginal "lineage diversity" but does not improve the capability spread or
reproducibility, which are higher-value. The design must leave a clean seam so
Gemini (or any further OpenAI-compatible endpoint) can be added later as pure
configuration.

## Research Alignment

- The runner is **not** a DeepSeek batch script; it distills the **tool
  oracle**, not any one LLM (reframe + runner specs).
- Frontier models (Claude, GPT-5.5) are first-attempt, no-tool baselines, not
  the final competitor.
- Data must be multi-source to avoid "SR2FPGA == single-model distillation."
- At least one teacher must have **open weights** so the dataset is
  regenerable.
- Teacher choice is recorded per sample and reported per source, so the paper
  can present the teacher as an analyzed factor.

## Current State (gap analysis)

Already in place (`LLM/src/sr2fpga_agent/runner.py`, `cli.py`):

- `TaskConfig.source` — each task can name its own source (default = global
  `provider`).
- `_project_generator_for_sample` builds and **caches a generator per source**,
  so different samples in one batch can use different generators.
- Per-sample metadata records `source`, `generator_provider`,
  `failure_origin`; `_sample_failure_origin` maps `deepseek*` -> `natural_llm`,
  `deterministic` -> `deterministic_template`.
- Preflight aggregates provider auth across all sample sources.
- Summary `calibration_matrix["source"]` already yields per-teacher `total`,
  `pass_levels`, `l3_pass_rate`, `l0_contract_failures`, and cross-file
  consistency error rate.

Missing (the only real work):

- **Connection settings are global single-valued.** `model`, `base_url`,
  `api_key_env` live on `RunnerConfig` (one each). Two DeepSeek-family sources
  must share one endpoint/key/model, so a second teacher *family* cannot be run.
- **Provider whitelist is hard-coded to three strings** in
  `build_project_generator` (`deterministic`, `deepseek`, `deepseek-his-v12`)
  and one in `build_repairer` (`deepseek`).
- No way to attach Claude / GPT-5.5 / Qwen, which need distinct
  endpoints, keys, and model names.

## Design

### 1. Per-source connection table

Add an optional top-level `sources:` mapping to the runner config. Each entry
declares the connection settings for one named source:

```yaml
sources:
  claude:
    kind: openai_compat          # generalized OpenAI-API generator
    model: claude-opus-4-8
    base_url: https://api.anthropic.com/v1
    api_key_env: ANTHROPIC_API_KEY
    generation_mode: two_stage   # req2his -> his2project (preferred) | direct
  gpt55:
    kind: openai_compat
    model: gpt-5.5
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY
    generation_mode: two_stage
  qwen:
    kind: openai_compat
    model: qwen2.5-coder-7b-instruct
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1  # OpenAI-compatible API
    api_key_env: DASHSCOPE_API_KEY
    generation_mode: two_stage
  deepseek-his-v12:                # existing source keeps working unchanged
    kind: deepseek
```

Resolution rules:

- A task's `source` string is looked up in `sources:` first.
- If absent, fall back to the existing global `provider` / `model` /
  `base_url` / `api_key_env` (backward compatible — existing configs are
  unchanged).
- `deterministic` needs no entry.

### 2. Generalized OpenAI-compatible generator

`DeepSeekClient`/`DeepSeekConfig` are already OpenAI-API-shaped. Generalize the
client (or wrap it) into an `OpenAICompatibleClient` parameterized by
`base_url`, `api_key`, `model`, and reuse the existing two-stage REQ2HIS ->
HIS2PROJECT generator (`DeepSeekTwoStageProjectGenerator`) and repairer logic
against it. The two-stage path is preferred because it already enforces the
canonical `system-his-v1.2` contract and feeds checker errors back for bounded
retry; each new teacher inherits that validation for free.

`build_project_generator` / `build_repairer` gain a `kind="openai_compat"`
branch that takes a resolved connection object instead of the global config.
Keep `deepseek` / `deepseek-his-v12` as aliases so nothing regresses.

### 3. Per-sample connection resolution

`_project_generator_for_sample` resolves each sample's connection from the
`sources:` table (falling back to global), then builds/caches the generator
keyed by source. The existing per-source cache already supports this; only the
inputs to `build_project_generator` change from global fields to a resolved
connection.

### 4. Metadata, failure-origin, schema version

- `_sample_failure_origin` must map the new frontier/open-weight teachers to
  `natural_llm` (they are real LLM generators). Make this driven by the
  resolved source `kind`, not a hard-coded `deepseek` prefix check.
- `_sample_system_his_schema_version`: any teacher using `generation_mode:
  two_stage` emits canonical `system-his-v1.2` and is therefore `clean`
  / `training_split: clean`. A `direct` mode source stays `quarantine` until
  validated. Drive this off `generation_mode`, not the literal
  `deepseek-his-v12` string.
- Record the resolved `model` (not just the source label) in sample metadata so
  a drifting API version is traceable.

### 5. Preflight & auth

`runner_preflight` already aggregates providers and checks DeepSeek auth.
Generalize auth diagnostics to iterate the resolved `sources:` table: for each
`openai_compat` source, check its `api_key_env` presence and, under
`--validate-provider`, make one minimal auth request per distinct endpoint.
Report status per source so a missing OpenAI/Anthropic/Qwen key is caught
before spending generation calls.

### 6. Reporting (no new work)

`calibration_matrix["source"]` and `metadata_breakdown["source"]` already
produce the per-teacher failure distribution table that defuses single-teacher
bias. `baseline_report.py` already renders by source. Confirm with a test that a
mixed-teacher run yields one row per teacher; no new reporting code expected.

## Reproducibility Notes

- Pin `model` strings in config and record the resolved model per sample.
- Treat the **frozen dataset (prompts + outputs + tool logs)** as the
  reproducible artifact; closed-API teacher drift is mitigated because at least
  one open-weight teacher (DeepSeek open / Qwen) can be re-run end to end.
- Never commit API keys; keys come only from `*_API_KEY` env (optionally via the
  existing ignored `.env` loader). The connection table stores only the env var
  *name*, never the value.

## Testing (TDD)

Unit tests, no live API calls (mock the client):

1. Config: `sources:` parsed; task `source` resolves to its entry; missing entry
   falls back to global; `deterministic` needs none.
2. Connection resolution: two tasks with different sources resolve to different
   `(base_url, model, api_key_env)` triples.
3. Generator construction: `kind: openai_compat` builds the generalized
   generator with the resolved connection; `deepseek` alias unchanged.
4. Metadata: a frontier `openai_compat` two_stage source -> `natural_llm`,
   `system-his-v1.2`, `training_split: clean`.
5. Preflight: per-source auth diagnostics list every `openai_compat` source;
   missing key for one source surfaces as that source's error only.
6. Reporting: a mixed two-teacher fixture run yields one `calibration_matrix`
   /`metadata_breakdown` row per teacher.
7. Backward compatibility: an existing config with no `sources:` block behaves
   exactly as today.

A live multi-teacher smoke (Claude + DeepSeek, 1 sample each, T1) is a manual
verification step after units pass, mirroring the existing `his-v12-smoke-*`
pattern; it is not part of the automated suite.

## Out of Scope / Future

- **Gemini** and any further frontier endpoints — add later as a pure `sources:`
  entry once the seam is proven.
- Student-side model selection / fine-tuning (separate thread; teacher work
  feeds it but does not depend on it).
- Per-teacher prompt calibration: each new teacher will need its System-HIS
  prompt tuned to pass L0, just as DeepSeek did. This design provides the wiring;
  prompt tuning per teacher is follow-on engineering tracked in
  `docs/current-status.md`.

## Resolved Decisions (2026-06-25)

1. **Endpoints:** Claude and GPT-5.5 connect **directly to their native
   OpenAI-compatible endpoints** (no gateway). Only `base_url`/auth differ per
   source.
2. **Generation mode:** **`two_stage` only** in this cut. All new teachers go
   through the validated REQ2HIS -> HIS2PROJECT path to inherit the v1.2
   contract guarantees. `direct` mode is deferred (not implemented now).
3. **Balancing:** **No per-teacher budget.** Teacher sample counts are
   controlled entirely by each task's `count`. `line_b_targets` is unchanged.
